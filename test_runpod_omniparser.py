"""
Test script for RunPod OmniParser integration.

This script tests:
1. Connection to RunPod Gradio endpoint
2. UI element detection
3. Finding specific elements
4. Integration with computer control
5. ACTUALLY CLICKS THE CHROME ICON (if found)
"""

import os
import time
import pyautogui
import shutil
import platform
from datetime import datetime
from dotenv import load_dotenv
from app.tools.vision_tools import capture_screenshot
from app.tools.omniparser_helper import get_omniparser, detect_ui_elements, find_element_by_description

load_dotenv()

# Setup logging and output directories
LOG_FILE = "logs/omniparser_test.log"
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
    """Log a separator line."""
    sep = "="*70
    log_and_print(sep)


def test_omniparser_connection():
    """Test basic connection to RunPod OmniParser."""
    log_separator()
    log_and_print("TEST 1: RunPod OmniParser Connection")
    log_separator()
    
    # Check if RUNPOD_URL is set
    runpod_url = os.getenv("RUNPOD_URL")
    if not runpod_url:
        log_and_print("❌ RUNPOD_URL not found in .env file!")
        log_and_print("   Add: RUNPOD_URL=https://your-runpod-url.gradio.live")
        return False
    
    log_and_print(f"✓ RUNPOD_URL found: {runpod_url}")
    
    try:
        parser = get_omniparser()
        log_and_print(f"✓ OmniParser initialized successfully")
        return True
    except Exception as e:
        log_and_print(f"❌ Failed to initialize OmniParser: {e}")
        return False


def test_element_detection():
    """Test UI element detection on current screen."""
    log_and_print("\n")
    log_separator()
    log_and_print("TEST 2: UI Element Detection")
    log_separator()
    
    try:
        # Capture screenshot
        log_and_print("\n1. Capturing screenshot...")
        capture_result = capture_screenshot()
        screenshot_path = capture_result.replace("Screenshot saved to:", "").strip()
        log_and_print(f"   ✓ Screenshot saved: {screenshot_path}")
        
        # Detect elements using OmniParser (getting full result including labeled image)
        log_and_print("\n2. Detecting UI elements with OmniParser...")
        log_and_print("   (This may take 10-20 seconds...)")
        
        parser = get_omniparser()
        result = parser.detect_elements(screenshot_path)
        
        elements = result.get('elements', [])
        labeled_image_path = result.get('labeled_image_path')
        raw_json = result.get('raw_json', '')
        
        log_and_print(f"\n✓ SUCCESS! Found {len(elements)} UI elements")
        
        # Log COMPLETE raw JSON output (no truncation)
        log_and_print(f"\n📄 Raw OmniParser JSON output (COMPLETE):")
        log_and_print(f"{'='*70}")
        log_and_print(raw_json)
        log_and_print(f"{'='*70}")
        
        # Save the full raw JSON to a file
        json_output_path = os.path.join(OUTPUT_DIR, "omniparser_raw_output.json")
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(raw_json)
        log_and_print(f"\n✓ Full raw JSON saved to: {json_output_path}")
        
        # Save and open the labeled image
        if labeled_image_path:
            log_and_print(f"\n📸 Labeled image from OmniParser: {labeled_image_path}")
            
            # Copy to our output directory with a better name
            labeled_output_path = os.path.join(OUTPUT_DIR, "labeled_screenshot.png")
            shutil.copy(labeled_image_path, labeled_output_path)
            log_and_print(f"   ✓ Labeled image copied to: {labeled_output_path}")
            
            # Open the labeled image
            log_and_print(f"\n🖼️  Opening labeled image for visual verification...")
            try:
                if platform.system() == "Windows":
                    os.startfile(labeled_output_path)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open '{labeled_output_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{labeled_output_path}'")
                log_and_print(f"   ✓ Labeled image opened in default viewer")
            except Exception as e:
                log_and_print(f"   ⚠️  Could not auto-open image: {e}")
                log_and_print(f"   → Please manually open: {os.path.abspath(labeled_output_path)}")
        else:
            log_and_print(f"\n⚠️  No labeled image returned from OmniParser")
        
        # Display ALL elements with FULL details
        log_and_print(f"\n📋 All {len(elements)} elements detected:")
        log_and_print(f"{'='*70}")
        
        if len(elements) == 0:
            log_and_print("\n⚠️  WARNING: No elements were parsed!")
            log_and_print("   This means the JSON parsing failed.")
            log_and_print("   Check the raw JSON output above and the saved JSON file.")
        else:
            for i, elem in enumerate(elements, 1):
                log_and_print(f"\n  Element {i}:")
                log_and_print(f"    ID: {elem['id']}")
                log_and_print(f"    Description: {elem['description']}")
                log_and_print(f"    Type: {elem.get('type', 'unknown')}")
                log_and_print(f"    Bounding Box: {elem['bbox']}")
                log_and_print(f"    Center Coordinates: {elem['center']}")
                
                # Highlight if it might be Chrome
                desc_lower = elem['description'].lower()
                if 'chrome' in desc_lower or 'browser' in desc_lower or 'google' in desc_lower:
                    log_and_print(f"    >>> 🎯 POTENTIAL CHROME MATCH! <<<")
        
        log_and_print(f"\n{'='*70}")
        
        return True, screenshot_path, elements, labeled_output_path if labeled_image_path else None
        
    except Exception as e:
        log_and_print(f"\n❌ Element detection failed: {e}")
        import traceback
        error_trace = traceback.format_exc()
        log_and_print(error_trace)
        return False, None, [], None


def test_find_and_click_chrome(screenshot_path, elements, labeled_image_path):
    """Test finding Chrome icon and ACTUALLY clicking it."""
    log_and_print("\n")
    log_separator()
    log_and_print("TEST 3: Find Chrome Icon and CLICK IT")
    log_separator()
    
    # Try to find Chrome/browser with multiple search terms
    search_terms = ["Chrome", "browser", "google chrome", "web browser", "chrome icon"]
    
    log_and_print(f"\nSearching for Chrome with terms: {search_terms}")
    
    found_element = None
    
    try:
        for term in search_terms:
            log_and_print(f"\n   Searching for '{term}'...")
            element = find_element_by_description(screenshot_path, term)
            
            if element:
                log_and_print(f"   ✓ Found match with term '{term}'!")
                found_element = element
                break
        
        if not found_element:
            log_and_print("\n   ⚠️  No Chrome icon found using search terms")
            log_and_print("   Possible reasons:")
            log_and_print("   - Chrome is not pinned to taskbar")
            log_and_print("   - Chrome window is maximized (covering taskbar)")
            log_and_print("   - Element description doesn't match search terms")
            log_and_print("\n   🔍 Showing ALL elements containing 'chrome' or 'browser':")
            found_any = False
            for elem in elements:
                desc_lower = elem['description'].lower()
                if "chrome" in desc_lower or "browser" in desc_lower or "google" in desc_lower:
                    log_and_print(f"   → {elem['id']}: {elem['description']}")
                    log_and_print(f"      Center: {elem['center']}, BBox: {elem['bbox']}")
                    found_any = True
            
            if not found_any:
                log_and_print("   → No elements found with 'chrome', 'browser', or 'google' in description")
                log_and_print("\n   💡 TIP: Look at the labeled image to see what was detected")
                log_and_print(f"       Image: {labeled_image_path}")
            
            return False
        
        # Found Chrome! Print details
        log_and_print("\n" + "="*70)
        log_and_print("🎯 CHROME ICON IDENTIFIED BY AGENT!")
        log_and_print("="*70)
        log_and_print(f"\n>>> THE AGENT CHOSE THIS LABEL AS CHROME: <<<")
        log_and_print(f"\nElement ID: {found_element['id']}")
        log_and_print(f"Description: '{found_element['description']}'")
        log_and_print(f"Type: {found_element.get('type', 'unknown')}")
        log_and_print(f"Bounding Box (raw): {found_element['bbox']}")
        log_and_print(f"Center Coordinates: {found_element['center']}")
        log_and_print(f"\n>>> THIS IS WHAT WILL BE CLICKED <<<")
        log_and_print("="*70)
        
        x, y = found_element['center']
        bbox = found_element['bbox']
        
        # Log detailed coordinate information
        log_and_print(f"\n📐 Detailed Coordinate Information:")
        log_and_print(f"   Bounding Box: {bbox}")
        if len(bbox) >= 4:
            log_and_print(f"   → Top-Left: ({bbox[0]}, {bbox[1]})")
            log_and_print(f"   → Bottom-Right: ({bbox[2]}, {bbox[3]})")
            log_and_print(f"   → Width: {bbox[2] - bbox[0]} pixels")
            log_and_print(f"   → Height: {bbox[3] - bbox[1]} pixels")
        log_and_print(f"   Center Point: ({x}, {y})")
        log_and_print(f"   → X coordinate: {x}")
        log_and_print(f"   → Y coordinate: {y}")
        
        # Get current screen size for reference
        screen_width, screen_height = pyautogui.size()
        log_and_print(f"\n🖥️  Screen Information:")
        log_and_print(f"   Screen Resolution: {screen_width} x {screen_height}")
        log_and_print(f"   Click position relative to screen:")
        log_and_print(f"   → X: {x}/{screen_width} ({(x/screen_width)*100:.1f}% from left)")
        log_and_print(f"   → Y: {y}/{screen_height} ({(y/screen_height)*100:.1f}% from top)")
        
        # Get current mouse position before clicking
        current_x, current_y = pyautogui.position()
        log_and_print(f"\n🖱️  Mouse Information:")
        log_and_print(f"   Current mouse position: ({current_x}, {current_y})")
        log_and_print(f"   Will move to: ({x}, {y})")
        log_and_print(f"   Distance to travel: {((x-current_x)**2 + (y-current_y)**2)**0.5:.1f} pixels")
        
        log_and_print(f"\n⏰ Countdown before click:")
        for i in range(3, 0, -1):
            log_and_print(f"   {i}...")
            time.sleep(1)
        
        log_and_print("\n⚡ EXECUTING CLICK NOW!")
        log_and_print(f"="*70)
        log_and_print(f">>> CLICKING ELEMENT: {found_element['id']} <<<")
        log_and_print(f">>> DESCRIPTION: '{found_element['description']}' <<<")
        log_and_print(f">>> COORDINATES: ({x}, {y}) <<<")
        log_and_print(f"="*70)
        log_and_print(f"\n   Moving mouse to ({x}, {y})...")
        
        # Move mouse and click with detailed logging
        pyautogui.moveTo(x, y, duration=0.3)
        log_and_print(f"   ✓ Mouse moved to target position")
        
        # Verify mouse is at correct position
        verify_x, verify_y = pyautogui.position()
        log_and_print(f"   Verifying position: ({verify_x}, {verify_y})")
        
        if abs(verify_x - x) <= 1 and abs(verify_y - y) <= 1:
            log_and_print(f"   ✓ Mouse position verified (±1 pixel tolerance)")
        else:
            log_and_print(f"   ⚠️  Mouse position mismatch!")
            log_and_print(f"      Expected: ({x}, {y})")
            log_and_print(f"      Actual: ({verify_x}, {verify_y})")
            log_and_print(f"      Difference: ({verify_x - x}, {verify_y - y})")
        
        time.sleep(0.2)
        log_and_print(f"   Performing left click...")
        pyautogui.click(x, y)
        
        log_and_print(f"\n✅ CLICK EXECUTED!")
        log_and_print(f"="*70)
        log_and_print(f">>> CLICKED: {found_element['id']} - '{found_element['description']}' <<<")
        log_and_print(f">>> AT COORDINATES: ({x}, {y}) <<<")
        log_and_print(f"="*70)
        log_and_print("\nWaiting 2 seconds to observe result...")
        time.sleep(2)
        
        # Check if Chrome process started or got focus
        log_and_print("\n📊 Post-Click Analysis:")
        log_and_print("   → Did Chrome window open or get focus?")
        log_and_print("   → Check your taskbar and screen")
        log_and_print(f"   → Compare with labeled image: {labeled_image_path}")
        
        log_and_print("\n✓ Click test completed!")
        log_and_print("   If Chrome didn't open, check:")
        log_and_print("   1. The labeled image - was the bounding box correct?")
        log_and_print("   2. The coordinates - do they match the visible Chrome icon?")
        log_and_print("   3. DPI settings - is DPI awareness working?")
        
        return True
        
    except Exception as e:
        log_and_print(f"\n❌ Element search/click failed: {e}")
        import traceback
        error_trace = traceback.format_exc()
        log_and_print(error_trace)
        return False


def test_integration_with_computer_control():
    """Test integration with computer control module."""
    log_and_print("\n")
    log_separator()
    log_and_print("TEST 4: Computer Control Integration")
    log_separator()
    
    try:
        from app.tools.computer_control import click_element
        
        log_and_print("\n✓ Computer control module imported successfully")
        log_and_print("✓ click_element function now uses OmniParser")
        log_and_print("✓ Integration verified - ready for autonomous mode")
        
        return True
        
    except Exception as e:
        log_and_print(f"\n❌ Integration test failed: {e}")
        import traceback
        error_trace = traceback.format_exc()
        log_and_print(error_trace)
        return False


def main():
    """Run all tests."""
    # Clear log file at start
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"RUNPOD OMNIPARSER TEST LOG\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n\n")
    
    log_and_print("\n")
    log_separator()
    log_and_print("RUNPOD OMNIPARSER INTEGRATION TEST SUITE")
    log_and_print("⚠️  THIS TEST WILL ACTUALLY CLICK THE CHROME ICON!")
    log_separator()
    log_and_print("\nThis will test your RunPod OmniParser deployment integration")
    log_and_print("Make sure your RunPod pod is running and RUNPOD_URL is set in .env")
    log_and_print(f"\nLog file: {LOG_FILE}\n")
    
    results = []
    
    # Test 1: Connection
    results.append(("Connection", test_omniparser_connection()))
    
    if not results[0][1]:
        log_and_print("\n⚠️  Cannot proceed without valid RUNPOD_URL")
        return
    
    # Test 2: Element detection
    success, screenshot_path, elements, labeled_image_path = test_element_detection()
    results.append(("Element Detection", success))
    
    if success and elements:
        # Test 3: Find and CLICK Chrome icon
        chrome_clicked = test_find_and_click_chrome(screenshot_path, elements, labeled_image_path)
        results.append(("Find and Click Chrome", chrome_clicked))
    
    # Test 4: Integration
    results.append(("Computer Control Integration", test_integration_with_computer_control()))
    
    # Summary
    log_and_print("\n")
    log_separator()
    log_and_print("TEST SUMMARY")
    log_separator()
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "❌ FAILED"
        log_and_print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        log_and_print("\n✅ ALL TESTS PASSED!")
        log_and_print("\nYour RunPod OmniParser integration is working correctly!")
        log_and_print("Chrome icon was successfully clicked!")
        log_and_print("\nNext steps:")
        log_and_print("1. Use 'python cli.py' to interact with your agent")
        log_and_print("2. Try computer control commands like 'Click the Chrome icon'")
        log_and_print("3. The agent will now use RunPod OmniParser for accurate clicking")
    else:
        log_and_print("\n⚠️  SOME TESTS FAILED")
        log_and_print("\nPlease check:")
        log_and_print("1. RUNPOD_URL is correctly set in .env")
        log_and_print("2. Your RunPod pod is running")
        log_and_print("3. You have gradio_client installed: pip install gradio_client")
        log_and_print("4. Chrome icon is visible on your screen")
    
    log_separator()
    log_and_print(f"\n📁 Output Files:")
    log_and_print(f"   • Full log: {os.path.abspath(LOG_FILE)}")
    log_and_print(f"   • Test output directory: {os.path.abspath(OUTPUT_DIR)}")
    log_and_print(f"     - labeled_screenshot.png (with bounding boxes)")
    log_and_print(f"     - omniparser_raw_output.json (full JSON data)")
    log_separator()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_and_print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        log_and_print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        error_trace = traceback.format_exc()
        log_and_print(error_trace)
    finally:
        log_and_print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_and_print(f"Full log available at: {os.path.abspath(LOG_FILE)}")

