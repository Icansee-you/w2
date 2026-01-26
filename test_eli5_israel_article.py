"""
Test script om de ELI5 samenvatting voor het Israël artikel te testen met het verbeterde prompt.
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

from nlp_utils import generate_eli5_summary_nl_with_llm

# Test artikel over Israël
test_title = "Leger Israël: overblijfselen laatste gijzelaar gevonden in Gaza"
test_text = """Het lichaam van de laatste Israëlische gijzelaar is gevonden in Gaza, meldt het Israëlische leger. Gisteren zei premier Netanyahu dat er op een begraafplaats in Noord-Gaza overblijfselen waren gevonden van Ran Gvili, 24, die op 7 oktober werd gedood en meegenomen. Dit was belangrijk voor fase één van het staakt-het-vuren, want alle gijzelaars, levend of overleden, moesten terug. Zijn familie wilde pas verder gaan als zijn lichaam terug was, dus er is met speciale graafapparatuur gezocht. Israël en Hamas geven elkaar de schuld van de vertraging. Bemiddelaars zoals de VS duwen nu voor fase twee: een internationale stabilisatiemacht, een tijdelijke Palestijnse regering en het ontwapenen van Hamas."""

print("=" * 80)
print("TEST ELI5 SAMENVATTING - ISRAËL ARTIKEL")
print("=" * 80)
print(f"\nTitel: {test_title}")
print(f"\nArtikel tekst: {test_text}")
print("\n" + "=" * 80)
print("GENEREREN ELI5 SAMENVATTING MET VERBETERD PROMPT...")
print("=" * 80 + "\n")

try:
    result = generate_eli5_summary_nl_with_llm(test_text, test_title)
    
    if result and isinstance(result, dict):
        summary = result.get('summary', '')
        llm = result.get('llm', 'Onbekend')
        
        print(f"[OK] ELI5 gegenereerd met {llm}")
        print("\n" + "=" * 80)
        print("ELI5 SAMENVATTING:")
        print("=" * 80)
        print(summary)
        print("=" * 80)
        
        # Check voor verbeteringen
        print("\n" + "-" * 80)
        print("CONTROLE:")
        print("-" * 80)
        if "staakt-het-vuren" in summary and "(tijdelijke stop" not in summary:
            print("✓ 'staakt-het-vuren' wordt niet uitgelegd (goed!)")
        else:
            print("✗ 'staakt-het-vuren' wordt uitgelegd (moet niet)")
        
        if "bemiddelaars" not in summary.lower() and "stabilisatiemacht" not in summary.lower():
            print("✓ Complexe termen zoals 'bemiddelaars' en 'stabilisatiemacht' zijn weggelaten (goed!)")
        else:
            print("✗ Complexe termen zijn nog aanwezig (moeten worden weggelaten)")
        
        if "gijzelaar" in summary.lower() and "(iemand die" not in summary.lower():
            print("✓ 'gijzelaar' wordt niet uitgelegd (goed!)")
        else:
            print("? 'gijzelaar' wordt mogelijk uitgelegd")
            
    else:
        print("[ERROR] Geen samenvatting gegenereerd")
        
except Exception as e:
    print(f"[ERROR] Fout bij generatie: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
