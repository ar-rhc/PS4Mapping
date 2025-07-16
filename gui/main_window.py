import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import socket
import os
import threading
import queue
import hid
import subprocess
from PIL import Image, ImageTk, ImageDraw
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pystray

# Constants
SETTINGS_FILE = "ds4_settings.json"

# Import the new modular components
from gui.mapping_dialog import MappingConfigFrame
from controller.hid_controller import HIDController, VENDOR_ID, PRODUCT_ID
from controller.data_parser import DS4DataParser
from network.udp_manager import UDPManager
from gui.tabs.lightbar_tab import LightbarTab
from gui.tabs.visualization_tab import VisualizationTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.rumble_tab import RumbleTab
# from gui.tabs.mouse_control_tab import MouseControlTab
from utils.settings_manager import SettingsManager
from utils.window_manager import WindowManager

# For mouse control - REMOVED
# from pynput.mouse import Button, Controller

class DS4ControlUI(tk.Tk):
    def __init__(self, test_mode=False):
        super().__init__()
        self.title("DualShock 4 HID Control UI (⌘W to hide)")
        self.test_mode = test_mode
        
        # --- Set Initial Window Position (Centered) ---
        window_width = 1600
        window_height = 900
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coord = (screen_width // 2) - (window_width // 2)
        y_coord = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x_coord}+{y_coord}')
        
        # Hide window initially
        # self.withdraw()
        
        if not self.test_mode:
            try:
                self.h = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
            except hid.HIDException as e:
                messagebox.showerror("HID Error", f"Could not open controller.\nMake sure it's connected and not in use by another application.\n\nError: {e}")
                self.destroy()
                return
        else:
            self.h = None # In test mode, we don't need a real device
        
        self.data_parser = DS4DataParser()
        
        # --- Thread-safe Queue for HID reports ---
        self.report_queue = queue.Queue()

        # --- App State ---
        self.is_running = True
        self.text_update_counter = 0
        self.last_poll_time = 0
        self.locked_axis = None
        self.show_window_flag = False
        self.quit_flag = False
        # self.mouse_control_enabled = False # REMOVED
        # self.mouse = Controller() # REMOVED
        
        # --- Managers ---
        self.settings_manager = SettingsManager(self)
        self.window_manager = WindowManager(self) # Must be after root window setup
        
        try:
            self.udp_manager = UDPManager()
        except Exception as e:
            messagebox.showerror("UDP Error", f"Could not initialize UDP manager.\n\nError: {e}")
            self.destroy()
            return

        # --- Load Settings ---
        self.settings_manager.load_settings()
        
        # --- Create UI ---
        self.create_menu()
        self.create_widgets()
        
        # --- App State for Mapping ---
        self._controller_mapping_active = False
        self._key_capture_active = False
        self._key_capture_btn = None
        self._captured_mods = {}
        self._captured_key = None
        self._highlighted_button = None

        # --- Bindings ---
        self.bind('<Command-c>', self.set_neutral_orientation)
        
        # --- Start Worker Threads ---
        if not self.test_mode:
            self.controller_thread = threading.Thread(target=self._controller_reader_thread, daemon=True)
            self.controller_thread.start()

            # Start the main polling loop
            self.after(10, self.poll_controller)
        else:
            print("--- RUNNING IN TEST MODE ---")
            print("--- Controller hardware polling is disabled. ---")
        
        print("DS4 Controller UI started. Check the system tray for the 🎮 icon.")

    def _controller_reader_thread(self):
        """
        Worker thread to read from the HID device.
        This runs in the background to avoid blocking the main UI thread.
        """
        while self.is_running:
            try:
                report = self.h.read(64)
                if report:
                    self.report_queue.put(report)
            except hid.HIDException:
                print("Controller disconnected. Stopping reader thread.")
                self.is_running = False
            except Exception as e:
                print(f"Error in controller reader thread: {e}")
                self.is_running = False

    # --- UI Creation ---
    def create_widgets(self):
        self.tab_control = ttk.Notebook(self)
       
        # --- Add Mapping Config tab FIRST (as default) ---
        self.mapping_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.mapping_tab, text='Mapping Config')
        self.mapping_config_frame = MappingConfigFrame(
            self.mapping_tab,
            on_start_controller_mapping=self.start_controller_mapping,
            on_start_key_capture=self.start_key_capture,
            on_set_profile_lightbar=self.set_profile_lightbar_and_reload
        )
        self.mapping_config_frame.pack(fill='both', expand=True)
        # --- End Mapping Config tab ---
       
        # Live Visualization Tab
        self.visual_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.visual_tab, text='Live Visualization')
        self.visualization_tab_modular = VisualizationTab(
            parent_frame=self.visual_tab,
            on_export_data=self.export_data,
            on_export_json=self.export_json,
            on_toggle_axis_lock=self.toggle_axis_lock,
            on_set_neutral=self.set_neutral_orientation
        )

        # Settings Tab
        self.settings_tab = tk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text='Settings')
        self.settings_tab_modular = SettingsTab(
            parent_frame=self.settings_tab,
            gui_instance=self
        )

        # Lightbar Tab
        self.lightbar_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.lightbar_tab, text='Lightbar')
        self.lightbar_tab_modular = LightbarTab(
            parent_frame=self.lightbar_tab, 
            hid_device=self.h,
            save_settings_callback=self.settings_manager.save_settings
        )

        # Rumble Tab
        self.rumble_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.rumble_tab, text='Rumble')
        self.rumble_tab_modular = RumbleTab(
            parent_frame=self.rumble_tab,
            hid_device=self.h,
            rumble_callbacks={
                'set_rumble_simple': self.set_rumble_simple,
                'set_rumble_0x11': self.set_rumble_0x11,
                'trigger_tactile_feedback': self.trigger_tactile_feedback,
                'stop_tactile_feedback': self.stop_tactile_feedback
            }
        )

        # Mouse Control Tab - Removed to fix performance issues with Hammerspoon
        # self.mouse_control_tab_frame = ttk.Frame(self.tab_control)
        # self.tab_control.add(self.mouse_control_tab_frame, text='Mouse Control')
        # self.mouse_control_tab = MouseControlTab(
        #     parent_frame=self.mouse_control_tab_frame,
        #     toggle_callback=self.toggle_mouse_control
        # )
        # self.mouse_control_tab.pack(fill='both', expand=True)
        
        self.tab_control.pack(expand=1, fill='both')
        self.settings_manager.update_ui_from_settings()

        # Set UDP manager callbacks now that all UI components are initialized
        self.udp_manager.set_toggle_window_callback(self.window_manager.toggle_window_visibility)
        if hasattr(self, 'lightbar_tab_modular'):
            self.udp_manager.set_lightbar_callback(self.lightbar_tab_modular.set_lightbar_color)

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Hide to Tray (⌘W)", command=self.window_manager.hide_window)
        file_menu.add_command(label="Show/Hide Window", command=self.window_manager.toggle_window_visibility)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.window_manager.quit_application)

    # --- Core Application Logic ---
    def poll_controller(self):
        """
        Polls the queue for data from the controller thread and updates the UI.
        This runs in the main UI thread and is non-blocking.
        """
        try:
            report = self.report_queue.get_nowait()
            
            if report:
                controller_data = self.data_parser.parse_controller_data(report)
                self.current_data = controller_data
                self.current_data['timestamp'] = time.time()
                
                is_visual_tab_active = False
                if self.state() == 'normal':
                    try:
                        current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
                        if current_tab_text == 'Live Visualization':
                            is_visual_tab_active = True
                    except tk.TclError:
                        pass

                if is_visual_tab_active:
                    self.update_visualizations(self.current_data)
                    self.text_update_counter += 1
                    if self.text_update_counter >= 5:
                        self.update_data_display(self.current_data)
                        self.text_update_counter = 0

                digital_changes = self.data_parser.check_digital_changes(controller_data)
                if self._controller_mapping_active and digital_changes:
                    pressed_button = None
                    # Check regular buttons first
                    if digital_changes.get('buttons'):
                        pressed_button = next(iter(digital_changes['buttons']))
                    # Check d-pad if no regular button was pressed
                    elif digital_changes.get('dpad'):
                        # The d-pad reports directions like 'up', 'down', etc.
                        # We need to create a unique name for mapping purposes.
                        pressed_button = f"dpad_{digital_changes['dpad']}"

                    if pressed_button:
                        self.handle_controller_press_for_mapping(pressed_button)
                elif digital_changes:
                    self.udp_manager.send_digital_changes(digital_changes)

        except queue.Empty:
            # This is expected when no new data is available
            pass
        except Exception as e:
            print(f'Polling error: {e}')
            
        if self.is_running:
            self.after(self.polling_rate, self.poll_controller)

    def check_digital_changes(self, new_data):
        """Check if digital inputs (buttons, d-pad) have changed since last check"""
        return self.data_parser.check_digital_changes(new_data)

    def set_profile_lightbar_and_reload(self, r, g, b):
        """Sets the lightbar color in the GUI. Hammerspoon is now independent."""
        # Set the color in the GUI
        if hasattr(self, 'lightbar_tab_modular'):
            self.lightbar_tab_modular.set_lightbar_color(r=r, g=g, b=b)
        
        # The python script no longer needs to force-reload Hammerspoon.
        # This was causing errors and is no longer necessary with the new efficient Lua script.
        print("Profile lightbar set in GUI. Hammerspoon will update on the next app focus change.")

    # --- Modular Callbacks ---
    def update_visualizations(self, data):
        """Update matplotlib visualizations with parsed data"""
        self.visualization_tab_modular.update_visualizations(data)
        if hasattr(self, 'rumble_tab_modular'):
            self.rumble_tab_modular.check_tactile_feedback(data['l2']['raw'], data['r2']['raw'])

    def update_data_display(self, data):
        self.visualization_tab_modular.update_data_display(data)

    def export_data(self):
        self.visualization_tab_modular._export_data()

    def export_json(self):
        self.visualization_tab_modular._export_json()

    def set_neutral_orientation(self, event=None):
        self.visualization_tab_modular._set_neutral_orientation(event)

    def update_alpha(self, value):
        self.alpha = float(value)
        if hasattr(self, 'visualization_tab_modular'):
            self.visualization_tab_modular.set_sensor_fusion_parameters(self.alpha, self.gyro_sensitivity, self.damping_factor)

    def update_sensitivity(self, value):
        self.gyro_sensitivity = float(value)
        if hasattr(self, 'visualization_tab_modular'):
            self.visualization_tab_modular.set_sensor_fusion_parameters(self.alpha, self.gyro_sensitivity, self.damping_factor)

    def update_damping(self, value):
        self.damping_factor = float(value)
        if hasattr(self, 'visualization_tab_modular'):
            self.visualization_tab_modular.set_sensor_fusion_parameters(self.alpha, self.gyro_sensitivity, self.damping_factor)

    def update_polling(self, value):
        self.polling_rate = int(value)

    def toggle_axis_lock(self, axis):
        self.visualization_tab_modular._toggle_axis_lock(axis)

    def set_rumble_simple(self, left_rumble=0, right_rumble=0):
        report = [0x05, 0xFF, 0x04, 0x00, left_rumble, right_rumble, 0, 0, 0] + [0]*23
        self.h.write(bytes(report))

    def set_rumble_0x11(self, left_rumble=0, right_rumble=0, r=0, g=0, b=0):
        report = [0x11, 0xc0, 0x20, 0xf3, 0xf3, 0x00, 0x00, right_rumble, left_rumble, r, g, b] + [0]*66
        self.h.write(bytes(report))

    def trigger_tactile_feedback(self, trigger):
        if hasattr(self, 'rumble_tab_modular'):
            rumble_settings = self.rumble_tab_modular.get_tactile_settings()
            if trigger == "L2":
                self.set_rumble_simple(rumble_settings['intensity'], 0)
            else:
                self.set_rumble_simple(0, rumble_settings['intensity'])
            self.after(rumble_settings['duration'], self.stop_tactile_feedback)

    def stop_tactile_feedback(self):
            self.set_rumble_simple(0, 0)

    # --- Mouse Control Logic (REMOVED) ---

    # --- Mapping Flow Logic ---

    def start_controller_mapping(self):
        if self._key_capture_active: return
        self._controller_mapping_active = True
        self.mapping_config_frame.info_label.config(text="Press any button on your controller to begin mapping...", fg="#007ACC")

    def handle_controller_press_for_mapping(self, button_name):
        self._controller_mapping_active = False
        self.start_key_capture(button_name, from_ui=False)

    def start_key_capture(self, btn, from_ui=True):
        if self._key_capture_active: return
            
        self._key_capture_active = True
        self._key_capture_btn = btn
        self._captured_mods = {}
        self._captured_key = None

        if self._highlighted_button:
            self.mapping_config_frame.set_button_highlight(self._highlighted_button, False)
        self.mapping_config_frame.set_button_highlight(btn, True)
        self._highlighted_button = btn
        
        info_label = self.mapping_config_frame.info_label
        button_label = self.mapping_config_frame.BUTTON_LABELS[btn]
        
        if from_ui:
            info_label.config(text=f"Press a key for '{button_label}'... (Esc to cancel)", fg="#1976D2")
        else:
            info_label.config(text=f"Waiting for key for '{button_label}'...", fg="#007ACC")
        
        self.focus_set()
        self.bind('<KeyPress>', self._on_key_press)
        self.bind('<KeyRelease>', self._on_key_release)

    def _on_key_press(self, event):
        keysym = event.keysym.lower()
        MODS = ['control_l', 'control_r', 'alt_l', 'alt_r', 'shift_l', 'shift_r', 'meta_l', 'meta_r', 'command_l', 'command_r', 'option_l', 'option_r']
        if keysym in MODS:
            if 'control' in keysym: self._captured_mods['ctrl'] = True
            elif 'alt' in keysym or 'option' in keysym: self._captured_mods['alt'] = True
            elif 'shift' in keysym: self._captured_mods['shift'] = True
            elif 'meta' in keysym or 'command' in keysym: self._captured_mods['cmd'] = True
        elif keysym == 'escape':
            self._cancel_key_capture()
        else:
            self._captured_key = keysym
            self._finish_key_capture()

    def _on_key_release(self, event):
        keysym = event.keysym.lower()
        if 'control' in keysym: self._captured_mods['ctrl'] = False
        elif 'alt' in keysym or 'option' in keysym: self._captured_mods['alt'] = False
        elif 'shift' in keysym: self._captured_mods['shift'] = False
        elif 'meta' in keysym or 'command' in keysym: self._captured_mods['cmd'] = False

    def _finish_key_capture(self):
        # --- PRE-CONDITION CHECK ---
        # Ensure a profile is selected before attempting to save a mapping.
        if not self.mapping_config_frame.active_profile_name:
            messagebox.showwarning("No Profile Selected", "Please select or create a profile before mapping a key.")
            self._cancel_key_capture() # Cancel to cleanup highlights and bindings
            return
            
        btn = self._key_capture_btn
        profile = self.mapping_config_frame.active_profile_name
        section = "dpad" if btn.startswith('dpad_') else "buttons"
        mapping_key = btn.replace('dpad_', '') if section == "dpad" else btn
        
        profile_section = self.mapping_config_frame.mappings.setdefault(profile, {}).setdefault(section, {})
        profile_section[mapping_key] = {'modifiers': self._captured_mods.copy(), 'key': self._captured_key}
        
        info_label = self.mapping_config_frame.info_label
        mod_symbols = {'cmd': '⌘', 'shift': '⇧', 'alt': '⌥', 'ctrl': '⌃'}
        mod_text = ''.join([mod_symbols[m] for m in ['cmd', 'shift', 'alt', 'ctrl'] if self._captured_mods.get(m)])
        key_name = f"{mod_text}{self._captured_key}"
        info_label.config(text=f"Mapped '{self.mapping_config_frame.BUTTON_LABELS[btn]}' to '{key_name}'!", fg="#388E3C")
        
        self.mapping_config_frame.update_button_colors()
        self.mapping_config_frame.save_mappings()
        self._cleanup_key_capture()

    def _cancel_key_capture(self):
        self.mapping_config_frame.info_label.config(text="Key mapping cancelled.", fg="#D32F2F")
        self._cleanup_key_capture()

    def _cleanup_key_capture(self):
        if self._highlighted_button:
            self.mapping_config_frame.set_button_highlight(self._highlighted_button, False)
            self._highlighted_button = None

        self.unbind('<KeyPress>')
        self.unbind('<KeyRelease>')
        self._key_capture_active = False
        self._key_capture_btn = None
        self.after(2000, lambda: self.mapping_config_frame.info_label.config(text="Click a button to map. Double-click to edit.", fg="white"))
        self.focus_set() # Return focus to main window