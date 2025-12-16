# Computer Control Mode - Complete Guide

## 🎯 Overview

The Windows Agent now has **autonomous computer control** capabilities! This means the agent can:
- **See** your screen using Gemini Vision
- **Click** buttons, icons, and UI elements
- **Type** text into any application
- **Navigate** using keyboard shortcuts
- **Interact** with any GUI application autonomously

## 🧠 Model Architecture

Your agent uses a **4-model AI pipeline**:

### 1. **Refiner Agent** (Planning)
- **Model**: OpenRouter DeepSeek R1-T2 Chimera (Free)
- **Role**: Breaks down user requests into execution plans
- **Example**: "Click the Chrome icon and search for Python" → 
  - Step 1: `click_element` - Click Chrome icon
  - Step 2: `type_text` - Type search query
  - Step 3: `press_key` - Press Enter

### 2. **Vision Model** (Screen Understanding)
- **Model**: Google Gemini 2.0 Flash Experimental
- **Fallbacks**: Gemini 2.0 Flash, Gemini 1.5 Flash
- **Role**: Analyzes screenshots to find UI elements and coordinates
- **Cost**: ~$0.00125 per screenshot (very cheap!)

### 3. **Main Agent** (Tool Execution)
- **Model**: Groq Llama 3.1 70B
- **Role**: Executes individual tool calls with correct parameters
- **Speed**: <1 second per action

### 4. **Judge Agent** (Validation)
- **Model**: OpenRouter DeepSeek R1-T2 Chimera (Free)
- **Role**: Validates actions weren't hallucinated
- **Purpose**: Ensures agent actually performed claimed actions

## 🎮 Available Computer Control Tools

### Mouse Control

#### 1. `click_element` (Vision-Guided) ⭐ **Most Powerful**
Finds and clicks UI elements by description.

**Examples:**
```
"Click the Save button"
"Click the Chrome icon on the taskbar"
"Click the Submit button in the form"
"Click the X button to close the window"
```

**How it works:**
1. Captures screenshot
2. Gemini analyzes image and finds element
3. Returns coordinates
4. Clicks at those coordinates

#### 2. `click_at_coordinates`
Precise clicking when you know exact coordinates.

**Parameters:**
- `x`: Pixels from left edge
- `y`: Pixels from top edge
- `clicks`: 1 for single, 2 for double click
- `button`: "left", "right", or "middle"

#### 3. `move_mouse`
Move cursor without clicking.

#### 4. `drag_to`
Click and drag to move windows, select text, etc.

#### 5. `get_mouse_position`
Get current cursor position (helpful for debugging).

#### 6. `scroll`
Scroll up/down by specified clicks.

### Keyboard Control

#### 7. `type_text`
Type text into the focused application.

**Parameters:**
- `text`: What to type
- `interval`: Delay between keystrokes (default: 0.05s)
- `press_enter`: Auto-press Enter after typing

**Example:**
```
type_text("Hello World", press_enter=True)
```

#### 8. `press_key`
Press individual keys like Enter, Tab, Escape, etc.

**Supported keys:**
- Navigation: `enter`, `tab`, `esc`, `backspace`, `delete`, `space`
- Arrows: `up`, `down`, `left`, `right`
- Function keys: `f1` through `f12`
- Special: `home`, `end`, `pageup`, `pagedown`

#### 9. `hotkey`
Press keyboard shortcuts (multiple keys simultaneously).

**Common shortcuts:**
- `hotkey("ctrl", "c")` - Copy
- `hotkey("ctrl", "v")` - Paste
- `hotkey("ctrl", "s")` - Save
- `hotkey("alt", "tab")` - Switch windows
- `hotkey("win", "d")` - Show desktop
- `hotkey("ctrl", "alt", "delete")` - Task manager

## 📋 Usage Examples

### Example 1: Fill Out a Web Form
```
User: "Fill out the contact form with name 'John Doe' and email 'john@example.com', then submit it"
```

**Agent's Execution Plan:**
1. `click_element` → Click the Name field
2. `type_text` → Type "John Doe"
3. `press_key` → Press Tab to move to next field
4. `type_text` → Type "john@example.com"
5. `click_element` → Click the Submit button

### Example 2: Open Notepad and Write
```
User: "Open Notepad, write 'Hello World', and save it as test.txt on Desktop"
```

**Agent's Execution Plan:**
1. `hotkey` → Press Win key to open Start menu
2. `type_text` → Type "notepad" with press_enter=True
3. `type_text` → Type "Hello World"
4. `hotkey` → Press Ctrl+S to save
5. `type_text` → Type file path
6. `press_key` → Press Enter

### Example 3: Navigate Chrome
```
User: "Open Chrome, go to GitHub, and search for 'python automation'"
```

**Agent's Execution Plan:**
1. `click_element` → Click Chrome icon
2. `click_element` → Click address bar
3. `type_text` → Type "github.com" with press_enter=True
4. `click_element` → Click search box on GitHub
5. `type_text` → Type "python automation" with press_enter=True

### Example 4: Complex Multi-App Task
```
User: "Take a screenshot, analyze what's on screen, and create a report document describing it"
```

**Agent's Execution Plan:**
1. `capture_screenshot` → Capture current screen
2. `analyze_image` → Use Gemini to describe screenshot
3. `create_note` → Create Word document with analysis
4. ✓ Document opens automatically

## 🔒 Safety Features

### 1. Rate Limiting
- **Limit**: 30 actions per minute
- **Purpose**: Prevents agent from spamming actions
- **Override**: Wait 60 seconds or restart

### 2. Failsafe
- **PyAutoGUI Failsafe**: Move mouse to **top-left corner** to abort
- **Purpose**: Emergency stop if agent goes rogue

### 3. Coordinate Validation
- All coordinates checked against screen bounds
- Invalid coordinates rejected before execution

### 4. Safe Mode (Optional)
- Human confirmation for sensitive actions
- Toggle in Settings or .env: `SAFE_MODE=True`

### 5. Restricted Apps (Future)
Currently commented out but can be enabled:
```python
RESTRICTED_APPS = ["cmd.exe", "powershell.exe", "regedit.exe"]
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- `pyautogui` - Mouse and keyboard control
- `google-genai` - Gemini vision API
- `pillow` - Image processing
- All existing dependencies

### 2. Configure API Keys

You need **2 API keys** for full functionality:

#### **Gemini API Key** (Required for Vision)
1. Go to: https://aistudio.google.com/app/apikey
2. Create a free API key
3. Add to `.env` file:
```
GEMINI_API_KEY=your_key_here
```

#### **Groq API Key** (Already configured)
Used for main agent - you already have this.

### 3. Run the Agent

**CLI Mode:**
```bash
python cli.py
```

**GUI Mode:**
```bash
python main_gui.py
```

### 4. Try Computer Control

**Simple test:**
```
"Click the Start button"
"Move the mouse to position 500, 300"
"Type 'Hello World' and press Enter"
```

**Complex test:**
```
"Open Chrome, search for 'python tutorials', and click the first result"
```

## 🎯 What Happens When You Use Computer Control?

### Execution Flow:

1. **User sends request**: "Click the Save button"

2. **Refiner Agent** analyzes and creates plan:
   ```json
   {
     "step": 1,
     "tool": "click_element",
     "instruction": "Find and click the Save button",
     "description": "Vision-guided click on Save button"
   }
   ```

3. **Main Agent** executes step:
   - Calls `click_element("Save button")`
   
4. **Computer Control module** takes over:
   - Captures screenshot → `Desktop/screenshots/screenshot_20231215_143022.png`
   - Sends to Gemini with prompt: "Find the Save button on this screen and return its coordinates"
   
5. **Gemini Vision** analyzes and responds:
   ```json
   {
     "x": 850,
     "y": 600,
     "confidence": 95,
     "description": "Blue 'Save' button in bottom-right corner"
   }
   ```

6. **PyAutoGUI** performs action:
   - Moves mouse to (850, 600) with smooth motion (0.3s)
   - Waits 0.2s
   - Clicks left mouse button

7. **Result returned**: "✓ Found and clicked 'Save button' at (850, 600)"

8. **Judge Agent** validates:
   - Confirms `click_element` tool was actually executed
   - Verifies result matches claimed action
   - Approves response

9. **User receives confirmation**: 
   ```
   "I have clicked the Save button at coordinates (850, 600)."
   ```

### Visual Feedback:

During execution, you'll see:
```
📋 Step 1/1: Vision-guided click on Save button
🤖 Executing: click_element({'element_description': 'Save button', 'clicks': 1, 'button': 'left'})
[Mouse smoothly moves to button]
[Click occurs]
📊 Execution Summary:
   Total steps: 1
   Successful: 1
   Failed: 0
```

## 💰 Cost Analysis (Money No Object)

With your Gemini API key, costs are **extremely low**:

### Per Action Costs:
- **Vision-guided click**: ~$0.00125 (one screenshot analysis)
- **Direct click**: $0 (no vision needed)
- **Type text**: $0 (pure automation)
- **Keyboard shortcuts**: $0 (pure automation)

### Example Task Costs:
- **Fill out web form** (5 steps, 1 vision call): ~$0.00125
- **Navigate Chrome** (10 steps, 3 vision calls): ~$0.00375
- **Complex automation** (50 steps, 20 vision calls): ~$0.025

**100 complex automations per day = $2.50/day = $75/month**

Even with heavy use, you'll spend less than a coffee shop visit per day!

## 🔧 Advanced: Best Gemini Model for Vision

Your current setup uses **Gemini 2.0 Flash Experimental** which is excellent and free.

### Model Upgrade Path (if needed):

```python
# In app/tools/vision_tools.py, line 94:
vision_models = [
    "gemini-2.0-flash-exp",       # Current (free, fast, excellent)
    "gemini-2.0-pro-exp",          # Better reasoning (paid)
    "gemini-2.0-flash-thinking",   # Best for complex planning (paid)
]
```

**Recommendation**: Stick with `gemini-2.0-flash-exp` unless you need:
- More complex spatial reasoning → upgrade to `gemini-2.0-pro-exp`
- Multi-step UI navigation planning → upgrade to `gemini-2.0-flash-thinking`

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY not configured"
**Solution**: Add your Gemini API key to `.env` file.

### Issue: "Could not find element on screen"
**Causes:**
- Element not visible (scrolled off screen)
- Element description too vague
- Window covered by other windows

**Solutions:**
- Be more specific: "Save button in bottom-right" instead of "Save button"
- Ensure window is visible and focused
- Try `describe_screen` first to see what's visible

### Issue: Coordinates out of bounds
**Solution**: Ensure you're clicking on the correct monitor (multi-monitor setups may need adjustment).

### Issue: Agent clicks wrong element
**Solution**: 
- Use more specific descriptions
- Include position hints: "top-right", "bottom panel", "left sidebar"
- Mention colors if distinctive: "red Delete button"

### Issue: Rate limit exceeded
**Solution**: Wait 60 seconds or reduce action frequency.

## 🎓 Pro Tips

### 1. Chain Vision with Actions
```
"Describe what's on screen, then click the most prominent button"
```

### 2. Use Hotkeys for Speed
Keyboard shortcuts are faster and more reliable than clicking:
- `hotkey("ctrl", "s")` instead of clicking File → Save

### 3. Verify Before Acting
```
"Describe the screen, then if you see a Submit button, click it"
```

### 4. Combine with Other Tools
```
"Search the web for 'latest Python version', open the first result, take a screenshot, and create a report"
```

### 5. Specific Descriptions Work Best
- ❌ "Click the button"
- ✅ "Click the blue Submit button in the bottom-right corner"

## 🚀 Future Enhancements (Possible)

- **Multi-monitor support**: Specify which screen to interact with
- **OCR integration**: Read text from screen for verification
- **Recording mode**: Record actions and replay them
- **Visual diff**: Compare before/after screenshots
- **Cursor highlighting**: Show where agent is clicking in real-time
- **Confidence thresholds**: Only act if vision confidence > X%

## 📚 Related Files

- `app/tools/computer_control.py` - Computer control implementation
- `app/tools/vision_tools.py` - Vision/screenshot tools
- `app/tools/tool_catalog.py` - Tool descriptions
- `app/core/agent.py` - Main agent orchestration
- `requirements.txt` - Dependencies

---

**You now have a fully autonomous computer control agent!** 🎉

Try it out with simple commands first, then gradually increase complexity. The agent learns from context and gets better at understanding your patterns.

