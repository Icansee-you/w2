"""
Test Hugging Face Inference API integration directly.
"""
import os
import sys

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_hf_eli5():
    """Test ELI5 generation with Hugging Face."""
    print("=" * 60)
    print("TESTING HUGGING FACE API - ELI5 SUMMARY")
    print("=" * 60)
    
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        print("\n[ERROR] HUGGINGFACE_API_KEY not set!")
        print("Get your API key from: https://huggingface.co/settings/tokens")
        print("Then set it: $env:HUGGINGFACE_API_KEY='your_key_here'")
        return False
    
    print(f"\n[OK] API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(token=api_key)
        
        test_title = "Nederland verhoogt defensie-uitgaven"
        test_text = "Mark Rutte heeft vandaag aangekondigd dat Nederland meer geld gaat uitgeven aan defensie. Dit komt na druk van de NAVO om meer te investeren in militaire capaciteiten."
        
        prompt = f"""Leg dit uit alsof ik 5 ben: {test_title}. {test_text}

Samenvatting (heel simpel, 2-3 zinnen):"""
        
        print(f"\nTest article:")
        print(f"  Title: {test_title}")
        print(f"  Content: {test_text[:100]}...")
        print("\n" + "-" * 60)
        print("Calling Hugging Face API...")
        
        # Try text generation with different models
        models = [
            "google/flan-t5-base",  # Multilingual
            "facebook/bart-large-cnn",  # Summarization
        ]
        
        for model in models:
            try:
                print(f"Trying model: {model}...")
                result = client.text_generation(
                    prompt,
                    model=model,
                    max_new_tokens=150,
                    temperature=0.7
                )
                
                if result and len(result.strip()) > 20:
                    print(f"\n[SUCCESS] ELI5 Summary generated:")
                    print(f"  Model: {model}")
                    print(f"  Summary: {result.strip()}")
                    return True
            except Exception as e:
                error_msg = str(e)[:200]
                if "503" in error_msg or "loading" in error_msg.lower():
                    print(f"  Model is loading, please wait...")
                    print(f"  (This can take 30-60 seconds on first use)")
                else:
                    print(f"  Error: {error_msg}")
        
        # Try summarization task
        try:
            print("Trying summarization task...")
            result = client.summarization(
                f"{test_title}. {test_text}",
                model="facebook/bart-large-cnn"
            )
            
            # Handle different response formats
            summary = None
            if isinstance(result, dict):
                summary = result.get('summary_text') or result.get('summary')
            elif isinstance(result, str):
                summary = result
            elif isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    summary = result[0].get('summary_text') or result[0].get('summary')
                elif isinstance(result[0], str):
                    summary = result[0]
            
            if summary:
                print(f"\n[SUCCESS] ELI5 Summary generated:")
                print(f"  Model: facebook/bart-large-cnn (summarization)")
                print(f"  Summary: {summary}")
                return True
        except Exception as e:
            print(f"  Summarization error: {str(e)[:200]}")
        
        print("\n[FAILED] Could not generate summary")
        print("Possible reasons:")
        print("1. Models are loading (first use takes 30-60 seconds)")
        print("2. API key permissions (try creating token with 'Write' access)")
        print("3. Rate limit exceeded")
        print("4. Network issues")
        
        return False
        
    except ImportError:
        print("\n[ERROR] huggingface_hub library not installed!")
        print("Install it: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"\n[ERROR] Hugging Face API error: {e}")
        return False


def test_hf_categorization():
    """Test categorization with Hugging Face."""
    print("\n" + "=" * 60)
    print("TESTING HUGGING FACE API - CATEGORIZATION")
    print("=" * 60)
    
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        print("\n[ERROR] HUGGINGFACE_API_KEY not set!")
        return False
    
    try:
        from huggingface_hub import InferenceClient
        from categorization_engine import CATEGORIES
        
        client = InferenceClient(token=api_key)
        
        test_title = "Nederland wint van Frankrijk in EK-kwalificatie"
        test_text = "De Nederlandse voetbalploeg heeft vandaag een belangrijke overwinning behaald in de EK-kwalificatie. Door een doelpunt van Memphis Depay in de 89e minuut won Nederland met 2-1 van Frankrijk."
        
        # Use zero-shot classification model
        model = "facebook/bart-large-mnli"
        
        # Convert categories to labels
        labels = CATEGORIES[:10]  # Limit to 10 for testing
        
        text = f"{test_title} {test_text}"
        
        print(f"\nTest article:")
        print(f"  Title: {test_title}")
        print(f"  Content: {test_text[:100]}...")
        print(f"\nTesting with {len(labels)} categories...")
        print("\n" + "-" * 60)
        print("Calling Hugging Face API...")
        
        try:
            result = client.zero_shot_classification(
                text,
                candidate_labels=labels,
                model=model,
                multi_label=True
            )
            
            print(f"\n[SUCCESS] Categorization result:")
            print(f"  Model: {model}")
            
            # Handle different response formats
            labels = []
            scores = []
            
            if isinstance(result, list):
                # New format: list of ZeroShotClassificationOutputElement
                for item in result:
                    if hasattr(item, 'label') and hasattr(item, 'score'):
                        labels.append(item.label)
                        scores.append(item.score)
                    elif isinstance(item, dict):
                        if 'label' in item and 'score' in item:
                            labels.append(item['label'])
                            scores.append(item['score'])
            elif isinstance(result, dict):
                if 'labels' in result and 'scores' in result:
                    labels = result['labels']
                    scores = result['scores']
            
            if labels and scores:
                # Get top categories
                categories_with_scores = list(zip(labels, scores))
                categories_with_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Filter by threshold (0.3)
                selected = [cat for cat, score in categories_with_scores if score > 0.3]
                
                print(f"  Selected categories: {', '.join(selected)}")
                print(f"  All scores:")
                for cat, score in categories_with_scores[:5]:
                    print(f"    {cat}: {score:.2f}")
                
                return len(selected) > 0
            else:
                print(f"  Unexpected response format: {result}")
                return False
        except Exception as e:
            error_msg = str(e)[:300]
            if "503" in error_msg or "loading" in error_msg.lower():
                print(f"[INFO] Model is loading, please wait...")
                print(f"  (This can take 30-60 seconds on first use)")
            else:
                print(f"[ERROR] {error_msg}")
            return False
            
    except ImportError:
        print("\n[ERROR] huggingface_hub library not installed!")
        print("Install it: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"\n[ERROR] Hugging Face API error: {e}")
        return False


def main():
    """Run all Hugging Face tests."""
    print("\n" + "=" * 60)
    print("HUGGING FACE API TEST SUITE")
    print("=" * 60)
    
    eli5_success = test_hf_eli5()
    cat_success = test_hf_categorization()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"ELI5 Generation: {'[PASS]' if eli5_success else '[FAIL]'}")
    print(f"Categorization:  {'[PASS]' if cat_success else '[FAIL]'}")
    
    if eli5_success and cat_success:
        print("\n[SUCCESS] Hugging Face API is working perfectly!")
        print("\nNext steps:")
        print("1. Set HUGGINGFACE_API_KEY in your .env file or environment")
        print("2. Restart your Streamlit app")
        print("3. The app will automatically use Hugging Face for LLM features")
    elif eli5_success or cat_success:
        print("\n[PARTIAL] Some tests passed. Check errors above.")
        print("\nNote: Models may need to load on first use (30-60 seconds)")
    else:
        print("\n[FAILED] Hugging Face API not working. Check:")
        print("1. API key is correct (starts with 'hf_')")
        print("2. Internet connection")
        print("3. Models may be loading (wait and try again)")
        print("4. Rate limit (free tier has limits)")


if __name__ == "__main__":
    main()

