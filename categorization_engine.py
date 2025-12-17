"""
Categorization engine using free LLM to categorize news articles.
Supports multiple categories per article.
"""
import os
from typing import List, Dict, Any, Optional
import json
import re


# Define all available categories
CATEGORIES = [
    "binnenland",
    "Buitenland - Europa",
    "buitenland - overig",
    "Misdaad",
    "Huizenmarkt",
    "Economie",
    "bekende Nederlanders",
    "Nationale Politiek",
    "Lokale Politiek",
    "Koningshuis",
    "Technologie",
    "Sport - Voetbal",
    "Sport - Wielrennen",
    "overige sport",
    "Internationale conflicten"
]

# Maximum categories per article
MAX_CATEGORIES = 20


def categorize_article(title: str, description: str = "", content: str = "") -> Dict[str, Any]:
    """
    Categorize an article using LLM or keyword matching.
    
    Args:
        title: Article title
        description: Article description/summary
        content: Full article content (optional)
    
    Returns:
        Dictionary with 'categories' (list) and 'llm' (str) keys
    """
    # First try LLM categorization
    result = _categorize_with_llm(title, description, content)
    
    categories = result.get('categories', []) if isinstance(result, dict) else []
    llm = result.get('llm', None) if isinstance(result, dict) else None
    
    # If LLM fails, fall back to keyword matching
    if not categories:
        categories = _categorize_with_keywords(title, description, content)
        llm = 'Keywords'  # Indicate keyword-based categorization
    
    # Limit to MAX_CATEGORIES
    return {
        'categories': categories[:MAX_CATEGORIES],
        'llm': llm or 'Keywords'
    }


def _categorize_with_llm(title: str, description: str, content: str) -> Dict[str, Any]:
    """Categorize using free LLM APIs. Returns dict with 'categories' and 'llm'."""
    text = f"{title} {description} {content[:1000]}".strip()
    
    # Try different LLM APIs (Hugging Face first - reliable and free)
    hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
    if hf_api_key:
        result = _categorize_with_huggingface(text, title, hf_api_key)
        if result:
            return {'categories': result, 'llm': 'Hugging Face'}
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        result = _categorize_with_groq(text, title, groq_api_key)
        if result:
            return {'categories': result, 'llm': 'Groq'}
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    if openai_api_key:
        result = _categorize_with_openai(text, title, openai_api_key, openai_base_url)
        if result:
            return {'categories': result, 'llm': 'OpenAI'}
    
    # ChatLLM - currently not working
    chatllm_api_key = os.getenv('CHATLLM_API_KEY')
    if chatllm_api_key:
        result = _categorize_with_chatllm(text, title, chatllm_api_key)
        if result:
            return {'categories': result, 'llm': 'ChatLLM'}
    
    return {'categories': [], 'llm': None}


def _categorize_with_chatllm(text: str, title: str, api_key: str) -> Optional[List[str]]:
    """Categorize using ChatLLM API (Aitomatic)."""
    try:
        import requests
        
        categories_list = ", ".join(CATEGORIES)
        
        prompt = f"""Categoriseer dit nieuwsartikel nauwkeurig. Kies ALLEEN categorieën die echt van toepassing zijn. Wees precies en vermijd foutieve categorisatie.

BELANGRIJKE REGELS:
- "Sport - Voetbal": ALLEEN artikelen die SPECIFIEK over voetbal/soccer gaan (wedstrijden, spelers, clubs, competities). NIET voor andere sporten of algemene sportnieuws.
- "Sport - Wielrennen": ALLEEN artikelen over wielrennen/cycling (Tour de France, Giro, wielrenners, koersen). NIET voor andere sporten.
- "overige sport": Alleen als het over sport gaat maar NIET voetbal of wielrennen.
- Wees voorzichtig: een artikel over "sport" in algemene zin is NIET automatisch "Sport - Voetbal".

Beschikbare categorieën met uitleg:
- binnenland: Algemeen Nederlands nieuws zonder specifieke categorie
- Buitenland - Europa: Nieuws over Europese landen (behalve conflicten)
- buitenland - overig: Nieuws over landen buiten Europa (behalve conflicten)
- Misdaad: Criminaliteit, moord, diefstal, rechtspraak
- Huizenmarkt: Woningen, huur, koop, hypotheken, vastgoed
- Economie: Economisch nieuws, inflatie, bedrijven, werkgelegenheid
- bekende Nederlanders: Acteurs, zangers, artiesten, celebrities
- Nationale Politiek: Kabinet, ministers, Tweede Kamer, regering
- Lokale Politiek: Gemeente, burgemeester, gemeenteraad
- Koningshuis: Koning, koningin, prins(es), Oranje
- Technologie: Tech, computers, AI, software, digitale ontwikkelingen
- Sport - Voetbal: ALLEEN specifiek over voetbal (wedstrijden, clubs, spelers, competities)
- Sport - Wielrennen: ALLEEN specifiek over wielrennen (koersen, wielrenners)
- overige sport: Andere sporten (tennis, zwemmen, atletiek, etc.) maar NIET voetbal of wielrennen
- Internationale conflicten: Oorlogen, conflicten (Rusland-Oekraïne, Gaza-Israël, Soedan, etc.)

Artikel:
Titel: {title}
Inhoud: {text[:1500]}

Analyseer het artikel zorgvuldig. Kies alleen categorieën die ECHT van toepassing zijn.
Geef alleen de categorieën terug, gescheiden door komma's. Bijvoorbeeld: "binnenland, Nationale Politiek"
Als geen specifieke categorie past, geef dan "binnenland" terug.

Categorieën:"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een precieze assistent die nieuwsartikelen categoriseert. Wees zeer voorzichtig met sportcategorieën: 'Sport - Voetbal' is ALLEEN voor artikelen die specifiek over voetbal gaan, NIET voor algemene sport of andere sporten. Geef alleen de categorieën terug die echt van toepassing zijn, gescheiden door komma's."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        # Try different API key formats and endpoints
        headers_formats = [
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"},
            {"X-API-Key": api_key, "Content-Type": "application/json"},
            {"api-key": api_key, "Content-Type": "application/json"},
        ]
        
        endpoints = [
            "https://api.chatllm.ai/v1/chat/completions",
            "https://chatllm.ai/api/v1/chat",
            "https://api.aitomatic.com/v1/chat/completions",
            "https://chatllm.aitomatic.com/api/v1/chat",
            "https://api.aitomatic.com/v1/completions",
        ]
        
        for api_url in endpoints:
            for headers in headers_formats:
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_text = None
                        
                        # Try different response formats
                        response_text = None
                        if result:
                            if 'choices' in result and result['choices'] and len(result['choices']) > 0:
                                response_text = result['choices'][0].get('message', {}).get('content', '').strip()
                            elif 'response' in result:
                                response_text = result['response'].strip() if result['response'] else None
                            elif 'text' in result:
                                response_text = result['text'].strip() if result['text'] else None
                            elif 'content' in result:
                                response_text = result['content'].strip() if result['content'] else None
                            elif 'output' in result:
                                response_text = result['output'].strip() if result['output'] else None
                        
                        if response_text:
                            categories = _parse_categories(response_text)
                            if categories:
                                return categories
                    elif response.status_code == 401:
                        continue  # Wrong auth, try next format
                except requests.exceptions.RequestException:
                    continue
                except Exception as e:
                    print(f"ChatLLM categorization error for {api_url}: {e}")
                    continue
    except Exception as e:
        print(f"ChatLLM categorization error: {e}")
    
    return None


def _categorize_with_groq(text: str, title: str, api_key: str) -> Optional[List[str]]:
    """Categorize using Groq API."""
    try:
        import groq
        client = groq.Groq(api_key=api_key)
        
        categories_list = ", ".join(CATEGORIES)
        
        prompt = f"""Categoriseer dit nieuwsartikel nauwkeurig. Kies ALLEEN categorieën die echt van toepassing zijn. Wees precies en vermijd foutieve categorisatie.

BELANGRIJKE REGELS:
- "Sport - Voetbal": ALLEEN artikelen die SPECIFIEK over voetbal/soccer gaan (wedstrijden, spelers, clubs, competities). NIET voor andere sporten of algemene sportnieuws.
- "Sport - Wielrennen": ALLEEN artikelen over wielrennen/cycling (Tour de France, Giro, wielrenners, koersen). NIET voor andere sporten.
- "overige sport": Alleen als het over sport gaat maar NIET voetbal of wielrennen.
- Wees voorzichtig: een artikel over "sport" in algemene zin is NIET automatisch "Sport - Voetbal".

Beschikbare categorieën met uitleg:
- binnenland: Algemeen Nederlands nieuws zonder specifieke categorie
- Buitenland - Europa: Nieuws over Europese landen (behalve conflicten)
- buitenland - overig: Nieuws over landen buiten Europa (behalve conflicten)
- Misdaad: Criminaliteit, moord, diefstal, rechtspraak
- Huizenmarkt: Woningen, huur, koop, hypotheken, vastgoed
- Economie: Economisch nieuws, inflatie, bedrijven, werkgelegenheid
- bekende Nederlanders: Acteurs, zangers, artiesten, celebrities
- Nationale Politiek: Kabinet, ministers, Tweede Kamer, regering
- Lokale Politiek: Gemeente, burgemeester, gemeenteraad
- Koningshuis: Koning, koningin, prins(es), Oranje
- Technologie: Tech, computers, AI, software, digitale ontwikkelingen
- Sport - Voetbal: ALLEEN specifiek over voetbal (wedstrijden, clubs, spelers, competities)
- Sport - Wielrennen: ALLEEN specifiek over wielrennen (koersen, wielrenners)
- overige sport: Andere sporten (tennis, zwemmen, atletiek, etc.) maar NIET voetbal of wielrennen
- Internationale conflicten: Oorlogen, conflicten (Rusland-Oekraïne, Gaza-Israël, Soedan, etc.)

Artikel:
Titel: {title}
Inhoud: {text[:1500]}

Analyseer het artikel zorgvuldig. Kies alleen categorieën die ECHT van toepassing zijn.
Geef alleen de categorieën terug, gescheiden door komma's. Bijvoorbeeld: "binnenland, Nationale Politiek"
Als geen specifieke categorie past, geef dan "binnenland" terug.

Categorieën:"""
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een precieze assistent die nieuwsartikelen categoriseert. Wees zeer voorzichtig met sportcategorieën: 'Sport - Voetbal' is ALLEEN voor artikelen die specifiek over voetbal gaan, NIET voor algemene sport of andere sporten. Geef alleen de categorieën terug die echt van toepassing zijn, gescheiden door komma's."
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
        
        if chat_completion and chat_completion.choices and len(chat_completion.choices) > 0:
            response = chat_completion.choices[0].message.content.strip()
            if response:
                return _parse_categories(response)
        return None
    except Exception as e:
        print(f"Groq categorization error: {e}")
        return None


def _categorize_with_openai(text: str, title: str, api_key: str, base_url: str) -> Optional[List[str]]:
    """Categorize using OpenAI-compatible API."""
    try:
        import requests
        
        categories_list = ", ".join(CATEGORIES)
        
        prompt = f"""Categoriseer dit nieuwsartikel nauwkeurig. Kies ALLEEN categorieën die echt van toepassing zijn. Wees precies en vermijd foutieve categorisatie.

BELANGRIJKE REGELS:
- "Sport - Voetbal": ALLEEN artikelen die SPECIFIEK over voetbal/soccer gaan (wedstrijden, spelers, clubs, competities). NIET voor andere sporten of algemene sportnieuws.
- "Sport - Wielrennen": ALLEEN artikelen over wielrennen/cycling (Tour de France, Giro, wielrenners, koersen). NIET voor andere sporten.
- "overige sport": Alleen als het over sport gaat maar NIET voetbal of wielrennen.
- Wees voorzichtig: een artikel over "sport" in algemene zin is NIET automatisch "Sport - Voetbal".

Beschikbare categorieën met uitleg:
- binnenland: Algemeen Nederlands nieuws zonder specifieke categorie
- Buitenland - Europa: Nieuws over Europese landen (behalve conflicten)
- buitenland - overig: Nieuws over landen buiten Europa (behalve conflicten)
- Misdaad: Criminaliteit, moord, diefstal, rechtspraak
- Huizenmarkt: Woningen, huur, koop, hypotheken, vastgoed
- Economie: Economisch nieuws, inflatie, bedrijven, werkgelegenheid
- bekende Nederlanders: Acteurs, zangers, artiesten, celebrities
- Nationale Politiek: Kabinet, ministers, Tweede Kamer, regering
- Lokale Politiek: Gemeente, burgemeester, gemeenteraad
- Koningshuis: Koning, koningin, prins(es), Oranje
- Technologie: Tech, computers, AI, software, digitale ontwikkelingen
- Sport - Voetbal: ALLEEN specifiek over voetbal (wedstrijden, clubs, spelers, competities)
- Sport - Wielrennen: ALLEEN specifiek over wielrennen (koersen, wielrenners)
- overige sport: Andere sporten (tennis, zwemmen, atletiek, etc.) maar NIET voetbal of wielrennen
- Internationale conflicten: Oorlogen, conflicten (Rusland-Oekraïne, Gaza-Israël, Soedan, etc.)

Artikel:
Titel: {title}
Inhoud: {text[:1500]}

Analyseer het artikel zorgvuldig. Kies alleen categorieën die ECHT van toepassing zijn.
Geef alleen de categorieën terug, gescheiden door komma's. Bijvoorbeeld: "binnenland, Nationale Politiek"
Als geen specifieke categorie past, geef dan "binnenland" terug.

Categorieën:"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een precieze assistent die nieuwsartikelen categoriseert. Wees zeer voorzichtig met sportcategorieën: 'Sport - Voetbal' is ALLEEN voor artikelen die specifiek over voetbal gaan, NIET voor algemene sport of andere sporten. Geef alleen de categorieën terug die echt van toepassing zijn, gescheiden door komma's."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result and 'choices' in result and len(result['choices']) > 0:
                response_text = result['choices'][0].get('message', {}).get('content', '').strip()
                if response_text:
                    return _parse_categories(response_text)
        return None
    except Exception as e:
        print(f"OpenAI categorization error: {e}")
    
    return None


def _categorize_with_huggingface(text: str, title: str, api_key: str) -> Optional[List[str]]:
    """Categorize using Hugging Face zero-shot classification."""
    try:
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(token=api_key)
        
        # Use zero-shot classification model
        model = "facebook/bart-large-mnli"
        
        # Limit categories for API call (HF has limits)
        categories_subset = CATEGORIES[:15]  # Use first 15 categories
        
        text_input = f"{title} {text[:1000]}"
        
        try:
            result = client.zero_shot_classification(
                text_input,
                candidate_labels=categories_subset,
                model=model,
                multi_label=True
            )
            
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
                # Get categories with score > 0.3
                categories_with_scores = list(zip(labels, scores))
                selected = [cat for cat, score in categories_with_scores if score > 0.3]
                
                # Map back to full category list (case-insensitive)
                valid_categories = []
                for selected_cat in selected:
                    for full_cat in CATEGORIES:
                        if selected_cat.lower() == full_cat.lower():
                            valid_categories.append(full_cat)
                            break
                
                if valid_categories:
                    return valid_categories
        except Exception as e:
            # Model might not be available or loading
            pass
            
    except ImportError:
        # Fallback to direct API if library not available
        try:
            import requests
            model = "facebook/bart-large-mnli"
            categories_subset = CATEGORIES[:15]
            text_input = f"{title} {text[:1000]}"
            
            api_url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "inputs": text_input,
                "parameters": {
                    "candidate_labels": categories_subset,
                    "multi_label": True
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                if 'labels' in result and 'scores' in result:
                    categories_with_scores = list(zip(result['labels'], result['scores']))
                    selected = [cat for cat, score in categories_with_scores if score > 0.3]
                    valid_categories = []
                    for selected_cat in selected:
                        for full_cat in CATEGORIES:
                            if selected_cat.lower() == full_cat.lower():
                                valid_categories.append(full_cat)
                                break
                    if valid_categories:
                        return valid_categories
        except Exception:
            pass
    except Exception as e:
        print(f"Hugging Face categorization error: {e}")
    
    return None


def _parse_categories(response: str) -> List[str]:
    """Parse LLM response into list of valid categories."""
    if not response:
        return []
    
    # Split by comma and clean
    categories = [c.strip() for c in response.split(',')]
    
    # Filter to only valid categories
    valid_categories = []
    for cat in categories:
        # Remove quotes if present
        cat = cat.strip('"\'')
        # Check if it matches any category (case-insensitive)
        for valid_cat in CATEGORIES:
            if cat.lower() == valid_cat.lower():
                valid_categories.append(valid_cat)
                break
    
    return valid_categories


def _categorize_with_keywords(title: str, description: str, content: str) -> List[str]:
    """Fallback keyword-based categorization."""
    text = f"{title} {description} {content}".lower()
    categories = []
    
    # Keyword rules (order matters - more specific first)
    
    # Internationale conflicten
    if any(kw in text for kw in ['rusland', 'oekraïne', 'oekraine', 'ukraine', 'gaza', 'israël', 'israel', 'palestina', 'soedan', 'sudan', 'conflict', 'oorlog', 'aanval']):
        categories.append("Internationale conflicten")
    
    # Buitenland - Europa
    if any(kw in text for kw in ['europa', 'eu', 'europese unie', 'brussel', 'frankrijk', 'duitsland', 'spanje', 'italië', 'belgië', 'polen', 'eurozone']):
        categories.append("Buitenland - Europa")
    
    # Buitenland - overig
    if any(kw in text for kw in ['amerika', 'verenigde staten', 'vs', 'china', 'japan', 'australië', 'canada', 'buitenland']):
        if "Buitenland - Europa" not in categories:
            categories.append("buitenland - overig")
    
    # Sport - Voetbal
    if any(kw in text for kw in ['voetbal', 'ajax', 'psv', 'feyenoord', 'eredivisie', 'champions league', 'ek', 'wk voetbal', 'voetballer']):
        categories.append("Sport - Voetbal")
    
    # Sport - Wielrennen
    if any(kw in text for kw in ['wielrennen', 'tour de france', 'giro', 'vuelta', 'wielrenner', 'koers', 'fietsen']):
        categories.append("Sport - Wielrennen")
    
    # overige sport
    if any(kw in text for kw in ['sport', 'olympische', 'atletiek', 'zwemmen', 'tennis', 'hockey', 'basketbal']):
        if "Sport - Voetbal" not in categories and "Sport - Wielrennen" not in categories:
            categories.append("overige sport")
    
    # Koningshuis
    if any(kw in text for kw in ['koning', 'koningin', 'prins', 'prinses', 'beatrix', 'willem-alexander', 'maxima', 'amalia', 'koningshuis', 'oranje']):
        categories.append("Koningshuis")
    
    # bekende Nederlanders
    if any(kw in text for kw in ['acteur', 'actrice', 'zanger', 'zangeres', 'artiest', 'presentator', 'bekende nederlander']):
        categories.append("bekende Nederlanders")
    
    # Nationale Politiek
    if any(kw in text for kw in ['kabinet', 'minister', 'premier', 'tweede kamer', 'eerste kamer', 'regering', 'oppositie', 'coalitie', 'den haag', 'binnenhof']):
        categories.append("Nationale Politiek")
    
    # Lokale Politiek
    if any(kw in text for kw in ['gemeente', 'burgemeester', 'wethouder', 'gemeenteraad', 'lokaal', 'gemeentelijk']):
        categories.append("Lokale Politiek")
    
    # Misdaad
    if any(kw in text for kw in ['moord', 'diefstal', 'inbraak', 'geweld', 'crimineel', 'politie', 'rechter', 'rechtbank', 'cel', 'gevangenis']):
        categories.append("Misdaad")
    
    # Huizenmarkt
    if any(kw in text for kw in ['huis', 'woning', 'huur', 'koop', 'hypotheek', 'vastgoed', 'huizenmarkt', 'woningmarkt', 'huurprijs', 'koopprijs']):
        categories.append("Huizenmarkt")
    
    # Economie
    if any(kw in text for kw in ['economie', 'economisch', 'inflatie', 'prijzen', 'geld', 'bank', 'beurs', 'bedrijf', 'werkgelegenheid', 'werkloosheid']):
        categories.append("Economie")
    
    # Technologie
    if any(kw in text for kw in ['technologie', 'tech', 'computer', 'internet', 'app', 'software', 'ai', 'artificiële intelligentie', 'robot', 'digitale']):
        categories.append("Technologie")
    
    # binnenland (default if nothing else matches)
    if not categories:
        categories.append("binnenland")
    
    return categories


def get_all_categories() -> List[str]:
    """Get list of all available categories."""
    return CATEGORIES.copy()

