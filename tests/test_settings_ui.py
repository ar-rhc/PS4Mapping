#!/usr/bin/env python3
"""
Test to verify settings UI is being updated correctly
"""

import tkinter as tk
import json
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.tabs.settings_tab import SettingsTab

# Constants
SETTINGS_FILE = "ds4_settings.json"

def test_settings_ui():
    """Test that settings are actually loaded into the UI"""
    print("=== Testing Settings UI ===")
    
    # Create a test window
    root = tk.Tk()
    root.title("Settings UI Test")
    root.geometry("600x400")
    
    # Create a test frame
    test_frame = tk.Frame(root)
    test_frame.pack(fill='both', expand=True)
    
    # Test callbacks
    def update_alpha(value):
        print(f"Alpha callback: {value}")
    
    def update_sensitivity(value):
        print(f"Sensitivity callback: {value}")
    
    def update_damping(value):
        print(f"Damping callback: {value}")
    
    def update_polling(value):
        print(f"Polling callback: {value}")
    
    def reset_settings():
        print("Reset callback called")
    
    def save_settings():
        print("Save callback called")
    
    # Create settings callbacks
    settings_callbacks = {
        'update_alpha': update_alpha,
        'update_sensitivity': update_sensitivity,
        'update_damping': update_damping,
        'update_polling': update_polling,
        'reset_settings': reset_settings,
        'save_settings': save_settings,
    }
    
    # Create the settings tab
    settings_tab = SettingsTab(test_frame, settings_callbacks)
    print("Settings tab created")
    
    # Check initial values
    print("\nInitial slider values:")
    print(f"  Alpha slider: {settings_tab.alpha_slider.get()}")
    print(f"  Sensitivity slider: {settings_tab.sensitivity_slider.get()}")
    print(f"  Damping slider: {settings_tab.damping_slider.get()}")
    print(f"  Polling slider: {settings_tab.polling_slider.get()}")
    
    # Load settings from file
    print("\nLoading settings from file...")
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        print(f"Loaded settings: {settings}")
    else:
        print("Settings file not found")
        settings = {
            'alpha': 0.85,
            'gyro_sensitivity': 500.0,
            'damping_factor': 0.95,
            'polling_rate': 8,
        }
    
    # Update UI with settings
    print("\nUpdating UI with settings...")
    settings_tab.update_from_settings(settings)
    
    # Check updated values
    print("\nUpdated slider values:")
    print(f"  Alpha slider: {settings_tab.alpha_slider.get()}")
    print(f"  Sensitivity slider: {settings_tab.sensitivity_slider.get()}")
    print(f"  Damping slider: {settings_tab.damping_slider.get()}")
    print(f"  Polling slider: {settings_tab.polling_slider.get()}")
    
    # Check labels
    print("\nLabel texts:")
    print(f"  Alpha label: {settings_tab.alpha_label.cget('text')}")
    print(f"  Sensitivity label: {settings_tab.sensitivity_label.cget('text')}")
    print(f"  Damping label: {settings_tab.damping_label.cget('text')}")
    print(f"  Polling label: {settings_tab.polling_label.cget('text')}")
    
    # Add a button to test reset
    def test_reset():
        print("\nTesting reset...")
        settings_tab._on_reset_settings()
        print("Reset callback should have been called")
    
    def test_save():
        print("\nTesting save...")
        settings_tab._on_save_settings()
        print("Save callback should have been called")
    
    # Add test buttons
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=10)
    
    tk.Button(button_frame, text="Test Reset", command=test_reset).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Test Save", command=test_save).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Close", command=root.quit).pack(side=tk.LEFT, padx=5)
    
    print("\nWindow opened. Test the buttons and check the console output.")
    print("The sliders should show the values from the settings file.")
    
    root.mainloop()
    root.destroy()

if __name__ == "__main__":
    test_settings_ui() 