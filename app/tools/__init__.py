"""
Tools module containing OS-level operation functions and web/image utilities.
"""

from .os_ops import (
    get_volume,
    set_volume,
    get_mouse_speed,
    set_mouse_speed,
    get_caps_lock_state,
    set_caps_lock,
    create_and_open_file,
    create_folder,
    list_directory,
    get_desktop_path,
)
from .web_search import web_search
from .image_tools import find_image
from .ppt_tools import create_presentation
from .registry import ToolRegistry

__all__ = [
    "get_volume",
    "set_volume",
    "get_mouse_speed",
    "set_mouse_speed",
    "get_caps_lock_state",
    "set_caps_lock",
    "create_and_open_file",
    "create_folder",
    "list_directory",
    "get_desktop_path",
    "web_search",
    "find_image",
    "create_presentation",
    "ToolRegistry",
]