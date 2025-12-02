import os
import string

def get_available_drives():
    """Returns a list of available drive letters (e.g., ['C:\\', 'D:\\'])"""
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(drive_path)
    return drives

def search_directory_recursive(root_path, target_filename):
    """
    Recursively searches a directory using os.scandir for speed.
    Returns the full path immediately upon finding a match.
    """
    try:
        # scandir is an iterator (faster/lighter than os.walk)
        with os.scandir(root_path) as entries:
            for entry in entries:
                try:
                    # 1. Check if it's the file we want
                    if entry.is_file():
                        # Case-insensitive comparison
                        if target_filename.lower() in entry.name.lower():
                            return entry.path
                    
                    # 2. If directory, recurse into it
                    elif entry.is_dir(follow_symlinks=False):
                        # Optimization: Skip massive system folders that slow us down
                        if entry.name.lower() in ["windows", "program files", "program files (x86)"]:
                            # We search these later, or skip if you prefer speed
                            continue
                            
                        found = search_directory_recursive(entry.path, target_filename)
                        if found:
                            return found
                except (PermissionError, OSError):
                    continue # Skip folders we can't open
    except (PermissionError, OSError):
        return None
    return None

def find_file_everywhere(filename):
    print(f"🕵️ Scanning for '{filename}'...")

    # --- PHASE 1: Smart Search (User Folder) ---
    # 90% of user files are here. We search this first for a "quick win".
    user_home = os.path.expanduser("~")
    print(f"   > Checking User Home ({user_home})...")
    result = search_directory_recursive(user_home, filename)
    if result: 
        return result

    # --- PHASE 2: Other Drives (D:, E:, etc) ---
    drives = get_available_drives()
    system_drive = os.getenv("SystemDrive", "C:") + "\\"
    
    for drive in drives:
        # Skip C: for now (we did User folder, will do rest of C: last)
        if drive.upper() == system_drive.upper():
            continue
            
        print(f"   > Checking Drive {drive}...")
        result = search_directory_recursive(drive, filename)
        if result: 
            return result

    # --- PHASE 3: The Rest of C: (Deep Scan) ---
    # If we still haven't found it, check the root of C: (excluding what we already checked)
    print(f"   > Checking System Root ({system_drive}) - This may take time...")
    
    # We use os.walk here because we need to carefully skip the User folder we already did
    for root, dirs, files in os.walk(system_drive):
        # Optimization: Don't re-scan Users
        if "Users" in dirs:
            dirs.remove("Users") 
            
        for name in files:
            if filename.lower() in name.lower():
                return os.path.join(root, name)
                
    return None

# --- Usage ---
if __name__ == "__main__":
    target = "hearthstone.exe"
    
    match = find_file_everywhere(target)
    
    if match:
        print(f"\n✅ Found: {match}")
    else:
        print("\n❌ File not found anywhere.")