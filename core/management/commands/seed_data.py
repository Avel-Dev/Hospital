"""
Django management command to seed the database with authentic test data.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Department, Doctor, Patient, PatientHealthRecord, Appointment


class Command(BaseCommand):
    help = 'Seeds the database with authentic-looking test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            PatientHealthRecord.objects.all().delete()
            Appointment.objects.all().delete()
            Patient.objects.all().delete()
            Doctor.objects.all().delete()
            Department.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create Departments
        departments_data = [
            ('Cardiology', 'Heart and cardiovascular system care'),
            ('Pediatrics', 'Medical care for infants, children, and adolescents'),
            ('Emergency Medicine', 'Emergency care and trauma services'),
            ('Orthopedics', 'Bones, joints, and musculoskeletal system'),
            ('Neurology', 'Brain and nervous system disorders'),
            ('Oncology', 'Cancer diagnosis and treatment'),
            ('General Medicine', 'Primary care and general health services'),
            ('Dermatology', 'Skin, hair, and nail conditions'),
        ]

        departments = {}
        for name, description in departments_data:
            dept, created = Department.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            departments[name] = dept
            if created:
                self.stdout.write(f'Created department: {name}')

        # Create Doctors
        doctors_data = {
            'Cardiology': [
                ('Dr. Sarah Johnson', 'sarah.johnson@hospital.com', '555-0101'),
                ('Dr. Michael Chen', 'michael.chen@hospital.com', '555-0102'),
                ('Dr. Emily Rodriguez', 'emily.rodriguez@hospital.com', '555-0103'),
            ],
            'Pediatrics': [
                ('Dr. James Wilson', 'james.wilson@hospital.com', '555-0201'),
                ('Dr. Lisa Anderson', 'lisa.anderson@hospital.com', '555-0202'),
                ('Dr. Robert Taylor', 'robert.taylor@hospital.com', '555-0203'),
            ],
            'Emergency Medicine': [
                ('Dr. Patricia Martinez', 'patricia.martinez@hospital.com', '555-0301'),
                ('Dr. David Brown', 'david.brown@hospital.com', '555-0302'),
            ],
            'Orthopedics': [
                ('Dr. Jennifer Lee', 'jennifer.lee@hospital.com', '555-0401'),
                ('Dr. Christopher White', 'christopher.white@hospital.com', '555-0402'),
            ],
            'Neurology': [
                ('Dr. Amanda Davis', 'amanda.davis@hospital.com', '555-0501'),
                ('Dr. Daniel Garcia', 'daniel.garcia@hospital.com', '555-0502'),
            ],
            'Oncology': [
                ('Dr. Michelle Thompson', 'michelle.thompson@hospital.com', '555-0601'),
            ],
            'General Medicine': [
                ('Dr. Kevin Moore', 'kevin.moore@hospital.com', '555-0701'),
                ('Dr. Nancy Jackson', 'nancy.jackson@hospital.com', '555-0702'),
            ],
            'Dermatology': [
                ('Dr. Steven Harris', 'steven.harris@hospital.com', '555-0801'),
            ],
        }

        doctors = {}
        for dept_name, doc_list in doctors_data.items():
            dept = departments[dept_name]
            for name, email, phone in doc_list:
                doctor, created = Doctor.objects.get_or_create(
                    full_name=name,
                    defaults={
                        'department': dept,
                        'email': email,
                        'phone': phone
                    }
                )
                doctors[name] = doctor
                if created:
                    self.stdout.write(f'Created doctor: {name} ({dept_name})')

        # Create Patients
        first_names_male = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles']
        first_names_female = ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 
                     'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee']

        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        genders = ['M', 'F']
        
        medical_conditions = [
            'Hypertension, Type 2 Diabetes',
            'Asthma, Seasonal allergies',
            'High cholesterol',
            'Previous appendectomy (2015)',
            'Migraine headaches',
            'None',
            'Arthritis, Osteoporosis',
            'GERD, IBS',
        ]

        allergies = [
            'Penicillin',
            'Shellfish, Peanuts',
            'Latex',
            'None',
            'Aspirin',
            'Iodine contrast',
            'Eggs',
            '',
        ]

        patients = []
        for i in range(50):  # Create 50 patients
            gender = random.choice(genders)
            first_name = random.choice(first_names_male if gender == 'M' else first_names_female)
            last_name = random.choice(last_names)
            
            # Generate realistic date of birth (ages 1-85)
            age = random.randint(1, 85)
            dob = timezone.now().date() - timedelta(days=age*365 + random.randint(0, 365))
            
            # Generate patient ID
            patient_id = f"PAT{str(i+1).zfill(6)}"
            
            # Generate email
            email = f"{first_name.lower()}.{last_name.lower()}@email.com"
            
            # Generate phone (US format)
            phone = f"555-{random.randint(1000, 9999)}"
            
            # Generate address
            street_num = random.randint(100, 9999)
            streets = ['Main St', 'Oak Ave', 'Park Blvd', 'Elm St', 'Maple Dr', 'Cedar Ln']
            cities = ['Springfield', 'Riverside', 'Greenwood', 'Oakwood', 'Lakeside']
            states = ['CA', 'NY', 'TX', 'FL', 'IL']
            address = f"{street_num} {random.choice(streets)}, {random.choice(cities)}, {random.choice(states)} {random.randint(10000, 99999)}"
            
            # Emergency contact
            ec_name = random.choice(['John', 'Jane', 'Mary', 'Robert']) + ' ' + random.choice(last_names)
            ec_phone = f"555-{random.randint(1000, 9999)}"
            
            patient = Patient.objects.create(
                patient_id=patient_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                gender=gender,
                email=email,
                phone=phone,
                address=address,
                emergency_contact_name=ec_name,
                emergency_contact_phone=ec_phone,
                blood_type=random.choice(blood_types),
                known_allergies=random.choice(allergies),
                medical_history=random.choice(medical_conditions),
            )
            patients.append(patient)
            if (i + 1) % 10 == 0:
                self.stdout.write(f'Created {i + 1} patients...')

        self.stdout.write(self.style.SUCCESS(f'Created {len(patients)} patients'))

        # Create Health Records (3-8 records per patient over time)
        visit_types = ['Routine', 'Follow-up', 'Emergency', 'Check-up', 'Consultation']
        diagnoses = [
            'Hypertension',
            'Upper respiratory infection',
            'Routine check-up - healthy',
            'Type 2 Diabetes',
            'Bronchitis',
            'Migraine',
            'Sprained ankle',
            'Fractured wrist',
            'Asthma exacerbation',
            'Pneumonia',
            'Healthy - no issues',
            'Strep throat',
            'Urinary tract infection',
            'Gastroenteritis',
            'Arthritis flare-up',
        ]

        medications_list = [
            'Lisinopril 10mg daily',
            'Metformin 500mg twice daily',
            'Amoxicillin 500mg three times daily for 7 days',
            'Ibuprofen 200mg as needed',
            'Albuterol inhaler as needed',
            'None',
            'Amlodipine 5mg daily',
            'Levothyroxine 75mcg daily',
            'Simvastatin 20mg daily',
            'Acetaminophen 500mg as needed',
        ]

        symptoms_list = [
            'Chest pain and shortness of breath',
            'Fever, cough, congestion',
            'No symptoms reported',
            'Headache and dizziness',
            'Joint pain and stiffness',
            'Abdominal pain and nausea',
            'Fatigue and weakness',
            'Rash and itching',
            'Sore throat and difficulty swallowing',
            'Back pain',
        ]

        record_count = 0
        for patient in patients:
            num_records = random.randint(3, 8)
            
            # Get doctors from patient's likely departments based on age
            if patient.age < 18:
                likely_depts = ['Pediatrics', 'Emergency Medicine', 'General Medicine']
            elif patient.age > 65:
                likely_depts = ['Cardiology', 'General Medicine', 'Neurology', 'Orthopedics']
            else:
                likely_depts = list(departments.keys())
            
            # Select 2-3 departments for this patient
            patient_depts = random.sample(likely_depts, min(3, len(likely_depts)))
            patient_doctors = [d for d in doctors.values() if d.department.name in patient_depts]
            
            if not patient_doctors:
                patient_doctors = list(doctors.values())[:3]
            
            # Create records over the past 2 years
            for i in range(num_records):
                days_ago = random.randint(1, 730)  # Past 2 years
                record_date = timezone.now() - timedelta(days=days_ago, hours=random.randint(8, 17))
                
                doctor = random.choice(patient_doctors)
                department = doctor.department
                
                # Generate realistic vital signs based on age
                if patient.age < 18:
                    systolic_bp = random.randint(90, 130)
                    diastolic_bp = random.randint(50, 85)
                    heart_rate = random.randint(70, 120)
                    weight = random.randint(15, 70) if patient.age < 12 else random.randint(40, 100)
                    height = random.randint(80, 180)
                elif patient.age > 65:
                    systolic_bp = random.randint(110, 160)
                    diastolic_bp = random.randint(60, 95)
                    heart_rate = random.randint(60, 100)
                    weight = random.randint(50, 100)
                    height = random.randint(150, 185)
                else:
                    systolic_bp = random.randint(100, 140)
                    diastolic_bp = random.randint(60, 90)
                    heart_rate = random.randint(55, 100)
                    weight = random.randint(50, 120)
                    height = random.randint(150, 200)
                
                temperature = round(random.uniform(36.1, 38.5), 1)
                
                diagnosis = random.choice(diagnoses)
                medications = random.choice(medications_list)
                symptoms = random.choice(symptoms_list)
                visit_type = random.choice(visit_types)
                
                notes = f"Patient seen for {visit_type.lower()} visit. {random.choice(['Vitals stable.', 'Patient reports improvement.', 'Follow-up recommended.', 'No concerns noted.'])}"
                
                PatientHealthRecord.objects.create(
                    patient=patient,
                    record_date=record_date,
                    doctor=doctor,
                    department=department,
                    systolic_bp=systolic_bp,
                    diastolic_bp=diastolic_bp,
                    heart_rate=heart_rate,
                    temperature=temperature,
                    weight=weight,
                    height=height,
                    symptoms=symptoms,
                    diagnosis=diagnosis,
                    medications=medications,
                    notes=notes,
                    visit_type=visit_type,
                )
                record_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {record_count} health records'))

        # Create Appointments (past and future)
        appointment_notes = [
            'Routine check-up',
            'Follow-up appointment',
            'Annual physical',
            'Consultation',
            'Review test results',
            'Symptom evaluation',
            '',
        ]

        future_appointments = 0
        for _ in range(30):  # Create 30 appointments
            patient = random.choice(patients)
            doctor = random.choice(list(doctors.values()))
            department = doctor.department
            
            # Mix of past and future appointments
            if random.random() < 0.3:  # 30% future appointments
                days_ahead = random.randint(1, 60)
                appt_date = timezone.now().date() + timedelta(days=days_ahead)
                future_appointments += 1
            else:
                days_ago = random.randint(1, 90)
                appt_date = timezone.now().date() - timedelta(days=days_ago)
            
            Appointment.objects.create(
                patient_name=patient.full_name,
                patient_email=patient.email,
                patient=patient,
                department=department,
                doctor=doctor,
                appointment_date=appt_date,
                notes=random.choice(appointment_notes),
            )

        self.stdout.write(self.style.SUCCESS(f'Created 30 appointments ({future_appointments} future)'))

        self.stdout.write(self.style.SUCCESS('\nData seeding completed successfully!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Departments: {Department.objects.count()}')
        self.stdout.write(f'  - Doctors: {Doctor.objects.count()}')
        self.stdout.write(f'  - Patients: {Patient.objects.count()}')
        self.stdout.write(f'  - Health Records: {PatientHealthRecord.objects.count()}')
        self.stdout.write(f'  - Appointments: {Appointment.objects.count()}')

