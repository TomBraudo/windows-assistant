import subprocess
import shutil

def find_files(filename: str, max_results: int = 5):
    """
    Uses the 'Everything' CLI to find files instantly.
    
    Args:
        filename (str): The fuzzy name to search (e.g., "todo.tx")
        max_results (int): How many matches to return.
        
    Returns:
        list[str]: A list of absolute file paths.
    """
    # 1. Safety Check: Ensure the tool exists
    if not shutil.which("es"):
        print("ERROR: 'es.exe' not found in PATH.")
        return []

    try:
        # 2. Construct the command
        # -n <num>                       : Limit results (prevents getting 100k files)
        # -sort-date-modified-descending : Puts most recent files at the top (Critical for AI)
        command = [
            'es', 
            filename, 
            '-n', str(max_results), 
            '-sort-date-modified-descending' 
        ]
        
        # 3. Execute without opening a black command window (Stealth mode)
        # startupinfo is specific to Windows to hide the console window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            startupinfo=startupinfo
        )
        
        # 4. Process results (remove empty lines)
        paths = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return paths

    except Exception as e:
        print(f"Search failed: {e}")
        return []

# --- Usage Example ---
if __name__ == "__main__":
    target = "todo.tx"
    print(f"🤖 Agent searching for: {target}...")
    
    matches = find_files(target)
    
    if matches:
        print(f"Found {len(matches)} files (Newest first):")
        for path in matches:
            print(f" - {path}")
            
        # The AI usually just wants the very first/best match:
        top_match = matches[0]
        print(f"\nTop Match to open: {top_match}")
    else:
        print("No matches found.")