"""
Quick test to find working Groq vision models.
Run this to discover which model names are currently valid.
"""

from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

# Test different model name variations
test_models = [
    "groq/meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 Scout (suggested)
    "groq/llama-4-scout-17b-16e-instruct",  # Alternative format
    "groq/llama-3.2-90b-vision-instruct",  # Current maintained model (Dec 2025)
    "groq/llama-3.2-11b-vision-preview",   # Deprecated
]

print("Testing Groq vision models...\n")

for model in test_models:
    try:
        print(f"Testing: {model}")
        response = completion(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            timeout=5
        )
        print(f"  ✓ SUCCESS: {model} is available!\n")
    except Exception as e:
        error_msg = str(e)
        if "decommissioned" in error_msg.lower():
            print(f"  ❌ DEPRECATED: {model}")
        elif "not found" in error_msg.lower():
            print(f"  ❌ NOT FOUND: {model}")
        else:
            print(f"  ⚠️  ERROR: {error_msg[:100]}")
        print()

print("\nCheck https://console.groq.com/docs/models for official list")

