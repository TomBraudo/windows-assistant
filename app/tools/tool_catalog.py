"""
Central catalog of high-level tools available to the Windows agent.

This is the single source of truth for the refiner's understanding of tools.
When adding new top-level tools, update TOOL_CATALOG here so the refiner can
recommend them to the main agent.
"""

from typing import List, Dict


TOOL_CATALOG: List[Dict[str, str]] = [
    # Basic System Controls
    {
        "name": "set_volume",
        "description": "Sets master volume (0-100).",
    },
    {
        "name": "get_volume",
        "description": "Gets current master volume level.",
    },
    {
        "name": "set_mouse_speed",
        "description": "Sets mouse speed (1-20).",
    },
    {
        "name": "set_caps_lock",
        "description": "Sets Caps Lock on or off (True/False).",
    },
    
    # File & Folder Operations
    {
        "name": "create_note",
        "description": "Creates a text or Word (.docx) file with given content and opens it for the user.",
    },
    {
        "name": "create_folder",
        "description": "Creates a new folder. Automatically creates parent folders if missing.",
    },
    {
        "name": "list_folder",
        "description": "Lists files and folders in a specific path.",
    },
    {
        "name": "search_files",
        "description": "Search for files by name on disk, optionally within a specific directory tree.",
    },
    
    # App Launching & File Opening
    {
        "name": "smart_search_and_open",
        "description": "Find and open files or executables on disk using a smart, multi-phase search.",
    },
    {
        "name": "launch_app",
        "description": "Launch desktop applications by resolving their real executable via web search and locating them on disk.",
    },
    {
        "name": "open_url",
        "description": "Open a specific URL in the browser (preferably Chrome) for the user.",
    },
    
    # Web & Research Tools
    {
        "name": "web_search",
        "description": "Search the web for information or to discover correct filenames/executables.",
    },
    {
        "name": "find_image",
        "description": "Search the web for an image, download it locally, and return its path for later insertion into documents or slides.",
    },
    
    # Document Creation
    {
        "name": "create_presentation",
        "description": "Create and open a PowerPoint (.pptx) file with a title, bullet points, and optional image. Use 'path' parameter for the file (e.g., 'My_Presentation.pptx' saves to Desktop, or provide full path).",
    },
]


def get_refiner_tools_text() -> str:
    """
    Returns a human-readable list of tools and descriptions for use
    inside the refiner's system prompt.
    """
    lines = ["The agent has access to these tools (names are for your understanding only):"]
    for tool in TOOL_CATALOG:
        lines.append(f"- {tool['name']}: {tool['description']}")
    return "\n".join(lines)


def get_all_tool_names() -> List[str]:
    """Return a list of all tool names in the catalog."""
    return [t["name"] for t in TOOL_CATALOG]


def get_tool_description(tool_name: str) -> str:
    """Get the description for a specific tool by name."""
    for tool in TOOL_CATALOG:
        if tool["name"] == tool_name:
            return tool["description"]
    return ""


def validate_tool_name(tool_name: str) -> bool:
    """Check if a tool name exists in the catalog."""
    return tool_name in get_all_tool_names()



