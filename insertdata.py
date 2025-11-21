# seed_patients.py
from django.contrib.auth import get_user_model
from core.models import Patient, Department, Doctor
from datetime import date, timedelta
import random

User = get_user_model()

# Create Department
dept, _ = Department.objects.get_or_create(
    name="General",
    defaults={"description": "General Medicine"},
)

# Create Doctor with proper login
doc_user, created = User.objects.get_or_create(
    username="doctor1",
    defaults={
        "email": "doctor@example.com",
        "role": "doctor",
        "is_active": True,       # required
        "is_staff": True,        # enables admin access if needed
    }
)
if created:
    doc_user.set_password("docpass123")
    doc_user.save()

doctor, _ = Doctor.objects.get_or_create(
    user=doc_user,
    defaults={"full_name": "Dr. Test", "department": dept}
)


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

print(f"✔ Successfully created/ensured 100 patients (created {created_count}).")
print("\n========== PATIENT LOGINS ==========")
for u, p in login_credentials[:10]:  # Show only first 10 for preview
    print(f"{u} / {p}")

print("\n✨ Doctor login:")
print("doctor1 / docpass123")
print("\n⚠ Full patient credentials not shown to avoid terminal flood.")
print("   You can access all users via Django admin or filter User.objects.all()")
