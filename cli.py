"""
CLI Entry Point for Windows Agent.
Original command-line interface (preserved for testing).
For GUI version, use main_gui.py instead.
"""

from app.tools.registry import ToolRegistry
from app.tools import os_ops
from app.tools.web_search import web_search
from app.tools.image_tools import find_image
from app.tools.ppt_tools import create_presentation
from app.tools import vision_tools
from app.tools.tool_catalog import get_tool_description
from app.core.agent import Agent
import os

def main():
    # 1. Setup the "Hands" (Registry)
    # All tool names and descriptions come from tool_catalog.py (single source of truth)
    registry = ToolRegistry()
    
    # Register tools using canonical names from TOOL_CATALOG
    # Basic System Controls
    registry.register("set_volume", os_ops.set_volume, get_tool_description("set_volume"))
    registry.register("get_volume", os_ops.get_volume, get_tool_description("get_volume"))
    registry.register("set_mouse_speed", os_ops.set_mouse_speed, get_tool_description("set_mouse_speed"))
    registry.register("set_caps_lock", os_ops.set_caps_lock, get_tool_description("set_caps_lock"))
    
    # File & Folder Operations
    registry.register("create_note", os_ops.create_and_open_file, get_tool_description("create_note"))
    registry.register("create_folder", os_ops.create_folder, get_tool_description("create_folder"))
    registry.register("list_folder", os_ops.list_directory, get_tool_description("list_folder"))
    registry.register("search_files", os_ops.search_files, get_tool_description("search_files"))
    
    # App Launching & File Opening
    registry.register("smart_search_and_open", os_ops.smart_search_and_open, get_tool_description("smart_search_and_open"))
    registry.register("launch_app", os_ops.launch_app, get_tool_description("launch_app"))
    registry.register("open_url", os_ops.open_url, get_tool_description("open_url"))
    
    # Web & Research Tools
    registry.register("web_search", web_search, get_tool_description("web_search"))
    registry.register("find_image", find_image, get_tool_description("find_image"))
    
    # Document Creation
    registry.register("create_presentation", create_presentation, get_tool_description("create_presentation"))
    
    # Vision & Screen Analysis
    registry.register("capture_screenshot", vision_tools.capture_screenshot, get_tool_description("capture_screenshot"))
    registry.register("analyze_image", vision_tools.analyze_image, get_tool_description("analyze_image"))
    registry.register("analyze_screenshot", vision_tools.analyze_screenshot, get_tool_description("analyze_screenshot"))
    registry.register("find_ui_element", vision_tools.find_ui_element, get_tool_description("find_ui_element"))
    registry.register("describe_screen", vision_tools.describe_screen, get_tool_description("describe_screen"))

    # 2. Setup the "Brain" (Agent)
    agent = Agent(registry=registry)
    
    print("🤖 Windows Agent Online (CLI Mode). Type 'quit' to exit.")
    print("---------------------------------------------")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["quit", "exit"]:
                break
            
            response = agent.process(user_input)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()

