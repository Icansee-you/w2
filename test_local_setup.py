"""
Test script to verify local setup for Streamlit.
Run this before running streamlit_app.py to check for common issues.
"""
import sys
import os
from pathlib import Path

def check_virtual_env():
    """Check if virtual environment is activated."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("[OK] Virtual environment is activated")
        return True
    else:
        print("[WARNING] Virtual environment doesn't appear to be activated")
        print("  Activate it with: .\\venv\\Scripts\\Activate.ps1 (Windows) or source venv/bin/activate (Mac/Linux)")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'streamlit',
        'django',
        'python-dotenv',
        'pytz',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"[OK] {package} is installed")
        except ImportError:
            print(f"[MISSING] {package} is NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n[WARNING] Missing packages: {', '.join(missing)}")
        print("  Install with: pip install -r requirements.txt")
        return False
    return True

def check_django_setup():
    """Check if Django can be initialized."""
    try:
        BASE_DIR = Path(__file__).resolve().parent
        sys.path.insert(0, str(BASE_DIR))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        
        import django
        django.setup()
        print("[OK] Django can be initialized")
        
        from apps.news.models import Article, Category
        print("[OK] Django models can be imported")
        
        # Check database
        try:
            category_count = Category.objects.count()
            article_count = Article.objects.count()
            print(f"[OK] Database connection works (Categories: {category_count}, Articles: {article_count})")
        except Exception as e:
            print(f"[WARNING] Database issue: {e}")
            print("  Try running: python manage.py migrate")
            return False
        
        return True
    except Exception as e:
        print(f"[ERROR] Django setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("Streamlit Local Setup Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Virtual Environment", check_virtual_env),
        ("Dependencies", check_dependencies),
        ("Django Setup", check_django_setup),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    if all(results):
        print("[SUCCESS] All checks passed! You can run: streamlit run streamlit_app.py")
    else:
        print("[FAILED] Some checks failed. Please fix the issues above before running Streamlit.")
    print("=" * 60)

if __name__ == "__main__":
    main()

