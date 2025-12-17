"""
Direct test of ChatLLM API to debug connection issues.
"""
import os
import requests
import json

# Set API key
api_key = "s2_733cff6da442497eb4f1a5f2e11f9d7a"

print("=" * 60)
print("TESTING CHATLLM API DIRECTLY")
print("=" * 60)

test_prompt = "Leg dit uit alsof ik 5 ben: Nederland verhoogt defensie-uitgaven."

# Try different endpoint/auth combinations
endpoints = [
    "https://api.chatllm.ai/v1/chat/completions",
    "https://chatllm.ai/api/v1/chat",
    "https://api.aitomatic.com/v1/chat/completions",
    "https://chatllm.aitomatic.com/api/v1/chat",
    "https://api.aitomatic.com/v1/completions",
]

headers_formats = [
    {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"},
    {"X-API-Key": api_key, "Content-Type": "application/json"},
    {"api-key": api_key, "Content-Type": "application/json"},
]

payloads = [
    {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "Je bent een vriendelijke assistent."},
            {"role": "user", "content": test_prompt}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    },
    {
        "prompt": test_prompt,
        "max_tokens": 100,
        "temperature": 0.7
    },
    {
        "input": test_prompt,
        "max_tokens": 100,
        "temperature": 0.7
    }
]

success = False
for endpoint_idx, endpoint in enumerate(endpoints):
    for header_idx, headers in enumerate(headers_formats):
        for payload_idx, payload in enumerate(payloads):
            try:
                print(f"\nTrying: {endpoint}")
                print(f"  Headers: {list(headers.keys())[0]}")
                print(f"  Payload format: {list(payload.keys())[0]}")
                
                response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  Response keys: {list(result.keys())}")
                    
                    # Try to extract response
                    text = None
                    if 'choices' in result and len(result['choices']) > 0:
                        text = result['choices'][0].get('message', {}).get('content', '')
                    elif 'response' in result:
                        text = result['response']
                    elif 'text' in result:
                        text = result['text']
                    elif 'content' in result:
                        text = result['content']
                    elif 'output' in result:
                        text = result['output']
                    
                    if text:
                        print(f"\n[SUCCESS] Response received:")
                        print(f"  {text[:200]}")
                        success = True
                        break
                    else:
                        print(f"  Full response: {json.dumps(result, indent=2)[:500]}")
                elif response.status_code == 401:
                    print(f"  [AUTH ERROR] Unauthorized - wrong auth format")
                elif response.status_code == 404:
                    print(f"  [NOT FOUND] Endpoint doesn't exist")
                else:
                    print(f"  [ERROR] {response.text[:200]}")
            except requests.exceptions.Timeout:
                print(f"  [TIMEOUT] Request timed out")
            except requests.exceptions.RequestException as e:
                print(f"  [REQUEST ERROR] {str(e)[:100]}")
            except Exception as e:
                print(f"  [ERROR] {str(e)[:100]}")
        
        if success:
            break
    if success:
        break

if not success:
    print("\n" + "=" * 60)
    print("[FAILED] No working endpoint/auth/payload combination found")
    print("=" * 60)
    print("\nPossible issues:")
    print("1. API key format might be incorrect")
    print("2. Endpoint URLs might have changed")
    print("3. API might require different authentication")
    print("4. Network/firewall blocking requests")

