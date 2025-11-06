"""
Quick verification script to check seeded data
Run with: python verify_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_site.settings')
django.setup()

from django.utils import timezone
from core.models import Patient, PatientHealthRecord, Department, Doctor, Appointment

print("=" * 60)
print("DATABASE SUMMARY")
print("=" * 60)
print(f"Departments: {Department.objects.count()}")
print(f"  - {', '.join([d.name for d in Department.objects.all()])}")
print()
print(f"Doctors: {Doctor.objects.count()}")
for dept in Department.objects.all():
    count = Doctor.objects.filter(department=dept).count()
    print(f"  - {dept.name}: {count} doctors")
print()
print(f"Patients: {Patient.objects.count()}")
sample_patient = Patient.objects.first()
if sample_patient:
    print(f"  Sample: {sample_patient.patient_id} - {sample_patient.full_name} ({sample_patient.age} years old)")
    print(f"    Blood Type: {sample_patient.blood_type}")
    print(f"    Allergies: {sample_patient.known_allergies or 'None'}")
    print(f"    Medical History: {sample_patient.medical_history or 'None'}")
print()
print(f"Health Records: {PatientHealthRecord.objects.count()}")
sample_record = PatientHealthRecord.objects.first()
if sample_record:
    print(f"  Sample Record:")
    print(f"    Patient: {sample_record.patient.full_name}")
    print(f"    Date: {sample_record.record_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"    Doctor: {sample_record.doctor.full_name}")
    print(f"    Diagnosis: {sample_record.diagnosis}")
    if sample_record.systolic_bp and sample_record.diastolic_bp:
        print(f"    BP: {sample_record.systolic_bp}/{sample_record.diastolic_bp} mmHg")
    if sample_record.bmi:
        print(f"    BMI: {sample_record.bmi:.2f}")
print()
print(f"Appointments: {Appointment.objects.count()}")
future_appts = Appointment.objects.filter(appointment_date__gte=timezone.now().date()).count()
print(f"  Future appointments: {future_appts}")
print("=" * 60)

