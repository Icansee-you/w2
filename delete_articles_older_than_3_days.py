"""
Script om alle artikelen ouder dan 3 dagen te verwijderen uit Supabase.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from supabase_client import get_supabase_client

def delete_articles_older_than_3_days():
    """Verwijder alle artikelen ouder dan 3 dagen uit Supabase."""
    print("=" * 80)
    print("VERWIJDER ARTIKELEN OUDER DAN 3 DAGEN")
    print("=" * 80)
    
    supabase = get_supabase_client()
    
    try:
        # Bereken 3 dagen geleden (72 uur)
        cutoff_date = datetime.now(pytz.UTC) - timedelta(days=3)
        cutoff_date_str = cutoff_date.isoformat()
        
        print(f"\n[INFO] Verwijder artikelen ouder dan: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"       (3 dagen geleden)\n")
        
        # Haal eerst alle artikelen op die ouder zijn dan 3 dagen
        print("[INFO] Haal artikelen op die ouder zijn dan 3 dagen...")
        response = supabase.client.table('articles').select('id, title, published_at').lt('published_at', cutoff_date_str).execute()
        
        articles_to_delete = response.data if response.data else []
        
        if not articles_to_delete:
            print("[INFO] Geen artikelen gevonden die ouder zijn dan 3 dagen.")
            return
        
        print(f"[INFO] {len(articles_to_delete)} artikelen gevonden die ouder zijn dan 3 dagen.")
        
        # Toon eerste paar artikelen als voorbeeld
        print("\n[INFO] Voorbeeld artikelen die verwijderd worden:")
        for i, article in enumerate(articles_to_delete[:5], 1):
            title = article.get('title', '')[:60]
            published = article.get('published_at', '')[:19] if article.get('published_at') else 'Unknown'
            print(f"  {i}. [{published}] {title}...")
        if len(articles_to_delete) > 5:
            print(f"  ... en {len(articles_to_delete) - 5} meer")
        
        # Verwijder artikelen
        print(f"\n[INFO] Verwijder {len(articles_to_delete)} artikelen...")
        deleted_count = 0
        errors = []
        
        # Verwijder in batches voor betere performance
        batch_size = 100
        for i in range(0, len(articles_to_delete), batch_size):
            batch = articles_to_delete[i:i+batch_size]
            article_ids = [article['id'] for article in batch]
            
            try:
                # Verwijder batch
                supabase.client.table('articles').delete().in_('id', article_ids).execute()
                deleted_count += len(batch)
                print(f"  [OK] Verwijderd: {deleted_count}/{len(articles_to_delete)} artikelen")
            except Exception as e:
                error_msg = f"Fout bij verwijderen batch {i//batch_size + 1}: {e}"
                errors.append(error_msg)
                print(f"  [ERROR] {error_msg}")
        
        print("\n" + "=" * 80)
        print("RESULTAAT")
        print("=" * 80)
        print(f"  [OK] {deleted_count} artikelen succesvol verwijderd")
        if errors:
            print(f"  [WARN] {len(errors)} fouten opgetreden")
            for error in errors:
                print(f"         - {error}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Fout bij verwijderen artikelen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_articles_older_than_3_days()
