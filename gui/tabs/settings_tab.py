#!/usr/bin/env python3
"""
Settings Tab Module
Handles DS4 controller sensor fusion and general settings
"""

import tkinter as tk
import sys


class SettingsTab:
    """
    Settings control tab for DS4 controller
    Provides controls for sensor fusion parameters and general settings
    """
    
    def __init__(self, parent_frame, gui_instance):
        """
        Initialize the settings tab
        
        Args:
            parent_frame: Parent tkinter frame to pack into
            gui_instance: A direct reference to the main DS4ControlUI instance
        """
        self.parent_frame = parent_frame
        self.gui_instance = gui_instance
        
        # Create the tab content
        self.create_widgets()
    
    def create_widgets(self):
        """Create the settings control widgets"""
        frame = self.parent_frame
        
        # Title
        title_label = tk.Label(frame, text="Sensor Fusion Settings", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Complementary Filter Alpha (0.8-0.98)
        alpha_frame = tk.Frame(frame)
        alpha_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(alpha_frame, text="Filter Responsiveness (Alpha):").pack(anchor='w')
        self.alpha_slider = tk.Scale(alpha_frame, from_=0.80, to=0.98, resolution=0.01, 
                                   orient=tk.HORIZONTAL, command=self._on_alpha_change)
        self.alpha_slider.pack(fill='x')
        self.alpha_label = tk.Label(alpha_frame, text="Current: 0.85 (Higher = Smoother, Lower = More Responsive)")
        self.alpha_label.pack(anchor='w')
        
        # Gyro Sensitivity (200-1000)
        sensitivity_frame = tk.Frame(frame)
        sensitivity_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(sensitivity_frame, text="Gyro Sensitivity:").pack(anchor='w')
        self.sensitivity_slider = tk.Scale(sensitivity_frame, from_=200, to=1000, resolution=10,
                                         orient=tk.HORIZONTAL, command=self._on_sensitivity_change)
        self.sensitivity_slider.pack(fill='x')
        self.sensitivity_label = tk.Label(sensitivity_frame, text="Current: 500 (Lower = More Sensitive)")
        self.sensitivity_label.pack(anchor='w')
        
        # Damping Factor (0.90-0.99)
        damping_frame = tk.Frame(frame)
        damping_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(damping_frame, text="Neutral Return Damping:").pack(anchor='w')
        self.damping_slider = tk.Scale(damping_frame, from_=0.90, to=0.99, resolution=0.01,
                                     orient=tk.HORIZONTAL, command=self._on_damping_change)
        self.damping_slider.pack(fill='x')
        self.damping_label = tk.Label(damping_frame, text="Current: 0.95 (Higher = Slower Return to Neutral)")
        self.damping_label.pack(anchor='w')
        
        # Polling Rate (5-100ms)
        polling_frame = tk.Frame(frame)
        polling_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(polling_frame, text="Polling Rate (ms):").pack(anchor='w')
        self.polling_slider = tk.Scale(polling_frame, from_=5, to=100, resolution=1,
                                     orient=tk.HORIZONTAL, command=self._on_polling_change)
        self.polling_slider.pack(fill='x')
        self.polling_label = tk.Label(polling_frame, text="Current: 8ms (125 Hz)")
        self.polling_label.pack(anchor='w')
        
        # Reset button
        reset_btn = tk.Button(frame, text="Reset to Defaults", command=self.gui_instance.settings_manager.reset_settings)
        reset_btn.pack(pady=20)
        
        # Save Settings button - now directly calls the main window's method
        save_btn = tk.Button(frame, text="Save Settings", command=self.gui_instance.settings_manager.save_settings)
        save_btn.pack(pady=10)
    
    def _on_alpha_change(self, value):
        """Handle alpha value change"""
        alpha = float(value)
        self.alpha_label.config(text=f"Current: {alpha:.2f} (Higher = Smoother, Lower = More Responsive)")
        self.gui_instance.update_alpha(alpha)
    
    def _on_sensitivity_change(self, value):
        """Handle sensitivity value change"""
        sensitivity = float(value)
        self.sensitivity_label.config(text=f"Current: {sensitivity:.0f} (Lower = More Sensitive)")
        self.gui_instance.update_sensitivity(sensitivity)
    
    def _on_damping_change(self, value):
        """Handle damping value change"""
        damping = float(value)
        self.damping_label.config(text=f"Current: {damping:.2f} (Higher = Slower Return to Neutral)")
        self.gui_instance.update_damping(damping)
    
    def _on_polling_change(self, value):
        """Handle polling rate change"""
        polling = int(value)
        self.polling_label.config(text=f"Current: {polling}ms ({1000//polling} Hz)")
        self.gui_instance.update_polling(polling)
    
    def update_from_settings(self, settings):
        """Update UI from settings dictionary"""
        if 'alpha' in settings:
            self.alpha_slider.set(settings['alpha'])
            self.alpha_label.config(text=f"Current: {settings['alpha']:.2f} (Higher = Smoother, Lower = More Responsive)")
        
        if 'gyro_sensitivity' in settings:
            self.sensitivity_slider.set(settings['gyro_sensitivity'])
            self.sensitivity_label.config(text=f"Current: {settings['gyro_sensitivity']:.0f} (Lower = More Sensitive)")
        
        if 'damping_factor' in settings:
            self.damping_slider.set(settings['damping_factor'])
            self.damping_label.config(text=f"Current: {settings['damping_factor']:.2f} (Higher = Slower Return to Neutral)")
        
        if 'polling_rate' in settings:
            self.polling_slider.set(settings['polling_rate'])
            self.polling_label.config(text=f"Current: {settings['polling_rate']}ms ({1000//settings['polling_rate']} Hz)")
    
    def get_current_settings(self):
        """Get current settings from UI"""
        return {
            'alpha': self.alpha_slider.get(),
            'gyro_sensitivity': self.sensitivity_slider.get(),
            'damping_factor': self.damping_slider.get(),
            'polling_rate': self.polling_slider.get()
        } 