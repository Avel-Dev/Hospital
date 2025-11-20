from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import AuditLog, DoctorProfile, PatientProfile


User = get_user_model()


class AccountProvisioningTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='AdminPass123',
            role=User.Roles.ADMIN,
        )

    def test_doctor_profile_created_on_shell_user_creation(self):
        """Creating a doctor user via shell should produce a profile with formatted ID."""
        doctor = User.objects.create_user(
            username='drsmith',
            email='drsmith@example.com',
            password='Password123!',
            role=User.Roles.DOCTOR,
        )

        profile = DoctorProfile.objects.get(user=doctor)
        self.assertEqual(profile.doctor_id, f'DOC{doctor.pk:05d}')
        self.assertTrue(doctor.is_doctor)

    def test_patient_profile_created_on_shell_user_creation(self):
        patient_user = User.objects.create_user(
            username='pat-jones',
            email='pat@example.com',
            password='Password123!',
            role=User.Roles.PATIENT,
        )

        profile = PatientProfile.objects.get(user=patient_user)
        self.assertEqual(profile.patient_id, f'PAT{patient_user.pk:05d}')
        self.assertTrue(patient_user.is_patient)

    def test_create_user_view_restricted_to_admin_roles(self):
        url = reverse('core_create_user')
        analyst = User.objects.create_user(
            username='analyst1',
            email='analyst@example.com',
            password='Password123!',
            role=User.Roles.ANALYST,
        )
        self.client.force_login(analyst)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_create_user_view_triggers_password_reset_when_password_missing(self):
        url = reverse('core_create_user')
        self.client.force_login(self.admin)

        payload = {
            'username': 'drnew',
            'email': 'drnew@example.com',
            'role': User.Roles.DOCTOR,
            'is_active': True,
            'password': '',
        }

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        new_user = User.objects.get(username='drnew')
        self.assertFalse(new_user.has_usable_password())

        profile = new_user.doctor_profile
        self.assertEqual(profile.doctor_id, f'DOC{new_user.pk:05d}')

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('drnew@example.com', mail.outbox[0].to)

        log_entry = AuditLog.objects.filter(target='drnew').latest('created_at')
        self.assertFalse(log_entry.details['password_provided'])
        self.assertEqual(log_entry.details['role'], User.Roles.DOCTOR)

    def test_create_user_view_sets_password_when_provided(self):
        url = reverse('core_create_user')
        self.client.force_login(self.admin)

        payload = {
            'username': 'patient1',
            'email': 'patient1@example.com',
            'role': User.Roles.PATIENT,
            'is_active': True,
            'password': 'SecurePass123!',
        }

        self.client.post(url, data=payload)
        user = User.objects.get(username='patient1')
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertTrue(user.patient_account_profile.patient_id.startswith('PAT'))

        log_entry = AuditLog.objects.filter(target='patient1').latest('created_at')
        self.assertTrue(log_entry.details['password_provided'])

