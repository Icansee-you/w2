"""
Test script voor RouteLLM categorisatie.
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

# Set test API key
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from categorization_engine import categorize_article, _categorize_with_routellm
import os

# Test artikel
test_title = "Koning Willem-Alexander opent nieuw museum in Amsterdam"
test_description = "De koning heeft vandaag een nieuw museum geopend in de hoofdstad."
test_content = "Koning Willem-Alexander heeft vandaag officieel het nieuwe Rijksmuseum geopend. Het museum toont Nederlandse kunst en geschiedenis."

print("=" * 60)
print("TEST ROUTELLM CATEGORISATIE")
print("=" * 60)
print(f"\nTest artikel:")
print(f"Titel: {test_title}")
print(f"Beschrijving: {test_description}")
print("\n" + "=" * 60)
print("Categoriseren met RouteLLM...")
print("=" * 60 + "\n")

try:
    result = categorize_article(
        title=test_title,
        description=test_description,
        content=test_content,
        rss_feed_url=None
    )
    
    if result:
        print("RESULTAAT:")
        print(f"  LLM: {result.get('llm', 'Onbekend')}")
        print(f"  Main Category: {result.get('main_category', 'Geen')}")
        print(f"  Sub Categories: {result.get('sub_categories', [])}")
        print(f"  Categories: {result.get('categories', [])}")
        print(f"  Argumentatie: {result.get('categorization_argumentation', 'Geen')}")
        
        if result.get('llm') == 'RouteLLM':
            print("\n[OK] RouteLLM categorisatie succesvol!")
        else:
            print(f"\n[INFO] Categorisatie gebruikt {result.get('llm')} in plaats van RouteLLM")
    else:
        print("[WARN] Geen resultaat van categorisatie")
        
except Exception as e:
    print(f"[ERROR] Fout bij categorisatie: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
