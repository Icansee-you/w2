"""
Test script to verify LLM integrations for ELI5 summaries and categorization.
"""
import os
import sys

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Environment variables can be set directly

def test_eli5_generation():
    """Test ELI5 summary generation."""
    print("=" * 60)
    print("TESTING ELI5 SUMMARY GENERATION")
    print("=" * 60)
    
    # Import after env is loaded
    from nlp_utils import generate_eli5_summary_nl_with_llm
    
    test_text = """
    Mark Rutte heeft vandaag aangekondigd dat Nederland meer geld gaat uitgeven aan defensie.
    Dit komt na druk van de NAVO om meer te investeren in militaire capaciteiten.
    Het kabinet wil de defensie-uitgaven verhogen naar 2% van het BBP.
    """
    test_title = "Nederland verhoogt defensie-uitgaven"
    
    print(f"\nTest artikel:")
    print(f"Titel: {test_title}")
    print(f"Inhoud: {test_text[:100]}...")
    print("\n" + "-" * 60)
    
    result = generate_eli5_summary_nl_with_llm(test_text, test_title)
    
    if result and result.get('summary'):
        print(f"\n[SUCCESS] ELI5 Summary generated:")
        print(f"  LLM: {result.get('llm', 'Unknown')}")
        print(f"  Summary: {result['summary']}")
        return True
    else:
        print("\n[FAILED] No summary generated")
        return False


def test_categorization():
    """Test article categorization."""
    print("\n" + "=" * 60)
    print("TESTING ARTICLE CATEGORIZATION")
    print("=" * 60)
    
    from categorization_engine import categorize_article
    
    test_text = """
    De Nederlandse voetbalploeg heeft vandaag een belangrijke overwinning behaald in de EK-kwalificatie.
    Door een doelpunt van Memphis Depay in de 89e minuut won Nederland met 2-1 van Frankrijk.
    Dit betekent dat Nederland nu op de tweede plaats staat in de poule.
    """
    test_title = "Nederland wint van Frankrijk in EK-kwalificatie"
    
    print(f"\nTest artikel:")
    print(f"Titel: {test_title}")
    print(f"Inhoud: {test_text[:100]}...")
    print("\n" + "-" * 60)
    
    categories = categorize_article(test_title, test_text, "")
    
    if categories and len(categories) > 0:
        print(f"\n[SUCCESS] Categories assigned:")
        print(f"  Categories: {', '.join(categories)}")
        return True
    else:
        print("\n[FAILED] No categories assigned")
        return False


def check_api_keys():
    """Check which API keys are available."""
    print("\n" + "=" * 60)
    print("CHECKING API KEYS")
    print("=" * 60)
    
    keys = {
        'CHATLLM_API_KEY': os.getenv('CHATLLM_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'HUGGINGFACE_API_KEY': os.getenv('HUGGINGFACE_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    }
    
    available = []
    for key_name, key_value in keys.items():
        if key_value:
            # Show first and last 4 chars for security
            masked = f"{key_value[:4]}...{key_value[-4:]}" if len(key_value) > 8 else "***"
            print(f"  [OK] {key_name}: {masked}")
            available.append(key_name)
        else:
            print(f"  [X] {key_name}: Not set")
    
    return available


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Check API keys
    available_keys = check_api_keys()
    
    if not available_keys:
        print("\n[WARNING] No API keys found!")
        print("   Set at least one of: CHATLLM_API_KEY, GROQ_API_KEY, HUGGINGFACE_API_KEY, OPENAI_API_KEY")
        return
    
    # Test ELI5
    eli5_success = test_eli5_generation()
    
    # Test categorization
    cat_success = test_categorization()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"ELI5 Generation: {'[PASS]' if eli5_success else '[FAIL]'}")
    print(f"Categorization:  {'[PASS]' if cat_success else '[FAIL]'}")
    
    if eli5_success and cat_success:
        print("\n[SUCCESS] All tests passed!")
    elif eli5_success or cat_success:
        print("\n[PARTIAL] Some tests passed, but improvements needed.")
    else:
        print("\n[FAILED] All tests failed. Check API keys and network connection.")


if __name__ == "__main__":
    main()

