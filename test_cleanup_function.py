"""
Test script to verify the delete_old_articles database function works.
"""
import sys
import os
from datetime import datetime, timedelta
import pytz

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import required modules
try:
    from supabase_client import SupabaseClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def test_cleanup_function():
    """Test if the delete_old_articles database function works."""
    print("=" * 80)
    print("TEST CLEANUP FUNCTION")
    print("=" * 80)
    print(f"Tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize Supabase client
    try:
        supabase = SupabaseClient()
    except Exception as e:
        print(f"ERROR: Fout bij initialiseren Supabase client: {e}")
        return
    
    # Calculate cutoff date (72 hours ago)
    cutoff_date = datetime.now(pytz.UTC) - timedelta(hours=72)
    cutoff_date_str = cutoff_date.isoformat()
    
    print(f"Cutoff datum (72 uur geleden): {cutoff_date_str}")
    print()
    
    # Count articles before
    print("Stap 1: Tellen hoeveel artikelen ouder dan 72 uur zijn...")
    try:
        count_response = supabase.client.table('articles').select('id', count='exact').lt('published_at', cutoff_date_str).execute()
        count_before = count_response.count if hasattr(count_response, 'count') and count_response.count is not None else 0
        print(f"  Artikelen ouder dan 72 uur: {count_before}")
    except Exception as e:
        print(f"  ERROR bij tellen: {e}")
        count_before = 0
    
    # Try calling the database function
    print()
    print("Stap 2: Aanroepen delete_old_articles() database functie...")
    try:
        response = supabase.client.rpc('delete_old_articles').execute()
        print(f"  Response type: {type(response)}")
        print(f"  Response data: {response.data}")
        
        if response.data is not None:
            deleted_count = response.data
            if isinstance(deleted_count, list) and len(deleted_count) > 0:
                deleted_count = deleted_count[0]
            elif isinstance(deleted_count, dict):
                deleted_count = deleted_count.get('delete_old_articles', 0)
            
            print(f"  Verwijderd: {deleted_count} artikelen")
        else:
            print("  WARNING: Geen data teruggekregen van functie")
            deleted_count = 0
    except Exception as e:
        print(f"  ERROR bij aanroepen functie: {e}")
        import traceback
        traceback.print_exc()
        deleted_count = 0
    
    # Count articles after
    print()
    print("Stap 3: Tellen hoeveel artikelen ouder dan 72 uur zijn na cleanup...")
    try:
        count_response = supabase.client.table('articles').select('id', count='exact').lt('published_at', cutoff_date_str).execute()
        count_after = count_response.count if hasattr(count_response, 'count') and count_response.count is not None else 0
        print(f"  Artikelen ouder dan 72 uur: {count_after}")
    except Exception as e:
        print(f"  ERROR bij tellen: {e}")
        count_after = 0
    
    print()
    print("=" * 80)
    print("RESULTATEN")
    print("=" * 80)
    print(f"Artikelen voor cleanup: {count_before}")
    print(f"Artikelen verwijderd (volgens functie): {deleted_count}")
    print(f"Artikelen na cleanup: {count_after}")
    print(f"Verschil: {count_before - count_after}")
    print()


if __name__ == "__main__":
    try:
        test_cleanup_function()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
