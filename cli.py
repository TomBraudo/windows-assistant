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
from app.tools import computer_control
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
    
    # Computer Control (Mouse & Keyboard)
    registry.register("click_at_coordinates", computer_control.click_at_coordinates, get_tool_description("click_at_coordinates"))
    registry.register("click_element", computer_control.click_element, get_tool_description("click_element"))
    registry.register("type_text", computer_control.type_text, get_tool_description("type_text"))
    registry.register("press_key", computer_control.press_key, get_tool_description("press_key"))
    registry.register("hotkey", computer_control.hotkey, get_tool_description("hotkey"))
    registry.register("scroll", computer_control.scroll, get_tool_description("scroll"))
    registry.register("move_mouse", computer_control.move_mouse, get_tool_description("move_mouse"))
    registry.register("get_mouse_position", computer_control.get_mouse_position, get_tool_description("get_mouse_position"))
    registry.register("drag_to", computer_control.drag_to, get_tool_description("drag_to"))

    # 2. Setup the "Brain" (Agent)
    agent = Agent(registry=registry)
    
    print("🤖 Windows Agent Online (CLI Mode). Type 'quit' to exit.")
    print("=" * 60)
    print("\n📋 MODES:")
    print("  💬 Ask Mode (default): Use standard tools and web search")
    print("  🤖 Agent Mode: Autonomous computer control with vision")
    print("\nTo switch modes, type:")
    print("  /ask  - Switch to Ask Mode")
    print("  /agent - Switch to Agent Mode")
    print("=" * 60)
    
    current_mode = "ask"  # Default mode

    while True:
        try:
            mode_indicator = "💬" if current_mode == "ask" else "🤖"
            user_input = input(f"\n{mode_indicator} You [{current_mode.upper()}]: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                break
            
            # Check for mode switch commands
            if user_input.lower() == "/ask":
                current_mode = "ask"
                print("Switched to 💬 Ask Mode (standard tools, no computer control)")
                continue
            elif user_input.lower() == "/agent":
                current_mode = "agent"
                print("Switched to 🤖 Agent Mode (autonomous computer control with vision)")
                continue
            
            response = agent.process(user_input, mode=current_mode)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()

