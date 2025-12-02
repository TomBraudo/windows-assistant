import json
import os
import platform
from typing import List, Dict, Any, Optional
from .llm import LLMClient
from app.tools.registry import ToolRegistry
from app.tools.os_ops import get_desktop_path # <--- Import the helper

class Agent:
    def __init__(self, registry: ToolRegistry, model: str = "groq/llama-3.3-70b-versatile"):
        self.llm = LLMClient(model)
        self.registry = registry
        self.history: List[Dict[str, Any]] = []
        
        # --- Context Injection ---
        user = os.getlogin()
        cwd = os.getcwd()
        # Use the robust helper to find the REAL desktop (OneDrive aware)
        desktop = get_desktop_path()
        
        # --- IMPROVED SYSTEM PROMPT ---
        self.system_prompt = f"""You are a Windows Automation Agent running on {platform.system()}.
        
        SYSTEM CONTEXT:
        - Current User: {user}
        - Working Directory: {cwd}
        - Real Desktop Path: {desktop}
        
        CRITICAL INSTRUCTIONS:
        1. **ACT, DON'T TEACH**: Do NOT explain how to perform a task with Python code. Do NOT show code snippets.
        2. **USE TOOLS**: If a tool exists for the user's request, call it immediately.
        3. **CONFIRMATION**: After running a tool, simply state what was done (e.g., "I have created the file at [path].").
        4. **DEFAULT PATHS**: If the user asks for the "Desktop" or doesn't specify a folder, ALWAYS use the 'Real Desktop Path' provided above.
        5. **SMART FILE / APP OPENING**:
           - When the user wants to open or launch something (e.g. "open X", "launch X", "run X"):
             *If X looks like a concrete filename or path* (has an extension like ".py", ".txt", ".exe"
             or contains a slash/backslash, or is written like "@test_find_files.py"), you MAY call
             'smart_search_and_open' directly with that exact string.
           - If the user only gives a bare name with no extension (e.g. "hearthstone", "fortnite", "battlenet",
             "whatsapp"), you MUST NOT call 'smart_search_and_open' directly with that bare name.
             Instead, first resolve what they most likely meant.
        6. **AMBIGUOUS OR UNCERTAIN REQUESTS (MANDATORY FLOW)**:
           - For bare or ambiguous names without an extension, you MUST do the following in order:
             1) Reason about what the user likely means (e.g. game launcher, desktop app, etc.).
             2) Call the 'web_search' tool to look up the correct Windows application and its typical
                executable / launcher name (for example, mapping "battlenet" to "Battle.net.exe",
                or "whatsapp" to the correct Windows app/launcher name).
             3) From the web search results, explicitly choose ONE concrete filename (including extension),
                and then call 'smart_search_and_open' with that concrete filename so it can locate and open
                the correct file.
           - Do NOT brute-force or guess multiple exe names yourself when the request is ambiguous; always
             use 'web_search' first to refine the request into a specific filename, then perform file search
             and launch using that filename.
        """

    def process(self, user_input: str) -> str:
        """Main loop: Listen -> Think -> Act -> Reply"""
        
        # 1. Add User Input to History
        self.history.append({"role": "user", "content": user_input})
        
        # 2. First Call: Ask LLM (with Tools)
        response = self.llm.complete(
            messages=[{"role": "system", "content": self.system_prompt}] + self.history,
            tools=self.registry.get_tool_schema(),
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        
        # 3. Check for Tool Calls
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            self.history.append(msg)
            
            # Execute all requested tools
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                print(f"🤖 Agent executing: {func_name}({args})")
                
                try:
                    # EXECUTE via Registry
                    result = self.registry.execute(func_name, **args)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Error: {str(e)}"

                # Add result to history
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result_str
                })

            # 4. Second Call: Get Final Response based on tool results
            final_response = self.llm.complete(
                messages=[{"role": "system", "content": self.system_prompt}] + self.history
            )
            final_text = final_response.choices[0].message.content
            self.history.append({"role": "assistant", "content": final_text})
            return final_text
        
        else:
            # No tools needed, just return text
            text = msg.content
            self.history.append({"role": "assistant", "content": text})
            return text