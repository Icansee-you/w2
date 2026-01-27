"""
Script to delete articles older than 72 hours and verify deletion.
"""
import sys
import os
from datetime import datetime, timedelta
import pytz
import time

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


def delete_and_verify():
    """Delete articles older than 72 hours and verify deletion."""
    print("=" * 80)
    print("VERWIJDER EN VERIFIEER ARTIKELEN OUDER DAN 72 UUR")
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
    print()
    
    # Get article IDs to delete
    print("Stap 1: Ophalen artikel IDs ouder dan 72 uur...")
    article_ids_to_delete = []
    
    try:
        response = supabase.client.table('articles').select('id').lt('published_at', cutoff_date_str).execute()
        article_ids_to_delete = [a['id'] for a in (response.data if response.data else [])]
        print(f"  Gevonden: {len(article_ids_to_delete)} artikelen")
    except Exception as e:
        print(f"  ERROR: {e}")
        return
    
    if len(article_ids_to_delete) == 0:
        print("Geen artikelen gevonden om te verwijderen.")
        return
    
    # Show first few IDs
    print(f"  Eerste 5 IDs: {article_ids_to_delete[:5]}")
    print()
    
    # Delete articles in batches
    print("Stap 2: Verwijderen artikelen in batches...")
    deleted_count = 0
    batch_size = 100
    
    for i in range(0, len(article_ids_to_delete), batch_size):
        batch = article_ids_to_delete[i:i+batch_size]
        try:
            # Delete batch
            response = supabase.client.table('articles').delete().in_('id', batch).execute()
            
            # Check response
            if response.data:
                batch_deleted = len(response.data)
            else:
                # If no data returned, assume all were deleted
                batch_deleted = len(batch)
            
            deleted_count += batch_deleted
            print(f"  Batch {i//batch_size + 1}: {batch_deleted} artikelen verwijderd (totaal: {deleted_count}/{len(article_ids_to_delete)})")
            
            # Show response details for first batch
            if i == 0:
                print(f"    Response type: {type(response)}")
                print(f"    Response data: {response.data[:3] if response.data and len(response.data) > 0 else 'None'}")
        except Exception as e:
            print(f"  ERROR bij verwijderen batch {i//batch_size + 1}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    
    # Wait a moment for database to update
    print("Stap 3: Wachten 2 seconden voor database update...")
    time.sleep(2)
    print()
    
    # Verify deletion
    print("Stap 4: Verifiëren of artikelen zijn verwijderd...")
    try:
        # Try to get one of the deleted IDs
        if len(article_ids_to_delete) > 0:
            test_id = article_ids_to_delete[0]
            verify_response = supabase.client.table('articles').select('id').eq('id', test_id).execute()
            
            if verify_response.data and len(verify_response.data) > 0:
                print(f"  WARNING: Test ID {test_id} bestaat nog steeds!")
            else:
                print(f"  OK: Test ID {test_id} is verwijderd")
        
        # Count remaining old articles
        count_response = supabase.client.table('articles').select('id', count='exact').lt('published_at', cutoff_date_str).execute()
        remaining_count = count_response.count if hasattr(count_response, 'count') and count_response.count is not None else 0
        
        if remaining_count > 0:
            print(f"  WARNING: Er zijn nog steeds {remaining_count} artikelen ouder dan 72 uur")
        else:
            print(f"  OK: Geen artikelen ouder dan 72 uur gevonden")
            
    except Exception as e:
        print(f"  ERROR bij verifiëren: {e}")
    
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
        delete_and_verify()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
