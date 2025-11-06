from django.shortcuts import render, redirect, get_object_or_404
from .models import Department, Doctor, Appointment, Patient, PatientHealthRecord
from django import forms
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg, Max, Min
from collections import defaultdict
import json
from datetime import timedelta



class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'patient_name',
            'patient_email',
            'patient',
            'department',
            'doctor',
            'appointment_date',
            'notes',
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


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
            'phone',
            'address',
            'emergency_contact_name',
            'emergency_contact_phone',
            'blood_type',
            'known_allergies',
            'medical_history',
        ]
        widgets = {
            'patient_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'known_allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


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


def dashboard(request):
    # Overall statistics
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_departments = Department.objects.count()
    total_appointments = Appointment.objects.count()
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
    
    # Department-wise patient distribution (from appointments and health records)
    dept_patient_counts = defaultdict(int)
    # Count unique patients per department from appointments
    for dept in Department.objects.all():
        patient_count = Patient.objects.filter(
            Q(appointments__department=dept) | Q(health_records__department=dept)
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
        'total_appointments': total_appointments,
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


def departments(request):
    department_list = Department.objects.all()
    return render(request, 'departments.html', {'departments': department_list})


def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    doctors = department.doctors.all()
    
    # Get unique patients who have appointments or health records in this department
    patients_from_appointments = Patient.objects.filter(
        appointments__department=department
    ).distinct()
    
    patients_from_health_records = Patient.objects.filter(
        health_records__department=department
    ).distinct()
    
    # Combine and get unique patients
    patients = (patients_from_appointments | patients_from_health_records).distinct()
    
    # Get recent appointments for this department
    recent_appointments = department.appointments.all()[:10]
    
    return render(request, 'department_detail.html', {
        'department': department,
        'doctors': doctors,
        'patients': patients,
        'recent_appointments': recent_appointments,
    })


def doctors(request):
    doctor_list = Doctor.objects.select_related('department').all()
    return render(request, 'doctors.html', {'doctors': doctor_list})


def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('home')
    else:
        form = AppointmentForm()
    return render(request, 'book_appointment.html', {'form': form})


# Patient Management Views
def patient_list(request):
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
            Q(appointments__department__name=filter_value) | Q(health_records__department__name=filter_value)
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


def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient registered successfully!')
            return redirect('patient_list')
    else:
        form = PatientForm()
    return render(request, 'patient_form.html', {'form': form, 'title': 'Register New Patient'})


def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    health_records = patient.health_records.all()[:10]  # Latest 10 records
    appointments = patient.appointments.all()[:10]  # Latest 10 appointments
    return render(request, 'patient_detail.html', {
        'patient': patient,
        'health_records': health_records,
        'appointments': appointments,
    })


def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('patient_detail', pk=pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patient_form.html', {'form': form, 'title': 'Update Patient Information', 'patient': patient})


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


def health_record_detail(request, pk):
    record = get_object_or_404(PatientHealthRecord, pk=pk)
    return render(request, 'health_record_detail.html', {'record': record})


# Delete Views
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        # Check for related records
        doctors_count = department.doctors.count()
        appointments_count = department.appointments.count()
        health_records_count = department.health_records.count()
        
        if doctors_count > 0 or appointments_count > 0 or health_records_count > 0:
            messages.error(request, 
                f'Cannot delete department "{department.name}" because it has '
                f'{doctors_count} doctor(s), {appointments_count} appointment(s), '
                f'and {health_records_count} health record(s) associated with it.')
            return redirect('departments')
        
        department_name = department.name
        department.delete()
        messages.success(request, f'Department "{department_name}" deleted successfully!')
        return redirect('departments')
    
    # GET request - show confirmation
    doctors_count = department.doctors.count()
    appointments_count = department.appointments.count()
    health_records_count = department.health_records.count()
    
    return render(request, 'delete_confirm.html', {
        'object': department,
        'object_type': 'Department',
        'object_name': department.name,
        'cancel_url': 'departments',
        'related_count': {
            'Doctors': doctors_count,
            'Appointments': appointments_count,
            'Health Records': health_records_count,
        }
    })


def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    
    if request.method == 'POST':
        # Check for related records
        appointments_count = doctor.appointments.count()
        health_records_count = doctor.health_records.count()
        
        if appointments_count > 0 or health_records_count > 0:
            messages.error(request, 
                f'Cannot delete doctor "{doctor.full_name}" because they have '
                f'{appointments_count} appointment(s) and {health_records_count} health record(s) associated.')
            return redirect('doctors')
        
        doctor_name = doctor.full_name
        doctor.delete()
        messages.success(request, f'Doctor "{doctor_name}" deleted successfully!')
        return redirect('doctors')
    
    # GET request - show confirmation
    appointments_count = doctor.appointments.count()
    health_records_count = doctor.health_records.count()
    
    return render(request, 'delete_confirm.html', {
        'object': doctor,
        'object_type': 'Doctor',
        'object_name': doctor.full_name,
        'cancel_url': 'doctors',
        'related_count': {
            'Appointments': appointments_count,
            'Health Records': health_records_count,
        }
    })


def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Count related records for warning
        health_records_count = patient.health_records.count()
        appointments_count = patient.appointments.count()
        
        patient_name = patient.full_name
        patient_id = patient.patient_id
        patient.delete()
        
        messages.success(request, 
            f'Patient "{patient_name}" (ID: {patient_id}) deleted successfully! '
            f'This also deleted {health_records_count} health record(s). '
            f'{appointments_count} appointment(s) were unlinked.')
        return redirect('patient_list')
    
    # GET request - show confirmation
    health_records_count = patient.health_records.count()
    appointments_count = patient.appointments.count()
    
    return render(request, 'delete_confirm.html', {
        'object': patient,
        'object_type': 'Patient',
        'object_name': f'{patient.full_name} (ID: {patient.patient_id})',
        'cancel_url': 'patient_detail',
        'cancel_url_pk': patient.pk,
        'related_count': {
            'Health Records': health_records_count,
            'Appointments': appointments_count,
        },
        'warning_message': 'Deleting a patient will also delete all associated health records.'
    })


def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        patient_name = appointment.patient_name
        appointment_date = appointment.appointment_date
        appointment.delete()
        messages.success(request, f'Appointment for "{patient_name}" on {appointment_date} deleted successfully!')
        
        # Redirect back to patient detail if linked, otherwise to home
        if appointment.patient:
            return redirect('patient_detail', pk=appointment.patient.pk)
        return redirect('home')
    
    # GET request - show confirmation
    return render(request, 'delete_confirm.html', {
        'object': appointment,
        'object_type': 'Appointment',
        'object_name': f'{appointment.patient_name} - {appointment.appointment_date}',
        'cancel_url': 'patient_detail' if appointment.patient else 'home',
        'cancel_url_pk': appointment.patient.pk if appointment.patient else None,
    })

# Create your views here.
