#!/usr/bin/env python3
"""
Lightbar Tab Module
Handles DS4 controller lightbar color control
"""

import tkinter as tk
from controller.hid_controller import set_lightbar_and_rumble


class LightbarTab:
    """
    Lightbar control tab for DS4 controller
    Provides RGB sliders to control the controller's lightbar color
    """
    
    def __init__(self, parent_frame, hid_device, save_settings_callback=None):
        """
        Initialize the lightbar tab
        
        Args:
            parent_frame: Parent tkinter frame to pack into
            hid_device: HID device handle for sending commands
            save_settings_callback: Callback to trigger main save function
        """
        self.parent_frame = parent_frame
        self.hid_device = hid_device
        self.save_settings_callback = save_settings_callback
        
        # Create the tab content
        self.create_widgets()
    
    def create_widgets(self):
        """Create the lightbar control widgets"""
        frame = self.parent_frame
        
        # Red channel control
        tk.Label(frame, text="Red").pack()
        self.red = tk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.set_lightbar_on_drag)
        self.red.pack(fill='x')
        
        # Green channel control
        tk.Label(frame, text="Green").pack()
        self.green = tk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.set_lightbar_on_drag)
        self.green.pack(fill='x')
        
        # Blue channel control
        tk.Label(frame, text="Blue").pack()
        self.blue = tk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.set_lightbar_on_drag)
        self.blue.pack(fill='x')
        
        # Save button
        save_btn = tk.Button(frame, text="Save Lightbar Color", command=self.save_lightbar_setting)
        save_btn.pack(pady=10)

    def set_lightbar_on_drag(self, value):
        """Sets the lightbar color live as the user drags the slider."""
        self.set_lightbar()
    
    def save_lightbar_setting(self):
        """Saves the current lightbar color to the settings file."""
        self.set_lightbar() # Ensure current color is set
        if self.save_settings_callback:
            self.save_settings_callback()
            print("Lightbar settings saved.")
        else:
            print("ERROR: Save settings callback not available.")

    def set_lightbar(self):
        """Set the lightbar color using current slider values"""
        r = self.red.get()
        g = self.green.get()
        b = self.blue.get()
        set_lightbar_and_rumble(self.hid_device, r, g, b)
    
    def set_lightbar_color(self, r, g, b):
        """Sets the lightbar color from external call and updates UI."""
        self.red.set(r)
        self.green.set(g)
        self.blue.set(b)
        self.set_lightbar()

    def get_color_settings(self):
        """Get current color values from sliders for saving."""
        return {
            'led_r': self.red.get(),
            'led_g': self.green.get(),
            'led_b': self.blue.get()
        }
    
    def update_from_settings(self, settings):
        """Set color values from loaded settings and update the lightbar."""
        r = settings.get('led_r', 0)
        g = settings.get('led_g', 0)
        b = settings.get('led_b', 255) # Default to blue
        
        self.red.set(r)
        self.green.set(g)
        self.blue.set(b)
        
        # Also apply the color to the lightbar immediately
        self.set_lightbar() 