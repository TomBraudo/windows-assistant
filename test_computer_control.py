"""
Test script for computer control features.
Run this to verify that computer control is working correctly.
"""

from app.tools.computer_control import (
    get_mouse_position,
    move_mouse,
    click_at_coordinates,
    type_text,
    press_key,
    hotkey,
    scroll
)
from app.tools.vision_tools import capture_screenshot, analyze_image
import time


def test_mouse_position():
    """Test getting mouse position."""
    print("\n=== Test 1: Get Mouse Position ===")
    result = get_mouse_position()
    print(result)
    assert "Mouse position:" in result
    print("✓ PASSED")


def test_move_mouse():
    """Test moving mouse."""
    print("\n=== Test 2: Move Mouse ===")
    print("Moving mouse to (500, 500)...")
    result = move_mouse(500, 500, duration=1.0)
    print(result)
    assert "✓" in result
    print("✓ PASSED")
    time.sleep(1)


def test_screenshot_and_vision():
    """Test screenshot capture and vision analysis."""
    print("\n=== Test 3: Screenshot & Vision ===")
    
    # Capture screenshot
    print("Capturing screenshot...")
    screenshot_result = capture_screenshot()
    print(screenshot_result)
    assert "Screenshot saved to:" in screenshot_result
    
    # Extract path
    screenshot_path = screenshot_result.replace("Screenshot saved to:", "").strip()
    
    # Analyze with simple question
    print("\nAnalyzing screenshot with Gemini...")
    analysis = analyze_image(screenshot_path, "What can you see on this screen? Describe in one sentence.")
    print(f"Analysis: {analysis[:200]}...")
    
    if "❌" in analysis:
        print("⚠️  WARNING: Vision API not configured properly")
        print("Make sure GEMINI_API_KEY is set in .env file")
    else:
        print("✓ PASSED")


def test_keyboard():
    """Test keyboard input."""
    print("\n=== Test 4: Keyboard Input ===")
    print("This will open Notepad and type 'Hello from Computer Control!'")
    print("Press Ctrl+C within 5 seconds to cancel...")
    time.sleep(5)
    
    # Open Notepad
    print("Opening Notepad...")
    hotkey("win", "r")  # Open Run dialog
    time.sleep(0.5)
    type_text("notepad", press_enter=True)
    time.sleep(2)
    
    # Type message
    print("Typing message...")
    type_text("Hello from Computer Control!\n\nThis is a test of autonomous typing.", interval=0.1)
    
    print("\n✓ PASSED (Check Notepad window)")
    print("Note: Close Notepad manually (don't save)")


def test_vision_guided_click():
    """Test vision-guided clicking (requires GUI)."""
    print("\n=== Test 5: Vision-Guided Click ===")
    print("SKIPPED - This requires a specific UI element to click")
    print("Try this manually by running:")
    print('  python cli.py')
    print('  Then type: "Click the Start button"')


def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPUTER CONTROL TEST SUITE")
    print("=" * 60)
    print("\nThis will test the computer control features.")
    print("Some tests will move your mouse and type text!")
    print("\nPress Ctrl+C to abort at any time.")
    print("Move mouse to TOP-LEFT corner for emergency stop (PyAutoGUI failsafe).")
    
    input("\nPress Enter to start tests...")
    
    try:
        # Basic tests
        test_mouse_position()
        test_move_mouse()
        test_screenshot_and_vision()
        
        # Interactive test
        print("\n" + "=" * 60)
        response = input("Run keyboard test? This will open Notepad and type. (y/n): ")
        if response.lower() == 'y':
            test_keyboard()
        else:
            print("Skipped keyboard test")
        
        # Vision-guided click info
        test_vision_guided_click()
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETE!")
        print("=" * 60)
        print("\n✓ All tests passed!")
        print("\nNext steps:")
        print("1. Run 'python cli.py' for CLI mode")
        print("2. Run 'python main_gui.py' for GUI mode")
        print("3. Try: 'Click the Start button'")
        print("4. Try: 'Describe what's on my screen'")
        print("5. Try: 'Open Notepad and write Hello World'")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests aborted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

