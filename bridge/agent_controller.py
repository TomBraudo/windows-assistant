"""
Thread-safe controller for agent execution.
Allows GUI to call agent without blocking the UI thread.
"""

import threading
from typing import Callable, Optional
from queue import Queue
from dotenv import load_dotenv
import pythoncom  # For COM initialization in threads
from app.core.agent import Agent
from app.tools.registry import ToolRegistry


class AgentController:
    """
    Thread-safe wrapper for the Agent that prevents UI blocking.
    
    Handles:
    - Non-blocking agent execution
    - Status callbacks to UI
    - Thread-safe message passing
    """
    
    def __init__(self, registry: ToolRegistry):
        # Ensure environment variables are loaded
        load_dotenv()
        self.agent = Agent(registry=registry)
        self.is_processing = False
        self._lock = threading.Lock()
    
    def process_async(
        self, 
        user_input: str, 
        image_path: Optional[str] = None,
        mode: str = "ask",
        callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Process user input in a background thread.
        
        Args:
            user_input: The user's message/command
            image_path: Optional path to an image to analyze
            mode: Execution mode - "ask" (standard tools) or "agent" (computer control only)
            callback: Optional callback(status, message) for UI updates
                     status can be: "processing", "complete", "error"
        """
        def _run():
            # Initialize COM for this thread (required for pycaw/Windows audio)
            pythoncom.CoInitialize()
            
            try:
                with self._lock:
                    if self.is_processing:
                        if callback:
                            callback("error", "Agent is already processing a request.")
                        return
                    
                    self.is_processing = True
                
                try:
                    if callback:
                        status_msg = "Agent Mode: Using vision feedback..." if mode == "agent" else "Agent is thinking..."
                        callback("processing", status_msg)
                    
                    # If image is provided, ADD IT TO CONTEXT
                    if image_path:
                        # Format context to clearly indicate attached image
                        if user_input:
                            combined_input = f"[User attached image: {image_path}]\n\nUser request: {user_input}"
                        else:
                            combined_input = f"[User attached image: {image_path}]\n\nUser request: Analyze and describe this image in detail."
                        
                        response = self.agent.process(combined_input, mode=mode)
                    else:
                        # Execute agent with specified mode
                        response = self.agent.process(user_input, mode=mode)
                    
                    if callback:
                        callback("complete", response)
                
                except Exception as e:
                    if callback:
                        callback("error", f"Error: {str(e)}")
                
                finally:
                    with self._lock:
                        self.is_processing = False
            
            finally:
                # Uninitialize COM when thread finishes
                pythoncom.CoUninitialize()
        
        # Start background thread
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    
    def is_busy(self) -> bool:
        """Check if agent is currently processing."""
        with self._lock:
            return self.is_processing

