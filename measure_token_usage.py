"""
Meet gemiddeld tokenverbruik voor 1x categorisatie en 1x ELI5-samenvatting.
Voert een paar sample-calls uit en toont gemiddelde prompt_tokens, completion_tokens en total_tokens.
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from categorization_engine import categorize_article
    from nlp_utils import generate_eli5_summary_nl_with_llm
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Vaste sample-artikelen (realistisch formaat) om tokenverbruik te meten
SAMPLES = [
    {
        "title": "Kabinet komt met nieuw plan voor klimaat",
        "description": "Het kabinet presenteert vandaag een uitgebreid pakket maatregelen om de CO2-uitstoot te verminderen. Experts reageren verdeeld.",
        "content": "Den Haag wil dat Nederland in 2030 de helft minder broeikasgassen uitstoot. Daarvoor zijn nieuwe windparken op zee en meer isolatie van woningen gepland. Oppositie en belangenclubs vinden het plan nog niet ver genoeg.",
    },
    {
        "title": "Politie pakt verdachte op na overval",
        "description": "Een man is aangehouden na een gewapende overval op een filiaal in het centrum. Er raakte niemand gewond.",
        "content": "De overval vond dinsdagmiddag plaats. De verdachte zou met een vuurwapen hebben gedreigd. De politie zoekt nog getuigen.",
    },
    {
        "title": "Nederland wint met 2-1 van Duitsland",
        "description": "Oranje heeft in de voorronde van het EK een zege geboekt op Duitsland. Beide doelpunten vielen in de tweede helft.",
        "content": "Trainer Ronald Koeman was tevreden over de inzet. Volgende week volgt de uitwedstrijd tegen Frankrijk.",
    },
]

NUM_SAMPLES = 3  # aantal calls per type (categorisatie en ELI5)


def main():
    print("=" * 60)
    print("TOKENVERBRUIK METEN")
    print("  Categorisatie: gemiddelde over", NUM_SAMPLES, "calls")
    print("  ELI5:          gemiddelde over", NUM_SAMPLES, "calls")
    print("=" * 60)

    # ---- Categorisatie ----
    cat_usage = []
    for i in range(min(NUM_SAMPLES, len(SAMPLES))):
        s = SAMPLES[i]
        text = f"{s['title']} {s['description']} {s['content']}"[:1500]
        result = categorize_article(
            title=s["title"],
            description=s["description"],
            content=s["content"],
            rss_feed_url=None,
            use_only_routellm=True,
        )
        usage = result.get("_token_usage") if result else None
        if usage and usage.get("total_tokens") is not None:
            cat_usage.append(usage)
            print(f"  Categorisatie {i+1}: total={usage.get('total_tokens')}, prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")
        else:
            print(f"  Categorisatie {i+1}: geen token-usage (API faalde of gaf geen usage)")

    # ---- ELI5 ----
    eli5_usage = []
    for i in range(min(NUM_SAMPLES, len(SAMPLES))):
        s = SAMPLES[i]
        text = f"{s['title']}\n{s['description']}\n{s['content']}"[:3000]
        result = generate_eli5_summary_nl_with_llm(text, s["title"])
        usage = result.get("token_usage") if result else None
        if usage and usage.get("total_tokens") is not None:
            eli5_usage.append(usage)
            print(f"  ELI5 {i+1}: total={usage.get('total_tokens')}, prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")
        else:
            print(f"  ELI5 {i+1}: geen token-usage (API faalde of gaf geen usage)")

    # ---- Gemiddelden ----
    print()
    print("=" * 60)
    print("GEMIDDELDEN (op basis van geslaagde calls)")
    print("=" * 60)

    if cat_usage:
        n = len(cat_usage)
        avg_p = sum(u.get("prompt_tokens") or 0 for u in cat_usage) / n
        avg_c = sum(u.get("completion_tokens") or 0 for u in cat_usage) / n
        avg_t = sum(u.get("total_tokens") or 0 for u in cat_usage) / n
        print(f"  Categorisatie (per artikel, n={n}):")
        print(f"    Gem. prompt_tokens:     {avg_p:.0f}")
        print(f"    Gem. completion_tokens: {avg_c:.0f}")
        print(f"    Gem. total_tokens:      {avg_t:.0f}")
    else:
        print("  Categorisatie: geen data (alle calls faalden of leverden geen usage).")

    if eli5_usage:
        n = len(eli5_usage)
        avg_p = sum(u.get("prompt_tokens") or 0 for u in eli5_usage) / n
        avg_c = sum(u.get("completion_tokens") or 0 for u in eli5_usage) / n
        avg_t = sum(u.get("total_tokens") or 0 for u in eli5_usage) / n
        print(f"  ELI5 samenvatting (per artikel, n={n}):")
        print(f"    Gem. prompt_tokens:     {avg_p:.0f}")
        print(f"    Gem. completion_tokens: {avg_c:.0f}")
        print(f"    Gem. total_tokens:      {avg_t:.0f}")
    else:
        print("  ELI5: geen data (alle calls faalden of leverden geen usage).")

    print()
    print("Let op: groottes hangen af van artikeltekst en welk LLM (Groq/RouteLLM) werd gebruikt.")


if __name__ == "__main__":
    main()
