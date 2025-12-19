"""
Simplest possible test - just like test_agent.py but with the latest screenshot.
"""

from gradio_client import Client, file
import os
from dotenv import load_dotenv

load_dotenv()

# Get the latest screenshot
SCREENSHOT_PATH = r"C:\Users\tombr\Desktop\screenshots\screenshot_20251216_125818.png"
GRADIO_URL = os.getenv("RUNPOD_URL")

print(f"Testing with screenshot: {SCREENSHOT_PATH}")
print(f"File exists: {os.path.exists(SCREENSHOT_PATH)}")
print(f"File size: {os.path.getsize(SCREENSHOT_PATH) if os.path.exists(SCREENSHOT_PATH) else 'N/A'} bytes")
print(f"\nConnecting to: {GRADIO_URL}")

try:
    client = Client(GRADIO_URL)
    print("✓ Client created")
    
    print("\nSending image to OmniParser...")
    result = client.predict(
        image_input=file(SCREENSHOT_PATH),
        box_threshold=0.05,
        iou_threshold=0.1,
        api_name="/process"
    )
    
    print(f"\n✅ SUCCESS!")
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    print(f"Labeled image: {result[0]}")
    print(f"JSON preview: {result[1][:200]}...")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

