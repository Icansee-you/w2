"""
Debug script om te testen waarom nieuwe artikelen met keywords worden gecategoriseerd.
"""
import sys
import os
from pathlib import Path

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

from secrets_helper import get_secret
from categorization_engine import categorize_article

def test_categorization():
    """Test categorisatie met een voorbeeld artikel."""
    print("=" * 80)
    print("TEST CATEGORISATIE DEBUG")
    print("=" * 80)
    
    # Test API key retrieval
    print("\n[1] Test API key retrieval:")
    routellm_key = get_secret('ROUTELLM_API_KEY')
    groq_key = get_secret('GROQ_API_KEY')
    hf_key = get_secret('HUGGINGFACE_API_KEY')
    
    print(f"   RouteLLM key: {'Gevonden' if routellm_key else 'NIET GEVONDEN'}")
    if routellm_key:
        print(f"   RouteLLM key (first 10): {routellm_key[:10]}...")
    print(f"   Groq key: {'Gevonden' if groq_key else 'NIET GEVONDEN'}")
    print(f"   HuggingFace key: {'Gevonden' if hf_key else 'NIET GEVONDEN'}")
    
    # Test categorisatie met een voorbeeld artikel
    print("\n[2] Test categorisatie met voorbeeld artikel:")
    title = "Nederlandse voetballer scoort winnend doelpunt in Champions League"
    description = "Een Nederlandse voetballer heeft gisteren het winnende doelpunt gescoord in de Champions League wedstrijd."
    content = "De wedstrijd was spannend en eindigde met een 2-1 overwinning voor het Nederlandse team."
    rss_feed_url = "https://feeds.nos.nl/nosnieuwsalgemeen"
    
    print(f"   Titel: {title}")
    print(f"   RSS Feed: {rss_feed_url}")
    print("\n   Categoriseren...")
    
    try:
        result = categorize_article(title, description, content, rss_feed_url=rss_feed_url)
        
        print(f"\n   Resultaat:")
        print(f"   - Main Category: {result.get('main_category')}")
        print(f"   - Sub Categories: {result.get('sub_categories')}")
        print(f"   - Categories: {result.get('categories')}")
        print(f"   - LLM: {result.get('llm')}")
        print(f"   - Argumentatie: {result.get('categorization_argumentation', '')[:100]}...")
        
        if result.get('llm') in ['Keywords', 'Keywords-Fallback', 'Keywords-Error']:
            print("\n   [ERROR] Artikel werd gecategoriseerd met keywords in plaats van LLM!")
        elif result.get('llm') == 'LLM-Failed':
            print("\n   [WARN] LLM categorisatie faalde")
        elif result.get('llm') == 'RouteLLM':
            print("\n   [OK] Artikel werd succesvol gecategoriseerd met RouteLLM")
        elif result.get('llm'):
            print(f"\n   [OK] Artikel werd gecategoriseerd met {result.get('llm')}")
        else:
            print("\n   [WARN] Geen LLM informatie beschikbaar")
            
    except Exception as e:
        print(f"\n   [ERROR] Fout bij categorisatie: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_categorization()
