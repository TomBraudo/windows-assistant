"""
Settings panel for API keys and configuration.
"""

import customtkinter as ctk
from typing import Callable, Optional
import os
from dotenv import load_dotenv, set_key


class SettingsPanel(ctk.CTkFrame):
    """
    Settings panel for managing API keys and agent configuration.
    """
    
    def __init__(self, parent, on_save: Optional[Callable] = None):
        super().__init__(parent)
        
        self.on_save = on_save
        self.env_path = ".env"
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Settings",
            font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 20), sticky="w")
        
        # API Keys section
        api_section = ctk.CTkLabel(
            self,
            text="🔑 API Keys",
            font=("Segoe UI", 14, "bold")
        )
        api_section.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        # Groq API Key
        groq_label = ctk.CTkLabel(self, text="Groq API Key:", font=("Segoe UI", 11))
        groq_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.groq_entry = ctk.CTkEntry(
            self, 
            placeholder_text="gsk_...", 
            width=400, 
            show="*",
            font=("Segoe UI", 11),
            height=35
        )
        self.groq_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # OpenRouter API Key
        openrouter_label = ctk.CTkLabel(self, text="OpenRouter API Key:", font=("Segoe UI", 11))
        openrouter_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.openrouter_entry = ctk.CTkEntry(
            self, 
            placeholder_text="sk-or-...", 
            width=400, 
            show="*",
            font=("Segoe UI", 11),
            height=35
        )
        self.openrouter_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # SerpAPI Key
        serpapi_label = ctk.CTkLabel(self, text="SerpAPI Key:", font=("Segoe UI", 11))
        serpapi_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.serpapi_entry = ctk.CTkEntry(
            self, 
            placeholder_text="serpapi key...", 
            width=400, 
            show="*",
            font=("Segoe UI", 11),
            height=35
        )
        self.serpapi_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # Gemini API Key
        gemini_label = ctk.CTkLabel(self, text="Gemini API Key:", font=("Segoe UI", 11))
        gemini_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        
        self.gemini_entry = ctk.CTkEntry(
            self, 
            placeholder_text="gemini key...", 
            width=400, 
            show="*",
            font=("Segoe UI", 11),
            height=35
        )
        self.gemini_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        # Agent Settings section
        agent_section = ctk.CTkLabel(
            self,
            text="🛡️ Agent Settings",
            font=("Segoe UI", 14, "bold")
        )
        agent_section.grid(row=6, column=0, columnspan=2, padx=10, pady=(20, 5), sticky="w")
        
        # Safe Mode toggle
        safemode_label = ctk.CTkLabel(self, text="Safe Mode:", font=("Segoe UI", 11))
        safemode_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        self.safemode_switch = ctk.CTkSwitch(
            self,
            text="Require confirmation for sensitive operations",
            font=("Segoe UI", 11)
        )
        self.safemode_switch.grid(row=7, column=1, padx=10, pady=5, sticky="w")
        self.safemode_switch.select()  # Default on
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        
        self.save_button = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self._on_save_clicked,
            font=("Segoe UI", 12, "bold"),
            height=35,
            fg_color="#4CAF50",
            hover_color="#45A049"
        )
        self.save_button.pack(side="left", padx=5)
        
        self.load_button = ctk.CTkButton(
            button_frame,
            text="📁 Load from .env",
            command=self.load_settings,
            font=("Segoe UI", 12),
            height=35,
            fg_color="#757575",
            hover_color="#616161"
        )
        self.load_button.pack(side="left", padx=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 10)
        )
        self.status_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Load existing settings
        self.load_settings()
    
    def load_settings(self):
        """Load settings from .env file."""
        load_dotenv()
        
        groq_key = os.getenv("GROQ_API_KEY", "")
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        serpapi_key = os.getenv("SERPAPI_API_KEY", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        safe_mode = os.getenv("SAFE_MODE", "True").lower() == "true"
        
        self.groq_entry.delete(0, "end")
        self.groq_entry.insert(0, groq_key)
        
        self.openrouter_entry.delete(0, "end")
        self.openrouter_entry.insert(0, openrouter_key)
        
        self.serpapi_entry.delete(0, "end")
        self.serpapi_entry.insert(0, serpapi_key)
        
        self.gemini_entry.delete(0, "end")
        self.gemini_entry.insert(0, gemini_key)
        
        if safe_mode:
            self.safemode_switch.select()
        else:
            self.safemode_switch.deselect()
        
        self.status_label.configure(text="Settings loaded from .env")
    
    def _on_save_clicked(self):
        """Save settings to .env file."""
        groq_key = self.groq_entry.get().strip()
        openrouter_key = self.openrouter_entry.get().strip()
        serpapi_key = self.serpapi_entry.get().strip()
        gemini_key = self.gemini_entry.get().strip()
        safe_mode = "True" if self.safemode_switch.get() else "False"
        
        # Create .env if it doesn't exist
        if not os.path.exists(self.env_path):
            with open(self.env_path, "w") as f:
                f.write("")
        
        # Update .env file
        if groq_key:
            set_key(self.env_path, "GROQ_API_KEY", groq_key)
        if openrouter_key:
            set_key(self.env_path, "OPENROUTER_API_KEY", openrouter_key)
        if serpapi_key:
            set_key(self.env_path, "SERPAPI_API_KEY", serpapi_key)
        if gemini_key:
            set_key(self.env_path, "GEMINI_API_KEY", gemini_key)
        
        set_key(self.env_path, "SAFE_MODE", safe_mode)
        
        # Reload environment
        load_dotenv(override=True)
        
        self.status_label.configure(text="✓ Settings saved to .env")
        
        if self.on_save:
            self.on_save()

