import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from PIL import Image, ImageTk
import os
import json
import sys
from tkmacosx import Button

class MappingConfigFrame(tk.Frame):
    """Mapping configuration frame for DS4 controller button mapping"""
    
    BUTTON_COORDS = {
        'square': (394, 105), 'cross': (437, 136), 'circle': (474, 103), 'triangle': (437, 64),
        'l1': (169, 34), 'r1': (424, 28),
        'share': (221, 47), 'options': (388, 46),
        'l3': (229, 156), 'r3': (370, 156),
        'dpad_up': (164, 73), 'dpad_down': (162, 144), 'dpad_left': (124, 100), 'dpad_right': (195, 99),
        'l2_pressed': (162, 8), 'r2_pressed': (431, 4),
    }
    
    BUTTON_LABELS = {
        'cross': 'Cross', 'circle': 'Circle', 'square': 'Square', 'triangle': 'Triangle',
        'l1': 'L1', 'r1': 'R1', 'l2_pressed': 'L2 Press', 'r2_pressed': 'R2 Press',
        'l3': 'L3', 'r3': 'R3', 'share': 'Share', 'options': 'Options',
        'dpad_up': 'D-Pad Up', 'dpad_down': 'D-Pad Down', 'dpad_left': 'D-Pad Left', 'dpad_right': 'D-Pad Right'
    }
    
    MAPPING_FILE = os.path.expanduser("~/.hammerspoon/mappings.json")
    PS4_IMAGE = os.path.join(os.path.dirname(__file__), "../assets/ps4.png")
    MOD_SYMBOLS = {'cmd': '⌘', 'shift': '⇧', 'alt': '⌥', 'ctrl': '⌃'}
    
    # Keycode map for macOS to handle Option key combinations correctly.
    # This is a workaround for a limitation in how tkinter processes modified key events on macOS.
    KC_MAP_MAC = {
        0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x', 8: 'c', 9: 'v', 11: 'b', 12: 'q',
        13: 'w', 14: 'e', 15: 'r', 16: 't', 17: 'y', 18: '1', 19: '2', 20: '3', 21: '4', 22: '6', 23: '5',
        24: '=', 25: '9', 26: '7', 27: '-', 28: '8', 29: '0', 30: ']', 31: 'o', 32: 'u', 33: '[', 34: 'i',
        35: 'p', 36: 'return', 37: 'l', 38: 'j', 39: "'", 40: 'k', 41: ';', 42: '\\', 43: ',', 44: '/',
        45: 'n', 46: 'm', 47: '.', 49: 'space', 50: '`', 51: 'delete', 53: 'escape',
    }

    def __init__(self, parent, on_start_controller_mapping=None, on_start_key_capture=None, on_set_profile_lightbar=None):
        super().__init__(parent, bg='#2c2c2c')
        self.on_start_key_capture = on_start_key_capture
        self.on_start_controller_mapping = on_start_controller_mapping
        self.on_set_profile_lightbar = on_set_profile_lightbar

        self.mappings = self.load_mappings()
        self.active_profile_name = "Default"
        if "Default" not in self.mappings:
            self.mappings["Default"] = {"buttons": {}, "dpad": {}}

        self.button_widgets = {}
        self.key_labels = {}
        self._click_timer = None
        self.lightbar_color_viewer = None # Add this
        
        self.create_widgets()

    def create_widgets(self):
        # --- Top bar for controls ---
        top_bar = tk.Frame(self, bg='#2c2c2c')
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        tk.Button(top_bar, text="Map with Controller", command=self.on_start_controller_mapping).pack(side=tk.LEFT)
        tk.Button(top_bar, text="Save All Mappings", command=self.save_mappings).pack(side=tk.LEFT, padx=10)
        
        # Lightbar controls
        lightbar_frame = tk.Frame(top_bar, bg='#2c2c2c')
        lightbar_frame.pack(side=tk.LEFT)
        
        tk.Button(lightbar_frame, text="Set Profile Lightbar", command=self.set_profile_lightbar_color).pack(side=tk.LEFT)
        
        self.lightbar_color_viewer = tk.Label(lightbar_frame, text="", bg='#2c2c2c', relief="sunken", borderwidth=1, width=4)
        self.lightbar_color_viewer.pack(side=tk.LEFT, padx=5, ipady=2)


        # --- Main content area ---
        main_frame = tk.Frame(self, bg='#2c2c2c')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        # --- Canvas on the left ---
        canvas_frame = tk.Frame(main_frame, bg='white')
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # --- Profile panel on the right ---
        profile_panel_bg = '#333333'
        profile_panel = tk.Frame(main_frame, width=200, bg=profile_panel_bg)
        profile_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        profile_panel.pack_propagate(False)
        
        tk.Label(profile_panel, text="Profiles", font=("Arial", 14, "bold"), bg=profile_panel_bg, fg='white').pack(pady=10)
        self.profile_listbox = tk.Listbox(profile_panel, font=("Arial", 12), activestyle='dotbox', 
                                         selectbackground='#007ACC', selectforeground='white',
                                         bg='#444444', fg='white', highlightthickness=0, borderwidth=0)
        self.profile_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.populate_profile_listbox()
        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_listbox_select)
        
        # Trigger initial selection to load first profile's color
        if self.profile_listbox.size() > 0:
            self.profile_listbox.event_generate("<<ListboxSelect>>")
        
        profile_controls = tk.Frame(profile_panel, bg=profile_panel_bg)
        profile_controls.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)
        Button(profile_controls, text="+ Add", command=self.add_profile).pack(side='left', expand=True, padx=(0, 2))
        Button(profile_controls, text="- Delete", command=self.delete_profile).pack(side='right', expand=True, padx=(2, 0))
        
        # --- Bottom Info Label ---
        self.info_label = tk.Label(self, text="Click a button to map. Double-click to edit.", font=("Arial", 12, "bold"), fg='white', bg='#2c2c2c')
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=10)
        
        self.ps4_img = None
        self.scaled_buttons = {}
        
    def on_resize(self, event=None):
        self.load_and_place_image()

    def load_and_place_image(self):
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        try:
            img = Image.open(self.PS4_IMAGE)
            img_aspect = img.width / img.height
            canvas_aspect = canvas_width / canvas_height
            if img_aspect > canvas_aspect:
                new_width = canvas_width
                self.scale_factor = new_width / img.width
            else:
                new_height = canvas_height
                self.scale_factor = new_height / img.height
                new_width = int(new_height * img_aspect)
            
            new_height = int(new_width / img_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.ps4_img = ImageTk.PhotoImage(img)
            img_x = (canvas_width - new_width) // 2
            img_y = (canvas_height - new_height) // 2
            
            self.canvas.create_image(img_x, img_y, anchor='nw', image=self.ps4_img)
            self.scaled_buttons = {btn: (img_x + int(x * self.scale_factor), img_y + int(y * self.scale_factor)) for btn, (x, y) in self.BUTTON_COORDS.items()}
        except Exception as e:
            self.canvas.create_text(canvas_width/2, canvas_height/2, text=f"[Image not found]\n{e}", fill="red")
        self.place_buttons()
        
    def place_buttons(self):
        self.button_widgets.clear()
        self.key_labels.clear()
        for btn, (x,y) in self.scaled_buttons.items():
            if btn not in self.BUTTON_LABELS: continue
            
            w = Button(self.canvas, text=self.BUTTON_LABELS[btn], width=80, height=30, 
                      font=("Arial", 10, "bold"), fg="white", bg="#808080", 
                      activebackground="#808080", activeforeground="white", 
                      highlightthickness=0, borderwidth=0)
            
            w.bind('<Button-1>', lambda e, b=btn: self.handle_click(b, "single"))
            w.bind('<Double-Button-1>', lambda e, b=btn: self.handle_click(b, "double"))

            self.button_widgets[btn] = w
            self.canvas.create_window(x, y, window=w)
            
            key_label = tk.Label(self.canvas, text="", font=("Arial", 9), fg="white", 
                               bg="#808080", height=1, relief="flat", anchor="center")
            self.key_labels[btn] = key_label
            self.canvas.create_window(x, y + 22, window=key_label, width=80)
        self.update_button_colors()

    def set_button_highlight(self, btn, highlight=False):
        """Sets or removes a highlight outline on a mapping button."""
        widget = self.button_widgets.get(btn)
        if widget:
            if highlight:
                widget.config(highlightbackground="yellow", highlightcolor="yellow", highlightthickness=2)
            else:
                widget.config(highlightthickness=0)

    def handle_click(self, btn, click_type):
        if self._click_timer:
            self.after_cancel(self._click_timer)
            self._click_timer = None

        if click_type == "double":
            self.edit_mapping(btn)
        else:
            self.on_start_key_capture(btn, from_ui=True)

    def load_mappings(self):
        try:
            if os.path.exists(self.MAPPING_FILE):
                with open(self.MAPPING_FILE, 'r') as f: return json.load(f)
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load mappings file:\n{e}")
        return {"Default": {"buttons": {}, "dpad": {}}}

    def save_mappings(self):
        try:
            os.makedirs(os.path.dirname(self.MAPPING_FILE), exist_ok=True)
            with open(self.MAPPING_FILE, 'w') as f: json.dump(self.mappings, f, indent=2)
            self.info_label.config(text="Mappings saved successfully!", fg="#388E3C")
            self.after(2000, lambda: self.info_label.config(text="Click a button to map. Double-click to edit.", fg="white"))
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save mappings file:\n{e}")

    def update_button_colors(self):
        active_map = self.mappings.get(self.active_profile_name, {})
        for btn, widget in self.button_widgets.items():
            section = "dpad" if btn.startswith('dpad_') else "buttons"
            mapping_key = btn.replace('dpad_', '') if section == "dpad" else btn
            mapping = active_map.get(section, {}).get(mapping_key)
            key_label = self.key_labels.get(btn)
            bg_color, key_text = ("#808080", "")
            if mapping:
                if 'bttnamekey' in mapping and mapping['bttnamekey']:
                    bg_color, key_text = ("#2196F3", f"BTT: {mapping['bttnamekey']}")
                elif 'key' in mapping and mapping['key']:
                    bg_color = "#4CAF50"
                    mods = mapping.get('modifiers', {})
                    mod_keys = [self.MOD_SYMBOLS[m] for m in ['cmd', 'shift', 'alt', 'ctrl'] if mods.get(m)]
                    key_text = ''.join(mod_keys) + mapping['key']
            widget.config(bg=bg_color, activebackground=bg_color)
            if key_label: key_label.config(text=key_text, bg=bg_color, fg="white")

    def populate_profile_listbox(self):
        self.profile_listbox.delete(0, tk.END)
        for i, name in enumerate(self.mappings.keys()):
            self.profile_listbox.insert(tk.END, name)
            if name == self.active_profile_name:
                self.profile_listbox.selection_set(i)
                self.profile_listbox.activate(i)

    def on_profile_listbox_select(self, event=None):
        selection = self.profile_listbox.curselection()
        if selection:
            self.active_profile_name = self.profile_listbox.get(selection[0])
            self.update_button_colors()
            
            # Update and apply lightbar color
            active_map = self.mappings.get(self.active_profile_name, {})
            color_rgb = active_map.get('lightbar') # Will be None if not set
            
            self._update_color_viewer(color_rgb)

            if color_rgb and self.on_set_profile_lightbar:
                self.on_set_profile_lightbar(r=color_rgb[0], g=color_rgb[1], b=color_rgb[2])

    def add_profile(self):
        new_name = f"Profile_{len(self.mappings) + 1}"
        i = 1
        while new_name in self.mappings:
            i += 1
            new_name = f"Profile_{len(self.mappings) + i}"
        self.mappings[new_name] = {"buttons": {}, "dpad": {}}
        self.populate_profile_listbox()
        for i, name in enumerate(self.mappings.keys()):
            if name == new_name:
                self.profile_listbox.selection_set(i)
                self.on_profile_listbox_select()
                break

    def delete_profile(self):
        if self.active_profile_name == "Default":
            messagebox.showwarning("Cannot Delete", "The Default profile cannot be deleted.")
            return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{self.active_profile_name}'?"):
            del self.mappings[self.active_profile_name]
            self.active_profile_name = "Default"
            self.populate_profile_listbox()
            self.update_button_colors()
            self.save_mappings()

    def set_profile_lightbar_color(self):
        """Opens a color chooser and saves the selected color to the current profile."""
        if not self.active_profile_name:
            messagebox.showwarning("No Profile Selected", "Please select a profile first.")
            return

        # Get current color if it exists
        current_color_rgb = self.mappings.get(self.active_profile_name, {}).get('lightbar')
        initial_color_hex = f'#{current_color_rgb[0]:02x}{current_color_rgb[1]:02x}{current_color_rgb[2]:02x}' if current_color_rgb else "#ffffff"

        # Open color chooser
        color_data = colorchooser.askcolor(color=initial_color_hex, title="Choose a lightbar color")
        
        if color_data and color_data[0]:
            rgb, hex_color = color_data
            r, g, b = map(int, rgb)
            
            # Save to mappings
            if self.active_profile_name not in self.mappings:
                self.mappings[self.active_profile_name] = {"buttons": {}, "dpad": {}}
            self.mappings[self.active_profile_name]['lightbar'] = [r, g, b]
            
            # Save to file
            self.save_mappings()
            
            # Apply color immediately via callback
            if self.on_set_profile_lightbar:
                self.on_set_profile_lightbar(r=r, g=g, b=b)
            
            # Update the color viewer
            self._update_color_viewer([r, g, b])

    def _update_color_viewer(self, rgb_list):
        """Updates the color viewer label with the given RGB color."""
        if rgb_list and len(rgb_list) == 3:
            # Convert RGB to hex string
            hex_color = f'#{rgb_list[0]:02x}{rgb_list[1]:02x}{rgb_list[2]:02x}'
            self.lightbar_color_viewer.config(bg=hex_color)
        else:
            # Default color if no lightbar setting exists for the profile
            self.lightbar_color_viewer.config(bg='#2c2c2c')

    def edit_mapping(self, btn):
        active_profile = self.active_profile_name
        section = "dpad" if btn.startswith('dpad_') else "buttons"
        mapping_key = btn.replace('dpad_', '') if section == "dpad" else btn
        current_mapping = self.mappings.get(active_profile, {}).get(section, {}).get(mapping_key, {})

        top = tk.Toplevel(self)
        top.title(f"Edit: {self.BUTTON_LABELS[btn]}")
        top.transient(self)
        top.grab_set()
        top.geometry("400x350")
        top.configure(bg="#3c3c3c")

        captured_key = tk.StringVar(value=current_mapping.get('key', 'Not Mapped'))
        
        # --- Keystroke Section ---
        key_frame = tk.LabelFrame(top, text="Keystroke", fg="white", bg="#3c3c3c", padx=10, pady=10)
        key_frame.pack(pady=10, padx=10, fill="x")
        
        mods_vars = {m: tk.BooleanVar(value=current_mapping.get('modifiers', {}).get(m, False)) for m in ['cmd', 'shift', 'alt', 'ctrl']}
        mod_frame = tk.Frame(key_frame, bg="#3c3c3c")
        mod_frame.pack(pady=5)
        for m_name, m_symbol in self.MOD_SYMBOLS.items():
            tk.Checkbutton(mod_frame, text=m_symbol, variable=mods_vars[m_name], 
                           font=("Arial", 14),
                           bg="#3c3c3c", fg="white", selectcolor="#555555",
                           activebackground="#3c3c3c", activeforeground="white",
                           highlightbackground="#3c3c3c").pack(side='left', padx=5)
        
        key_display_frame = tk.Frame(key_frame, bg="#3c3c3c")
        key_display_frame.pack(pady=5)
        tk.Label(key_display_frame, text="Key:", fg="white", bg="#3c3c3c").pack(side=tk.LEFT)
        key_display_label = tk.Label(key_display_frame, textvariable=captured_key, width=12, relief="sunken", bg="#555555", fg="white", font=("Arial", 12))
        key_display_label.pack(side=tk.LEFT, padx=5)
        
        def start_capture():
            remap_btn.config(text="Press a key...", state=tk.DISABLED)
            top.bind("<KeyPress>", capture_key)
            top.focus_set()

        def capture_key(event):
            top.unbind("<KeyPress>")
            remap_btn.config(text="Remap Key", state=tk.NORMAL)
            
            # --- Temporary Debugging ---
            print(f"DEBUG: KeySym='{event.keysym}', KeyCode={event.keycode}, State={event.state}")
            # -------------------------

            # Ignore modifier key presses themselves
            mod_keys = ['command_l', 'command_r', 'shift_l', 'shift_r', 'alt_l', 'alt_r', 'control_l', 'control_r', 'caps_lock', 'escape']
            if event.keysym.lower() in mod_keys:
                return

            # Update modifier checkboxes from event state
            mods_vars['cmd'].set(bool(event.state & 0x10))
            mods_vars['shift'].set(bool(event.state & 0x1))
            mods_vars['alt'].set(bool(event.state & 0x8))
            mods_vars['ctrl'].set(bool(event.state & 0x4))
            
            key_name = ""
            is_alt_pressed = mods_vars['alt'].get()
            
            # On macOS, if Option/Alt is pressed, event.keysym gives a special character.
            # We use the keycode to get the actual key pressed as a workaround.
            if is_alt_pressed and sys.platform == "darwin":
                key_name = self.KC_MAP_MAC.get(event.keycode, event.keysym)
            else:
                key_name = event.keysym
            
            # Standardize some key names
            if len(key_name) > 1:
                key_name = key_name.lower()
            
            # Don't capture modifiers as the key
            if key_name.lower() not in ['command_l', 'command_r', 'shift_l', 'shift_r', 'alt_l', 'alt_r', 'control_l', 'control_r']:
                 captured_key.set(key_name)

        remap_btn = Button(key_frame, text="Remap Key", command=start_capture)
        remap_btn.pack(pady=5)

        # --- BTT Trigger Section ---
        btt_frame = tk.LabelFrame(top, text="OR: BTT Named Trigger", fg="white", bg="#3c3c3c", padx=10, pady=10)
        btt_frame.pack(pady=10, padx=10, fill="x")
        
        btt_var = tk.StringVar(value=current_mapping.get('bttnamekey', ''))
        btt_entry = tk.Entry(btt_frame, textvariable=btt_var, width=30)
        btt_entry.pack(pady=5)
        
        # --- Actions ---
        action_frame = tk.Frame(top, bg="#3c3c3c")
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        def save_changes():
            btt_name = btt_var.get().strip()
            key_name = captured_key.get().strip()
            
            new_mapping = {}
            if btt_name:
                new_mapping = {'bttnamekey': btt_name}
            elif key_name and key_name != "Not Mapped":
                new_mapping['key'] = key_name
                new_mapping['modifiers'] = {m: v.get() for m, v in mods_vars.items()}
            
            profile_section = self.mappings.setdefault(active_profile, {}).setdefault(section, {})
            if new_mapping:
                 profile_section[mapping_key] = new_mapping
            elif mapping_key in profile_section:
                del profile_section[mapping_key]

            self.update_button_colors()
            self.save_mappings()
            top.destroy()

        def unmap():
            profile_section = self.mappings.setdefault(active_profile, {}).setdefault(section, {})
            if mapping_key in profile_section:
                del profile_section[mapping_key]
            self.update_button_colors()
            self.save_mappings()
            top.destroy()

        save_btn = Button(action_frame, text="Save & Close", command=save_changes, bg="#4CAF50", fg="white")
        save_btn.pack(side=tk.LEFT, expand=True, padx=5)
        unmap_btn = Button(action_frame, text="Unmap", command=unmap, bg="#D32F2F", fg="white")
        unmap_btn.pack(side=tk.LEFT, expand=True, padx=5)
        cancel_btn = Button(action_frame, text="Cancel", command=top.destroy)
        cancel_btn.pack(side=tk.RIGHT, expand=True, padx=5) 