"""
Test script om te zien wat er gebeurt wanneer een nieuw artikel wordt toegevoegd.
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

from articles_repository import fetch_and_upsert_articles

def test_new_article():
    """Test het toevoegen van een nieuw artikel."""
    print("=" * 80)
    print("TEST NIEUW ARTIKEL CATEGORISATIE")
    print("=" * 80)
    
    # Test met een RSS feed
    feed_url = "https://feeds.nos.nl/nosnieuwsalgemeen"
    
    print(f"\n[INFO] Test met feed: {feed_url}")
    print(f"[INFO] Haal maximaal 1 nieuw artikel op...\n")
    
    try:
        result = fetch_and_upsert_articles(
            feed_url,
            max_items=1,
            use_llm_categorization=True
        )
        
        print(f"\n[RESULTAAT]")
        print(f"  Success: {result.get('success')}")
        print(f"  Inserted: {result.get('inserted', 0)}")
        print(f"  Updated: {result.get('updated', 0)}")
        print(f"  Skipped: {result.get('skipped', 0)}")
        
        if result.get('error'):
            print(f"  Error: {result.get('error')}")
        
        # Als er een artikel is toegevoegd, check de categorisatie
        if result.get('inserted', 0) > 0:
            print("\n[INFO] Nieuw artikel toegevoegd - check de database voor categorisatie details")
            print("       (categorization_llm zou 'RouteLLM' moeten zijn, niet 'Keywords')")
        
    except Exception as e:
        print(f"\n[ERROR] Fout bij test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_new_article()
