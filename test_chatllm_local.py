"""
Test script for ChatLLM API integration (local testing).
Run this to verify ChatLLM API is working before using it in the main app.
"""
import os
import sys
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def test_chatllm_eli5():
    """Test ELI5 summary generation with ChatLLM."""
    print("=" * 60)
    print("Testing ChatLLM API - ELI5 Summary Generation")
    print("=" * 60)
    
    # Set API key if provided as argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        os.environ['CHATLLM_API_KEY'] = api_key
        print(f"Using API key from command line argument")
    else:
        api_key = os.getenv('CHATLLM_API_KEY')
        if not api_key:
            print("[ERROR] CHATLLM_API_KEY not set!")
            print("\nSet it in one of these ways:")
            print("  1. Environment variable: $env:CHATLLM_API_KEY='s2_...'")
            print("  2. Command line: python test_chatllm_local.py s2_...")
            print("  3. Create .env file with: CHATLLM_API_KEY=s2_...")
            return False
        print(f"Using API key from environment: {api_key[:10]}...")
    
    print()
    
    # Test article
    test_title = "Premier Rutte bezoekt Oekraïne voor vredesoverleg"
    test_text = """
    De Nederlandse premier Mark Rutte heeft vandaag Oekraïne bezocht om te praten over vrede.
    Hij sprak met de Oekraïense president over de oorlog met Rusland. Rutte zei dat Nederland
    Oekraïne blijft steunen. De premier wil helpen om een einde te maken aan het conflict.
    """
    
    print(f"Test Article:")
    print(f"  Title: {test_title}")
    print(f"  Content: {test_text.strip()[:100]}...")
    print()
    
    try:
        from nlp_utils import generate_eli5_summary_nl
        
        print("Generating ELI5 summary with ChatLLM...")
        summary = generate_eli5_summary_nl(test_text, test_title)
        
        if summary:
            print("[SUCCESS] ELI5 summary generated!")
            print(f"\nGenerated Summary:")
            print(f"  {summary}")
            return True
        else:
            print("[FAILED] No summary generated")
            print("  ChatLLM API might not be working. Check:")
            print("  - API key is correct")
            print("  - Internet connection")
            print("  - API endpoint is accessible")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chatllm_categorization():
    """Test article categorization with ChatLLM."""
    print("\n" + "=" * 60)
    print("Testing ChatLLM API - Article Categorization")
    print("=" * 60)
    
    api_key = os.getenv('CHATLLM_API_KEY')
    if not api_key:
        print("⚠️  Skipping categorization test (no API key)")
        return False
    
    print()
    
    # Test article
    test_title = "Ajax wint Champions League finale tegen Real Madrid"
    test_description = "Ajax heeft de Champions League finale gewonnen met 3-1 tegen Real Madrid."
    test_content = "In een spannende finale versloeg Ajax Real Madrid met 3-1. De Nederlandse club won voor het eerst sinds 1995."
    
    print(f"Test Article:")
    print(f"  Title: {test_title}")
    print(f"  Description: {test_description}")
    print()
    
    try:
        from categorization_engine import categorize_article
        
        print("Categorizing article with ChatLLM...")
        categories = categorize_article(test_title, test_description, test_content)
        
        if categories:
            print("✅ SUCCESS!")
            print(f"\nAssigned Categories:")
            for cat in categories:
                print(f"  - {cat}")
            return True
        else:
            print("[FAILED] No categories assigned")
            print("  Falling back to keyword matching...")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ChatLLM API Local Test")
    print("=" * 60)
    print()
    
    # Test ELI5
    eli5_success = test_chatllm_eli5()
    
    # Test categorization
    cat_success = test_chatllm_categorization()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"ELI5 Generation: {'[PASSED]' if eli5_success else '[FAILED]'}")
    print(f"Categorization: {'[PASSED]' if cat_success else '[FAILED]'}")
    print()
    
    if eli5_success and cat_success:
        print("[SUCCESS] All tests passed! ChatLLM API is working correctly.")
        print("\nYou can now run the Streamlit app:")
        print("  streamlit run streamlit_app.py")
    elif eli5_success:
        print("[WARNING] ELI5 works, but categorization failed (will use keyword fallback)")
    elif cat_success:
        print("[WARNING] Categorization works, but ELI5 failed (will use other APIs)")
    else:
        print("[ERROR] ChatLLM API is not working. Check:")
        print("  - API key is correct: s2_733cff6da442497eb4f1a5f2e11f9d7a")
        print("  - Internet connection")
        print("  - API endpoint accessibility")
        print("\nThe app will still work using fallback methods.")


if __name__ == "__main__":
    main()

