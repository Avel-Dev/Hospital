from django.shortcuts import render, redirect, get_object_or_404
from .models import Department, Doctor, Appointment, Patient, PatientHealthRecord
from django import forms
from django.contrib import messages


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
    return render(request, 'patient_list.html', {'patients': patients, 'search_query': search_query})


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
