"""
Script to set up external database connection and migrate data.
Run this after configuring DATABASE_URL environment variable.
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
from django.db import connection
from apps.news.models import Article, Category


def setup_external_database():
    """Set up external database connection."""
    print("=" * 60)
    print("External Database Setup")
    print("=" * 60)
    print()
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️  DATABASE_URL not set!")
        print("   Set it in your environment or .env file:")
        print("   DATABASE_URL=postgres://user:password@host:port/database")
        return
    
    print(f"✓ DATABASE_URL is set")
    print(f"  Database: {connection.settings_dict.get('NAME', 'Unknown')}")
    print()
    
    # Test connection
    print("Testing database connection...")
    try:
        connection.ensure_connection()
        print("✓ Database connection successful!")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return
    
    print()
    
    # Run migrations
    print("Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✓ Migrations completed")
    except Exception as e:
        print(f"⚠ Migration warning: {e}")
    
    print()
    
    # Initialize categories
    print("Initializing categories...")
    try:
        execute_from_command_line(['manage.py', 'init_categories'])
        print("✓ Categories initialized")
    except Exception as e:
        print(f"⚠ Category initialization warning: {e}")
        # Try manual creation
        category_data = [
            ('POLITICS', 'Politiek'),
            ('NATIONAL', 'Nationaal'),
            ('INTERNATIONAL', 'Internationaal'),
            ('SPORT', 'Sport'),
            ('TRUMP', 'Trump'),
            ('RUSSIA', 'Rusland'),
            ('OTHER', 'Overig'),
        ]
        for key, name in category_data:
            Category.objects.get_or_create(key=key, defaults={'name': name})
        print("✓ Categories created manually")
    
    print()
    
    # Check current data
    article_count = Article.objects.count()
    category_count = Category.objects.count()
    
    print("Database Status:")
    print(f"  - Articles: {article_count}")
    print(f"  - Categories: {category_count}")
    print()
    
    if article_count == 0:
        print("⚠ No articles found.")
        print("   To import articles, run:")
        print("   python manage.py ingest_nos --max-items 100")
    else:
        print("✓ Database is ready with articles!")
        print()
        print("Articles by category:")
        for category in Category.objects.all():
            count = Article.objects.filter(category=category).count()
            print(f"  - {category.name}: {count}")
    
    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    setup_external_database()

