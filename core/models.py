from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Doctor(models.Model):
    full_name = models.CharField(max_length=160)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.department.name})"


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    patient_id = models.CharField(max_length=20, unique=True, help_text="Unique patient identifier")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=160, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    known_allergies = models.TextField(blank=True, help_text="List any known allergies")
    medical_history = models.TextField(blank=True, help_text="Previous medical conditions and surgeries")
    registration_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
    def __str__(self) -> str:
        return f"{self.patient_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class PatientHealthRecord(models.Model):
    """Time-series health records for patients - designed for data analysis"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_records')
    record_date = models.DateTimeField(default=timezone.now)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='health_records')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='health_records')
    
    # Vital Signs - Numeric fields for analysis
    systolic_bp = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(300)], 
                                      help_text="Systolic blood pressure (mmHg)")
    diastolic_bp = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(200)],
                                      help_text="Diastolic blood pressure (mmHg)")
    heart_rate = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(300)],
                                     help_text="Heart rate (bpm)")
    temperature = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(30), MaxValueValidator(45)],
                                      help_text="Body temperature (°C)")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                 validators=[MinValueValidator(0), MaxValueValidator(500)],
                                 help_text="Weight (kg)")
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                 validators=[MinValueValidator(0), MaxValueValidator(300)],
                                 help_text="Height (cm)")
    
    # Calculated fields for analysis
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                              help_text="Body Mass Index (automatically calculated)")
    
    # Clinical Information
    symptoms = models.TextField(blank=True, help_text="Patient-reported symptoms")
    diagnosis = models.CharField(max_length=255, blank=True, help_text="Diagnosis or condition")
    medications = models.TextField(blank=True, help_text="Medications prescribed")
    notes = models.TextField(blank=True, help_text="Additional clinical notes")
    
    # Metadata for analysis
    visit_type = models.CharField(max_length=50, blank=True, 
                                 help_text="e.g., Routine, Emergency, Follow-up")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-record_date', '-created_at']
        indexes = [
            models.Index(fields=['patient', '-record_date']),
            models.Index(fields=['record_date']),
            models.Index(fields=['department', 'record_date']),
            models.Index(fields=['diagnosis']),
        ]
    
    def __str__(self) -> str:
        return f"Health Record for {self.patient.patient_id} - {self.record_date.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Calculate BMI if weight and height are provided
        if self.weight and self.height:
            height_m = self.height / 100  # Convert cm to meters
            if height_m > 0:
                self.bmi = self.weight / (height_m ** 2)
        super().save(*args, **kwargs)


class Appointment(models.Model):
    patient_name = models.CharField(max_length=160)
    patient_email = models.EmailField()
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='appointments', help_text="Link to patient record if available")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='appointments')
    appointment_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-appointment_date', '-created_at']

    def __str__(self) -> str:
        return f"Appointment: {self.patient_name} with {self.doctor.full_name} on {self.appointment_date}"

# Create your models here.
