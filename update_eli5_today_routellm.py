"""
Script om ELI5 samenvattingen te updaten voor alle artikelen van vandaag met RouteLLM.
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

# Set RouteLLM API key
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from supabase_client import get_supabase_client
from nlp_utils import generate_eli5_summary_nl_with_llm

def update_eli5_for_today_articles():
    """Update ELI5 samenvattingen voor alle artikelen van vandaag met RouteLLM."""
    print("=" * 80)
    print("ELI5 SAMENVATTING UPDATE - ARTIKELEN VAN VANDAAG")
    print("=" * 80)
    
    # Check if RouteLLM API key is available
    routellm_api_key = os.getenv('ROUTELLM_API_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')
    
    if not routellm_api_key and not groq_api_key:
        print("[ERROR] ROUTELLM_API_KEY of GROQ_API_KEY niet gevonden!")
        return
    
    print(f"[INFO] API keys gevonden")
    if routellm_api_key:
        print(f"       RouteLLM: {routellm_api_key[:10]}...")
    if groq_api_key:
        print(f"       Groq: {groq_api_key[:10]}...")
    
    # Get timezone (Amsterdam)
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')
    now = datetime.now(amsterdam_tz)
    
    # Calculate start of today (00:00:00) and end of today (23:59:59)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    print(f"[INFO] Periode: {today_start.strftime('%Y-%m-%d %H:%M')} - {today_end.strftime('%Y-%m-%d %H:%M')} (Amsterdam tijd)")
    print(f"[INFO] Haal artikelen op...\n")
    
    supabase = get_supabase_client()
    
    try:
        # Get all articles from today
        # Convert to UTC for database query
        today_start_utc = today_start.astimezone(pytz.UTC)
        today_end_utc = today_end.astimezone(pytz.UTC)
        
        # Query articles from today
        response = supabase.client.table('articles').select('*').gte('published_at', today_start_utc.isoformat()).lte('published_at', today_end_utc.isoformat()).order('published_at', desc=True).execute()
        
        articles = response.data if hasattr(response, 'data') else []
        
        if not articles:
            print("[INFO] Geen artikelen gevonden voor vandaag.")
            return
        
        print(f"[INFO] {len(articles)} artikelen gevonden. Start ELI5 update...\n")
        
        generated_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, article in enumerate(articles, 1):
            try:
                article_id = article.get('id')
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('full_content', '')
                published_at = article.get('published_at', '')
                
                if not article_id or not title:
                    print(f"  [{i}] [SKIP] Artikel zonder ID of titel")
                    skipped_count += 1
                    continue
                
                # Format published date for display
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    pub_date_ams = pub_date.astimezone(amsterdam_tz)
                    date_str = pub_date_ams.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = published_at[:10] if published_at else 'Onbekend'
                
                print(f"  [{i}/{len(articles)}] [{date_str}] {title[:60]}...")
                
                # Combine text for ELI5 generation
                text = f"{title}"
                if description:
                    text += f" {description}"
                if content:
                    text += f" {content[:2000]}"  # Limit content to avoid too long prompts
                
                # Generate ELI5 summary (will try Groq first, then RouteLLM)
                try:
                    result = generate_eli5_summary_nl_with_llm(text, title)
                    
                    if result and isinstance(result, dict):
                        summary = result.get('summary', '')
                        llm = result.get('llm', 'Onbekend')
                        
                        # Check if generation failed
                        if summary == 'failed LLM' or llm == 'Failed':
                            print(f"       [WARN] LLM generatie gefaald")
                            error_count += 1
                            continue
                        
                        if not summary:
                            print(f"       [WARN] Geen samenvatting gegenereerd")
                            error_count += 1
                            continue
                        
                        # Save to database
                        try:
                            supabase.update_article_eli5(article_id, summary, llm)
                            generated_count += 1
                            print(f"       [OK] ELI5 gegenereerd met {llm}")
                        except Exception as save_error:
                            print(f"       [ERROR] Fout bij opslaan: {save_error}")
                            error_count += 1
                    else:
                        print(f"       [ERROR] Geen samenvatting gegenereerd")
                        error_count += 1
                        
                except Exception as eli5_error:
                    print(f"       [ERROR] ELI5 generatie mislukt: {eli5_error}")
                    error_count += 1
                    continue
                    
            except Exception as e:
                print(f"  [{i}] [ERROR] Fout bij artikel {article.get('id', 'unknown')}: {e}")
                error_count += 1
                continue
            
            # Progress update every 10 articles
            if i % 10 == 0:
                print(f"\n[PROGRESS] {i}/{len(articles)} artikelen verwerkt ({generated_count} succesvol, {error_count} fouten)\n")
        
        print("\n" + "=" * 80)
        print("RESULTAAT")
        print("=" * 80)
        print(f"  [OK] {generated_count} ELI5 samenvattingen gegenereerd en opgeslagen")
        if error_count > 0:
            print(f"  [WARN] {error_count} artikelen hadden fouten")
        if skipped_count > 0:
            print(f"  [SKIP] {skipped_count} artikelen overgeslagen")
        print(f"  [TOTAAL] {len(articles)} artikelen verwerkt")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Fout bij update: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_eli5_for_today_articles()
