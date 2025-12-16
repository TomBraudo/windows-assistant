"""
Main application window for Windows Agent GUI.
"""

import customtkinter as ctk
from frontend.components.chat_panel import ChatPanel
from frontend.components.settings_panel import SettingsPanel
from bridge.agent_controller import AgentController


class MainWindow(ctk.CTk):
    """
    Main application window with tabbed interface.
    """
    
    def __init__(self, controller: AgentController):
        super().__init__()
        
        self.controller = controller
        
        # Window configuration
        self.title("Windows Agent")
        self.geometry("1000x750")
        
        # Set appearance - modern dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Add tabs
        self.tabview.add("Chat")
        self.tabview.add("Settings")
        
        # Configure tab grids
        self.tabview.tab("Chat").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Chat").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Settings").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Settings").grid_columnconfigure(0, weight=1)
        
        # Create chat panel
        self.chat_panel = ChatPanel(
            self.tabview.tab("Chat"),
            on_send=self._on_user_message
        )
        self.chat_panel.grid(row=0, column=0, sticky="nsew")
        
        # Create settings panel
        self.settings_panel = SettingsPanel(
            self.tabview.tab("Settings"),
            on_save=self._on_settings_saved
        )
        self.settings_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Welcome message
        self.chat_panel.add_message(
            "🤖 Agent",
            "Windows Agent Online. How can I help you today?\n\nTry commands like:\n• 'Set volume to 50'\n• 'Search for files named test.py'\n• 'Research quantum computing and create a presentation'",
            is_user=False
        )
    
    def _on_user_message(self, message_data: dict):
        """Handle user sending a message (with optional image)."""
        text = message_data.get("text", "")
        image_path = message_data.get("image_path")
        mode = message_data.get("mode", "ask")  # Get mode from message data
        
        # Display user message with image if provided
        display_text = text if text else "[Image only]"
        self.chat_panel.add_message("You", display_text, is_user=True, image_path=image_path)
        
        # Disable input while processing
        self.chat_panel.set_input_enabled(False)
        
        # Set appropriate status based on mode
        if mode == "agent":
            self.chat_panel.set_status("🤖 Agent Mode: Using vision-guided computer control...")
        else:
            self.chat_panel.set_status("💬 Agent is thinking...")
        
        # Process in background (pass text, image, and mode)
        self.controller.process_async(
            user_input=text,
            image_path=image_path,
            mode=mode,
            callback=self._on_agent_response
        )
    
    def _on_agent_response(self, status: str, message: str):
        """Handle agent response callback."""
        # Schedule UI update on main thread
        self.after(0, self._update_ui_with_response, status, message)
    
    def _update_ui_with_response(self, status: str, message: str):
        """Update UI with agent response (runs on main thread)."""
        if status == "complete":
            self.chat_panel.add_message("Agent", message, is_user=False)
            self.chat_panel.set_status("Ready")
            self.chat_panel.set_input_enabled(True)
        
        elif status == "error":
            self.chat_panel.add_message("Agent", f"❌ {message}", is_user=False)
            self.chat_panel.set_status("Error occurred")
            self.chat_panel.set_input_enabled(True)
        
        elif status == "processing":
            self.chat_panel.set_status(message)
    
    def _on_settings_saved(self):
        """Handle settings being saved."""
        # Could reload agent with new settings here if needed
        pass

