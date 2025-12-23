"""Quick test to debug ChatLLM API."""
import os
import requests

api_key = "s2_156073f76d354d72a6b0fb22c94a2f8d"

endpoints = [
    "https://api.chatllm.ai/v1/chat/completions",
    "https://chatllm.ai/api/v1/chat",
    "https://api.aitomatic.com/v1/chat/completions",
]

headers_formats = [
    {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"},
    {"X-API-Key": api_key, "Content-Type": "application/json"},
]

payload = {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
}

print("Testing ChatLLM API endpoints...")
print("=" * 60)

for endpoint in endpoints:
    for headers in headers_formats:
        try:
            print(f"\nTrying: {endpoint}")
            print(f"Headers: {list(headers.keys())}")
            response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"SUCCESS! Response: {response.text[:200]}")
                break
            else:
                print(f"Response: {response.text[:200]}")
        except requests.exceptions.Timeout:
            print("Timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Error: {e}")

