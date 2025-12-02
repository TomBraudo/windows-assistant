"""
OS-level operations for Windows control.
Contains functions for volume, mouse speed, caps lock, file operations, search, and launching.
"""

import ctypes
import os
import re
import subprocess
import shutil
import string
import webbrowser
from ctypes import wintypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from docx import Document

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


# --- Helper: Drive & File Search (ported from test_find_files) ---
def _get_available_drives():
    """Returns a list of available drive letters (e.g., ['C:\\', 'D:\\'])."""
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(drive_path)
    return drives


def _search_directory_recursive(root_path: str, target_filename: str):
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
                        # Case-insensitive comparison, substring match
                        if target_filename.lower() in entry.name.lower():
                            return entry.path

                    # 2. If directory, recurse into it
                    elif entry.is_dir(follow_symlinks=False):
                        # Optimization: Skip massive system folders that slow us down
                        if entry.name.lower() in ["windows", "program files", "program files (x86)"]:
                            # These can be searched later if needed
                            continue

                        found = _search_directory_recursive(entry.path, target_filename)
                        if found:
                            return found
                except (PermissionError, OSError):
                    # Skip entries we can't access
                    continue
    except (PermissionError, OSError):
        return None
    return None


def smart_find_file(filename: str):
    """
    Smart, system-wide search for a file name.

    Strategy (ported from test_find_files.py):
    1) Search the current user's home directory first (fast / high hit rate).
    2) Search all other available drives except the system drive.
    3) Deep scan the rest of the system drive, excluding the Users folder
       (which was already covered in step 1).

    Returns:
        - Full path to the first matching file (case-insensitive, substring match),
          or None if nothing is found.
    """
    print(f"Searching for '{filename}' across the system...")

    # --- PHASE 1: Smart Search (User Folder) ---
    user_home = os.path.expanduser("~")
    print(f"   > Checking User Home ({user_home})...")
    result = _search_directory_recursive(user_home, filename)
    if result:
        return result

    # --- PHASE 2: Other Drives (D:, E:, etc) ---
    drives = _get_available_drives()
    system_drive = os.getenv("SystemDrive", "C:") + "\\"

    for drive in drives:
        # Skip system drive for now (user folder already scanned, rest done in phase 3)
        if drive.upper() == system_drive.upper():
            continue

        print(f"   > Checking Drive {drive}...")
        result = _search_directory_recursive(drive, filename)
        if result:
            return result

    # --- PHASE 3: The Rest of the System Drive (Deep Scan) ---
    print(f"   > Checking System Root ({system_drive}) - this may take time...")

    # Use os.walk here because we need to carefully skip the User folder we already scanned
    for root, dirs, files in os.walk(system_drive):
        # Optimization: Don't re-scan Users
        if "Users" in dirs:
            dirs.remove("Users")

        for name in files:
            if filename.lower() in name.lower():
                return os.path.join(root, name)

    return None


def _normalize_search_query(raw: str) -> str:
    """
    Normalizes a raw user query into a clean search token.

    - Strips surrounding quotes and whitespace.
    - Strips a leading '@' used to reference filenames (e.g. '@test_find_files.py').
    """
    if raw is None:
        return ""

    # Basic cleaning
    q = raw.strip().strip('"').strip("'")

    # Strip leading '@' used for filename references
    if q.startswith("@"):
        q = q[1:]

    q = q.strip()

    # If the query looks like a full sentence that happens to mention a filename
    # (e.g. "Find and open the file named offside_rule_report.docx"),
    # extract just the last "word.ext" style token.
    matches = re.findall(r"([^\s\\/:*?\"<>|]+\.[^\s\\/:*?\"<>|]+)", q)
    if matches:
        q = matches[-1]

    return q.strip()


def _looks_like_explicit_filename(token: str) -> bool:
    """
    Heuristic: does this look like a concrete filename (e.g. 'test_find_files.py')?
    """
    if not token:
        return False
    # Contains a path separator or a dot that isn't the first/last char
    if any(sep in token for sep in ("/", "\\")):
        return True
    dot_idx = token.rfind(".")
    if dot_idx > 0 and dot_idx < len(token) - 1:
        return True
    return False


def _candidate_executables_from_name(name: str):
    """
    Given a bare app/game name like 'hearthstone' or 'fortnite',
    generate a small ordered list of plausible executable names.
    """
    base = name.strip().strip('"').strip("'")
    if not base:
        return []

    candidates = []
    simple = base
    title = base.title()

    # Simple .exe forms
    candidates.append(f"{simple}.exe")
    if title.lower() != simple.lower():
        candidates.append(f"{title}.exe")

    # Common launcher/client patterns
    candidates.append(f"{simple}Launcher.exe")
    candidates.append(f"{title}Launcher.exe")
    candidates.append(f"{simple}Client.exe")
    candidates.append(f"{title}Client.exe")

    # De-duplicate preserving order
    seen = set()
    uniq = []
    for c in candidates:
        if c.lower() not in seen:
            uniq.append(c)
            seen.add(c.lower())
    return uniq

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
    Creates a file with the given content and opens it.

    Behavior:
    - If the path ends with '.docx', a real Word document is created using python-docx,
      with `content` inserted as a paragraph.
    - For all other extensions, a UTF-8 text file is created with the raw content.
    """
    try:
        if not os.path.isabs(path):
            path = os.path.join(get_desktop_path(), path)
        full_path = os.path.abspath(path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f"DEBUG: Writing to {full_path}")

        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        if ext == ".docx":
            # Create a real Word document
            doc = Document()
            # Simple behavior: single paragraph with the provided content
            doc.add_paragraph(content)
            doc.save(full_path)
        else:
            # Fallback: plain text file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        if not os.path.exists(full_path):
            return f"Error: Write operation finished, but file not found at {full_path}"

        try:
            os.startfile(full_path)
        except Exception as e:
            # File exists but couldn't be opened; report gracefully
            return f"File created at: {full_path}, but failed to open it automatically: {e}"

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
    High-level wrapper around the smart file search.

    - If `search_path` is provided, only that directory tree is searched (fast, targeted).
    - Otherwise, uses the full smart system-wide search strategy from `smart_find_file`.

    Returns a human-readable string (for the agent) describing the result.
    """
    try:
        # If a specific path is provided, do a focused recursive scan there
        if search_path:
            if not os.path.exists(search_path):
                return f"Error: Path does not exist: {search_path}"

            print(f"Searching for '{filename}' in '{search_path}'...")
            matches = []

            # Use scandir-based recursion starting from the given path
            result = _search_directory_recursive(search_path, filename)
            if result:
                matches.append(result)

            if matches:
                # For now `max_results` is effectively 1 because `_search_directory_recursive`
                # returns on first match; this keeps behavior consistent with the smart search.
                return "Found matches:\n" + "\n".join(matches)

            return f"No files found named '{filename}' under {search_path}."

        # No specific path: use the full smart system-wide search
        result = smart_find_file(filename)
        if result:
            return f"Found: {result}"

        return f"No files found named '{filename}' anywhere that I can access."

    except Exception as e:
        return f"Search failed: {str(e)}"


def smart_search_and_open(target: str):
    """
    Smart entry point for the agent when the user says things like:

    - "open @test_find_files.py"
    - "find test_find_files.py"
    - "start hearthstone"
    - "launch fortnite"

    Behavior:
    - If the target looks like an explicit filename or path (has an extension or slash),
      search for that exact filename using the smart system-wide search, then open it.
    - If it's a bare name (no extension), assume it's an app/game and try a small set
      of plausible executable names (e.g. 'hearthstone.exe', 'Hearthstone.exe',
      'hearthstoneLauncher.exe', etc.), preferring the first one that exists.
    """
    try:
        query = _normalize_search_query(target)
        if not query:
            return "Error: No target provided to search/open."

        # Case 1: explicit filename/path
        if _looks_like_explicit_filename(query):
            path = smart_find_file(query)
            if not path:
                return f"Could not find a file matching '{query}'."

            try:
                os.startfile(path)
            except Exception as e:
                return f"Found '{path}' but failed to open it: {e}"

            return f"Opened file: {path}"

        # Case 2: bare app/game name → try candidate executables
        candidates = _candidate_executables_from_name(query)
        if not candidates:
            return f"Could not infer an executable from '{query}'."

        last_error = None
        for exe_name in candidates:
            path = smart_find_file(exe_name)
            if not path:
                continue

            try:
                os.startfile(path)
                return f"Launcher started: {path}"
            except Exception as e:
                # Remember but keep trying other candidates
                last_error = f"Found '{path}' but failed to launch it: {e}"

        if last_error:
            return last_error

        pretty_candidates = ", ".join(candidates)
        return (
            f"Could not find a suitable launcher for '{query}'. "
            f"Tried candidates: {pretty_candidates}"
        )

    except Exception as e:
        return f"Smart search/open failed: {str(e)}"

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


def open_url(url: str, force_chrome: bool = True):
    """
    Opens a URL in the browser.

    - If force_chrome is True, it will first try to open the URL in Chrome
      (assuming 'chrome' is available on PATH).
    - If that fails, it falls back to the system default browser.
    """
    try:
        if force_chrome:
            try:
                # Use Windows 'start' with chrome; relies on chrome in PATH
                subprocess.Popen(f'start "" chrome "{url}"', shell=True)
                return f"Opened in Chrome: {url}"
            except Exception:
                # Fall back to default browser below
                pass

        webbrowser.open(url)
        return f"Opened URL in default browser: {url}"
    except Exception as e:
        return f"Failed to open URL '{url}': {e}"