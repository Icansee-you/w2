"""
Script to delete articles older than 72 hours from Supabase.
"""
import sys
import os
from datetime import datetime

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables directly
    pass

# Import required modules
try:
    from supabase_client import SupabaseClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def delete_old_articles():
    """Delete articles older than 72 hours from Supabase."""
    print("=" * 80)
    print("VERWIJDER ARTIKELEN OUDER DAN 72 UUR")
    print("=" * 80)
    print(f"Start tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize Supabase client
    try:
        supabase = SupabaseClient()
    except Exception as e:
        print(f"ERROR: Fout bij initialiseren Supabase client: {e}")
        return
    
    # Delete articles older than 72 hours
    print("Verwijderen artikelen ouder dan 72 uur...")
    print()
    
    try:
        result = supabase.delete_old_articles(hours_old=72)
        
        if result.get('success'):
            deleted_count = result.get('deleted_count', 0)
            print("=" * 80)
            print("VERWIJDERING VOLTOOID")
            print("=" * 80)
            print(f"Eind tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            print(f"Statistieken:")
            print(f"   Verwijderde artikelen: {deleted_count}")
            print()
        else:
            error = result.get('error', 'Unknown error')
            print("=" * 80)
            print("ERROR")
            print("=" * 80)
            print(f"Fout bij verwijderen: {error}")
            print()
            
    except Exception as e:
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print(f"Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
        print()


if __name__ == "__main__":
    try:
        delete_old_articles()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
