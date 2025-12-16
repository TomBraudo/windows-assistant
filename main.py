from app.tools.registry import ToolRegistry
from app.tools import os_ops
from app.tools.web_search import web_search
from app.tools.image_tools import find_image
from app.tools.ppt_tools import create_presentation
from app.tools import computer_control
from app.tools.tool_catalog import get_tool_description
from app.core.agent import Agent
import os

def main():
    # 1. Setup the "Hands" (Registry)
    # All tool names and descriptions come from tool_catalog.py (single source of truth)
    registry = ToolRegistry(safe_mode=True)
    
    # Register tools using canonical names from TOOL_CATALOG
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
    
    # Computer Control (Mouse & Keyboard)
    registry.register("click_at_coordinates", computer_control.click_at_coordinates, get_tool_description("click_at_coordinates"), sensitive=True)
    registry.register("click_element", computer_control.click_element, get_tool_description("click_element"), sensitive=True)
    registry.register("type_text", computer_control.type_text, get_tool_description("type_text"), sensitive=True)
    registry.register("press_key", computer_control.press_key, get_tool_description("press_key"), sensitive=False)
    registry.register("hotkey", computer_control.hotkey, get_tool_description("hotkey"), sensitive=True)
    registry.register("scroll", computer_control.scroll, get_tool_description("scroll"), sensitive=False)
    registry.register("move_mouse", computer_control.move_mouse, get_tool_description("move_mouse"), sensitive=False)
    registry.register("get_mouse_position", computer_control.get_mouse_position, get_tool_description("get_mouse_position"), sensitive=False)
    registry.register("drag_to", computer_control.drag_to, get_tool_description("drag_to"), sensitive=True)

    # 2. Setup the "Brain" (Agent)
    agent = Agent(registry=registry)
    
    print("🤖 Windows Agent Online. Type 'quit' to exit.")
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