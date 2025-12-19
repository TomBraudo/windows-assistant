"""
Element filtering tool for smart UI element selection.

Filters UI elements based on position, size, type, and keywords
to reduce noise before sending to refiner.
"""

from typing import List, Dict, Optional, Tuple
from app.core.logging_utils import get_logger

logger = get_logger("element_filter", "tools.log")


class ElementFilter:
    """Filter UI elements based on various criteria."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize filter with screen dimensions.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def filter_elements(
        self,
        elements: List[Dict],
        position_filter: Optional[Dict] = None,
        size_filter: Optional[Dict] = None,
        type_filter: Optional[List[str]] = None,
        keyword_filter: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        min_results: int = 5
    ) -> List[Dict]:
        """
        Filter elements based on multiple criteria.
        
        Args:
            elements: List of UI elements to filter
            position_filter: Dict with x_min, x_max, y_min, y_max (as percentages 0-1 or pixels)
            size_filter: Dict with min_width, max_width, min_height, max_height, 
                        min_aspect_ratio, max_aspect_ratio
            type_filter: List of allowed types (e.g., ['icon', 'text'])
            keyword_filter: List of keywords - element must contain at least one
            exclude_keywords: List of keywords - element must NOT contain any
            min_results: Minimum results to return (loosen filters if needed)
        
        Returns:
            Filtered list of elements
        """
        logger.info(f"Starting filter with {len(elements)} elements")
        
        filtered = elements.copy()
        
        # Track filter effectiveness
        filter_stats = {
            "initial": len(filtered),
            "after_position": 0,
            "after_size": 0,
            "after_type": 0,
            "after_keyword": 0,
            "after_exclude": 0
        }
        
        # 1. Position filter
        if position_filter:
            filtered = self._filter_by_position(filtered, position_filter)
            filter_stats["after_position"] = len(filtered)
            logger.info(f"After position filter: {len(filtered)} elements")
        
        # 2. Size filter
        if size_filter:
            filtered = self._filter_by_size(filtered, size_filter)
            filter_stats["after_size"] = len(filtered)
            logger.info(f"After size filter: {len(filtered)} elements")
        
        # 3. Type filter
        if type_filter:
            filtered = self._filter_by_type(filtered, type_filter)
            filter_stats["after_type"] = len(filtered)
            logger.info(f"After type filter: {len(filtered)} elements")
        
        # 4. Keyword filter (include)
        if keyword_filter:
            filtered = self._filter_by_keywords(filtered, keyword_filter, include=True)
            filter_stats["after_keyword"] = len(filtered)
            logger.info(f"After keyword filter: {len(filtered)} elements")
        
        # 5. Exclude keywords
        if exclude_keywords:
            filtered = self._filter_by_keywords(filtered, exclude_keywords, include=False)
            filter_stats["after_exclude"] = len(filtered)
            logger.info(f"After exclude filter: {len(filtered)} elements")
        
        # If too few results, relax filters progressively
        if len(filtered) < min_results:
            logger.warning(f"Only {len(filtered)} elements after filtering (min: {min_results})")
            logger.warning("Relaxing filters to get more results...")
            
            # Try without exclude keywords first
            if exclude_keywords:
                filtered = self._refilter_without(
                    elements, position_filter, size_filter, 
                    type_filter, keyword_filter, None
                )
            
            # Still too few? Try without keyword filter
            if len(filtered) < min_results and keyword_filter:
                filtered = self._refilter_without(
                    elements, position_filter, size_filter, 
                    type_filter, None, None
                )
            
            # Still too few? Try without type filter
            if len(filtered) < min_results and type_filter:
                filtered = self._refilter_without(
                    elements, position_filter, size_filter, 
                    None, None, None
                )
            
            logger.info(f"After relaxing filters: {len(filtered)} elements")
        
        logger.info(f"Filter stats: {filter_stats}")
        logger.info(f"Final filtered count: {len(filtered)}")
        
        return filtered
    
    def _filter_by_position(self, elements: List[Dict], pos_filter: Dict) -> List[Dict]:
        """Filter by position (x, y coordinates)."""
        filtered = []
        
        for elem in elements:
            center_x, center_y = elem['center']
            bbox = elem['bbox']
            
            # Convert percentage to pixels if needed
            x_min = self._to_pixels(pos_filter.get('x_min'), self.screen_width, is_x=True)
            x_max = self._to_pixels(pos_filter.get('x_max'), self.screen_width, is_x=True)
            y_min = self._to_pixels(pos_filter.get('y_min'), self.screen_height, is_x=False)
            y_max = self._to_pixels(pos_filter.get('y_max'), self.screen_height, is_x=False)
            
            # Check if center point is within bounds
            passes = True
            
            if x_min is not None and center_x < x_min:
                passes = False
            if x_max is not None and center_x > x_max:
                passes = False
            if y_min is not None and center_y < y_min:
                passes = False
            if y_max is not None and center_y > y_max:
                passes = False
            
            if passes:
                filtered.append(elem)
        
        return filtered
    
    def _filter_by_size(self, elements: List[Dict], size_filter: Dict) -> List[Dict]:
        """Filter by size (width, height, aspect ratio)."""
        filtered = []
        
        for elem in elements:
            bbox = elem['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            aspect_ratio = width / height if height > 0 else 0
            
            passes = True
            
            if size_filter.get('min_width') and width < size_filter['min_width']:
                passes = False
            if size_filter.get('max_width') and width > size_filter['max_width']:
                passes = False
            if size_filter.get('min_height') and height < size_filter['min_height']:
                passes = False
            if size_filter.get('max_height') and height > size_filter['max_height']:
                passes = False
            if size_filter.get('min_aspect_ratio') and aspect_ratio < size_filter['min_aspect_ratio']:
                passes = False
            if size_filter.get('max_aspect_ratio') and aspect_ratio > size_filter['max_aspect_ratio']:
                passes = False
            
            if passes:
                filtered.append(elem)
        
        return filtered
    
    def _filter_by_type(self, elements: List[Dict], type_filter: List[str]) -> List[Dict]:
        """Filter by element type."""
        return [
            elem for elem in elements
            if elem.get('type', 'unknown') in type_filter
        ]
    
    def _filter_by_keywords(
        self, 
        elements: List[Dict], 
        keywords: List[str],
        include: bool = True
    ) -> List[Dict]:
        """
        Filter by keywords in description.
        
        Args:
            include: If True, keep elements that contain ANY keyword
                    If False, exclude elements that contain ANY keyword
        """
        filtered = []
        
        for elem in elements:
            desc_lower = elem['description'].lower()
            has_keyword = any(kw.lower() in desc_lower for kw in keywords)
            
            if include and has_keyword:
                filtered.append(elem)
            elif not include and not has_keyword:
                filtered.append(elem)
        
        return filtered
    
    def _to_pixels(
        self, 
        value: Optional[float], 
        dimension: int,
        is_x: bool
    ) -> Optional[int]:
        """
        Convert value to pixels.
        
        If value is between 0-1, treat as percentage.
        If value is > 1, treat as absolute pixels.
        """
        if value is None:
            return None
        
        if 0 <= value <= 1:
            # Percentage
            return int(value * dimension)
        else:
            # Absolute pixels
            return int(value)
    
    def _refilter_without(
        self,
        elements: List[Dict],
        position_filter: Optional[Dict],
        size_filter: Optional[Dict],
        type_filter: Optional[List[str]],
        keyword_filter: Optional[List[str]],
        exclude_keywords: Optional[List[str]]
    ) -> List[Dict]:
        """Reapply filters with some disabled."""
        return self.filter_elements(
            elements,
            position_filter=position_filter,
            size_filter=size_filter,
            type_filter=type_filter,
            keyword_filter=keyword_filter,
            exclude_keywords=exclude_keywords,
            min_results=0  # Don't recursively relax
        )


def create_taskbar_filter(screen_width: int, screen_height: int) -> Dict:
    """
    Create a filter for taskbar icons.
    
    Returns:
        Filter specification dict
    """
    return {
        "position_filter": {
            "y_min": 0.9,  # Bottom 10% of screen
            "y_max": None
        },
        "type_filter": ["icon"],
        "size_filter": {
            "min_width": 20,  # Small icons
            "max_width": 100,
            "min_height": 20,
            "max_height": 100
        }
    }


def create_url_bar_filter(screen_width: int, screen_height: int) -> Dict:
    """
    Create a filter for URL bars.
    
    Returns:
        Filter specification dict
    """
    return {
        "position_filter": {
            "y_min": 0,
            "y_max": 0.2,  # Top 20% of screen
        },
        "size_filter": {
            "min_width": screen_width * 0.2,  # At least 20% of screen width
            "min_aspect_ratio": 10  # Very horizontal (wide and thin)
        },
        "type_filter": ["text"]
    }

