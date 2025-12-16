"""
Chat interface component for Windows Agent GUI.
Displays conversation history and handles user input.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from tkinter import filedialog
from PIL import Image, ImageTk
import os


class ChatPanel(ctk.CTkFrame):
    """
    Main chat interface with message history and input box.
    """
    
    def __init__(self, parent, on_send: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__(parent)
        
        self.on_send = on_send
        self.attached_image_path = None  # Store attached image path
        self.image_preview_frame = None  # Preview frame reference
        self.agent_mode = "ask"  # Default mode: "ask" or "agent"
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)  # Message area expands
        self.grid_rowconfigure(1, weight=0)  # Preview area (if image attached)
        self.grid_rowconfigure(2, weight=0)  # Input area fixed
        self.grid_columnconfigure(0, weight=1)
        
        # Message display area (scrollable)
        self.message_frame = ctk.CTkScrollableFrame(
            self,
            label_text="💬 Conversation",
            label_font=("Segoe UI", 14, "bold"),
            fg_color="#1A1A1A"
        )
        self.message_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        
        # Mode selector frame (above input area)
        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mode_frame.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")
        
        mode_label = ctk.CTkLabel(
            self.mode_frame,
            text="Mode:",
            font=("Segoe UI", 11, "bold")
        )
        mode_label.pack(side="left", padx=(5, 10))
        
        # Mode segmented button
        self.mode_selector = ctk.CTkSegmentedButton(
            self.mode_frame,
            values=["Ask", "Agent"],
            command=self._on_mode_changed,
            font=("Segoe UI", 11),
            fg_color="#2B2B2B",
            selected_color="#1E88E5",
            selected_hover_color="#1565C0",
            unselected_color="#424242",
            unselected_hover_color="#616161"
        )
        self.mode_selector.set("Ask")  # Default
        self.mode_selector.pack(side="left", padx=5)
        
        # Mode description
        self.mode_description = ctk.CTkLabel(
            self.mode_frame,
            text="💬 Ask Mode: Use tools and web search (no mouse/keyboard control)",
            font=("Segoe UI", 9),
            text_color="#B0B0B0"
        )
        self.mode_description.pack(side="left", padx=15)
        
        # Input area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        # Image attach button
        self.attach_button = ctk.CTkButton(
            self.input_frame,
            text="📎",
            command=self._on_attach_clicked,
            width=50,
            height=80,
            font=("Segoe UI", 16),
            fg_color="#424242",
            hover_color="#616161"
        )
        self.attach_button.grid(row=0, column=0, padx=(0, 8), pady=5)
        
        # Text input box with modern styling
        self.input_box = ctk.CTkTextbox(
            self.input_frame,
            height=80,
            wrap="word",
            font=("Segoe UI", 11),
            fg_color="#2B2B2B",
            border_width=2,
            border_color="#1E88E5"
        )
        self.input_box.grid(row=0, column=1, padx=(0, 8), pady=5, sticky="ew")
        self.input_box.bind("<Control-Return>", self._on_ctrl_enter)
        self.input_box.bind("<Control-v>", self._on_paste)
        
        # Send button with modern styling
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send ➤",
            command=self._on_send_clicked,
            width=100,
            height=80,
            font=("Segoe UI", 12, "bold"),
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        self.send_button.grid(row=0, column=2, padx=(8, 0), pady=5)
        
        # Status label with better styling
        self.status_label = ctk.CTkLabel(
            self.input_frame,
            text="✓ Ready",
            font=("Segoe UI", 10),
            text_color="#4CAF50"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))
    
    def _on_mode_changed(self, value: str):
        """Handle mode selection change."""
        self.agent_mode = value.lower()  # "ask" or "agent"
        
        if self.agent_mode == "ask":
            self.mode_description.configure(
                text="💬 Ask Mode: Use tools and web search (no mouse/keyboard control)"
            )
        else:  # agent mode
            self.mode_description.configure(
                text="🤖 Agent Mode: Autonomous computer control with vision (mouse/keyboard control)"
            )
    
    def get_mode(self) -> str:
        """Get current agent mode."""
        return self.agent_mode
    
    def _on_attach_clicked(self):
        """Handle attach button click - open file dialog for image."""
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.webp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.attached_image_path = file_path
            self._show_image_preview(file_path)
    
    def _on_paste(self, event):
        """Handle Ctrl+V paste - check for image in clipboard."""
        try:
            from PIL import ImageGrab
            # Try to get image from clipboard
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                # Save temporary image
                temp_dir = os.path.join(os.path.expanduser("~"), "Desktop", "temp_images")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, "pasted_image.png")
                img.save(temp_path)
                self.attached_image_path = temp_path
                self._show_image_preview(temp_path)
                return "break"  # Prevent default paste
        except:
            pass  # If no image in clipboard, allow normal text paste
        return None
    
    def _show_image_preview(self, image_path: str):
        """Show a preview thumbnail of the attached image with remove button."""
        # Remove existing preview if any
        if self.image_preview_frame:
            self.image_preview_frame.destroy()
        
        # Create preview frame
        self.image_preview_frame = ctk.CTkFrame(
            self,
            fg_color="#2B2B2B",
            corner_radius=8
        )
        self.image_preview_frame.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="w")
        
        try:
            # Load and resize image for preview
            img = Image.open(image_path)
            # Create thumbnail (max 100px height)
            max_height = 100
            ratio = max_height / img.height
            new_size = (int(img.width * ratio), max_height)
            img.thumbnail(new_size, Image.Resampling.LANCZOS)
            
            # Convert to CTkImage
            preview_image = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(img.width, img.height)
            )
            
            # Image preview
            image_label = ctk.CTkLabel(
                self.image_preview_frame,
                image=preview_image,
                text=""
            )
            image_label.image = preview_image  # Keep reference
            image_label.pack(side="left", padx=10, pady=10)
            
            # Filename label
            filename = os.path.basename(image_path)
            name_label = ctk.CTkLabel(
                self.image_preview_frame,
                text=filename[:30] + "..." if len(filename) > 30 else filename,
                font=("Segoe UI", 10)
            )
            name_label.pack(side="left", padx=(0, 10))
            
            # Remove button (X)
            remove_button = ctk.CTkButton(
                self.image_preview_frame,
                text="✕",
                width=30,
                height=30,
                font=("Segoe UI", 14, "bold"),
                fg_color="#D32F2F",
                hover_color="#B71C1C",
                command=self._remove_image_preview
            )
            remove_button.pack(side="right", padx=10, pady=10)
            
        except Exception as e:
            # If preview fails, show error message
            error_label = ctk.CTkLabel(
                self.image_preview_frame,
                text=f"Preview error: {str(e)[:50]}",
                font=("Segoe UI", 9),
                text_color="#FF5252"
            )
            error_label.pack(padx=10, pady=10)
    
    def _remove_image_preview(self):
        """Remove the image preview and clear attached image."""
        self.attached_image_path = None
        if self.image_preview_frame:
            self.image_preview_frame.destroy()
            self.image_preview_frame = None
        self.set_status("✓ Ready")
    
    def _on_send_clicked(self):
        """Handle send button click."""
        message = self.input_box.get("1.0", "end-1c").strip()
        if (message or self.attached_image_path) and self.on_send:
            # Create message dict with text, optional image, and mode
            message_data = {
                "text": message,
                "image_path": self.attached_image_path,
                "mode": self.agent_mode  # Include current mode
            }
            
            # Clear the input box, attached image, and preview immediately
            self.input_box.delete("1.0", "end")
            self.attached_image_path = None
            
            # Remove preview frame
            if self.image_preview_frame:
                self.image_preview_frame.destroy()
                self.image_preview_frame = None
            
            # Force UI update
            self.input_box.update()
            
            # Send the message
            self.on_send(message_data)
            
            # Reset status
            self.set_status("✓ Ready")
    
    def _on_ctrl_enter(self, event):
        """Handle Ctrl+Enter keyboard shortcut."""
        self._on_send_clicked()
        return "break"  # Prevent default behavior
    
    def add_message(self, sender: str, text: str, is_user: bool = False, image_path: Optional[str] = None):
        """
        Add a message to the chat display.
        
        Args:
            sender: Name of sender ("You" or "Agent")
            text: Message content
            is_user: True if user message, False if agent
            image_path: Optional path to image to display in message
        """
        # Message container with modern colors
        if is_user:
            bg_color = "#1E88E5"  # Blue for user
            text_color = "#FFFFFF"  # White text
        else:
            bg_color = "#2D2D2D"  # Dark gray for agent
            text_color = "#FFFFFF"  # White text
        
        msg_frame = ctk.CTkFrame(
            self.message_frame,
            fg_color=bg_color,
            corner_radius=12
        )
        msg_frame.pack(fill="x", padx=10, pady=8)
        
        # Sender label
        sender_label = ctk.CTkLabel(
            msg_frame,
            text=sender,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            text_color=text_color
        )
        sender_label.pack(anchor="w", padx=15, pady=(10, 2))
        
        # Display image if provided
        if image_path and os.path.exists(image_path):
            try:
                # Load and resize image
                img = Image.open(image_path)
                # Resize to max width 400px while maintaining aspect ratio
                max_width = 400
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to CTkImage for better HighDPI support
                ctk_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(img.width, img.height)
                )
                
                # Display image
                image_label = ctk.CTkLabel(msg_frame, image=ctk_image, text="")
                image_label.image = ctk_image  # Keep reference to prevent garbage collection
                image_label.pack(anchor="w", padx=15, pady=(5, 5))
            except Exception as e:
                # If image fails to load, show error
                error_label = ctk.CTkLabel(
                    msg_frame,
                    text=f"[Image load error: {str(e)}]",
                    font=("Segoe UI", 9),
                    text_color="#FF5252"
                )
                error_label.pack(anchor="w", padx=15, pady=(5, 5))
        
        # Message text
        if text:
            text_label = ctk.CTkLabel(
                msg_frame,
                text=text,
                font=("Segoe UI", 11),
                anchor="w",
                justify="left",
                wraplength=650,
                text_color=text_color
            )
            text_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Auto-scroll to bottom
        self.message_frame._parent_canvas.yview_moveto(1.0)
    
    def set_status(self, status: str):
        """Update the status label."""
        self.status_label.configure(text=status)
    
    def set_input_enabled(self, enabled: bool):
        """Enable/disable input while agent is processing."""
        if enabled:
            self.send_button.configure(state="normal")
            self.input_box.configure(state="normal")
        else:
            self.send_button.configure(state="disabled")
            self.input_box.configure(state="disabled")

