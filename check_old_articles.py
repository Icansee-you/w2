"""
Script to check how many articles are older than 72 hours in Supabase.
"""
import sys
import os
from datetime import datetime, timedelta
import pytz

# Load environment variables from .env file (for local development)
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


def check_old_articles():
    """Check how many articles are older than 72 hours."""
    print("=" * 80)
    print("CONTROLE ARTIKELEN OUDER DAN 72 UUR")
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
    print(f"Nu: {datetime.now(pytz.UTC).isoformat()}")
    print()
    
    try:
        # Get all articles (without limit)
        print("Ophalen alle artikelen...")
        all_articles = []
        offset = 0
        batch_size = 100
        
        while True:
            # Try without ordering first to see all articles
            response = supabase.client.table('articles').select('id, published_at, title').limit(batch_size).offset(offset).execute()
            articles = response.data if response.data else []
            
            if not articles or len(articles) == 0:
                break
            
            all_articles.extend(articles)
            offset += batch_size
            
            print(f"  Opgehaald: {len(all_articles)} artikelen...")
            
            if len(articles) < batch_size:
                break
        
        print(f"Totaal artikelen gevonden: {len(all_articles)}")
        print()
        
        # Check which articles are older than 72 hours
        old_articles = []
        articles_without_date = []
        
        for article in all_articles:
            published_at = article.get('published_at')
            if not published_at:
                articles_without_date.append(article)
            else:
                try:
                    # Parse the published_at date
                    if isinstance(published_at, str):
                        # Try parsing ISO format
                        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    else:
                        pub_date = published_at
                    
                    # Make sure it's timezone-aware
                    if pub_date.tzinfo is None:
                        pub_date = pytz.UTC.localize(pub_date)
                    
                    # Check if older than cutoff
                    if pub_date < cutoff_date:
                        old_articles.append({
                            'id': article.get('id'),
                            'title': article.get('title', '')[:60],
                            'published_at': published_at
                        })
                except Exception as e:
                    print(f"Error parsing date for article {article.get('id')}: {e}, date: {published_at}")
        
        print("=" * 80)
        print("RESULTATEN")
        print("=" * 80)
        print(f"Totaal artikelen: {len(all_articles)}")
        print(f"Artikelen ouder dan 72 uur: {len(old_articles)}")
        print(f"Artikelen zonder published_at: {len(articles_without_date)}")
        print()
        
        if old_articles:
            print("Voorbeelden van oude artikelen (eerste 10):")
            for i, article in enumerate(old_articles[:10], 1):
                print(f"  {i}. {article['title']}... (published_at: {article['published_at']})")
            print()
        
        if articles_without_date:
            print(f"Artikelen zonder published_at (eerste 5):")
            for i, article in enumerate(articles_without_date[:5], 1):
                print(f"  {i}. ID: {article.get('id')}, Title: {article.get('title', '')[:60]}...")
            print()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        check_old_articles()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
