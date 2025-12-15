"""
Vision tools for Windows Agent using Google Gemini Vision models.

Provides:
- Screenshot capture
- Image analysis using Gemini vision
- UI element detection
"""

import os
from typing import Optional, Dict, Any
from PIL import ImageGrab, Image
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def capture_screenshot(save_path: Optional[str] = None) -> str:
    """
    Capture a screenshot of the entire screen.
    
    Args:
        save_path: Optional path to save the screenshot. If not provided,
                   saves to a temporary location in Desktop/screenshots.
    
    Returns:
        Path to the saved screenshot file.
    """
    try:
        # Capture screenshot
        screenshot = ImageGrab.grab()
        
        # Determine save location
        if save_path is None:
            # Default to Desktop/screenshots folder
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            screenshots_dir = os.path.join(desktop, "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
        else:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        
        # Save screenshot
        screenshot.save(save_path)
        
        return f"Screenshot saved to: {save_path}"
    
    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"


def analyze_image(image_path: str, question: str = "What do you see in this image?") -> str:
    """
    Analyze an image using Google Gemini Vision models.
    
    Args:
        image_path: Path to the image file to analyze
        question: Question to ask about the image
    
    Returns:
        AI's analysis of the image
    """
    try:
        # Verify image exists
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}"
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return (
                "❌ GEMINI_API_KEY not configured\n\n"
                "To fix:\n"
                "1. Go to Settings tab\n"
                "2. Add your GEMINI_API_KEY\n"
                "3. Or add to .env file: GEMINI_API_KEY=your_key_here"
            )
        
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Load image using PIL
        image = Image.open(image_path)
        
        # Use Gemini 2.0 Flash (supports vision)
        # Try multiple models in case one fails
        vision_models = [
            "gemini-2.0-flash-exp",  # Experimental, latest
            "gemini-2.0-flash",      # Stable
            "gemini-1.5-flash",      # Fallback
        ]
        
        last_error = None
        for model_name in vision_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[question, image],
                )
                
                # Extract text from response
                result_text = ""
                for part in response.parts:
                    if part.text is not None:
                        result_text += part.text
                
                if result_text:
                    return result_text.strip()
                else:
                    return "No text response from vision model."
            
            except Exception as e:
                last_error = str(e)
                # Try next model
                continue
        
        # If all models failed
        return (
            f"❌ GEMINI VISION ANALYSIS FAILED\n\n"
            f"Tried models: {', '.join(vision_models)}\n"
            f"Last error: {last_error}\n\n"
            f"Check your GEMINI_API_KEY and quota at:\n"
            f"https://aistudio.google.com/app/apikey"
        )
    
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def analyze_screenshot(question: str = "What do you see on the screen?") -> str:
    """
    Convenience function: Capture a screenshot and analyze it in one step.
    
    Args:
        question: Question to ask about the screenshot
    
    Returns:
        AI's analysis of the screenshot
    """
    # Capture screenshot
    capture_result = capture_screenshot()
    
    # Extract path from result
    if "Screenshot saved to:" in capture_result:
        screenshot_path = capture_result.replace("Screenshot saved to:", "").strip()
    else:
        return capture_result  # Return error if capture failed
    
    # Analyze the screenshot
    analysis = analyze_image(screenshot_path, question)
    
    return f"{capture_result}\n\nAnalysis:\n{analysis}"


def find_ui_element(element_description: str) -> str:
    """
    Find a UI element on the screen by description.
    
    Args:
        element_description: Description of the UI element (e.g., "Save button", "Search box")
    
    Returns:
        Information about the element's location
    """
    question = f"Where is the {element_description}? Describe its location on the screen (e.g., top-left, center, bottom-right) and what it looks like."
    return analyze_screenshot(question)


def describe_screen() -> str:
    """
    Get a general description of what's currently on screen.
    
    Returns:
        Description of the current screen contents
    """
    return analyze_screenshot(
        "Describe what's currently displayed on the screen. "
        "Include any applications, windows, text, or notable UI elements you can see."
    )

