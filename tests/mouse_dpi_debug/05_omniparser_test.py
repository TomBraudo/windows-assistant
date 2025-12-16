"""
OmniParser Test - Use Microsoft's OmniParser for UI element detection.

This test uses OmniParser (via Replicate API) to:
1. Detect UI elements on screen
2. Get accurate bounding boxes
3. Find Chrome icon
4. Click it to verify accuracy

OmniParser is specifically trained for UI understanding and provides
pixel-perfect coordinates, unlike general vision models.
"""

import os
import time
import ctypes
from pathlib import Path
from dotenv import load_dotenv

# Set DPI awareness FIRST
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    print("✓ DPI awareness set")
except:
    ctypes.windll.user32.SetProcessDPIAware()
    print("✓ DPI awareness set (fallback)")

# Now import other libraries
from PIL import ImageGrab, Image, ImageDraw, ImageFont
import pyautogui
import replicate

# Load environment variables
load_dotenv()


def capture_screenshot(save_path):
    """Capture full screenshot."""
    print("\n📸 Capturing screenshot...")
    screenshot = ImageGrab.grab()
    screenshot.save(save_path)
    print(f"✓ Screenshot saved: {save_path}")
    print(f"  Resolution: {screenshot.size[0]} x {screenshot.size[1]}")
    return screenshot


def parse_screen_with_omniparser(image_path):
    """
    Use OmniParser API to detect UI elements.
    
    Returns:
        labeled_image_url: URL to image with boxes drawn
        parsed_content: Text description of elements
        label_coordinates: Dict mapping ID -> bounding box coordinates
    """
    print("\n🔍 Sending screenshot to OmniParser API...")
    print("   This may take 10-20 seconds...")
    
    # Check if API key is set
    api_key = os.getenv("REPLICATE_API_TOKEN") or os.getenv("REPLICATE_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ REPLICATE_API_TOKEN not found in .env file!\n"
            "   Add: REPLICATE_API_TOKEN=r8_your_token_here"
        )
    
    os.environ["REPLICATE_API_TOKEN"] = api_key
    
    try:
        print("🚀 Using Private Deployment (A100)...")
        
        # 1. Create the prediction explicitly against the DEPLOYMENT
        prediction = replicate.deployments.predictions.create(
            "tombraudo/omniparser",
            input={
                "image": open(image_path, "rb"),
                "imgsz": 1920,           # Standard desktop width
                "box_threshold": 0.05,   # Sensitivity (0.05 is standard)
                "iou_threshold": 0.1     # Overlap handling
            }
        )
        
        # 2. Deployments are async by default, so we must wait for the result
        prediction.wait()
        
        # 3. Get the output
        output = prediction.output
        
        # Debug: Print raw output structure
        print(f"\n🐛 DEBUG: Raw output type: {type(output)}")
        print(f"🐛 DEBUG: Raw output keys: {output.keys() if isinstance(output, dict) else 'N/A'}")
        
        # Extract results from OmniParser output format
        labeled_image_url = None
        parsed_content = None
        label_coordinates = {}
        
        if isinstance(output, dict):
            # OmniParser returns: {'elements': 'icon 0: {...}\nicon 1: {...}', 'img': <FileOutput>}
            elements_str = output.get("elements", "")
            labeled_image_obj = output.get("img")
            
            # The 'img' is a FileOutput object, we can get its URL
            if labeled_image_obj:
                labeled_image_url = str(labeled_image_obj)
            
            # Parse the elements string
            if elements_str:
                parsed_content = elements_str
                
                # Build label_coordinates dictionary from the elements string
                # Format: "icon 181: {'type': 'icon', 'bbox': [0.572, 0.963, 0.591, 0.994], ...}"
                import ast
                lines = elements_str.strip().split('\n')
                
                for line in lines:
                    try:
                        if ':' in line and 'icon' in line:
                            # Extract icon ID (e.g., "icon 181")
                            id_part = line.split(':', 1)[0].strip()
                            rest = line.split(':', 1)[1].strip()
                            
                            # Parse the dictionary
                            if rest.startswith('{'):
                                element_data = ast.literal_eval(rest)
                                bbox = element_data.get('bbox')
                                
                                if bbox:
                                    label_coordinates[id_part] = bbox
                    except Exception as e:
                        # Skip lines that can't be parsed
                        pass
                
                print(f"🐛 DEBUG: Parsed {len(label_coordinates)} elements with coordinates")
        
        print("\n✓ OmniParser analysis complete!")
        print(f"  Found {len(label_coordinates) if label_coordinates else 0} UI elements")
        
        return labeled_image_url, parsed_content, label_coordinates
        
    except Exception as e:
        print(f"❌ OmniParser API error: {e}")
        raise


def download_labeled_image(url, save_path):
    """Download the labeled image from OmniParser."""
    import requests
    
    print(f"\n📥 Downloading labeled image...")
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✓ Labeled image saved: {save_path}")
        return True
    else:
        print(f"❌ Failed to download: {response.status_code}")
        return False


def find_element_by_description(parsed_content, label_coordinates, search_terms):
    """
    Find UI element by searching for keywords in parsed content.
    
    Args:
        parsed_content: Text description from OmniParser
        label_coordinates: Coordinate mapping
        search_terms: List of keywords to search for (e.g., ["chrome", "browser"])
    
    Returns:
        element_id, bbox, description
    """
    print(f"\n🔎 Searching for element matching: {search_terms}")
    
    # Parse the content (it's usually a string with labeled elements)
    if isinstance(parsed_content, str):
        lines = parsed_content.strip().split('\n')
    else:
        lines = [str(parsed_content)]
    
    matches = []
    
    # Search through parsed content
    for line in lines:
        # Parse the line format: "icon 228: {'type': 'icon', 'content': 'the web browser.'}"
        if ':' in line:
            id_part = line.split(':', 1)[0].strip()
            rest = line.split(':', 1)[1].strip()
            
            # Try to evaluate if it looks like a dict
            try:
                import ast
                if rest.startswith('{'):
                    element_data = ast.literal_eval(rest)
                    content = element_data.get('content', '')
                    element_type = element_data.get('type', '')
                    
                    # Search in content
                    for term in search_terms:
                        if term.lower() in content.lower() or term.lower() in element_type.lower():
                            # Get bbox from label_coordinates
                            bbox = label_coordinates.get(id_part)
                            
                            if bbox:
                                matches.append({
                                    'id': id_part,
                                    'bbox': bbox,
                                    'description': content,
                                    'type': element_type,
                                    'line': line
                                })
                                print(f"  ✓ Found: {id_part} - {element_type}: {content}")
                                break
            except:
                # Fallback: simple text search
                for term in search_terms:
                    if term.lower() in line.lower():
                        bbox = label_coordinates.get(id_part)
                        if bbox:
                            matches.append({
                                'id': id_part,
                                'bbox': bbox,
                                'description': rest,
                                'line': line
                            })
                            print(f"  ✓ Found: {line}")
                            break
    
    if not matches:
        print(f"  ❌ No matches found for {search_terms}")
        print(f"\n  Available elements (first 10):")
        for line in lines[:10]:
            print(f"    - {line}")
        if len(lines) > 10:
            print(f"    ... and {len(lines) - 10} more")
    
    return matches


def get_bbox_center(bbox, screen_width=None, screen_height=None):
    """
    Calculate center point of bounding box.
    
    Args:
        bbox: Can be [x1, y1, x2, y2] or [[x1, y1], [x2, y2]]
              Values can be normalized (0-1) or pixel coordinates
        screen_width: Screen width for converting normalized coords
        screen_height: Screen height for converting normalized coords
    
    Returns:
        (center_x, center_y) in pixels
    """
    if isinstance(bbox[0], (list, tuple)):
        # Format: [[x1, y1], [x2, y2]]
        x1, y1 = bbox[0]
        x2, y2 = bbox[1]
    else:
        # Format: [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox
    
    # Check if coordinates are normalized (0-1 range)
    if x1 <= 1 and y1 <= 1 and x2 <= 1 and y2 <= 1:
        if screen_width and screen_height:
            # Convert normalized to pixel coordinates
            x1 = x1 * screen_width
            y1 = y1 * screen_height
            x2 = x2 * screen_width
            y2 = y2 * screen_height
    
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    
    return center_x, center_y


def visualize_bbox_on_screenshot(screenshot_path, bbox, output_path, label="Target"):
    """Draw bounding box and center point on screenshot."""
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img)
    
    # Parse bbox
    if isinstance(bbox[0], (list, tuple)):
        x1, y1 = bbox[0]
        x2, y2 = bbox[1]
    else:
        x1, y1, x2, y2 = bbox
    
    # Draw bounding box (green)
    draw.rectangle([x1, y1, x2, y2], outline="green", width=4)
    
    # Draw center point (red cross)
    center_x, center_y = get_bbox_center(bbox)
    size = 20
    draw.line([(center_x - size, center_y), (center_x + size, center_y)], fill="red", width=4)
    draw.line([(center_x, center_y - size), (center_x, center_y + size)], fill="red", width=4)
    
    # Draw circle around center
    draw.ellipse([center_x - 30, center_y - 30, center_x + 30, center_y + 30], outline="red", width=3)
    
    # Add label
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((x1, y1 - 25), label, fill="green", font=font)
    draw.text((center_x + 35, center_y - 10), f"({center_x}, {center_y})", fill="red", font=font)
    
    img.save(output_path)
    print(f"✓ Visualization saved: {output_path}")


def test_omniparser_chrome_detection():
    """Main test: Find and click Chrome icon using OmniParser."""
    
    print("="*70)
    print("OMNIPARSER TEST - CHROME ICON DETECTION")
    print("="*70)
    
    # Create output directory
    output_dir = Path("tests/mouse_dpi_debug/omniparser_output")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Step 1: Capture screenshot
    screenshot_path = output_dir / "desktop_screenshot.png"
    screenshot = capture_screenshot(str(screenshot_path))
    
    # Step 2: Send to OmniParser
    try:
        labeled_url, parsed_content, label_coordinates = parse_screen_with_omniparser(
            str(screenshot_path)
        )
    except Exception as e:
        print(f"\n❌ OmniParser failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your REPLICATE_API_TOKEN in .env file")
        print("2. Ensure you have internet connection")
        print("3. Check Replicate API status")
        return
    
    # Step 3: Download labeled image
    if labeled_url:
        labeled_path = output_dir / "labeled_screenshot.png"
        download_labeled_image(labeled_url, str(labeled_path))
    
    # Step 4: Display parsed content
    print("\n📋 PARSED CONTENT:")
    print("-" * 70)
    if isinstance(parsed_content, str):
        lines = parsed_content.strip().split('\n')
        for i, line in enumerate(lines[:20], 1):  # Show first 20
            print(f"{i:2d}. {line}")
        if len(lines) > 20:
            print(f"    ... and {len(lines) - 20} more elements")
    else:
        print(parsed_content)
    
    # Step 5: Display coordinates structure
    print("\n📐 COORDINATE MAPPING:")
    print("-" * 70)
    if label_coordinates:
        print(f"Found {len(label_coordinates)} elements with coordinates")
        print("\nFirst 5 examples:")
        for i, (key, value) in enumerate(list(label_coordinates.items())[:5], 1):
            print(f"{i}. ID: {key} → BBox: {value}")
    else:
        print("❌ No coordinates returned!")
    
    # Step 6: Find Chrome icon
    print("\n🎯 SEARCHING FOR CHROME/BROWSER ICON:")
    print("-" * 70)
    
    search_terms = ["browser", "chrome", "web browser", "google chrome", "google"]
    matches = find_element_by_description(parsed_content, label_coordinates, search_terms)
    
    if not matches:
        print("\n⚠️  Chrome not found. Trying alternative searches...")
        # Show all available elements for manual inspection
        print("\nAll detected elements:")
        if isinstance(parsed_content, str):
            for line in parsed_content.strip().split('\n'):
                print(f"  - {line}")
        
        print("\n💡 Manual mode: You can specify an element ID to test")
        return
    
    # Step 7: Use first match
    target = matches[0]
    print(f"\n✓ Selected target: {target['description']}")
    print(f"  Element ID: {target['id']}")
    print(f"  Bounding Box (normalized): {target['bbox']}")
    
    # Get screen dimensions
    screen_width, screen_height = screenshot.size
    print(f"  Screen dimensions: {screen_width} x {screen_height}")
    
    # Calculate center in pixel coordinates
    center_x, center_y = get_bbox_center(target['bbox'], screen_width, screen_height)
    print(f"  Center Point (pixels): ({center_x}, {center_y})")
    
    # Convert bbox to pixels for visualization
    bbox = target['bbox']
    if isinstance(bbox[0], (list, tuple)):
        x1, y1 = bbox[0]
        x2, y2 = bbox[1]
    else:
        x1, y1, x2, y2 = bbox
    
    # Convert to pixels if normalized
    if x1 <= 1 and y1 <= 1:
        x1, y1, x2, y2 = int(x1 * screen_width), int(y1 * screen_height), int(x2 * screen_width), int(y2 * screen_height)
    pixel_bbox = [x1, y1, x2, y2]
    
    # Step 8: Visualize
    vis_path = output_dir / "chrome_target_visualization.png"
    visualize_bbox_on_screenshot(
        str(screenshot_path),
        pixel_bbox,
        str(vis_path),
        label=f"Browser Icon (ID: {target['id']})"
    )
    
    print(f"\n📊 Visualization saved!")
    print(f"  Open: {vis_path.absolute()}")
    print(f"  Green box should be around Chrome icon")
    print(f"  Red crosshair shows click point: ({center_x}, {center_y})")
    
    # Step 9: Auto-click the browser icon
    print("\n⚡ CLICK TEST:")
    print("-" * 70)
    print(f"\nAuto-clicking Chrome icon at ({center_x}, {center_y}) in 3 seconds...")
    print("Watch your taskbar!")
    time.sleep(3)
    
    try:
        pyautogui.click(center_x, center_y)
        print("✓ Click executed!")
        
        time.sleep(1)
        print("\n✓ Click completed! Did Chrome open/focus?")
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\n✓ Screenshot captured: {screenshot_path.absolute()}")
    if labeled_url:
        print(f"✓ Labeled image: {labeled_path.absolute()}")
    print(f"✓ Visualization: {vis_path.absolute()}")
    print(f"✓ Found {len(matches)} browser icon(s)")
    if matches:
        print(f"✓ Clicked at coordinates: ({center_x}, {center_y})")
        print("\nVerification:")
        print("1. Check visualization - is green box around Chrome icon?")
        print("2. Did Chrome open/focus after the click?")
        print("3. If YES → OmniParser + DPI fix is working perfectly!")
        print("4. If NO → Check coordinate conversion or search terms")
        print("\nNext steps:")
        print("→ If successful, integrate OmniParser into agent's autonomous mode")
        print("→ Replace generic vision model with OmniParser for UI detection")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        test_omniparser_chrome_detection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

