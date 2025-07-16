#!/usr/bin/env python3
"""
Command-line tool to set the DualShock 4 lightbar color
by sending a command to the main running application.

Usage:
    python3 set_lightbar.py <red> <green> <blue>
    
Example:
    python3 set_lightbar.py 255 0 0  # Sets lightbar to red
"""

import socket
import sys
import json

def send_command(r, g, b, host='127.0.0.1', port=12346):
    """Sends a 'set_lightbar' command via UDP."""
    command = {
        "command": "set_lightbar",
        "r": r,
        "g": g,
        "b": b
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(json.dumps(command).encode('utf-8'), (host, port))
        print(f"✅ Command sent to set lightbar to RGB({r}, {g}, {b})")
    except Exception as e:
        print(f"❌ Error sending command: {e}")
        print("Is the main application (hid_control_ui_hybrid.py) running?")
        sys.exit(1)

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    
    try:
        r = int(sys.argv[1])
        g = int(sys.argv[2])
        b = int(sys.argv[3])
        
        for val, color in [(r, 'Red'), (g, 'Green'), (b, 'Blue')]:
            if not 0 <= val <= 255:
                print(f"❌ Error: {color} value must be between 0 and 255.")
                sys.exit(1)
                
        send_command(r, g, b)
        
    except ValueError:
        print("❌ Error: Color values must be integers between 0 and 255.")
        sys.exit(1)

if __name__ == "__main__":
    main() 