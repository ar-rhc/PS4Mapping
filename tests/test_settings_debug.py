#!/usr/bin/env python3
"""
Debug test for settings functionality
"""

import json
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Constants
SETTINGS_FILE = "ds4_settings.json"

def test_settings_loading():
    """Test settings loading logic"""
    print("Testing settings loading logic...")
    
    default_settings = {
        'alpha': 0.85,
        'gyro_sensitivity': 500.0,
        'damping_factor': 0.95,
        'polling_rate': 8,
    }
    
    # Test with no file
    if os.path.exists(SETTINGS_FILE):
        os.remove(SETTINGS_FILE)
        print("Removed existing settings file")
    
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
    alpha = settings['alpha']
    gyro_sensitivity = settings['gyro_sensitivity']
    damping_factor = settings['damping_factor']
    polling_rate = settings['polling_rate']
    
    print(f"Applied settings: alpha={alpha}, sensitivity={gyro_sensitivity}, damping={damping_factor}, polling={polling_rate}")
    
    return settings

def test_settings_saving():
    """Test settings saving logic"""
    print("\nTesting settings saving logic...")
    
    test_settings = {
        'alpha': 0.90,
        'gyro_sensitivity': 600.0,
        'damping_factor': 0.97,
        'polling_rate': 10,
        'test_value': 'test'
    }
    
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(test_settings, f, indent=2)
        print(f"Settings saved to {SETTINGS_FILE}: {test_settings}")
        
        # Read back to verify
        with open(SETTINGS_FILE, 'r') as f:
            read_settings = json.load(f)
        print(f"Read back settings: {read_settings}")
        
        if read_settings == test_settings:
            print("✓ Settings save/load test passed")
        else:
            print("✗ Settings save/load test failed")
            
    except Exception as e:
        print(f"✗ Error saving settings: {e}")

def test_settings_file_exists():
    """Check if settings file exists"""
    print(f"\nChecking if settings file exists: {SETTINGS_FILE}")
    if os.path.exists(SETTINGS_FILE):
        print("✓ Settings file exists")
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            print(f"✓ Settings file can be read: {settings}")
        except Exception as e:
            print(f"✗ Error reading settings file: {e}")
    else:
        print("✗ Settings file does not exist")

if __name__ == "__main__":
    print("=== Settings Debug Test ===")
    
    # Test loading
    settings = test_settings_loading()
    
    # Test saving
    test_settings_saving()
    
    # Check file
    test_settings_file_exists()
    
    print("\n=== Test Complete ===") 