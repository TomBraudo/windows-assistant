"""
OmniParser Integration - Ready-to-use helper functions.

This module provides clean functions to integrate OmniParser
into your agent for accurate UI element detection.

Usage:
    from tests.mouse_dpi_debug.omniparser_integration import (
        detect_ui_elements,
        find_element_and_click
    )
    
    # Detect all elements
    elements = detect_ui_elements("screenshot.png")
    
    # Find and click specific element
    find_element_and_click("screenshot.png", "chrome icon")
"""

import os
import time
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import replicate

load_dotenv()


class OmniParserHelper:
    """Helper class for OmniParser integration."""
    
    def __init__(self):
        """Initialize OmniParser helper."""
        self.api_key = os.getenv("REPLICATE_API_TOKEN") or os.getenv("REPLICATE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "REPLICATE_API_TOKEN not found in environment!\n"
                "Add to .env file: REPLICATE_API_TOKEN=r8_your_token_here"
            )
        
        os.environ["REPLICATE_API_TOKEN"] = self.api_key
    
    def detect_elements(
        self,
        image_path: str,
        box_threshold: float = 0.05,
        iou_threshold: float = 0.1
    ) -> Dict:
        """
        Detect UI elements using OmniParser.
        
        Args:
            image_path: Path to screenshot
            box_threshold: Detection sensitivity (0.01-0.5, lower = more elements)
            iou_threshold: Overlap handling (0.1 = standard)
        
        Returns:
            Dict with:
                - labeled_image_url: URL to labeled image
                - elements: List of {id, description, bbox, center}
                - raw_content: Raw parsed content
                - raw_coordinates: Raw coordinate mapping
        """
        print(f"🔍 Analyzing screenshot with OmniParser...")
        
        output = replicate.run(
            "microsoft/omniparser-v2:49cf3d41b8d3aca1360514e83be4c97131ce8f0d99abfc365526d8384caa88df",
            input={
                "image": open(image_path, "rb"),
                "imgsz": 1920,
                "box_threshold": box_threshold,
                "iou_threshold": iou_threshold
            }
        )
        
        labeled_url = output.get("labeled_image")
        parsed_content = output.get("parsed_content", "")
        label_coordinates = output.get("label_coordinates", {})
        
        # Parse into clean structure
        elements = self._parse_elements(parsed_content, label_coordinates)
        
        print(f"✓ Found {len(elements)} UI elements")
        
        return {
            "labeled_image_url": labeled_url,
            "elements": elements,
            "raw_content": parsed_content,
            "raw_coordinates": label_coordinates
        }
    
    def _parse_elements(self, content: str, coordinates: Dict) -> List[Dict]:
        """Parse OmniParser output into clean element list."""
        elements = []
        
        if isinstance(content, str):
            lines = content.strip().split('\n')
        else:
            lines = [str(content)]
        
        for line in lines:
            # Extract ID and description
            if ':' in line:
                parts = line.split(':', 1)
                element_id = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else line
            else:
                element_id = line.strip()
                description = line
            
            # Get coordinates
            bbox = coordinates.get(element_id)
            
            if bbox:
                center = self._get_bbox_center(bbox)
                
                elements.append({
                    'id': element_id,
                    'description': description,
                    'bbox': bbox,
                    'center': center,
                    'raw_line': line
                })
        
        return elements
    
    def _get_bbox_center(self, bbox) -> Tuple[int, int]:
        """Calculate center of bounding box."""
        if isinstance(bbox[0], (list, tuple)):
            x1, y1 = bbox[0]
            x2, y2 = bbox[1]
        else:
            x1, y1, x2, y2 = bbox
        
        return int((x1 + x2) / 2), int((y1 + y2) / 2)
    
    def find_element(
        self,
        elements: List[Dict],
        search_terms: List[str],
        case_sensitive: bool = False
    ) -> Optional[Dict]:
        """
        Find element matching search terms.
        
        Args:
            elements: List of parsed elements
            search_terms: Keywords to search for
            case_sensitive: Whether to match case
        
        Returns:
            First matching element or None
        """
        for element in elements:
            description = element['description']
            
            if not case_sensitive:
                description = description.lower()
                search_terms = [term.lower() for term in search_terms]
            
            for term in search_terms:
                if term in description:
                    return element
        
        return None
    
    def get_all_elements_text(self, elements: List[Dict]) -> str:
        """Get formatted text of all elements for LLM context."""
        lines = []
        for elem in elements:
            lines.append(f"{elem['id']}: {elem['description']} at {elem['center']}")
        return "\n".join(lines)


# ============================================================================
# Easy-to-use functions
# ============================================================================

def detect_ui_elements(image_path: str) -> List[Dict]:
    """
    Detect all UI elements on screenshot.
    
    Args:
        image_path: Path to screenshot
    
    Returns:
        List of elements with id, description, bbox, center
    
    Example:
        elements = detect_ui_elements("screenshot.png")
        for elem in elements:
            print(f"{elem['id']}: {elem['description']} at {elem['center']}")
    """
    helper = OmniParserHelper()
    result = helper.detect_elements(image_path)
    return result['elements']


def find_element_by_name(image_path: str, search_terms: List[str]) -> Optional[Dict]:
    """
    Find specific element on screenshot.
    
    Args:
        image_path: Path to screenshot
        search_terms: List of keywords (e.g., ["chrome", "browser"])
    
    Returns:
        Element dict with id, description, bbox, center or None
    
    Example:
        element = find_element_by_name("screenshot.png", ["chrome", "google"])
        if element:
            print(f"Found at: {element['center']}")
    """
    helper = OmniParserHelper()
    result = helper.detect_elements(image_path)
    return helper.find_element(result['elements'], search_terms)


def get_element_coordinates_for_llm(image_path: str) -> str:
    """
    Get formatted text of all UI elements for LLM context.
    
    This provides the LLM with a list of clickable elements
    instead of asking it to guess coordinates.
    
    Args:
        image_path: Path to screenshot
    
    Returns:
        Formatted string: "ID: description at (x, y)"
    
    Example:
        context = get_element_coordinates_for_llm("screenshot.png")
        
        llm_prompt = f'''
        Here are the UI elements visible:
        {context}
        
        Which element should I click to open Chrome?
        Reply with just the element ID.
        '''
    """
    helper = OmniParserHelper()
    result = helper.detect_elements(image_path)
    return helper.get_all_elements_text(result['elements'])


def quick_test():
    """Quick test of OmniParser integration."""
    print("="*70)
    print("OMNIPARSER QUICK TEST")
    print("="*70)
    
    from PIL import ImageGrab
    
    # Capture screenshot
    print("\n1. Capturing screenshot...")
    screenshot = ImageGrab.grab()
    screenshot.save("temp_screenshot.png")
    print("✓ Screenshot saved")
    
    # Detect elements
    print("\n2. Detecting UI elements...")
    try:
        elements = detect_ui_elements("temp_screenshot.png")
        print(f"✓ Found {len(elements)} elements")
        
        # Show first 10
        print("\nFirst 10 elements:")
        for elem in elements[:10]:
            print(f"  {elem['id']}: {elem['description']}")
            print(f"       → Center: {elem['center']}")
        
        # Try to find Chrome
        print("\n3. Searching for Chrome...")
        chrome = find_element_by_name("temp_screenshot.png", ["chrome", "google chrome"])
        
        if chrome:
            print(f"✓ Found Chrome!")
            print(f"  ID: {chrome['id']}")
            print(f"  Description: {chrome['description']}")
            print(f"  Click coordinates: {chrome['center']}")
        else:
            print("⚠️  Chrome not found")
        
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCheck:")
        print("1. REPLICATE_API_TOKEN in .env")
        print("2. Internet connection")
        print("3. pip install replicate")


if __name__ == "__main__":
    quick_test()

