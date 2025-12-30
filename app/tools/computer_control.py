"""
Computer control tools for autonomous GUI interaction.

Uses vision-guided control:
- Gemini 2.0 for screen understanding and coordinate detection
- PyAutoGUI for mouse/keyboard control
- Vision feedback loop for verification
"""

import os
import json
import time
import ctypes
import pyautogui
from typing import Optional, Dict, Any, Tuple
from .vision_tools import capture_screenshot, analyze_image
from app.core.logging_utils import get_logger

# ============================================================================
# DPI AWARENESS FIX - Prevents coordinate mismatches on high DPI screens
# ============================================================================
try:
    # This tells Windows: "I know how to handle high DPI, don't lie to me about coordinates"
    # 1 = Process_System_DPI_Aware
    # 2 = Process_Per_Monitor_DPI_Aware (Better for multi-monitor)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    # Fallback for older Windows versions (Windows 7/8)
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass  # If both fail, just continue without DPI awareness

# Configure PyAutoGUI safety features
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.5  # Default pause between actions

logger = get_logger("computer_control", "tools.log")


# Safety configuration
RESTRICTED_APPS = ["cmd.exe", "powershell.exe", "regedit.exe", "taskmgr.exe"]
MAX_ACTIONS_PER_MINUTE = 30  # Rate limiting
_action_timestamps = []


def _is_safe_action() -> bool:
    """Rate limiting: ensure we don't spam actions too quickly."""
    global _action_timestamps
    current_time = time.time()
    
    # Remove timestamps older than 1 minute
    _action_timestamps = [t for t in _action_timestamps if current_time - t < 60]
    
    if len(_action_timestamps) >= MAX_ACTIONS_PER_MINUTE:
        logger.warning("Rate limit exceeded: %d actions in the last minute", len(_action_timestamps))
        return False
    
    _action_timestamps.append(current_time)
    return True


def _parse_coordinates(vision_response: str) -> Optional[Tuple[int, int]]:
    """
    Parse coordinates from Gemini's vision response.
    Expects JSON like: {"x": 100, "y": 200, "confidence": 85}
    """
    try:
        # Try to extract JSON from response
        # Handle cases where model wraps JSON in markdown
        response = vision_response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response = "\n".join(lines)
        
        # Remove "json" tag if present
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        
        if "error" in data:
            logger.warning("Vision model returned error: %s", data["error"])
            return None
        
        x = data.get("x")
        y = data.get("y")
        confidence = data.get("confidence", 0)
        
        if x is None or y is None:
            logger.warning("Missing x or y coordinates in response")
            return None
        
        # Validate coordinates are within screen bounds
        screen_width, screen_height = pyautogui.size()
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            logger.warning(
                "Coordinates (%d, %d) out of screen bounds (%d x %d)",
                x, y, screen_width, screen_height
            )
            return None
        
        if confidence < 50:
            logger.warning("Low confidence (%d%%) for coordinates", confidence)
        
        logger.info("Parsed coordinates: (%d, %d) with %d%% confidence", x, y, confidence)
        return (int(x), int(y))
    
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from vision response: %s", e)
        logger.debug("Vision response was: %s", vision_response)
        return None
    except Exception as e:
        logger.error("Error parsing coordinates: %s", e)
        return None


def click_at_coordinates(x: int, y: int, clicks: int = 1, button: str = "left") -> str:
    """
    Click at specific screen coordinates.
    
    Args:
        x: X coordinate (pixels from left)
        y: Y coordinate (pixels from top)
        clicks: Number of clicks (1 for single, 2 for double)
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Confirmation message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        screen_width, screen_height = pyautogui.size()
        
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            return f"❌ Coordinates ({x}, {y}) out of screen bounds ({screen_width} x {screen_height})"
        
        logger.info("Clicking at (%d, %d) with %s button, %d times", x, y, button, clicks)
        
        # Move to position with smooth motion
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.1)
        
        # Click
        pyautogui.click(x, y, clicks=clicks, button=button)
        
        return f"✓ Clicked at ({x}, {y})"
    
    except Exception as e:
        logger.error("Error clicking at coordinates: %s", e)
        return f"❌ Error clicking: {str(e)}"


def click_element(element_description: str, clicks: int = 1, button: str = "left") -> str:
    """
    Vision-guided clicking: Find an element on screen and click it.
    
    Args:
        element_description: Natural language description of what to click
                           (e.g., "Save button", "Chrome icon", "Search box")
        clicks: Number of clicks (1 for single, 2 for double)
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Result message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        logger.info("Vision-guided click requested for: %s", element_description)
        
        # Step 1: Capture current screen
        capture_result = capture_screenshot()
        if not capture_result.startswith("Screenshot saved to:"):
            return f"❌ Failed to capture screen: {capture_result}"
        
        screenshot_path = capture_result.replace("Screenshot saved to:", "").strip()
        
        # Step 2: Ask Gemini to find the element and return coordinates
        prompt = f"""Find the {element_description} on this screen.

Analyze the screen carefully and locate the element. Return ONLY a JSON object (no extra text) with:
{{
  "x": <pixel_x_coordinate>,
  "y": <pixel_y_coordinate>,
  "confidence": <0-100>,
  "description": "<brief description of what you found>"
}}

If you cannot find it clearly, return:
{{
  "error": "not found",
  "reason": "<why it couldn't be found>"
}}

Rules:
- Coordinates must be the CENTER of the element
- x is pixels from the LEFT edge of screen
- y is pixels from the TOP edge of screen
- confidence should reflect how certain you are
- Return ONLY the JSON, no markdown, no extra text"""
        
        vision_response = analyze_image(screenshot_path, prompt)
        
        # Check for vision API errors
        if "❌" in vision_response or "FAILED" in vision_response:
            return f"❌ Vision analysis failed: {vision_response}"
        
        logger.debug("Vision response: %s", vision_response)
        
        # Step 3: Parse coordinates
        coords = _parse_coordinates(vision_response)
        
        if coords is None:
            return f"❌ Could not find '{element_description}' on screen.\n\nVision response: {vision_response[:200]}"
        
        x, y = coords
        
        # Step 4: Move and click
        logger.info("Moving to (%d, %d) and clicking", x, y)
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.2)
        pyautogui.click(x, y, clicks=clicks, button=button)
        
        return f"✓ Found and clicked '{element_description}' at ({x}, {y})"
    
    except Exception as e:
        logger.error("Error in click_element: %s", e)
        return f"❌ Error: {str(e)}"


def type_text(text: str, interval: float = 0.05, press_enter: bool = False) -> str:
    """
    Type text using keyboard simulation.
    
    Args:
        text: Text to type
        interval: Delay between keystrokes (seconds)
        press_enter: Whether to press Enter after typing
    
    Returns:
        Confirmation message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        logger.info("Typing text (length: %d chars)", len(text))
        
        pyautogui.write(text, interval=interval)
        
        if press_enter:
            time.sleep(0.2)
            pyautogui.press('enter')
            logger.info("Pressed Enter after typing")
        
        return f"✓ Typed {len(text)} characters" + (" and pressed Enter" if press_enter else "")
    
    except Exception as e:
        logger.error("Error typing text: %s", e)
        return f"❌ Error typing: {str(e)}"


def press_key(key: str, presses: int = 1, interval: float = 0.1) -> str:
    """
    Press a keyboard key.
    
    Args:
        key: Key name (e.g., "enter", "tab", "esc", "backspace", "delete", "space")
             Also supports: "up", "down", "left", "right", "f1"-"f12", etc.
        presses: Number of times to press the key
        interval: Delay between presses (seconds)
    
    Returns:
        Confirmation message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        logger.info("Pressing key '%s' %d times", key, presses)
        
        pyautogui.press(key, presses=presses, interval=interval)
        
        return f"✓ Pressed '{key}' key {presses} time(s)"
    
    except Exception as e:
        logger.error("Error pressing key: %s", e)
        return f"❌ Error pressing key: {str(e)}"


def hotkey(*keys: str) -> str:
    """
    Press a keyboard shortcut (multiple keys simultaneously).
    
    Args:
        *keys: Keys to press together (e.g., "ctrl", "c" for Ctrl+C)
    
    Returns:
        Confirmation message
    
    Examples:
        hotkey("ctrl", "c")  # Copy
        hotkey("ctrl", "v")  # Paste
        hotkey("alt", "tab") # Switch windows
        hotkey("win", "d")   # Show desktop
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        logger.info("Pressing hotkey: %s", " + ".join(keys))
        
        pyautogui.hotkey(*keys)
        
        return f"✓ Pressed hotkey: {' + '.join(keys)}"
    
    except Exception as e:
        logger.error("Error pressing hotkey: %s", e)
        return f"❌ Error pressing hotkey: {str(e)}"


def scroll(clicks: int, direction: str = "down") -> str:
    """
    Scroll the mouse wheel.
    
    Args:
        clicks: Number of scroll clicks (positive values scroll in direction)
        direction: "up" or "down"
    
    Returns:
        Confirmation message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        logger.info("Scrolling %s by %d clicks", direction, clicks)
        
        # PyAutoGUI: positive = scroll down, negative = scroll up
        scroll_amount = -clicks if direction == "up" else clicks
        pyautogui.scroll(scroll_amount)
        
        return f"✓ Scrolled {direction} by {clicks} clicks"
    
    except Exception as e:
        logger.error("Error scrolling: %s", e)
        return f"❌ Error scrolling: {str(e)}"


def move_mouse(x: int, y: int, duration: float = 0.3) -> str:
    """
    Move the mouse cursor to a position without clicking.
    
    Args:
        x: X coordinate (pixels from left)
        y: Y coordinate (pixels from top)
        duration: Time to take for the movement (seconds)
    
    Returns:
        Confirmation message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        screen_width, screen_height = pyautogui.size()
        
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            return f"❌ Coordinates ({x}, {y}) out of screen bounds ({screen_width} x {screen_height})"
        
        logger.info("Moving mouse to (%d, %d)", x, y)
        
        pyautogui.moveTo(x, y, duration=duration)
        
        return f"✓ Moved mouse to ({x}, {y})"
    
    except Exception as e:
        logger.error("Error moving mouse: %s", e)
        return f"❌ Error moving mouse: {str(e)}"


def get_mouse_position() -> str:
    """
    Get the current mouse cursor position.
    
    Returns:
        Current (x, y) coordinates
    """
    try:
        x, y = pyautogui.position()
        return f"Mouse position: ({x}, {y})"
    
    except Exception as e:
        return f"❌ Error getting mouse position: {str(e)}"


def drag_to(x: int, y: int, duration: float = 0.5, button: str = "left") -> str:
    """
    Drag from current mouse position to target coordinates.
    
    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Time to take for the drag (seconds)
        button: Mouse button to hold ("left", "right", "middle")
    
    Returns:
        Confirmation message
    """
    if not _is_safe_action():
        return "❌ Rate limit exceeded. Wait before performing more actions."
    
    try:
        screen_width, screen_height = pyautogui.size()
        
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            return f"❌ Coordinates ({x}, {y}) out of screen bounds ({screen_width} x {screen_height})"
        
        start_x, start_y = pyautogui.position()
        logger.info("Dragging from (%d, %d) to (%d, %d)", start_x, start_y, x, y)
        
        pyautogui.dragTo(x, y, duration=duration, button=button)
        
        return f"✓ Dragged from ({start_x}, {start_y}) to ({x}, {y})"
    
    except Exception as e:
        logger.error("Error dragging: %s", e)
        return f"❌ Error dragging: {str(e)}"

