"""
Test script om ELI5 generatie te testen met Groq eerst, dan RouteLLM.
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

# Set API keys for testing
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', '')
os.environ['ROUTELLM_API_KEY'] = 's2_760166137897436c8b1dc5248b05db5a'

from nlp_utils import generate_eli5_summary_nl_with_llm

# Test artikel
test_title = "Koning Willem-Alexander opent nieuw museum in Amsterdam"
test_text = "Koning Willem-Alexander heeft vandaag officieel het nieuwe Rijksmuseum geopend. Het museum toont Nederlandse kunst en geschiedenis. De opening werd bijgewoond door verschillende hoogwaardigheidsbekleders."

print("=" * 80)
print("TEST ELI5 GENERATIE - GROQ EERST, DAN ROUTELLM")
print("=" * 80)
print(f"\nTest artikel:")
print(f"Titel: {test_title}")
print(f"Inhoud: {test_text}")
print("\n" + "=" * 80)
print("GENEREREN ELI5 SAMENVATTING...")
print("=" * 80 + "\n")

try:
    result = generate_eli5_summary_nl_with_llm(test_text, test_title)
    
    if result:
        print("RESULTAAT:")
        print(f"  LLM: {result.get('llm', 'Onbekend')}")
        print(f"  Samenvatting: {result.get('summary', 'Geen')}")
        
        if result.get('llm') == 'Groq':
            print("\n[OK] ELI5 gegenereerd met Groq (eerste keuze)")
        elif result.get('llm') == 'RouteLLM':
            print("\n[OK] ELI5 gegenereerd met RouteLLM (tweede keuze)")
        elif result.get('llm') == 'Failed':
            print("\n[WARN] Beide LLMs faalden - 'failed LLM' teruggegeven")
        else:
            print(f"\n[INFO] Onverwachte LLM: {result.get('llm')}")
    else:
        print("[WARN] Geen resultaat van ELI5 generatie")
        
except Exception as e:
    print(f"[ERROR] Fout bij ELI5 generatie: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
