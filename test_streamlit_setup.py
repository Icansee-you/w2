"""Test script to verify Streamlit setup works."""
import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    # Initialize Django
    import django
    django.setup()
    print("✓ Django initialized successfully")
    
    # Test imports
    from apps.news.models import Article, Category
    print("✓ Models imported successfully")
    
    # Test database connection
    category_count = Category.objects.count()
    article_count = Article.objects.count()
    print(f"✓ Database connection successful")
    print(f"  - Categories: {category_count}")
    print(f"  - Articles: {article_count}")
    
    print("\n✓ All tests passed! Streamlit app should work.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

