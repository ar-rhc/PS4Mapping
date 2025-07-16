import json
import os

class SettingsManager:
    """Handles loading, saving, and applying application settings."""
    
    SETTINGS_FILE = "ds4_settings.json"

    def __init__(self, app):
        """
        Initializes the SettingsManager.
        
        Args:
            app: The main DS4ControlUI application instance.
        """
        self.app = app

    def load_settings(self):
        """Load settings from JSON file or create a default one."""
        try:
            with open(self.SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
        except FileNotFoundError:
            settings = self._get_default_settings()
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        
        # Apply settings to the application instance
        self.app.alpha = settings.get('alpha', 0.98)
        self.app.gyro_sensitivity = settings.get('gyro_sensitivity', 1.0)
        self.app.damping_factor = settings.get('damping_factor', 0.1)
        self.app.polling_rate = settings.get('polling_rate', 1)
        self.app.saved_axis_locks = settings.get('axis_locks', {'roll': False, 'pitch': False, 'yaw': False})
        self.app.locked_axis = settings.get('locked_axis')
        
        # Keep a direct reference for other modules to use
        self.app.settings = settings

    def save_settings(self):
        """Save the current application settings to the JSON file."""
        orientation_offset = {}
        axis_locks = {}
        if hasattr(self.app, 'visualization_tab_modular'):
            orientation_offset = self.app.visualization_tab_modular.orientation_offset.copy()
            axis_locks = self.app.visualization_tab_modular.axis_locks.copy()
        
        rumble_settings = {}
        if hasattr(self.app, 'rumble_tab_modular'):
            rumble_settings = self.app.rumble_tab_modular.get_tactile_settings()

        lightbar_settings = {}
        if hasattr(self.app, 'lightbar_tab_modular'):
            lightbar_settings = self.app.lightbar_tab_modular.get_color_settings()

        settings = {
            'alpha': self.app.alpha,
            'gyro_sensitivity': self.app.gyro_sensitivity,
            'damping_factor': self.app.damping_factor,
            'polling_rate': self.app.polling_rate,
            'orientation_offset': orientation_offset,
            'axis_locks': axis_locks,
            'locked_axis': self.app.locked_axis,
            **rumble_settings,
            **lightbar_settings
        }
        
        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)

    def reset_settings(self):
        """Reset settings to their default values."""
        self.app.alpha = 0.85
        self.app.gyro_sensitivity = 500.0
        self.app.damping_factor = 0.95
        self.app.polling_rate = 50
        self.app.locked_axis = None
        
        # Update the UI to reflect the reset
        self.update_ui_from_settings()

    def update_ui_from_settings(self):
        """Update all relevant UI components with the current settings."""
        if hasattr(self.app, 'settings_tab_modular'):
            self.app.settings_tab_modular.update_from_settings(self.app.settings)
        
        if hasattr(self.app, 'visualization_tab_modular'):
            self.app.visualization_tab_modular.update_from_settings({'axis_locks': self.app.saved_axis_locks})
            self.app.visualization_tab_modular.set_sensor_fusion_parameters(self.app.alpha, self.app.gyro_sensitivity, self.app.damping_factor)
            if hasattr(self.app, 'saved_orientation_offset'):
                self.app.visualization_tab_modular.orientation_offset = self.app.saved_orientation_offset.copy()
            self.app.visualization_tab_modular._update_lock_button_colors()
        
        if hasattr(self.app, 'rumble_tab_modular'):
            self.app.rumble_tab_modular.update_from_settings(self.app.settings)

        if hasattr(self.app, 'lightbar_tab_modular'):
            self.app.lightbar_tab_modular.update_from_settings(self.app.settings)
            
    def _get_default_settings(self):
        """Return a dictionary of default settings."""
        return {
            'alpha': 0.98, 'gyro_sensitivity': 1.0, 'damping_factor': 0.1, 'polling_rate': 1,
            'axis_locks': {'roll': False, 'pitch': False, 'yaw': False}, 'locked_axis': None,
            'tactile_enabled': False, 'threshold1_enabled': True, 'threshold1_value': 64,
            'threshold2_enabled': True, 'threshold2_value': 128, 'threshold3_enabled': True,
            'threshold3_value': 192, 'tactile_duration': 50, 'tactile_intensity': 255,
            'led_r': 0, 'led_g': 0, 'led_b': 255
        } 