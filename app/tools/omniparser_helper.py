"""
OmniParser integration using RunPod Gradio deployment.

This module provides UI element detection using your private RunPod deployment
instead of the expensive Replicate API.
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional
from gradio_client import Client, file
from dotenv import load_dotenv
from app.core.logging_utils import get_logger

load_dotenv()
logger = get_logger("omniparser", "tools.log")

# Timeout and retry settings
API_TIMEOUT = 180  # 3 minutes timeout (OmniParser can be slow)
MAX_RETRIES = 2


class RunPodOmniParser:
    """Helper class for RunPod OmniParser integration via Gradio."""
    
    def __init__(self):
        """Initialize RunPod OmniParser helper."""
        self.gradio_url = os.getenv("RUNPOD_URL")
        
        if not self.gradio_url:
            raise ValueError(
                "RUNPOD_URL not found in environment!\n"
                "Add to .env file: RUNPOD_URL=https://your-runpod-url.gradio.live"
            )
        
        logger.info(f"Initialized OmniParser with RunPod URL: {self.gradio_url}")
    
    def detect_elements(
        self,
        image_path: str,
        box_threshold: float = 0.05,
        iou_threshold: float = 0.1
    ) -> Dict:
        """
        Detect UI elements using OmniParser on RunPod.
        EXACTLY matches test_agent.py syntax.
        """
        logger.info(f"Connecting to {self.gradio_url}...")
        
        # EXACT syntax from test_agent.py
        client = Client(self.gradio_url)
        
        logger.info(f"Sending image: {image_path}")
        
        # The API returns a tuple: (temporary_file_path_to_image, json_string)
        result = client.predict(
            image_input=file(image_path),
            box_threshold=box_threshold,
            iou_threshold=iou_threshold,
            api_name="/process"
        )
        
        # Handle the result - EXACT logic from test_agent.py
        if len(result) >= 2:
            # result[0] is the path to the labeled image (downloaded to a temp folder)
            temp_image_path = result[0]
            # result[1] is the text/coordinates
            json_output = result[1]
            
            logger.info(f"SUCCESS! Labeled image: {temp_image_path}")
            logger.info(f"JSON preview: {json_output[:200]}...")
            
            # Parse the JSON to extract elements
            elements = self._parse_elements(json_output)
            
            logger.info(f"Parsed {len(elements)} UI elements")
            
            return {
                "labeled_image_path": temp_image_path,
                "elements": elements,
                "raw_json": json_output
            }
        else:
            raise ValueError(f"Unexpected result format: {result}")
    
    def _parse_elements(self, json_output: str) -> List[Dict]:
        """
        Parse OmniParser output into clean element list.
        
        OmniParser returns elements in format (Python dict notation, not JSON):
        icon 0: {'type': 'text', 'bbox': [x1, y1, x2, y2], 'content': 'description'}
        icon 1: {'type': 'icon', 'bbox': [x1, y1, x2, y2], 'content': 'Chrome'}
        ...
        """
        elements = []
        
        try:
            import ast
            from PIL import ImageGrab
            
            # Get screen dimensions for converting normalized coordinates
            screen = ImageGrab.grab()
            screen_width, screen_height = screen.size
            logger.info(f"Screen dimensions: {screen_width}x{screen_height}")
            
            # Parse line by line
            lines = json_output.strip().split('\n')
            logger.info(f"Parsing {len(lines)} lines from OmniParser output")
            
            for line in lines:
                if not line.strip() or ':' not in line:
                    continue
                
                try:
                    # Format: "icon 103: {'type': 'icon', 'bbox': [...], 'content': '...'}"
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        continue
                    
                    element_id = parts[0].strip()
                    dict_str = parts[1].strip()
                    
                    # Parse the Python dict using ast.literal_eval
                    element_data = ast.literal_eval(dict_str)
                    
                    if not isinstance(element_data, dict):
                        continue
                    
                    bbox_norm = element_data.get('bbox', [])
                    content = element_data.get('content', '')
                    element_type = element_data.get('type', 'unknown')
                    
                    if bbox_norm and len(bbox_norm) >= 4:
                        # Convert normalized coordinates [0-1] to pixels
                        x1 = int(bbox_norm[0] * screen_width)
                        y1 = int(bbox_norm[1] * screen_height)
                        x2 = int(bbox_norm[2] * screen_width)
                        y2 = int(bbox_norm[3] * screen_height)
                        
                        bbox_pixels = [x1, y1, x2, y2]
                        center = self._get_bbox_center(bbox_pixels)
                        
                        elements.append({
                            'id': element_id,
                            'description': content,
                            'type': element_type,
                            'bbox': bbox_pixels,
                            'bbox_normalized': bbox_norm,
                            'center': center
                        })
                
                except Exception as e:
                    logger.debug(f"Failed to parse line: {line[:100]}... Error: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(elements)} elements")
        
        except Exception as e:
            logger.error(f"Failed to parse OmniParser output: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        return elements
    
    def _get_bbox_center(self, bbox: List) -> Tuple[int, int]:
        """Calculate center of bounding box."""
        if len(bbox) >= 4:
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            return int((x1 + x2) / 2), int((y1 + y2) / 2)
        return (0, 0)
    
    def find_element(
        self,
        elements: List[Dict],
        search_description: str
    ) -> Optional[Dict]:
        """
        Find element matching search description.
        
        Special handling for "URL bar" / "address bar" searches - uses geometric detection.
        
        Args:
            elements: List of parsed elements
            search_description: What to search for (e.g., "Chrome icon", "Save button", "URL bar")
        
        Returns:
            Best matching element or None
        """
        search_lower = search_description.lower()
        
        # Special case: URL bar / address bar detection
        if any(keyword in search_lower for keyword in ['url bar', 'address bar', 'url', 'address', 'search bar']):
            logger.info("Using geometric detection for URL/address bar")
            return self._find_url_bar(elements)
        
        # Normal text matching
        search_terms = search_lower.split()
        
        best_match = None
        best_score = 0
        
        for element in elements:
            description = element['description'].lower()
            element_type = element.get('type', '').lower()
            
            # Calculate match score
            score = 0
            for term in search_terms:
                if term in description:
                    score += 2
                if term in element_type:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = element
        
        if best_match:
            logger.info(f"Found match for '{search_description}': {best_match['id']} - {best_match['description']}")
        else:
            logger.warning(f"No match found for '{search_description}'")
        
        return best_match
    
    def _find_url_bar(self, elements: List[Dict]) -> Optional[Dict]:
        """
        Find URL bar using geometric properties instead of text matching.
        
        URL bars have distinctive characteristics:
        - Very wide (typically > 400px)
        - Very thin (high aspect ratio > 15:1)
        - Near top of screen (y < 200)
        - Type is 'text'
        - Contains URL-like content (http, .com, /, etc.)
        """
        logger.info("Detecting URL bar using geometric analysis...")
        
        candidates = []
        
        for element in elements:
            bbox = element['bbox']
            if len(bbox) < 4:
                continue
            
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            center_x, center_y = element['center']
            
            # Skip if height is 0 to avoid division by zero
            if height == 0:
                continue
            
            aspect_ratio = width / height
            description = element['description'].lower()
            
            # Scoring based on URL bar characteristics
            score = 0
            reasons = []
            
            # 1. Width (URL bar is wide)
            if width > 400:
                score += 5
                reasons.append(f"wide ({width}px)")
            elif width > 250:
                score += 2
                reasons.append(f"medium width ({width}px)")
            
            # 2. Aspect ratio (URL bar is very horizontal)
            if aspect_ratio > 20:
                score += 5
                reasons.append(f"very horizontal (ratio {aspect_ratio:.1f}:1)")
            elif aspect_ratio > 15:
                score += 3
                reasons.append(f"horizontal (ratio {aspect_ratio:.1f}:1)")
            elif aspect_ratio > 10:
                score += 1
            
            # 3. Position (URL bar is near top, but not at very top)
            if 50 < center_y < 150:
                score += 5
                reasons.append(f"perfect position (y={center_y})")
            elif center_y < 200:
                score += 2
                reasons.append(f"near top (y={center_y})")
            
            # 4. Type (URL bar contains text)
            if element.get('type') == 'text':
                score += 2
                reasons.append("text type")
            
            # 5. Content (contains URL-like patterns)
            url_patterns = ['http', 'www', '.com', '.net', '.org', '/', ':', '//']
            url_matches = sum(1 for pattern in url_patterns if pattern in description)
            if url_matches >= 2:
                score += 3
                reasons.append(f"URL-like content ({url_matches} patterns)")
            elif url_matches >= 1:
                score += 1
            
            # 6. Horizontal center (URL bar is usually centered horizontally)
            # Assuming typical screen width around 1920px
            if 200 < center_x < 1000:
                score += 1
                reasons.append("centered")
            
            if score >= 8:  # Minimum threshold
                candidates.append({
                    'element': element,
                    'score': score,
                    'reasons': reasons
                })
                logger.info(f"  Candidate: {element['id']} - score={score}, reasons={reasons}")
        
        if not candidates:
            logger.warning("No URL bar candidates found")
            return None
        
        # Sort by score and return best match
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        
        logger.info(f"Selected URL bar: {best['element']['id']} (score={best['score']})")
        logger.info(f"  Description: {best['element']['description']}")
        logger.info(f"  Reasons: {', '.join(best['reasons'])}")
        
        return best['element']
    
    def get_all_elements_text(self, elements: List[Dict]) -> str:
        """Get formatted text of all elements for LLM context."""
        lines = []
        for elem in elements:
            lines.append(
                f"{elem['id']}: {elem['description']} "
                f"(type: {elem.get('type', 'unknown')}) "
                f"at center {elem['center']}"
            )
        return "\n".join(lines)


# ============================================================================
# Singleton instance for easy access
# ============================================================================

_omniparser_instance: Optional[RunPodOmniParser] = None


def get_omniparser() -> RunPodOmniParser:
    """Get or create the singleton OmniParser instance."""
    global _omniparser_instance
    if _omniparser_instance is None:
        _omniparser_instance = RunPodOmniParser()
    return _omniparser_instance


def detect_ui_elements(image_path: str) -> List[Dict]:
    """
    Detect all UI elements on screenshot using RunPod OmniParser.
    
    Args:
        image_path: Path to screenshot
    
    Returns:
        List of elements with id, description, type, bbox, center
    """
    parser = get_omniparser()
    result = parser.detect_elements(image_path)
    return result['elements']


def find_element_by_description(image_path: str, description: str) -> Optional[Dict]:
    """
    Find specific element on screenshot.
    
    Args:
        image_path: Path to screenshot
        description: What to look for (e.g., "Chrome icon", "Save button")
    
    Returns:
        Element dict with id, description, bbox, center or None
    """
    parser = get_omniparser()
    result = parser.detect_elements(image_path)
    return parser.find_element(result['elements'], description)

