#!/usr/bin/env python3
"""
Test script for LightbarTab class
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the gui directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gui'))

from gui.tabs.lightbar_tab import LightbarTab

def test_lightbar_tab():
    """Test the LightbarTab class independently"""
    
    # Create root window
    root = tk.Tk()
    root.title("LightbarTab Test")
    root.geometry("600x400")
    
    # Create a notebook for the tab
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Create a frame for the lightbar tab
    lightbar_frame = ttk.Frame(notebook)
    notebook.add(lightbar_frame, text="Lightbar")
    
    # Mock HID device (None for testing)
    mock_hid_device = None
    
    # Create the lightbar tab
    try:
        lightbar_tab = LightbarTab(
            parent_frame=lightbar_frame,
            hid_device=mock_hid_device
        )
        print("✓ LightbarTab created successfully")
        
        # Test setting values
        lightbar_tab.set_color_values(255, 0, 0)  # Red
        print("✓ LightbarTab set_color_values called successfully")
        
        # Test getting values
        color_values = lightbar_tab.get_color_values()
        print(f"✓ Color values: {color_values}")
        
    except Exception as e:
        print(f"✗ Error creating LightbarTab: {e}")
        import traceback
        traceback.print_exc()
    
    # Add a test button
    test_button = tk.Button(root, text="Test Lightbar", 
                           command=lambda: print("Test button clicked"))
    test_button.pack(pady=10)
    
    print("LightbarTab test window created. Close the window to exit.")
    root.mainloop()

if __name__ == "__main__":
    test_lightbar_tab() 