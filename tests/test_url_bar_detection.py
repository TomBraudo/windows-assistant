"""
Test script for URL bar detection with OmniParser.

This test identifies how OmniParser labels the Chrome URL bar (address bar).
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.tools.omniparser_helper import get_omniparser

load_dotenv()

# Setup logging
LOG_FILE = "logs/url_bar_test.log"
OUTPUT_DIR = "test_output/url_bar"
os.makedirs("logs", exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_and_print(message):
    """Print to console and log to file."""
    print(message)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_separator():
    """Log a separator line."""
    sep = "="*70
    log_and_print(sep)

def test_url_bar_detection():
    """Test URL bar detection with OmniParser."""
    
    # Clear log file at start
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"URL BAR DETECTION TEST LOG\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n\n")
    
    log_separator()
    log_and_print("🔍 URL BAR DETECTION TEST")
    log_separator()
    log_and_print("")
    log_and_print("Goal: Identify how OmniParser labels the Chrome URL/address bar")
    log_and_print("")
    
    # Test image path
    image_path = r"C:\Users\tombr\OneDrive\Desktop\screenshots\url_test.png"
    
    # Check if image exists
    if not os.path.exists(image_path):
        log_and_print(f"❌ ERROR: Test image not found at: {image_path}")
        log_and_print("\nPlease ensure Chrome is open with URL bar visible and save a screenshot to:")
        log_and_print(image_path)
        return False
    
    log_and_print(f"✓ Test image found: {image_path}")
    log_and_print(f"  File size: {os.path.getsize(image_path)} bytes")
    
    # Check RUNPOD_URL
    runpod_url = os.getenv("RUNPOD_URL")
    if not runpod_url:
        log_and_print("\n❌ ERROR: RUNPOD_URL not found in .env file!")
        return False
    
    log_and_print(f"\n✓ RUNPOD_URL: {runpod_url}")
    
    try:
        # Initialize OmniParser
        log_and_print("\n📡 Connecting to OmniParser...")
        parser = get_omniparser()
        log_and_print("✓ Connected successfully")
        
        # Detect elements
        log_and_print("\n🔍 Analyzing URL bar screenshot with OmniParser...")
        log_and_print("   (This may take 10-30 seconds...)")
        
        start_time = time.time()
        result = parser.detect_elements(image_path)
        elapsed = time.time() - start_time
        
        log_and_print(f"\n✓ Analysis complete in {elapsed:.1f} seconds")
        
        elements = result.get('elements', [])
        labeled_image_path = result.get('labeled_image_path')
        raw_json = result.get('raw_json', '')
        
        log_and_print(f"✓ Found {len(elements)} UI elements")
        
        # Save outputs
        import shutil
        
        # Save labeled image
        if labeled_image_path:
            output_image = os.path.join(OUTPUT_DIR, "labeled_url_bar.png")
            shutil.copy(labeled_image_path, output_image)
            log_and_print(f"\n✓ Labeled image saved: {output_image}")
            
            # Open the image
            import platform
            try:
                if platform.system() == "Windows":
                    os.startfile(output_image)
                    log_and_print("✓ Labeled image opened in viewer")
            except:
                pass
        
        # Save raw JSON
        json_output_path = os.path.join(OUTPUT_DIR, "url_bar_elements.json")
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(raw_json)
        log_and_print(f"✓ Raw JSON saved: {json_output_path}")
        
        # Log ALL elements
        log_and_print("\n" + "="*70)
        log_and_print(f"📋 ALL {len(elements)} DETECTED ELEMENTS:")
        log_and_print("="*70)
        
        url_bar_candidates = []
        
        for i, elem in enumerate(elements, 1):
            log_and_print(f"\nElement {i}:")
            log_and_print(f"  ID: {elem['id']}")
            log_and_print(f"  Description: '{elem['description']}'")
            log_and_print(f"  Type: {elem.get('type', 'unknown')}")
            log_and_print(f"  Center: {elem['center']}")
            log_and_print(f"  BBox: {elem['bbox']}")
            
            # Check if this might be the URL bar
            desc_lower = elem['description'].lower()
            if any(keyword in desc_lower for keyword in [
                'url', 'address', 'search', 'bar', 'http', 'www', 'chrome', 
                '.com', 'google', 'omnibox', 'location'
            ]):
                log_and_print(f"  >>> 🎯 POTENTIAL URL BAR CANDIDATE! <<<")
                url_bar_candidates.append(elem)
        
        log_and_print("\n" + "="*70)
        
        # Test the new geometric detector
        log_and_print("\n" + "="*70)
        log_and_print("🤖 TESTING GEOMETRIC URL BAR DETECTOR")
        log_and_print("="*70)
        
        detected_url_bar = parser._find_url_bar(elements)
        
        if detected_url_bar:
            log_and_print(f"\n✅ GEOMETRIC DETECTOR FOUND URL BAR:")
            log_and_print(f"  ID: {detected_url_bar['id']}")
            log_and_print(f"  Description: '{detected_url_bar['description']}'")
            log_and_print(f"  Type: {detected_url_bar.get('type', 'unknown')}")
            log_and_print(f"  Center: {detected_url_bar['center']}")
            log_and_print(f"  BBox: {detected_url_bar['bbox']}")
            
            bbox = detected_url_bar['bbox']
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            aspect_ratio = width / height if height > 0 else 0
            
            log_and_print(f"\n  Dimensions:")
            log_and_print(f"    Width: {width}px")
            log_and_print(f"    Height: {height}px")
            log_and_print(f"    Aspect Ratio: {aspect_ratio:.1f}:1")
            log_and_print(f"    Position: ({x1}, {y1}) to ({x2}, {y2})")
            
            log_and_print(f"\n  💡 To click this URL bar, use:")
            log_and_print(f"    click_element('URL bar')")
            log_and_print(f"    or")
            log_and_print(f"    click_at_coordinates({detected_url_bar['center'][0]}, {detected_url_bar['center'][1]})")
        else:
            log_and_print("\n❌ GEOMETRIC DETECTOR DID NOT FIND URL BAR")
        
        # Analyze keyword-based candidates
        log_and_print("\n" + "="*70)
        log_and_print("🔍 KEYWORD-BASED CANDIDATES (for comparison)")
        log_and_print("="*70)
        
        if url_bar_candidates:
            log_and_print(f"\nFound {len(url_bar_candidates)} potential URL bar element(s):\n")
            
            for i, candidate in enumerate(url_bar_candidates, 1):
                log_and_print(f"\nCandidate {i}:")
                log_and_print(f"  ID: {candidate['id']}")
                log_and_print(f"  Description: '{candidate['description']}'")
                log_and_print(f"  Type: {candidate.get('type', 'unknown')}")
                log_and_print(f"  Center: {candidate['center']}")
                log_and_print(f"  BBox: {candidate['bbox']}")
                
                # Calculate position relative to screen
                bbox = candidate['bbox']
                x1, y1, x2, y2 = bbox
                width = x2 - x1
                height = y2 - y1
                
                log_and_print(f"  Width: {width}px, Height: {height}px")
                log_and_print(f"  Position: Top-left at ({x1}, {y1})")
                
            # Recommend the best candidate
            log_and_print("\n" + "="*70)
            log_and_print("💡 RECOMMENDATION:")
            log_and_print("="*70)
            
            # Usually URL bar is wide and horizontal, near the top
            best_candidate = None
            best_score = 0
            
            for candidate in url_bar_candidates:
                bbox = candidate['bbox']
                x1, y1, x2, y2 = bbox
                width = x2 - x1
                height = y2 - y1
                
                # Score based on:
                # - Width (wider is better for URL bar)
                # - Aspect ratio (URL bar is very wide vs height)
                # - Position (higher on screen is better)
                aspect_ratio = width / height if height > 0 else 0
                
                score = 0
                if width > 400:  # URL bar should be wide
                    score += 3
                if aspect_ratio > 5:  # URL bar is long and thin
                    score += 2
                if y1 < 200:  # URL bar is near top
                    score += 1
                if candidate.get('type') == 'text':  # URL bar contains text
                    score += 1
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if best_candidate:
                log_and_print(f"\n🎯 BEST KEYWORD-BASED CANDIDATE:")
                log_and_print(f"   ID: {best_candidate['id']}")
                log_and_print(f"   Description: '{best_candidate['description']}'")
                log_and_print(f"   Center: {best_candidate['center']}")
        else:
            log_and_print("\n⚠️  No keyword-based candidates found")
            log_and_print("   (This is expected - URL bar is labeled with its content, not 'url bar')")
        
        # Final recommendation
        log_and_print("\n" + "="*70)
        log_and_print("💡 FINAL RECOMMENDATION")
        log_and_print("="*70)
        
        if detected_url_bar:
            log_and_print(f"\n✅ USE GEOMETRIC DETECTOR for URL bar:")
            log_and_print(f"   Element: {detected_url_bar['id']}")
            log_and_print(f"   Description: '{detected_url_bar['description']}'")
            log_and_print(f"   Coordinates: {detected_url_bar['center']}")
            log_and_print(f"\n   In your agent, use:")
            log_and_print(f"   >>> click_element('URL bar') <<<")
            log_and_print(f"   >>> click_element('address bar') <<<")
            log_and_print(f"   The helper will automatically use geometric detection!")
        else:
            log_and_print("\n⚠️  Geometric detector failed to find URL bar")
            log_and_print("   Please review the labeled image and all elements above")
        
        # Summary
        log_and_print("\n" + "="*70)
        log_and_print("✅ TEST COMPLETE")
        log_and_print("="*70)
        log_and_print(f"\n📁 Output Files:")
        log_and_print(f"   • Log: {os.path.abspath(LOG_FILE)}")
        log_and_print(f"   • Labeled image: {os.path.abspath(output_image) if labeled_image_path else 'N/A'}")
        log_and_print(f"   • JSON data: {os.path.abspath(json_output_path)}")
        log_and_print("\n" + "="*70)
        
        return True
        
    except Exception as e:
        log_and_print(f"\n❌ ERROR: {e}")
        import traceback
        error_trace = traceback.format_exc()
        log_and_print(error_trace)
        return False

if __name__ == "__main__":
    try:
        success = test_url_bar_detection()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        log_and_print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        log_and_print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

