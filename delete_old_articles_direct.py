"""
Script to directly delete articles older than 72 hours from Supabase.
Uses a more direct approach by fetching article IDs first and then deleting them.
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


def delete_old_articles_direct():
    """Delete articles older than 72 hours using direct approach."""
    print("=" * 80)
    print("VERWIJDER ARTIKELEN OUDER DAN 72 UUR (DIRECT)")
    print("=" * 80)
    print(f"Start tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    print(f"Nu: {datetime.now(pytz.UTC).isoformat()}")
    print()
    
    # Get all article IDs that are older than 72 hours
    print("Ophalen artikel IDs ouder dan 72 uur...")
    article_ids_to_delete = []
    offset = 0
    batch_size = 1000
    
    while True:
        try:
            # Get article IDs with published_at < cutoff_date
            response = supabase.client.table('articles').select('id').lt('published_at', cutoff_date_str).limit(batch_size).offset(offset).execute()
            articles = response.data if response.data else []
            
            if not articles or len(articles) == 0:
                break
            
            article_ids_to_delete.extend([a['id'] for a in articles])
            offset += batch_size
            
            print(f"  Gevonden: {len(article_ids_to_delete)} artikelen...")
            
            if len(articles) < batch_size:
                break
        except Exception as e:
            print(f"  ERROR bij ophalen: {e}")
            break
    
    print(f"Totaal artikelen gevonden om te verwijderen: {len(article_ids_to_delete)}")
    print()
    
    if len(article_ids_to_delete) == 0:
        print("Geen artikelen gevonden die verwijderd moeten worden.")
        return
    
    # Delete articles in batches
    print("Verwijderen artikelen...")
    deleted_count = 0
    batch_size = 100  # Delete in batches of 100
    
    for i in range(0, len(article_ids_to_delete), batch_size):
        batch = article_ids_to_delete[i:i+batch_size]
        try:
            # Delete batch
            response = supabase.client.table('articles').delete().in_('id', batch).execute()
            batch_deleted = len(response.data) if response.data else len(batch)
            deleted_count += batch_deleted
            print(f"  Batch {i//batch_size + 1}: {batch_deleted} artikelen verwijderd (totaal: {deleted_count}/{len(article_ids_to_delete)})")
        except Exception as e:
            print(f"  ERROR bij verwijderen batch {i//batch_size + 1}: {e}")
    
    print()
    print("=" * 80)
    print("VERWIJDERING VOLTOOID")
    print("=" * 80)
    print(f"Eind tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Statistieken:")
    print(f"   Gevonden artikelen: {len(article_ids_to_delete)}")
    print(f"   Verwijderd: {deleted_count}")
    print()


if __name__ == "__main__":
    try:
        delete_old_articles_direct()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
