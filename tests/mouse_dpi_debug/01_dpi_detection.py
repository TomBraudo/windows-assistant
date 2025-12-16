"""
DPI Detection Test - Check if DPI awareness is working correctly.

This script checks:
1. Current DPI scaling settings
2. Whether process is DPI aware
3. Screen resolution (logical vs physical)
4. Scaling factor
"""

import ctypes
import sys

print("="*70)
print("DPI DETECTION TEST")
print("="*70)

# Test 1: Check DPI awareness status
print("\n1. DPI AWARENESS STATUS:")
print("-" * 70)

try:
    awareness = ctypes.c_int()
    ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
    
    awareness_levels = {
        0: "UNAWARE - Will see scaled coordinates (BAD)",
        1: "SYSTEM_AWARE - Aware of system DPI (GOOD)",
        2: "PER_MONITOR_AWARE - Aware of per-monitor DPI (BEST)"
    }
    
    print(f"Current Process DPI Awareness: {awareness_levels.get(awareness.value, 'UNKNOWN')}")
    
    if awareness.value == 0:
        print("❌ PROBLEM: Process is NOT DPI aware!")
        print("   Coordinates will be WRONG on high-DPI displays.")
    else:
        print("✓ GOOD: Process is DPI aware.")
        
except Exception as e:
    print(f"❌ Could not check DPI awareness: {e}")
    print("   This might be Windows 7 (use older API)")


# Test 2: Set DPI awareness and verify
print("\n2. SETTING DPI AWARENESS:")
print("-" * 70)

try:
    # Try to set DPI awareness
    result = ctypes.windll.shcore.SetProcessDpiAwareness(1)
    print(f"SetProcessDpiAwareness(1) returned: {result}")
    
    if result == 0:
        print("✓ Successfully set DPI awareness!")
    else:
        print(f"⚠️  Return code {result} - might already be set or error")
        
except Exception as e:
    print(f"SetProcessDpiAwareness failed: {e}")
    print("Trying fallback method (Windows 7/8)...")
    
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        print("✓ Fallback SetProcessDPIAware() succeeded")
    except Exception as e2:
        print(f"❌ Fallback also failed: {e2}")


# Test 3: Check screen resolution and DPI
print("\n3. SCREEN RESOLUTION & DPI:")
print("-" * 70)

try:
    user32 = ctypes.windll.user32
    
    # Get screen dimensions (DPI-aware if awareness is set)
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    print(f"Screen Resolution: {screen_width} x {screen_height}")
    
    # Get DPI settings
    hdc = user32.GetDC(0)
    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
    dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
    user32.ReleaseDC(0, hdc)
    
    print(f"DPI: {dpi_x} x {dpi_y}")
    
    # Calculate scaling
    scaling_x = dpi_x / 96.0  # 96 is default DPI
    scaling_y = dpi_y / 96.0
    
    print(f"Scaling Factor: {scaling_x:.2f}x (X), {scaling_y:.2f}x (Y)")
    
    if scaling_x > 1.0:
        print(f"✓ High DPI detected ({scaling_x:.0f}x scaling)")
        print(f"  Physical screen: {int(screen_width * scaling_x)} x {int(screen_height * scaling_y)}")
    else:
        print("✓ Standard DPI (no scaling)")
        
except Exception as e:
    print(f"❌ Error checking screen info: {e}")


# Test 4: PyAutoGUI compatibility check
print("\n4. PYAUTOGUI COMPATIBILITY:")
print("-" * 70)

try:
    import pyautogui
    
    pag_size = pyautogui.size()
    print(f"PyAutoGUI sees screen as: {pag_size.width} x {pag_size.height}")
    
    if pag_size.width == screen_width and pag_size.height == screen_height:
        print("✓ PyAutoGUI matches system metrics (GOOD)")
    else:
        print("❌ MISMATCH between PyAutoGUI and system!")
        print(f"   System: {screen_width} x {screen_height}")
        print(f"   PyAutoGUI: {pag_size.width} x {pag_size.height}")
        print("   This will cause coordinate errors!")
        
except ImportError:
    print("⚠️  PyAutoGUI not installed (run: pip install pyautogui)")
except Exception as e:
    print(f"❌ PyAutoGUI error: {e}")


# Test 5: Recommendations
print("\n5. RECOMMENDATIONS:")
print("-" * 70)

print("""
For accurate clicking, you need:
1. ✓ DPI awareness set BEFORE importing pyautogui
2. ✓ Coordinates from vision should match physical screen
3. ✓ Test with visual feedback to confirm accuracy

Next steps:
1. Run 02_visual_click_test.py to see where clicks land
2. Run 03_screenshot_coordinate_test.py to test vision coordinates
""")

print("="*70)
print("TEST COMPLETE")
print("="*70)

