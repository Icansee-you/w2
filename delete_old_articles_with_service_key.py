"""
Script to delete articles older than 72 hours using SERVICE_ROLE_KEY if available.
This bypasses Row Level Security (RLS) policies.
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
    from supabase import create_client, Client
except ImportError as e:
    print(f"Error importing supabase: {e}")
    sys.exit(1)


def delete_with_service_key():
    """Delete articles using SERVICE_ROLE_KEY if available."""
    print("=" * 80)
    print("VERWIJDER ARTIKELEN OUDER DAN 72 UUR (MET SERVICE ROLE KEY)")
    print("=" * 80)
    print(f"Start tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Try to get service role key
    try:
        from secrets_helper import get_secret
        supabase_url = get_secret('SUPABASE_URL')
        supabase_service_key = get_secret('SUPABASE_SERVICE_ROLE_KEY')
    except:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url:
        print("ERROR: SUPABASE_URL niet gevonden")
        return
    
    if not supabase_service_key:
        print("WARNING: SUPABASE_SERVICE_ROLE_KEY niet gevonden")
        print("Delete operaties kunnen worden geblokkeerd door Row Level Security (RLS).")
        print()
        print("Opties:")
        print("1. Voeg SUPABASE_SERVICE_ROLE_KEY toe aan je .env bestand")
        print("2. Voer het SQL script 'delete_old_articles_sql.sql' uit in Supabase SQL Editor")
        print()
        return
    
    # Create client with service role key (bypasses RLS)
    try:
        client = create_client(supabase_url, supabase_service_key)
    except Exception as e:
        print(f"ERROR: Fout bij aanmaken Supabase client: {e}")
        return
    
    # Calculate cutoff date (72 hours ago)
    cutoff_date = datetime.now(pytz.UTC) - timedelta(hours=72)
    cutoff_date_str = cutoff_date.isoformat()
    
    print(f"Cutoff datum (72 uur geleden): {cutoff_date_str}")
    print()
    
    # Get article IDs to delete
    print("Ophalen artikel IDs ouder dan 72 uur...")
    article_ids_to_delete = []
    
    try:
        response = client.table('articles').select('id').lt('published_at', cutoff_date_str).execute()
        article_ids_to_delete = [a['id'] for a in (response.data if response.data else [])]
        print(f"  Gevonden: {len(article_ids_to_delete)} artikelen")
    except Exception as e:
        print(f"  ERROR: {e}")
        return
    
    if len(article_ids_to_delete) == 0:
        print("Geen artikelen gevonden om te verwijderen.")
        return
    
    # Delete articles in batches
    print("Verwijderen artikelen...")
    deleted_count = 0
    batch_size = 100
    
    for i in range(0, len(article_ids_to_delete), batch_size):
        batch = article_ids_to_delete[i:i+batch_size]
        try:
            response = client.table('articles').delete().in_('id', batch).execute()
            batch_deleted = len(response.data) if response.data else len(batch)
            deleted_count += batch_deleted
            print(f"  Batch {i//batch_size + 1}: {batch_deleted} artikelen verwijderd (totaal: {deleted_count}/{len(article_ids_to_delete)})")
        except Exception as e:
            print(f"  ERROR bij verwijderen batch {i//batch_size + 1}: {e}")
    
    print()
    print("=" * 80)
    print("VOLTOOID")
    print("=" * 80)
    print(f"Eind tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Statistieken:")
    print(f"   Gevonden artikelen: {len(article_ids_to_delete)}")
    print(f"   Verwijderd: {deleted_count}")
    print()


if __name__ == "__main__":
    try:
        delete_with_service_key()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
