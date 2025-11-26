from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class UserManager(DjangoUserManager):
    """Custom manager that injects sensible defaults for our role field."""

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        default_role = getattr(self.model.Roles, 'PATIENT', 'patient')
        extra_fields.setdefault('role', default_role)
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        super_role = getattr(self.model.Roles, 'SUPERADMIN', 'superadmin')
        extra_fields.setdefault('role', super_role)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Primary identity model with opinionated roles."""

    class Roles(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        DOCTOR = 'doctor', 'Doctor'
        PATIENT = 'patient', 'Patient'
        ANALYST = 'analyst', 'Analyst'

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PATIENT,
        help_text="Controls provisioning, profiles, and access policies.",
    )

    objects = UserManager()

    @property
    def is_admin_user(self) -> bool:
        return self.role in {self.Roles.ADMIN, self.Roles.SUPERADMIN}

    @property
    def is_doctor(self) -> bool:
        return self.role == self.Roles.DOCTOR

    @property
    def is_patient(self) -> bool:
        return self.role == self.Roles.PATIENT

    def save(self, *args, **kwargs):
        if self.role in {self.Roles.ADMIN, self.Roles.SUPERADMIN}:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False

        if self.role == self.Roles.SUPERADMIN:
            self.is_superuser = True

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['username']


def _format_profile_id(prefix: str, pk: int) -> str:
    return f"{prefix}{pk:05d}"


class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    full_name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=120, blank=True)
    doctor_id = models.CharField(max_length=8, unique=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.doctor_id})"


class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_account_profile',
    )
    full_name = models.CharField(max_length=255)
    patient_id = models.CharField(max_length=8, unique=True)
    aadhar_number = models.CharField(max_length=12, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.patient_id})"


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_events',
    )
    action = models.CharField(max_length=64)
    target = models.CharField(max_length=150, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['action', '-created_at'])]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} - {self.action} ({self.target})"


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_record',
        null=True,
        blank=True,
        help_text="Link to a doctor login account",
    )
    full_name = models.CharField(max_length=160)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)

    def __str__(self) -> str:
        if self.user:
            return f"{self.full_name} ({self.department.name}) - @{self.user.username}"
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
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='patient_profile',
        help_text="Link to user account for login",
    )
    patient_id = models.CharField(max_length=20, unique=True, help_text="Unique patient identifier")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField()
    PHONE_COUNTRY_CHOICES = [
        ('+91', '+91 (India)'),
        ('+1', '+1 (USA / Canada)'),
        ('+44', '+44 (United Kingdom)'),
        ('+61', '+61 (Australia)'),
        ('+971', '+971 (UAE)'),
    ]
    
    phone_country_code = models.CharField(
        max_length=5,
        choices=PHONE_COUNTRY_CHOICES,
        default='+91',
        help_text="International dialing code, e.g., +91",
    )
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{7,15}$', 'Enter digits only (7-15 characters).')],
    )
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=160, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    known_allergies = models.TextField(blank=True, help_text="List any known allergies")
    medical_history = models.TextField(blank=True, help_text="Previous medical conditions and surgeries")
    aadhar_number = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(r'^\d{12}$', 'Enter a valid 12-digit Aadhar number.')],
        help_text="12-digit national identifier (Aadhar).",
    )
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

