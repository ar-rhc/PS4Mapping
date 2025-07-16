#
# hid_control_ui.py - DualShock 4 Lightbar Control UI
#
# This script provides a simple UI to control the DualShock 4 lightbar color using tkinter.
# The UI is organized with tabs; the first tab is for lightbar RGB control using sliders.
#
# TODO: In the future, add an RGB triangle selector for more intuitive color picking.
#
# Usage:
#   1. Make sure you have the 'hid' Python package installed (pip install hid).
#   2. Connect your PS4 controller via USB.
#   3. Run this script: python hid_control_ui.py
#
# The script currently supports lightbar color control. Rumble and other features can be added in future tabs.
#
import tkinter as tk
from tkinter import ttk, messagebox
import hid
import time
import json
import socket
import os
import threading
import queue
from PIL import Image, ImageTk, ImageDraw
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkmacosx import Button
import pystray

VENDOR_ID = 1356
PRODUCT_ID = 2508
SETTINGS_FILE = "ds4_settings.json"

# Output report for lightbar and rumble (USB, report ID 0x05, 32 bytes)
def set_lightbar_and_rumble(h, r, g, b, left_rumble=0, right_rumble=0):
    report = [0x05, 0xFF, 0x04, 0x00, left_rumble, right_rumble, r, g, b] + [0]*23
    h.write(bytes(report))

# --- MappingConfigFrame (refactored from mapping_config.py) ---
class MappingConfigFrame(tk.Frame):
    BUTTONS = {
        'square': (394, 105),
        'cross': (437, 136),
        'circle': (474, 103),
        'triangle': (437, 64),
        'l1': (169, 34),
        'r1': (424, 28),
        'l2': (162, 8),
        'r2': (431, 4),
        'share': (221, 47),
        'options': (388, 46),
        'l3': (229, 156),
        'r3': (370, 156),
        'ps': (299, 192),
        'touchpad': (329, 264),
        'dpad_up': (164, 73),
        'dpad_down': (162, 144),
        'dpad_left': (124, 100),
        'dpad_right': (195, 99)
    }
    BUTTON_LABELS = {
        'square': '□', 'cross': '×', 'circle': '○', 'triangle': '△',
        'l1': 'L1', 'r1': 'R1', 'l2': 'L2', 'r2': 'R2',
        'share': 'Share', 'options': 'Options',
        'l3': 'L3', 'r3': 'R3', 'ps': 'PS', 'touchpad': 'TP',
        'dpad_up': '↑', 'dpad_down': '↓', 'dpad_left': '←', 'dpad_right': '→'
    }
    MAPPING_FILE = os.path.join(os.path.dirname(__file__), "../ds4_mapping.json")
    EXPORT_LUA_FILE = "/Users/alex/.hammerspoon/controller.lua"
    PS4_IMAGE = os.path.join(os.path.dirname(__file__), "../assets/ps4.png")

    def __init__(self, parent):
        super().__init__(parent)
        self.mappings = self.load_mappings()
        self.active_profile_name = "Default"  # Keep track of the selected profile
        self.button_widgets = {}
        self.key_labels = {}
        self.create_visual_ui()
        self.populate_profile_listbox()  # Populate the list on startup
        self.update_button_colors()

    def create_visual_ui(self):
        # Create the main two-column layout
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill='both', expand=True)

        # --- Canvas on the Left ---
        self.canvas = tk.Canvas(main_frame, width=950, height=700, bg='white', highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)

        # --- Profile List Panel on the Right ---
        profile_panel = tk.Frame(main_frame, width=250, bg='#222')
        profile_panel.pack(side='right', fill='y', padx=(0, 5), pady=5)
        profile_panel.pack_propagate(False)

        tk.Label(profile_panel, text="App Profiles", font=("Arial", 16, "bold"), bg='#222', fg='white').pack(pady=10)

        # Listbox for profile selection (darker bg, black text)
        self.profile_listbox = tk.Listbox(profile_panel, font=("Arial", 12), activestyle='dotbox', selectbackground='#1976D2', selectforeground='white', bg='#333', fg='white', highlightbackground='#222', highlightcolor='#222')
        self.profile_listbox.pack(fill='both', expand=True, padx=10, pady=(0, 5))
        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_listbox_select)

        # Add/Delete buttons at the bottom of the profile panel
        profile_controls = tk.Frame(profile_panel, bg='#222')
        profile_controls.pack(side='bottom', fill='x', pady=5)
        Button(profile_controls, text="+ Add", command=self.add_profile, bg='#444', fg='white').pack(side='left', expand=True, padx=5)
        Button(profile_controls, text="- Delete", command=self.delete_profile, bg='#444', fg='white').pack(side='right', expand=True, padx=5)

        # Load and display controller image with scaling
        try:
            img = Image.open(self.PS4_IMAGE).convert('RGBA')
            bg = Image.new('RGBA', img.size, (255,255,255,255))
            img = Image.alpha_composite(bg, img)
            
            # Scale the image to fit the larger canvas (approximately 1.5x scale)
            scale_factor = 1.5
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.ps4_img = ImageTk.PhotoImage(img)
            # Center the image in the canvas
            canvas_width = 950
            canvas_height = 700
            img_x = (canvas_width - new_width) // 2
            img_y = (canvas_height - new_height) // 2
            self.canvas.create_image(img_x, img_y, anchor='nw', image=self.ps4_img)
            
            # Scale button positions to match the resized image
            self.scaled_buttons = {}
            for btn, (x, y) in self.BUTTONS.items():
                scaled_x = img_x + int(x * scale_factor)
                scaled_y = img_y + int(y * scale_factor)
                self.scaled_buttons[btn] = (scaled_x, scaled_y)
                
        except Exception as e:
            self.ps4_img = None
            self.canvas.create_text(475, 350, text="[PS4 image not found]", font=("Arial", 24), fill="red")
            # Fallback button positions for when image is not found
            self.scaled_buttons = self.BUTTONS.copy()
        
        # Overlay buttons using scaled positions
        for btn, (x, y) in self.scaled_buttons.items():
            w = Button(
                self,
                text=self.BUTTON_LABELS[btn],
                width=60,
                height=30,
                font=("Arial", 11, "bold"),
                fg="white",
                bg="#808080",
                activebackground="#808080",
                activeforeground="white",
                highlightthickness=0,
                borderwidth=0
            )
            self.button_widgets[btn] = w
            self.canvas.create_window(x, y, window=w)

            # Bind single and double click events
            w.bind('<Button-1>', lambda e, b=btn: self.start_key_capture(b))
            w.bind('<Double-Button-1>', lambda e, b=btn: self.edit_mapping(b))

            # Create key display label below the button (manual width, no width param on Label)
            key_label = tk.Label(
                self,
                text="",  # Will be updated in update_button_colors
                font=("Arial", 10, "bold"),  # Larger font
                fg="white",  # White text for better contrast
                bg="#808080",  # Light grey background
                height=1,  # Single line height
                relief="flat",
                anchor="center"
            )
            self.key_labels[btn] = key_label
            # Position label directly below the button (no gap), set width to 40px
            self.canvas.create_window(x, y + 22, window=key_label, width=50)
        
        # Save & Export button - positioned in bottom right
        self.save_btn = Button(self, text="Save & Export", command=self.save_and_export, bg="#808080", fg="white", font=("Arial", 12, "bold"), activebackground="#808080", activeforeground="white", highlightthickness=0, borderwidth=0)
        self.canvas.create_window(850, 650, window=self.save_btn)
        
        # Info label - positioned at bottom center
        self.info_label = tk.Label(self, text="Click a button to map. Green = mapped, gray = unmapped.", font=("Arial", 10, "bold"), fg="black", bg="white")
        self.canvas.create_window(475, 680, window=self.info_label)

    def edit_mapping(self, btn):
        active_profile = self.active_profile_name if hasattr(self, 'active_profile_name') else 'Default'
        if active_profile not in self.mappings:
            self.mappings[active_profile] = {"buttons": {}, "dpad": {}}
        
        # Determine which section to use
        if btn.startswith('dpad_'):
            direction = btn.replace('dpad_', '')
            section = "dpad"
            mapping_key = direction
        else:
            section = "buttons"
            mapping_key = btn
        
        top = tk.Toplevel(self)
        top.title(f"Map {self.BUTTON_LABELS[btn]}")
        top.configure(bg="#222")
        tk.Label(top, text=f"Map {self.BUTTON_LABELS[btn]} to:", font=("Arial", 12, "bold"), fg="white", bg="#222").pack(pady=5)
        mods = {'ctrl': tk.BooleanVar(), 'opt': tk.BooleanVar(), 'shift': tk.BooleanVar(), 'cmd': tk.BooleanVar()}
        mod_frame = tk.Frame(top, bg="#222")
        mod_frame.pack(pady=5)
        for m in mods:
            # Use proper labels for macOS
            label_text = "Opt" if m == "opt" else m.capitalize()
            tk.Checkbutton(
                mod_frame,
                text=label_text,
                variable=mods[m],
                font=("Arial", 10, "bold"),
                fg="white",
                bg="#222",
                selectcolor="#444",
                activebackground="#222",
                activeforeground="white",
                highlightthickness=0,
                borderwidth=0
            ).pack(side='left', padx=5)
        key_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=key_var, font=("Arial", 12, "bold"), width=10, fg="white", bg="black", state="readonly", readonlybackground="black")
        entry.pack(pady=5)
        entry.focus_set()
        def on_key(event):
            key_var.set(event.keysym)
        entry.bind('<Key>', on_key)
        
        # Load existing mapping
        if mapping_key in self.mappings[active_profile].get(section, {}):
            m = self.mappings[active_profile][section][mapping_key]
            for k in mods:
                mods[k].set(m.get('modifiers', {}).get(k, False))
            key_var.set(m.get('key', ''))
        
        def save():
            if section not in self.mappings[active_profile]:
                self.mappings[active_profile][section] = {}
            self.mappings[active_profile][section][mapping_key] = {
                'modifiers': {k: mods[k].get() for k in mods},
                'key': key_var.get()
            }
            self.update_button_colors()
            self.save_mappings()
            top.destroy()
        
        Button(top, text="Save", command=save, bg="#808080", fg="white", font=("Arial", 10, "bold"), activebackground="#808080", activeforeground="white", highlightthickness=0, borderwidth=0).pack(pady=5)
        
        def unmap():
            if section in self.mappings[active_profile] and mapping_key in self.mappings[active_profile][section]:
                del self.mappings[active_profile][section][mapping_key]
                self.update_button_colors()
                self.save_mappings()
            top.destroy()
        
        Button(top, text="Unmap", command=unmap, bg="#D32F2F", fg="white", font=("Arial", 10, "bold"), activebackground="#D32F2F", activeforeground="white", highlightthickness=0, borderwidth=0).pack(pady=5)
        Button(top, text="Cancel", command=top.destroy, bg="#808080", fg="white", font=("Arial", 10, "bold"), activebackground="#808080", activeforeground="white", highlightthickness=0, borderwidth=0).pack(pady=5)

    def update_button_colors(self):
        # Get active profile
        active_profile = self.active_profile_name if hasattr(self, 'active_profile_name') else 'Default'
        profile_map = self.mappings.get(active_profile, {"buttons": {}, "dpad": {}})
        
        for btn, w in self.button_widgets.items():
            # Determine which section to look in
            if btn.startswith('dpad_'):
                direction = btn.replace('dpad_', '')
                mapping = profile_map.get("dpad", {}).get(direction)
            else:
                mapping = profile_map.get("buttons", {}).get(btn)
            
            if mapping and mapping.get('key'):
                # Button is mapped
                w.config(bg="#4CAF50", activebackground="#4CAF50")  # Green
                # Update key label
                key_label = self.key_labels[btn]
                key_text = mapping.get('key', '')
                # Add modifier indicators
                mods = mapping.get('modifiers', {})
                mod_indicators = []
                if mods.get('ctrl'): mod_indicators.append('Ctrl')
                if mods.get('opt'): mod_indicators.append('Opt')
                if mods.get('shift'): mod_indicators.append('Shift')
                if mods.get('cmd'): mod_indicators.append('Cmd')
                if mod_indicators:
                    key_text = '+'.join(mod_indicators) + '+' + key_text
                # Truncate if too long
                if len(key_text) > 8:
                    key_text = key_text[:6] + '..'
                key_label.config(text=key_text, fg="white", bg="#4CAF50")
            else:
                # Button is not mapped
                w.config(bg="#808080", activebackground="#808080")  # Gray
                # Clear key label
                key_label = self.key_labels[btn]
                key_label.config(text="", fg="white", bg="#808080")

    def migrate_mappings_structure(self, old_mappings):
        """Migrate old flat mapping structure to new nested structure"""
        new_mappings = {}
        
        # Check if this is the old structure where button names are at the top level
        has_top_level_buttons = False
        for key in old_mappings.keys():
            if key in self.BUTTONS or key.startswith('dpad_'):
                has_top_level_buttons = True
                break
        
        if has_top_level_buttons:
            # This is the old structure with button names at the top level
            # Create a Default profile and move all mappings there
            new_mappings["Default"] = {
                "buttons": {},
                "dpad": {}
            }
            
            for key, mapping in old_mappings.items():
                if key.startswith('dpad_'):
                    # Convert dpad_up -> up, dpad_down -> down, etc.
                    direction = key.replace('dpad_', '')
                    new_mappings["Default"]["dpad"][direction] = mapping
                elif key in self.BUTTONS:
                    # Regular button
                    new_mappings["Default"]["buttons"][key] = mapping
                elif isinstance(mapping, dict) and ("buttons" in mapping or "dpad" in mapping):
                    # This is already a profile with the new structure
                    new_mappings[key] = mapping
                else:
                    # This might be a profile name with old structure
                    new_mappings[key] = {"buttons": {}, "dpad": {}}
        else:
            # This is already the new structure or profiles with old structure
            for profile_name, profile_data in old_mappings.items():
                if not isinstance(profile_data, dict):
                    continue
                    
                # Check if it already has the new structure
                if "buttons" in profile_data or "dpad" in profile_data:
                    new_mappings[profile_name] = profile_data
                else:
                    # This is a profile with old flat structure
                    new_mappings[profile_name] = {
                        "buttons": {},
                        "dpad": {}
                    }
                    
                    for key, mapping in profile_data.items():
                        if key.startswith('dpad_'):
                            # Convert dpad_up -> up, dpad_down -> down, etc.
                            direction = key.replace('dpad_', '')
                            new_mappings[profile_name]["dpad"][direction] = mapping
                        else:
                            # Regular button
                            new_mappings[profile_name]["buttons"][key] = mapping
        
        return new_mappings

    def load_mappings(self):
        """Load mappings from JSON file with structure migration"""
        try:
            if os.path.exists(self.MAPPING_FILE):
                with open(self.MAPPING_FILE, 'r') as f:
                    mappings = json.load(f)
                
                # Check if migration is needed (old flat structure)
                needs_migration = False
                for profile_name, profile_data in mappings.items():
                    if isinstance(profile_data, dict):
                        # Check if it has the new nested structure
                        if "buttons" not in profile_data and "dpad" not in profile_data:
                            needs_migration = True
                            break
                
                if needs_migration:
                    print("Migrating mapping structure to new nested format...")
                    mappings = self.migrate_mappings_structure(mappings)
                    # Save the migrated structure
                    self.save_mappings_to_file(mappings)
                
                return mappings
            else:
                # Create default structure
                return {"Default": {"buttons": {}, "dpad": {}}}
        except Exception as e:
            print(f"Error loading mappings: {e}")
            return {"Default": {"buttons": {}, "dpad": {}}}

    def save_mappings_to_file(self, mappings):
        """Save mappings to JSON file"""
        try:
            with open(self.MAPPING_FILE, 'w') as f:
                json.dump(mappings, f, indent=2)
        except Exception as e:
            print(f"Error saving mappings: {e}")

    def save_mappings(self):
        """Save current mappings to file"""
        self.save_mappings_to_file(self.mappings)

    def save_and_export(self):
        """Save mappings and export to Lua, then reload Hammerspoon using CLI"""
        self.save_mappings()
        self.export_to_lua()
        
        # Try to reload using Hammerspoon CLI
        if self.reload_hammerspoon_config():
            print("✅ Export completed! Hammerspoon reloaded via CLI.")
            self.info_label.config(text="Mappings saved and exported! Hammerspoon reloaded.", fg="#4CAF50")
        else:
            print("✅ Export completed! Hammerspoon will auto-reload via file watcher.")
            self.info_label.config(text="Mappings saved and exported! Auto-reload triggered.", fg="#4CAF50")
        
        self.after(3000, lambda: self.info_label.config(text="Click a button to map. Green = mapped, gray = unmapped.", fg="black"))

    def reload_hammerspoon_config(self):
        """Reload Hammerspoon configuration using CLI"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':  # macOS only
                # Try to reload using Hammerspoon CLI
                result = subprocess.run(['hs', '-c', 'hs.reload()'], 
                                       capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print("✅ Hammerspoon reloaded via CLI")
                    return True
                else:
                    print(f"⚠️  CLI reload failed: {result.stderr}")
                    return False
            else:
                print("⚠️  Hammerspoon CLI only supported on macOS")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  CLI reload timed out")
            return False
        except FileNotFoundError:
            print("⚠️  Hammerspoon CLI not found - will rely on file watcher")
            return False
        except Exception as e:
            print(f"⚠️  Error with CLI reload: {e}")
            return False

    def export_to_lua(self):
        try:
            # Create the complete controller.lua file content
            lua_content = '''-- Hammerspoon Controller Mapper
-- Receives DS4 data from Python script via UDP and maps it to key presses.

local json = require("hs.json")
local eventtap = require("hs.eventtap")

local controller = {}

-- ##################################################################
-- MAPPINGS GENERATED BY DS4 MAPPING UI
-- ##################################################################
controller.mappings = {
'''
            
            def lua_table_block(items, indent=0):
                """Helper to format a Lua table block with commas between items, but not after the last one"""
                lines = []
                for i, (k, v) in enumerate(items):
                    comma = ',' if i < len(items) - 1 else ''
                    lines.append(' ' * indent + f'{k} = {v}{comma}')
                return '\n'.join(lines)
            
            # Add mappings
            profile_names = [k for k in self.mappings.keys() if isinstance(self.mappings[k], dict) and "buttons" in self.mappings[k]]
            for pi, profile_name in enumerate(profile_names):
                profile_data = self.mappings[profile_name]
                lua_content += f'    ["{profile_name}"] = {{\n'
                
                # Buttons
                button_items = []
                for btn, mapping in profile_data.get("buttons", {}).items():
                    key = mapping.get('key', '')
                    if key:
                        mods = mapping.get('modifiers', {})
                        # Convert 'opt' to 'alt' for Hammerspoon compatibility
                        modlist = []
                        for mod in ['cmd','ctrl','opt','shift']:
                            if mods.get(mod):
                                # Convert 'opt' to 'alt' for Hammerspoon
                                lua_mod = 'alt' if mod == 'opt' else mod
                                modlist.append(lua_mod)
                        mods_lua = '{' + ','.join(f'"{mod}"' for mod in modlist) + '}'
                        button_items.append((btn, f'{{modifiers={mods_lua}, key="{key}"}}'))
                
                lua_content += '        buttons = {\n'
                lua_content += lua_table_block(button_items, indent=12)
                if button_items:
                    lua_content += '\n'
                lua_content += '        },\n'
                
                # Dpad
                dpad_items = []
                for direction, mapping in profile_data.get("dpad", {}).items():
                    key = mapping.get('key', '')
                    if key:
                        mods = mapping.get('modifiers', {})
                        # Convert 'opt' to 'alt' for Hammerspoon compatibility
                        modlist = []
                        for mod in ['cmd','ctrl','opt','shift']:
                            if mods.get(mod):
                                # Convert 'opt' to 'alt' for Hammerspoon
                                lua_mod = 'alt' if mod == 'opt' else mod
                                modlist.append(lua_mod)
                        mods_lua = '{' + ','.join(f'"{mod}"' for mod in modlist) + '}'
                        dpad_items.append((direction, f'{{modifiers={mods_lua}, key="{key}"}}'))
                
                lua_content += '        dpad = {\n'
                lua_content += lua_table_block(dpad_items, indent=12)
                if dpad_items:
                    lua_content += '\n'
                lua_content += '        }\n'
                lua_content += '    }'
                if pi < len(profile_names) - 1:
                    lua_content += ',\n'
                else:
                    lua_content += '\n'
            
            lua_content += '''}

-- ##################################################################

local keycodes = require("hs.keycodes").map

-- Key translation table for user-friendly names
local keyTranslations = {
    ["backspace"] = "delete",
    ["enter"] = "return",
    ["esc"] = "escape"
    -- Add more as needed
}

-- Helper function to translate keys
local function translateKey(key)
    key = key:lower()
    if keycodes[key] then
        return key
    elseif keyTranslations[key] then
        return keyTranslations[key]
    else
        return key
    end
end

-- State tracking to prevent continuous key presses (profile-specific)
local previousState = {
    buttons = {},  -- Will be profile-specific: buttons[profile][button]
    dpad = {},     -- Will be profile-specific: dpad[profile]
    sticks = { left = {}, right = {} }
}

-- UDP socket to listen for data from Python
local udpSocket = nil
local UDP_PORT = 12345 -- Must match the port in your Python script

-- ## Core Mapping Logic ## --

function controller.processData(data)
    local status, decoded = pcall(json.decode, data)
    if not status then
        return
    end

    -- Get the active application name for profile selection
    local activeApp = hs.application.frontmostApplication()
    local appName = activeApp and activeApp:name() or "Default"
    
    -- Select the appropriate profile
    local profile = controller.mappings[appName] or controller.mappings["Default"] or {buttons = {}, dpad = {}}
    
    -- Initialize profile-specific state tracking
    if not previousState.buttons[appName] then
        previousState.buttons[appName] = {}
    end
    if not previousState.dpad[appName] then
        previousState.dpad[appName] = {}
    end
    
    -- TRUE EVENT-BASED PROCESSING
    -- Only process if there's an actual event (button press, d-pad change, stick movement)
    local hasEvent = false
    local events = {}

    -- 1. Check for button events (only process if buttons changed)
    for button, mapping in pairs(profile.buttons) do
        local isPressed = decoded.buttons[button]
        local wasPressed = previousState.buttons[appName][button] or false

        -- Rising edge detection (false -> true transition)
        if isPressed and not wasPressed then
            hasEvent = true
            table.insert(events, {type = "button", button = button, mapping = mapping})
        end
        previousState.buttons[appName][button] = isPressed
    end

    -- 2. Check for D-Pad events (only process if d-pad changed)
    local currentDpad = decoded.dpad
    local previousDpad = previousState.dpad[appName].current or "none"

    if currentDpad ~= previousDpad then
        hasEvent = true
        local dpadToDirection = {
            ["up"] = "up", ["down"] = "down", ["left"] = "left", ["right"] = "right",
            ["ne"] = "ne", ["se"] = "se", ["sw"] = "sw", ["nw"] = "nw"
        }
        -- Trigger on button RELEASE (when going from a direction back to "none")
        if currentDpad == "none" and previousDpad ~= "none" then
            local direction = dpadToDirection[previousDpad]
            if direction and profile.dpad[direction] then
                table.insert(events, {type = "dpad", direction = direction, mapping = profile.dpad[direction]})
            end
        end
        previousState.dpad[appName].current = currentDpad
    end

    -- 4. Process all events at once (only if there are events)
    if hasEvent then
        for _, event in ipairs(events) do
            local keydesc = ""
            local modifiers = {}
            local key = nil

            -- Support new mapping format: {modifiers=..., key=...}
            if event.mapping and type(event.mapping) == "table" and event.mapping.key then
                modifiers = event.mapping.modifiers or {}
                key = translateKey(event.mapping.key)  -- Translate the key
                keydesc = (next(modifiers) and table.concat(modifiers, "-") .. "-" or "") .. key
            else
                key = translateKey(event.mapping or event.key)  -- Translate the key
                keydesc = tostring(key)
            end

            if event.type == "button" then
                print("🎮 Button pressed: " .. event.button .. " -> Key: " .. keydesc)
            elseif event.type == "dpad" then
                print("🎮 D-pad pressed: " .. event.direction .. " -> Key: " .. keydesc)
            end

            -- Send the key event
            hs.eventtap.keyStroke(modifiers, key)
        end
    end
end


-- ## Socket Control ## --

function controller:start()
    if udpSocket then
        print("Controller mapper already running.")
        return
    end

    print("Starting controller mapper...")
    udpSocket = hs.socket.udp.new()
    udpSocket:setCallback(controller.processData)

    local success = udpSocket:listen(UDP_PORT)
    if success then
        udpSocket:receive()
        hs.notify.new({title="Controller Active", informativeText="DS4 mapping is ON."}):send()
    else
        hs.notify.new({title="Controller Error", informativeText="Could not listen on port " .. UDP_PORT}):send()
        udpSocket = nil
    end
end

function controller:stop()
    if udpSocket then
        print("Stopping controller mapper...")
        udpSocket:close()
        udpSocket = nil
        hs.notify.new({title="Controller Inactive", informativeText="DS4 mapping is OFF."}):send()
    else
        print("Controller mapper is not running.")
    end
end

-- Start automatically
controller:start()

return controller
'''
            
            # Write the complete file
            with open(self.EXPORT_LUA_FILE, 'w') as f:
                f.write(lua_content)
            
            print(f"Updated Hammerspoon controller file: {self.EXPORT_LUA_FILE}")
            
        except Exception as e:
            print(f"Error exporting to Lua: {e}")
            try:
                # Create backup file with new structure
                with open("controller_mapping_backup.lua", 'w') as f:
                    f.write('-- Auto-generated DS4 to key mapping (new structure)\n')
                    f.write('controller.mappings = {\n')
                    for profile_name, profile_data in self.mappings.items():
                        if not isinstance(profile_data, dict) or "buttons" not in profile_data:
                            continue
                        f.write(f'    ["{profile_name}"] = {{\n')
                        f.write('        buttons = {\n')
                        for btn, mapping in profile_data.get("buttons", {}).items():
                            key = mapping.get('key', '')
                            if key:
                                mods = mapping.get('modifiers', {})
                                modlist = [mod for mod in ['cmd','ctrl','alt','shift'] if mods.get(mod)]
                                mods_lua = '{' + ','.join(f'"{mod}"' for mod in modlist) + '}'
                                f.write(f'            {btn} = {{modifiers={mods_lua}, key="{key}"}},\n')
                        f.write('        },\n')
                        f.write('        dpad = {\n')
                        for direction, mapping in profile_data.get("dpad", {}).items():
                            key = mapping.get('key', '')
                            if key:
                                mods = mapping.get('modifiers', {})
                                modlist = [mod for mod in ['cmd','ctrl','alt','shift'] if mods.get(mod)]
                                mods_lua = '{' + ','.join(f'"{mod}"' for mod in modlist) + '}'
                                f.write(f'            {direction} = {{modifiers={mods_lua}, key="{key}"}},\n')
                        f.write('        },\n')
                        f.write('    },\n')
                    f.write('}\n')
                print("Created backup mapping file: controller_mapping_backup.lua")
            except Exception as e2:
                print(f"Error creating backup: {e2}")

    # --- Add these new methods inside the MappingConfigFrame class ---
    def start_key_capture(self, btn):
        """Initiates the key capture mode for a specific button."""
        # Only allow one key capture at a time
        if hasattr(self, '_key_capture_active') and self._key_capture_active:
            return
        self._key_capture_active = True
        self._captured_mods = {'ctrl': False, 'opt': False, 'shift': False, 'cmd': False}
        self._captured_key = None
        self._key_capture_btn = btn
        self.info_label.config(text=f"Press a key combination for '{self.BUTTON_LABELS[btn]}'... (Press Esc to cancel)", fg="#1976D2")
        # Bind events to the root window to capture keys globally
        self.winfo_toplevel().focus_set()
        self.winfo_toplevel().bind_all('<KeyPress>', self._on_key_press)
        self.winfo_toplevel().bind_all('<KeyRelease>', self._on_key_release)
        # Store the active profile at the time of capture
        self._key_capture_profile = self.active_profile_name if hasattr(self, 'active_profile_name') else 'Default'

    def _on_key_press(self, event):
        """Handles key press events during capture mode."""
        # Map macOS modifier keys properly
        if event.keysym in ('Control_L', 'Control_R'):
            self._captured_mods['ctrl'] = True
        elif event.keysym in ('Option_L', 'Option_R', 'Alt_L', 'Alt_R'):
            self._captured_mods['opt'] = True  # Use 'opt' for macOS Option key
        elif event.keysym in ('Shift_L', 'Shift_R'):
            self._captured_mods['shift'] = True
        elif event.keysym in ('Meta_L', 'Meta_R', 'Command', 'Command_L', 'Command_R'):
            self._captured_mods['cmd'] = True
        elif event.keysym == 'Escape':
            self._cancel_key_capture()
        else:
            # Only set the key if it's not a pure modifier
            if event.keysym not in ('Control_L', 'Control_R', 'Option_L', 'Option_R', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Meta_L', 'Meta_R', 'Command', 'Command_L', 'Command_R'):
                # Handle Option key combinations properly
                if self._captured_mods.get('opt', False):
                    # When Option is held, we need to get the base key
                    # Use a mapping approach since keycode ranges might vary on macOS
                    
                    # Direct mapping for common Option+key combinations that produce special chars
                    option_key_map = {
                        'ssharp': 's',           # Option+S
                        'partialderivative': 'd', # Option+D  
                        'integral': 'b',         # Option+B
                        'mu': 'm',               # Option+M
                        'dead_acute': 'e',       # Option+E
                        'registered': 'r',       # Option+R
                        'trademark': '2',        # Option+2
                        'cent': '4',             # Option+4
                        'infinity': '5',         # Option+5
                        'section': '6',          # Option+6
                        'paragraph': '7',        # Option+7
                        'bullet': '8',           # Option+8
                        'ordfeminine': '9',      # Option+9
                        'masculine': '0',        # Option+0
                        'ae': "'",               # Option+'
                        'oe': 'q',               # Option+Q
                        'sum': 'w',              # Option+W
                        'dead_grave': '`',       # Option+`
                        'asciitilde': 'n',       # Option+N
                        'guillemotleft': '\\',   # Option+\
                        'guillemotright': '|',   # Option+|
                    }
                    
                    keysym_lower = event.keysym.lower()
                    if keysym_lower in option_key_map:
                        self._captured_key = option_key_map[keysym_lower]
                    elif len(event.keysym) == 1 and event.keysym.isalpha():
                        # Single letter, use directly
                        self._captured_key = event.keysym.lower()
                    elif len(event.keysym) == 1 and event.keysym.isdigit():
                        # Single digit, use directly
                        self._captured_key = event.keysym
                    else:
                        # For unmapped special characters, just use the keysym
                        self._captured_key = event.keysym.lower()
                else:
                    # No Option key, use keysym directly
                    self._captured_key = event.keysym.lower()
                
                self._finish_key_capture()

    def _on_key_release(self, event):
        """Handles key release events during capture mode."""
        # This function is primarily to handle cases where only modifiers are pressed and released
        # without a final key, though our current logic finalizes on the first non-modifier press.
        # It can be expanded if needed.
        pass

    def _finish_key_capture(self):
        """Finalizes the key capture, saves the mapping, and cleans up."""
        btn = self._key_capture_btn
        profile = self._key_capture_profile if hasattr(self, '_key_capture_profile') else (self.active_profile_name if hasattr(self, 'active_profile_name') else 'Default')
        if profile not in self.mappings:
            self.mappings[profile] = {"buttons": {}, "dpad": {}}
        
        # Determine which section to use
        if btn.startswith('dpad_'):
            direction = btn.replace('dpad_', '')
            section = "dpad"
            mapping_key = direction
        else:
            section = "buttons"
            mapping_key = btn
        
        if section not in self.mappings[profile]:
            self.mappings[profile][section] = {}
        
        self.mappings[profile][section][mapping_key] = {
            'modifiers': self._captured_mods.copy(),
            'key': self._captured_key
        }
        self.info_label.config(text=f"Mapped '{self.BUTTON_LABELS[btn]}' to a new key!", fg="#388E3C")
        self.update_button_colors()
        self.save_mappings()
        self._cleanup_key_capture()

    def _cancel_key_capture(self):
        """Cancels the key capture mode."""
        self.info_label.config(text="Key mapping cancelled.", fg="#D32F2F")
        self._cleanup_key_capture()

    def _cleanup_key_capture(self):
        """Unbinds events and resets state after capture is finished or cancelled."""
        if hasattr(self, '_key_capture_active') and self._key_capture_active:
            self._key_capture_active = False
            self.winfo_toplevel().unbind_all('<KeyPress>')
            self.winfo_toplevel().unbind_all('<KeyRelease>')
            self.after(2000, lambda: self.info_label.config(text="Click a button to map. Double-click to edit.", fg="black"))

    def add_profile(self):
        import subprocess
        import platform
        from tkinter import simpledialog, messagebox
        app_names = []
        if platform.system() == 'Darwin':
            try:
                script = 'tell application "System Events" to get the name of every process whose background only is false'
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                if result.returncode == 0:
                    app_names = [name.strip() for name in result.stdout.split(',') if name.strip()]
            except Exception as e:
                print(f"Error getting app list: {e}")
        # Show dialog with app list and custom entry
        dialog = tk.Toplevel(self)
        dialog.title("Add Profile")
        tk.Label(dialog, text="Select an app or enter a custom name:", font=("Arial", 12)).pack(pady=5)
        listbox = tk.Listbox(dialog, font=("Arial", 11), height=10, width=30)
        for name in app_names:
            listbox.insert(tk.END, name)
        listbox.pack(padx=10, pady=5)
        entry = tk.Entry(dialog, font=("Arial", 11), width=30)
        entry.pack(padx=10, pady=5)
        entry.focus_set()
        def on_ok():
            name = entry.get().strip() or (listbox.get(listbox.curselection()[0]) if listbox.curselection() else None)
            if not name:
                messagebox.showerror("Error", "Please select or enter a profile name.", parent=dialog)
                return
            if name in self.mappings:
                messagebox.showerror("Error", f"Profile '{name}' already exists.", parent=dialog)
                return
            self.mappings[name] = {"buttons": {}, "dpad": {}}
            self.active_profile_name = name
            self.populate_profile_listbox() # Refresh the list
            self.update_button_colors()
            dialog.destroy()
        ok_btn = Button(dialog, text="Add", command=on_ok)
        ok_btn.pack(side='left', padx=10, pady=10)
        cancel_btn = Button(dialog, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side='right', padx=10, pady=10)
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

    def delete_profile(self):
        from tkinter import messagebox
        profile_to_delete = self.active_profile_name
        if not profile_to_delete or profile_to_delete == "Default":
            messagebox.showerror("Error", "Cannot delete the 'Default' profile.")
            return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the '{profile_to_delete}' profile?"):
            del self.mappings[profile_to_delete]
            self.active_profile_name = "Default" # Fallback to Default
            self.populate_profile_listbox() # Refresh the list
            self.update_button_colors()
            print(f"Profile '{profile_to_delete}' deleted.")

    def populate_profile_listbox(self):
        """Clears and redraws the list of profiles in the side panel listbox."""
        self.profile_listbox.delete(0, tk.END)
        # Ensure "Default" is always first
        profiles = sorted(self.mappings.keys(), key=lambda p: (p != 'Default', p.lower()))
        for profile_name in profiles:
            self.profile_listbox.insert(tk.END, profile_name)
        # Reselect the currently active profile
        if self.active_profile_name in profiles:
            idx = profiles.index(self.active_profile_name)
            self.profile_listbox.selection_set(idx)
            self.profile_listbox.activate(idx)
            self.profile_listbox.see(idx)

    def on_profile_listbox_select(self, event=None):
        """Handles selection change in the profile listbox."""
        selection_indices = self.profile_listbox.curselection()
        if selection_indices:
            selected_profile = self.profile_listbox.get(selection_indices[0])
            if self.active_profile_name != selected_profile:
                self.active_profile_name = selected_profile
                self.update_button_colors() # Update the view to reflect the new profile

# --- End MappingConfigFrame ---

class DS4ControlUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DualShock 4 HID Control UI (⌘W to hide)")
        
        # --- Set Initial Window Position (Centered) ---
        window_width = 1600
        window_height = 900

        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate coordinates for the top-left corner of the window
        x_coord = (screen_width // 2) - (window_width // 2)
        y_coord = (screen_height // 2) - (window_height // 2)

        # Set the geometry to size and position the window
        self.geometry(f'{window_width}x{window_height}+{x_coord}+{y_coord}')
        # ---------------------------------------------
        
        # Hide window initially - will show when user clicks tray icon
        self.withdraw()
        
        self.h = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
        
        # --- Main Thread Polling Support ---
        self.text_update_counter = 0
        self.is_running = True
        # -------------------------
        
        # --- UDP Socket Setup for Hammerspoon Communication ---
        self.udp_host = '127.0.0.1'  # Localhost
        self.udp_port = 12345        # Port for Hammerspoon to listen on
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"Broadcasting controller data to UDP {self.udp_host}:{self.udp_port}")
        # -----------------------------------------------------
        
        # --- Optimization Support ---
        self.text_update_counter = 0
        self.last_poll_time = 0
        # ---------------------------
        
        # Load settings from file
        self.load_settings()
        
        # Initialize orientation tracking with sensor fusion
        self.orientation = {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        self.last_time = time.time()
        
        # Store current controller data for export
        self.current_data = None
        
        # Create menu bar first
        self.create_menu()
        
        self.create_widgets()
        
        # Bind the 'c' key to set custom neutral position
        self.bind('<c>', self.set_neutral_orientation)
        
        # Bind Cmd+W to hide window to tray
        self.bind('<Command-w>', self.hide_window)
        self.bind('<Command-W>', self.hide_window)  # Also bind uppercase
        
        # Initialize tray flags
        self.show_window_flag = False
        self.quit_flag = False
        
        # Create the system tray icon
        self.create_tray_icon()
        
        # Start the tray flag checker
        self.check_tray_flags()
        
        # Start the main thread polling
        self.poll_controller()
        
        # Show startup notification
        print("DS4 Controller UI started. Check the system tray for the 🎮 icon.")

    def create_widgets(self):
        self.tab_control = ttk.Notebook(self)
       
        # --- Add Mapping Config tab FIRST (as default) ---
        self.mapping_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.mapping_tab, text='Mapping Config')
        self.mapping_config_frame = MappingConfigFrame(self.mapping_tab)
        self.mapping_config_frame.pack(fill='both', expand=True)
        # --- End Mapping Config tab ---
       
        # Live Visualization tab
        self.visual_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.visual_tab, text='Live Visualization')
        # Settings tab
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text='Settings')
        # Lightbar tab
        self.lightbar_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.lightbar_tab, text='Lightbar')
        # Rumble tab
        self.rumble_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.rumble_tab, text='Rumble')
        
        self.tab_control.pack(expand=1, fill='both')
        self.create_lightbar_tab()
        self.create_visualization_tab()
        self.create_settings_tab()
        self.create_rumble_tab()
        
        # Update UI elements with loaded settings
        self.update_ui_from_settings()

    def create_lightbar_tab(self):
        frame = self.lightbar_tab
        tk.Label(frame, text="Red").pack()
        self.red = tk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.red.pack(fill='x')
        tk.Label(frame, text="Green").pack()
        self.green = tk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.green.pack(fill='x')
        tk.Label(frame, text="Blue").pack()
        self.blue = tk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.blue.pack(fill='x')
        set_btn = Button(frame, text="Set Lightbar Color", command=self.set_lightbar)
        set_btn.pack(pady=10)

    def create_settings_tab(self):
        """Create the settings tab with adjustable parameters"""
        frame = self.settings_tab
        
        # Title
        title_label = tk.Label(frame, text="Sensor Fusion Settings", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Complementary Filter Alpha (0.8-0.98)
        alpha_frame = tk.Frame(frame)
        alpha_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(alpha_frame, text="Filter Responsiveness (Alpha):").pack(anchor='w')
        self.alpha_slider = tk.Scale(alpha_frame, from_=0.80, to=0.98, resolution=0.01, 
                                   orient=tk.HORIZONTAL, variable=tk.DoubleVar(value=self.alpha),
                                   command=self.update_alpha)
        self.alpha_slider.pack(fill='x')
        self.alpha_label = tk.Label(alpha_frame, text=f"Current: {self.alpha:.2f} (Higher = Smoother, Lower = More Responsive)")
        self.alpha_label.pack(anchor='w')
        
        # Gyro Sensitivity (200-1000)
        sensitivity_frame = tk.Frame(frame)
        sensitivity_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(sensitivity_frame, text="Gyro Sensitivity:").pack(anchor='w')
        self.sensitivity_slider = tk.Scale(sensitivity_frame, from_=200, to=1000, resolution=10,
                                         orient=tk.HORIZONTAL, variable=tk.DoubleVar(value=self.gyro_sensitivity),
                                         command=self.update_sensitivity)
        self.sensitivity_slider.pack(fill='x')
        self.sensitivity_label = tk.Label(sensitivity_frame, text=f"Current: {self.gyro_sensitivity:.0f} (Lower = More Sensitive)")
        self.sensitivity_label.pack(anchor='w')
        
        # Damping Factor (0.90-0.99)
        damping_frame = tk.Frame(frame)
        damping_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(damping_frame, text="Neutral Return Damping:").pack(anchor='w')
        self.damping_slider = tk.Scale(damping_frame, from_=0.90, to=0.99, resolution=0.01,
                                     orient=tk.HORIZONTAL, variable=tk.DoubleVar(value=self.damping_factor),
                                     command=self.update_damping)
        self.damping_slider.pack(fill='x')
        self.damping_label = tk.Label(damping_frame, text=f"Current: {self.damping_factor:.2f} (Higher = Slower Return to Neutral)")
        self.damping_label.pack(anchor='w')
        
        # Polling Rate (10-100ms)
        polling_frame = tk.Frame(frame)
        polling_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(polling_frame, text="Polling Rate (ms):").pack(anchor='w')
        self.polling_slider = tk.Scale(polling_frame, from_=10, to=100, resolution=5,
                                     orient=tk.HORIZONTAL, variable=tk.IntVar(value=self.polling_rate),
                                     command=self.update_polling)
        self.polling_slider.pack(fill='x')
        self.polling_label = tk.Label(polling_frame, text=f"Current: {self.polling_rate}ms ({1000//self.polling_rate} Hz)")
        self.polling_label.pack(anchor='w')
        
        # Reset button
        reset_btn = Button(frame, text="Reset to Defaults", command=self.reset_settings)
        reset_btn.pack(pady=20)
        
        # Save Settings button
        save_btn = Button(frame, text="Save Settings", command=self.save_settings)
        save_btn.pack(pady=10)

    def create_visualization_tab(self):
        frame = self.visual_tab
        # Set up matplotlib figure with 3D support
        from mpl_toolkits.mplot3d import Axes3D
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
        circle = plt.Circle((0, 0), 1, fill=False, color='gray', linestyle='--')
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
        
        # 3D triangle for gyro orientation
        self.gyro_triangle = None
        self.ax_gyro.text2D(0.02, 0.98, 'Controller Orientation', transform=self.ax_gyro.transAxes, fontsize=10, verticalalignment='top')
        
        # Raw gyro data ball
        self.gyro_ball, = self.ax_gyro.plot([0], [0], [0], 'ro', markersize=15, label='Raw Gyro Data')
        
        # Raw data display text
        self.gyro_text = self.ax_gyro.text2D(0.02, 0.02, 'Gyro: X=0 Y=0 Z=0', transform=self.ax_gyro.transAxes, fontsize=9, verticalalignment='bottom', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Axis Locks Section (moved to gyro panel)
        lock_frame = tk.Frame(frame)
        lock_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        lock_title = tk.Label(lock_frame, text="Axis Locks:", font=("Arial", 10, "bold"))
        lock_title.pack(side=tk.LEFT, padx=(0, 10))
        
        # Roll lock button
        self.roll_lock_btn = Button(lock_frame, text="Roll (X)", width=8, 
                                     command=lambda: self.toggle_axis_lock('roll'))
        self.roll_lock_btn.pack(side=tk.LEFT, padx=2)
        
        # Pitch lock button
        self.pitch_lock_btn = Button(lock_frame, text="Pitch (Y)", width=8,
                                      command=lambda: self.toggle_axis_lock('pitch'))
        self.pitch_lock_btn.pack(side=tk.LEFT, padx=2)
        
        # Yaw lock button
        self.yaw_lock_btn = Button(lock_frame, text="Yaw (Z)", width=8,
                                     command=lambda: self.toggle_axis_lock('yaw'))
        self.yaw_lock_btn.pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.lock_status_label = tk.Label(lock_frame, text="No axis locked", fg="green", font=("Arial", 9))
        self.lock_status_label.pack(side=tk.RIGHT, padx=10)
        
        self.fig.tight_layout()
        
        # Create data display panel
        data_frame = tk.Frame(frame)
        data_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Data display title
        data_title = tk.Label(data_frame, text="Controller Data Export", font=("Arial", 12, "bold"))
        data_title.pack(pady=(0, 5))
        
        # Create scrollable text area for data display
        text_frame = tk.Frame(data_frame)
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
        export_frame = tk.Frame(data_frame)
        export_frame.pack(pady=5)
        
        export_btn = Button(export_frame, text="Export Text", command=self.export_data)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        json_export_btn = Button(export_frame, text="Export JSON", command=self.export_json)
        json_export_btn.pack(side=tk.LEFT, padx=5)
        
        # Embed matplotlib in tkinter (left side)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill='both', expand=1)
        
        # Bind 'c' key to set neutral orientation
        self.bind('<c>', self.set_neutral_orientation)

    def poll_controller(self):
        """
        Reads from the controller on the main thread and conditionally updates the UI.
        This avoids the GIL-related crash from the background thread.
        """
        try:
            # hid.read() is now safely on the main thread
            report = self.h.read(64)
            
            if report:
                # Parse and process the data every time
                controller_data = self.parse_controller_data(report)
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
                
                # Run fusion math regardless, so orientation data is current for UDP
                self.update_orientation_with_fusion(
                    gyro['x'], gyro['y'], gyro['z'], 
                    accel['x'], accel['y'], accel['z'],
                    update_triangle=is_visual_tab_active # Only update 3D model if tab is visible
                )

                # Store data for UDP and export
                self.current_data = controller_data
                self.current_data['timestamp'] = time.time()
                self.current_data['orientation'] = self.orientation.copy()
                if hasattr(self, 'axis_locks'):
                    self.current_data['axis_locks'] = self.axis_locks.copy()
                
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
                    self.canvas.draw()
                
                # Send data to Hammerspoon via UDP
                    try:
                        message = json.dumps(self.current_data).encode('utf-8')
                        self.udp_socket.sendto(message, (self.udp_host, self.udp_port))
                    except Exception as send_error:
                        print(f"UDP send error: {send_error}")
                
        except hid.HIDException as e:
            print(f"Controller disconnected or HID error: {e}")
            self.quit_application() # Cleanly quit if controller is lost
            return # Stop polling
        except Exception as e:
            print(f'Polling error: {e}')
            
        # Schedule the next poll
        self.after(self.polling_rate, self.poll_controller)

    def parse_controller_data(self, report):
        """Parse all controller data from HID report"""
        import struct
        
        data = {}
        
        # Analog sticks (normalize to -1 to 1 range)
        data['left_stick'] = {
            'x': (report[1] - 128) / 128,
            'y': (report[2] - 128) / 128,
            'raw_x': report[1],
            'raw_y': report[2]
        }
        data['right_stick'] = {
            'x': (report[3] - 128) / 128,
            'y': (report[4] - 128) / 128,
            'raw_x': report[3],
            'raw_y': report[4]
        }
        
        # Triggers
        data['l2'] = {
            'value': report[8] / 255.0,
            'raw': report[8]
        }
        data['r2'] = {
            'value': report[9] / 255.0,
            'raw': report[9]
        }
        
        # Buttons (byte 5 and 6)
        button_byte1 = report[5]
        button_byte2 = report[6]
        
        data['buttons'] = {
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
        
        # D-pad (byte 5, bits 0-3)
        dpad = button_byte1 & 0x0F
        # Correct DS4 D-pad mapping: 8=none, 0=up, 1=ne, 2=right, 3=se, 4=down, 5=sw, 6=left, 7=nw
        dpad_states = {
            8: 'none',
            0: 'up',
            1: 'ne',    # north-east (up-right)
            2: 'right', 
            3: 'se',    # south-east (down-right)
            4: 'down',
            5: 'sw',    # south-west (down-left)
            6: 'left',
            7: 'nw'     # north-west (up-left)
        }
        data['dpad'] = dpad_states[dpad] or 'none'
        data['dpad_raw'] = dpad  # Add raw value for debugging
        
        # PS button and touchpad (byte 7)
        data['ps_button'] = bool(report[7] & 0x01)
        data['touchpad_pressed'] = bool(report[7] & 0x02)
        
        # Gyro (X, Y, Z)
        data['gyro'] = {
            'x': struct.unpack('<h', bytes(report[13:15]))[0],
            'y': struct.unpack('<h', bytes(report[15:17]))[0],
            'z': struct.unpack('<h', bytes(report[17:19]))[0]
        }
        
        # Accelerometer (X, Y, Z)
        data['accelerometer'] = {
            'x': struct.unpack('<h', bytes(report[19:21]))[0],
            'y': struct.unpack('<h', bytes(report[21:23]))[0],
            'z': struct.unpack('<h', bytes(report[23:25]))[0]
        }
        
        # Touchpad data (if available)
        if len(report) > 35:
            data['touchpad'] = {
                'active': bool(report[35] & 0x80),
                'id': report[35] & 0x7F,
                'x': struct.unpack('<h', bytes(report[36:38]))[0],
                'y': struct.unpack('<h', bytes(report[38:40]))[0]
            }
        else:
            data['touchpad'] = {
                'active': False,
                'id': 0,
                'x': 0,
                'y': 0
            }
        
        # Battery level (if available)
        if len(report) > 30:
            data['battery'] = report[30] & 0x0F
        else:
            data['battery'] = 0
        
        return data

    def update_visualizations(self, data):
        """Update matplotlib visualizations with parsed data"""
        # Update analog sticks
        self.stick_left.set_data([data['left_stick']['x']], [data['left_stick']['y']])
        self.stick_right.set_data([data['right_stick']['x']], [data['right_stick']['y']])
        
        # Update triggers
        self.l2_bar[0].set_height(data['l2']['value'] * 2)
        self.r2_bar[0].set_height(data['r2']['value'] * 2)
        
        # Update trigger visualization in rumble tab
        if hasattr(self, 'trigger_canvas'):
            self.draw_trigger_visualization(data['l2']['raw'], data['r2']['raw'])
        
        # Check for tactile feedback
        self.check_tactile_feedback(data['l2']['raw'], data['r2']['raw'])
        
        # Update gyro visualization
        gyro = data['gyro']
        accel = data['accelerometer']
        
        self.gyro_ball.set_data([gyro['x']], [gyro['y']])
        self.gyro_ball.set_3d_properties([gyro['z']])
        self.gyro_text.set_text(f'Gyro: X={gyro["x"]} Y={gyro["y"]} Z={gyro["z"]}\nAccel: X={accel["x"]} Y={accel["y"]} Z={accel["z"]}')
        
        # Update orientation with sensor fusion
        self.update_orientation_with_fusion(gyro['x'], gyro['y'], gyro['z'], 
                                          accel['x'], accel['y'], accel['z'])

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

OTHER:
Battery:   {data['battery']}/15
"""
        
        # Update text widget
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(1.0, display_text)

    def export_data(self):
        """Export current controller data to text file"""
        try:
            filename = f"../exports/ds4_data_export_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(self.data_text.get(1.0, tk.END))
            print(f"Data exported to {filename}")
        except Exception as e:
            print(f"Error exporting data: {e}")

    def export_json(self):
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

    def set_neutral_orientation(self, event=None):
        """Captures the current orientation to use as the zero-offset."""
        print("Setting new neutral orientation.")
        # Store the current angle as the new offset
        self.orientation_offset['roll'] = self.orientation['roll']
        self.orientation_offset['pitch'] = self.orientation['pitch']
        self.orientation_offset['yaw'] = self.orientation['yaw']
        print(f"Offset captured: {self.orientation_offset}")

    def update_alpha(self, value):
        """Update the complementary filter alpha value"""
        self.alpha = float(value)
        self.alpha_label.config(text=f"Current: {self.alpha:.2f} (Higher = Smoother, Lower = More Responsive)")

    def update_sensitivity(self, value):
        """Update the gyro sensitivity value"""
        self.gyro_sensitivity = float(value)
        self.sensitivity_label.config(text=f"Current: {self.gyro_sensitivity:.0f} (Lower = More Sensitive)")

    def update_damping(self, value):
        """Update the damping factor value"""
        self.damping_factor = float(value)
        self.damping_label.config(text=f"Current: {self.damping_factor:.2f} (Higher = Slower Return to Neutral)")

    def update_polling(self, value):
        """Update the polling rate value"""
        self.polling_rate = int(value)
        self.polling_label.config(text=f"Current: {self.polling_rate}ms ({1000//self.polling_rate} Hz)")

    def reset_settings(self):
        """Reset all settings to default values"""
        self.alpha = 0.85
        self.gyro_sensitivity = 500.0
        self.damping_factor = 0.95
        self.polling_rate = 50
        self.orientation_offset = {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        self.axis_locks = {'roll': False, 'pitch': False, 'yaw': False}
        self.locked_axis = None
        
        # Update sliders
        self.alpha_slider.set(self.alpha)
        self.sensitivity_slider.set(self.gyro_sensitivity)
        self.damping_slider.set(self.damping_factor)
        self.polling_slider.set(self.polling_rate)
        
        # Update labels
        self.update_alpha(self.alpha)
        self.update_sensitivity(self.gyro_sensitivity)
        self.update_damping(self.damping_factor)
        self.update_polling(self.polling_rate)
        
        # Update lock buttons
        self.update_lock_button_colors()
        self.lock_status_label.config(text="No axis locked", fg="green")

    def load_settings(self):
        """Load settings from JSON file"""
        default_settings = {
            'alpha': 0.85,
            'gyro_sensitivity': 500.0,
            'damping_factor': 0.95,
            'polling_rate': 50,
            'orientation_offset': {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0},
            'axis_locks': {'roll': False, 'pitch': False, 'yaw': False},
            'locked_axis': None,
            'tactile_enabled': False,
            'threshold1_enabled': True,
            'threshold1_value': 64,
            'threshold2_enabled': True,
            'threshold2_value': 128,
            'threshold3_enabled': True,
            'threshold3_value': 192,
            'tactile_duration': 50,
            'tactile_intensity': 255
        }
        
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults to handle missing keys
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
            else:
                settings = default_settings
                print(f"Settings file not found. Using defaults.")
        except Exception as e:
            print(f"Error loading settings: {e}. Using defaults.")
            settings = default_settings
        
        # Apply loaded settings
        self.alpha = settings['alpha']
        self.gyro_sensitivity = settings['gyro_sensitivity']
        self.damping_factor = settings['damping_factor']
        self.polling_rate = settings['polling_rate']
        self.orientation_offset = settings['orientation_offset']
        self.axis_locks = settings['axis_locks']
        self.locked_axis = settings['locked_axis']
        self.tactile_enabled = settings['tactile_enabled']
        self.threshold1_enabled = settings['threshold1_enabled']
        self.threshold1_value = settings['threshold1_value']
        self.threshold2_enabled = settings['threshold2_enabled']
        self.threshold2_value = settings['threshold2_value']
        self.threshold3_enabled = settings['threshold3_enabled']
        self.threshold3_value = settings['threshold3_value']
        self.tactile_duration = settings['tactile_duration']
        self.tactile_intensity = settings['tactile_intensity']
        
        # Initialize previous trigger values for threshold crossing detection
        self.prev_l2_value = 0
        self.prev_r2_value = 0
        
        # Initialize rumble trigger tracking
        self.l2_last_rumble_threshold = None
        self.r2_last_rumble_threshold = None
        self.hysteresis_margin = 2
        
        print(f"Settings loaded: {settings}")
        
        # Update UI elements after loading settings
        self.update_ui_from_settings()

    def save_settings(self):
        """Save current settings to JSON file"""
        settings = {
            'alpha': self.alpha,
            'gyro_sensitivity': self.gyro_sensitivity,
            'damping_factor': self.damping_factor,
            'polling_rate': self.polling_rate,
            'orientation_offset': self.orientation_offset,
            'axis_locks': self.axis_locks,
            'locked_axis': self.locked_axis,
            'tactile_enabled': self.tactile_enabled,
            'threshold1_enabled': self.threshold1_enabled,
            'threshold1_value': self.threshold1_value,
            'threshold2_enabled': self.threshold2_enabled,
            'threshold2_value': self.threshold2_value,
            'threshold3_enabled': self.threshold3_enabled,
            'threshold3_value': self.threshold3_value,
            'tactile_duration': self.tactile_duration,
            'tactile_intensity': self.tactile_intensity
        }
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"Settings saved to {SETTINGS_FILE}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_ui_from_settings(self):
        """Update UI elements to reflect loaded settings"""
        # Update sliders if they exist (widgets might not be created yet)
        if hasattr(self, 'alpha_slider'):
            self.alpha_slider.set(self.alpha)
            self.sensitivity_slider.set(self.gyro_sensitivity)
            self.damping_slider.set(self.damping_factor)
            self.polling_slider.set(self.polling_rate)
            
            # Update labels
            self.update_alpha(self.alpha)
            self.update_sensitivity(self.gyro_sensitivity)
            self.update_damping(self.damping_factor)
            self.update_polling(self.polling_rate)
        
        # Update lock buttons if they exist
        if hasattr(self, 'roll_lock_btn'):
            self.update_lock_button_colors()
            if self.locked_axis:
                self.lock_status_label.config(text=f"{self.locked_axis.capitalize()} axis locked", fg="red")
            else:
                self.lock_status_label.config(text="No axis locked", fg="green")
        
        # Update tactile feedback controls if they exist
        if hasattr(self, 'tactile_var'):
            self.tactile_var.set(self.tactile_enabled)
        if hasattr(self, 'thresh1_enabled_var'):
            self.thresh1_enabled_var.set(self.threshold1_enabled)
        if hasattr(self, 'thresh2_enabled_var'):
            self.thresh2_enabled_var.set(self.threshold2_enabled)
        if hasattr(self, 'thresh3_enabled_var'):
            self.thresh3_enabled_var.set(self.threshold3_enabled)
        if hasattr(self, 'threshold1_slider'):
            self.threshold1_slider.set(self.threshold1_value)
            self.threshold1_label.config(text=f"Value: {self.threshold1_value}")
        if hasattr(self, 'threshold2_slider'):
            self.threshold2_slider.set(self.threshold2_value)
            self.threshold2_label.config(text=f"Value: {self.threshold2_value}")
        if hasattr(self, 'threshold3_slider'):
            self.threshold3_slider.set(self.threshold3_value)
            self.threshold3_label.config(text=f"Value: {self.threshold3_value}")
        if hasattr(self, 'duration_slider'):
            self.duration_slider.set(self.tactile_duration)
            self.duration_label.config(text=f"Value: {self.tactile_duration}ms")
        if hasattr(self, 'intensity_slider'):
            self.intensity_slider.set(self.tactile_intensity)
            self.intensity_label.config(text=f"Value: {self.tactile_intensity}")

    def toggle_axis_lock(self, axis):
        """Toggle axis lock - only one axis can be locked at a time"""
        if self.axis_locks[axis]:
            # Unlock this axis
            self.axis_locks[axis] = False
            self.locked_axis = None
            self.lock_status_label.config(text="No axis locked", fg="green")
        else:
            # Lock this axis and unlock others
            for ax in ['roll', 'pitch', 'yaw']:
                self.axis_locks[ax] = (ax == axis)
            self.locked_axis = axis if axis else None
            self.lock_status_label.config(text=f"{axis.capitalize()} axis locked", fg="red")
        
        # Update button colors
        self.update_lock_button_colors()

    def update_lock_button_colors(self):
        """Update button colors to show locked state"""
        # Reset all buttons to default
        self.roll_lock_btn.config(bg="SystemButtonFace", fg="black")
        self.pitch_lock_btn.config(bg="SystemButtonFace", fg="black")
        self.yaw_lock_btn.config(bg="SystemButtonFace", fg="black")
        
        # Highlight locked axis button
        if self.locked_axis == 'roll':
            self.roll_lock_btn.config(bg="red", fg="white")
        elif self.locked_axis == 'pitch':
            self.pitch_lock_btn.config(bg="red", fg="white")
        elif self.locked_axis == 'yaw':
            self.yaw_lock_btn.config(bg="red", fg="white")

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
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
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
        if hasattr(self, 'lock_indicator') and self.lock_indicator is not None:
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

    def set_lightbar(self):
        r = self.red.get()
        g = self.green.get()
        b = self.blue.get()
        set_lightbar_and_rumble(self.h, r, g, b)

    def create_rumble_tab(self):
        """Create the rumble control tab"""
        frame = self.rumble_tab
        
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
                                    command=self.update_strong_rumble, length=300)
        self.strong_slider.pack(padx=10, pady=5)
        self.strong_label = tk.Label(strong_frame, text="Intensity: 0")
        self.strong_label.pack(pady=5)
        
        # Weak motor (right) control
        weak_frame = tk.LabelFrame(left_frame, text="Weak Motor (Right)", font=("Arial", 12, "bold"))
        weak_frame.pack(fill=tk.X, pady=5)
        
        self.weak_slider = tk.Scale(weak_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                  command=self.update_weak_rumble, length=300)
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
            btn = Button(preset_frame, text=name, width=15,
                          command=lambda s=strong, w=weak: self.set_preset_rumble(s, w))
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
        apply_btn = Button(advanced_frame, text="Apply Rumble", command=self.apply_rumble, 
                            bg="green", fg="white", font=("Arial", 10, "bold"))
        apply_btn.pack(pady=5)
        
        # Test button
        test_btn = Button(advanced_frame, text="Test Rumble (255, 255)", command=self.test_rumble,
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
                      command=self.toggle_tactile_feedback, font=("Arial", 10)).pack(side=tk.LEFT)
        
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
                      command=self.update_threshold1_enabled).pack(side=tk.LEFT)
        tk.Label(thresh1_header, text="Threshold 1 (Low):", font=("Arial", 9)).pack(side=tk.LEFT)
        self.threshold1_slider = tk.Scale(thresh1_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                        command=self.update_threshold1_value, length=150)
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
                      command=self.update_threshold2_enabled).pack(side=tk.LEFT)
        tk.Label(thresh2_header, text="Threshold 2 (Med):", font=("Arial", 9)).pack(side=tk.LEFT)
        self.threshold2_slider = tk.Scale(thresh2_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                        command=self.update_threshold2_value, length=150)
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
                      command=self.update_threshold3_enabled).pack(side=tk.LEFT)
        tk.Label(thresh3_header, text="Threshold 3 (High):", font=("Arial", 9)).pack(side=tk.LEFT)
        self.threshold3_slider = tk.Scale(thresh3_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                        command=self.update_threshold3_value, length=150)
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
                                      command=self.update_tactile_duration, length=150)
        self.duration_slider.set(self.tactile_duration)
        self.duration_slider.pack(fill=tk.X)
        self.duration_label = tk.Label(duration_frame, text=f"Value: {self.tactile_duration}ms", font=("Arial", 8))
        self.duration_label.pack(anchor='w')
        
        # Intensity control
        intensity_frame = tk.Frame(settings_frame)
        intensity_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        tk.Label(intensity_frame, text="Intensity:", font=("Arial", 9)).pack(anchor='w')
        self.intensity_slider = tk.Scale(intensity_frame, from_=50, to=255, orient=tk.HORIZONTAL,
                                       command=self.update_tactile_intensity, length=150)
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

    def update_strong_rumble(self, value):
        """Update strong motor rumble value"""
        self.strong_rumble = int(value)
        self.strong_label.config(text=f"Intensity: {self.strong_rumble}")
        # Don't auto-apply, let user use Apply button

    def update_weak_rumble(self, value):
        """Update weak motor rumble value"""
        self.weak_rumble = int(value)
        self.weak_label.config(text=f"Intensity: {self.weak_rumble}")
        # Don't auto-apply, let user use Apply button

    def set_preset_rumble(self, strong, weak):
        """Set rumble to preset values"""
        self.strong_slider.set(strong)
        self.weak_slider.set(weak)
        self.strong_rumble = strong
        self.weak_rumble = weak
        self.strong_label.config(text=f"Intensity: {strong}")
        self.weak_label.config(text=f"Intensity: {weak}")
        # Don't auto-apply, let user use Apply button

    def apply_rumble(self):
        """Apply current rumble settings to controller"""
        try:
            if self.report_type.get() == "0x11":
                self.set_rumble_0x11(self.strong_rumble, self.weak_rumble)
            else:
                self.set_rumble_simple(self.strong_rumble, self.weak_rumble)
            
            # Update status
            if self.strong_rumble > 0 or self.weak_rumble > 0:
                self.rumble_status.config(text=f"Rumble: ON (L:{self.strong_rumble}, R:{self.weak_rumble})", fg="green")
            else:
                self.rumble_status.config(text="Rumble: OFF", fg="red")
        except Exception as e:
            print(f"Error applying rumble: {e}")

    def set_rumble_simple(self, left_rumble=0, right_rumble=0):
        """Set rumble using simple 0x05 report"""
        # Output report: [0x05, 0xFF, 0x04, 0x00, left_rumble, right_rumble, r, g, b, ...]
        report = [0x05, 0xFF, 0x04, 0x00, left_rumble, right_rumble, 0, 0, 0] + [0]*23
        self.h.write(bytes(report))

    def set_rumble_0x11(self, left_rumble=0, right_rumble=0, r=0, g=0, b=0):
        """Set rumble using full 0x11 report"""
        # Full output report (USB, 78 bytes, report ID 0x11)
        # Byte 4: 0xf3 enables rumble, 0xf0 disables
        # Byte 7: right/weak rumble, Byte 8: left/strong rumble
        # Byte 9-11: RGB
        report = [0x11, 0xc0, 0x20, 0xf3, 0xf3, 0x00, 0x00, right_rumble, left_rumble, r, g, b] + [0]*66
        self.h.write(bytes(report))

    def test_rumble(self):
        """Test rumble with maximum intensity"""
        try:
            # Test with the working simple format
            self.set_rumble_simple(255, 255)
            
            # Update status
            self.rumble_status.config(text="Test: MAX RUMBLE", fg="blue")
            
            # Reset after 1 second
            self.after(1000, self.reset_test_rumble)
        except Exception as e:
            print(f"Error in test rumble: {e}")

    def reset_test_rumble(self):
        """Reset test rumble and update status"""
        try:
            self.set_rumble_simple(0, 0)
            if self.strong_rumble > 0 or self.weak_rumble > 0:
                self.rumble_status.config(text=f"Rumble: ON (L:{self.strong_rumble}, R:{self.weak_rumble})", fg="green")
            else:
                self.rumble_status.config(text="Rumble: OFF", fg="red")
        except Exception as e:
            print(f"Error resetting test rumble: {e}")

    def toggle_tactile_feedback(self):
        """Toggle tactile feedback on/off"""
        self.tactile_enabled = self.tactile_var.get()
        print(f"Tactile feedback: {'ON' if self.tactile_enabled else 'OFF'}")

    def update_threshold1_enabled(self):
        """Update threshold 1 enabled state"""
        self.threshold1_enabled = self.thresh1_enabled_var.get()
        print(f"Threshold 1 enabled: {self.threshold1_enabled}")

    def update_threshold2_enabled(self):
        """Update threshold 2 enabled state"""
        self.threshold2_enabled = self.thresh2_enabled_var.get()
        print(f"Threshold 2 enabled: {self.threshold2_enabled}")

    def update_threshold3_enabled(self):
        """Update threshold 3 enabled state"""
        self.threshold3_enabled = self.thresh3_enabled_var.get()
        print(f"Threshold 3 enabled: {self.threshold3_enabled}")

    def update_threshold1_value(self, value):
        """Update threshold 1 value"""
        self.threshold1_value = int(value)
        self.threshold1_label.config(text=f"Value: {self.threshold1_value}")

    def update_threshold2_value(self, value):
        """Update threshold 2 value"""
        self.threshold2_value = int(value)
        self.threshold2_label.config(text=f"Value: {self.threshold2_value}")

    def update_threshold3_value(self, value):
        """Update threshold 3 value"""
        self.threshold3_value = int(value)
        self.threshold3_label.config(text=f"Value: {self.threshold3_value}")

    def update_tactile_duration(self, value):
        """Update tactile feedback duration"""
        self.tactile_duration = int(value)
        self.duration_label.config(text=f"Value: {self.tactile_duration}ms")

    def update_tactile_intensity(self, value):
        """Update tactile feedback intensity"""
        self.tactile_intensity = int(value)
        self.intensity_label.config(text=f"Value: {self.tactile_intensity}")

    def draw_trigger_visualization(self, l2_value, r2_value):
        """Draw trigger visualization bars horizontally with three thresholds"""
        self.trigger_canvas.delete("all")
        
        canvas_width = self.trigger_canvas.winfo_width()
        if canvas_width <= 1:  # Canvas not yet sized
            canvas_width = 300
        
        bar_height = 25
        bar_width = (canvas_width - 40) // 2
        y_offset = 20
        
        # L2 bar (blue) - horizontal
        l2_x = 10
        l2_y = y_offset
        l2_fill_width = int((l2_value / 255.0) * bar_width)
        
        # L2 background
        self.trigger_canvas.create_rectangle(l2_x, l2_y, l2_x + bar_width, l2_y + bar_height, 
                                          fill='lightgray', outline='gray')
        # L2 fill
        if l2_fill_width > 0:
            self.trigger_canvas.create_rectangle(l2_x, l2_y, l2_x + l2_fill_width, l2_y + bar_height, 
                                              fill='blue', outline='darkblue')
        
        # L2 threshold lines (vertical) - different colors for each threshold
        if self.threshold1_enabled:
            threshold_x = l2_x + int((self.threshold1_value / 255.0) * bar_width)
            self.trigger_canvas.create_line(threshold_x, l2_y, threshold_x, l2_y + bar_height, 
                                          fill='green', width=2, dash=(3, 3))
        
        if self.threshold2_enabled:
            threshold_x = l2_x + int((self.threshold2_value / 255.0) * bar_width)
            self.trigger_canvas.create_line(threshold_x, l2_y, threshold_x, l2_y + bar_height, 
                                          fill='orange', width=2, dash=(5, 5))
        
        if self.threshold3_enabled:
            threshold_x = l2_x + int((self.threshold3_value / 255.0) * bar_width)
            self.trigger_canvas.create_line(threshold_x, l2_y, threshold_x, l2_y + bar_height, 
                                          fill='red', width=2, dash=(7, 7))
        
        # L2 label
        self.trigger_canvas.create_text(l2_x + bar_width//2, l2_y + bar_height + 15, 
                                      text=f"L2: {l2_value}", font=("Arial", 8))
        
        # R2 bar (red) - horizontal
        r2_x = l2_x + bar_width + 20
        r2_y = y_offset
        r2_fill_width = int((r2_value / 255.0) * bar_width)
        
        # R2 background
        self.trigger_canvas.create_rectangle(r2_x, r2_y, r2_x + bar_width, r2_y + bar_height, 
                                          fill='lightgray', outline='gray')
        # R2 fill
        if r2_fill_width > 0:
            self.trigger_canvas.create_rectangle(r2_x, r2_y, r2_x + r2_fill_width, r2_y + bar_height, 
                                              fill='red', outline='darkred')
        
        # R2 threshold lines (vertical) - different colors for each threshold
        if self.threshold1_enabled:
            threshold_x = r2_x + int((self.threshold1_value / 255.0) * bar_width)
            self.trigger_canvas.create_line(threshold_x, r2_y, threshold_x, r2_y + bar_height, 
                                          fill='green', width=2, dash=(3, 3))
        
        if self.threshold2_enabled:
            threshold_x = r2_x + int((self.threshold2_value / 255.0) * bar_width)
            self.trigger_canvas.create_line(threshold_x, r2_y, threshold_x, r2_y + bar_height, 
                                          fill='orange', width=2, dash=(5, 5))
        
        if self.threshold3_enabled:
            threshold_x = r2_x + int((self.threshold3_value / 255.0) * bar_width)
            self.trigger_canvas.create_line(threshold_x, r2_y, threshold_x, r2_y + bar_height, 
                                          fill='red', width=2, dash=(7, 7))
        
        # R2 label
        self.trigger_canvas.create_text(r2_x + bar_width//2, r2_y + bar_height + 15, 
                                      text=f"R2: {r2_value}", font=("Arial", 8))

    def check_tactile_feedback(self, l2_value, r2_value):
        """Check if triggers cross any enabled thresholds and trigger tactile feedback with hysteresis"""
        if not self.tactile_enabled:
            return
        
        # Check L2 trigger threshold crossings (both up and down)
        if self.threshold1_enabled:
            self.check_threshold_crossing("L2", l2_value, self.prev_l2_value, self.threshold1_value, 1)
        if self.threshold2_enabled:
            self.check_threshold_crossing("L2", l2_value, self.prev_l2_value, self.threshold2_value, 2)
        if self.threshold3_enabled:
            self.check_threshold_crossing("L2", l2_value, self.prev_l2_value, self.threshold3_value, 3)
        
        # Check R2 trigger threshold crossings (both up and down)
        if self.threshold1_enabled:
            self.check_threshold_crossing("R2", r2_value, self.prev_r2_value, self.threshold1_value, 1)
        if self.threshold2_enabled:
            self.check_threshold_crossing("R2", r2_value, self.prev_r2_value, self.threshold2_value, 2)
        if self.threshold3_enabled:
            self.check_threshold_crossing("R2", r2_value, self.prev_r2_value, self.threshold3_value, 3)
        
        # Update previous values for next check
        self.prev_l2_value = l2_value
        self.prev_r2_value = r2_value

    def check_threshold_crossing(self, trigger, current_value, prev_value, threshold_value, threshold_num):
        """Check if trigger crosses threshold in either direction with hysteresis protection"""
        # Determine which trigger's last rumble state to check
        if trigger == "L2":
            last_rumble_threshold = self.l2_last_rumble_threshold
        else:  # R2
            last_rumble_threshold = self.r2_last_rumble_threshold
        
        # Check if we crossed the threshold in either direction
        crossed_up = prev_value < threshold_value and current_value >= threshold_value
        crossed_down = prev_value > threshold_value and current_value <= threshold_value
        
        if crossed_up or crossed_down:
            # Check if we're far enough away from the last rumble threshold
            can_rumble = True
            if last_rumble_threshold is not None and last_rumble_threshold == threshold_value:
                # Only apply hysteresis if we're crossing the same threshold again
                # Check if we've moved at least hysteresis_margin points away from this threshold
                distance_from_threshold = abs(current_value - threshold_value)
                can_rumble = distance_from_threshold >= self.hysteresis_margin
            
            if can_rumble:
                self.trigger_tactile_feedback(trigger)
                # Update the last rumble threshold for this trigger
                if trigger == "L2":
                    self.l2_last_rumble_threshold = threshold_value
                else:  # R2
                    self.r2_last_rumble_threshold = threshold_value

    def trigger_tactile_feedback(self, trigger):
        """Trigger tactile feedback for specified trigger"""
        try:
            # Set rumble based on trigger
            if trigger == "L2":
                # L2 triggers left (strong) motor
                self.set_rumble_simple(self.tactile_intensity, 0)
            else:  # R2
                # R2 triggers right (weak) motor
                self.set_rumble_simple(0, self.tactile_intensity)
            
            # Schedule rumble off after duration
            self.after(self.tactile_duration, self.stop_tactile_feedback)
            
            print(f"Tactile feedback triggered: {trigger} (intensity: {self.tactile_intensity}, duration: {self.tactile_duration}ms)")
            
        except Exception as e:
            print(f"Error triggering tactile feedback: {e}")

    def stop_tactile_feedback(self):
        """Stop tactile feedback rumble"""
        try:
            self.set_rumble_simple(0, 0)
        except Exception as e:
            print(f"Error stopping tactile feedback: {e}")

    def on_closing(self):
        """Clean shutdown of the application"""
        print("Shutting down...")
        
        # Close HID device
        if hasattr(self, 'h'):
            self.h.close()
        
        # Close UDP socket
        if hasattr(self, 'udp_socket'):
            self.udp_socket.close()
        
        self.quit()

    def create_menu(self):
        """Creates the main application menu."""
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="Hide to Tray (⌘W)", command=self.hide_window)
        file_menu.add_command(label="Show/Hide Window", command=self.toggle_window_visibility)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit_application)

    def toggle_window_visibility(self):
        """Toggle window visibility (hide/show)"""
        if self.state() == 'withdrawn':
            self.deiconify()
            self.lift()
        else:
            self.withdraw()

    def quit_application(self):
        """Performs a clean shutdown of the application."""
        print("Quit command received. Shutting down.")
        
        # Stop tray icon first
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                print(f"Error stopping tray icon: {e}")
        
        # Close connections
        self.udp_socket.close()
        self.h.close()
        self.destroy()

    def start_key_capture(self, btn):
        # Only allow one key capture at a time
        if hasattr(self, '_key_capture_active') and self._key_capture_active:
            return
        self._key_capture_active = True
        self._captured_mods = {'ctrl': False, 'opt': False, 'shift': False, 'cmd': False}
        self._captured_key = None
        self._key_capture_btn = btn
        self.info_label.config(text=f"Press a key for {self.BUTTON_LABELS[btn]} (Esc to cancel)", fg="#1976D2")
        self.focus_set()
        self.bind_all('<KeyPress>', self._on_key_press)
        self.bind_all('<KeyRelease>', self._on_key_release)
        # Store the active profile at the time of capture
        self._key_capture_profile = self.active_profile_name if hasattr(self, 'active_profile_name') else 'Default'

    def _on_key_press(self, event):
        # Map macOS modifier keys properly
        if event.keysym in ('Control_L', 'Control_R'):
            self._captured_mods['ctrl'] = True
        elif event.keysym in ('Option_L', 'Option_R', 'Alt_L', 'Alt_R'):
            self._captured_mods['opt'] = True  # Use 'opt' for macOS Option key
        elif event.keysym in ('Shift_L', 'Shift_R'):
            self._captured_mods['shift'] = True
        elif event.keysym in ('Meta_L', 'Meta_R', 'Command', 'Command_L', 'Command_R'):
            self._captured_mods['cmd'] = True
        elif event.keysym == 'Escape':
            self._cancel_key_capture()
            return
        else:
            # Only set the key if it's not a pure modifier
            if event.keysym not in ('Control_L', 'Control_R', 'Option_L', 'Option_R', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Meta_L', 'Meta_R', 'Command', 'Command_L', 'Command_R'):
                # Handle Option key combinations properly
                if self._captured_mods.get('opt', False):
                    # When Option is held, we need to get the base key from keycode
                    # Option+S: event.keysym might be 'ssharp', event.keycode is 115 (for 's')
                    # Option+D: event.keysym might be 'partialderivative', event.keycode is 100 (for 'd')
                    import string
                    
                    # Try to get the base key from keycode first
                    if hasattr(event, 'keycode'):
                        if 65 <= event.keycode <= 90:  # A-Z
                            self._captured_key = chr(event.keycode + 32).lower()  # Convert to lowercase
                        elif 97 <= event.keycode <= 122:  # a-z
                            self._captured_key = chr(event.keycode).lower()
                        elif 48 <= event.keycode <= 57:  # 0-9
                            self._captured_key = chr(event.keycode)
                        else:
                            # For other keys, try to use keysym but clean it up
                            if event.keysym in string.ascii_letters:
                                self._captured_key = event.keysym.lower()
                            else:
                                # Fallback to keysym for special keys
                                self._captured_key = event.keysym
                    else:
                        # Fallback if keycode is not available
                        if event.keysym in string.ascii_letters:
                            self._captured_key = event.keysym.lower()
                        else:
                            self._captured_key = event.keysym
                else:
                    # No Option key, use keysym directly
                    self._captured_key = event.keysym
                
                self._finish_key_capture()

    def _on_key_release(self, event):
        # Update modifier state
        if event.keysym in ('Control_L', 'Control_R'):
            self._captured_mods['ctrl'] = False
        elif event.keysym in ('Option_L', 'Option_R', 'Alt_L', 'Alt_R'):
            self._captured_mods['opt'] = False  # Use 'opt' for macOS Option key
        elif event.keysym in ('Shift_L', 'Shift_R'):
            self._captured_mods['shift'] = False
        elif event.keysym in ('Meta_L', 'Meta_R', 'Command', 'Command_L', 'Command_R'):
            self._captured_mods['cmd'] = False

    def _finish_key_capture(self):
        btn = self._key_capture_btn
        profile = self._key_capture_profile if hasattr(self, '_key_capture_profile') else (self.active_profile_name if hasattr(self, 'active_profile_name') else 'Default')
        if profile not in self.mappings:
            self.mappings[profile] = {"buttons": {}, "dpad": {}}
        
        # Determine which section to use
        if btn.startswith('dpad_'):
            direction = btn.replace('dpad_', '')
            section = "dpad"
            mapping_key = direction
        else:
            section = "buttons"
            mapping_key = btn
        
        if section not in self.mappings[profile]:
            self.mappings[profile][section] = {}
        
        self.mappings[profile][section][mapping_key] = {
            'modifiers': self._captured_mods.copy(),
            'key': self._captured_key
        }
        self.info_label.config(text=f"Mapped '{self.BUTTON_LABELS[btn]}' to a new key!", fg="#388E3C")
        self.update_button_colors()
        self.save_mappings()
        self._cleanup_key_capture()

    def _cancel_key_capture(self):
        self.info_label.config(text="Key mapping cancelled.", fg="#D32F2F")
        self._cleanup_key_capture()

    def _cleanup_key_capture(self):
        self._key_capture_active = False
        self._captured_mods = None
        self._captured_key = None
        self._key_capture_btn = None
        self.unbind_all('<KeyPress>')
        self.unbind_all('<KeyRelease>')
        self.after(2000, lambda: self.info_label.config(text="Click a button to map. Green = mapped, gray = unmapped.", fg="black"))

    def create_tray_icon(self):
        """Creates the system tray icon using pystray."""
        # Create a simple icon image (DS4 controller icon)
        image = Image.new('RGB', (64, 64), color='white')
        d = ImageDraw.Draw(image)
        # Draw a simple controller shape
        d.ellipse((8, 20, 24, 36), fill='#1976D2')  # Left stick
        d.ellipse((40, 20, 56, 36), fill='#1976D2')  # Right stick
        d.rectangle((20, 8, 44, 48), fill='#333333')  # Controller body
        d.ellipse((28, 16, 36, 24), fill='#FF5722')  # Center button
        
        # Define the menu that appears on right-click
        menu = pystray.Menu(
            pystray.MenuItem('Show Window', self.show_window_from_tray, default=True),
            pystray.MenuItem('Quit', self.quit_from_tray)
        )
        
        # Create the icon object
        self.tray_icon = pystray.Icon(
            'ds4_controller',
            image,
            'DS4 Controller',
            menu
        )

    def show_window_from_tray(self, icon=None, item=None):
        """Shows the main window from tray menu."""
        # Use a flag-based approach to avoid direct Tkinter calls from background thread
        self.show_window_flag = True

    def quit_from_tray(self, icon=None, item=None):
        """Quits the application from tray menu."""
        print("Quit command received from tray. Shutting down.")
        # Use a flag-based approach to avoid direct Tkinter calls from background thread
        self.quit_flag = True

    def check_tray_flags(self):
        """Check for tray-triggered actions and execute them on the main thread."""
        try:
            if hasattr(self, 'show_window_flag') and self.show_window_flag:
                self.show_window_flag = False
                self.deiconify()
                self.lift()
                self.focus_force()
                print("Window shown from tray.")
            
            if hasattr(self, 'quit_flag') and self.quit_flag:
                self.quit_flag = False
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    try:
                        self.tray_icon.stop()
                    except Exception as e:
                        print(f"Error stopping tray icon: {e}")
                self.quit_application()
                return  # Don't schedule another check
                
        except Exception as e:
            print(f"Error in tray flag check: {e}")
        
        # Schedule the next check
        self.after(100, self.check_tray_flags)

    def hide_window(self, event=None):
        """Hide the window to tray instead of quitting."""
        print("Window hidden to tray.")
        self.withdraw()  # Hide instead of quit

    def on_closing(self):
        """Clean shutdown of the application when window is closed."""
        self.hide_window()

if __name__ == "__main__":
    app = DS4ControlUI()
    app.protocol("WM_DELETE_WINDOW", app.hide_window)  # This now hides the window instead of quitting
    
    # Start the tray icon in detached mode
    app.tray_icon.run_detached()
    
    # Run the main Tkinter loop
    app.mainloop() 