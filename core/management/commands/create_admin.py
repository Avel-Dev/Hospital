"""
Django management command to create an admin user.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates an admin user with default credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for admin account (default: admin)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for admin account (default: admin123)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@hospital.com',
            help='Email for admin account (default: admin@hospital.com)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists. Skipping creation.')
            )
            return

        # Create superuser tied to superadmin role
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Roles.SUPERADMIN,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created admin user!\n'
                f'  Username: {username}\n'
                f'  Password: {password}\n'
                f'  Email: {email}\n\n'
                f'⚠️  IMPORTANT: Change the password after first login!'
            )
        )


