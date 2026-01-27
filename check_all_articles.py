"""
Check total number of articles and how many are older than 72 hours.
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


def check_all_articles():
    """Check total articles and how many are older than 72 hours."""
    print("=" * 80)
    print("CONTROLE ALLE ARTIKELEN")
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
    
    # Get total count
    print("Totaal aantal artikelen...")
    try:
        # Get all articles count
        all_articles = []
        offset = 0
        batch_size = 100
        
        while True:
            response = supabase.client.table('articles').select('id, published_at, title').limit(batch_size).offset(offset).execute()
            articles = response.data if response.data else []
            
            if not articles or len(articles) == 0:
                break
            
            all_articles.extend(articles)
            offset += batch_size
            
            if len(articles) < batch_size:
                break
        
        total_count = len(all_articles)
        print(f"  Totaal artikelen: {total_count}")
        
        # Count old articles
        old_count = 0
        old_articles = []
        
        for article in all_articles:
            published_at = article.get('published_at')
            if published_at:
                try:
                    if isinstance(published_at, str):
                        pub_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    else:
                        pub_dt = published_at
                    
                    if pub_dt.tzinfo is None:
                        pub_dt = pytz.UTC.localize(pub_dt)
                    
                    if pub_dt < cutoff_date:
                        old_count += 1
                        if len(old_articles) < 5:
                            old_articles.append({
                                'title': article.get('title', '')[:60],
                                'published_at': published_at
                            })
                except Exception:
                    pass
        
        print(f"  Artikelen ouder dan 72 uur: {old_count}")
        print(f"  Artikelen nieuwer dan 72 uur: {total_count - old_count}")
        
        if old_articles:
            print()
            print("Voorbeelden van oude artikelen:")
            for i, art in enumerate(old_articles, 1):
                print(f"  {i}. {art['title']}... ({art['published_at']})")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()


if __name__ == "__main__":
    try:
        check_all_articles()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
