"""
Screenshot + Coordinate Test - Test vision-to-click pipeline.

This mimics what the agent does:
1. Capture screenshot
2. Ask for coordinates of an element (manually input for testing)
3. Click at those coordinates
4. Verify if click landed correctly

This tests the full pipeline: screenshot → coordinates → click
"""

import ctypes
import time
import os
from pathlib import Path

# ============================================================================
# DPI FIX - MUST BE FIRST
# ============================================================================
print("Setting DPI awareness...")
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    print("✓ SetProcessDpiAwareness(1) - System DPI Aware")
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        print("✓ SetProcessDPIAware() - Fallback method")
    except:
        print("❌ Could not set DPI awareness")

# Now import after DPI is set
from PIL import ImageGrab, ImageDraw, ImageFont
import pyautogui


def capture_screenshot_with_overlay(save_path):
    """Capture screenshot and add coordinate grid overlay."""
    print("\nCapturing screenshot...")
    screenshot = ImageGrab.grab()
    
    # Create a copy for overlay
    overlay = screenshot.copy()
    draw = ImageDraw.Draw(overlay)
    
    # Add grid lines every 100 pixels
    width, height = screenshot.size
    
    # Vertical lines
    for x in range(0, width, 100):
        draw.line([(x, 0), (x, height)], fill="red", width=1)
        draw.text((x + 5, 5), str(x), fill="red")
    
    # Horizontal lines
    for y in range(0, height, 100):
        draw.line([(0, y), (width, y)], fill="red", width=1)
        draw.text((5, y + 5), str(y), fill="red")
    
    # Save both versions
    screenshot.save(save_path)
    overlay_path = save_path.replace(".png", "_grid.png")
    overlay.save(overlay_path)
    
    print(f"✓ Screenshot saved: {save_path}")
    print(f"✓ Grid overlay saved: {overlay_path}")
    print(f"   Resolution: {width} x {height}")
    
    return screenshot, width, height


def mark_click_on_screenshot(screenshot_path, x, y, output_path):
    """Mark where a click happened on the screenshot."""
    from PIL import Image
    
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img)
    
    # Draw red X
    size = 20
    draw.line([(x-size, y-size), (x+size, y+size)], fill="red", width=4)
    draw.line([(x-size, y+size), (x+size, y-size)], fill="red", width=4)
    
    # Draw circle around it
    draw.ellipse([x-30, y-30, x+30, y+30], outline="red", width=3)
    
    # Add label
    draw.text((x+35, y-10), f"Click at ({x}, {y})", fill="red")
    
    img.save(output_path)
    print(f"✓ Marked click on: {output_path}")


def test_coordinate_clicking():
    """Interactive test for clicking at specific coordinates."""
    
    print("\n" + "="*70)
    print("SCREENSHOT + COORDINATE TEST")
    print("="*70)
    
    # Create output directory
    output_dir = Path("tests/mouse_dpi_debug/test_output")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print("\nThis test simulates the vision-guided clicking process:")
    print("1. Captures your screen")
    print("2. You provide coordinates to click")
    print("3. Clicks at those coordinates")
    print("4. Marks the result on the screenshot")
    print("\nThis verifies the full DPI-aware pipeline!")
    
    input("\nPress Enter to capture screenshot...")
    
    # Capture screenshot
    screenshot_path = output_dir / "test_screenshot.png"
    screenshot, width, height = capture_screenshot_with_overlay(str(screenshot_path))
    
    print(f"\n✓ Screenshot captured")
    print(f"  Open: {screenshot_path.absolute()}")
    print(f"  Open: {str(screenshot_path).replace('.png', '_grid.png')} (with grid)")
    
    # Get PyAutoGUI's view of screen
    pag_size = pyautogui.size()
    print(f"\nScreen info:")
    print(f"  PIL sees: {width} x {height}")
    print(f"  PyAutoGUI sees: {pag_size.width} x {pag_size.height}")
    
    if width == pag_size.width and height == pag_size.height:
        print("  ✓ MATCH - Good sign for DPI awareness!")
    else:
        print("  ❌ MISMATCH - DPI issue detected!")
        print("     This will cause coordinate errors.")
    
    # Interactive clicking test
    while True:
        print("\n" + "-"*70)
        choice = input("\nOptions:\n"
                      "1. Click at specific coordinates\n"
                      "2. Test center click\n"
                      "3. Test corner clicks\n"
                      "4. Exit\n"
                      "Choice: ").strip()
        
        if choice == "1":
            try:
                x = int(input("Enter X coordinate: "))
                y = int(input("Enter Y coordinate: "))
                
                print(f"\nClicking at ({x}, {y}) in 3 seconds...")
                print("Watch your screen!")
                time.sleep(3)
                
                # Click
                pyautogui.click(x, y)
                print(f"✓ Clicked at ({x}, {y})")
                
                # Mark on screenshot
                marked_path = output_dir / f"test_click_{x}_{y}.png"
                mark_click_on_screenshot(str(screenshot_path), x, y, str(marked_path))
                
                print(f"\nCheck the result:")
                print(f"  1. Did click land where intended?")
                print(f"  2. See marked screenshot: {marked_path.absolute()}")
                
            except ValueError:
                print("❌ Invalid coordinates")
        
        elif choice == "2":
            # Test center
            x, y = width // 2, height // 2
            print(f"\nClicking center ({x}, {y}) in 3 seconds...")
            time.sleep(3)
            
            pyautogui.click(x, y)
            print(f"✓ Clicked center")
            
            marked_path = output_dir / f"test_click_center.png"
            mark_click_on_screenshot(str(screenshot_path), x, y, str(marked_path))
        
        elif choice == "3":
            # Test corners
            corners = [
                (100, 100, "top-left"),
                (width - 100, 100, "top-right"),
                (100, height - 100, "bottom-left"),
                (width - 100, height - 100, "bottom-right")
            ]
            
            for x, y, name in corners:
                print(f"\nClicking {name} ({x}, {y}) in 2 seconds...")
                time.sleep(2)
                pyautogui.click(x, y)
                
                marked_path = output_dir / f"test_click_{name}.png"
                mark_click_on_screenshot(str(screenshot_path), x, y, str(marked_path))
            
            print("\n✓ All corners clicked")
        
        elif choice == "4":
            break
        
        else:
            print("Invalid choice")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print(f"\nAll test images saved to: {output_dir.absolute()}")
    print("\nAnalysis:")
    print("- If clicks landed where intended → DPI fix works!")
    print("- If clicks are offset → DPI problem still exists")
    print("- Check marked screenshots to verify results")


if __name__ == "__main__":
    test_coordinate_clicking()

