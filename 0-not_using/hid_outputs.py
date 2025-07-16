#
# hid_test.py - PS4 DualShock 4 Controller HID Report Reader
#
# This script reads raw HID reports from a connected PS4 DualShock 4 controller using the hidapi Python library.
#
# Features:
# - Prints the full HID report as a list of integers for each poll.
# - Decodes and prints the D-pad direction and face button presses (Square, Cross, Circle, Triangle).
# - Decodes shoulder buttons (L1, R1, L2, R2), analog sticks, triggers, Share, Options, L3, R3, PS, Touchpad button.
# - Decodes gyroscope and accelerometer values.
# - Prints basic touchpad info (touch 1 and touch 2 position and ID).
# - Prints battery level and lightbar color (if available).
#
# Usage:
#   1. Make sure you have the 'hid' Python package installed (pip install hid).
#   2. Connect your PS4 controller via USB.
#   3. Run this script: python hid_test.py
#
# Output:
# - Each line shows the current state of the controller as a list of bytes.
# - Human-readable lines indicate D-pad direction, button presses, analog stick positions, trigger values, motion sensors, touchpad info, battery, and lightbar.
#
# You can expand this script to decode more buttons, sensors, or features as needed.
#

import hid
import time
import struct

VENDOR_ID = 1356  # Sony
PRODUCT_ID = 2508 # DualShock 4

h = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
h.nonblocking = True

print("Manufacturer:", h.manufacturer)
print("Product:", h.product)

last_report = None
print("Reading controller actions (press Ctrl+C to stop)...")
try:
    while True:
        report = h.read(64)
        if report and report != last_report:
            print(list(report))
            # Analog sticks
            lx, ly = report[1], report[2]
            rx, ry = report[3], report[4]
            print(f"Left Stick:   X={lx} Y={ly}")
            print(f"Right Stick:  X={rx} Y={ry}")
            # D-pad
            dpad = report[5] & 0x0F
            dpad_map = [
                "Up", "Up/Right", "Right", "Down/Right",
                "Down", "Down/Left", "Left", "Up/Left", "Released"
            ]
            dpad_str = dpad_map[dpad] if dpad < len(dpad_map) else "Unknown"
            print(f"D-pad: {dpad_str}")
            # Face buttons
            if report[5] & 0x10:
                print("Square pressed")
            if report[5] & 0x20:
                print("Cross (X) pressed")
            if report[5] & 0x40:
                print("Circle pressed")
            if report[5] & 0x80:
                print("Triangle pressed")
            # Shoulder buttons, Share, Options, L3, R3
            if report[6] & 0x01:
                print("L1 pressed")
            if report[6] & 0x02:
                print("R1 pressed")
            if report[6] & 0x04:
                print("L2 pressed")
            if report[6] & 0x08:
                print("R2 pressed")
            if report[6] & 0x10:
                print("Share pressed")
            if report[6] & 0x20:
                print("Options pressed")
            if report[6] & 0x40:
                print("L3 pressed")
            if report[6] & 0x80:
                print("R3 pressed")
            # PS and Touchpad buttons
            if report[7] & 0x01:
                print("PS button pressed")
            if report[7] & 0x02:
                print("Touchpad button pressed")
            # Triggers (analog)
            l2_analog = report[8]
            r2_analog = report[9]
            print(f"L2 analog: {l2_analog}")
            print(f"R2 analog: {r2_analog}")
            # Gyroscope (X, Y, Z)
            gyro_x = struct.unpack('<h', bytes(report[13:15]))[0]
            gyro_y = struct.unpack('<h', bytes(report[15:17]))[0]
            gyro_z = struct.unpack('<h', bytes(report[17:19]))[0]
            print(f"Gyro: X={gyro_x} Y={gyro_y} Z={gyro_z}")
            # Accelerometer (X, Y, Z)
            accel_x = struct.unpack('<h', bytes(report[19:21]))[0]
            accel_y = struct.unpack('<h', bytes(report[21:23]))[0]
            accel_z = struct.unpack('<h', bytes(report[23:25]))[0]
            print(f"Accel: X={accel_x} Y={accel_y} Z={accel_z}")
            # Touchpad (first and second touch)
            touchpad_byte = 35
            # Touch 1
            touch1_id = report[touchpad_byte] & 0x7F
            touch1_active = not (report[touchpad_byte] & 0x80)
            touch1_x = ((report[touchpad_byte+2] & 0x0F) << 8) | report[touchpad_byte+1]
            touch1_y = (report[touchpad_byte+3] << 4) | ((report[touchpad_byte+2] & 0xF0) >> 4)
            print(f"Touch 1: id={touch1_id} active={touch1_active} x={touch1_x} y={touch1_y}")
            # Touch 2
            touch2_id = report[touchpad_byte+4] & 0x7F
            touch2_active = not (report[touchpad_byte+4] & 0x80)
            touch2_x = ((report[touchpad_byte+6] & 0x0F) << 8) | report[touchpad_byte+5]
            touch2_y = (report[touchpad_byte+7] << 4) | ((report[touchpad_byte+6] & 0xF0) >> 4)
            print(f"Touch 2: id={touch2_id} active={touch2_active} x={touch2_x} y={touch2_y}")
            # Battery level (try byte 30, may vary)
            battery_level = report[30]
            print(f"Battery level (raw): {battery_level}")
            # Lightbar color (try bytes 32-34, may vary)
            lightbar_r = report[32]
            lightbar_g = report[33]
            lightbar_b = report[34]
            print(f"Lightbar RGB: ({lightbar_r}, {lightbar_g}, {lightbar_b})")
            last_report = report
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    h.close()