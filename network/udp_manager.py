#!/usr/bin/env python3
"""
UDP Manager Module
Handles UDP communication, packet queuing, and IPC functionality
"""

import socket
import threading
import queue
import time
import json
from typing import Dict, Any, Optional, Tuple


class UDPManager:
    """
    Manages UDP communication for DS4 controller data
    Handles packet queuing, threading, and IPC commands
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 12345, ipc_port: int = 12346):
        """
        Initialize UDP manager
        
        Args:
            host: UDP broadcast host
            port: UDP broadcast port
            ipc_port: IPC listening port
        """
        self.host = host
        self.port = port
        self.ipc_port = ipc_port
        
        # UDP socket for broadcasting
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # IPC socket for receiving commands
        self.ipc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Threading and control
        self.is_running = True
        self.udp_queue = queue.Queue()
        self.udp_thread = None
        
        # Statistics
        self.packets_sent = 0
        self.packets_saved = 0
        
        # Callbacks
        self.toggle_window_callback = None
        self._lightbar_callback = None
        
        print(f"Broadcasting controller data to UDP {self.host}:{self.port}")
        
        # Initialize sockets
        self._setup_sockets()
        
        # Start UDP sender thread
        self._start_udp_thread()
    
    def _setup_sockets(self):
        """Setup UDP and IPC sockets"""
        try:
            # Bind IPC socket for receiving commands
            self.ipc_socket.bind(('127.0.0.1', self.ipc_port))
            self.ipc_socket.setblocking(False)
            print(f"Listening for IPC commands on UDP port {self.ipc_port}")
        except OSError as e:
            print(f"Could not bind to port {self.ipc_port}. Is another instance running?\n\nError: {e}")
            raise
    
    def _start_udp_thread(self):
        """Start the UDP sender thread"""
        self.udp_thread = threading.Thread(target=self._udp_sender_thread, daemon=True)
        self.udp_thread.start()
    
    def _udp_sender_thread(self):
        """Dedicated thread for sending UDP packets with minimal latency"""
        while self.is_running:
            try:
                # Get packet from queue with timeout
                packet = self.udp_queue.get(timeout=0.001)  # 1ms timeout
                if packet:
                    self.udp_socket.sendto(packet, (self.host, self.port))
            except queue.Empty:
                continue  # No packets to send
            except Exception as e:
                print(f"UDP sender thread error: {e}")
                break
    
    def send_packet(self, data: bytes) -> bool:
        """
        Queue a packet for sending
        
        Args:
            data: Packet data to send
            
        Returns:
            True if queued successfully, False otherwise
        """
        try:
            self.udp_queue.put(data)
            return True
        except Exception as e:
            print(f"Error queuing UDP packet: {e}")
            return False
    
    def send_json(self, data: Dict[str, Any]) -> bool:
        """
        Send JSON data as UDP packet
        
        Args:
            data: Dictionary to send as JSON
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = json.dumps(data).encode('utf-8')
            return self.send_packet(message)
        except Exception as e:
            print(f"Error sending JSON data: {e}")
            return False
    
    def send_digital_changes(self, changes: Dict[str, Any]) -> bool:
        """
        Send digital input changes via UDP
        
        Args:
            changes: Dictionary containing button/d-pad changes
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Send individual events for each change, as expected by controller.lua
            for button, pressed in changes.get('buttons', {}).items():
                if pressed:  # Only send event on button press, not release
                    event = {
                        "event_type": "press",
                        "button": button,
                        "timestamp": time.time()
                    }
                    self.send_json(event)

            dpad_direction = changes.get('dpad')
            if dpad_direction and dpad_direction != "none":
                 event = {
                    "event_type": "press",
                    "button": f"dpad_{dpad_direction}",
                    "timestamp": time.time()
                }
                 self.send_json(event)
            
            self.packets_sent += 1
            return True
        except Exception as e:
            print(f"Error sending digital changes: {e}")
            self.packets_saved += 1
            return False
    
    def check_ipc_socket(self):
        """
        Check for incoming UDP commands from Hammerspoon or other scripts.
        Handles both simple string commands and complex JSON commands.
        """
        # print("DEBUG: Checking for IPC socket...") # Add this for very verbose logging
        try:
            data, addr = self.ipc_socket.recvfrom(1024)
            print(f"DEBUG: IPC raw data received: {data}") # See what's coming in
            message = data.decode('utf-8')
            
            # Try to parse as JSON for complex commands
            try:
                command_data = json.loads(message)
                command = command_data.get('command')

                if command == 'set_lightbar' and self._lightbar_callback:
                    r = command_data.get('r', 0)
                    g = command_data.get('g', 0)
                    b = command_data.get('b', 0)
                    self._lightbar_callback(r, g, b)
                    print(f"✅ IPC: Lightbar command executed ({r},{g},{b})")

            # Fallback to simple string command for backward compatibility
            except json.JSONDecodeError:
                if message == 'toggle_window' and self.toggle_window_callback:
                    self.toggle_window_callback()
            
        except BlockingIOError:
            pass  # This is normal, means no data was received
        except Exception as e:
            print(f"IPC Socket Error: {e}")

    def set_toggle_window_callback(self, callback):
        """Set callback for toggle window command"""
        self.toggle_window_callback = callback
    
    def set_lightbar_callback(self, callback):
        """Set callback for set_lightbar command"""
        print(f"DEBUG: Registering lightbar callback: {callback}")
        self._lightbar_callback = callback
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get UDP statistics
        
        Returns:
            Dictionary with UDP statistics
        """
        return {
            'packets_sent': self.packets_sent,
            'packets_saved': self.packets_saved,
            'queue_size': self.udp_queue.qsize(),
            'is_running': self.is_running
        }
    
    def reset_stats(self):
        """Reset UDP statistics"""
        self.packets_sent = 0
        self.packets_saved = 0
        print("📊 UDP statistics reset")
    
    def stop(self):
        """Stop the UDP manager and clean up"""
        print("🛑 Stopping UDP manager...")
        self.is_running = False
        
        # Wait for thread to finish
        if self.udp_thread and self.udp_thread.is_alive():
            self.udp_thread.join(timeout=1.0)
        
        # Close sockets
        try:
            self.udp_socket.close()
            self.ipc_socket.close()
        except Exception as e:
            print(f"Error closing UDP sockets: {e}")
        
        print("🛑 UDP manager stopped")


class UDPPacket:
    """Helper class for creating UDP packets"""
    
    @staticmethod
    def create_controller_packet(controller_data: Dict[str, Any]) -> bytes:
        """
        Create a controller data packet
        
        Args:
            controller_data: Parsed controller data
            
        Returns:
            Packet bytes
        """
        # Create a compact packet with essential data
        packet_data = {
            'timestamp': time.time(),
            'analog': {
                'left_stick': controller_data.get('left_stick', {}),
                'right_stick': controller_data.get('right_stick', {}),
                'l2': controller_data.get('l2', {}),
                'r2': controller_data.get('r2', {})
            },
            'digital': {
                'buttons': controller_data.get('buttons', {}),
                'dpad': controller_data.get('dpad')
            },
            'motion': {
                'gyro': controller_data.get('gyro', {}),
                'accelerometer': controller_data.get('accelerometer', {})
            },
            'orientation': controller_data.get('orientation', {})
        }
        return json.dumps(packet_data).encode('utf-8')
    
    @staticmethod
    def create_digital_packet(changes: Dict[str, Any]) -> bytes:
        """
        Create a compact packet with only digital changes
        
        Args:
            changes: Dictionary with button/d-pad changes
            
        Returns:
            Packet bytes
        """
        packet_data = {
            'timestamp': time.time(),
            'digital': changes
        }
        return json.dumps(packet_data).encode('utf-8')

def create_udp_manager(host: str = '127.0.0.1', port: int = 12345, ipc_port: int = 12346) -> UDPManager:
    """
    Factory function for UDPManager
    
    Args:
        host: UDP broadcast host
        port: UDP broadcast port
        ipc_port: IPC listening port
        
    Returns:
        UDPManager instance
    """
    return UDPManager(host, port, ipc_port) 