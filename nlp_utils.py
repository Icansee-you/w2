"""
NLP utilities for generating ELI5 summaries using free LLM APIs.
"""
import os
import re
import json
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    requests = None  # Will be handled gracefully in functions that use it

# RouteLLM: expliciet alleen dit model (geen intelligent routing naar GPT-5)
ROUTELLM_MODEL = "gpt-4o-mini"

# Global counter for RouteLLM API calls (ELI5)
_routellm_eli5_calls = 0


def get_routellm_eli5_count() -> int:
    """Get the number of RouteLLM API calls for ELI5 generation."""
    return _routellm_eli5_calls


def reset_routellm_eli5_counter():
    """Reset RouteLLM ELI5 API call counter."""
    global _routellm_eli5_calls
    _routellm_eli5_calls = 0


def generate_eli5_summary_nl(article_text: str, title: str = "") -> Optional[str]:
    """
    Generate an "Explain Like I'm 5" summary in Dutch using a free LLM.

    Args:
        article_text: The article content to summarize
        title: Article title (optional, for context)

    Returns:
        ELI5 summary in Dutch, or None if generation fails
    """
    result = generate_eli5_summary_nl_with_llm(article_text, title)
    return result.get('summary') if result else None


def generate_eli5_summary_nl_with_llm(article_text: str, title: str = "") -> Optional[Dict[str, Any]]:
    """
    Generate an "Explain Like I'm 5" summary in Dutch using a free LLM.
    Returns both the summary and which LLM was used.
    
    Args:
        article_text: The article content to summarize
        title: Article title (optional, for context)
    
    Returns:
        Dict with 'summary' and 'llm' keys, or None if generation fails
    """
    # Try different free LLM APIs in order of preference
    
    # Import secrets helper
    try:
        from secrets_helper import get_secret
    except ImportError:
        # Fallback if secrets_helper not available
        def get_secret(key, default=None):
            return os.getenv(key, default)
    
    # Option 1: Groq API (first priority)
    groq_api_key = get_secret('GROQ_API_KEY')
    if groq_api_key:
        result = _generate_with_groq(article_text, title, groq_api_key)
        if result:
            return {'summary': result.get('summary'), 'llm': 'Groq', 'token_usage': result.get('token_usage')}
    
    # Option 2: RouteLLM API (second priority)
    routellm_api_key = get_secret('ROUTELLM_API_KEY')
    if routellm_api_key:
        result = _generate_with_routellm(article_text, title, routellm_api_key)
        if result:
            return {'summary': result.get('summary'), 'llm': 'RouteLLM', 'token_usage': result.get('token_usage')}
    
    # If both Groq and RouteLLM fail, return "failed LLM"
    return {'summary': 'failed LLM', 'llm': 'Failed'}


def _generate_with_routellm(text: str, title: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Generate ELI5 summary using RouteLLM API with improved prompt. Returns dict with summary and optional token_usage."""
    global _routellm_eli5_calls
    if requests is None:
        return None
    try:
        import json
        from datetime import datetime
        
        # Increment counter BEFORE making the call
        _routellm_eli5_calls += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [RouteLLM ELI5] API call #{_routellm_eli5_calls} - Generating ELI5 for: {title[:50]}...")
        
        # New improved prompt
        prompt = f"""Je bent een expert in het uitleggen van complexe onderwerpen op een begrijpelijke manier. 
Maak een ELI5-samenvatting van het volgende nieuwsartikel in maximaal 5 regels.

Richtlijnen:
- Schrijf in een speelse, vriendschappelijke toon die geschikt is voor volwassenen en tieners
- Houd het verhaal vloeiend en natuurlijk, niet als bullet points
- Gebruik eenvoudige woorden en korte zinnen
- Als je complexe termen gebruikt die echt nodig zijn voor begrip (bijv. inflatie, algoritme), geef dan direct een korte uitleg in haakjes (geld wordt minder waard)
- Bekende termen zoals "staakt-het-vuren", "coalitie", "kabinet", "gijzelaar" hoef je NIET uit te leggen - deze zijn al duidelijk genoeg
- Te complexe termen die niet essentieel zijn voor het verhaal (zoals "bemiddelaars", "stabilisatiemacht", "internationale bemiddeling") kun je weglaten of vervangen door eenvoudigere alternatieven
- Focus op het hoofdverhaal, niet op alle details en technische termen
- Voeg algemene context toe als dat helpt om het onderwerp beter te begrijpen
- Zorg dat iemand zonder voorkennis het volledig snapt
- Geef alleen de samenvatting terug, geen extra commentaar

Titel: {title}

Artikel:
{text[:3000]}

ELI5 Samenvatting:"""
        
        # Stuur altijd expliciet model (nooit weglaten; anders default route-llm → GPT-5)
        url = "https://routellm.abacus.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        model = ROUTELLM_MODEL
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Je bent een expert in het uitleggen van complexe onderwerpen op een begrijpelijke manier. Je schrijft in een speelse, vriendschappelijke toon die geschikt is voor volwassenen en tieners."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.7,
                "stream": False
            }
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result and 'choices' in result and len(result['choices']) > 0:
                    response_model = result.get('model') or ''
                    if response_model and 'gpt-4o-mini' not in response_model.lower():
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] [RouteLLM ELI5] WAARSCHUWING: Wij vroegen '{model}' maar RouteLLM rapporteerde '{response_model}'.")
                    summary = result['choices'][0].get('message', {}).get('content', '').strip()
                    if summary:
                        summary = summary.strip()
                        prefixes = ["ELI5 Samenvatting:", "Samenvatting:", "ELI5:", "Samenvatting"]
                        for prefix in prefixes:
                            if summary.startswith(prefix):
                                summary = summary[len(prefix):].strip()
                        out = {'summary': summary}
                        usage = result.get('usage', {})
                        if usage:
                            out['token_usage'] = {
                                'prompt_tokens': usage.get('prompt_tokens'),
                                'completion_tokens': usage.get('completion_tokens'),
                                'total_tokens': usage.get('total_tokens'),
                            }
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] [RouteLLM ELI5] Successfully generated ELI5 (Total calls: {_routellm_eli5_calls})")
                        return out
                return None
            if response.status_code == 400:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] [RouteLLM ELI5] Model {model} not available (400)")
                return None
            if response.status_code == 401:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] [RouteLLM ELI5] ❌ Authentication error (401) - API key is invalid or expired")
                print(f"[{timestamp}] [RouteLLM ELI5] Please check your ROUTELLM_API_KEY in Streamlit Secrets or .env file")
                return None
            if response.status_code == 403:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                try:
                    error_detail = response.json()
                    print(f"[{timestamp}] [RouteLLM ELI5] ❌ Authorization error (403): {error_detail}")
                except Exception:
                    print(f"[{timestamp}] [RouteLLM ELI5] ❌ Authorization error (403) - You are not authorized to make requests")
                print(f"[{timestamp}] [RouteLLM ELI5] This usually means your API key has expired or doesn't have the right permissions")
                return None
            return None
        except requests.exceptions.RequestException as e:
            print(f"[RouteLLM ELI5] Request error: {e}")
            return None
        except Exception as e:
            print(f"[RouteLLM ELI5] Error: {e}")
            return None
    except Exception as e:
        print(f"RouteLLM ELI5 generation error: {e}")
        return None


def _generate_with_chatllm(text: str, title: str, api_key: str) -> Optional[str]:
    """Generate summary using ChatLLM API with improved error handling."""
    if requests is None:
        return None
    try:
        prompt = f"""Leg dit nieuwsartikel uit alsof ik 5 jaar ben. Gebruik heel eenvoudige Nederlandse woorden die een 5-jarige begrijpt. Gebruik korte zinnen (2-3 zinnen).

BELANGRIJK: Als je namen of woorden met een hoofdletter gebruikt (zoals Mark Rutte, Pornhub, of bedrijfsnamen), leg dan in een paar simpele woorden uit wat dat is. Bijvoorbeeld: "Mark Rutte (dat is de baas van Nederland)" of "Pornhub (dat is een website)". Landen zoals Nederland, Frankrijk, Duitsland hoef je niet uit te leggen.

Titel: {title}

Inhoud: {text[:2000]}

Samenvatting:"""
        
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
        
        payloads = [
            {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "Je bent een vriendelijke assistent die nieuwsartikelen uitlegt aan kinderen van 5 jaar oud. Gebruik altijd heel eenvoudige Nederlandse woorden en korte zinnen. Leg namen en bedrijfsnamen met een hoofdletter uit in simpele woorden (behalve bekende landen zoals Nederland, Frankrijk)."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            },
            {
                "prompt": prompt,
                "max_tokens": 200,
                "temperature": 0.7
            },
            {
                "input": prompt,
                "max_tokens": 200,
                "temperature": 0.7
            }
        ]
        
        for api_url in endpoints:
            for headers in headers_formats:
                for payload in payloads:
                    try:
                        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            # Try different response formats
                            if 'choices' in result and len(result['choices']) > 0:
                                summary = result['choices'][0].get('message', {}).get('content', '').strip()
                                if summary:
                                    return summary
                            elif 'response' in result:
                                summary = result['response'].strip()
                                if summary:
                                    return summary
                            elif 'text' in result:
                                summary = result['text'].strip()
                                if summary:
                                    return summary
                            elif 'content' in result:
                                summary = result['content'].strip()
                                if summary:
                                    return summary
                            elif 'output' in result:
                                summary = result['output'].strip()
                                if summary:
                                    return summary
                        elif response.status_code == 401:
                            # Wrong auth format, try next
                            continue
                    except requests.exceptions.RequestException as e:
                        continue  # Try next combination
                    except Exception as e:
                        print(f"ChatLLM parsing error for {api_url}: {e}")
                        continue
        
    except Exception as e:
        print(f"ChatLLM API error: {e}")
    
    return None


def _generate_with_huggingface(text: str, title: str, api_key: str) -> Optional[str]:
    """Generate summary using Hugging Face Inference API via huggingface_hub library."""
    try:
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(token=api_key)
        
        # Create a simple prompt for ELI5
        prompt = f"""Leg dit uit alsof ik 5 ben: {title}. {text[:1000]}

Samenvatting (heel simpel, 2-3 zinnen):"""
        
        # Try different models
        models = [
            "google/flan-t5-base",  # Multilingual, good for instructions
            "facebook/bart-large-cnn",  # Good for summarization
            "sshleifer/distilbart-cnn-12-6",  # Faster, smaller
        ]
        
        for model in models:
            try:
                # Use text generation for summarization
                result = client.text_generation(
                    prompt=prompt,
                    model=model,
                    max_new_tokens=150,
                    temperature=0.7
                )
                
                if result and len(result.strip()) > 20:
                    return result.strip()
                    
            except Exception as e:
                # Model might not support text_generation, try next
                continue
        
        # Fallback: try summarization task
        try:
            result = client.summarization(
                f"{title}. {text[:1000]}",
                model="facebook/bart-large-cnn"
            )
            
            # Handle different response formats
            if isinstance(result, dict):
                if 'summary_text' in result:
                    return result['summary_text'].strip()
                elif 'summary' in result:
                    return result['summary'].strip()
            elif isinstance(result, str):
                return result.strip()
            elif isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    return result[0].get('summary_text', '').strip()
                elif isinstance(result[0], str):
                    return result[0].strip()
                
        except Exception:
            pass  # Summarization not available
        
    except ImportError:
        # Fallback to direct API call if library not available
        if requests is None:
            return None
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            prompt = f"Leg dit uit alsof ik 5 ben: {title}. {text[:1000]}"
            
            # Try the old endpoint format (might still work for some models)
            api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
            payload = {"inputs": prompt, "parameters": {"max_length": 150}}
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    if 'summary_text' in result[0]:
                        return result[0]['summary_text'].strip()
                    elif 'generated_text' in result[0]:
                        return result[0]['generated_text'].strip()
        except Exception:
            pass
    except Exception as e:
        print(f"Hugging Face API error: {e}")
    
    return None


def _generate_with_groq(text: str, title: str, api_key: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Generate ELI5 summary using Groq API with improved prompt. Returns dict with summary and optional token_usage."""
    try:
        import groq
        from functools import wraps
        import threading
        
        client = groq.Groq(api_key=api_key, timeout=timeout)
        
        # Use the improved prompt
        prompt = f"""Je bent een expert in het uitleggen van complexe onderwerpen op een begrijpelijke manier. 
Maak een ELI5-samenvatting van het volgende nieuwsartikel in maximaal 5 regels.

Richtlijnen:
- Schrijf in een speelse, vriendschappelijke toon die geschikt is voor volwassenen en tieners
- Houd het verhaal vloeiend en natuurlijk, niet als bullet points
- Gebruik eenvoudige woorden en korte zinnen
- Als je complexe termen gebruikt die echt nodig zijn voor begrip (bijv. inflatie, algoritme), geef dan direct een korte uitleg in haakjes (geld wordt minder waard)
- Bekende termen zoals "staakt-het-vuren", "coalitie", "kabinet", "gijzelaar" hoef je NIET uit te leggen - deze zijn al duidelijk genoeg
- Te complexe termen die niet essentieel zijn voor het verhaal (zoals "bemiddelaars", "stabilisatiemacht", "internationale bemiddeling") kun je weglaten of vervangen door eenvoudigere alternatieven
- Focus op het hoofdverhaal, niet op alle details en technische termen
- Voeg algemene context toe als dat helpt om het onderwerp beter te begrijpen
- Zorg dat iemand zonder voorkennis het volledig snapt
- Geef alleen de samenvatting terug, geen extra commentaar

Titel: {title}

Artikel:
{text[:3000]}

ELI5 Samenvatting:"""
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Je bent een expert in het uitleggen van complexe onderwerpen op een begrijpelijke manier. Je schrijft in een speelse, vriendschappelijke toon die geschikt is voor volwassenen en tieners."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Free fast model
                temperature=0.7,
                max_tokens=300,
                timeout=timeout
            )
            
            summary = chat_completion.choices[0].message.content.strip()
            out = {'summary': summary}
            if getattr(chat_completion, 'usage', None):
                u = chat_completion.usage
                out['token_usage'] = {
                    'prompt_tokens': getattr(u, 'prompt_tokens', None),
                    'completion_tokens': getattr(u, 'completion_tokens', None),
                    'total_tokens': getattr(u, 'total_tokens', None),
                }
            return out
        except Exception as api_error:
            # Check if it's a timeout
            error_str = str(api_error).lower()
            if "timeout" in error_str or "timed out" in error_str:
                print(f"Groq API timeout after {timeout}s")
            else:
                print(f"Groq API error: {api_error}")
            return None
    except ImportError:
        print("Groq library not installed. Install with: pip install groq")
    except Exception as e:
        print(f"Groq API error: {e}")
    
    return None


def _generate_with_openai_compatible(text: str, title: str, api_key: str, base_url: str) -> Optional[str]:
    """Generate summary using OpenAI-compatible API."""
    if requests is None:
        return None
    try:
        prompt = f"""Leg dit nieuwsartikel uit alsof ik 5 jaar ben. Gebruik heel eenvoudige Nederlandse woorden die een 5-jarige begrijpt. Gebruik korte zinnen (2-3 zinnen).

BELANGRIJK: Als je namen of woorden met een hoofdletter gebruikt (zoals Mark Rutte, Pornhub, of bedrijfsnamen), leg dan in een paar simpele woorden uit wat dat is. Bijvoorbeeld: "Mark Rutte (dat is de baas van Nederland)" of "Pornhub (dat is een website)". Landen zoals Nederland, Frankrijk, Duitsland hoef je niet uit te leggen.

Titel: {title}

Inhoud: {text[:2000]}

Samenvatting:"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",  # Or use a free model from the provider
            "messages": [
                {
                    "role": "system",
                    "content": "Je bent een vriendelijke assistent die nieuwsartikelen uitlegt aan kinderen van 5 jaar oud. Gebruik altijd heel eenvoudige Nederlandse woorden en korte zinnen. Leg namen en bedrijfsnamen met een hoofdletter uit in simpele woorden (behalve bekende landen zoals Nederland, Frankrijk)."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"OpenAI-compatible API error: {e}")
    
    return None


def _simple_extract_summary(text: str) -> Optional[str]:
    """Fallback: Extract first 2-3 sentences as a simple summary."""
    if not text:
        return None
    
    # Split by sentence endings
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take first 2-3 sentences
    if len(sentences) >= 2:
        summary = '. '.join(sentences[:2])
        if summary and not summary[-1] in '.!?':
            summary += '.'
        return summary
    
    return text[:200] + "..." if len(text) > 200 else text

