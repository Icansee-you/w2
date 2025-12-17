"""
NLP utilities for generating ELI5 summaries using free LLM APIs.
"""
import os
from typing import Optional, Dict, Any
import requests
import json


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
    
    # Option 1: Hugging Face Inference API (free tier, reliable)
    hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
    if hf_api_key:
        summary = _generate_with_huggingface(article_text, title, hf_api_key)
        if summary:
            return {'summary': summary, 'llm': 'HuggingFace'}
    
    # Option 2: Groq API (free tier with API key, fast)
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        summary = _generate_with_groq(article_text, title, groq_api_key)
        if summary:
            return {'summary': summary, 'llm': 'Groq'}
    
    # Option 3: OpenAI-compatible API (e.g., Together AI, OpenRouter free models)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    if openai_api_key:
        summary = _generate_with_openai_compatible(article_text, title, openai_api_key, openai_base_url)
        if summary:
            return {'summary': summary, 'llm': 'OpenAI'}
    
    # Option 4: ChatLLM API (Aitomatic) - currently not working
    chatllm_api_key = os.getenv('CHATLLM_API_KEY')
    if chatllm_api_key:
        summary = _generate_with_chatllm(article_text, title, chatllm_api_key)
        if summary:
            return {'summary': summary, 'llm': 'ChatLLM'}
    
    # Option 5: Fallback to simple extraction if no API available
    summary = _simple_extract_summary(article_text)
    if summary:
        return {'summary': summary, 'llm': 'Simple'}
    return None


def _generate_with_chatllm(text: str, title: str, api_key: str) -> Optional[str]:
    """Generate summary using ChatLLM API with improved error handling."""
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


def _generate_with_groq(text: str, title: str, api_key: str) -> Optional[str]:
    """Generate summary using Groq API (fast and free tier available)."""
    try:
        import groq
        
        client = groq.Groq(api_key=api_key)
        
        prompt = f"""Leg dit nieuwsartikel uit alsof ik 5 jaar ben. Gebruik heel eenvoudige Nederlandse woorden die een 5-jarige begrijpt. Gebruik korte zinnen (2-3 zinnen).

BELANGRIJK: Als je namen of woorden met een hoofdletter gebruikt (zoals Mark Rutte, Pornhub, of bedrijfsnamen), leg dan in een paar simpele woorden uit wat dat is. Bijvoorbeeld: "Mark Rutte (dat is de baas van Nederland)" of "Pornhub (dat is een website)". Landen zoals Nederland, Frankrijk, Duitsland hoef je niet uit te leggen.

Titel: {title}

Inhoud: {text[:2000]}

Samenvatting:"""
        
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
            model="llama-3.1-8b-instant",  # Free fast model
            temperature=0.7,
            max_tokens=150
        )
        
        summary = chat_completion.choices[0].message.content.strip()
        return summary
    except ImportError:
        print("Groq library not installed. Install with: pip install groq")
    except Exception as e:
        print(f"Groq API error: {e}")
    
    return None


def _generate_with_openai_compatible(text: str, title: str, api_key: str, base_url: str) -> Optional[str]:
    """Generate summary using OpenAI-compatible API."""
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
    import re
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take first 2-3 sentences
    if len(sentences) >= 2:
        summary = '. '.join(sentences[:2])
        if summary and not summary[-1] in '.!?':
            summary += '.'
        return summary
    
    return text[:200] + "..." if len(text) > 200 else text

