"""
Test script to check if LLM categorization is working.
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from categorization_engine import categorize_article

# Test article
test_title = "Voetbalwedstrijd tussen Ajax en PSV eindigt in gelijkspel"
test_description = "De wedstrijd tussen Ajax en PSV eindigde in een 2-2 gelijkspel. Beide teams scoorden twee keer."
test_content = "Ajax en PSV speelden een spannende wedstrijd. De uitslag was 2-2."

print("=" * 60)
print("TESTING LLM CATEGORIZATION")
print("=" * 60)

# Check API keys
print("\nChecking API keys:")
hf_key = os.getenv('HUGGINGFACE_API_KEY')
groq_key = os.getenv('GROQ_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')
chatllm_key = os.getenv('CHATLLM_API_KEY')

print(f"  Hugging Face: {'✓ Set' if hf_key else '✗ Not set'}")
print(f"  Groq: {'✓ Set' if groq_key else '✗ Not set'}")
print(f"  OpenAI: {'✓ Set' if openai_key else '✗ Not set'}")
print(f"  ChatLLM: {'✓ Set' if chatllm_key else '✗ Not set'}")

if not any([hf_key, groq_key, openai_key, chatllm_key]):
    print("\n⚠️  WARNING: No LLM API keys found!")
    print("   Categorization will fall back to keyword matching.")
    print("   Set at least one API key in your environment variables.")

print("\n" + "=" * 60)
print("Testing categorization:")
print("=" * 60)
print(f"Title: {test_title}")
print(f"Description: {test_description}")

result = categorize_article(test_title, test_description, test_content)

if isinstance(result, dict):
    categories = result.get('categories', [])
    llm = result.get('llm', 'Unknown')
    print(f"\nResult:")
    print(f"  Categories: {categories}")
    print(f"  LLM used: {llm}")
    
    if llm == 'Keywords':
        print("\n⚠️  WARNING: Keyword-based categorization was used, not LLM!")
        print("   This means either:")
        print("   1. No LLM API keys are configured")
        print("   2. All LLM APIs failed")
    else:
        print(f"\n✓ Successfully used {llm} for categorization!")
else:
    print(f"\nUnexpected result format: {result}")

