from app.tools.registry import ToolRegistry
from app.tools import os_ops
from app.core.agent import Agent
import os

def main():
    # 1. Setup the "Hands" (Registry)
    registry = ToolRegistry(safe_mode=True)
    
    # Register atomic tools
    registry.register("set_volume", os_ops.set_volume, "Sets master volume (0-100).", sensitive=False)
    registry.register("get_volume", os_ops.get_volume, "Gets current volume.", sensitive=False)
    registry.register("set_mouse_speed", os_ops.set_mouse_speed, "Sets mouse speed (1-20).", sensitive=True)
    registry.register("set_caps_lock", os_ops.set_caps_lock, "Sets Caps Lock (True/False).", sensitive=False)
    
    # Register File & Folder Tools
    registry.register(
        "create_note", 
        os_ops.create_and_open_file, 
        "Creates a text file with content and opens it. path should include filename.",
        sensitive=True
    )
    
    registry.register(
        "create_folder", 
        os_ops.create_folder, 
        "Creates a new folder. Automatically creates parent folders if missing.",
        sensitive=True
    )
    
    registry.register(
        "list_folder", 
        os_ops.list_directory, 
        "Lists files and folders in a specific path.",
        sensitive=False
    )

    # --- NEW ADVANCED TOOLS ---
    registry.register(
        "search_files",
        os_ops.search_files,
        "Searches for a file by name. Default path is User Home. Returns full paths.",
        sensitive=False
    )

    registry.register(
        "launch_app",
        os_ops.launch_app,
        "Launches an application by name (e.g. 'notepad', 'steam', 'chrome').",
        sensitive=True # Confirm before launching apps
    )

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