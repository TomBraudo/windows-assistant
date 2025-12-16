"""
Visual Click Test - See where clicks actually land.

This creates a GUI with target circles. When you click a target,
it shows:
- Where you intended to click (target)
- Where the click actually registered
- The error distance

Run this to verify DPI fix is working!
"""

import tkinter as tk
from tkinter import ttk
import ctypes
import sys

# ============================================================================
# DPI FIX - MUST BE BEFORE ANY GUI IMPORTS
# ============================================================================
print("Setting DPI awareness...")
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    print("✓ DPI awareness set (Method 1)")
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        print("✓ DPI awareness set (Method 2 - Fallback)")
    except:
        print("❌ Could not set DPI awareness!")

# Now import PyAutoGUI AFTER setting DPI
import pyautogui


class ClickTester(tk.Tk):
    """Visual click testing application."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Visual Click Test - DPI Debug")
        self.geometry("800x600")
        
        # Data storage
        self.targets = []
        self.clicks = []
        self.target_size = 40
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            control_frame,
            text="Create Target",
            command=self.create_target,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Clear All",
            command=self.clear_all,
            bg="#F44336",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Test PyAutoGUI Click",
            command=self.test_pyautogui_click,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(
            control_frame,
            text="Click 'Create Target' then click on canvas",
            font=("Arial", 10)
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Info label
        info_frame = tk.Frame(self)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="This tool tests if mouse clicks land where intended.\n"
                 "1. Click 'Create Target' to place a target circle\n"
                 "2. Try clicking the center of the target\n"
                 "3. Red X shows where click actually landed",
            justify=tk.LEFT,
            font=("Arial", 9),
            bg="#FFFFCC"
        )
        self.info_label.pack(fill=tk.X)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Create initial target
        self.create_target_at(400, 300)
    
    def create_target_at(self, x, y):
        """Create a target circle at specific coordinates."""
        # Outer circle (red)
        outer = self.canvas.create_oval(
            x - self.target_size, y - self.target_size,
            x + self.target_size, y + self.target_size,
            outline="red", width=3, fill=""
        )
        
        # Inner circle (red)
        inner = self.canvas.create_oval(
            x - 10, y - 10,
            x + 10, y + 10,
            outline="red", width=2, fill="red"
        )
        
        # Center cross
        line1 = self.canvas.create_line(
            x - 15, y, x + 15, y,
            fill="black", width=2
        )
        line2 = self.canvas.create_line(
            x, y - 15, x, y + 15,
            fill="black", width=2
        )
        
        # Label
        label = self.canvas.create_text(
            x, y - self.target_size - 10,
            text=f"Target ({x}, {y})",
            font=("Arial", 10, "bold")
        )
        
        self.targets.append({
            "x": x,
            "y": y,
            "elements": [outer, inner, line1, line2, label]
        })
        
        self.status_label.config(text=f"Target created at ({x}, {y})")
    
    def create_target(self):
        """Create a new target at random position."""
        import random
        x = random.randint(100, 700)
        y = random.randint(100, 500)
        self.create_target_at(x, y)
    
    def on_canvas_click(self, event):
        """Handle click on canvas."""
        click_x = event.x
        click_y = event.y
        
        # Draw X where click landed
        size = 10
        x_mark1 = self.canvas.create_line(
            click_x - size, click_y - size,
            click_x + size, click_y + size,
            fill="red", width=3
        )
        x_mark2 = self.canvas.create_line(
            click_x - size, click_y + size,
            click_x + size, click_y - size,
            fill="red", width=3
        )
        
        # Label
        click_label = self.canvas.create_text(
            click_x, click_y + 20,
            text=f"Click ({click_x}, {click_y})",
            font=("Arial", 9),
            fill="red"
        )
        
        self.clicks.append({
            "x": click_x,
            "y": click_y,
            "elements": [x_mark1, x_mark2, click_label]
        })
        
        # Find nearest target and calculate error
        if self.targets:
            nearest = min(
                self.targets,
                key=lambda t: ((t["x"] - click_x)**2 + (t["y"] - click_y)**2)**0.5
            )
            
            distance = ((nearest["x"] - click_x)**2 + (nearest["y"] - click_y)**2)**0.5
            
            # Draw line from target to click
            line = self.canvas.create_line(
                nearest["x"], nearest["y"],
                click_x, click_y,
                fill="blue", width=2, dash=(5, 5)
            )
            
            status = f"Click at ({click_x}, {click_y}) - Error: {distance:.1f} pixels from target"
            
            if distance < 10:
                status += " - ✓ EXCELLENT!"
            elif distance < 20:
                status += " - ✓ Good"
            elif distance < 50:
                status += " - ⚠️  Acceptable"
            else:
                status += " - ❌ BAD (DPI issue?)"
            
            self.status_label.config(text=status)
    
    def test_pyautogui_click(self):
        """Test PyAutoGUI click on first target."""
        if not self.targets:
            self.status_label.config(text="No targets to click!")
            return
        
        target = self.targets[0]
        tx, ty = target["x"], target["y"]
        
        # Get window position
        win_x = self.winfo_rootx()
        win_y = self.winfo_rooty()
        
        # Canvas position
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        
        # Calculate screen coordinates
        screen_x = canvas_x + tx
        screen_y = canvas_y + ty
        
        self.status_label.config(
            text=f"PyAutoGUI clicking at screen ({screen_x}, {screen_y})..."
        )
        
        # Wait a bit
        self.after(1000, lambda: self._execute_pyautogui_click(screen_x, screen_y))
    
    def _execute_pyautogui_click(self, x, y):
        """Execute the PyAutoGUI click."""
        try:
            # Click with PyAutoGUI
            pyautogui.click(x, y)
            self.status_label.config(
                text=f"PyAutoGUI clicked at ({x}, {y}). Check if red X appeared on target!"
            )
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
    
    def clear_all(self):
        """Clear all targets and clicks."""
        for target in self.targets:
            for elem in target["elements"]:
                self.canvas.delete(elem)
        
        for click in self.clicks:
            for elem in click["elements"]:
                self.canvas.delete(elem)
        
        self.targets.clear()
        self.clicks.clear()
        
        self.status_label.config(text="Cleared all")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("VISUAL CLICK TEST")
    print("="*70)
    print("\nThis tool helps verify DPI fix is working:")
    print("1. Targets (red circles) show where to click")
    print("2. Red X marks show where clicks actually land")
    print("3. Blue dashed line shows error distance")
    print("\nIf clicks land on target centers → DPI fix works!")
    print("If clicks are offset → DPI issue still exists")
    print("="*70 + "\n")
    
    app = ClickTester()
    app.mainloop()

