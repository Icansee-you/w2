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
    "Koningshuis",
    "Misdaad",
    "Sport",
    "Politiek",
    "Buitenland",
    "Cultuur",
    "Opmerkelijk",
    "Algemeen"
]

# RSS Feed overrides - these feeds force a specific main_category
RSS_FEED_OVERRIDES = {
    "https://feeds.nos.nl/nosnieuwsbuitenland": "Buitenland",
    "https://feeds.nos.nl/nosnieuwspolitiek": "Politiek",
    "https://feeds.nos.nl/nosnieuwsopmerkelijk": "Opmerkelijk",
    "https://feeds.nos.nl/nosnieuwskoningshuis": "Koningshuis",
    "https://feeds.nos.nl/nossportalgemeen": "Sport"
}

# Maximum categories per article
MAX_CATEGORIES = 20

# Global counter for RouteLLM API calls (categorization)
_routellm_categorization_calls = 0


def get_routellm_categorization_count() -> int:
    """Get the number of RouteLLM API calls for categorization."""
    return _routellm_categorization_calls


def reset_routellm_categorization_counter():
    """Reset RouteLLM categorization API call counter."""
    global _routellm_categorization_calls
    _routellm_categorization_calls = 0


def _get_categorization_prompt(title: str, text: str, rss_feed_url: str = None) -> str:
    """Get standardized categorization prompt for all LLMs with new main_category/sub_categories system."""
    # Check if RSS feed has override
    forced_main_category = None
    if rss_feed_url:
        forced_main_category = RSS_FEED_OVERRIDES.get(rss_feed_url)
    
    prompt = """SYSTEEMROL
Je bent een data-analist gespecialiseerd in media. Je taak is het categoriseren van Nederlandse nieuwsartikelen op basis van hun inhoud en de RSS-feed URL waar het artikel vandaan komt.

Categorisatie-regels
Main Category (exact één kiezen)
Kies precies één main_category uit deze lijst, in deze volgorde van prioriteit (tenzij een RSS-override geldt; zie punt 4):
Koningshuis
Misdaad
Sport
Politiek
Buitenland
Cultuur
Opmerkelijk
Algemeen (default als niets anders past)

Sub Categories (0 of meer extra labels)
Kies sub_categories als extra labels uit exact dezelfde lijst. Subcategorieën zijn aanvullend; ze hoeven niet hetzelfde te zijn als de main_category.

BELANGRIJK: "Algemeen" kan NOOIT een sub_categorie zijn. Als main_category "Algemeen" is, geef dan GEEN sub_categories. Als main_category iets anders is (bijv. Sport, Politiek), gebruik dan NOOIT "Algemeen" als sub_categorie.

Inhoudelijke beslisregels (vooral relevant bij algemene feeds)
- Onderwerp > locatie: als het onderwerp primair Sport/Politiek/Koningshuis/Misdaad is, kies dat boven Buitenland.
- Opmerkelijk-regel: als het artikel alleen nieuwswaardig is door het vreemde/grappige/ongewone aspect, kies Opmerkelijk als main_category (ook als het zich in sport/politiek afspeelt).
- Politiek: gebruik Politiek alleen voor Nederlandse politiek/beleid. Buitenlandse politiek valt onder Buitenland (en krijgt géén Politiek als subcategory puur omdat het politiek is).
- Misdaad: vandalisme, aanslagen, rechtszaken, drugscircuit, cybercrime, etc. (ook als het zich afspeelt in cultuur- of sportcontext).
- Koningshuis: nieuws over alle leden van het Nederlandse Koningshuis.

RSS-feed override (main_category is vast en moet je overnemen)
"""
    
    if forced_main_category:
        prompt += f"\n⚠️ BELANGRIJK: Dit artikel komt uit een feed die main_category forceert.\n"
        prompt += f"Feed: {rss_feed_url} → main_category MOET exact '{forced_main_category}' zijn.\n"
        prompt += f"Bepaal in dat geval nog wél sub_categories op basis van de tekst.\n"
    else:
        prompt += "\nGeen RSS-feed override. Bepaal main_category op basis van de tekst.\n"
    
    prompt += f"""
Artikel:
Titel: {title}
Inhoud: {text[:1500]}
RSS Feed URL: {rss_feed_url or 'Onbekend'}

Output-format (plain text):
Main Category: [Categorie]
Sub Categories: [Categorie 1, Categorie 2, ...] of Geen
Argumentatie: [Max 2 zinnen totaal]

Geef je antwoord in exact dit formaat."""
    
    return prompt


def categorize_article(title: str, description: str = "", content: str = "", rss_feed_url: str = None) -> Dict[str, Any]:
    """
    Categorize an article using LLM or keyword matching.
    
    Args:
        title: Article title
        description: Article description/summary
        content: Full article content (optional)
        rss_feed_url: RSS feed URL where article came from (for override logic)
    
    Returns:
        Dictionary with 'categories' (list), 'main_category' (str), 'sub_categories' (list), 
        'categorization_argumentation' (str), and 'llm' (str) keys
    """
    # Check RSS feed override
    forced_main_category = None
    if rss_feed_url:
        forced_main_category = RSS_FEED_OVERRIDES.get(rss_feed_url)
    
    # First try LLM categorization
    result = _categorize_with_llm(title, description, content, rss_feed_url)
    
    main_category = result.get('main_category')
    sub_categories = result.get('sub_categories', [])
    categories = result.get('categories', [])
    argumentation = result.get('categorization_argumentation', '')
    llm = result.get('llm', None) if isinstance(result, dict) else None
    
    # Apply RSS feed override if needed
    if forced_main_category:
        main_category = forced_main_category
        # Keep sub_categories from LLM, but ensure main_category is not in sub_categories
        # Also remove "Algemeen" from sub_categories (it should never be there)
        if main_category in sub_categories:
            sub_categories = [c for c in sub_categories if c != main_category]
        if main_category == 'Algemeen':
            sub_categories = []
        else:
            sub_categories = [c for c in sub_categories if c != 'Algemeen']
    
    # If LLM fails completely, we should NOT fall back to keywords
    # Instead, return a default category and mark it as failed
    if not main_category and not categories:
        print(f"[WARN] All LLM categorization failed for article: {title[:50]}...")
        # Use 'Algemeen' as default, but mark it clearly
        main_category = 'Algemeen'
        categories = ['Algemeen']
        sub_categories = []
        argumentation = 'LLM categorisatie faalde - standaard categorie gebruikt'
        llm = 'LLM-Failed'  # Indicate that LLM failed, not keyword-based
    
    # Remove "Algemeen" from sub_categories if present (it should never be there)
    # Also, if main_category is "Algemeen", ensure sub_categories is empty
    if main_category == 'Algemeen':
        sub_categories = []
    else:
        # Remove "Algemeen" from sub_categories if it somehow got in there
        sub_categories = [c for c in sub_categories if c != 'Algemeen']
    
    # Combine main_category and sub_categories into categories list for backward compatibility
    # IMPORTANT: Never include "Algemeen" in categories if it's not the main_category
    if main_category:
        all_categories = [main_category]
        if sub_categories:
            # Only add sub_categories that are not main_category AND not "Algemeen"
            all_categories.extend([c for c in sub_categories if c != main_category and c != 'Algemeen'])
        categories = list(dict.fromkeys(all_categories))  # Remove duplicates while preserving order
    elif categories:
        # If we have categories but no main_category, use first as main
        main_category = categories[0]
        sub_categories = categories[1:] if len(categories) > 1 else []
        # Remove "Algemeen" from sub_categories if main_category is not "Algemeen"
        if main_category != 'Algemeen':
            sub_categories = [c for c in sub_categories if c != 'Algemeen']
        else:
            sub_categories = []  # Algemeen has no sub_categories
    
    # Limit to MAX_CATEGORIES
    return {
        'categories': categories[:MAX_CATEGORIES],
        'main_category': main_category,
        'sub_categories': sub_categories[:MAX_CATEGORIES-1] if main_category else sub_categories[:MAX_CATEGORIES],
        'categorization_argumentation': argumentation,
        'llm': llm or 'LLM-Failed'
    }


def _categorize_with_llm(title: str, description: str, content: str, rss_feed_url: str = None) -> Dict[str, Any]:
    """Categorize using free LLM APIs. Returns dict with 'categories', 'main_category', 'sub_categories', 'categorization_argumentation', and 'llm'."""
    text = f"{title} {description} {content[:1000]}".strip()
    
    # Import secrets helper
    try:
        from secrets_helper import get_secret
    except ImportError:
        # Fallback if secrets_helper not available
        def get_secret(key, default=None):
            return os.getenv(key, default)
    
    # Try different LLM APIs
    # RouteLLM first (user requested)
    routellm_api_key = get_secret('ROUTELLM_API_KEY')
    if routellm_api_key:
        result = _categorize_with_routellm(text, title, routellm_api_key, rss_feed_url)
        if result:
            return result
    
    # Hugging Face (reliable and free)
    hf_api_key = get_secret('HUGGINGFACE_API_KEY')
    if hf_api_key:
        result = _categorize_with_huggingface(text, title, hf_api_key, rss_feed_url)
        if result:
            return result
    
    # Groq (fast and free)
    groq_api_key = get_secret('GROQ_API_KEY')
    if groq_api_key:
        result = _categorize_with_groq(text, title, groq_api_key, rss_feed_url)
        if result:
            return result
    
    # OpenAI
    openai_api_key = get_secret('OPENAI_API_KEY')
    openai_base_url = get_secret('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    if openai_api_key:
        result = _categorize_with_openai(text, title, openai_api_key, openai_base_url, rss_feed_url)
        if result:
            return result
    
    # ChatLLM - currently not working
    chatllm_api_key = get_secret('CHATLLM_API_KEY')
    if chatllm_api_key:
        result = _categorize_with_chatllm(text, title, chatllm_api_key, rss_feed_url)
        if result:
            return result
    
    return {'categories': [], 'main_category': None, 'sub_categories': [], 'categorization_argumentation': '', 'llm': None}


def _categorize_with_chatllm(text: str, title: str, api_key: str, rss_feed_url: str = None) -> Optional[Dict[str, Any]]:
    """Categorize using ChatLLM API (Aitomatic)."""
    try:
        import requests
        
        prompt = _get_categorization_prompt(title, text, rss_feed_url)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een data-analist gespecialiseerd in media. Je categoriseert Nederlandse nieuwsartikelen volgens de gegeven instructies."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200,
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
                            parsed = _parse_categorization_response(response_text)
                            if parsed.get('main_category') or parsed.get('categories'):
                                parsed['llm'] = 'ChatLLM'
                                return parsed
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


def _categorize_with_groq(text: str, title: str, api_key: str, rss_feed_url: str = None) -> Optional[Dict[str, Any]]:
    """Categorize using Groq API."""
    try:
        import groq
        client = groq.Groq(api_key=api_key)
        
        prompt = _get_categorization_prompt(title, text, rss_feed_url)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een data-analist gespecialiseerd in media. Je categoriseert Nederlandse nieuwsartikelen volgens de gegeven instructies."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=200
        )
        
        if chat_completion and chat_completion.choices and len(chat_completion.choices) > 0:
            response = chat_completion.choices[0].message.content.strip()
            if response:
                parsed = _parse_categorization_response(response)
                parsed['llm'] = 'Groq'
                return parsed
        return None
    except Exception as e:
        print(f"Groq categorization error: {e}")
        return None


def _categorize_with_openai(text: str, title: str, api_key: str, base_url: str, rss_feed_url: str = None) -> Optional[Dict[str, Any]]:
    """Categorize using OpenAI-compatible API."""
    try:
        import requests
        
        prompt = _get_categorization_prompt(title, text, rss_feed_url)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een data-analist gespecialiseerd in media. Je categoriseert Nederlandse nieuwsartikelen volgens de gegeven instructies."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200,
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
                    parsed = _parse_categorization_response(response_text)
                    parsed['llm'] = 'OpenAI'
                    return parsed
        return None
    except Exception as e:
        print(f"OpenAI categorization error: {e}")
    
    return None


def _categorize_with_huggingface(text: str, title: str, api_key: str, rss_feed_url: str = None) -> Optional[Dict[str, Any]]:
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
                        # Convert to new format
                        main_category = valid_categories[0] if valid_categories else None
                        sub_categories = valid_categories[1:] if len(valid_categories) > 1 else []
                        
                        # Remove "Algemeen" from sub_categories if main_category is "Algemeen"
                        if main_category == 'Algemeen':
                            sub_categories = []
                        else:
                            # Remove "Algemeen" from sub_categories if it somehow got in there
                            sub_categories = [c for c in sub_categories if c != 'Algemeen']
                        
                        return {
                            'main_category': main_category,
                            'sub_categories': sub_categories,
                            'categories': valid_categories,
                            'categorization_argumentation': '',
                            'llm': 'Hugging Face'
                        }
        except Exception:
            pass
    except Exception as e:
        print(f"Hugging Face categorization error: {e}")
    
    return None


def _categorize_with_routellm(text: str, title: str, api_key: str, rss_feed_url: str = None) -> Optional[Dict[str, Any]]:
    """Categorize using RouteLLM API (Abacus AI)."""
    global _routellm_categorization_calls
    try:
        import requests
        import json
        from datetime import datetime
        
        # Increment counter BEFORE making the call
        _routellm_categorization_calls += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [RouteLLM CATEGORIZATION] API call #{_routellm_categorization_calls} - Categorizing article: {title[:50]}...")
        
        prompt = _get_categorization_prompt(title, text, rss_feed_url)
        
        # RouteLLM endpoint from documentation
        url = "https://routellm.abacus.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Try different models that RouteLLM might support
        models_to_try = ["gpt-5", "gpt-4", "gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"]
        
        for model in models_to_try:
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Je bent een data-analist gespecialiseerd in media. Je categoriseert Nederlandse nieuwsartikelen volgens de gegeven instructies."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3,
                    "stream": False  # Non-streaming for simplicity
                }
                
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload),  # Use data=json.dumps() as per documentation
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result and 'choices' in result and len(result['choices']) > 0:
                        response_text = result['choices'][0].get('message', {}).get('content', '').strip()
                        if response_text:
                            parsed = _parse_categorization_response(response_text)
                            parsed['llm'] = 'RouteLLM'
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"[{timestamp}] [RouteLLM] Successfully categorized using model {model} (Total calls: {_routellm_categorization_calls})")
                            return parsed
                elif response.status_code == 400:
                    # Model might not be available, try next
                    continue
                elif response.status_code == 401:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] [RouteLLM] ❌ Authentication error (401) - API key is invalid or expired")
                    print(f"[{timestamp}] [RouteLLM] Please check your ROUTELLM_API_KEY in Streamlit Secrets or .env file")
                    return None
                elif response.status_code == 403:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        error_detail = response.json()
                        print(f"[{timestamp}] [RouteLLM] ❌ Authorization error (403): {error_detail}")
                    except:
                        print(f"[{timestamp}] [RouteLLM] ❌ Authorization error (403) - You are not authorized to make requests")
                    print(f"[{timestamp}] [RouteLLM] This usually means your API key has expired or doesn't have the right permissions")
                    return None
                else:
                    # Log error but try next model
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] [RouteLLM] Model {model} returned status {response.status_code}")
                    if response.status_code != 400:  # Don't log 400 as it's just model not available
                        try:
                            error_detail = response.json()
                            print(f"[{timestamp}] [RouteLLM] Error detail: {error_detail}")
                        except:
                            pass
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"[RouteLLM] Request error for model {model}: {e}")
                continue
            except Exception as e:
                print(f"[RouteLLM] Error for model {model}: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"RouteLLM categorization error: {e}")
        return None


def _parse_categories(response: str) -> List[str]:
    """Parse LLM response into list of valid categories (legacy format)."""
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


def _parse_categorization_response(response: str) -> Dict[str, Any]:
    """Parse LLM response in new format: Main Category, Sub Categories, Argumentatie."""
    if not response:
        return {'main_category': None, 'sub_categories': [], 'categorization_argumentation': '', 'categories': []}
    
    main_category = None
    sub_categories = []
    argumentation = ''
    
    # Parse the structured response
    lines = response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for Main Category
        if line.lower().startswith('main category:'):
            main_cat = line.split(':', 1)[1].strip()
            # Validate and find matching category
            for cat in CATEGORIES:
                if main_cat.lower() == cat.lower():
                    main_category = cat
                    break
        
        # Check for Sub Categories
        elif line.lower().startswith('sub categories:'):
            sub_cats_str = line.split(':', 1)[1].strip()
            if sub_cats_str.lower() != 'geen' and sub_cats_str.lower() != 'none':
                # Parse comma-separated list
                sub_cats = [c.strip().strip('"\'') for c in sub_cats_str.split(',')]
                for sub_cat in sub_cats:
                    for cat in CATEGORIES:
                        # Never add "Algemeen" as sub_category, and never add main_category as sub_category
                        if sub_cat.lower() == cat.lower() and cat != main_category and cat != 'Algemeen':
                            sub_categories.append(cat)
                            break
        
        # Check for Argumentatie
        elif line.lower().startswith('argumentatie:'):
            argumentation = line.split(':', 1)[1].strip()
            # Continue reading argumentation if it spans multiple lines
            current_section = 'argumentation'
        elif current_section == 'argumentation':
            argumentation += ' ' + line
    
    # Remove "Algemeen" from sub_categories if present (it should never be there)
    # Also, if main_category is "Algemeen", ensure sub_categories is empty
    if main_category == 'Algemeen':
        sub_categories = []
    else:
        # Remove "Algemeen" from sub_categories if it somehow got in there
        sub_categories = [c for c in sub_categories if c != 'Algemeen']
    
    # Combine main_category and sub_categories for backward compatibility
    # IMPORTANT: Never include "Algemeen" in categories if it's not the main_category
    categories = []
    if main_category:
        categories.append(main_category)
    # Only add sub_categories that are not main_category AND not "Algemeen"
    categories.extend([c for c in sub_categories if c != main_category and c != 'Algemeen' and c not in categories])
    
    return {
        'main_category': main_category,
        'sub_categories': sub_categories,
        'categorization_argumentation': argumentation.strip(),
        'categories': categories
    }


def _categorize_with_keywords(title: str, description: str, content: str) -> List[str]:
    """Fallback keyword-based categorization."""
    text = f"{title} {description} {content}".lower()
    categories = []
    
    # Keyword rules for the new categories (priority order: Koningshuis, Misdaad, Sport, Politiek, Buitenland, Cultuur, Opmerkelijk)
    
    # Koningshuis (highest priority)
    if any(kw in text for kw in ['koning', 'koningin', 'prins', 'prinses', 'beatrix', 'willem-alexander', 'maxima', 'amalia', 'koningshuis', 'oranje', 'koninklijk', 'koninklijke']):
        categories.append("Koningshuis")
    
    # Misdaad
    if any(kw in text for kw in ['misdaad', 'crimineel', 'diefstal', 'inbraak', 'moord', 'doodslag', 'aanslag', 'terrorisme', 'drugs', 'drugscircuit', 'cybercrime', 'hack', 'vandalisme', 'rechtszaak', 'veroordeeld', 'gevangenis', 'celstraf']):
        categories.append("Misdaad")
    
    # Sport
    if any(kw in text for kw in ['sport', 'voetbal', 'ajax', 'psv', 'feyenoord', 'eredivisie', 'champions league', 'ek', 'wk voetbal', 'voetballer', 'wielrennen', 'tour de france', 'giro', 'vuelta', 'wielrenner', 'koers', 'fietsen', 'olympische', 'atletiek', 'zwemmen', 'tennis', 'hockey', 'basketbal']):
        categories.append("Sport")
    
    # Politiek (Nederlandse politiek)
    if any(kw in text for kw in ['politiek', 'kabinet', 'minister', 'premier', 'tweede kamer', 'eerste kamer', 'regering', 'oppositie', 'coalitie', 'den haag', 'binnenhof', 'gemeente', 'burgemeester', 'wethouder', 'gemeenteraad', 'lokaal', 'gemeentelijk', 'verkiezing', 'partij', 'vvd', 'pvda', 'cda', 'd66', 'sp', 'gl', 'fvd', 'pvdd']):
        categories.append("Politiek")
    
    # Buitenland
    if any(kw in text for kw in ['buitenland', 'europa', 'eu', 'europese unie', 'brussel', 'frankrijk', 'duitsland', 'spanje', 'italië', 'belgië', 'polen', 'amerika', 'verenigde staten', 'vs', 'china', 'japan', 'australië', 'canada', 'rusland', 'oekraïne', 'oekraine', 'ukraine', 'gaza', 'israël', 'israel', 'palestina', 'soedan', 'sudan', 'conflict', 'oorlog', 'aanval', 'internationaal']):
        categories.append("Buitenland")
    
    # Cultuur
    if any(kw in text for kw in ['cultuur', 'kunst', 'museum', 'theater', 'muziek', 'film', 'boek', 'literatuur', 'tentoonstelling', 'festival', 'cultureel', 'culturele']):
        categories.append("Cultuur")
    
    # Opmerkelijk
    if any(kw in text for kw in ['opmerkelijk', 'bijzonder', 'vreemd', 'grappig', 'ongewoon', 'raar', 'curieus', 'merkwaardig']):
        categories.append("Opmerkelijk")
    
    # Algemeen (default if nothing matches)
    if not categories:
        categories.append("Algemeen")
    
    return categories


def get_all_categories() -> List[str]:
    """Get list of all available categories."""
    return CATEGORIES.copy()
