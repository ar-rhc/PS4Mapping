#!/usr/bin/env python3
"""
DS4 Controller Latency Test
Measures end-to-end latency from button press to key trigger
"""

import hid
import time
import json
import socket
import threading
import statistics
from datetime import datetime
import os

# DS4 Controller IDs
VENDOR_ID = 1356
PRODUCT_ID = 2508

# UDP Configuration
UDP_HOST = '127.0.0.1'
UDP_PORT = 12345

class LatencyTester:
    def __init__(self):
        self.device = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.test_results = []
        self.running = False
        self.test_button = 'cross'  # Test with cross button
        self.press_times = []
        self.release_times = []
        
    def connect_controller(self):
        """Connect to DS4 controller"""
        try:
            self.device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
            print(f"✅ Connected to DS4 Controller")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to DS4: {e}")
            return False
    
    def parse_controller_data(self, report):
        """Parse controller data (simplified version)"""
        # Buttons (byte 5 and 6)
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
        """Measure end-to-end latency"""
        print(f"\n🎮 Starting latency test with '{self.test_button}' button...")
        print("Press the button multiple times to measure latency")
        print("Press Ctrl+C to stop and see results\n")
        
        previous_state = False
        test_count = 0
        
        while self.running and test_count < 50:  # Max 50 tests
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
                    
                    # Detect button release (falling edge)
                    elif not current_state and previous_state:
                        release_time = time.time()
                        self.release_times.append(release_time)
                    
                    previous_state = current_state
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error reading controller: {e}")
                break
        
        self.running = False
    
    def calculate_statistics(self):
        """Calculate latency statistics"""
        if len(self.press_times) < 2:
            print("❌ Not enough data for analysis")
            return
        
        # Calculate intervals between presses (for consistency testing)
        intervals = []
        for i in range(1, len(self.press_times)):
            interval = (self.press_times[i] - self.press_times[i-1]) * 1000  # Convert to ms
            intervals.append(interval)
        
        # Calculate press durations
        durations = []
        for i in range(min(len(self.press_times), len(self.release_times))):
            duration = (self.release_times[i] - self.press_times[i]) * 1000  # Convert to ms
            durations.append(duration)
        
        print("\n" + "="*60)
        print("📊 LATENCY TEST RESULTS")
        print("="*60)
        print(f"Total tests: {len(self.press_times)}")
        print(f"Test button: {self.test_button}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n⏱️  PRESS INTERVALS (ms):")
        print(f"  Min: {min(intervals):.2f}")
        print(f"  Max: {max(intervals):.2f}")
        print(f"  Mean: {statistics.mean(intervals):.2f}")
        print(f"  Median: {statistics.median(intervals):.2f}")
        print(f"  Std Dev: {statistics.stdev(intervals):.2f}")
        
        if durations:
            print(f"\n⏱️  PRESS DURATIONS (ms):")
            print(f"  Min: {min(durations):.2f}")
            print(f"  Max: {max(durations):.2f}")
            print(f"  Mean: {statistics.mean(durations):.2f}")
            print(f"  Median: {statistics.median(durations):.2f}")
        
        # Save results to file
        self.save_results(intervals, durations)
    
    def save_results(self, intervals, durations):
        """Save test results to file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_button': self.test_button,
            'total_tests': len(self.press_times),
            'intervals_ms': intervals,
            'durations_ms': durations,
            'statistics': {
                'intervals': {
                    'min': min(intervals),
                    'max': max(intervals),
                    'mean': statistics.mean(intervals),
                    'median': statistics.median(intervals),
                    'std_dev': statistics.stdev(intervals)
                }
            }
        }
        
        if durations:
            results['statistics']['durations'] = {
                'min': min(durations),
                'max': max(durations),
                'mean': statistics.mean(durations),
                'median': statistics.median(durations)
            }
        
        filename = f"../exports/latency_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
    
    def run_test(self):
        """Run the complete latency test"""
        if not self.connect_controller():
            return
        
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
        if self.device:
            self.device.close()
        self.udp_socket.close()
        print("\n🧹 Cleanup completed")

def main():
    print("🎮 DS4 Controller Latency Test")
    print("="*40)
    print("This test measures:")
    print("- Button press detection time")
    print("- UDP transmission time")
    print("- Overall system responsiveness")
    print("\nMake sure:")
    print("1. DS4 controller is connected")
    print("2. Hammerspoon is running")
    print("3. Controller mappings are configured")
    
    tester = LatencyTester()
    tester.run_test()

if __name__ == "__main__":
    main() 