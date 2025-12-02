import os
from dotenv import load_dotenv
from litellm import completion

# 1. Load the keys from .env
load_dotenv()

def test_provider(provider_name, model_name):
    print(f"Testing {provider_name} ({model_name})...", end=" ", flush=True)
    try:
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": "Reply with only the word 'Connected'."}]
        )
        # Success print
        print(f"SUCCESS! \n   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED. \n   Error: {e}")

if __name__ == "__main__":
    # Test Groq (Speed - Llama 3.3)
    test_provider("Groq", "groq/llama-3.3-70b-versatile")
    
    # Test Google (Context - Gemini 1.5 Flash Stable)
    # Changed from 2.0-exp to 1.5-flash to fix "Limit: 0" error
    test_provider("Google", "gemini/gemini-2.5-flash")