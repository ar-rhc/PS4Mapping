#!/usr/bin/env python3
"""
Test script to verify settings functionality
"""

import json
import os

# Test settings file
SETTINGS_FILE = "ds4_settings.json"

def test_settings_file():
    """Test if settings file exists and can be read/written"""
    print("Testing settings file functionality...")
    
    # Check if file exists
    if os.path.exists(SETTINGS_FILE):
        print(f"✓ Settings file exists: {SETTINGS_FILE}")
        
        # Try to read it
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            print(f"✓ Settings file can be read: {len(settings)} settings loaded")
            print(f"  Current settings: {settings}")
        except Exception as e:
            print(f"✗ Error reading settings file: {e}")
            return False
    else:
        print(f"✗ Settings file does not exist: {SETTINGS_FILE}")
        return False
    
    # Test writing settings
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
        print("✓ Settings file can be written")
        
        # Read back to verify
        with open(SETTINGS_FILE, 'r') as f:
            read_settings = json.load(f)
        if read_settings == test_settings:
            print("✓ Settings file write/read test passed")
        else:
            print("✗ Settings file write/read test failed")
            return False
            
    except Exception as e:
        print(f"✗ Error writing settings file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_settings_file()
    if success:
        print("\n✓ All settings tests passed!")
    else:
        print("\n✗ Some settings tests failed!") 