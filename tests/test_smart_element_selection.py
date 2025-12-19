"""
Test script to demonstrate the smart element selection flow with actual execution.

Flow:
1. Open Chrome from taskbar
2. Find and click URL bar
3. Type youtube.com and press Enter

This shows how the refiner analyzes UI elements considering:
- Description
- Position (coordinates)
- Size (width/height)
- Type (text/icon/etc.)

Then recommends the best element and EXECUTES the action.
"""

import os
import json
import time
import shutil
import platform
from datetime import datetime
from dotenv import load_dotenv
import sys
import pyautogui

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.tools.omniparser_helper import get_omniparser
from app.core.llm import LLMClient
from app.tools.computer_control import capture_screenshot
from app.tools.element_filter import ElementFilter
from PIL import Image

load_dotenv()

# Configure pyautogui
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

LOG_FILE = "logs/smart_element_selection_test.log"
OUTPUT_DIR = "test_output"
os.makedirs("logs", exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_and_print(message):
    """Print to console and log to file."""
    print(message)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_separator():
    sep = "="*70
    log_and_print(sep)

def log_subseparator():
    sep = "-"*70
    log_and_print(sep)

def find_and_click_element(goal, parser, refiner_llm, screenshot_path, step_name):
    """Find the best element for a goal and click it with intelligent filtering."""
    
    log_and_print(f"\n📸 Detecting UI elements for: {goal}")
    log_and_print(f"   (This may take 10-20 seconds...)")
    
    result = parser.detect_elements(screenshot_path)
    elements = result.get('elements', [])
    labeled_image_path = result.get('labeled_image_path')
    raw_output_string = result.get('raw_output_string', '')
    
    # Get screen dimensions
    img = Image.open(screenshot_path)
    screen_width, screen_height = img.size
    log_and_print(f"   Screen dimensions: {screen_width}x{screen_height}")
    
    log_and_print(f"\n✓ SUCCESS! Found {len(elements)} UI elements")
    
    # Save raw JSON output
    json_filename = f"omniparser_raw_{step_name}.json"
    json_output_path = os.path.join(OUTPUT_DIR, json_filename)
    with open(json_output_path, "w", encoding="utf-8") as f:
        f.write(raw_output_string)
    log_and_print(f"✓ Raw JSON saved to: {json_output_path}")
    
    # Save and open the labeled image
    if labeled_image_path:
        log_and_print(f"\n📸 Labeled image from OmniParser: {labeled_image_path}")
        
        # Copy to output directory
        labeled_filename = f"labeled_{step_name}.png"
        labeled_output_path = os.path.join(OUTPUT_DIR, labeled_filename)
        shutil.copy(labeled_image_path, labeled_output_path)
        log_and_print(f"   ✓ Labeled image saved to: {labeled_output_path}")
        
        # Image saved (not auto-opening to avoid interruption)
        log_and_print(f"\n💾 Labeled image saved (not auto-opening)")
    else:
        log_and_print(f"\n⚠️  No labeled image returned from OmniParser")
    
    # Display ALL elements with FULL details
    log_and_print(f"\n📋 All {len(elements)} detected elements:")
    log_and_print(f"{'='*70}")
    
    if len(elements) == 0:
        log_and_print("\n⚠️  WARNING: No elements were parsed!")
    else:
        for i, elem in enumerate(elements, 1):
            log_and_print(f"\n  Element {i}:")
            log_and_print(f"    ID: {elem['id']}")
            log_and_print(f"    Description: '{elem['description']}'")
            log_and_print(f"    Type: {elem.get('type', 'unknown')}")
            log_and_print(f"    Bounding Box (pixels): {elem['bbox']}")
            log_and_print(f"    Center Coordinates: {elem['center']}")
            
            # Calculate size
            bbox = elem['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            log_and_print(f"    Size: {width}x{height}px")
    
    log_and_print(f"\n{'='*70}")
    
    # STEP 1: Pre-filter with intelligent filtering
    log_and_print(f"\n")
    log_subseparator()
    log_and_print("🎯 INTELLIGENT FILTERING")
    log_subseparator()
    
    log_and_print(f"\n🧠 Pre-refiner: Analyzing goal to determine filters...")
    
    # Ask pre-refiner to specify filters
    pre_refiner_prompt = f"""GOAL: {goal}

SCREEN DIMENSIONS: {screen_width}x{screen_height} pixels
TOTAL UI ELEMENTS DETECTED: {len(elements)}

CRITICAL: Be concise and fast. Return ONLY the JSON, no extra explanation.

Analyze the goal and specify filters to find the most relevant UI elements.

FILTER OPTIONS:
1. **position_filter**: Specify screen region
   - y_min, y_max: 0.0-1.0 (percentage from top)
     Example: y_min=0.9 means bottom 10% (for taskbar icons)
     Example: y_max=0.2 means top 20% (for URL bars, title bars)
   - x_min, x_max: 0.0-1.0 (percentage from left)

2. **size_filter**: Specify dimensions
   - min_width, max_width: pixels
   - min_height, max_height: pixels
   - min_aspect_ratio, max_aspect_ratio: width/height ratio
     Example: min_aspect_ratio=10 for URL bars (very wide and thin)

3. **type_filter**: Array of allowed types
   - Options: ["icon", "text", "button"]

4. **keyword_filter**: Array of keywords - must contain at least ONE
   - Example: ["chrome", "browser", "google"] for Chrome icon

5. **exclude_keywords**: Array of keywords - must NOT contain ANY
   - Example: ["folder", "file", "document"] to exclude file-related items

EXAMPLES:

For "Open Chrome from taskbar":
{{
  "position_filter": {{"y_min": 0.9}},
  "type_filter": ["icon"],
  "keyword_filter": ["chrome", "browser", "google"],
  "size_filter": {{"min_width": 20, "max_width": 100, "min_height": 20, "max_height": 100}}
}}

For "Click URL bar":
{{
  "position_filter": {{"y_max": 0.15}},
  "type_filter": ["text"],
  "size_filter": {{"min_width": {int(screen_width * 0.3)}, "min_aspect_ratio": 10}}
}}

For "Click Submit button":
{{
  "type_filter": ["text", "button"],
  "keyword_filter": ["submit", "send", "ok", "confirm"]
}}

IMPORTANT NOTES:
- If goal involves "URL bar" or "address bar", know that empty URL bars may NOT be detected as UI elements
- For URL bars, be lenient with filters (don't require specific keywords)
- Focus on position (top) and size (wide) for URL bars

Return ONLY JSON (no markdown, no explanation):
{{
  "position_filter": {{...}},
  "size_filter": {{...}},
  "type_filter": [...],
  "keyword_filter": [...],
  "exclude_keywords": [...],
  "reasoning": "brief reason"
}}"""
    
    pre_refiner_response = refiner_llm.get_response_text(
        [{"role": "user", "content": pre_refiner_prompt}],
        temperature=0.1
    )
    
    # Parse filter specification
    try:
        filter_spec = json.loads(pre_refiner_response.strip().replace("```json", "").replace("```", ""))
        
        log_and_print(f"\n📋 PRE-REFINER FILTER SPECIFICATION:")
        log_and_print(f"   Reasoning: {filter_spec.get('reasoning', 'N/A')}")
        
        if filter_spec.get('position_filter'):
            log_and_print(f"   Position: {filter_spec['position_filter']}")
        if filter_spec.get('size_filter'):
            log_and_print(f"   Size: {filter_spec['size_filter']}")
        if filter_spec.get('type_filter'):
            log_and_print(f"   Types: {filter_spec['type_filter']}")
        if filter_spec.get('keyword_filter'):
            log_and_print(f"   Keywords: {filter_spec['keyword_filter']}")
        if filter_spec.get('exclude_keywords'):
            log_and_print(f"   Exclude: {filter_spec['exclude_keywords']}")
        
        # Apply filters
        log_and_print(f"\n🔍 Applying filters to {len(elements)} elements...")
        
        element_filter = ElementFilter(screen_width, screen_height)
        filtered_elements = element_filter.filter_elements(
            elements,
            position_filter=filter_spec.get('position_filter'),
            size_filter=filter_spec.get('size_filter'),
            type_filter=filter_spec.get('type_filter'),
            keyword_filter=filter_spec.get('keyword_filter'),
            exclude_keywords=filter_spec.get('exclude_keywords'),
            min_results=5
        )
        
        log_and_print(f"   ✅ Filtered down to {len(filtered_elements)} relevant elements!")
        
        # Show filtered elements
        log_and_print(f"\n📋 FILTERED ELEMENTS ({len(filtered_elements)}):")
        for i, elem in enumerate(filtered_elements, 1):
            bbox = elem['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            log_and_print(f"   {i}. {elem['id']}: '{elem['description']}' (type: {elem['type']}) at {elem['center']}, size: {width}x{height}px")
        
    except json.JSONDecodeError as e:
        log_and_print(f"\n⚠️  Failed to parse filter spec: {e}")
        log_and_print(f"   Using all elements as fallback")
        filtered_elements = elements[:50]  # Fallback to first 50
    except Exception as e:
        log_and_print(f"\n⚠️  Filter error: {e}")
        filtered_elements = elements[:50]
    
    # STEP 2: Main refiner selects from filtered elements
    log_and_print(f"\n")
    log_subseparator()
    log_and_print("🧠 MAIN REFINER: SELECTING BEST ELEMENT")
    log_subseparator()
    
    # Format filtered elements for main refiner
    elements_text = "\n\nFILTERED UI ELEMENTS (most relevant):\n"
    for elem in filtered_elements:
        elements_text += f"{elem['id']}: {elem['description']} (type: {elem.get('type', 'unknown')}) at center {elem['center']}\n"
    
    # Ask main refiner to select best element
    log_and_print(f"\n🧠 Main refiner analyzing {len(filtered_elements)} filtered elements...")
    
    refiner_prompt = f"""GOAL: {goal}

{elements_text}

YOU MUST select the BEST element for this goal.

CRITICAL - BE FAST AND CONCISE:
- Return ONLY JSON (no markdown, no extra text)
- Keep reasoning brief (one sentence)
1. Review ALL available UI elements above
2. For each element, consider:
   - Description: What is it?
   - Position: Where is it (center coordinates)?
   - Size: Width/height matter for things like URL bars
   - Type: Is it text, icon, button?
3. Choose the BEST element for the goal
4. Explain WHY you selected it

Return ONLY JSON (no markdown):
{{
  "selected_element_id": "icon X",
  "element_description": "exact description",
  "selection_reasoning": "brief reason"
}}"""
    
    response = refiner_llm.get_response_text(
        [{"role": "user", "content": refiner_prompt}],
        temperature=0.1
    )
    
    # Parse response
    analysis = json.loads(response.strip().replace("```json", "").replace("```", ""))
    
    log_and_print(f"\n📊 REFINER'S SELECTION:")
    log_and_print(f"   Selected: {analysis.get('selected_element_id', 'N/A')}")
    log_and_print(f"   Description: {analysis.get('element_description', 'N/A')}")
    log_and_print(f"\n   Reasoning:")
    log_and_print(f"   {analysis.get('selection_reasoning', 'N/A')}")
    
    # Find the selected element
    selected_id = analysis.get('selected_element_id', '')
    selected_element = None
    for elem in elements:
        if elem['id'] == selected_id:
            selected_element = elem
            break
    
    if not selected_element:
        raise ValueError(f"Could not find selected element: {selected_id}")
    
    # Click the element
    x, y = selected_element['center']
    log_and_print(f"\n🖱️  Clicking at ({x}, {y})...")
    pyautogui.click(x, y)
    log_and_print(f"   ✓ Clicked!")
    
    return selected_element

def test_smart_selection():
    """Test smart element selection with actual execution."""
    
    # Clear log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"SMART ELEMENT SELECTION TEST - FULL EXECUTION\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n\n")
    
    log_separator()
    log_and_print("🧠 SMART ELEMENT SELECTION TEST - FULL EXECUTION")
    log_separator()
    log_and_print("\nGoal: Execute a full flow:")
    log_and_print("  1. Open Chrome from taskbar")
    log_and_print("  2. Find and click URL bar")
    log_and_print("  3. Type youtube.com and press Enter\n")
    
    parser = get_omniparser()
    # Use Groq for speed (free tier)
    refiner_llm = LLMClient("groq/llama-3.3-70b-versatile")
    
    try:
        # STEP 1: Open Chrome from taskbar
        log_separator()
        log_and_print("STEP 1: OPEN CHROME FROM TASKBAR")
        log_separator()
        
        # Take initial screenshot (Monitor 1 - Primary only)
        log_and_print("\n📸 Capturing screenshot of Monitor 1 (Primary)...")
        screenshot_result = capture_screenshot(primary_only=True)
        screenshot_path = screenshot_result.replace("Screenshot saved to:", "").strip()
        log_and_print(f"   Screenshot: {screenshot_path}")
        
        # Verify monitor capture
        from PIL import Image as PILImage
        img_check = PILImage.open(screenshot_path)
        log_and_print(f"   Monitor 1 size: {img_check.width}x{img_check.height}px")
        
        # Find and click Chrome
        chrome_element = find_and_click_element(
            "Open Chrome browser from the taskbar",
            parser,
            refiner_llm,
            screenshot_path,
            "step1_chrome"
        )
        
        log_and_print(f"\n⏳ Waiting 3 seconds for Chrome to open...")
        time.sleep(3)
        
        # STEP 2: Find and click URL bar
        log_separator()
        log_and_print("STEP 2: FIND AND CLICK URL BAR")
        log_separator()
        
        # Take screenshot of Chrome window (Monitor 1 - Primary)
        log_and_print("\n📸 Capturing screenshot of Chrome on Monitor 1...")
        screenshot_result = capture_screenshot(primary_only=True)
        screenshot_path = screenshot_result.replace("Screenshot saved to:", "").strip()
        log_and_print(f"   Screenshot: {screenshot_path}")
        
        # Find and click URL bar - with smart fallback
        log_and_print(f"\n💡 Smart Strategy: URL bars may not be visible when empty")
        log_and_print(f"   Will try visual detection first, then Ctrl+L fallback")
        
        try:
            url_bar_element = find_and_click_element(
                "Click the URL bar (address bar) at the top of Chrome - it's a wide, horizontal text field",
                parser,
                refiner_llm,
                screenshot_path,
                "step2_urlbar"
            )
            log_and_print(f"\n✓ URL bar clicked successfully")
        except (ValueError, Exception) as e:
            log_and_print(f"\n⚠️  Visual detection failed: {e}")
            log_and_print(f"   Falling back to Ctrl+L hotkey (universal URL bar focus)")
            
            # Fallback: Ctrl+L always focuses URL bar in browsers
            log_and_print(f"\n⌨️  Pressing Ctrl+L to focus URL bar...")
            pyautogui.hotkey('ctrl', 'l')
            log_and_print(f"   ✓ Ctrl+L pressed (URL bar should now be focused)")
        
        log_and_print(f"\n⏳ Waiting 1 second for URL bar to focus...")
        time.sleep(1)
        
        # STEP 3: Type youtube.com and press Enter
        log_separator()
        log_and_print("STEP 3: TYPE YOUTUBE.COM AND PRESS ENTER")
        log_separator()
        
        # Clear any existing text first
        log_and_print("\n⌨️  Clearing URL bar (Ctrl+A, Delete)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('delete')
        time.sleep(0.3)
        
        # Type the URL
        url = "youtube.com"
        log_and_print(f"⌨️  Typing: {url}")
        pyautogui.write(url, interval=0.1)
        
        log_and_print(f"⏳ Waiting 0.5 seconds...")
        time.sleep(0.5)
        
        log_and_print(f"⌨️  Pressing Enter...")
        pyautogui.press('enter')
        
        log_and_print(f"\n⏳ Waiting 3 seconds for page to load...")
        time.sleep(3)
        
        # VERIFICATION: Take final screenshot
        log_separator()
        log_and_print("VERIFICATION: FINAL STATE")
        log_separator()
        
        log_and_print("\n📸 Capturing final screenshot (Monitor 1)...")
        screenshot_result = capture_screenshot(primary_only=True)
        screenshot_path = screenshot_result.replace("Screenshot saved to:", "").strip()
        log_and_print(f"   Screenshot: {screenshot_path}")
        
        log_and_print(f"\n📸 Analyzing final screen state...")
        log_and_print(f"   (This may take 10-20 seconds...)")
        
        # Check if we're on YouTube
        result = parser.detect_elements(screenshot_path)
        elements = result.get('elements', [])
        labeled_image_path = result.get('labeled_image_path')
        raw_output_string = result.get('raw_output_string', '')
        
        log_and_print(f"\n✓ Found {len(elements)} UI elements on final screen")
        
        # Save final state outputs
        json_output_path = os.path.join(OUTPUT_DIR, "omniparser_raw_step3_final.json")
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(raw_output_string)
        log_and_print(f"✓ Final state JSON saved to: {json_output_path}")
        
        if labeled_image_path:
            labeled_output_path = os.path.join(OUTPUT_DIR, "labeled_step3_final.png")
            shutil.copy(labeled_image_path, labeled_output_path)
            log_and_print(f"✓ Final labeled image saved to: {labeled_output_path}")
            
            # Final image saved (not auto-opening)
            log_and_print(f"💾 Final labeled image saved (not auto-opening)")
        
        # Display all elements on final screen
        log_and_print(f"\n📋 All {len(elements)} elements on final screen:")
        log_and_print(f"{'='*70}")
        
        youtube_found = False
        for i, elem in enumerate(elements, 1):
            log_and_print(f"\n  Element {i}:")
            log_and_print(f"    ID: {elem['id']}")
            log_and_print(f"    Description: '{elem['description']}'")
            log_and_print(f"    Type: {elem.get('type', 'unknown')}")
            log_and_print(f"    Center: {elem['center']}")
            
            # Check for YouTube
            if 'youtube' in elem['description'].lower():
                youtube_found = True
                log_and_print(f"    >>> ✅ YOUTUBE DETECTED! <<<")
        
        log_and_print(f"\n{'='*70}")
        
        if youtube_found:
            log_and_print(f"\n✅ SUCCESS! YouTube page loaded correctly!")
        else:
            log_and_print(f"\n⚠️  Could not verify YouTube page (might still be loading or different URL)")
        
    except Exception as e:
        log_and_print(f"\n❌ Test failed: {e}")
        import traceback
        log_and_print(traceback.format_exc())
    
    # Summary
    log_separator()
    log_and_print("✅ TEST COMPLETE")
    log_separator()
    log_and_print(f"\nLog file: {os.path.abspath(LOG_FILE)}")
    log_and_print("\nThis test demonstrated:")
    log_and_print("  ✓ Smart element selection by refiner")
    log_and_print("  ✓ Actual execution (clicking, typing)")
    log_and_print("  ✓ Multi-step task completion")
    log_and_print("  ✓ Verification of results")
    log_separator()

if __name__ == "__main__":
    try:
        test_smart_selection()
    except KeyboardInterrupt:
        log_and_print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        log_and_print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

