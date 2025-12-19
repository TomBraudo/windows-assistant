"""
Quick diagnostic script to test RunPod Gradio connection.

This checks if your Gradio endpoint is working BEFORE running the full test.
"""

import os
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

def test_connection():
    """Test basic connection to Gradio endpoint."""
    print("="*70)
    print("GRADIO ENDPOINT CONNECTION TEST")
    print("="*70)
    
    # Check RUNPOD_URL
    runpod_url = os.getenv("RUNPOD_URL")
    
    if not runpod_url:
        print("\n❌ ERROR: RUNPOD_URL not found in .env file!")
        print("\nAdd this to your .env file:")
        print("RUNPOD_URL=https://your-runpod-url.gradio.live")
        return False
    
    print(f"\n✓ RUNPOD_URL found: {runpod_url}")
    
    # Test connection
    print("\n📡 Testing connection...")
    try:
        print("   Creating Gradio client...")
        client = Client(runpod_url)
        print("   ✓ Client created successfully!")
        
        # Try to get API info
        print("\n📋 Checking API endpoints...")
        try:
            # View available endpoints
            print(f"   Available endpoints: {client.endpoints}")
            print("\n   ✓ Endpoint is responsive!")
        except Exception as e:
            print(f"   ⚠️  Could not list endpoints: {e}")
        
        print("\n✅ CONNECTION TEST PASSED!")
        print("\nYour RunPod Gradio endpoint is working.")
        print("You can now run: python test_runpod_omniparser.py")
        return True
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("\n🔍 Troubleshooting:")
        print("1. Is your RunPod pod running?")
        print("   → Check your RunPod dashboard")
        print("\n2. Is the Gradio URL correct and not expired?")
        print(f"   → Current URL: {runpod_url}")
        print("   → Try opening it in your browser")
        print("   → You should see a Gradio interface")
        print("\n3. Check your internet connection")
        print("\n4. If pod was restarted, the Gradio URL may have changed")
        print("   → Get the new URL from RunPod and update .env")
        
        return False

if __name__ == "__main__":
    test_connection()

