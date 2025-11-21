from collections import defaultdict
from datetime import timedelta
import json

import logging
logger = logging.getLogger(__name__)

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordResetForm
from django.db import transaction
from django.db.models import Avg, Count, Max, Min, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string

from .decorators import role_required
from .forms import CreateUserForm
from .models import AuditLog, Department, Doctor, Patient, PatientHealthRecord

User = get_user_model()

def generate_patient_id():
    """Generate a unique patient identifier for self-service signups."""
    base = timezone.now().strftime('PAT%Y%m%d')
    while True:
        candidate = f"{base}{get_random_string(4).upper()}"
        if not Patient.objects.filter(patient_id=candidate).exists():
            return candidate


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DoctorAccountForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    full_name = forms.CharField(max_length=160, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.order_by('name')

    phone = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def save(self):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                role=User.Roles.DOCTOR,
            )
            doctor = Doctor.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                department=self.cleaned_data['department'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data['phone'],
            )
        return doctor


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'patient_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'email',
            'phone_country_code',
            'phone',
            'address',
            'emergency_contact_name',
            'emergency_contact_phone',
            'blood_type',
            'known_allergies',
            'medical_history',
            'aadhar_number',
        ]
        widgets = {
            'patient_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_country_code': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9876543210'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'known_allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'aadhar_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12-digit number'}),
        }


class AdminPatientAccountForm(PatientForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Used for patient portal login.',
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        patient = super().save(commit=False)
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                role=User.Roles.PATIENT,
            )
            patient.user = user
            if commit:
                patient.save()
        return patient
    
    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar:
            aadhar = aadhar.strip()
            self.cleaned_data['aadhar_number'] = aadhar
        if aadhar and Patient.objects.filter(aadhar_number=aadhar).exists():
            raise forms.ValidationError('This Aadhar number is already registered.')
        return aadhar
    
    class Meta(PatientForm.Meta):
        fields = PatientForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('patient_id') and not self.data.get('patient_id'):
            generated = generate_patient_id()
            self.fields['patient_id'].initial = generated
        if not self.initial.get('phone_country_code'):
            self.fields['phone_country_code'].initial = '+91'
        self.fields['aadhar_number'].required = True
        self.fields['patient_id'].help_text = 'You can keep the suggested ID or provide your own.'
        self.fields['phone'].help_text = 'Enter digits only, without the country code.'
        self.fields['aadhar_number'].help_text = '12-digit Aadhar number. Required for verification.'


class PatientSignupForm(PatientForm):
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Used for logging in.',
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta(PatientForm.Meta):
        fields = PatientForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('patient_id') and not self.data.get('patient_id'):
            generated = generate_patient_id()
            self.fields['patient_id'].initial = generated
        if not self.initial.get('phone_country_code'):
            self.fields['phone_country_code'].initial = '+91'
        self.fields['aadhar_number'].required = True
        self.fields['patient_id'].help_text = 'You can keep the suggested ID or provide your own.'
        self.fields['phone'].help_text = 'Enter digits only, without the country code.'
        self.fields['aadhar_number'].help_text = '12-digit Aadhar number. Required for verification.'

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar:
            aadhar = aadhar.strip()
            self.cleaned_data['aadhar_number'] = aadhar
        if aadhar and Patient.objects.filter(aadhar_number=aadhar).exists():
            raise forms.ValidationError('This Aadhar number is already registered.')
        return aadhar


class PatientHealthRecordForm(forms.ModelForm):
    class Meta:
        model = PatientHealthRecord
        fields = [
            'patient',
            'record_date',
            'doctor',
            'department',
            'visit_type',
            'systolic_bp',
            'diastolic_bp',
            'heart_rate',
            'temperature',
            'weight',
            'height',
            'symptoms',
            'diagnosis',
            'medications',
            'notes',
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'record_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'visit_type': forms.TextInput(attrs={'class': 'form-control'}),
            'systolic_bp': forms.NumberInput(attrs={'class': 'form-control'}),
            'diastolic_bp': forms.NumberInput(attrs={'class': 'form-control'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'temperature': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
            'medications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def patient_signup(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('dashboard' if request.user.is_staff else 'home')
    
    if request.method == 'POST':
        form = PatientSignupForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                role=User.Roles.PATIENT,
            )
            patient = form.save(commit=False)
            patient.user = user
            patient.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome aboard.')
            return redirect('patient_detail', pk=patient.pk)
    else:
        form = PatientSignupForm()
    # inside patient_signup view, before render(...)
    textarea_fields = ['address', 'known_allergies', 'medical_history']
    return render(request, 'patient_signup.html', {'form': form, 'textarea_fields': textarea_fields})    
    #return render(request, 'patient_signup.html', {'form': form})


def is_admin(user):
    return user.is_authenticated and user.is_staff


def get_logged_in_doctor(user):
    if not user.is_authenticated or not getattr(user, 'is_doctor', False):
        return None
    try:
        return user.doctor_record
    except Doctor.DoesNotExist:
        return None


def doctor_patient_queryset(doctor):
    return Patient.objects.filter(health_records__doctor=doctor).distinct()


def doctor_can_view_patient(doctor, patient):
    if not doctor:
        return False
    return patient.health_records.filter(doctor=doctor).exists()


@role_required(User.Roles.ADMIN, User.Roles.SUPERADMIN)
def create_user_view(request):
    """
    Admin dashboard entry point for provisioning workforce accounts.

    Security tip: enable MFA/SSO (e.g., django-two-factor-auth or mozilla-django-oidc)
    for admin/doctor roles to reduce phishing exposure.
    """

    form = CreateUserForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        new_user = form.save()

        password_was_provided = form.password_provided
        if not password_was_provided:
            reset_form = PasswordResetForm({'email': new_user.email})
            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    use_https=request.is_secure(),
                )

        AuditLog.objects.create(
            actor=request.user,
            action='create_user',
            target=new_user.username,
            details={
                'role': new_user.role,
                'password_provided': password_was_provided,
            },
        )

        messages.success(request, f"User '{new_user.username}' created successfully.")
        return redirect('core_create_user')

    return render(request, 'admin/create_user.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='home')
def dashboard(request):
    # Overall statistics - only admins can see all data
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_departments = Department.objects.count()
    total_health_records = PatientHealthRecord.objects.count()
    
    # Gender distribution
    gender_data = Patient.objects.values('gender').annotate(count=Count('id'))
    gender_labels = []
    gender_counts = []
    gender_map = {'M': 'Male', 'F': 'Female', 'O': 'Other', 'P': 'Prefer not to say'}
    for item in gender_data:
        gender_labels.append(gender_map.get(item['gender'], item['gender']))
        gender_counts.append(item['count'])
    
    # Blood type distribution
    blood_type_data = Patient.objects.exclude(blood_type='').values('blood_type').annotate(count=Count('id')).order_by('blood_type')
    blood_type_labels = [item['blood_type'] for item in blood_type_data]
    blood_type_counts = [item['count'] for item in blood_type_data]
    
    # Age groups distribution
    patients = Patient.objects.all()
    age_groups = {
        '0-17': 0,
        '18-30': 0,
        '31-45': 0,
        '46-60': 0,
        '61-75': 0,
        '75+': 0
    }
    for patient in patients:
        age = patient.age
        if age <= 17:
            age_groups['0-17'] += 1
        elif age <= 30:
            age_groups['18-30'] += 1
        elif age <= 45:
            age_groups['31-45'] += 1
        elif age <= 60:
            age_groups['46-60'] += 1
        elif age <= 75:
            age_groups['61-75'] += 1
        else:
            age_groups['75+'] += 1
    
    age_group_labels = list(age_groups.keys())
    age_group_counts = list(age_groups.values())
    
    # Patient registrations over time (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    registrations = Patient.objects.filter(registration_date__gte=twelve_months_ago).extra(
        select={'month': "strftime('%%Y-%%m', registration_date)"}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    registration_months = [item['month'] for item in registrations]
    registration_counts = [item['count'] for item in registrations]
    
    # Department-wise patient distribution (based on health records)
    dept_patient_counts = defaultdict(int)
    for dept in Department.objects.all():
        patient_count = Patient.objects.filter(
            health_records__department=dept
        ).distinct().count()
        dept_patient_counts[dept.name] = patient_count
    
    dept_labels = list(dept_patient_counts.keys())
    dept_patient_data = list(dept_patient_counts.values())
    
    # Top diagnoses
    diagnoses = PatientHealthRecord.objects.exclude(diagnosis='').values('diagnosis').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    diagnosis_labels = [item['diagnosis'] for item in diagnoses]
    diagnosis_counts = [item['count'] for item in diagnoses]
    
    # Average vital signs by department
    dept_vitals = {}
    for dept in Department.objects.all():
        records = PatientHealthRecord.objects.filter(department=dept).exclude(systolic_bp__isnull=True)
        if records.exists():
            avg_bp_sys = records.aggregate(Avg('systolic_bp'))['systolic_bp__avg']
            avg_bp_dia = records.filter(diastolic_bp__isnull=False).aggregate(Avg('diastolic_bp'))['diastolic_bp__avg']
            avg_hr = records.filter(heart_rate__isnull=False).aggregate(Avg('heart_rate'))['heart_rate__avg']
            dept_vitals[dept.name] = {
                'systolic_bp': round(avg_bp_sys, 1) if avg_bp_sys else None,
                'diastolic_bp': round(avg_bp_dia, 1) if avg_bp_dia else None,
                'heart_rate': round(avg_hr, 1) if avg_hr else None,
            }
    
    # BMI distribution
    bmi_records = PatientHealthRecord.objects.exclude(bmi__isnull=True).values_list('bmi', flat=True)
    bmi_categories = {
        'Underweight (<18.5)': 0,
        'Normal (18.5-24.9)': 0,
        'Overweight (25-29.9)': 0,
        'Obese (≥30)': 0
    }
    for bmi in bmi_records:
        if bmi < 18.5:
            bmi_categories['Underweight (<18.5)'] += 1
        elif bmi < 25:
            bmi_categories['Normal (18.5-24.9)'] += 1
        elif bmi < 30:
            bmi_categories['Overweight (25-29.9)'] += 1
        else:
            bmi_categories['Obese (≥30)'] += 1
    
    bmi_labels = list(bmi_categories.keys())
    bmi_counts = list(bmi_categories.values())
    
    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_departments': total_departments,
        'total_health_records': total_health_records,
        'gender_labels': json.dumps(gender_labels),
        'gender_counts': json.dumps(gender_counts),
        'blood_type_labels': json.dumps(blood_type_labels),
        'blood_type_counts': json.dumps(blood_type_counts),
        'age_group_labels': json.dumps(age_group_labels),
        'age_group_counts': json.dumps(age_group_counts),
        'registration_months': json.dumps(registration_months),
        'registration_counts': json.dumps(registration_counts),
        'dept_labels': json.dumps(dept_labels),
        'dept_patient_data': json.dumps(dept_patient_data),
        'diagnosis_labels': json.dumps(diagnosis_labels),
        'diagnosis_counts': json.dumps(diagnosis_counts),
        'dept_vitals': dept_vitals,
        'bmi_labels': json.dumps(bmi_labels),
        'bmi_counts': json.dumps(bmi_counts),
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def departments(request):
    department_list = Department.objects.all()
    return render(request, 'departments.html', {'departments': department_list})


@login_required
@user_passes_test(is_admin, login_url='home')
def department_create(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        department = form.save()
        messages.success(request, f'Department "{department.name}" added successfully!')
        return redirect('departments')
    return render(request, 'department_form.html', {'form': form, 'title': 'Add Department'})


@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    doctors = department.doctors.all()
    
    # Filter data based on user type
    if request.user.is_staff:
        patients = Patient.objects.filter(
            health_records__department=department
        ).distinct()
        recent_records = department.health_records.select_related('patient', 'doctor').all()[:10]
    elif getattr(request.user, 'is_doctor', False):
        doctor = get_logged_in_doctor(request.user)
        if not doctor:
            messages.error(request, 'No doctor profile associated with your account.')
            return redirect('home')
        patients = Patient.objects.filter(
            health_records__doctor=doctor,
            health_records__department=department,
        ).distinct()
        recent_records = department.health_records.filter(doctor=doctor).select_related('patient').all()[:10]
    else:
        # Patient can only see their own data
        try:
            patient = request.user.patient_profile
            patients = Patient.objects.filter(pk=patient.pk)
            recent_records = department.health_records.filter(patient=patient).select_related('doctor').all()[:10]
        except Patient.DoesNotExist:
            patients = Patient.objects.none()
            recent_records = PatientHealthRecord.objects.none()
    
    return render(request, 'department_detail.html', {
        'department': department,
        'doctors': doctors,
        'patients': patients,
        'recent_records': recent_records,
    })


@login_required
def doctors(request):
    doctor_list = Doctor.objects.select_related('department').all()
    return render(request, 'doctors.html', {'doctors': doctor_list})


@login_required
@user_passes_test(is_admin, login_url='home')
def doctor_create(request):
    if request.method == 'POST':
        form = DoctorAccountForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f'Doctor account for "{doctor.full_name}" created successfully!')
            return redirect('doctors')
    else:
        form = DoctorAccountForm()
    return render(request, 'doctor_account_form.html', {'form': form, 'title': 'Add Doctor Account'})


# Patient Management Views
@login_required
def patient_list(request):
    if getattr(request.user, 'is_doctor', False):
        return redirect('doctor_patients')
    # Redirect patients to their own detail page
    if not request.user.is_staff:
        try:
            patient = request.user.patient_profile
            return redirect('patient_detail', pk=patient.pk)
        except Patient.DoesNotExist:
            messages.info(request, 'No patient profile found. Please contact administrator.')
            return redirect('home')
    
    # Admin can see all patients
    patients = Patient.objects.all()
    
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter_type', '')
    filter_value = request.GET.get('filter_value', '')
    
    if search_query:
        patients = patients.filter(
            patient_id__icontains=search_query
        ) | patients.filter(
            first_name__icontains=search_query
        ) | patients.filter(
            last_name__icontains=search_query
        ) | patients.filter(
            email__icontains=search_query
        )
    
    # Apply filters from chart clicks
    if filter_type == 'gender':
        gender_map = {'Male': 'M', 'Female': 'F', 'Other': 'O', 'Prefer not to say': 'P'}
        patients = patients.filter(gender=gender_map.get(filter_value, filter_value))
    elif filter_type == 'blood_type':
        patients = patients.filter(blood_type=filter_value)
    elif filter_type == 'age_group':
        today = timezone.now().date()
        from datetime import date
        
        if filter_value == '0-17':
            max_date = today.replace(year=today.year - 17)
            patients = patients.filter(date_of_birth__gte=max_date)
        elif filter_value == '18-30':
            min_date = today.replace(year=today.year - 30)
            max_date = today.replace(year=today.year - 18)
            patients = patients.filter(date_of_birth__gte=min_date, date_of_birth__lt=max_date)
        elif filter_value == '31-45':
            min_date = today.replace(year=today.year - 45)
            max_date = today.replace(year=today.year - 31)
            patients = patients.filter(date_of_birth__gte=min_date, date_of_birth__lt=max_date)
        elif filter_value == '46-60':
            min_date = today.replace(year=today.year - 60)
            max_date = today.replace(year=today.year - 46)
            patients = patients.filter(date_of_birth__gte=min_date, date_of_birth__lt=max_date)
        elif filter_value == '61-75':
            min_date = today.replace(year=today.year - 75)
            max_date = today.replace(year=today.year - 61)
            patients = patients.filter(date_of_birth__gte=min_date, date_of_birth__lt=max_date)
        elif filter_value == '75+':
            min_date = today.replace(year=today.year - 75)
            patients = patients.filter(date_of_birth__lt=min_date)
    elif filter_type == 'department':
        patients = patients.filter(
            health_records__department__name=filter_value
        ).distinct()
    elif filter_type == 'diagnosis':
        patients = patients.filter(health_records__diagnosis=filter_value).distinct()
    elif filter_type == 'bmi':
        if filter_value == 'Underweight (<18.5)':
            patients = patients.filter(health_records__bmi__lt=18.5).distinct()
        elif filter_value == 'Normal (18.5-24.9)':
            patients = patients.filter(health_records__bmi__gte=18.5, health_records__bmi__lt=25).distinct()
        elif filter_value == 'Overweight (25-29.9)':
            patients = patients.filter(health_records__bmi__gte=25, health_records__bmi__lt=30).distinct()
        elif filter_value == 'Obese (≥30)':
            patients = patients.filter(health_records__bmi__gte=30).distinct()
    
    filter_label = ''
    if filter_type and filter_value:
        filter_label = f"{filter_type.replace('_', ' ').title()}: {filter_value}"
    
    return render(request, 'patient_list.html', {
        'patients': patients,
        'search_query': search_query,
        'filter_type': filter_type,
        'filter_value': filter_value,
        'filter_label': filter_label,
    })


@role_required(User.Roles.DOCTOR)
def doctor_patients(request):
    doctor = get_logged_in_doctor(request.user)
    if not doctor:
        messages.error(request, 'No doctor profile found for your account.')
        return redirect('home')
    patients = doctor_patient_queryset(doctor).order_by('last_name', 'first_name')
    search_query = request.GET.get('search', '')
    if search_query:
        patients = patients.filter(
            Q(patient_id__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )
    return render(request, 'doctor_patients.html', {
        'patients': patients,
        'search_query': search_query,
        'doctor': doctor,
    })

@login_required
@user_passes_test(is_admin, login_url='home')
def patient_create(request):
    if request.method == 'POST':
        form = AdminPatientAccountForm(request.POST, request.FILES)
        logger.info("patient_create POST keys: %s", list(request.POST.keys()))
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Patient account for \"{patient.full_name}\" created successfully!')
            return redirect('patient_list')
        else:
            logger.info("patient_create form errors: %s", form.errors.as_json())
            messages.error(request, "There were errors in the submitted form. See fields highlighted.")
    else:
        form = AdminPatientAccountForm(initial={'patient_id': generate_patient_id()})

    textarea_fields = ['address', 'known_allergies', 'medical_history']
    account_fields = ['username', 'password1', 'password2']

    return render(request, 'patient_form.html', {
        'form': form,
        'title': 'Register New Patient',
        'show_account_fields': True,
        'textarea_fields': textarea_fields,
        'account_fields': account_fields,
        'patient': None,
    })




@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to view this patient
    if request.user.is_staff:
        pass
    elif getattr(request.user, 'is_doctor', False):
        doctor = get_logged_in_doctor(request.user)
        if not doctor or not doctor_can_view_patient(doctor, patient):
            messages.error(request, 'You do not have permission to view this patient record.')
            return redirect('home')
    else:
        try:
            user_patient = request.user.patient_profile
            if patient.pk != user_patient.pk:
                messages.error(request, 'You do not have permission to view this patient record.')
                return redirect('home')
        except Patient.DoesNotExist:
            messages.error(request, 'No patient profile found.')
            return redirect('home')
    
    health_records = patient.health_records.all()[:10]  # Latest 10 records
    return render(request, 'patient_detail.html', {
        'patient': patient,
        'health_records': health_records,
    })


@login_required
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to update this patient
    if request.user.is_staff:
        pass
    elif getattr(request.user, 'is_doctor', False):
        messages.error(request, 'Doctors cannot modify patient profiles.')
        return redirect('home')
    else:
        try:
            user_patient = request.user.patient_profile
            if patient.pk != user_patient.pk:
                messages.error(request, 'You do not have permission to update this patient record.')
                return redirect('home')
        except Patient.DoesNotExist:
            messages.error(request, 'No patient profile found.')
            return redirect('home')
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('patient_detail', pk=pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patient_form.html', {
        'form': form,
        'title': 'Update Patient Information',
        'patient': patient,
        'show_account_fields': False,
    })


@login_required
@user_passes_test(is_admin, login_url='home')
def health_record_create(request, patient_pk=None):
    if request.method == 'POST':
        form = PatientHealthRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Health record added successfully!')
            return redirect('patient_detail', pk=form.cleaned_data['patient'].pk)
    else:
        form = PatientHealthRecordForm()
        if patient_pk:
            try:
                patient = Patient.objects.get(pk=patient_pk)
                form.fields['patient'].initial = patient.pk
            except Patient.DoesNotExist:
                pass
    return render(request, 'health_record_form.html', {
        'form': form, 
        'title': 'Add Health Record',
        'patient_pk': patient_pk
    })


@login_required
def health_record_detail(request, pk):
    record = get_object_or_404(PatientHealthRecord, pk=pk)
    
    # Check if user has permission to view this record
    if request.user.is_staff:
        pass
    elif getattr(request.user, 'is_doctor', False):
        doctor = get_logged_in_doctor(request.user)
        if not doctor or record.doctor != doctor:
            messages.error(request, 'You do not have permission to view this health record.')
            return redirect('home')
    else:
        try:
            user_patient = request.user.patient_profile
            if record.patient.pk != user_patient.pk:
                messages.error(request, 'You do not have permission to view this health record.')
                return redirect('home')
        except Patient.DoesNotExist:
            messages.error(request, 'No patient profile found.')
            return redirect('home')
    
    return render(request, 'health_record_detail.html', {'record': record})


# Delete Views
@login_required
@user_passes_test(is_admin, login_url='home')
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        # Check for related records
        doctors_count = department.doctors.count()
        health_records_count = department.health_records.count()
        
        if doctors_count > 0 or health_records_count > 0:
            messages.error(request, 
                f'Cannot delete department "{department.name}" because it has '
                f'{doctors_count} doctor(s) and {health_records_count} health record(s) associated with it.')
            return redirect('departments')
        
        department_name = department.name
        department.delete()
        messages.success(request, f'Department "{department_name}" deleted successfully!')
        return redirect('departments')
    
    # GET request - show confirmation
    doctors_count = department.doctors.count()
    health_records_count = department.health_records.count()
    
    return render(request, 'delete_confirm.html', {
        'object': department,
        'object_type': 'Department',
        'object_name': department.name,
        'cancel_url': 'departments',
        'related_count': {
            'Doctors': doctors_count,
            'Health Records': health_records_count,
        }
    })


@login_required
@user_passes_test(is_admin, login_url='home')
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    
    if request.method == 'POST':
        # Check for related records
        health_records_count = doctor.health_records.count()
        
        if health_records_count > 0:
            messages.error(request, 
                f'Cannot delete doctor "{doctor.full_name}" because they have '
                f'{health_records_count} health record(s) associated.')
            return redirect('doctors')
        
        doctor_name = doctor.full_name
        doctor.delete()
        messages.success(request, f'Doctor "{doctor_name}" deleted successfully!')
        return redirect('doctors')
    
    # GET request - show confirmation
    health_records_count = doctor.health_records.count()
    
    return render(request, 'delete_confirm.html', {
        'object': doctor,
        'object_type': 'Doctor',
        'object_name': doctor.full_name,
        'cancel_url': 'doctors',
        'related_count': {
            'Health Records': health_records_count,
        }
    })


@login_required
@user_passes_test(is_admin, login_url='home')
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Count related records for warning
        health_records_count = patient.health_records.count()
        
        patient_name = patient.full_name
        patient_id = patient.patient_id
        patient.delete()
        
        messages.success(request, 
            f'Patient "{patient_name}" (ID: {patient_id}) deleted successfully! '
            f'This also deleted {health_records_count} health record(s).')
        return redirect('patient_list')
    
    # GET request - show confirmation
    health_records_count = patient.health_records.count()
    
    return render(request, 'delete_confirm.html', {
        'object': patient,
        'object_type': 'Patient',
        'object_name': f'{patient.full_name} (ID: {patient.patient_id})',
        'cancel_url': 'patient_detail',
        'cancel_url_pk': patient.pk,
        'related_count': {
            'Health Records': health_records_count,
        },
        'warning_message': 'Deleting a patient will also delete all associated health records.'
    })


@role_required(User.Roles.PATIENT)
def patient_self_delete(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, 'No patient profile found.')
        return redirect('home')
    
    if request.method == 'POST':
        patient_name = patient.full_name
        patient_id = patient.patient_id
        health_records_count = patient.health_records.count()
        user = request.user
        logout(request)
        user.delete()
        return render(request, 'account_deleted.html', {
            'patient_name': patient_name,
            'patient_id': patient_id,
            'health_records_count': health_records_count,
        })
    
    health_records_count = patient.health_records.count()
    return render(request, 'delete_confirm.html', {
        'object': patient,
        'object_type': 'Account',
        'object_name': f'{patient.full_name} (ID: {patient.patient_id})',
        'cancel_url': 'patient_detail',
        'cancel_url_pk': patient.pk,
        'related_count': {
            'Health Records': health_records_count,
        },
        'warning_message': 'Deleting your account will remove your login permanently. Hospital staff may retain medical records for compliance.',
    })


# Create your views here.
