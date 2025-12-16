"""
Comprehensive DPI Fix Test - All fixes in one place.

This script tries ALL known DPI awareness methods and tests them.
Use this to find which method works best for your system.
"""

import ctypes
import sys
import time

print("="*70)
print("COMPREHENSIVE DPI FIX TEST")
print("="*70)

# Store original state
original_state = {}


def method_1_shcore():
    """Method 1: Windows 8.1+ shcore.dll (Recommended)"""
    print("\n1. Testing: SetProcessDpiAwareness(1) - SYSTEM_AWARE")
    print("-" * 70)
    
    try:
        result = ctypes.windll.shcore.SetProcessDpiAwareness(1)
        print(f"   Return code: {result}")
        
        if result == 0:
            print("   ✓ SUCCESS")
            return True
        elif result == -2147024891:  # E_ACCESSDENIED
            print("   ⚠️  Already set (this is OK)")
            return True
        else:
            print(f"   ❌ FAILED with code {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return False


def method_2_shcore_per_monitor():
    """Method 2: Windows 8.1+ per-monitor awareness (Best for multi-monitor)"""
    print("\n2. Testing: SetProcessDpiAwareness(2) - PER_MONITOR_AWARE")
    print("-" * 70)
    
    try:
        result = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        print(f"   Return code: {result}")
        
        if result == 0:
            print("   ✓ SUCCESS (Best for multi-monitor setups)")
            return True
        elif result == -2147024891:
            print("   ⚠️  Already set")
            return True
        else:
            print(f"   ❌ FAILED with code {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return False


def method_3_user32():
    """Method 3: Windows Vista/7/8 fallback"""
    print("\n3. Testing: SetProcessDPIAware() - Legacy method")
    print("-" * 70)
    
    try:
        result = ctypes.windll.user32.SetProcessDPIAware()
        print(f"   Return code: {result}")
        
        if result:
            print("   ✓ SUCCESS (Legacy method)")
            return True
        else:
            print("   ❌ FAILED")
            return False
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return False


def check_current_awareness():
    """Check current DPI awareness status"""
    print("\nCURRENT DPI AWARENESS STATUS:")
    print("-" * 70)
    
    try:
        awareness = ctypes.c_int()
        ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        
        levels = {
            0: "UNAWARE (coordinates will be wrong!)",
            1: "SYSTEM_AWARE (good)",
            2: "PER_MONITOR_AWARE (best)"
        }
        
        print(f"   Current level: {awareness.value} - {levels.get(awareness.value, 'Unknown')}")
        return awareness.value
        
    except Exception as e:
        print(f"   Could not check: {e}")
        return -1


def test_screen_info():
    """Test screen resolution detection"""
    print("\nSCREEN RESOLUTION TEST:")
    print("-" * 70)
    
    try:
        user32 = ctypes.windll.user32
        
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        
        print(f"   System metrics: {width} x {height}")
        
        # Get DPI
        hdc = user32.GetDC(0)
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)
        user32.ReleaseDC(0, hdc)
        
        scaling = dpi_x / 96.0
        print(f"   DPI: {dpi_x} x {dpi_y}")
        print(f"   Scaling: {scaling:.2f}x")
        
        if scaling > 1.0:
            physical_width = int(width * scaling)
            physical_height = int(height * scaling)
            print(f"   Physical resolution: {physical_width} x {physical_height}")
        
        return width, height, scaling
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, None, None


def test_pyautogui_compat(system_width, system_height):
    """Test PyAutoGUI compatibility"""
    print("\nPYAUTOGUI COMPATIBILITY TEST:")
    print("-" * 70)
    
    try:
        import pyautogui
        
        pag_width, pag_height = pyautogui.size()
        print(f"   PyAutoGUI sees: {pag_width} x {pag_height}")
        print(f"   System sees: {system_width} x {system_height}")
        
        if pag_width == system_width and pag_height == system_height:
            print("   ✓ MATCH - Coordinates will be accurate!")
            return True
        else:
            diff_x = abs(pag_width - system_width)
            diff_y = abs(pag_height - system_height)
            print(f"   ❌ MISMATCH - Off by {diff_x}x{diff_y} pixels")
            print("      Clicks will be INACCURATE!")
            return False
            
    except ImportError:
        print("   ⚠️  PyAutoGUI not installed")
        return None


def run_all_tests():
    """Run all tests in sequence"""
    
    print("\n" + "="*70)
    print("RUNNING ALL TESTS")
    print("="*70)
    
    # Check initial state
    initial_awareness = check_current_awareness()
    
    # Try methods in order
    results = {}
    
    if initial_awareness == 0:
        # Not aware, try to set it
        print("\n⚠️  Process is NOT DPI aware. Trying fixes...")
        
        results["method_1"] = method_1_shcore()
        if not results["method_1"]:
            results["method_2"] = method_2_shcore_per_monitor()
        if not any(results.values()):
            results["method_3"] = method_3_user32()
    else:
        print("\n✓ Process is already DPI aware!")
    
    # Check final state
    final_awareness = check_current_awareness()
    
    # Test screen info
    width, height, scaling = test_screen_info()
    
    # Test PyAutoGUI
    if width and height:
        pyautogui_ok = test_pyautogui_compat(width, height)
    else:
        pyautogui_ok = None
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    print(f"\n1. DPI Awareness: ", end="")
    if final_awareness > 0:
        print("✓ WORKING")
    else:
        print("❌ NOT SET")
    
    print(f"2. Screen Detection: ", end="")
    if width and height:
        print(f"✓ WORKING ({width}x{height})")
    else:
        print("❌ FAILED")
    
    print(f"3. PyAutoGUI Compat: ", end="")
    if pyautogui_ok:
        print("✓ ACCURATE")
    elif pyautogui_ok is False:
        print("❌ MISMATCH (clicks will be wrong)")
    else:
        print("? UNKNOWN")
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    if final_awareness > 0 and pyautogui_ok:
        print("\n✓✓✓ ALL TESTS PASSED!")
        print("\nYour DPI fix is working correctly.")
        print("Coordinates should be accurate.")
        print("\nNext steps:")
        print("1. Run 02_visual_click_test.py to verify visually")
        print("2. Run 03_screenshot_coordinate_test.py to test full pipeline")
        
    elif final_awareness > 0 and not pyautogui_ok:
        print("\n⚠️  DPI awareness is set but PyAutoGUI sees wrong resolution!")
        print("\nPossible causes:")
        print("1. PyAutoGUI was imported BEFORE setting DPI awareness")
        print("2. Need to restart Python process")
        print("\nSolution:")
        print("Make sure DPI awareness is set BEFORE 'import pyautogui'")
        
    else:
        print("\n❌ DPI awareness could not be set!")
        print("\nPossible causes:")
        print("1. Windows version too old")
        print("2. Process already has DPI awareness set to different level")
        print("3. Permissions issue")
        print("\nTry:")
        print("1. Run as administrator")
        print("2. Restart Python and try again")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    run_all_tests()

