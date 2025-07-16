#!/usr/bin/env python3
"""
Advanced DS4 Controller Latency Test
Measures complete end-to-end latency including system key injection
"""

import hid
import time
import json
import socket
import threading
import statistics
import subprocess
from datetime import datetime
import os
import re

# DS4 Controller IDs
VENDOR_ID = 1356
PRODUCT_ID = 2508

# UDP Configuration
UDP_HOST = '127.0.0.1'
UDP_PORT = 12345

class AdvancedLatencyTester:
    def __init__(self):
        self.device = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False
        self.test_button = 'cross'
        self.press_times = []
        self.key_detection_times = []
        self.latencies = []
        
        # For key event detection
        self.key_log_process = None
        self.key_events = []
        
    def connect_controller(self):
        """Connect to DS4 controller"""
        try:
            self.device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
            print(f"✅ Connected to DS4 Controller")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to DS4: {e}")
            return False
    
    def start_key_monitoring(self):
        """Start monitoring for key events using log stream"""
        try:
            # Monitor Console.app for key events
            cmd = [
                'log', 'stream', 
                '--predicate', 'process == "Hammerspoon" AND eventMessage CONTAINS "Controller"',
                '--style', 'compact'
            ]
            
            self.key_log_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_key_events)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            print("✅ Started key event monitoring")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start key monitoring: {e}")
            return False
    
    def monitor_key_events(self):
        """Monitor for key events in log stream"""
        while self.running and self.key_log_process:
            try:
                line = self.key_log_process.stdout.readline()
                if line:
                    # Look for controller key events
                    if "Controller -> Key:" in line:
                        event_time = time.time()
                        self.key_events.append(event_time)
                        print(f"🔑 Key event detected at {event_time:.6f}")
                        
                        # Match with most recent button press
                        if self.press_times:
                            latency = (event_time - self.press_times[-1]) * 1000  # Convert to ms
                            self.latencies.append(latency)
                            print(f"   Latency: {latency:.2f}ms")
                            
            except Exception as e:
                if self.running:
                    print(f"Error monitoring keys: {e}")
                break
    
    def parse_controller_data(self, report):
        """Parse controller data"""
        button_byte1 = report[5]
        button_byte2 = report[6]
        
        buttons = {
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
        
        return buttons
    
    def send_udp_data(self, buttons):
        """Send button data via UDP"""
        data = {
            'buttons': buttons,
            'dpad': 'none',
            'timestamp': time.time()
        }
        message = json.dumps(data).encode('utf-8')
        self.udp_socket.sendto(message, (UDP_HOST, UDP_PORT))
    
    def measure_latency(self):
        """Measure end-to-end latency with key detection"""
        print(f"\n🎮 Starting advanced latency test...")
        print("Press the button multiple times to measure complete latency")
        print("Monitoring for actual key events in system...")
        print("Press Ctrl+C to stop and see results\n")
        
        previous_state = False
        test_count = 0
        
        while self.running and test_count < 30:  # Max 30 tests
            try:
                report = self.device.read(64)
                if report:
                    buttons = self.parse_controller_data(report)
                    current_state = buttons[self.test_button]
                    
                    # Detect button press (rising edge)
                    if current_state and not previous_state:
                        press_time = time.time()
                        self.press_times.append(press_time)
                        
                        # Send UDP data immediately
                        self.send_udp_data(buttons)
                        
                        test_count += 1
                        print(f"Test {test_count}: Button pressed at {press_time:.6f}")
                        
                        # Wait a bit for key event
                        time.sleep(0.1)
                    
                    previous_state = current_state
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error reading controller: {e}")
                break
        
        self.running = False
    
    def calculate_statistics(self):
        """Calculate comprehensive latency statistics"""
        print("\n" + "="*70)
        print("📊 ADVANCED LATENCY TEST RESULTS")
        print("="*70)
        print(f"Total button presses: {len(self.press_times)}")
        print(f"Total key events detected: {len(self.key_events)}")
        print(f"Successful latency measurements: {len(self.latencies)}")
        print(f"Test button: {self.test_button}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.latencies:
            print(f"\n⏱️  END-TO-END LATENCY (ms):")
            print(f"  Min: {min(self.latencies):.2f}")
            print(f"  Max: {max(self.latencies):.2f}")
            print(f"  Mean: {statistics.mean(self.latencies):.2f}")
            print(f"  Median: {statistics.median(self.latencies):.2f}")
            print(f"  Std Dev: {statistics.stdev(self.latencies):.2f}")
            
            # Performance analysis
            print(f"\n📈 PERFORMANCE ANALYSIS:")
            fast_responses = [l for l in self.latencies if l < 10]
            medium_responses = [l for l in self.latencies if 10 <= l < 20]
            slow_responses = [l for l in self.latencies if l >= 20]
            
            print(f"  Fast responses (<10ms): {len(fast_responses)} ({len(fast_responses)/len(self.latencies)*100:.1f}%)")
            print(f"  Medium responses (10-20ms): {len(medium_responses)} ({len(medium_responses)/len(self.latencies)*100:.1f}%)")
            print(f"  Slow responses (≥20ms): {len(slow_responses)} ({len(slow_responses)/len(self.latencies)*100:.1f}%)")
            
            if slow_responses:
                print(f"  ⚠️  Slowest response: {max(self.latencies):.2f}ms")
            
        else:
            print("\n❌ No latency measurements captured")
            print("Possible issues:")
            print("- Hammerspoon not running")
            print("- No controller mappings configured")
            print("- Key events not being logged")
        
        # Save detailed results
        self.save_results()
    
    def save_results(self):
        """Save detailed test results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_button': self.test_button,
            'total_presses': len(self.press_times),
            'total_key_events': len(self.key_events),
            'successful_measurements': len(self.latencies),
            'press_times': self.press_times,
            'key_event_times': self.key_events,
            'latencies_ms': self.latencies,
            'statistics': {}
        }
        
        if self.latencies:
            results['statistics'] = {
                'min': min(self.latencies),
                'max': max(self.latencies),
                'mean': statistics.mean(self.latencies),
                'median': statistics.median(self.latencies),
                'std_dev': statistics.stdev(self.latencies)
            }
        
        filename = f"../exports/advanced_latency_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {filename}")
    
    def run_test(self):
        """Run the complete advanced latency test"""
        if not self.connect_controller():
            return
        
        if not self.start_key_monitoring():
            print("⚠️  Continuing without key monitoring...")
        
        self.running = True
        
        # Start measurement thread
        test_thread = threading.Thread(target=self.measure_latency)
        test_thread.start()
        
        try:
            test_thread.join()
        except KeyboardInterrupt:
            print("\n⏹️  Test interrupted by user")
            self.running = False
        
        self.calculate_statistics()
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        if self.key_log_process:
            self.key_log_process.terminate()
            self.key_log_process.wait()
        
        if self.device:
            self.device.close()
        
        self.udp_socket.close()
        print("\n🧹 Cleanup completed")

def main():
    print("🎮 Advanced DS4 Controller Latency Test")
    print("="*50)
    print("This test measures COMPLETE end-to-end latency:")
    print("- Button press detection")
    print("- UDP transmission")
    print("- Hammerspoon processing")
    print("- System key injection")
    print("- Actual key event detection")
    print("\nRequirements:")
    print("1. DS4 controller connected")
    print("2. Hammerspoon running with controller module")
    print("3. Controller mappings configured")
    print("4. Console.app access for key monitoring")
    
    tester = AdvancedLatencyTester()
    tester.run_test()

if __name__ == "__main__":
    main() 