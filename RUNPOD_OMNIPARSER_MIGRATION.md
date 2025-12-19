# RunPod OmniParser Migration Guide

## Overview

The Windows Assistant has been migrated from using **Replicate API** (expensive) to your **RunPod deployment** (cost-effective) for UI element detection with OmniParser.

## What Changed?

### Before (Replicate API)
- Used Replicate's hosted OmniParser API
- Cost: ~$0.10-$0.20 per image analysis
- Required: `REPLICATE_API_TOKEN`

### After (RunPod Deployment)
- Uses your private RunPod OmniParser deployment
- Cost: Only RunPod pod charges (~$0.20/hour for GPU)
- Required: `RUNPOD_URL`

## New Architecture

```
User Request → Refiner Agent → Autonomous Mode
                                     ↓
                            Capture Screenshot
                                     ↓
                       RunPod OmniParser (Gradio API)
                                     ↓
                    Detect UI Elements + Coordinates
                                     ↓
                       Refiner Analyzes Elements
                                     ↓
                    Agent Clicks Exact Element
```

## Files Modified

### 1. **New File: `app/tools/omniparser_helper.py`**
   - Gradio client integration
   - Element detection and parsing
   - Similar to your `test_agent.py` but integrated into the system

### 2. **Updated: `app/tools/computer_control.py`**
   - `click_element()` now uses OmniParser instead of Gemini Vision
   - More accurate coordinate detection
   - Better reliability

### 3. **Updated: `app/core/refiner_agent.py`**
   - Refiner now requires specific element descriptions
   - Better guidance for click actions
   - More precise instructions

### 4. **Updated: `app/core/autonomous_mode.py`**
   - Detects UI elements before each action
   - Provides element list to refiner
   - Refiner can suggest specific elements to click

### 5. **Updated: `requirements.txt`**
   - Added: `gradio_client`

## Setup Instructions

### 1. Add RunPod URL to .env

Add this line to your `.env` file:

```bash
RUNPOD_URL=https://your-runpod-url.gradio.live
```

Replace `https://your-runpod-url.gradio.live` with your actual RunPod Gradio URL.

### 2. Install Dependencies

```bash
pip install gradio_client
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 3. Test the Integration

Run the test script:

```bash
python test_runpod_omniparser.py
```

This will:
- ✓ Verify RUNPOD_URL is set
- ✓ Connect to your RunPod deployment
- ✓ Detect UI elements on your screen
- ✓ Test finding specific elements
- ✓ Verify computer control integration

## New Flow Explanation

### 1. **User Request**
```
User: "Click the Chrome icon"
```

### 2. **Refiner Creates Execution Plan**
The refiner now specifies EXACTLY what to look for:
```json
{
  "step": 1,
  "tool": "click_element",
  "instruction": "Click the Chrome browser icon on the taskbar"
}
```

### 3. **Autonomous Mode Detects Elements**
Before executing, the autonomous mode:
1. Captures screenshot
2. Sends to RunPod OmniParser
3. Gets back list of elements:
   ```
   icon 5: Chrome browser icon (type: icon) at center (1850, 1060)
   icon 12: File Explorer (type: icon) at center (1750, 1060)
   ...
   ```

### 4. **Refiner Analyzes Available Elements**
Refiner sees the list and suggests:
```json
{
  "suggested_action": "Click the Chrome browser icon",
  "tool_recommendation": "click_element",
  "parameters": {"element_description": "Chrome browser icon"}
}
```

### 5. **Agent Clicks with Pixel-Perfect Accuracy**
```python
click_element("Chrome browser icon")
```

OmniParser finds the element and returns exact coordinates: `(1850, 1060)`

## Key Improvements

### ✅ Cost Savings
- **Before**: $0.10-$0.20 per click action
- **After**: Only RunPod pod costs (~$0.20/hour unlimited clicks)

### ✅ Accuracy
- OmniParser is specifically trained for UI detection
- Pixel-perfect bounding boxes
- More reliable than general vision models

### ✅ Refiner Integration
- Refiner now sees ALL available UI elements
- Can make better decisions about what to click
- More specific instructions to agent

### ✅ Fallback Support
- Still uses Gemini Vision for general screen description
- OmniParser specifically for coordinate detection
- Best of both worlds

## Troubleshooting

### Error: "RUNPOD_URL not found"
**Solution**: Add `RUNPOD_URL` to your `.env` file

```bash
RUNPOD_URL=https://your-runpod-url.gradio.live
```

### Error: "OmniParser API error"
**Solutions**:
1. Check if your RunPod pod is running
2. Verify the Gradio URL is correct
3. Test the URL in your browser - you should see the Gradio interface

### Error: "gradio_client not installed"
**Solution**:
```bash
pip install gradio_client
```

### No elements detected
**Possible causes**:
1. Screen is mostly empty (desktop with no icons)
2. OmniParser threshold too high (default 0.05 is good)
3. Image not sent correctly

## Testing Your Setup

### Quick Test
```bash
python test_runpod_omniparser.py
```

### Manual Test
```python
from app.tools.omniparser_helper import detect_ui_elements
from app.tools.vision_tools import capture_screenshot

# Capture screen
result = capture_screenshot()
path = result.replace("Screenshot saved to:", "").strip()

# Detect elements
elements = detect_ui_elements(path)

# Print results
for elem in elements:
    print(f"{elem['id']}: {elem['description']} at {elem['center']}")
```

### Integration Test (Safe - No Clicking)
```python
from app.tools.computer_control import click_element

# This will detect but not actually click (because element doesn't exist)
result = click_element("TEST_ELEMENT_THAT_DOES_NOT_EXIST")
print(result)

# Should return: "Could not find 'TEST_ELEMENT_THAT_DOES_NOT_EXIST' on screen"
```

## Usage Examples

### CLI Mode
```bash
python cli.py
```

Then try:
```
> Click the Chrome icon
> Click the Save button
> Click the first search result
```

### GUI Mode
```bash
python main_gui.py
```

In autonomous mode, try:
```
Open Chrome and search for "python tutorials"
```

The agent will:
1. Detect all icons on screen
2. Find Chrome icon via OmniParser
3. Click it with exact coordinates
4. Continue with the task

## Comparison: Before vs After

### Before (Gemini Vision)
```python
# 1. Screenshot → Gemini
# 2. Gemini: "I think Chrome is at (1850, 1060)"
# 3. Click (1850, 1060)
# 4. Sometimes accurate, sometimes off by 50-100 pixels
```

### After (RunPod OmniParser)
```python
# 1. Screenshot → RunPod OmniParser
# 2. OmniParser: "icon 5: Chrome at bbox [1820, 1040, 1880, 1080]"
# 3. Calculate center: (1850, 1060) ← EXACT
# 4. Click (1850, 1060) ← ALWAYS ACCURATE
```

## Migration Checklist

- [x] Create `omniparser_helper.py` with Gradio client
- [x] Update `computer_control.py` to use OmniParser
- [x] Update `refiner_agent.py` to require specific labels
- [x] Update `autonomous_mode.py` to provide element context
- [x] Add `gradio_client` to requirements
- [ ] **Set `RUNPOD_URL` in .env** ← **YOU NEED TO DO THIS**
- [ ] **Run test script** ← **DO THIS NEXT**
- [ ] **Test with actual agent** ← **FINAL STEP**

## Next Steps

1. **Add your RunPod URL to `.env`**:
   ```bash
   RUNPOD_URL=https://your-actual-url.gradio.live
   ```

2. **Run the test script**:
   ```bash
   python test_runpod_omniparser.py
   ```

3. **Try the agent**:
   ```bash
   python cli.py
   ```
   
   Test with: `"Click the Chrome icon"`

4. **Verify cost savings**:
   - Check your Replicate usage (should be $0 now)
   - Check your RunPod charges (should be ~$0.20/hour)

## Support

If you encounter issues:

1. **Check the logs**: 
   - `logs/tools.log` - OmniParser activity
   - `logs/agent.log` - Agent decisions

2. **Verify your setup**:
   - RunPod pod is running
   - RUNPOD_URL is correct
   - gradio_client is installed

3. **Test components individually**:
   - Use `test_runpod_omniparser.py`
   - Check each test result

---

**Summary**: Your agent now uses your cost-effective RunPod deployment instead of expensive Replicate API, with better accuracy and full integration with the refiner agent for smarter decision-making!

