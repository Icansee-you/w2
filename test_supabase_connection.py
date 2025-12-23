"""
Test script to verify Supabase connection and check if tables exist.
"""
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_supabase_connection():
    """Test Supabase connection and check tables."""
    print("=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    print()
    
    # Check credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("[ERROR] Supabase credentials not found!")
        print()
        print("Please set:")
        print("  SUPABASE_URL=https://skfizxuvxenrltqdwkha.supabase.co")
        print("  SUPABASE_ANON_KEY=your-anon-key")
        print()
        print("Or create a .env file with these values.")
        return False
    
    print(f"[OK] Supabase URL: {supabase_url}")
    print(f"[OK] Anon Key: {supabase_key[:20]}...")
    print()
    
    # Test connection
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        
        print("Testing connection...")
        
        # Try to query articles table
        try:
            response = client.table('articles').select('id').limit(1).execute()
            print("[SUCCESS] Connection successful!")
            print("[SUCCESS] 'articles' table exists and is accessible")
        except Exception as e:
            if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                print("[WARNING] Connection works, but 'articles' table doesn't exist yet")
                print("          You need to run supabase_schema.sql in Supabase SQL Editor")
            else:
                print(f"[WARNING] Connection issue: {e}")
        
        # Try to query user_preferences table
        try:
            response = client.table('user_preferences').select('id').limit(1).execute()
            print("[SUCCESS] 'user_preferences' table exists and is accessible")
        except Exception as e:
            if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                print("[WARNING] 'user_preferences' table doesn't exist yet")
                print("          You need to run supabase_schema.sql in Supabase SQL Editor")
            else:
                print(f"[WARNING] Issue with user_preferences: {e}")
        
        print()
        print("=" * 60)
        print("Connection Test Complete")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. If tables don't exist, run supabase_schema.sql in Supabase SQL Editor")
        print("  2. Then run: .\run_streamlit.ps1")
        print("  3. Test by signing up and importing articles")
        
        return True
        
    except ImportError:
        print("[ERROR] supabase package not installed")
        print("        Run: pip install supabase")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection()

