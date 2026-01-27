"""
Check articles without published_at that might be older than 72 hours.
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


def check_articles_without_published_at():
    """Check articles without published_at."""
    print("=" * 80)
    print("CONTROLE ARTIKELEN ZONDER PUBLISHED_AT")
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
    
    # Get all articles
    print("Ophalen alle artikelen...")
    try:
        all_articles = []
        offset = 0
        batch_size = 100
        
        while True:
            response = supabase.client.table('articles').select('id, published_at, created_at, title').limit(batch_size).offset(offset).execute()
            articles = response.data if response.data else []
            
            if not articles or len(articles) == 0:
                break
            
            all_articles.extend(articles)
            offset += batch_size
            
            if len(articles) < batch_size:
                break
        
        total_count = len(all_articles)
        print(f"  Totaal artikelen: {total_count}")
        
        # Check articles without published_at
        articles_without_pub = []
        old_articles_without_pub = []
        
        for article in all_articles:
            published_at = article.get('published_at')
            created_at = article.get('created_at')
            
            if not published_at:
                articles_without_pub.append(article)
                
                # Check if created_at is older than 72 hours
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            created_dt = created_at
                        
                        if created_dt.tzinfo is None:
                            created_dt = pytz.UTC.localize(created_dt)
                        
                        if created_dt < cutoff_date:
                            old_articles_without_pub.append({
                                'id': article.get('id'),
                                'title': article.get('title', '')[:60],
                                'created_at': created_at
                            })
                    except Exception as e:
                        pass
        
        print(f"  Artikelen zonder published_at: {len(articles_without_pub)}")
        print(f"  Artikelen zonder published_at ouder dan 72 uur: {len(old_articles_without_pub)}")
        
        if old_articles_without_pub:
            print()
            print("Artikelen zonder published_at die ouder zijn dan 72 uur:")
            for i, art in enumerate(old_articles_without_pub[:10], 1):
                print(f"  {i}. {art['title']}... (created_at: {art['created_at']})")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()


if __name__ == "__main__":
    try:
        check_articles_without_published_at()
    except KeyboardInterrupt:
        print("\n\nWARNING: Script gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nERROR: Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
