#!/usr/bin/env python3
"""
Rumble Tab Module
Handles DS4 controller rumble control and tactile feedback
"""

import tkinter as tk
from controller.hid_controller import set_lightbar_and_rumble


class RumbleTab:
    """
    Rumble control tab for DS4 controller
    Provides rumble control, preset patterns, and tactile feedback
    """
    
    def __init__(self, parent_frame, hid_device, rumble_callbacks=None):
        """
        Initialize the rumble tab
        
        Args:
            parent_frame: Parent tkinter frame to pack into
            hid_device: HID device handle for sending commands
            rumble_callbacks: Dictionary of callback functions for rumble events
        """
        self.parent_frame = parent_frame
        self.hid_device = hid_device
        self.rumble_callbacks = rumble_callbacks or {}
        
        # Initialize rumble values
        self.strong_rumble = 0
        self.weak_rumble = 0
        
        # Initialize tactile feedback settings
        self.tactile_enabled = False
        self.threshold1_enabled = True
        self.threshold1_value = 64
        self.threshold2_enabled = True
        self.threshold2_value = 128
        self.threshold3_enabled = True
        self.threshold3_value = 192
        self.tactile_duration = 50  # milliseconds - short for strong rumble
        self.tactile_intensity = 255  # strong intensity
        
        # Track previous trigger states for threshold crossing detection
        self.prev_l2_value = 0
        self.prev_r2_value = 0
        
        # Track last rumble trigger points to prevent rapid re-triggering
        self.l2_last_rumble_threshold = None
        self.r2_last_rumble_threshold = None
        self.hysteresis_margin = 2  # Points away from threshold required before re-triggering
        
        # Create the tab content
        self.create_widgets()
    
    def create_widgets(self):
        """Create the rumble control widgets"""
        frame = self.parent_frame
        
        # Title
        title_label = tk.Label(frame, text="DualShock 4 Rumble Control", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Create main control frame
        control_frame = tk.Frame(frame)
        control_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Individual motor controls
        left_frame = tk.Frame(control_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Strong motor (left) control
        strong_frame = tk.LabelFrame(left_frame, text="Strong Motor (Left)", font=("Arial", 12, "bold"))
        strong_frame.pack(fill=tk.X, pady=5)
        
        self.strong_slider = tk.Scale(strong_frame, from_=0, to=255, orient=tk.HORIZONTAL, 
                                    command=self._on_strong_rumble_change, length=300)
        self.strong_slider.pack(padx=10, pady=5)
        self.strong_label = tk.Label(strong_frame, text="Intensity: 0")
        self.strong_label.pack(pady=5)
        
        # Weak motor (right) control
        weak_frame = tk.LabelFrame(left_frame, text="Weak Motor (Right)", font=("Arial", 12, "bold"))
        weak_frame.pack(fill=tk.X, pady=5)
        
        self.weak_slider = tk.Scale(weak_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                  command=self._on_weak_rumble_change, length=300)
        self.weak_slider.pack(padx=10, pady=5)
        self.weak_label = tk.Label(weak_frame, text="Intensity: 0")
        self.weak_label.pack(pady=5)
        
        # Right side - Preset patterns and controls
        right_frame = tk.Frame(control_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Preset patterns
        preset_frame = tk.LabelFrame(right_frame, text="Preset Patterns", font=("Arial", 12, "bold"))
        preset_frame.pack(fill=tk.X, pady=5)
        
        # Preset buttons
        preset_buttons = [
            ("Light Rumble", 50, 50),
            ("Medium Rumble", 128, 128),
            ("Strong Rumble", 200, 200),
            ("Maximum Rumble", 255, 255),
            ("Left Only", 255, 0),
            ("Right Only", 0, 255),
            ("Pulse Pattern", 255, 128),
            ("Stop Rumble", 0, 0)
        ]
        
        for i, (name, strong, weak) in enumerate(preset_buttons):
            btn = tk.Button(preset_frame, text=name, width=15,
                          command=lambda s=strong, w=weak: self._on_set_preset_rumble(s, w))
            btn.grid(row=i//2, column=i%2, padx=5, pady=3, sticky='ew')
        
        # Advanced controls
        advanced_frame = tk.LabelFrame(right_frame, text="Advanced Controls", font=("Arial", 12, "bold"))
        advanced_frame.pack(fill=tk.X, pady=10)
        
        # Report type selection
        report_frame = tk.Frame(advanced_frame)
        report_frame.pack(fill=tk.X, pady=5)
        tk.Label(report_frame, text="Report Type:").pack(side=tk.LEFT)
        self.report_type = tk.StringVar(value="0x05")
        tk.Radiobutton(report_frame, text="0x11 (Full)", variable=self.report_type, value="0x11").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(report_frame, text="0x05 (Simple)", variable=self.report_type, value="0x05").pack(side=tk.LEFT, padx=5)
        
        # Apply button
        apply_btn = tk.Button(advanced_frame, text="Apply Rumble", command=self._on_apply_rumble, 
                            bg="green", fg="white", font=("Arial", 10, "bold"))
        apply_btn.pack(pady=5)
        
        # Test button
        test_btn = tk.Button(advanced_frame, text="Test Rumble (255, 255)", command=self._on_test_rumble,
                           bg="blue", fg="white", font=("Arial", 10, "bold"))
        test_btn.pack(pady=5)
        
        # Tactile Feedback Panel
        tactile_frame = tk.LabelFrame(frame, text="Tactile Feedback (L2/R2)", font=("Arial", 12, "bold"))
        tactile_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Enable/disable tactile feedback
        enable_frame = tk.Frame(tactile_frame)
        enable_frame.pack(fill=tk.X, pady=5)
        self.tactile_var = tk.BooleanVar(value=self.tactile_enabled)
        tk.Checkbutton(enable_frame, text="Enable Tactile Feedback", variable=self.tactile_var, 
                      command=self._on_toggle_tactile_feedback, font=("Arial", 10)).pack(side=tk.LEFT)
        
        # Three threshold controls
        threshold_frame = tk.Frame(tactile_frame)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        # Threshold 1 (Low)
        thresh1_frame = tk.Frame(threshold_frame)
        thresh1_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        thresh1_header = tk.Frame(thresh1_frame)
        thresh1_header.pack(fill=tk.X)
        self.thresh1_enabled_var = tk.BooleanVar(value=self.threshold1_enabled)
        tk.Checkbutton(thresh1_header, text="", variable=self.thresh1_enabled_var, 
                      command=self._on_threshold1_enabled).pack(side=tk.LEFT)
        tk.Label(thresh1_header, text="Threshold 1 (Low):", font=("Arial", 9)).pack(side=tk.LEFT)
        self.threshold1_slider = tk.Scale(thresh1_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                        command=self._on_threshold1_value, length=150)
        self.threshold1_slider.set(self.threshold1_value)
        self.threshold1_slider.pack(fill=tk.X)
        self.threshold1_label = tk.Label(thresh1_frame, text=f"Value: {self.threshold1_value}", font=("Arial", 8))
        self.threshold1_label.pack(anchor='w')
        
        # Threshold 2 (Medium)
        thresh2_frame = tk.Frame(threshold_frame)
        thresh2_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        thresh2_header = tk.Frame(thresh2_frame)
        thresh2_header.pack(fill=tk.X)
        self.thresh2_enabled_var = tk.BooleanVar(value=self.threshold2_enabled)
        tk.Checkbutton(thresh2_header, text="", variable=self.thresh2_enabled_var, 
                      command=self._on_threshold2_enabled).pack(side=tk.LEFT)
        tk.Label(thresh2_header, text="Threshold 2 (Med):", font=("Arial", 9)).pack(side=tk.LEFT)
        self.threshold2_slider = tk.Scale(thresh2_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                        command=self._on_threshold2_value, length=150)
        self.threshold2_slider.set(self.threshold2_value)
        self.threshold2_slider.pack(fill=tk.X)
        self.threshold2_label = tk.Label(thresh2_frame, text=f"Value: {self.threshold2_value}", font=("Arial", 8))
        self.threshold2_label.pack(anchor='w')
        
        # Threshold 3 (High)
        thresh3_frame = tk.Frame(threshold_frame)
        thresh3_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        thresh3_header = tk.Frame(thresh3_frame)
        thresh3_header.pack(fill=tk.X)
        self.thresh3_enabled_var = tk.BooleanVar(value=self.threshold3_enabled)
        tk.Checkbutton(thresh3_header, text="", variable=self.thresh3_enabled_var, 
                      command=self._on_threshold3_enabled).pack(side=tk.LEFT)
        tk.Label(thresh3_header, text="Threshold 3 (High):", font=("Arial", 9)).pack(side=tk.LEFT)
        self.threshold3_slider = tk.Scale(thresh3_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                        command=self._on_threshold3_value, length=150)
        self.threshold3_slider.set(self.threshold3_value)
        self.threshold3_slider.pack(fill=tk.X)
        self.threshold3_label = tk.Label(thresh3_frame, text=f"Value: {self.threshold3_value}", font=("Arial", 8))
        self.threshold3_label.pack(anchor='w')
        
        # Tactile settings
        settings_frame = tk.Frame(tactile_frame)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Duration control
        duration_frame = tk.Frame(settings_frame)
        duration_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Label(duration_frame, text="Duration (ms):", font=("Arial", 9)).pack(anchor='w')
        self.duration_slider = tk.Scale(duration_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                                      command=self._on_tactile_duration, length=150)
        self.duration_slider.set(self.tactile_duration)
        self.duration_slider.pack(fill=tk.X)
        self.duration_label = tk.Label(duration_frame, text=f"Value: {self.tactile_duration}ms", font=("Arial", 8))
        self.duration_label.pack(anchor='w')
        
        # Intensity control
        intensity_frame = tk.Frame(settings_frame)
        intensity_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        tk.Label(intensity_frame, text="Intensity:", font=("Arial", 9)).pack(anchor='w')
        self.intensity_slider = tk.Scale(intensity_frame, from_=50, to=255, orient=tk.HORIZONTAL,
                                       command=self._on_tactile_intensity, length=150)
        self.intensity_slider.set(self.tactile_intensity)
        self.intensity_slider.pack(fill=tk.X)
        self.intensity_label = tk.Label(intensity_frame, text=f"Value: {self.tactile_intensity}", font=("Arial", 8))
        self.intensity_label.pack(anchor='w')
        
        # Trigger visualization
        viz_frame = tk.Frame(tactile_frame)
        viz_frame.pack(fill=tk.X, pady=5)
        tk.Label(viz_frame, text="Trigger Visualization:", font=("Arial", 9, "bold")).pack(anchor='w')
        
        # Create canvas for trigger visualization
        self.trigger_canvas = tk.Canvas(viz_frame, height=60, bg='white')
        self.trigger_canvas.pack(fill=tk.X, pady=2)
        
        # Draw trigger bars
        self.draw_trigger_visualization(0, 0)
        
        # Status display
        status_frame = tk.LabelFrame(frame, text="Status", font=("Arial", 10, "bold"))
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.rumble_status = tk.Label(status_frame, text="Rumble: OFF", fg="red", font=("Arial", 12))
        self.rumble_status.pack(pady=5)
    
    # Event handlers
    def _on_strong_rumble_change(self, value):
        """Handle strong rumble value change and apply it."""
        self.strong_rumble = int(value)
        self.strong_label.config(text=f"Intensity: {self.strong_rumble}")
        self._on_apply_rumble()

    def _on_weak_rumble_change(self, value):
        """Handle weak rumble value change and apply it."""
        self.weak_rumble = int(value)
        self.weak_label.config(text=f"Intensity: {self.weak_rumble}")
        self._on_apply_rumble()

    def _on_set_preset_rumble(self, strong, weak):
        """Handle preset rumble selection and apply it."""
        self.strong_slider.set(strong)
        self.weak_slider.set(weak)
        # Manually update state since setting slider won't trigger command
        self.strong_rumble = strong
        self.weak_rumble = weak
        self.strong_label.config(text=f"Intensity: {strong}")
        self.weak_label.config(text=f"Intensity: {weak}")
        self._on_apply_rumble()

    def _on_apply_rumble(self):
        """Apply rumble based on the selected report type."""
        report_type = self.report_type.get()
        if report_type == '0x05':
            if 'set_rumble_simple' in self.rumble_callbacks:
                self.rumble_callbacks['set_rumble_simple'](self.strong_rumble, self.weak_rumble)
        elif report_type == '0x11':
            if 'set_rumble_0x11' in self.rumble_callbacks:
                # Note: This doesn't include lightbar colors.
                self.rumble_callbacks['set_rumble_0x11'](self.strong_rumble, self.weak_rumble)
        self.update_rumble_status(self.strong_rumble > 0 or self.weak_rumble > 0, self.strong_rumble, self.weak_rumble)

    def _on_test_rumble(self):
        """Handle test rumble button"""
        if 'set_rumble_simple' in self.rumble_callbacks:
            self.rumble_callbacks['set_rumble_simple'](255, 255)
            self.parent_frame.after(1000, lambda: self.rumble_callbacks['set_rumble_simple'](0, 0))

    def _on_toggle_tactile_feedback(self):
        """Handle tactile feedback toggle"""
        self.tactile_enabled = self.tactile_var.get()
        if 'toggle_tactile_feedback' in self.rumble_callbacks:
            self.rumble_callbacks['toggle_tactile_feedback']()
    
    def _on_threshold1_enabled(self):
        """Handle threshold 1 enabled toggle"""
        self.threshold1_enabled = self.thresh1_enabled_var.get()
        if 'update_threshold1_enabled' in self.rumble_callbacks:
            self.rumble_callbacks['update_threshold1_enabled']()
    
    def _on_threshold2_enabled(self):
        """Handle threshold 2 enabled toggle"""
        self.threshold2_enabled = self.thresh2_enabled_var.get()
        if 'update_threshold2_enabled' in self.rumble_callbacks:
            self.rumble_callbacks['update_threshold2_enabled']()
    
    def _on_threshold3_enabled(self):
        """Handle threshold 3 enabled toggle"""
        self.threshold3_enabled = self.thresh3_enabled_var.get()
        if 'update_threshold3_enabled' in self.rumble_callbacks:
            self.rumble_callbacks['update_threshold3_enabled']()
    
    def _on_threshold1_value(self, value):
        """Handle threshold 1 value change"""
        self.threshold1_value = int(value)
        self.threshold1_label.config(text=f"Value: {self.threshold1_value}")
        if 'update_threshold1_value' in self.rumble_callbacks:
            self.rumble_callbacks['update_threshold1_value'](self.threshold1_value)
    
    def _on_threshold2_value(self, value):
        """Handle threshold 2 value change"""
        self.threshold2_value = int(value)
        self.threshold2_label.config(text=f"Value: {self.threshold2_value}")
        if 'update_threshold2_value' in self.rumble_callbacks:
            self.rumble_callbacks['update_threshold2_value'](self.threshold2_value)
    
    def _on_threshold3_value(self, value):
        """Handle threshold 3 value change"""
        self.threshold3_value = int(value)
        self.threshold3_label.config(text=f"Value: {self.threshold3_value}")
        if 'update_threshold3_value' in self.rumble_callbacks:
            self.rumble_callbacks['update_threshold3_value'](self.threshold3_value)
    
    def _on_tactile_duration(self, value):
        """Handle tactile duration change"""
        self.tactile_duration = int(value)
        self.duration_label.config(text=f"Value: {self.tactile_duration}ms")
        if 'update_tactile_duration' in self.rumble_callbacks:
            self.rumble_callbacks['update_tactile_duration'](self.tactile_duration)
    
    def _on_tactile_intensity(self, value):
        """Handle tactile intensity change"""
        self.tactile_intensity = int(value)
        self.intensity_label.config(text=f"Value: {self.tactile_intensity}")
        if 'update_tactile_intensity' in self.rumble_callbacks:
            self.rumble_callbacks['update_tactile_intensity'](self.tactile_intensity)
    
    # Public methods
    def draw_trigger_visualization(self, l2_value, r2_value):
        """Draw trigger visualization on canvas"""
        canvas = self.trigger_canvas
        canvas.delete("all")
        
        # Draw L2 trigger (left side)
        l2_height = int((l2_value / 255.0) * 50)
        canvas.create_rectangle(10, 50 - l2_height, 30, 50, fill='blue', outline='black')
        canvas.create_text(20, 55, text=f"L2: {l2_value}")
        
        # Draw R2 trigger (right side)
        r2_height = int((r2_value / 255.0) * 50)
        canvas.create_rectangle(70, 50 - r2_height, 90, 50, fill='red', outline='black')
        canvas.create_text(80, 55, text=f"R2: {r2_value}")
        
        # Draw threshold lines
        if self.threshold1_enabled:
            thresh1_y = 50 - int((self.threshold1_value / 255.0) * 50)
            canvas.create_line(5, thresh1_y, 35, thresh1_y, fill='green', width=1)
        if self.threshold2_enabled:
            thresh2_y = 50 - int((self.threshold2_value / 255.0) * 50)
            canvas.create_line(5, thresh2_y, 35, thresh2_y, fill='orange', width=1)
        if self.threshold3_enabled:
            thresh3_y = 50 - int((self.threshold3_value / 255.0) * 50)
            canvas.create_line(5, thresh3_y, 35, thresh3_y, fill='red', width=1)
        
        # Draw threshold lines for R2
        if self.threshold1_enabled:
            thresh1_y = 50 - int((self.threshold1_value / 255.0) * 50)
            canvas.create_line(65, thresh1_y, 95, thresh1_y, fill='green', width=1)
        if self.threshold2_enabled:
            thresh2_y = 50 - int((self.threshold2_value / 255.0) * 50)
            canvas.create_line(65, thresh2_y, 95, thresh2_y, fill='orange', width=1)
        if self.threshold3_enabled:
            thresh3_y = 50 - int((self.threshold3_value / 255.0) * 50)
            canvas.create_line(65, thresh3_y, 95, thresh3_y, fill='red', width=1)
    
    def update_rumble_status(self, is_on, strong=0, weak=0):
        """Update rumble status display"""
        if is_on:
            self.rumble_status.config(text=f"Rumble: ON (L:{strong}, R:{weak})", fg="green")
        else:
            self.rumble_status.config(text="Rumble: OFF", fg="red")
    
    def check_tactile_feedback(self, l2_value, r2_value):
        """Check for tactile feedback triggers"""
        if not self.tactile_enabled:
            return
        
        # Check L2 thresholds
        self._check_threshold_crossing('l2', l2_value, self.prev_l2_value)
        self.prev_l2_value = l2_value
        
        # Check R2 thresholds
        self._check_threshold_crossing('r2', r2_value, self.prev_r2_value)
        self.prev_r2_value = r2_value
    
    def _check_threshold_crossing(self, trigger, current_value, prev_value):
        """Check if a threshold was crossed"""
        thresholds = []
        if self.threshold1_enabled:
            thresholds.append((1, self.threshold1_value))
        if self.threshold2_enabled:
            thresholds.append((2, self.threshold2_value))
        if self.threshold3_enabled:
            thresholds.append((3, self.threshold3_value))
        
        for threshold_num, threshold_value in thresholds:
            # Check if threshold was crossed (going up)
            if prev_value < threshold_value <= current_value:
                # Check hysteresis to prevent rapid re-triggering
                last_threshold = self.l2_last_rumble_threshold if trigger == 'l2' else self.r2_last_rumble_threshold
                if last_threshold != threshold_num:
                    self._trigger_tactile_feedback(trigger, threshold_num)
                    if trigger == 'l2':
                        self.l2_last_rumble_threshold = threshold_num
                    else:
                        self.r2_last_rumble_threshold = threshold_num
            
            # Check if threshold was crossed (going down)
            elif current_value < threshold_value <= prev_value:
                # Reset hysteresis when going below threshold
                if trigger == 'l2':
                    self.l2_last_rumble_threshold = None
                else:
                    self.r2_last_rumble_threshold = None
    
    def _trigger_tactile_feedback(self, trigger, threshold_num):
        """Trigger tactile feedback"""
        if 'trigger_tactile_feedback' in self.rumble_callbacks:
            self.rumble_callbacks['trigger_tactile_feedback'](trigger)
    
    def get_rumble_values(self):
        """Get current rumble values"""
        return {
            'strong': self.strong_rumble,
            'weak': self.weak_rumble,
            'report_type': self.report_type.get()
        }
    
    def get_tactile_settings(self):
        """Get current tactile feedback settings"""
        return {
            'enabled': self.tactile_enabled,
            'threshold1_enabled': self.threshold1_enabled,
            'threshold1_value': self.threshold1_value,
            'threshold2_enabled': self.threshold2_enabled,
            'threshold2_value': self.threshold2_value,
            'threshold3_enabled': self.threshold3_enabled,
            'threshold3_value': self.threshold3_value,
            'duration': self.tactile_duration,
            'intensity': self.tactile_intensity
        } 

    def update_from_settings(self, settings):
        """Update UI elements with loaded settings"""
        # Update tactile feedback settings
        self.tactile_enabled = settings.get('tactile_enabled', False)
        self.tactile_var.set(self.tactile_enabled)
        
        # Update threshold 1 settings
        self.threshold1_enabled = settings.get('threshold1_enabled', True)
        self.thresh1_enabled_var.set(self.threshold1_enabled)
        self.threshold1_value = settings.get('threshold1_value', 64)
        self.threshold1_slider.set(self.threshold1_value)
        self.threshold1_label.config(text=f"Value: {self.threshold1_value}")
        
        # Update threshold 2 settings
        self.threshold2_enabled = settings.get('threshold2_enabled', True)
        self.thresh2_enabled_var.set(self.threshold2_enabled)
        self.threshold2_value = settings.get('threshold2_value', 128)
        self.threshold2_slider.set(self.threshold2_value)
        self.threshold2_label.config(text=f"Value: {self.threshold2_value}")
        
        # Update threshold 3 settings
        self.threshold3_enabled = settings.get('threshold3_enabled', True)
        self.thresh3_enabled_var.set(self.threshold3_enabled)
        self.threshold3_value = settings.get('threshold3_value', 192)
        self.threshold3_slider.set(self.threshold3_value)
        self.threshold3_label.config(text=f"Value: {self.threshold3_value}")
        
        # Update tactile feedback duration and intensity
        self.tactile_duration = settings.get('tactile_duration', 50)
        self.duration_slider.set(self.tactile_duration)
        self.duration_label.config(text=f"Value: {self.tactile_duration}ms")
        
        self.tactile_intensity = settings.get('tactile_intensity', 255)
        self.intensity_slider.set(self.tactile_intensity)
        self.intensity_label.config(text=f"Value: {self.tactile_intensity}") 