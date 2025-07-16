#!/usr/bin/env python3
"""
Binary Protocol for DS4 Controller Data
Efficient binary format for UDP transmission
"""

import struct
import time

class DS4BinaryProtocol:
    """Binary protocol for DS4 controller data transmission"""
    
    # Packet format: [header, button_flags_low, button_flags_high, dpad, timestamp_low, timestamp_high, checksum]
    # Total: 8 bytes (vs ~100+ bytes for JSON)
    
    PACKET_HEADER = 0x44  # 'D' for DS4
    PACKET_SIZE = 8
    
    # Button bit mapping (16 buttons = 2 bytes)
    BUTTON_MAPPING = [
        'square', 'cross', 'circle', 'triangle',
        'l1', 'r1', 'l2_pressed', 'r2_pressed',
        'share', 'options', 'l3', 'r3',
        'ps_button', 'touchpad_pressed', 'unused1', 'unused2'
    ]
    
    # D-pad mapping
    DPAD_MAPPING = {
        'none': 0, 'up': 1, 'down': 2, 'left': 3, 'right': 4,
        'ne': 5, 'se': 6, 'sw': 7, 'nw': 8
    }
    
    @classmethod
    def pack_digital_state(cls, buttons, dpad='none'):
        """Pack button and d-pad state into binary format"""
        # Calculate button flags
        button_flags = 0
        for i, button in enumerate(cls.BUTTON_MAPPING):
            if buttons.get(button, False):
                button_flags |= (1 << i)
        
        # Get d-pad value
        dpad_value = cls.DPAD_MAPPING.get(dpad, 0)
        
        # Get timestamp (32-bit)
        timestamp = int(time.time() * 1000)  # Convert to milliseconds
        
        # Pack into 8-byte packet
        packet = struct.pack('<BBBBHH',
            cls.PACKET_HEADER,           # 1 byte: Header
            button_flags & 0xFF,         # 1 byte: Button flags low
            (button_flags >> 8) & 0xFF,  # 1 byte: Button flags high
            dpad_value,                  # 1 byte: D-pad
            timestamp & 0xFFFF,          # 2 bytes: Timestamp low
            (timestamp >> 16) & 0xFFFF,  # 2 bytes: Timestamp high
        )
        
        return packet
    
    @classmethod
    def unpack_digital_state(cls, packet):
        """Unpack binary packet into button and d-pad state"""
        if len(packet) != cls.PACKET_SIZE:
            raise ValueError(f"Invalid packet size: {len(packet)} bytes")
        
        # Unpack packet
        header, button_low, button_high, dpad_value, timestamp_low, timestamp_high = struct.unpack('<BBBBHH', packet)
        
        # Verify header
        if header != cls.PACKET_HEADER:
            raise ValueError(f"Invalid packet header: 0x{header:02X}")
        
        # Reconstruct button flags
        button_flags = button_low + (button_high * 256)
        
        # Unpack buttons
        buttons = {}
        for i, button in enumerate(cls.BUTTON_MAPPING):
            buttons[button] = (button_flags & (1 << i)) != 0
        
        # Unpack d-pad
        dpad_names = list(cls.DPAD_MAPPING.keys())
        dpad = dpad_names[dpad_value] if dpad_value < len(dpad_names) else 'none'
        
        # Reconstruct timestamp
        timestamp = timestamp_low + (timestamp_high * 65536)
        timestamp_seconds = timestamp / 1000.0  # Convert back to seconds
        
        return {
            'buttons': buttons,
            'dpad': dpad,
            'timestamp': timestamp_seconds
        }
    
    @classmethod
    def calculate_packet_size(cls):
        """Calculate packet size for comparison"""
        return cls.PACKET_SIZE
    
    @classmethod
    def get_json_equivalent_size(cls, buttons, dpad):
        """Estimate JSON packet size for comparison"""
        json_data = {
            'buttons': buttons,
            'dpad': dpad,
            'timestamp': time.time()
        }
        import json
        return len(json.dumps(json_data).encode('utf-8'))

# Example usage and testing
if __name__ == "__main__":
    # Test data
    test_buttons = {
        'square': False, 'cross': True, 'circle': False, 'triangle': False,
        'l1': False, 'r1': True, 'l2_pressed': False, 'r2_pressed': False,
        'share': False, 'options': False, 'l3': False, 'r3': False,
        'ps_button': False, 'touchpad_pressed': False
    }
    test_dpad = 'up'
    
    print("🧪 Binary Protocol Test")
    print("="*40)
    
    # Pack data
    packet = DS4BinaryProtocol.pack_digital_state(test_buttons, test_dpad)
    print(f"Binary packet size: {len(packet)} bytes")
    print(f"Binary packet: {packet.hex()}")
    
    # Unpack data
    unpacked = DS4BinaryProtocol.unpack_digital_state(packet)
    print(f"Unpacked data: {unpacked}")
    
    # Size comparison
    json_size = DS4BinaryProtocol.get_json_equivalent_size(test_buttons, test_dpad)
    binary_size = DS4BinaryProtocol.calculate_packet_size()
    
    print(f"\n📊 Size Comparison:")
    print(f"JSON size: {json_size} bytes")
    print(f"Binary size: {binary_size} bytes")
    print(f"Compression: {((json_size - binary_size) / json_size * 100):.1f}%")
    print(f"Size reduction: {json_size / binary_size:.1f}x smaller") 