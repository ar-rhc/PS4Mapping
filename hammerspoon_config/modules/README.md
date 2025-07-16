# DualShock 4 Controller Mapping System for macOS

## Overview
This system enables advanced mapping of DualShock 4 (DS4) controller inputs to macOS keystrokes or BetterTouchTool (BTT) named triggers, with per-application profiles and real-time reloading. It consists of:

- **Python Tkinter UI** (`hid_control_ui.py`):
  - Visual interface for configuring controller-to-key/BTT mappings.
  - Supports per-app profiles, fuzzy app matching, and instant mapping/unmapping.
  - Saves mappings to `~/.hammerspoon/mappings.json`.
- **Hammerspoon Lua Module** (`modules/controller.lua`):
  - Loads mappings and listens for controller events via UDP.
  - Triggers keystrokes or BTT actions based on the active app and mapping.
  - Supports fuzzy profile matching and real-time mapping reloads.

## File Structure

```
~/.hammerspoon/
  ├── modules/
  │   ├── controller.lua         # Main controller logic (this module)
  │   └── ...                    # Other Hammerspoon modules
  ├── mappings.json              # Controller mapping file (written by Python UI)
  ├── init.lua                   # Loads modules and starts system
  └── ...
```

## How It Works

1. **Configure Mappings**: Run the Python UI (`hid_control_ui.py`).
   - Map controller buttons/D-pad to keystrokes (with modifiers) or BTT triggers.
   - Create/edit/delete per-app profiles. Fuzzy matching allows flexible app names.
   - Mappings are saved to `~/.hammerspoon/mappings.json`.
2. **Hammerspoon Loads Mappings**: The Lua module watches for changes to `mappings.json` and reloads automatically.
3. **Controller Events**: The Python script sends controller state via UDP to Hammerspoon, which processes events and triggers mapped actions for the active app.

## Mapping File Format (`mappings.json`)

```json
{
  "Default": {
    "buttons": {
      "cross": { "key": "return", "modifiers": {} },
      "circle": { "key": "left", "modifiers": {"ctrl": false, "opt": false, "shift": false, "cmd": false} }
    },
    "dpad": {
      "up": { "key": "up", "modifiers": {} },
      "down": { "key": "down", "modifiers": {} }
    }
  },
  "Adobe Lightroom Classic": {
    "buttons": {
      "square": { "key": "left", "modifiers": {"ctrl": false, "opt": false, "shift": false, "cmd": false} },
      "options": { "bttnamekey": "ps4-1" }
    },
    "dpad": {
      "up": { "key": "left", "modifiers": {"ctrl": false, "opt": false, "shift": false, "cmd": false} }
    }
  }
}
```
- **Profiles**: Top-level keys (e.g., `Default`, `Adobe Lightroom Classic`) are app profiles.
- **buttons/dpad**: Map controller buttons/D-pad directions to actions.
- **Keystroke mapping**: `{ "key": "a", "modifiers": {"cmd": true, ...} }`
- **BTT trigger**: `{ "bttnamekey": "trigger_name" }`

## Setup & Usage

1. **Install Hammerspoon**: https://www.hammerspoon.org/
2. **Install Python dependencies**: `pip install hid pillow matplotlib tkmacosx pystray`
3. **Run the Python UI**:
   ```sh
   python /path/to/hid_control_ui.py
   ```
4. **Configure mappings** in the UI and save. The file is written to `~/.hammerspoon/mappings.json`.
5. **Reload Hammerspoon** (or it will auto-reload on mapping changes).
6. **Connect your DS4 controller** and use as mapped!

## Advanced Features
- **Fuzzy Profile Matching**: App names in profiles are matched flexibly (e.g., "Lightroom" matches "Adobe Lightroom Classic").
- **Real-Time Reload**: Mappings reload instantly when the JSON file changes.
- **BTT Integration**: Map controller buttons to BetterTouchTool named triggers.
- **Per-Profile or Global Mapping**: Map buttons for all profiles or just one.

## Troubleshooting
- **Mappings not working?**
  - Ensure the Python UI writes to `~/.hammerspoon/mappings.json`.
  - Check Hammerspoon console for errors (View > Console).
  - Make sure the UDP port (default 12345) matches in both scripts.
  - For BTT triggers, ensure BetterTouchTool is running and the trigger name matches.
- **Profile not detected?**
  - Try adding a fuzzy/shorter profile name (e.g., "Lightroom").
  - Check the active app name in Hammerspoon console.

## Extending
- Add new profiles or mappings in the UI.
- Edit `controller.lua` for custom logic or new event types.
- See other modules in `~/.hammerspoon/modules/` for more automation ideas.

---

For questions or improvements, see the code comments in `controller.lua` and `hid_control_ui.py`. 