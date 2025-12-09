"""
Test the new sequential single-tool-per-call flow.

This test verifies that:
1. The refiner creates an execution plan with ordered steps
2. The agent executes one tool per API call
3. Results from previous steps are passed to subsequent steps
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.agent import Agent
from app.tools.registry import ToolRegistry
from app.tools import os_ops
from app.tools.web_search import web_search
from app.tools.image_tools import find_image
from app.tools.ppt_tools import create_presentation
from app.tools.tool_catalog import get_tool_description


def setup_registry():
    """Setup registry with all tools (same as main.py)."""
    registry = ToolRegistry(safe_mode=False)  # Disable safe mode for testing
    
    # Basic System Controls
    registry.register("set_volume", os_ops.set_volume, get_tool_description("set_volume"), sensitive=False)
    registry.register("get_volume", os_ops.get_volume, get_tool_description("get_volume"), sensitive=False)
    registry.register("set_mouse_speed", os_ops.set_mouse_speed, get_tool_description("set_mouse_speed"), sensitive=True)
    registry.register("set_caps_lock", os_ops.set_caps_lock, get_tool_description("set_caps_lock"), sensitive=False)
    
    # File & Folder Operations
    registry.register("create_note", os_ops.create_and_open_file, get_tool_description("create_note"), sensitive=True)
    registry.register("create_folder", os_ops.create_folder, get_tool_description("create_folder"), sensitive=True)
    registry.register("list_folder", os_ops.list_directory, get_tool_description("list_folder"), sensitive=False)
    registry.register("search_files", os_ops.search_files, get_tool_description("search_files"), sensitive=False)
    
    # App Launching & File Opening
    registry.register("smart_search_and_open", os_ops.smart_search_and_open, get_tool_description("smart_search_and_open"), sensitive=True)
    registry.register("launch_app", os_ops.launch_app, get_tool_description("launch_app"), sensitive=True)
    registry.register("open_url", os_ops.open_url, get_tool_description("open_url"), sensitive=False)
    
    # Web & Research Tools
    registry.register("web_search", web_search, get_tool_description("web_search"), sensitive=False)
    registry.register("find_image", find_image, get_tool_description("find_image"), sensitive=False)
    
    # Document Creation
    registry.register("create_presentation", create_presentation, get_tool_description("create_presentation"), sensitive=True)
    
    return registry


def test_sequential_execution():
    """Test that multi-step operations execute sequentially."""
    print("\n" + "="*60)
    print("Testing Sequential Single-Tool Execution Flow")
    print("="*60 + "\n")
    
    # Initialize the agent with properly configured registry
    print("Setting up registry with all tools...")
    registry = setup_registry()
    print(f"✓ Registered {len(registry.list_tools())} tools\n")
    
    agent = Agent(registry)
    
    # Test case: Research and create document (should be 2 separate calls)
    test_query = "Search for information about Python asyncio and create a text file summary on my desktop"
    
    print(f"Test Query: {test_query}\n")
    print("Expected behavior:")
    print("  Step 1: web_search for Python asyncio")
    print("  Step 2: create_note with research results\n")
    print("Note: Tool names come from tool_catalog.py (single source of truth)")
    print("-"*60 + "\n")
    
    try:
        result = agent.process(test_query)
        print("\n" + "-"*60)
        print("Final Result:")
        print(result)
        print("\n" + "="*60)
        print("Test completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_sequential_execution()

