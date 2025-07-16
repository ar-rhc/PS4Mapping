#!/usr/bin/env python3
"""
DS4 Controller Data Parser
Handles parsing of HID reports from the DualShock 4 controller
"""

import struct
import time
from typing import Dict, Any, Optional


class DS4DataParser:
    """
    Parser for DualShock 4 controller HID reports
    Handles all data extraction and normalization from raw HID reports
    """
    
    # DS4 D-pad mapping constants
    DPAD_STATES = {
        8: 'none',
        0: 'up',
        1: 'ne',    # north-east (up-right)
        2: 'right', 
        3: 'se',    # south-east (down-right)
        4: 'down',
        5: 'sw',    # south-west (down-left)
        6: 'left',
        7: 'nw'     # north-west (up-left)
    }
    
    def __init__(self):
        """Initialize the data parser"""
        self.previous_digital_state = {
            'buttons': {},
            'dpad': 'none'
        }
    
    def parse_controller_data(self, report: bytes) -> Dict[str, Any]:
        """
        Parse all controller data from HID report
        
        Args:
            report: Raw HID report bytes from the controller
            
        Returns:
            Dictionary containing all parsed controller data
        """
        data = {}
        
        # Analog sticks (normalize to -1 to 1 range)
        data['left_stick'] = {
            'x': (report[1] - 128) / 128,
            'y': (report[2] - 128) / 128,
            'raw_x': report[1],
            'raw_y': report[2]
        }
        data['right_stick'] = {
            'x': (report[3] - 128) / 128,
            'y': (report[4] - 128) / 128,
            'raw_x': report[3],
            'raw_y': report[4]
        }
        
        # Triggers
        data['l2'] = {
            'value': report[8] / 255.0,
            'raw': report[8]
        }
        data['r2'] = {
            'value': report[9] / 255.0,
            'raw': report[9]
        }
        
        # Buttons (byte 5 and 6)
        button_byte1 = report[5]
        button_byte2 = report[6]
        
        data['buttons'] = {
            'square': bool(button_byte1 & 0x10),
            'cross': bool(button_byte1 & 0x20),
            'circle': bool(button_byte1 & 0x40),
            'triangle': bool(button_byte1 & 0x80),
            'l1': bool(button_byte2 & 0x01),
            'r1': bool(button_byte2 & 0x02),
            'l2_pressed': bool(button_byte2 & 0x04),
            'r2_pressed': bool(button_byte2 & 0x08),
            'share': bool(button_byte2 & 0x10),
            'options': bool(button_byte2 & 0x20),
            'l3': bool(button_byte2 & 0x40),
            'r3': bool(button_byte2 & 0x80)
        }
        
        # D-pad (byte 5, bits 0-3)
        dpad = button_byte1 & 0x0F
        data['dpad'] = self.DPAD_STATES.get(dpad, 'none')
        data['dpad_raw'] = dpad  # Add raw value for debugging
        
        # PS button and touchpad (byte 7)
        data['ps_button'] = bool(report[7] & 0x01)
        data['touchpad_pressed'] = bool(report[7] & 0x02)
        
        # Gyro (X, Y, Z)
        data['gyro'] = {
            'x': struct.unpack('<h', bytes(report[13:15]))[0],
            'y': struct.unpack('<h', bytes(report[15:17]))[0],
            'z': struct.unpack('<h', bytes(report[17:19]))[0]
        }
        
        # Accelerometer (X, Y, Z)
        data['accelerometer'] = {
            'x': struct.unpack('<h', bytes(report[19:21]))[0],
            'y': struct.unpack('<h', bytes(report[21:23]))[0],
            'z': struct.unpack('<h', bytes(report[23:25]))[0]
        }
        
        # Touchpad data (if available)
        if len(report) > 35:
            data['touchpad'] = {
                'active': bool(report[35] & 0x80),
                'id': report[35] & 0x7F,
                'x': struct.unpack('<h', bytes(report[36:38]))[0],
                'y': struct.unpack('<h', bytes(report[38:40]))[0]
            }
        else:
            data['touchpad'] = {
                'active': False,
                'id': 0,
                'x': 0,
                'y': 0
            }
        
        # Battery level (if available)
        if len(report) > 30:
            data['battery'] = report[30] & 0x0F
        else:
            data['battery'] = 0
        
        return data
    
    def check_digital_changes(self, new_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check for digital input changes, reporting only on the press event.
        
        Args:
            new_data: Current controller data
            
        Returns:
            Dictionary of changes if any, None if no changes
        """
        changes = {'buttons': {}, 'dpad': None}
        has_changes = False

        # Check for button presses (transition from False to True)
        for button, is_pressed in new_data['buttons'].items():
            was_pressed = self.previous_digital_state['buttons'].get(button, False)
            if is_pressed and not was_pressed:
                changes['buttons'][button] = True
                has_changes = True
        
        # Check for D-pad presses
        current_dpad = new_data.get('dpad', 'none')
        previous_dpad = self.previous_digital_state.get('dpad', 'none')
        if current_dpad != 'none' and current_dpad != previous_dpad:
            changes['dpad'] = current_dpad
            has_changes = True

        # Always update the full state to accurately track releases
        self.previous_digital_state = {
            'buttons': new_data['buttons'].copy(),
            'dpad': new_data['dpad']
        }
        
        return changes if has_changes else None
    
    def get_analog_summary(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get a summary of analog inputs for quick access
        
        Args:
            data: Parsed controller data
            
        Returns:
            Dictionary with analog input summaries
        """
        return {
            'left_stick_x': data['left_stick']['x'],
            'left_stick_y': data['left_stick']['y'],
            'right_stick_x': data['right_stick']['x'],
            'right_stick_y': data['right_stick']['y'],
            'l2_value': data['l2']['value'],
            'r2_value': data['r2']['value']
        }
    
    def get_digital_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of digital inputs for quick access
        
        Args:
            data: Parsed controller data
            
        Returns:
            Dictionary with digital input summaries
        """
        return {
            'buttons': data['buttons'],
            'dpad': data['dpad'],
            'ps_button': data['ps_button'],
            'touchpad_pressed': data['touchpad_pressed']
        }
    
    def get_sensor_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of sensor data for quick access
        
        Args:
            data: Parsed controller data
            
        Returns:
            Dictionary with sensor summaries
        """
        return {
            'gyro': data['gyro'],
            'accelerometer': data['accelerometer'],
            'touchpad': data['touchpad'],
            'battery': data['battery']
        }
    
    def is_button_pressed(self, data: Dict[str, Any], button_name: str) -> bool:
        """
        Check if a specific button is pressed
        
        Args:
            data: Parsed controller data
            button_name: Name of the button to check
            
        Returns:
            True if button is pressed, False otherwise
        """
        return data['buttons'].get(button_name, False)
    
    def is_any_button_pressed(self, data: Dict[str, Any]) -> bool:
        """
        Check if any button is currently pressed
        
        Args:
            data: Parsed controller data
            
        Returns:
            True if any button is pressed, False otherwise
        """
        return any(data['buttons'].values())
    
    def get_pressed_buttons(self, data: Dict[str, Any]) -> list:
        """
        Get a list of currently pressed buttons
        
        Args:
            data: Parsed controller data
            
        Returns:
            List of pressed button names
        """
        return [btn for btn, pressed in data['buttons'].items() if pressed]
    
    def is_dpad_pressed(self, data: Dict[str, Any]) -> bool:
        """
        Check if any d-pad direction is pressed
        
        Args:
            data: Parsed controller data
            
        Returns:
            True if d-pad is pressed, False otherwise
        """
        return data['dpad'] != 'none'
    
    def get_dpad_direction(self, data: Dict[str, Any]) -> str:
        """
        Get the current d-pad direction
        
        Args:
            data: Parsed controller data
            
        Returns:
            D-pad direction string
        """
        return data['dpad']
    
    def reset_digital_state(self):
        """Reset the stored digital state (useful for reconnection)"""
        self.previous_digital_state = {
            'buttons': {},
            'dpad': 'none'
        }
    
    def validate_report(self, report: bytes) -> bool:
        """
        Validate that a HID report has the expected structure
        
        Args:
            report: Raw HID report bytes
            
        Returns:
            True if report is valid, False otherwise
        """
        # DS4 reports should be at least 25 bytes for basic functionality
        if len(report) < 25:
            return False
        
        # Check for expected report structure
        # This is a basic validation - could be enhanced with more specific checks
        return True
    
    def get_report_info(self, report: bytes) -> Dict[str, Any]:
        """
        Get information about the HID report structure
        
        Args:
            report: Raw HID report bytes
            
        Returns:
            Dictionary with report information
        """
        return {
            'length': len(report),
            'is_valid': self.validate_report(report),
            'has_touchpad': len(report) > 35,
            'has_battery': len(report) > 30
        }


# Convenience function for quick parsing
def parse_ds4_report(report: bytes) -> Dict[str, Any]:
    """
    Convenience function to parse a DS4 HID report
    
    Args:
        report: Raw HID report bytes
        
    Returns:
        Parsed controller data
    """
    parser = DS4DataParser()
    return parser.parse_controller_data(report)


# Example usage and testing
if __name__ == "__main__":
    # Create a test parser
    parser = DS4DataParser()
    
    # Example of how to use the parser
    print("DS4 Data Parser initialized")
    print("Use parse_controller_data(report) to parse HID reports")
    print("Use check_digital_changes(data) to detect button changes") 