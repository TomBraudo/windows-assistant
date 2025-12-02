# Implementation Master Plan: Autonomous Windows Control Agent

This implementation plan transforms the architectural research into a
concrete, executed project. It focuses on the **"Custom Loop"**
approach, which offers maximum customizability for an experimental
project without the bloat of enterprise frameworks.

------------------------------------------------------------------------

## 1. Project Scope & Philosophy

**Goal:**\
Construct a local Python-based agent that translates natural language
voice/text commands into OS-level actions (Volume, Brightness, Files)
using remote "Free/Cheap" LLMs.

**Status:**\
Experimental / Prototype.

**Core Architecture:**\
- **Brain:** External API (Groq Llama 3.3 or Google Gemini 2.0 Flash).\
- **Hands:** Local Python libraries (`pycaw`, `pywin32`,
`screen_brightness_control`).\
- **Nerves:** `LiteLLM` for unified API handling.

------------------------------------------------------------------------

## Phase 1: Infrastructure & Accounts

Before touching the command line, secure your "cognitive compute"
resources.

### 1.1 API Procurement

Since you cannot run a 70B model locally, you will act as a client to
remote providers.

1.  **Primary Provider (Speed & Free Tier): Groq Cloud**
    -   *Target Model:* Llama 3.3 70B\
    -   *Reason:* Ultra-low latency and a generous free tier.
2.  **Secondary Provider (Context & Logic): Google AI Studio**
    -   *Target Model:* Gemini 2.0 Flash\
    -   *Reason:* Huge free context (1M tokens) and high RPM quota.
3.  **Fallback/Paid Provider: DeepSeek or OpenRouter**
    -   *Target Model:* DeepSeek-V3\
    -   *Reason:* Cheapest paid fallback (\~\$0.14/M tokens). Load \$5
        as buffer.

### 1.2 Development Tooling

1.  **Python Interpreter**\
    Install Python 3.10+ with "Add to PATH".

2.  **C++ Build Tools**\
    Install Microsoft Visual C++ Build Tools → "Desktop development with
    C++".

3.  **Terminal**\
    Use PowerShell or Windows Terminal.

------------------------------------------------------------------------

## Phase 2: Environment Configuration

### 2.1 Virtual Environment (Venv)

Create a dedicated Python virtual environment to avoid dependency
conflicts.

### 2.2 Dependency Strategy

Install libraries in categories:

#### **Group A: The Brain**

-   `litellm`
-   `python-dotenv`

#### **Group B: The Hands**

-   `pycaw`
-   `comtypes`
-   `screen_brightness_control`
-   `pywin32`

#### **Group C: Voice**

-   `SpeechRecognition`
-   `pyaudio`
-   `edge-tts`

------------------------------------------------------------------------

## Phase 3: The "Safe Mode" Architecture

### 3.1 Allow-list Protocol

Do *not* give the agent arbitrary shell access.\
Define **atomic allowed functions** only: - Allowed: `set_volume`,
`get_brightness`, `launch_app` - Banned: `cmd.exe`, `powershell.exe`,
`delete_file`, etc.

### 3.2 Human-in-the-Loop Switch

For sensitive tools: - Pause for confirmation:\
*"Agent wants to X. Proceed? (Y/N)"* - Add a `SAFE_MODE=True/False`
flag.

------------------------------------------------------------------------

## Phase 4: Implementation Workflow

### Step 1: Connection Test

Test Groq/Llama 3.3 via `LiteLLM`:\
- Load keys\
- Send "Hello"\
- Expect \<1s latency

### Step 2: Tool Construction (Hands)

Build isolated tools first:

#### **Audio Tool**

Uses `pycaw` to set system volume.

#### **Brightness Tool**

Uses `screen_brightness_control` with graceful error handling.

#### **App Launcher**

Map app names → executable paths with `subprocess`.

### Step 3: Reasoning Loop (Brain)

Write your own lightweight tool-calling loop:

1.  System prompt\
2.  JSON tool schema\
3.  Loop:
    -   Listen\
    -   Think (LLM call)\
    -   Detect tool call\
    -   Execute function\
    -   Send result back for final wording

### Step 4: Voice Interface

#### **STT Input:**

Use `SpeechRecognition` + Groq Whisper.

#### **TTS Output:**

Use `edge-tts`, save temp audio file, play, delete.

------------------------------------------------------------------------

## Phase 5: Testing & Refinement

### 5.1 Latency Tuning

-   Pre-load libraries\
-   Trim long history (\>10--20 turns)

### 5.2 Error Handling

-   Catch hallucinated tool names\
-   Handle Admin-permission failures (run terminal as Administrator)

------------------------------------------------------------------------

## Summary Checklist

-   [ ] **Keys:** Groq (Primary), Gemini (Context), DeepSeek (Backup)\
-   [ ] **Install:** Python, C++ Tools, `litellm`, `pycaw`, `pywin32`,
    `screen_brightness_control`\
-   [ ] **Safety:** Define allow-list of functions\
-   [ ] **Build:** Tools → Loop → Voice\
-   [ ] **Run:** Launch via Admin terminal
