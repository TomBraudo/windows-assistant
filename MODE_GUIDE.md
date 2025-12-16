# Agent Modes Guide

Your Windows Agent now has **two distinct modes** that you can toggle between:

## 🎯 Modes Overview

### 💬 **Ask Mode** (Default)
- Uses standard tools and web search
- **NO mouse/keyboard control**
- Fast and predictable
- Best for information gathering and file operations

**Available Tools:**
- Web search (SerpAPI)
- File operations (create, search, list)
- Document creation (PowerPoint, Word)
- System controls (volume, mouse speed)
- App launching
- Image search and download
- Vision analysis (analyze images/screenshots)

**Example Commands:**
```
"Search the web for Python tutorials"
"Create a presentation about quantum computing"
"Set volume to 50"
"Find files named test.py"
"Analyze this screenshot and tell me what apps are open"
```

---

### 🤖 **Agent Mode**
- Autonomous computer control with vision feedback
- **ONLY uses mouse/keyboard control**
- Sees the screen and iterates until task complete
- Best for GUI interaction and browser automation

**How It Works:**
1. Agent sees current screen (Gemini Vision)
2. Decides next action (click, type, etc.)
3. Executes action (PyAutoGUI)
4. Observes result on screen
5. Repeats until goal achieved (max 20 iterations)

**Available Tools:**
- `click_element` - Vision-guided clicking
- `click_at_coordinates` - Direct coordinate clicking
- `type_text` - Keyboard text input
- `press_key` - Single key presses
- `hotkey` - Keyboard shortcuts
- `scroll` - Mouse wheel scrolling
- `move_mouse` - Cursor movement
- `describe_screen` - Screen analysis

**Example Commands:**
```
"Open Chrome and search for 'latest video from randalone'"
"Navigate to github.com"
"Click the Submit button in the form"
"Fill out the contact form with my information"
"Open Notepad and write a shopping list"
```

---

## 📱 How to Switch Modes

### In GUI:
1. Look for the **Mode selector** above the text input box
2. Click either **"Ask"** or **"Agent"**
3. The description updates to show which mode is active
4. Send your message - it will use the selected mode

![Mode Toggle Example]
```
[Ask] | [Agent]
💬 Ask Mode: Use tools and web search (no mouse/keyboard control)
```

### In CLI:
Type these commands to switch modes:
```
/ask    - Switch to Ask Mode
/agent  - Switch to Agent Mode
```

The prompt will show current mode:
```
💬 You [ASK]: your message here
🤖 You [AGENT]: your message here
```

---

## 🤔 When to Use Each Mode

### Use **Ask Mode** when:
- ✅ You need information from the web
- ✅ You want to create documents/presentations
- ✅ You need file operations
- ✅ You want fast, predictable results
- ✅ You're analyzing images/screenshots (without interaction)
- ✅ You want system controls (volume, etc.)

### Use **Agent Mode** when:
- ✅ You need to interact with Chrome/browser
- ✅ You want to click buttons or fill forms
- ✅ You need to navigate GUI applications
- ✅ You want autonomous task completion
- ✅ The task requires seeing the screen state
- ✅ You need to type into applications

---

## 💡 Important Differences

| Feature | Ask Mode | Agent Mode |
|---------|----------|------------|
| **Speed** | Fast (direct tool calls) | Slower (iterative vision loop) |
| **Web Search** | ✅ Uses SerpAPI | ❌ Only browser interaction |
| **Mouse Control** | ❌ No | ✅ Yes |
| **Keyboard Control** | ❌ No | ✅ Yes |
| **Vision Feedback** | Only for analysis | ✅ Continuous loop |
| **Max Iterations** | N/A (single execution plan) | 20 iterations |
| **Cost per Request** | ~$0 (free tier APIs) | ~$0.025 (Gemini Vision calls) |
| **Predictability** | High | Medium (depends on screen state) |

---

## 🔄 Example: Same Task, Different Modes

### Task: "Search for latest video from randalone"

**Ask Mode Execution:**
```
Step 1: web_search("latest video from randalone")
  → Returns: "Based on web search results..."
Done in 2 seconds
```

**Agent Mode Execution:**
```
Iteration 1: describe_screen()
  → "Desktop with taskbar visible"

Iteration 2: click_element("Chrome icon on taskbar")
  → Chrome opens

Iteration 3: click_element("address bar at top")
  → Address bar focused

Iteration 4: type_text("youtube.com/randalone", press_enter=True)
  → Navigates to channel

Iteration 5: describe_screen()
  → "YouTube channel page with latest videos"
  
Done in 15-20 seconds
```

**When to use which:**
- **Ask Mode**: Faster, just get information about latest video
- **Agent Mode**: When you want to actually navigate to the page and interact with it

---

## 🚨 Common Mistakes

### ❌ Wrong: Using Agent Mode for simple queries
```
Mode: Agent
Input: "What is the weather today?"
```
**Problem**: Agent Mode will try to control your computer to find weather, which is unnecessary.

**Solution**: Use Ask Mode
```
Mode: Ask
Input: "Search the web for today's weather"
```

---

### ❌ Wrong: Using Ask Mode for browser interaction
```
Mode: Ask
Input: "Open Chrome and go to github.com"
```
**Problem**: Ask Mode will use `launch_app` and `open_url` but won't actually navigate with computer control.

**Solution**: Use Agent Mode
```
Mode: Agent
Input: "Open Chrome and go to github.com"
```

---

## 🎓 Pro Tips

### 1. Start with Ask Mode
Default to Ask Mode for most tasks. Only switch to Agent Mode when you specifically need GUI interaction.

### 2. Be Specific in Agent Mode
```
❌ "Click the button"
✅ "Click the Submit button in the bottom-right corner"
```

### 3. Combine Modes
Switch between modes as needed:
```
Ask Mode: "Search for the best Python IDE"
→ Get information

Agent Mode: "Open Chrome and download VS Code from the first result"
→ Perform the download
```

### 4. Check What's Happening
In Agent Mode, watch your screen - you'll see the mouse moving and typing in real-time!

### 5. Emergency Stop
If Agent Mode goes wrong:
- **Move mouse to top-left corner** (PyAutoGUI failsafe)
- **Press Ctrl+C** in terminal/CLI

---

## 📊 Performance Comparison

**Simple Web Search:**
- Ask Mode: **2 seconds** ⚡
- Agent Mode: **15-20 seconds** 🐢

**Navigate to Website:**
- Ask Mode: Opens in browser but **no control** ❌
- Agent Mode: **Full navigation** with vision ✅

**Create Document:**
- Ask Mode: **Instant** (direct tool) ✅
- Agent Mode: **Not available** (no document tools) ❌

**Fill Web Form:**
- Ask Mode: **Not available** ❌
- Agent Mode: **Vision-guided form filling** ✅

---

## 🔧 Technical Details

### Ask Mode Architecture:
```
User Request
    ↓
Refiner Agent (creates execution plan)
    ↓
Main Agent (executes tools sequentially)
    ↓
Judge Agent (validates results)
    ↓
Response to User
```

### Agent Mode Architecture:
```
User Request
    ↓
Autonomous Agent (loop up to 20 iterations):
  1. Capture screenshot
  2. Analyze with Gemini Vision
  3. Decide next action
  4. Execute action (mouse/keyboard)
  5. Check if complete
  6. Repeat
    ↓
Response to User
```

---

## 🎯 Summary

- **Ask Mode** = Information gathering, file operations, document creation (fast, no computer control)
- **Agent Mode** = GUI automation, browser interaction, form filling (slower, full computer control)

Toggle between them freely based on your task!

---

**For detailed computer control information, see:** `COMPUTER_CONTROL_GUIDE.md`

**For quick start:** `QUICKSTART_COMPUTER_CONTROL.txt`

