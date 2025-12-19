"""
Quick test for agent mode with the new intelligent filtering system.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.tools.registry import ToolRegistry
from app.core.agent import Agent

def main():
    print("="*70)
    print("🤖 TESTING AGENT MODE WITH INTELLIGENT FILTERING")
    print("="*70)
    print()
    
    # Initialize registry and agent
    registry = ToolRegistry()
    agent = Agent(registry)
    
    # Test request
    test_request = "open youtube.com"
    
    print(f"📝 Test Request: {test_request}")
    print()
    print("Starting agent mode (this will actually control your computer)...")
    print("Make sure Chrome is closed before starting!")
    print()
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()
    
    try:
        result = agent.process(test_request, mode="agent")
        print()
        print("="*70)
        print("✅ RESULT:")
        print("="*70)
        print(result)
    
    except KeyboardInterrupt:
        print("\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

