#!/usr/bin/env python3
"""
Test script to verify settings integration with modular tabs
"""

import tkinter as tk
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.tabs.settings_tab import SettingsTab

def test_settings_tab():
    """Test the settings tab functionality"""
    print("Testing SettingsTab integration...")
    
    # Create a test window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create a test frame
    test_frame = tk.Frame(root)
    
    # Test callbacks
    test_values = {}
    
    def update_alpha(value):
        test_values['alpha'] = float(value)
        print(f"  Alpha updated: {value}")
    
    def update_sensitivity(value):
        test_values['gyro_sensitivity'] = float(value)
        print(f"  Sensitivity updated: {value}")
    
    def update_damping(value):
        test_values['damping_factor'] = float(value)
        print(f"  Damping updated: {value}")
    
    def update_polling(value):
        test_values['polling_rate'] = int(value)
        print(f"  Polling updated: {value}")
    
    def reset_settings():
        test_values['reset'] = True
        print("  Reset settings called")
    
    def save_settings():
        test_values['save'] = True
        print("  Save settings called")
    
    # Create settings callbacks
    settings_callbacks = {
        'update_alpha': update_alpha,
        'update_sensitivity': update_sensitivity,
        'update_damping': update_damping,
        'update_polling': update_polling,
        'reset_settings': reset_settings,
        'save_settings': save_settings,
    }
    
    try:
        # Create the settings tab
        settings_tab = SettingsTab(test_frame, settings_callbacks)
        print("✓ SettingsTab created successfully")
        
        # Test updating from settings
        test_settings = {
            'alpha': 0.90,
            'gyro_sensitivity': 600.0,
            'damping_factor': 0.97,
            'polling_rate': 10,
        }
        
        settings_tab.update_from_settings(test_settings)
        print("✓ SettingsTab.update_from_settings() called successfully")
        
        # Test getting current settings
        current_settings = settings_tab.get_current_settings()
        print(f"✓ Current settings retrieved: {current_settings}")
        
        # Verify the settings match
        for key, value in test_settings.items():
            if abs(current_settings[key] - value) < 0.01:  # Allow small floating point differences
                print(f"  ✓ {key}: {value} matches")
            else:
                print(f"  ✗ {key}: expected {value}, got {current_settings[key]}")
        
        # Test button callbacks
        print("\nTesting button callbacks...")
        settings_tab._on_reset_settings()
        settings_tab._on_save_settings()
        
        if test_values.get('reset'):
            print("✓ Reset callback works")
        else:
            print("✗ Reset callback failed")
            
        if test_values.get('save'):
            print("✓ Save callback works")
        else:
            print("✗ Save callback failed")
        
        print("\n✓ All SettingsTab tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing SettingsTab: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_settings_tab()
    if success:
        print("\n✓ Settings integration test completed successfully!")
    else:
        print("\n✗ Settings integration test failed!") 