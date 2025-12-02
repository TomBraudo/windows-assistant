"""
OS-level operations for Windows control.
Contains functions for volume, mouse speed, caps lock, and other system settings.
"""

import ctypes
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

# --- 1. Volume Tools (Updated for modern pycaw) ---
def get_volume():
    """Returns the current master volume as a percentage (0-100)."""
    device = AudioUtilities.GetSpeakers()
    # Updated: Access the interface directly via the property
    interface = device.EndpointVolume
    # Get scalar volume (0.0 to 1.0) and convert to percentage
    return round(interface.GetMasterVolumeLevelScalar() * 100)

def set_volume(level):
    """Sets the master volume to a specific percentage (0-100)."""
    device = AudioUtilities.GetSpeakers()
    # Updated: Access the interface directly via the property
    interface = device.EndpointVolume
    
    # Clamp value between 0 and 100
    level = max(0, min(100, level))
    interface.SetMasterVolumeLevelScalar(level / 100, None)
    print(f"Volume set to {level}%")

# --- 2. Mouse Speed Tools (using ctypes) ---
def get_mouse_speed():
    """Returns current mouse speed (1-20). Default is usually 10."""
    speed = ctypes.c_int()
    user32.SystemParametersInfoW(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0)
    return speed.value

def set_mouse_speed(speed):
    """Sets mouse speed (Range: 1-20)."""
    speed = max(1, min(20, speed))
    user32.SystemParametersInfoW(
        SPI_SETMOUSESPEED, 
        0, 
        ctypes.c_void_p(speed), 
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )
    print(f"Mouse speed set to {speed}")

# --- 3. Caps Lock Tools (using ctypes) ---
def get_caps_lock_state():
    """Returns True if Caps Lock is ON, False if OFF."""
    return (user32.GetKeyState(VK_CAPITAL) & 1) == 1

def set_caps_lock(target_state: bool):
    """
    Ensures Caps Lock matches the target state (True=ON, False=OFF).
    """
    current_state = get_caps_lock_state()
    
    if current_state != target_state:
        # Simulate Key Press
        user32.keybd_event(VK_CAPITAL, 0, 0, 0)
        # Simulate Key Release
        user32.keybd_event(VK_CAPITAL, 0, KEYEVENTF_KEYUP, 0)
        state_str = "ON" if target_state else "OFF"
        print(f"Caps Lock toggled {state_str}")
    else:
        print("Caps Lock already in target state.")


if __name__ == "__main__":
    set_mouse_speed(20)