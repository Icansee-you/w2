"""
Test script om ELI5 samenvattingen te genereren met RouteLLM voor de 5 nieuwste artikelen.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
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

# Set RouteLLM API key (tijdelijk voor test)
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from supabase_client import get_supabase_client
from nlp_utils import generate_eli5_summary_nl_with_llm

def test_eli5_for_latest_articles(limit: int = 5):
    """Test ELI5 generatie voor de nieuwste artikelen."""
    print("=" * 80)
    print("ELI5 SAMENVATTING TEST - ROUTELLM")
    print("=" * 80)
    
    # Check if RouteLLM API key is available
    routellm_api_key = os.getenv('ROUTELLM_API_KEY')
    if not routellm_api_key:
        print("[ERROR] ROUTELLM_API_KEY niet gevonden!")
        return
    
    print(f"[INFO] RouteLLM API key gevonden: {routellm_api_key[:10]}...")
    print(f"[INFO] Haal {limit} nieuwste artikelen op...\n")
    
    supabase = get_supabase_client()
    
    try:
        # Get latest articles
        articles = supabase.get_articles(limit=limit)
        
        if not articles:
            print("[WARN] Geen artikelen gevonden.")
            return
        
        print(f"[INFO] {len(articles)} artikelen gevonden. Start ELI5 generatie...\n")
        
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        
        for i, article in enumerate(articles, 1):
            try:
                article_id = article.get('id')
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('full_content', '')
                published_at = article.get('published_at', '')
                
                if not article_id or not title:
                    print(f"  [{i}] [SKIP] Artikel zonder ID of titel")
                    continue
                
                # Format published date for display
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    pub_date_ams = pub_date.astimezone(amsterdam_tz)
                    date_str = pub_date_ams.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = published_at[:10] if published_at else 'Onbekend'
                
                print("=" * 80)
                print(f"ARTIKEL {i}/{len(articles)}")
                print("=" * 80)
                print(f"Titel: {title}")
                print(f"Datum: {date_str}")
                print(f"\nBeschrijving: {description[:200]}..." if description else "Geen beschrijving")
                print("\n" + "-" * 80)
                print("GENEREREN ELI5 SAMENVATTING...")
                print("-" * 80)
                
                # Combine text for ELI5 generation
                text = f"{title}"
                if description:
                    text += f" {description}"
                if content:
                    text += f" {content[:2000]}"  # Limit content to avoid too long prompts
                
                # Generate ELI5 summary
                try:
                    result = generate_eli5_summary_nl_with_llm(text, title)
                    
                    if result and isinstance(result, dict):
                        summary = result.get('summary', '')
                        llm = result.get('llm', 'Onbekend')
                        
                        print(f"\n[OK] ELI5 gegenereerd met {llm}")
                        print("\n" + "=" * 80)
                        print("ELI5 SAMENVATTING:")
                        print("=" * 80)
                        print(summary)
                        print("=" * 80)
                        
                        if llm != 'RouteLLM':
                            print(f"\n[WARN] Gebruikt {llm} in plaats van RouteLLM")
                    else:
                        print(f"\n[ERROR] Geen samenvatting gegenereerd")
                        
                except Exception as eli5_error:
                    print(f"\n[ERROR] ELI5 generatie mislukt: {eli5_error}")
                    import traceback
                    traceback.print_exc()
                    
            except Exception as e:
                print(f"  [{i}] [ERROR] Fout bij artikel {article.get('id', 'unknown')}: {e}")
                continue
            
            print("\n\n")
        
        print("=" * 80)
        print("TEST VOLTOOID")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Fout bij test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_eli5_for_latest_articles(limit=5)
