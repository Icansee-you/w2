"""
Test Groq API integration directly.
"""
import os
import sys

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_groq_eli5():
    """Test ELI5 generation with Groq."""
    print("=" * 60)
    print("TESTING GROQ API - ELI5 SUMMARY")
    print("=" * 60)
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("\n[ERROR] GROQ_API_KEY not set!")
        print("Get your API key from: https://console.groq.com/")
        print("Then set it: $env:GROQ_API_KEY='your_key_here'")
        return False
    
    print(f"\n[OK] API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        import groq
        client = groq.Groq(api_key=api_key)
        
        test_title = "Nederland verhoogt defensie-uitgaven"
        test_text = "Mark Rutte heeft vandaag aangekondigd dat Nederland meer geld gaat uitgeven aan defensie. Dit komt na druk van de NAVO om meer te investeren in militaire capaciteiten."
        
        prompt = f"""Leg dit nieuwsartikel uit alsof ik 5 jaar ben. Gebruik heel eenvoudige Nederlandse woorden die een 5-jarige begrijpt. Gebruik korte zinnen (2-3 zinnen).

BELANGRIJK: Als je namen of woorden met een hoofdletter gebruikt (zoals Mark Rutte, Pornhub, of bedrijfsnamen), leg dan in een paar simpele woorden uit wat dat is. Bijvoorbeeld: "Mark Rutte (dat is de baas van Nederland)" of "Pornhub (dat is een website)". Landen zoals Nederland, Frankrijk, Duitsland hoef je niet uit te leggen.

Titel: {test_title}

Inhoud: {test_text}

Samenvatting:"""
        
        print(f"\nTest article:")
        print(f"  Title: {test_title}")
        print(f"  Content: {test_text[:100]}...")
        print("\n" + "-" * 60)
        print("Calling Groq API...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een vriendelijke assistent die nieuwsartikelen uitlegt aan kinderen van 5 jaar oud. Gebruik altijd heel eenvoudige Nederlandse woorden en korte zinnen. Leg namen en bedrijfsnamen met een hoofdletter uit in simpele woorden (behalve bekende landen zoals Nederland, Frankrijk)."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150
        )
        
        summary = chat_completion.choices[0].message.content.strip()
        
        print(f"\n[SUCCESS] ELI5 Summary generated:")
        print(f"  Model: llama-3.1-8b-instant")
        print(f"  Summary: {summary}")
        return True
        
    except ImportError:
        print("\n[ERROR] Groq library not installed!")
        print("Install it: pip install groq")
        return False
    except Exception as e:
        print(f"\n[ERROR] Groq API error: {e}")
        return False


def test_groq_categorization():
    """Test categorization with Groq."""
    print("\n" + "=" * 60)
    print("TESTING GROQ API - CATEGORIZATION")
    print("=" * 60)
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("\n[ERROR] GROQ_API_KEY not set!")
        return False
    
    try:
        import groq
        from categorization_engine import CATEGORIES, _parse_categories
        
        client = groq.Groq(api_key=api_key)
        
        test_title = "Nederland wint van Frankrijk in EK-kwalificatie"
        test_text = "De Nederlandse voetbalploeg heeft vandaag een belangrijke overwinning behaald in de EK-kwalificatie. Door een doelpunt van Memphis Depay in de 89e minuut won Nederland met 2-1 van Frankrijk."
        
        categories_list = ", ".join(CATEGORIES)
        
        prompt = f"""Categoriseer dit nieuwsartikel. Kies alle categorieën die van toepassing zijn (een artikel kan in meerdere categorieën passen).

Beschikbare categorieën:
{categories_list}

Artikel:
Titel: {test_title}
Inhoud: {test_text[:1500]}

Geef alleen de categorieën terug, gescheiden door komma's. Bijvoorbeeld: "binnenland, Nationale Politiek" of "Buitenland - Europa, Internationale conflicten"
Als geen categorie past, geef dan "binnenland" terug.

Categorieën:"""
        
        print(f"\nTest article:")
        print(f"  Title: {test_title}")
        print(f"  Content: {test_text[:100]}...")
        print("\n" + "-" * 60)
        print("Calling Groq API...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een assistent die nieuwsartikelen categoriseert. Geef alleen de categorieën terug, gescheiden door komma's."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=100
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        categories = _parse_categories(response_text)
        
        print(f"\n[SUCCESS] Categories assigned:")
        print(f"  Model: llama-3.1-8b-instant")
        print(f"  Raw response: {response_text}")
        print(f"  Parsed categories: {', '.join(categories)}")
        return True
        
    except ImportError:
        print("\n[ERROR] Groq library not installed!")
        print("Install it: pip install groq")
        return False
    except Exception as e:
        print(f"\n[ERROR] Groq API error: {e}")
        return False


def main():
    """Run all Groq tests."""
    print("\n" + "=" * 60)
    print("GROQ API TEST SUITE")
    print("=" * 60)
    
    eli5_success = test_groq_eli5()
    cat_success = test_groq_categorization()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"ELI5 Generation: {'[PASS]' if eli5_success else '[FAIL]'}")
    print(f"Categorization:  {'[PASS]' if cat_success else '[FAIL]'}")
    
    if eli5_success and cat_success:
        print("\n[SUCCESS] Groq API is working perfectly!")
        print("\nNext steps:")
        print("1. Set GROQ_API_KEY in your .env file or environment")
        print("2. Restart your Streamlit app")
        print("3. The app will automatically use Groq for LLM features")
    elif eli5_success or cat_success:
        print("\n[PARTIAL] Some tests passed. Check errors above.")
    else:
        print("\n[FAILED] Groq API not working. Check:")
        print("1. API key is correct")
        print("2. Internet connection")
        print("3. Groq library is installed: pip install groq")


if __name__ == "__main__":
    main()

