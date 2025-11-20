from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AuditLog,
    Department,
    Doctor,
    DoctorProfile,
    Patient,
    PatientHealthRecord,
    PatientProfile,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Role-based access', {'fields': ('role',)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Role-based access', {'fields': ('role',)}),
    )
    search_fields = ('username', 'email', 'role')


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'full_name', 'specialization', 'user')
    search_fields = ('doctor_id', 'full_name', 'user__username')


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'full_name', 'user')
    search_fields = ('patient_id', 'full_name', 'user__username')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'target', 'details')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "department", "email", "phone")
    list_filter = ("department",)
    search_fields = ("full_name", "email", "phone")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "first_name", "last_name", "gender", "date_of_birth", "email", "registration_date")
    list_filter = ("gender", "blood_type", "registration_date")
    search_fields = ("patient_id", "first_name", "last_name", "email", "phone")
    readonly_fields = ("registration_date",)
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Medical Information', {
            'fields': ('blood_type', 'known_allergies', 'medical_history')
        }),
        ('Metadata', {
            'fields': ('registration_date',)
        }),
    )


@admin.register(PatientHealthRecord)
class PatientHealthRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "record_date", "doctor", "department", "diagnosis", "visit_type", "bmi")
    list_filter = ("department", "doctor", "visit_type", "record_date", "diagnosis")
    search_fields = ("patient__patient_id", "patient__first_name", "patient__last_name", "diagnosis", "symptoms")
    readonly_fields = ("bmi", "created_at")
    fieldsets = (
        ('Patient & Visit Information', {
            'fields': ('patient', 'record_date', 'doctor', 'department', 'visit_type')
        }),
        ('Vital Signs', {
            'fields': ('systolic_bp', 'diastolic_bp', 'heart_rate', 'temperature', 'weight', 'height', 'bmi')
        }),
        ('Clinical Information', {
            'fields': ('symptoms', 'diagnosis', 'medications', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
# Register your models here.
