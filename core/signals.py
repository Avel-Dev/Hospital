from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DoctorProfile, PatientProfile, _format_profile_id


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def provision_profiles(sender, instance, created, **kwargs):
    """Provision related profile records when a user is added."""
    if not created:
        return

    full_name = instance.get_full_name() or instance.username

    if instance.role == instance.Roles.DOCTOR:
        DoctorProfile.objects.create(
            user=instance,
            full_name=full_name,
            specialization='General Medicine',
            doctor_id=_format_profile_id('DOC', instance.pk),
        )
    elif instance.role == instance.Roles.PATIENT:
        PatientProfile.objects.create(
            user=instance,
            full_name=full_name,
            patient_id=_format_profile_id('PAT', instance.pk),
        )

