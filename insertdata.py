# seed_patients.py
from django.contrib.auth import get_user_model
from core.models import Patient, Department, Doctor
from datetime import date, timedelta
import random

User = get_user_model()

# Create Departments
departments_data = [
    ("Cardiology", "Heart and cardiovascular system care"),
    ("Pediatrics", "Medical care for infants, children, and adolescents"),
    ("Emergency Medicine", "Emergency care and trauma services"),
    ("Orthopedics", "Bones, joints, and musculoskeletal system"),
    ("Neurology", "Brain and nervous system disorders"),
    ("General Medicine", "Primary care and general health services"),
    ("Dermatology", "Skin, hair, and nail conditions"),
]

departments = {}
for name, description in departments_data:
    dept, _ = Department.objects.get_or_create(
        name=name,
        defaults={"description": description}
    )
    departments[name] = dept

# Create Doctors with usernames and passwords
doctors_data = [
    ("Dr. Sarah Johnson", "Cardiology", "sarah.johnson@hospital.com", "555-0101"),
    ("Dr. Michael Chen", "Cardiology", "michael.chen@hospital.com", "555-0102"),
    ("Dr. Emily Rodriguez", "Cardiology", "emily.rodriguez@hospital.com", "555-0103"),
    ("Dr. James Wilson", "Pediatrics", "james.wilson@hospital.com", "555-0201"),
    ("Dr. Lisa Anderson", "Pediatrics", "lisa.anderson@hospital.com", "555-0202"),
    ("Dr. Robert Taylor", "Pediatrics", "robert.taylor@hospital.com", "555-0203"),
    ("Dr. Patricia Martinez", "Emergency Medicine", "patricia.martinez@hospital.com", "555-0301"),
    ("Dr. David Brown", "Emergency Medicine", "david.brown@hospital.com", "555-0302"),
    ("Dr. Jennifer Lee", "Orthopedics", "jennifer.lee@hospital.com", "555-0401"),
    ("Dr. Christopher White", "Orthopedics", "christopher.white@hospital.com", "555-0402"),
    ("Dr. Amanda Davis", "Neurology", "amanda.davis@hospital.com", "555-0501"),
    ("Dr. Daniel Garcia", "Neurology", "daniel.garcia@hospital.com", "555-0502"),
    ("Dr. Kevin Moore", "General Medicine", "kevin.moore@hospital.com", "555-0701"),
    ("Dr. Nancy Jackson", "General Medicine", "nancy.jackson@hospital.com", "555-0702"),
    ("Dr. Steven Harris", "Dermatology", "steven.harris@hospital.com", "555-0801"),
]

doctor_credentials = []
doctor_created_count = 0

for i, (full_name, dept_name, email, phone) in enumerate(doctors_data, start=1):
    # Generate username from doctor name
    username = f"doctor{i}"
    password = f"doc{i}pass123"
    
    # Get department
    dept = departments.get(dept_name, departments["General Medicine"])
    
    # Create User account for doctor
    doc_user, user_created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": User.Roles.DOCTOR,
            "is_active": True,
            "is_staff": True,  # enables admin access if needed
        }
    )
    
    if user_created:
        doc_user.set_password(password)
        doc_user.save()
    
    # Create Doctor record linked to User
    doctor, doctor_created = Doctor.objects.get_or_create(
        user=doc_user,
        defaults={
            "full_name": full_name,
            "department": dept,
            "email": email,
            "phone": phone,
        }
    )
    
    if doctor_created:
        doctor_created_count += 1
    
    doctor_credentials.append((username, password, full_name, dept_name))


def random_dob():
    """Generate random date of birth (20–70 years old)."""
    return date.today() - timedelta(days=random.randint(20 * 365, 70 * 365))


created_count = 0
login_credentials = []

for i in range(1, 101):
    username = f"patient{i}"
    email = f"{username}@test.com"
    password = f"pass{i}123"

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": "patient",
            "is_active": True,    # ensures the user can login
        }
    )

    if created:
        user.set_password(password)
        user.save()

    patient, pcreated = Patient.objects.get_or_create(
        patient_id=f"P{i:04d}",
        defaults={
            "user": user,
            "first_name": f"Test{i}",
            "last_name": "User",
            "date_of_birth": random_dob(),
            "gender": random.choice(["M", "F", "O"]),
            "email": email,
            "phone_country_code": "+91",
            "phone": str(random.randint(7000000000, 9999999999)),
            "aadhar_number": str(random.randint(10**11, 10**12 - 1)),
            "address": "Sample address",
            "emergency_contact_name": "Emergency Test",
            "emergency_contact_phone": "9876543210",
            "blood_type": random.choice(["A+", "A-", "B+", "O+", "AB+"]),
            "known_allergies": "None",
            "medical_history": "Healthy",
        }
    )
    if pcreated:
        created_count += 1

    login_credentials.append((username, password))

print(f"✔ Successfully created/ensured {len(doctors_data)} doctors (created {doctor_created_count}).")
print(f"✔ Successfully created/ensured 100 patients (created {created_count}).")

print("\n========== DOCTOR LOGINS ==========")
for username, password, full_name, dept_name in doctor_credentials:
    print(f"{username} / {password} - {full_name} ({dept_name})")

print("\n========== PATIENT LOGINS ==========")
for u, p in login_credentials[:10]:  # Show only first 10 for preview
    print(f"{u} / {p}")

print("\n⚠ Full patient credentials not shown to avoid terminal flood.")
print("   You can access all users via Django admin or filter User.objects.all()")
