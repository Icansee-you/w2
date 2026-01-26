"""
Script om ELI5 samenvattingen te genereren voor de 5 nieuwste artikelen met RouteLLM.
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

# Set RouteLLM API key
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from supabase_client import get_supabase_client
from nlp_utils import generate_eli5_summary_nl_with_llm

def generate_eli5_for_latest_5():
    """Genereer ELI5 samenvattingen voor de 5 nieuwste artikelen."""
    print("=" * 80)
    print("ELI5 SAMENVATTING GENERATIE - 5 NIEUWSTE ARTIKELEN")
    print("=" * 80)
    
    # Check if RouteLLM API key is available
    routellm_api_key = os.getenv('ROUTELLM_API_KEY')
    if not routellm_api_key:
        print("[ERROR] ROUTELLM_API_KEY niet gevonden!")
        return
    
    print(f"[INFO] RouteLLM API key gevonden: {routellm_api_key[:10]}...")
    print(f"[INFO] Haal 5 nieuwste artikelen op...\n")
    
    supabase = get_supabase_client()
    
    try:
        # Get latest articles - check more to find ones without LLM-ELI5
        all_articles = supabase.get_articles(limit=20)
        
        # Filter to find articles without LLM-ELI5
        valid_llms = ['RouteLLM', 'Groq', 'HuggingFace', 'OpenAI', 'ChatLLM']
        articles_to_process = []
        
        for article in all_articles:
            existing_eli5 = article.get('eli5_summary_nl')
            existing_eli5_llm = article.get('eli5_llm', '')
            
            # Include if no ELI5, or ELI5 not from valid LLM
            if not existing_eli5 or existing_eli5_llm not in valid_llms:
                articles_to_process.append(article)
                if len(articles_to_process) >= 5:
                    break
        
        articles = articles_to_process
        
        if not articles:
            print("[WARN] Geen artikelen gevonden.")
            return
        
        print(f"[INFO] {len(articles)} artikelen gevonden. Start ELI5 generatie...\n")
        
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
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
                existing_eli5 = article.get('eli5_summary_nl')
                existing_eli5_llm = article.get('eli5_llm', '')
                
                if not article_id or not title:
                    print(f"  [{i}] [SKIP] Artikel zonder ID of titel")
                    skipped_count += 1
                    continue
                
                # Check if ELI5 already exists and was made by an LLM
                # Valid LLMs: RouteLLM, Groq, HuggingFace, OpenAI, ChatLLM
                valid_llms = ['RouteLLM', 'Groq', 'HuggingFace', 'OpenAI', 'ChatLLM']
                if existing_eli5 and existing_eli5_llm in valid_llms:
                    print(f"  [{i}] [SKIP] Artikel heeft al een LLM-ELI5 ({existing_eli5_llm})")
                    skipped_count += 1
                    continue
                
                if existing_eli5:
                    print(f"  [{i}] [INFO] Artikel heeft een ELI5 maar niet van LLM ({existing_eli5_llm or 'Onbekend'}), wordt herzien")
                
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
                print("\n" + "-" * 80)
                print("GENEREREN ELI5 SAMENVATTING MET ROUTELLM...")
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
                        
                        if not summary:
                            print(f"\n[WARN] Geen samenvatting gegenereerd")
                            error_count += 1
                            continue
                        
                        print(f"\n[OK] ELI5 gegenereerd met {llm}")
                        print("\n" + "=" * 80)
                        print("ELI5 SAMENVATTING:")
                        print("=" * 80)
                        print(summary)
                        print("=" * 80)
                        
                        # Save to database
                        try:
                            supabase.update_article_eli5(article_id, summary, llm)
                            generated_count += 1
                            print(f"\n[OK] ELI5 samenvatting opgeslagen in database")
                        except Exception as save_error:
                            print(f"\n[ERROR] Fout bij opslaan: {save_error}")
                            error_count += 1
                    else:
                        print(f"\n[ERROR] Geen samenvatting gegenereerd")
                        error_count += 1
                        
                except Exception as eli5_error:
                    print(f"\n[ERROR] ELI5 generatie mislukt: {eli5_error}")
                    import traceback
                    traceback.print_exc()
                    error_count += 1
                    
            except Exception as e:
                print(f"  [{i}] [ERROR] Fout bij artikel {article.get('id', 'unknown')}: {e}")
                error_count += 1
                continue
            
            print("\n\n")
        
        print("=" * 80)
        print("RESULTAAT")
        print("=" * 80)
        print(f"  [OK] {generated_count} ELI5 samenvattingen gegenereerd en opgeslagen")
        if error_count > 0:
            print(f"  [WARN] {error_count} artikelen hadden fouten")
        if skipped_count > 0:
            print(f"  [SKIP] {skipped_count} artikelen overgeslagen (hebben al ELI5)")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Fout bij generatie: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    generate_eli5_for_latest_5()
