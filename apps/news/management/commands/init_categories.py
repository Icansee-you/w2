"""
Management command to initialize categories.
Creates all Category objects if they don't exist.
"""
from django.core.management.base import BaseCommand
from apps.news.models import Category


class Command(BaseCommand):
    help = 'Initialize news categories'

    def handle(self, *args, **options):
        categories_data = [
            (Category.POLITICS, 'Politiek'),
            (Category.NATIONAL, 'Nationaal'),
            (Category.INTERNATIONAL, 'Internationaal'),
            (Category.SPORT, 'Sport'),
            (Category.OTHER, 'Overig'),
        ]
        
        created_count = 0
        for key, name in categories_data:
            category, created = Category.objects.get_or_create(
                key=key,
                defaults={'name': name}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Category "{name}" created.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category "{name}" already exists.')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} categories created.')
        )

