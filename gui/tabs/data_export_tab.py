#!/usr/bin/env python3
"""
Data Export Tab Module
Handles DS4 controller data display and export functionality
"""

import tkinter as tk
import time
import numpy as np


class DataExportTab:
    """
    Data export tab for DS4 controller
    Provides data display and export functionality
    """
    
    def __init__(self, parent_frame, export_callbacks=None):
        """
        Initialize the data export tab
        
        Args:
            parent_frame: Parent tkinter frame to pack into
            export_callbacks: Dictionary of callback functions for export operations
        """
        self.parent_frame = parent_frame
        self.export_callbacks = export_callbacks or {}
        
        # Create the tab content
        self.create_widgets()
    
    def create_widgets(self):
        """Create the data export widgets"""
        frame = self.parent_frame
        
        # Data display title
        data_title = tk.Label(frame, text="Controller Data Export", font=("Arial", 12, "bold"))
        data_title.pack(pady=(0, 5))
        
        # Create scrollable text area for data display
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget for data display
        self.data_text = tk.Text(text_frame, height=20, width=50, font=("Courier", 12), 
                                yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.data_text.yview)
        
        # Export buttons
        export_frame = tk.Frame(frame)
        export_frame.pack(pady=5)
        
        export_btn = tk.Button(export_frame, text="Export Text", command=self._on_export_data)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        json_export_btn = tk.Button(export_frame, text="Export JSON", command=self._on_export_json)
        json_export_btn.pack(side=tk.LEFT, padx=5)
    
    def _on_export_data(self):
        """Handle export data button"""
        if 'export_data' in self.export_callbacks:
            self.export_callbacks['export_data']()
    
    def _on_export_json(self):
        """Handle export JSON button"""
        if 'export_json' in self.export_callbacks:
            self.export_callbacks['export_json']()
    
    def update_data_display(self, data, orientation=None, axis_locks=None, polling_rate=8):
        """
        Update the data display with current controller data
        
        Args:
            data: Controller data dictionary
            orientation: Orientation data dictionary
            axis_locks: Axis locks dictionary
            polling_rate: Current polling rate in ms
        """
        if not data:
            return
        
        # Format the display text
        display_text = f"""CONTROLLER DATA EXPORT
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

ANALOG INPUTS:
Left Stick:  X={data.get('left_stick', {}).get('x', 0):6.3f} Y={data.get('left_stick', {}).get('y', 0):6.3f}
Right Stick: X={data.get('right_stick', {}).get('x', 0):6.3f} Y={data.get('right_stick', {}).get('y', 0):6.3f}
L2 Trigger:  {data.get('l2', {}).get('value', 0):6.3f}
R2 Trigger:  {data.get('r2', {}).get('value', 0):6.3f}

DIGITAL INPUTS:
Buttons:     {', '.join([k for k, v in data.get('buttons', {}).items() if v]) or 'None'}
D-pad:       {data.get('dpad', 'none')}
PS Button:   {data.get('ps_button', False)}

SENSORS:
Gyro:        X={data.get('gyro', {}).get('x', 0):8.1f} Y={data.get('gyro', {}).get('y', 0):8.1f} Z={data.get('gyro', {}).get('z', 0):8.1f}
Accelerometer: X={data.get('accelerometer', {}).get('x', 0):8.1f} Y={data.get('accelerometer', {}).get('y', 0):8.1f} Z={data.get('accelerometer', {}).get('z', 0):8.1f}
Touchpad:    X={data.get('touchpad', {}).get('x', 0):6.1f} Y={data.get('touchpad', {}).get('y', 0):6.1f} Active={data.get('touchpad', {}).get('active', False)}

ORIENTATION:"""
        
        if orientation:
            display_text += f"""
Roll:        {orientation.get('roll', 0):8.3f} rad ({np.degrees(orientation.get('roll', 0)):6.1f}°)
Pitch:       {orientation.get('pitch', 0):8.3f} rad ({np.degrees(orientation.get('pitch', 0)):6.1f}°)
Yaw:         {orientation.get('yaw', 0):8.3f} rad ({np.degrees(orientation.get('yaw', 0)):6.1f}°)"""
        
        if axis_locks:
            display_text += f"""

AXIS LOCKS:
Roll:        {axis_locks.get('roll', False)}
Pitch:       {axis_locks.get('pitch', False)}
Yaw:         {axis_locks.get('yaw', False)}"""
        
        display_text += f"""

OTHER:
Battery:     {data.get('battery', 0)}/15
Polling Rate: {polling_rate}ms (~{1000//polling_rate} Hz)
"""
        
        # Update text widget
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(1.0, display_text)
    
    def get_display_text(self):
        """Get the current display text"""
        return self.data_text.get(1.0, tk.END)
    
    def clear_display(self):
        """Clear the data display"""
        self.data_text.delete(1.0, tk.END) 