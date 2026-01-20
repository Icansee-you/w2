"""
Categorization engine using free LLM to categorize news articles.
Supports multiple categories per article.
"""
import os
from typing import List, Dict, Any, Optional
import json
import re


# Define all available categories (synchronized with homepage and user page)
CATEGORIES = [
    "Buitenland",
    "Sport",
    "Bekende personen",
    "Koningshuis",
    "Politiek"
]

# Maximum categories per article
MAX_CATEGORIES = 20


def _get_categorization_prompt(title: str, text: str) -> str:
    """Get standardized categorization prompt for all LLMs."""
    return f"""Categoriseer dit nieuwsartikel nauwkeurig. Kies ALLEEN categorieën die echt van toepassing zijn. Wees precies en vermijd foutieve categorisatie.

Beschikbare categorieën met uitleg:
- Buitenland: Alle nieuws over landen buiten Nederland (Europa, wereldwijd, internationale conflicten, buitenlandse politiek, etc.)
- Sport: Alle sportnieuws (voetbal, wielrennen, tennis, zwemmen, atletiek, Olympische Spelen, etc.)
- Bekende personen: Acteurs, zangers, artiesten, celebrities, bekende Nederlanders, entertainment
- Koningshuis: Koning, koningin, prins(es), Oranje, koninklijke familie, koninklijke evenementen
- Politiek: Alle politieke nieuws (nationaal, lokaal, kabinet, ministers, Tweede Kamer, gemeenteraad, verkiezingen, etc.)

Artikel:
Titel: {title}
Inhoud: {text[:1500]}

Analyseer het artikel zorgvuldig. Kies alleen categorieën die ECHT van toepassing zijn.
Een artikel kan meerdere categorieën hebben. Geef alleen de categorieën terug, gescheiden door komma's. 
Bijvoorbeeld: "Politiek, Buitenland" of "Sport" of "Bekende personen, Koningshuis"
Als geen specifieke categorie past, geef dan geen categorieën terug (lege string).

Categorieën:"""


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
    
    # Import secrets helper
    try:
        from secrets_helper import get_secret
    except ImportError:
        # Fallback if secrets_helper not available
        def get_secret(key, default=None):
            return os.getenv(key, default)
    
    # Try different LLM APIs (Hugging Face first - reliable and free)
    hf_api_key = get_secret('HUGGINGFACE_API_KEY')
    if hf_api_key:
        result = _categorize_with_huggingface(text, title, hf_api_key)
        if result:
            return {'categories': result, 'llm': 'Hugging Face'}
    
    groq_api_key = get_secret('GROQ_API_KEY')
    if groq_api_key:
        result = _categorize_with_groq(text, title, groq_api_key)
        if result:
            return {'categories': result, 'llm': 'Groq'}
    
    openai_api_key = get_secret('OPENAI_API_KEY')
    openai_base_url = get_secret('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    if openai_api_key:
        result = _categorize_with_openai(text, title, openai_api_key, openai_base_url)
        if result:
            return {'categories': result, 'llm': 'OpenAI'}
    
    # ChatLLM - currently not working
    chatllm_api_key = get_secret('CHATLLM_API_KEY')
    if chatllm_api_key:
        result = _categorize_with_chatllm(text, title, chatllm_api_key)
        if result:
            return {'categories': result, 'llm': 'ChatLLM'}
    
    return {'categories': [], 'llm': None}


def _categorize_with_chatllm(text: str, title: str, api_key: str) -> Optional[List[str]]:
    """Categorize using ChatLLM API (Aitomatic)."""
    try:
        import requests
        
        prompt = _get_categorization_prompt(title, text)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een precieze assistent die nieuwsartikelen categoriseert in de volgende categorieën: Buitenland, Sport, Bekende personen, Koningshuis, Politiek. Geef alleen de categorieën terug die echt van toepassing zijn, gescheiden door komma's."
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
        
        prompt = _get_categorization_prompt(title, text)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een precieze assistent die nieuwsartikelen categoriseert in de volgende categorieën: Buitenland, Sport, Bekende personen, Koningshuis, Politiek. Geef alleen de categorieën terug die echt van toepassing zijn, gescheiden door komma's."
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
        
        prompt = _get_categorization_prompt(title, text)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een precieze assistent die nieuwsartikelen categoriseert in de volgende categorieën: Buitenland, Sport, Bekende personen, Koningshuis, Politiek. Geef alleen de categorieën terug die echt van toepassing zijn, gescheiden door komma's."
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
        
        # Use all 5 categories
        categories_subset = CATEGORIES
        
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
            categories_subset = CATEGORIES
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
    
    # Keyword rules for the 5 new categories
    
    # Buitenland
    if any(kw in text for kw in ['buitenland', 'europa', 'eu', 'europese unie', 'brussel', 'frankrijk', 'duitsland', 'spanje', 'italië', 'belgië', 'polen', 'amerika', 'verenigde staten', 'vs', 'china', 'japan', 'australië', 'canada', 'rusland', 'oekraïne', 'oekraine', 'ukraine', 'gaza', 'israël', 'israel', 'palestina', 'soedan', 'sudan', 'conflict', 'oorlog', 'aanval', 'internationaal']):
        categories.append("Buitenland")
    
    # Sport
    if any(kw in text for kw in ['sport', 'voetbal', 'ajax', 'psv', 'feyenoord', 'eredivisie', 'champions league', 'ek', 'wk voetbal', 'voetballer', 'wielrennen', 'tour de france', 'giro', 'vuelta', 'wielrenner', 'koers', 'fietsen', 'olympische', 'atletiek', 'zwemmen', 'tennis', 'hockey', 'basketbal']):
        categories.append("Sport")
    
    # Bekende personen
    if any(kw in text for kw in ['acteur', 'actrice', 'zanger', 'zangeres', 'artiest', 'presentator', 'bekende nederlander', 'celebrity', 'ster', 'bekende']):
        categories.append("Bekende personen")
    
    # Koningshuis
    if any(kw in text for kw in ['koning', 'koningin', 'prins', 'prinses', 'beatrix', 'willem-alexander', 'maxima', 'amalia', 'koningshuis', 'oranje']):
        categories.append("Koningshuis")
    
    # Politiek
    if any(kw in text for kw in ['politiek', 'kabinet', 'minister', 'premier', 'tweede kamer', 'eerste kamer', 'regering', 'oppositie', 'coalitie', 'den haag', 'binnenhof', 'gemeente', 'burgemeester', 'wethouder', 'gemeenteraad', 'lokaal', 'gemeentelijk', 'verkiezing', 'partij']):
        categories.append("Politiek")
    
    return categories


def get_all_categories() -> List[str]:
    """Get list of all available categories."""
    return CATEGORIES.copy()
