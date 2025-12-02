"""
OS-level operations for Windows control.
Contains functions for volume, mouse speed, caps lock, file operations, search, and launching.
"""

import ctypes
import os
import subprocess
import shutil
from ctypes import wintypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

# --- Constants & Structures ---
SPI_GETMOUSESPEED = 0x0070
SPI_SETMOUSESPEED = 0x0071
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02
VK_CAPITAL = 0x14
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32

# Define explicit types for SystemParametersInfoW
user32.SystemParametersInfoW.argtypes = [
    wintypes.UINT,
    wintypes.UINT,
    ctypes.c_void_p,
    wintypes.UINT
]
user32.SystemParametersInfoW.restype = wintypes.BOOL

# --- Helper: Find Real Desktop ---
def get_desktop_path():
    """
    Finds the actual Desktop path, accounting for OneDrive redirection.
    """
    home = os.path.expanduser("~")
    onedrive_desktop = os.path.join(home, "OneDrive", "Desktop")
    if os.path.exists(onedrive_desktop):
        return onedrive_desktop
    return os.path.join(home, "Desktop")

# --- 1. Volume Tools ---
def get_volume():
    device = AudioUtilities.GetSpeakers()
    interface = device.EndpointVolume
    return round(interface.GetMasterVolumeLevelScalar() * 100)

def set_volume(level):
    device = AudioUtilities.GetSpeakers()
    interface = device.EndpointVolume
    level = max(0, min(100, int(level)))
    interface.SetMasterVolumeLevelScalar(level / 100, None)
    return f"Volume set to {level}%"

# --- 2. Mouse Speed Tools ---
def get_mouse_speed():
    speed = ctypes.c_int()
    user32.SystemParametersInfoW(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0)
    return speed.value

def set_mouse_speed(speed):
    try:
        speed = int(speed)
    except ValueError:
        return f"Error: '{speed}' is not a valid number."
        
    speed = max(1, min(20, speed))
    print(f"DEBUG: Setting Mouse Speed to {speed}")

    success = user32.SystemParametersInfoW(
        SPI_SETMOUSESPEED, 
        0, 
        ctypes.c_void_p(speed), 
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )
    if not success:
        return f"Failed to set mouse speed (Error {ctypes.get_last_error()})"
    return f"Mouse speed set to {speed}"

# --- 3. Caps Lock Tools ---
def get_caps_lock_state():
    return (user32.GetKeyState(VK_CAPITAL) & 1) == 1

def set_caps_lock(target_state: bool):
    current_state = get_caps_lock_state()
    if current_state != target_state:
        user32.keybd_event(VK_CAPITAL, 0, 0, 0)
        user32.keybd_event(VK_CAPITAL, 0, KEYEVENTF_KEYUP, 0)
        return "Caps Lock toggled."
    return "Caps Lock already in target state."

# --- 4. File Operations ---
def create_and_open_file(path: str, content: str):
    """
    Creates a text file with the given content and opens it.
    """
    try:
        if not os.path.isabs(path):
            path = os.path.join(get_desktop_path(), path)
        full_path = os.path.abspath(path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f"DEBUG: Writing to {full_path}")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        if not os.path.exists(full_path):
            return f"Error: Write operation finished, but file not found at {full_path}"
            
        os.startfile(full_path)
        return f"Success. File created and opened at: {full_path}"
    except Exception as e:
        return f"Error processing file: {str(e)}"

# --- 5. Folder Operations ---
def create_folder(path: str):
    """Creates a new folder."""
    try:
        if not os.path.isabs(path):
            path = os.path.join(get_desktop_path(), path)
        full_path = os.path.abspath(path)
        
        if os.path.exists(full_path):
            return f"Info: Folder already exists at {full_path}"
            
        os.makedirs(full_path, exist_ok=True)
        return f"Success. Created folder: {full_path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def list_directory(path: str):
    """Lists the files and folders in the given directory path."""
    try:
        if not os.path.isabs(path):
            path = os.path.join(get_desktop_path(), path)
        full_path = os.path.abspath(path)
        
        if not os.path.exists(full_path):
            return f"Error: Path does not exist: {full_path}"
        if not os.path.isdir(full_path):
            return f"Error: Path is not a directory: {full_path}"
            
        items = os.listdir(full_path)
        if not items:
            return f"Directory is empty: {full_path}"
        return f"Contents of {full_path}:\n" + "\n".join(f"- {item}" for item in items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

# --- 6. Advanced Tools ---
def search_files(filename: str, search_path: str = None, max_results: int = 5):
    """
    Searches for a file by name.
    Priority 1: Desktop
    Priority 2: C:\\Program Files (x86)
    """
    try:
        # Define search paths: Desktop first, then Program Files (x86)
        paths_to_search = []
        
        if search_path:
            # If user provided a specific path, search ONLY that
            paths_to_search.append(search_path)
        else:
            # Default behavior: Priority list
            paths_to_search.append(get_desktop_path())
            paths_to_search.append(r"C:\Program Files (x86)")

        matches = []
        
        for current_path in paths_to_search:
            if not os.path.exists(current_path):
                continue
                
            print(f"DEBUG: Searching for '{filename}' in {current_path}...")
            
            for root, dirs, files in os.walk(current_path):
                for file in files:
                    if filename.lower() in file.lower():
                        full_path = os.path.join(root, file)
                        matches.append(full_path)
                        if len(matches) >= max_results:
                            return f"Found first {max_results} matches:\n" + "\n".join(matches)
            
            # If we found matches in this priority tier, stop and return them
            # (Don't search Program Files if we found it on Desktop)
            if matches:
                return f"Found matches in {current_path}:\n" + "\n".join(matches)

        return f"No files found named '{filename}' in checked locations."
        
    except Exception as e:
        return f"Search failed: {str(e)}"

def launch_app(app_name: str):
    """
    Launches an application by name or path.
    """
    try:
        print(f"DEBUG: Launching {app_name}")
        subprocess.Popen(f"start {app_name}", shell=True)
        return f"Command sent to launch: {app_name}"
    except Exception as e:
        return f"Failed to launch {app_name}: {str(e)}"