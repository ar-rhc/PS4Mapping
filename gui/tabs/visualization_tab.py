#!/usr/bin/env python3
"""
Visualization Tab Module
Encapsulates the Live Visualization tab for the DS4 controller UI
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import time
import json
import os

class VisualizationTab:
    def __init__(self, parent_frame, on_export_data=None, on_export_json=None, on_toggle_axis_lock=None, on_set_neutral=None):
        """
        Args:
            parent_frame: The parent tkinter frame to pack widgets into
            on_export_data: Callback for exporting data as text
            on_export_json: Callback for exporting data as JSON
            on_toggle_axis_lock: Callback for toggling axis lock (receives axis name)
            on_set_neutral: Callback for setting neutral orientation
        """
        self.parent_frame = parent_frame
        self.on_export_data = on_export_data
        self.on_export_json = on_export_json
        self.on_toggle_axis_lock = on_toggle_axis_lock
        self.on_set_neutral = on_set_neutral
        
        # Initialize orientation tracking with sensor fusion
        self.orientation = {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        self.orientation_offset = {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        self.last_time = time.time()
        
        # Axis locks
        self.axis_locks = {'roll': False, 'pitch': False, 'yaw': False}
        self.locked_axis = None
        
        # Sensor fusion parameters (will be set by main window)
        self.alpha = 0.95  # Complementary filter alpha
        self.gyro_sensitivity = 500  # Gyro sensitivity
        self.damping_factor = 0.95  # Damping factor
        
        # Store current data for export
        self.current_data = None
        
        # Visualization elements
        self.gyro_triangle = None
        self.lock_indicator = None
        
        self._build_ui()

    def _build_ui(self):
        frame = self.parent_frame
        # Set up matplotlib figure with 3D support
        self.fig = plt.figure(figsize=(10, 4))
        # Analog sticks plot (circular)
        self.ax_stick = self.fig.add_subplot(121)
        self.ax_stick.set_aspect('equal')
        self.ax_stick.set_xlim(-1.2, 1.2)
        self.ax_stick.set_ylim(-1.2, 1.2)
        self.ax_stick.set_title('Analog Sticks & Triggers')
        self.ax_stick.set_xlabel('X')
        self.ax_stick.set_ylabel('Y')
        self.ax_stick.grid(True)
        # Draw circular boundaries for sticks
        circle = Circle((0, 0), 1, fill=False, color='gray', linestyle='--')
        self.ax_stick.add_patch(circle)
        # Stick indicators
        self.stick_left, = self.ax_stick.plot([], [], 'bo', markersize=10, label='Left Stick')
        self.stick_right, = self.ax_stick.plot([], [], 'ro', markersize=10, label='Right Stick')
        self.ax_stick.legend(loc='upper left')
        # Trigger bars on the sides (vertical bars on left and right)
        self.l2_bar = self.ax_stick.bar([-1], [0], width=0.2, color='blue', alpha=0.7, bottom=-1.0)
        self.r2_bar = self.ax_stick.bar([1], [0], width=0.2, color='red', alpha=0.7, bottom=-1.0)
        # 3D Gyro plot
        self.ax_gyro = self.fig.add_subplot(122, projection='3d')
        self.ax_gyro.set_title('Gyroscope (3D)')
        self.ax_gyro.set_xlabel('X')
        self.ax_gyro.set_ylabel('Y')
        self.ax_gyro.set_zlabel('Z')
        self.ax_gyro.set_xlim(-800, 800)
        self.ax_gyro.set_ylim(-800, 800)
        self.ax_gyro.set_zlim(-800, 800)
        self.gyro_triangle = None
        self.ax_gyro.text2D(0.02, 0.98, 'Controller Orientation', transform=self.ax_gyro.transAxes, fontsize=10, verticalalignment='top')
        self.gyro_ball, = self.ax_gyro.plot([0], [0], [0], 'ro', markersize=15, label='Raw Gyro Data')
        self.gyro_text = self.ax_gyro.text2D(0.02, 0.02, 'Gyro: X=0 Y=0 Z=0', transform=self.ax_gyro.transAxes, fontsize=9, verticalalignment='bottom', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        # Axis Locks Section
        lock_frame = tk.Frame(frame)
        lock_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        lock_title = tk.Label(lock_frame, text="Axis Locks:", font=("Arial", 10, "bold"))
        lock_title.pack(side=tk.LEFT, padx=(0, 10))
        self.roll_lock_btn = tk.Button(lock_frame, text="Roll (X)", width=8, command=lambda: self._toggle_axis_lock('roll'))
        self.roll_lock_btn.pack(side=tk.LEFT, padx=2)
        self.pitch_lock_btn = tk.Button(lock_frame, text="Pitch (Y)", width=8, command=lambda: self._toggle_axis_lock('pitch'))
        self.pitch_lock_btn.pack(side=tk.LEFT, padx=2)
        self.yaw_lock_btn = tk.Button(lock_frame, text="Yaw (Z)", width=8, command=lambda: self._toggle_axis_lock('yaw'))
        self.yaw_lock_btn.pack(side=tk.LEFT, padx=2)
        self.lock_status_label = tk.Label(lock_frame, text="No axis locked", fg="green", font=("Arial", 9))
        self.lock_status_label.pack(side=tk.RIGHT, padx=10)
        self.fig.tight_layout()
        # Data display panel
        data_frame = tk.Frame(frame)
        data_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        data_title = tk.Label(data_frame, text="Controller Data Export", font=("Arial", 12, "bold"))
        data_title.pack(pady=(0, 5))
        text_frame = tk.Frame(data_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_text = tk.Text(text_frame, height=20, width=50, font=("Courier", 12), yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.data_text.yview)
        export_frame = tk.Frame(data_frame)
        export_frame.pack(pady=5)
        export_btn = tk.Button(export_frame, text="Export Text", command=self._export_data)
        export_btn.pack(side=tk.LEFT, padx=5)
        json_export_btn = tk.Button(export_frame, text="Export JSON", command=self._export_json)
        json_export_btn.pack(side=tk.LEFT, padx=5)
        # Embed matplotlib in tkinter (left side)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill='both', expand=1)
        # Bind 'c' key to set neutral orientation
        frame.bind_all('<c>', self._set_neutral_orientation)

    def _export_data(self):
        """Export current controller data to text file"""
        try:
            filename = f"../exports/ds4_data_export_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(self.data_text.get(1.0, tk.END))
            print(f"Data exported to {filename}")
        except Exception as e:
            print(f"Error exporting data: {e}")

    def _export_json(self):
        """Export current controller data to JSON file"""
        try:
            if self.current_data is None:
                print("No data available for export")
                return
                
            filename = f"../exports/ds4_data_export_{time.strftime('%Y%m%d_%H%M%S')}.json"
            
            # Prepare data for JSON export
            export_data = {
                'timestamp': self.current_data['timestamp'],
                'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
                'analog_inputs': {
                    'left_stick': self.current_data['left_stick'],
                    'right_stick': self.current_data['right_stick'],
                    'l2_trigger': self.current_data['l2'],
                    'r2_trigger': self.current_data['r2']
                },
                'buttons': self.current_data['buttons'],
                'dpad': self.current_data['dpad'],
                'ps_button': self.current_data['ps_button'],
                'touchpad': self.current_data['touchpad'],
                'sensors': {
                    'raw': {
                        'gyro': self.current_data['gyro'],
                        'accelerometer': self.current_data['accelerometer']
                    },
                    'processed': {
                        'orientation': self.current_data['orientation'],
                        'orientation_degrees': {
                            'roll': np.degrees(self.current_data['orientation']['roll']),
                            'pitch': np.degrees(self.current_data['orientation']['pitch']),
                            'yaw': np.degrees(self.current_data['orientation']['yaw'])
                        }
                    }
                },
                'axis_locks': self.current_data['axis_locks'],
                'battery': self.current_data['battery']
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"JSON data exported to {filename}")
        except Exception as e:
            print(f"Error exporting JSON data: {e}")

    def _toggle_axis_lock(self, axis):
        """Toggle axis lock for the specified axis"""
        if self.axis_locks[axis]:
            # Unlock the axis
            self.axis_locks[axis] = False
            self.locked_axis = None
            self.lock_status_label.config(text="No axis locked", fg="green")
        else:
            # Lock the axis - unlock others first
            for other_axis in self.axis_locks:
                self.axis_locks[other_axis] = False
            self.axis_locks[axis] = True
            self.locked_axis = axis
            self.lock_status_label.config(text=f"{axis.title()} axis locked", fg="red")
        
        # Update button colors
        self._update_lock_button_colors()

    def _update_lock_button_colors(self):
        """Update the colors of lock buttons based on their state"""
        for axis, btn in [('roll', self.roll_lock_btn), ('pitch', self.pitch_lock_btn), ('yaw', self.yaw_lock_btn)]:
            if self.axis_locks[axis]:
                btn.config(bg='red', fg='white')
            else:
                btn.config(bg='SystemButtonFace', fg='black')

    def _set_neutral_orientation(self, event=None):
        """Captures the current orientation to use as the zero-offset."""
        # Store the current angle as the new offset
        self.orientation_offset['roll'] = self.orientation['roll']
        self.orientation_offset['pitch'] = self.orientation['pitch']
        self.orientation_offset['yaw'] = self.orientation['yaw']
        
        # Force immediate visualization update with new offset
        self.update_gyro_triangle(self.orientation['roll'], self.orientation['pitch'], self.orientation['yaw'])
        self.canvas.draw()

    def update_visualizations(self, data):
        """Update matplotlib visualizations with parsed data"""
        # Update analog sticks
        self.stick_left.set_data([data['left_stick']['x']], [data['left_stick']['y']])
        self.stick_right.set_data([data['right_stick']['x']], [data['right_stick']['y']])
        # Update triggers
        self.l2_bar[0].set_height(data['l2']['value'] * 2)
        self.r2_bar[0].set_height(data['r2']['value'] * 2)
        # Update gyro visualization
        gyro = data['gyro']
        accel = data['accelerometer']
        self.gyro_ball.set_data([gyro['x']], [gyro['y']])
        self.gyro_ball.set_3d_properties([gyro['z']])
        self.gyro_text.set_text(f'Gyro: X={gyro["x"]} Y={gyro["y"]} Z={gyro["z"]}\nAccel: X={accel["x"]} Y={accel["y"]} Z={accel["z"]}')
        
        # Update orientation with sensor fusion
        self.update_orientation_with_fusion(gyro['x'], gyro['y'], gyro['z'], 
                                          accel['x'], accel['y'], accel['z'])
        
        self.canvas.draw()

    def update_data_display(self, data):
        """Update the data display text area"""
        # Store current data for export
        self.current_data = data.copy()
        self.current_data['timestamp'] = time.time()
        self.current_data['orientation'] = self.orientation.copy()
        self.current_data['axis_locks'] = self.axis_locks.copy()
        
        # Format data for display
        display_text = f"""=== DS4 Controller Data Export ===
Timestamp: {time.strftime('%H:%M:%S')}

ANALOG INPUTS:
Left Stick:  X={data['left_stick']['x']:6.3f} Y={data['left_stick']['y']:6.3f} (raw: {data['left_stick']['raw_x']:3d}, {data['left_stick']['raw_y']:3d})
Right Stick: X={data['right_stick']['x']:6.3f} Y={data['right_stick']['y']:6.3f} (raw: {data['right_stick']['raw_x']:3d}, {data['right_stick']['raw_y']:3d})
L2 Trigger:  {data['l2']['value']:6.3f} (raw: {data['l2']['raw']:3d})
R2 Trigger:  {data['r2']['value']:6.3f} (raw: {data['r2']['raw']:3d})

BUTTONS:
Square:    {data['buttons']['square']}
Cross:     {data['buttons']['cross']}
Circle:    {data['buttons']['circle']}
Triangle:  {data['buttons']['triangle']}
L1:        {data['buttons']['l1']}
R1:        {data['buttons']['r1']}
L2 Press:  {data['buttons']['l2_pressed']}
R2 Press:  {data['buttons']['r2_pressed']}
Share:     {data['buttons']['share']}
Options:   {data['buttons']['options']}
L3:        {data['buttons']['l3']}
R3:        {data['buttons']['r3']}
PS Button: {data['ps_button']}
D-Pad:     {data['dpad']} (raw: {data['dpad_raw']})

TOUCHPAD:
Active:    {data['touchpad']['active']}
ID:        {data['touchpad']['id']}
Position:  X={data['touchpad']['x']:6d} Y={data['touchpad']['y']:6d}

SENSORS (RAW):
Gyro:      X={data['gyro']['x']:6d} Y={data['gyro']['y']:6d} Z={data['gyro']['z']:6d}
Accel:     X={data['accelerometer']['x']:6d} Y={data['accelerometer']['y']:6d} Z={data['accelerometer']['z']:6d}

SENSORS (PROCESSED):
Roll:      {self.orientation['roll']:8.3f} rad ({np.degrees(self.orientation['roll']):6.1f}°)
Pitch:     {self.orientation['pitch']:8.3f} rad ({np.degrees(self.orientation['pitch']):6.1f}°)
Yaw:       {self.orientation['yaw']:8.3f} rad ({np.degrees(self.orientation['yaw']):6.1f}°)

AXIS LOCKS:
Roll:      {self.axis_locks['roll']}
Pitch:     {self.axis_locks['pitch']}
Yaw:       {self.axis_locks['yaw']}

=== End Data Export ===
"""
        
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(tk.END, display_text)
        self.data_text.see(tk.END)

    def update_orientation_with_fusion(self, gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z, update_triangle=True):
        """Update orientation using complementary filter with gyro and accelerometer data"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Complementary filter parameters - adjustable via GUI
        alpha = self.alpha  # Weighting factor from GUI slider
        
        # Calculate pitch and roll from accelerometer data
        # We use atan2 for a stable calculation in all quadrants
        accel_roll = np.arctan2(accel_y, accel_z)
        accel_pitch = np.arctan2(-accel_x, np.sqrt(accel_y**2 + accel_z**2))
        
        # Convert gyro rates to radians/sec with adjustable sensitivity
        gyro_roll_rate = np.radians(gyro_x / self.gyro_sensitivity)   # X-axis for roll
        gyro_pitch_rate = np.radians(gyro_z / self.gyro_sensitivity)  # Z-axis for pitch
        gyro_yaw_rate = np.radians(gyro_y / self.gyro_sensitivity)    # Y-axis for yaw
        
        # Apply complementary filter with better responsiveness
        # Roll: primarily gyro, corrected by accelerometer (unless locked)
        if not self.axis_locks['roll']:
            self.orientation['roll'] = alpha * (self.orientation['roll'] + gyro_roll_rate * dt) + (1 - alpha) * accel_roll
        
        # Pitch: primarily gyro, corrected by accelerometer (unless locked)
        if not self.axis_locks['pitch']:
            self.orientation['pitch'] = alpha * (self.orientation['pitch'] + gyro_pitch_rate * dt) + (1 - alpha) * accel_pitch
        
        # Yaw: gyro only (accelerometer can't help with yaw) (unless locked)
        if not self.axis_locks['yaw']:
            self.orientation['yaw'] += gyro_yaw_rate * dt
        
        # Add some damping to help return to neutral (only for unlocked axes)
        damping = self.damping_factor
        if abs(gyro_roll_rate) < 0.01 and not self.axis_locks['roll']:  # If no significant movement
            self.orientation['roll'] *= damping
        if abs(gyro_pitch_rate) < 0.01 and not self.axis_locks['pitch']:  # If no significant movement
            self.orientation['pitch'] *= damping
        
        # Update the 3D triangle with fused orientation (only if requested)
        if update_triangle:
            self.update_gyro_triangle(self.orientation['roll'], self.orientation['pitch'], self.orientation['yaw'])

    def update_gyro_triangle(self, roll, pitch, yaw):
        """Update the 3D triangle to show controller orientation, adjusted for a custom offset."""
        # Remove previous triangle if it exists
        if self.gyro_triangle is not None:
            self.gyro_triangle.remove()
        
        # Apply the custom orientation offset
        display_roll = roll - self.orientation_offset['roll']
        display_pitch = pitch - self.orientation_offset['pitch']
        display_yaw = yaw - self.orientation_offset['yaw']
        
        # Create a 30-30-120 degree triangle with depth
        # Base triangle dimensions
        base_width = 500
        depth = 200
        
        # Calculate triangle points for 30-30-120 degree triangle
        # Top point (controller facing direction) at 120 degrees
        # Bottom points at 30 degrees each
        height = base_width * np.tan(np.radians(30))  # Height from base to top
        
        # Front face (controller face)
        front_triangle = np.array([
            [-base_width/2, -height/2, depth/2],   # Bottom left
            [base_width/2, -height/2, depth/2],    # Bottom right
            [0, height/2, depth/2]                 # Top center (controller facing)
        ])
        
        # Back face
        back_triangle = np.array([
            [-base_width/2, -height/2, -depth/2],  # Bottom left
            [base_width/2, -height/2, -depth/2],   # Bottom right
            [0, height/2, -depth/2]                # Top center
        ])
        
        # Apply rotation based on gyro data
        # Apply rotations using the fused orientation angles
        def rotate_point(point, roll, pitch, yaw):
            x, y, z = point
            
            # Yaw rotation (turning left/right)
            if abs(yaw) > 0.001:
                cos_yaw = np.cos(yaw)
                sin_yaw = np.sin(yaw)
                x_new = x * cos_yaw - y * sin_yaw
                y_new = x * sin_yaw + y * cos_yaw
                x, y = x_new, y_new
            
            # Roll rotation (side tilting)
            if abs(roll) > 0.001:
                cos_roll = np.cos(roll)
                sin_roll = np.sin(roll)
                y_new = y * cos_roll - z * sin_roll
                z_new = y * sin_roll + z * cos_roll
                y, z = y_new, z_new
            
            # Pitch rotation (forward/backward tilt)
            if abs(pitch) > 0.001:
                cos_pitch = np.cos(pitch)
                sin_pitch = np.sin(pitch)
                x_new = x * cos_pitch + z * sin_pitch
                z_new = -x * sin_pitch + z * cos_pitch
                x, z = x_new, z_new
            
            return [x, y, z]
        
        # Rotate all points using the offset-adjusted orientation
        rotated_front = np.array([rotate_point(p, display_roll, display_pitch, display_yaw) for p in front_triangle])
        rotated_back = np.array([rotate_point(p, display_roll, display_pitch, display_yaw) for p in back_triangle])
        
        # Create 3D object faces
        faces = []
        
        # Front and back faces
        faces.append(rotated_front)
        faces.append(rotated_back)
        
        # Side faces (connecting front and back)
        faces.append([rotated_front[0], rotated_front[1], rotated_back[1], rotated_back[0]])  # Bottom
        faces.append([rotated_front[1], rotated_front[2], rotated_back[2], rotated_back[1]])  # Right
        faces.append([rotated_front[2], rotated_front[0], rotated_back[0], rotated_back[2]])  # Left
        
        # Create the 3D object
        poly3d = Poly3DCollection(faces, alpha=0.7, facecolor='green', edgecolor='black')
        
        # Add to the plot
        self.gyro_triangle = self.ax_gyro.add_collection3d(poly3d)
        
        # Add red line for locked axis if any
        if self.locked_axis:
            self.add_locked_axis_indicator(display_roll, display_pitch, display_yaw)

    def add_locked_axis_indicator(self, roll, pitch, yaw):
        """Add a red line to show which axis is locked"""
        # Remove previous indicator if it exists
        if self.lock_indicator is not None:
            self.lock_indicator.remove()
        
        # Create a line along the locked axis
        if self.locked_axis == 'roll':
            # Red line along Y-axis (roll axis - side tilting)
            y_line = np.array([[0, -300, 0], [0, 300, 0]])
            self.lock_indicator, = self.ax_gyro.plot(y_line[:, 0], y_line[:, 1], y_line[:, 2], 
                                                   'r-', linewidth=3, alpha=0.8)
        elif self.locked_axis == 'pitch':
            # Red line along X-axis (pitch axis - forward/backward tilt)
            x_line = np.array([[-300, 0, 0], [300, 0, 0]])
            self.lock_indicator, = self.ax_gyro.plot(x_line[:, 0], x_line[:, 1], x_line[:, 2], 
                                                   'r-', linewidth=3, alpha=0.8)
        elif self.locked_axis == 'yaw':
            # Red line along Z-axis (yaw axis - turning left/right)
            z_line = np.array([[0, 0, -300], [0, 0, 300]])
            self.lock_indicator, = self.ax_gyro.plot(z_line[:, 0], z_line[:, 1], z_line[:, 2], 
                                                   'r-', linewidth=3, alpha=0.8)

    def set_sensor_fusion_parameters(self, alpha, gyro_sensitivity, damping_factor):
        """Set the sensor fusion parameters from the main window"""
        self.alpha = alpha
        self.gyro_sensitivity = gyro_sensitivity
        self.damping_factor = damping_factor

    def get_orientation(self):
        """Get the current orientation"""
        return self.orientation.copy()

    def get_axis_locks(self):
        """Return current axis locks state"""
        return self.axis_locks

    def update_from_settings(self, settings):
        """Update visualization tab settings from loaded settings"""
        if 'axis_locks' in settings:
            self.axis_locks = settings['axis_locks']
            # Update UI to reflect loaded settings
            self._update_lock_button_colors()
            if any(self.axis_locks.values()):
                locked = [axis for axis, locked in self.axis_locks.items() if locked]
                self.lock_status_label.config(text=f"{', '.join(locked)} axis locked", fg="red")
            else:
                self.lock_status_label.config(text="No axis locked", fg="green") 