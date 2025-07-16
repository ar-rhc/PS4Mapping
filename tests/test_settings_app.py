#!/usr/bin/env python3
"""
Minimal test application to verify settings functionality
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

class TestSettingsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Settings Test App")
        self.root.geometry("600x400")
        
        # Initialize settings
        self.alpha = 0.85
        self.gyro_sensitivity = 500.0
        self.damping_factor = 0.95
        self.polling_rate = 8
        
        # Load settings
        self.load_settings()
        
        # Create UI
        self.create_widgets()
        
        # Update UI from settings
        self.update_ui_from_settings()
        
    def load_settings(self):
        """Load settings from JSON file"""
        default_settings = {
            'alpha': 0.85,
            'gyro_sensitivity': 500.0,
            'damping_factor': 0.95,
            'polling_rate': 8,
        }
        
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    print(f"Loaded settings: {settings}")
                    # Merge with defaults to handle missing keys
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
            else:
                settings = default_settings
                print(f"Settings file not found. Using defaults: {settings}")
        except Exception as e:
            print(f"Error loading settings: {e}. Using defaults.")
            settings = default_settings
        
        # Apply loaded settings
        self.alpha = settings['alpha']
        self.gyro_sensitivity = settings['gyro_sensitivity']
        self.damping_factor = settings['damping_factor']
        self.polling_rate = settings['polling_rate']
        
        print(f"Applied settings: alpha={self.alpha}, sensitivity={self.gyro_sensitivity}, damping={self.damping_factor}, polling={self.polling_rate}")
    
    def create_widgets(self):
        """Create the UI widgets"""
        # Create settings tab
        self.settings_tab = SettingsTab(
            parent_frame=self.root,
            settings_callbacks={
                'update_alpha': self.update_alpha,
                'update_sensitivity': self.update_sensitivity,
                'update_damping': self.update_damping,
                'update_polling': self.update_polling,
                'reset_settings': self.reset_settings,
                'save_settings': self.save_settings,
            }
        )
        
        # Add status label
        self.status_label = tk.Label(self.root, text="Status: Ready", fg="green")
        self.status_label.pack(side=tk.BOTTOM, pady=10)
        
    def update_ui_from_settings(self):
        """Update UI elements to reflect loaded settings"""
        print("Updating UI from settings...")
        self.settings_tab.update_from_settings({
            'alpha': self.alpha,
            'gyro_sensitivity': self.gyro_sensitivity,
            'damping_factor': self.damping_factor,
            'polling_rate': self.polling_rate,
        })
        self.status_label.config(text=f"Settings loaded: α={self.alpha:.2f}, sens={self.gyro_sensitivity:.0f}, damp={self.damping_factor:.2f}, poll={self.polling_rate}ms")
    
    def update_alpha(self, value):
        """Update alpha value"""
        self.alpha = float(value)
        print(f"Alpha updated to: {self.alpha}")
    
    def update_sensitivity(self, value):
        """Update sensitivity value"""
        self.gyro_sensitivity = float(value)
        print(f"Sensitivity updated to: {self.gyro_sensitivity}")
    
    def update_damping(self, value):
        """Update damping value"""
        self.damping_factor = float(value)
        print(f"Damping updated to: {self.damping_factor}")
    
    def update_polling(self, value):
        """Update polling value"""
        self.polling_rate = int(value)
        print(f"Polling updated to: {self.polling_rate}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        print("Resetting settings to defaults...")
        self.alpha = 0.85
        self.gyro_sensitivity = 500.0
        self.damping_factor = 0.95
        self.polling_rate = 8
        self.update_ui_from_settings()
        self.status_label.config(text="Settings reset to defaults", fg="orange")
    
    def save_settings(self):
        """Save current settings"""
        print("Saving settings...")
        settings = {
            'alpha': self.alpha,
            'gyro_sensitivity': self.gyro_sensitivity,
            'damping_factor': self.damping_factor,
            'polling_rate': self.polling_rate,
        }
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"Settings saved to {SETTINGS_FILE}: {settings}")
            self.status_label.config(text=f"Settings saved successfully", fg="green")
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.status_label.config(text=f"Error saving settings: {e}", fg="red")
    
    def run(self):
        """Run the application"""
        print("Starting test application...")
        self.root.mainloop()

if __name__ == "__main__":
    app = TestSettingsApp()
    app.run() 