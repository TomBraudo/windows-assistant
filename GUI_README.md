# Windows Agent - GUI Version

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Launch the GUI and go to the **Settings** tab to enter your API keys:
- Groq API Key (for main agent)
- OpenRouter API Key (for refiner/judge agents)
- SerpAPI Key (for web search and images)

Or edit `.env` file directly:
```
GROQ_API_KEY=your_groq_key
OPENROUTER_API_KEY=your_openrouter_key
SERPAPI_API_KEY=your_serpapi_key
SAFE_MODE=True
```

### 3. Run the GUI
```bash
python main_gui.py
```

## Features

### Chat Interface
- Type commands in natural language
- View conversation history
- Real-time status updates
- Press **Ctrl+Enter** to send messages

### Settings Panel
- Configure API keys securely
- Toggle Safe Mode (confirmation for sensitive operations)
- Save/load settings from .env file

### Backend Integration
- Thread-safe execution (UI stays responsive)
- Full access to all 16 agent tools
- 3-agent pipeline (Refiner → Executor → Judge)

## Project Structure

```
frontend/               # GUI layer
  ├── components/
  │   ├── chat_panel.py      # Chat interface
  │   └── settings_panel.py  # Settings UI
  └── main_window.py         # Main application window

bridge/                 # Frontend ↔ Backend communication
  └── agent_controller.py    # Thread-safe agent wrapper

app/                    # Backend (unchanged)
  ├── core/            # Agent logic
  └── tools/           # Tool implementations

main_gui.py            # GUI entry point
cli.py                 # CLI version (preserved for testing)
```

## Usage Examples

**In the Chat tab, try:**
- "Set volume to 50"
- "Search for files named test.py"
- "Research quantum computing and create a presentation"
- "Open Chrome and go to github.com"
- "Create a note called ideas.txt with content: remember to..."

## Safe Mode

When enabled (default), the agent will ask for confirmation before:
- Creating files or folders
- Launching applications
- Modifying system settings (mouse speed, etc.)

Toggle in Settings → Safe Mode switch.

## CLI Version

The original command-line interface is preserved:
```bash
python cli.py
```

## Next Steps

Future enhancements:
- Screenshot capture + vision analysis
- Execution plan visualization
- System tray integration
- Package as standalone .exe

