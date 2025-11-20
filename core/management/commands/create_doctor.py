"""
CLI helper to provision doctor accounts with role-aware defaults.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.management.base import BaseCommand

from core.models import AuditLog


User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a doctor user; mirrors the admin web form behavior.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Doctor username/login')
        parser.add_argument('--email', required=True, help='Doctor email')
        parser.add_argument('--full-name', required=True, help='Doctor full name')
        parser.add_argument('--specialization', default='General Medicine')
        parser.add_argument(
            '--password',
            default='',
            help='Optional password. Leave blank to trigger password-reset email.',
        )
        parser.add_argument(
            '--domain',
            default='localhost:8000',
            help='Domain used in password reset emails when password missing.',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        full_name = options['full_name']
        specialization = options['specialization']
        domain = options['domain']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User "{username}" already exists.'))
            return

        name_parts = full_name.strip().split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        user = User(
            username=username,
            email=email,
            role=User.Roles.DOCTOR,
            first_name=first_name,
            last_name=last_name,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()

        profile = getattr(user, 'doctor_profile', None)
        if profile:
            profile.full_name = full_name
            profile.specialization = specialization
            profile.save(update_fields=['full_name', 'specialization'])

        if not password:
            reset_form = PasswordResetForm({'email': user.email})
            if reset_form.is_valid():
                reset_form.save(
                    domain_override=domain,
                    use_https=False,
                )

        AuditLog.objects.create(
            actor=None,
            action='create_user',
            target=user.username,
            details={'role': user.role, 'password_provided': bool(password), 'source': 'create_doctor_cmd'},
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Doctor account "{username}" created with role={user.role} '
                f'({"password set" if password else "password reset email queued"}).'
            )
        )

