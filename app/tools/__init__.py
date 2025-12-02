"""
Tools module containing OS-level operation functions.
"""

from .os_ops import (
    get_volume,
    set_volume,
    get_mouse_speed,
    set_mouse_speed,
    get_caps_lock_state,
    set_caps_lock,
    create_and_open_file,
    create_folder,      # <--- Added
    list_directory,     # <--- Added
    get_desktop_path,
)
from .registry import ToolRegistry

__all__ = [
    "get_volume",
    "set_volume",
    "get_mouse_speed",
    "set_mouse_speed",
    "get_caps_lock_state",
    "set_caps_lock",
    "create_and_open_file",
    "create_folder",    # <--- Added
    "list_directory",   # <--- Added
    "get_desktop_path",
    "ToolRegistry",
]