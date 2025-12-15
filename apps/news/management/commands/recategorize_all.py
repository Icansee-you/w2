"""
Management command to recategorize all articles using the categorizer.
"""
from django.core.management.base import BaseCommand
from apps.news.models import Article
from apps.news.categorizer import assign_category


class Command(BaseCommand):
    help = 'Recategorize all articles using the categorizer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        articles = Article.objects.all()
        total = articles.count()
        
        self.stdout.write(f'Recategorizing {total} articles...')
        
        recategorized = 0
        unchanged = 0
        
        for article in articles:
            old_category = article.category
            
            new_category = assign_category(
                title=article.title or '',
                summary=article.summary or '',
                content=article.content or ''
            )
            
            if new_category != old_category:
                if not dry_run:
                    article.category = new_category
                    article.save(update_fields=['category'])
                
                recategorized += 1
                self.stdout.write(
                    f'  [{recategorized}/{total}] "{article.title[:60]}..." '
                    f'{old_category.name if old_category else "None"} → '
                    f'{new_category.name if new_category else "None"}'
                )
            else:
                unchanged += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: Would recategorize {recategorized} articles, '
                    f'{unchanged} unchanged'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nRecategorization complete: {recategorized} articles recategorized, '
                    f'{unchanged} unchanged'
                )
            )
