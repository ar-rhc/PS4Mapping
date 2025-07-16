"""
NOTE: This file is kept for reference but is not currently used in the application.
The mouse control functionality was removed due to performance issues with Hammerspoon integration.
If you want to re-enable mouse control in the future, make sure to address the following:
1. High polling rate causing Hammerspoon slowdown
2. UDP packet flooding from continuous joystick updates
3. Interference with normal controller button mapping

Last active: 2024
"""
import tkinter as tk
from tkinter import ttk

class MouseControlTab(tk.Frame):
    """A tkinter frame for mouse control settings."""
    
    def __init__(self, parent_frame, toggle_callback):
        """
        Initialize the Mouse Control Tab.
        
        Args:
            parent_frame: The parent tkinter frame.
            toggle_callback: A function to call when the enable/disable state changes.
        """
        super().__init__(parent_frame)
        self.toggle_callback = toggle_callback
        
        self.is_enabled = tk.BooleanVar()
        
        self.create_widgets()

    def create_widgets(self):
        """Create and place the widgets for this tab."""
        
        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # --- Toggle Switch ---
        toggle_frame = ttk.LabelFrame(main_frame, text="Mouse Control", padding="10")
        toggle_frame.pack(fill='x', pady=5)
        
        toggle_button = ttk.Checkbutton(
            toggle_frame,
            text="Enable Joystick Mouse Control",
            variable=self.is_enabled,
            command=self._on_toggle,
            style="Switch.TCheckbutton" # For a modern switch-like look
        )
        toggle_button.pack(side='left', padx=5)
        
        # --- Info Label ---
        info_label = ttk.Label(
            main_frame,
            text="When enabled, the left joystick will control the mouse cursor.",
            font=("Arial", 10),
            wraplength=300,
            justify='left'
        )
        info_label.pack(fill='x', pady=10)

    def _on_toggle(self):
        """Callback for when the checkbutton is toggled."""
        if self.toggle_callback:
            self.toggle_callback(self.is_enabled.get())

# To allow testing this tab independently
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Mouse Control Tab Test")
    
    # Style for the switch
    style = ttk.Style(root)
    style.configure("Switch.TCheckbutton", font=("Arial", 12))

    def test_callback(is_enabled):
        print(f"Mouse control enabled: {is_enabled}")

    tab = MouseControlTab(root, test_callback)
    tab.pack(fill='both', expand=True, padx=10, pady=10)
    
    root.mainloop() 