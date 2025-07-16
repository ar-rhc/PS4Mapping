#!/usr/bin/env python3
"""
Hybrid DS4 Controller UI - Combines rich GUI with high-performance event-driven UDP
This version keeps all the existing GUI functionality while using the new event-driven UDP system
"""

# Import the existing GUI code
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
import hid
import json

import tkinter as tk

# Import the original GUI (we'll inherit from it)
from gui.main_window import DS4ControlUI
from controller.data_parser import DS4DataParser

class HybridDS4ControlUI(DS4ControlUI):
    """
    Hybrid DS4 Controller UI that combines:
    - All existing GUI functionality (mapping, visualization, etc.)
    - High-performance event-driven UDP for Hammerspoon
    """
    
    def __init__(self):
        # Initialize the data parser BEFORE calling parent
        # This ensures it's available when parent's poll_controller() is called
        self.data_parser = DS4DataParser()
        
        # Initialize the parent class first
        super().__init__()
        
        print("🎮 Hybrid DS4 Controller UI initialized")
    
    def poll_controller(self):
        """
        Modified polling method that uses event-driven UDP
        Keeps all existing GUI functionality while using the new UDP system
        """
        try:
            # Check for IPC commands from other scripts
            if hasattr(self, 'udp_manager'):
                self.udp_manager.check_ipc_socket()

            # hid.read() is now safely on the main thread
            report = self.h.read(64)
            
            if report:
                # Parse and process the data every time
                controller_data = self.data_parser.parse_controller_data(report)
                gyro = controller_data['gyro']
                accel = controller_data['accelerometer']
                
                # --- Conditional UI Updating (The main optimization) ---
                is_visual_tab_active = False
                if self.state() == 'normal': # Only check tabs if window is visible
                    try:
                        current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
                        if current_tab_text == 'Live Visualization':
                            is_visual_tab_active = True
                    except tk.TclError:
                        pass # Ignore error if tabs aren't ready
                
                # Sensor fusion and orientation tracking now handled by visualization tab
                # The visualization tab will handle this when update_visualizations is called

                # Store data for UDP and export
                self.current_data = controller_data
                self.current_data['timestamp'] = time.time()
                # Orientation and axis locks now handled by visualization tab
                
                # Only do expensive UI drawing if the tab is visible
                if is_visual_tab_active:
                    self.update_visualizations(self.current_data)
                    
                    # Throttle the text display update
                    self.text_update_counter += 1
                    update_text_frequency = 5 # Update text ~every 5th poll
                    if self.text_update_counter >= update_text_frequency:
                        self.update_data_display(self.current_data)
                        self.text_update_counter = 0

                    # Redraw the Matplotlib canvas
                    if hasattr(self, 'visualization_tab_modular'):
                        self.visualization_tab_modular.canvas.draw()
                
                # The old `event_udp_integration` is now removed.
                # We will rely solely on the DS4DataParser's change detection
                # and the original UDPManager for sending BTT-compatible events.

                # ALWAYS check for and send discrete digital changes for BTT
                try:
                    digital_changes = self.data_parser.check_digital_changes(controller_data)
                    if digital_changes:
                        # If in controller mapping mode, intercept the press and start key capture
                        if self._controller_mapping_active:
                            button_to_map = None
                            # Find the first pressed button, ignoring release events
                            if digital_changes.get('buttons'):
                                for btn, state in digital_changes['buttons'].items():
                                    if state == 'press':
                                        button_to_map = btn
                                        break  # Use the first pressed button found
                            
                            # If no regular button was pressed, check the D-pad
                            if not button_to_map and digital_changes.get('dpad') and digital_changes['dpad'] != 'none':
                                button_to_map = f"dpad_{digital_changes['dpad']}"
                            
                            if button_to_map:
                                # This method is on the parent UI class and will handle updating the
                                # mapping dialog and stopping the capture mode.
                                self.handle_controller_press_for_mapping(button_to_map)
                        
                        # Otherwise, send the change as a normal mapped event
                        elif hasattr(self, 'udp_manager'):
                            self.udp_manager.send_digital_changes(digital_changes)
                        
                except Exception as send_error:
                    print(f"BTT/Digital UDP send error: {send_error}")
                
        except hid.HIDException as e:
            print(f"Controller disconnected or HID error: {e}")
            self.quit_application() # Cleanly quit if controller is lost
            return # Stop polling
        except Exception as e:
            print(f'Polling error: {e}')
            
        # Schedule the next poll
        self.after(self.polling_rate, self.poll_controller)
    
    def quit_application(self):
        """Modified quit method to stop event-driven UDP"""
        print("Quit command received. Shutting down.")
        
        # Stop tray icon first
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                print(f"Error stopping tray icon: {e}")
        
        # Close HID device
        if hasattr(self, 'h'):
            self.h.close()

        # Close UDP manager if it exists
        if hasattr(self, 'udp_manager'):
            try:
                self.udp_manager.stop()
            except Exception as e:
                print(f"Error stopping UDP manager: {e}")
        
        self.destroy()


def main():
    """Main function to run the hybrid DS4 controller UI"""
    print("🎮 Starting Hybrid DS4 Controller UI")

    try:
        app = HybridDS4ControlUI()
        
        # Only set up window protocol if the app was created successfully
        if hasattr(app, 'destroy') and not app.winfo_exists():
            print("❌ Application failed to initialize properly")
            return
            
        # This now hides the window instead of quitting
        app.protocol("WM_DELETE_WINDOW", app.window_manager.hide_window)
        
        # Start the Polling Loop
        app.poll_controller()
        
        # Start the tray icon in detached mode
        if hasattr(app, 'tray_icon') and app.tray_icon:
            app.tray_icon.run_detached() 
        
        # Run the main Tkinter loop
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Failed to start Hybrid DS4Controller UI: {e}")
        print("💡 Make sure your DS4 controller is connected via USB")


if __name__ == "__main__":
    main()