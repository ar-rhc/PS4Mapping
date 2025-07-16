#!/usr/bin/env python3
"""
Test main window settings loading
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

class TestMainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
        # Initialize settings
        self.alpha = 0.85
        self.gyro_sensitivity = 500.0
        self.damping_factor = 0.95
        self.polling_rate = 8
        
        # Load settings
        self.load_settings()
        
        # Create settings tab
        self.create_settings_tab()
        
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
    
    def create_settings_tab(self):
        """Create the settings tab"""
        print("Creating settings tab...")
        test_frame = tk.Frame(self.root)
        
        self.settings_tab_modular = SettingsTab(
            parent_frame=test_frame,
            settings_callbacks={
                'update_alpha': self.update_alpha,
                'update_sensitivity': self.update_sensitivity,
                'update_damping': self.update_damping,
                'update_polling': self.update_polling,
                'reset_settings': self.reset_settings,
                'save_settings': self.save_settings,
            }
        )
        print("Settings tab created successfully")
    
    def update_ui_from_settings(self):
        """Update UI elements to reflect loaded settings"""
        print("Updating UI from settings...")
        if hasattr(self, 'settings_tab_modular'):
            print("Settings tab modular found, updating...")
            self.settings_tab_modular.update_from_settings({
                'alpha': self.alpha,
                'gyro_sensitivity': self.gyro_sensitivity,
                'damping_factor': self.damping_factor,
                'polling_rate': self.polling_rate,
            })
            print(f"Settings passed to modular tab: alpha={self.alpha}, sensitivity={self.gyro_sensitivity}, damping={self.damping_factor}, polling={self.polling_rate}")
        else:
            print("Settings tab modular not found!")
    
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
        
        if hasattr(self, 'settings_tab_modular'):
            print("Updating settings tab with reset values...")
            self.settings_tab_modular.update_from_settings({
                'alpha': self.alpha,
                'gyro_sensitivity': self.gyro_sensitivity,
                'damping_factor': self.damping_factor,
                'polling_rate': self.polling_rate,
            })
        else:
            print("Settings tab modular not found during reset!")
    
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
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def test_settings_functionality(self):
        """Test the settings functionality"""
        print("\n=== Testing Settings Functionality ===")
        
        # Test current settings
        current_settings = self.settings_tab_modular.get_current_settings()
        print(f"Current settings from tab: {current_settings}")
        
        # Test reset
        print("\nTesting reset...")
        self.reset_settings()
        
        # Test save
        print("\nTesting save...")
        self.save_settings()
        
        # Test button callbacks
        print("\nTesting button callbacks...")
        self.settings_tab_modular._on_reset_settings()
        self.settings_tab_modular._on_save_settings()
        
        print("\n=== Test Complete ===")
    
    def cleanup(self):
        """Clean up"""
        self.root.destroy()

if __name__ == "__main__":
    print("=== Main Window Settings Test ===")
    
    app = TestMainWindow()
    app.test_settings_functionality()
    app.cleanup()
    
    print("Test completed!") 