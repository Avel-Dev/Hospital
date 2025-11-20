# Hospital Management System - Seed Data

## Seeding Test Data

This project includes a management command to populate the database with authentic-looking test data for development and testing purposes.

### Usage

To seed the database with test data:

```bash
python manage.py seed_data
```

To clear existing data and re-seed from scratch:

```bash
python manage.py seed_data --clear
```

### What Gets Created

The seed command creates:

- **8 Departments**: Cardiology, Pediatrics, Emergency Medicine, Orthopedics, Neurology, Oncology, General Medicine, Dermatology
- **17 Doctors**: Assigned across departments with realistic names, emails, and phone numbers
- **50 Patients**: With realistic:
  - Names, ages (1-85 years), genders
  - Contact information (emails, phones, addresses)
  - Emergency contacts
  - Blood types (randomly assigned)
  - Allergies and medical history
  - Patient IDs (PAT000001, PAT000002, etc.)
  
- **~250+ Health Records**: Each patient has 3-8 health records over the past 2 years with:
  - Timestamped visits
  - Vital signs (BP, heart rate, temperature, weight, height)
  - Auto-calculated BMI
  - Diagnoses (15+ different conditions)
  - Medications prescribed
  - Symptoms and clinical notes
  - Visit types (Routine, Follow-up, Emergency, etc.)
  

### Verification

To verify the seeded data, run:

```bash
python verify_data.py
```

This will display a summary of all data in the database.

### Data Characteristics

- **Realistic vital signs**: Age-appropriate ranges
  - Pediatric patients: lower BP, higher heart rates
  - Elderly patients: higher BP ranges
  - Adult patients: normal ranges
  
- **Time-series data**: Health records span the past 2 years, allowing for trend analysis

- **Department matching**: Patients are matched with appropriate departments based on age
  - Children → Pediatrics
  - Elderly → Cardiology, General Medicine
  - All ages → Variety of departments

- **Varied diagnoses**: Includes common conditions like:
  - Hypertension
  - Upper respiratory infections
  - Diabetes
  - Routine check-ups
  - Various injuries and conditions

### Notes

- The seed command uses `get_or_create` to avoid duplicates, so running it multiple times won't create duplicate departments or doctors
- Patient IDs are sequential (PAT000001, PAT000002, etc.)
- Health records are randomly distributed across the past 2 years
- Use `--clear` flag to start fresh if you need to reset the data

