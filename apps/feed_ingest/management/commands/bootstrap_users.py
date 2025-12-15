"""
Management command to bootstrap initial users.
Creates superuser and user 'chris' with password 'input123'.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Bootstrap initial users (superuser and user chris)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--superuser-username',
            type=str,
            default='admin',
            help='Superuser username (default: admin)'
        )
        parser.add_argument(
            '--superuser-email',
            type=str,
            default='admin@example.com',
            help='Superuser email (default: admin@example.com)'
        )
        parser.add_argument(
            '--superuser-password',
            type=str,
            default=None,
            help='Superuser password (default: prompt)'
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation'
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create superuser
            if not options['skip_superuser']:
                superuser_username = options['superuser_username']
                superuser_email = options['superuser_email']
                superuser_password = options['superuser_password']
                
                if not superuser_password:
                    from getpass import getpass
                    superuser_password = getpass('Superuser password: ')
                
                if User.objects.filter(username=superuser_username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Superuser "{superuser_username}" already exists. Skipping.')
                    )
                else:
                    User.objects.create_superuser(
                        username=superuser_username,
                        email=superuser_email,
                        password=superuser_password
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Superuser "{superuser_username}" created successfully.')
                    )
            
            # Create user 'chris'
            chris_username = 'chris'
            chris_password = 'input123'
            
            if User.objects.filter(username=chris_username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User "{chris_username}" already exists. Skipping.')
                )
            else:
                User.objects.create_user(
                    username=chris_username,
                    password=chris_password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'User "{chris_username}" created successfully with password "input123".')
                )

