"""
Hercategoriseer alleen artikelen met categorization_llm = 'LLM-Failed'.
- Rate limit: 1 artikel per 20 seconden (om LLM-server niet te overbelasten)
- Volgorde: eerst Groq, daarna RouteLLM
- Logt voortgang naar console en logbestand
- Telt aantal Groq en RouteLLM API calls
"""
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from supabase_client import SupabaseClient
    from categorization_engine import (
        categorize_article,
        get_groq_categorization_count,
        get_routellm_categorization_count,
        reset_groq_categorization_counter,
        reset_routellm_categorization_counter,
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def get_llm_failed_articles(supabase) -> List[Dict[str, Any]]:
    """Haal alle artikelen op waar categorization_llm = 'LLM-Failed'."""
    all_articles = []
    offset = 0
    batch_size = 100
    while True:
        response = supabase.client.table('articles').select(
            'id, stable_id, title, description, full_content, rss_feed_url'
        ).eq('categorization_llm', 'LLM-Failed').order('published_at', desc=True).limit(batch_size).offset(offset).execute()
        articles = response.data if response.data else []
        if not articles:
            break
        all_articles.extend(articles)
        offset += batch_size
        if len(articles) < batch_size:
            break
    return all_articles


def update_article_categories(supabase, article_id: str, categorization_result: Dict[str, Any]) -> bool:
    """Update artikel met nieuwe categorisatie (main_category, sub_categories, categories, etc.)."""
    try:
        import pytz
        main_category = categorization_result.get('main_category')
        sub_categories = categorization_result.get('sub_categories', [])
        categories = categorization_result.get('categories', [])
        categorization_llm = categorization_result.get('llm', 'Unknown')
        categorization_argumentation = categorization_result.get('categorization_argumentation', '')

        update_data = {
            'main_category': main_category,
            'sub_categories': sub_categories,
            'categories': categories,
            'categorization_llm': categorization_llm,
            'updated_at': datetime.now(pytz.UTC).isoformat()
        }
        if categorization_argumentation:
            update_data['categorization_argumentation'] = categorization_argumentation

        supabase.client.table('articles').update(update_data).eq('id', article_id).execute()
        return True
    except Exception as e:
        print(f"Error updating article categories: {e}")
        return False


def run_recategorize_llm_failed():
    """Voer hercategorisatie uit voor alle LLM-Failed artikelen."""
    start_time = datetime.now()
    log_filename = f"recategorize_llm_failed_{start_time.strftime('%Y%m%d_%H%M%S')}.log"
    log_lines = []

    def log(msg: str):
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line)
        log_lines.append(line)

    log("=" * 80)
    log("HERCATEGORISATIE LLM-FAILED ARTIKELEN")
    log("   Rate: 1 artikel per 20 seconden | Alleen RouteLLM (Groq overgeslagen)")
    log("=" * 80)

    try:
        supabase = SupabaseClient()
    except Exception as e:
        log(f"ERROR: Supabase client: {e}")
        return

    articles = get_llm_failed_articles(supabase)
    total = len(articles)

    if total == 0:
        log("Geen artikelen met categorization_llm = 'LLM-Failed' gevonden.")
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        return

    log(f"Gevonden: {total} artikelen met LLM-Failed")
    reset_groq_categorization_counter()
    reset_routellm_categorization_counter()
    log("")

    success_count = 0
    error_count = 0

    for idx, article in enumerate(articles, 1):
        if idx > 1:
            log("Wachten 20 seconden...")
            time.sleep(20)

        article_id = article.get('id')
        title = (article.get('title') or 'Geen titel')[:60]
        if not article_id:
            log(f"[{idx}/{total}] SKIP: geen id")
            error_count += 1
            continue

        title_full = article.get('title', '')
        description = article.get('description', '') or article.get('summary', '')
        content = article.get('full_content', '') or description
        rss_feed_url = article.get('rss_feed_url')

        try:
            result = categorize_article(
                title=title_full,
                description=description,
                content=(content or '')[:3000],
                rss_feed_url=rss_feed_url,
                use_only_routellm=True,
            )
        except Exception as e:
            log(f"[{idx}/{total}] ERROR: {title}... -> Exception: {e}")
            error_count += 1
            continue

        main_category = result.get('main_category')
        llm_used = result.get('llm', 'Unknown')

        if main_category and llm_used and llm_used != 'LLM-Failed':
            if update_article_categories(supabase, article_id, result):
                groq_calls = get_groq_categorization_count()
                routellm_calls = get_routellm_categorization_count()
                log(f"[{idx}/{total}] OK: {title}... -> {main_category} (LLM: {llm_used}) [Groq: {groq_calls}, RouteLLM: {routellm_calls}]")
                usage = result.get('_token_usage')
                if usage:
                    pt, ct, tt = usage.get('prompt_tokens'), usage.get('completion_tokens'), usage.get('total_tokens')
                    pts = usage.get('compute_points_used')
                    if pt is not None or ct is not None or tt is not None or pts is not None:
                        log(f"        Tokens: prompt={pt}, completion={ct}, total={tt}, compute_points_used={pts}")
                    else:
                        log(f"        Token usage: {usage}")
                else:
                    log(f"        Token usage: niet beschikbaar in response")
                # Log tokengebruik in Supabase voor per-uur rapportage
                supabase.log_llm_usage(
                    llm=llm_used,
                    call_type='categorization',
                    prompt_tokens=usage.get('prompt_tokens') if usage else None,
                    completion_tokens=usage.get('completion_tokens') if usage else None,
                    total_tokens=usage.get('total_tokens') if usage else None,
                    compute_points_used=usage.get('compute_points_used') if usage else None,
                    article_id=article_id,
                )
                success_count += 1
            else:
                log(f"[{idx}/{total}] ERROR: update mislukt voor {title}...")
                error_count += 1
        else:
            log(f"[{idx}/{total}] MISLUKT: {title}... (LLM: {llm_used})")
            error_count += 1

    # Eindstatistieken
    groq_total = get_groq_categorization_count()
    routellm_total = get_routellm_categorization_count()

    log("")
    log("=" * 80)
    log("RESULTATEN")
    log("=" * 80)
    log(f"Verwerkt: {total} | Succes: {success_count} | Fouten: {error_count}")
    log(f"LLM API calls: Groq {groq_total}, RouteLLM {routellm_total}, Totaal {groq_total + routellm_total}")
    log("=" * 80)

    try:
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        log(f"Log weggeschreven naar: {log_filename}")
    except Exception as e:
        log(f"Logbestand kon niet worden geschreven: {e}")


if __name__ == "__main__":
    try:
        run_recategorize_llm_failed()
    except KeyboardInterrupt:
        print("\n\nScript gestopt door gebruiker (Ctrl+C)")
    except Exception as e:
        print(f"\n\nOnverwachte fout: {e}")
        import traceback
        traceback.print_exc()
