"""
Setup script for Streamlit deployment.
This script initializes the database for Streamlit Cloud deployment.
Run this script once after deploying to Streamlit Cloud.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
import django
django.setup()

from django.core.management import execute_from_command_line
from apps.news.models import Category
from apps.feed_ingest.models import IngestionRun


def setup_database():
    """Initialize database for Streamlit."""
    print("Setting up database for Streamlit...")
    
    # Run migrations
    print("\n1. Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✓ Migrations completed")
    except Exception as e:
        print(f"⚠ Migration warning: {e}")
        print("   Continuing anyway...")
    
    # Initialize categories
    print("\n2. Initializing categories...")
    category_data = [
        ('POLITICS', 'Politiek'),
        ('NATIONAL', 'Nationaal'),
        ('INTERNATIONAL', 'Internationaal'),
        ('SPORT', 'Sport'),
        ('TRUMP', 'Trump'),
        ('RUSSIA', 'Rusland'),
        ('OTHER', 'Overig'),
    ]
    
    created_count = 0
    for key, name in category_data:
        category, created = Category.objects.get_or_create(key=key, defaults={'name': name})
        if created:
            created_count += 1
    
    if created_count > 0:
        print(f"✓ Created {created_count} new categories")
    else:
        print("✓ All categories already exist")
    
    # Try to run init_categories command if available
    try:
        execute_from_command_line(['manage.py', 'init_categories'])
        print("✓ Categories initialized via command")
    except Exception as e:
        # Command might not exist or might fail, that's okay
        pass
    
    # Check if database has articles
    from apps.news.models import Article
    article_count = Article.objects.count()
    print(f"\n3. Database status:")
    print(f"   - Articles: {article_count}")
    print(f"   - Categories: {Category.objects.count()}")
    
    if article_count == 0:
        print("\n⚠ No articles found. To import articles:")
        print("   - Run locally: python manage.py ingest_nos --max-items 100")
        print("   - Or set up Celery/Redis for automatic ingestion")
    else:
        print(f"\n✓ Database ready with {article_count} articles")
    
    print("\n✓ Setup complete!")


if __name__ == "__main__":
    setup_database()

