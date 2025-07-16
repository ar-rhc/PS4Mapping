#!/usr/bin/env python3
"""
Test script for modular tab classes
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gui.tabs.lightbar_tab import LightbarTab
    from gui.tabs.settings_tab import SettingsTab
    from gui.tabs.visualization_tab import VisualizationTab
    from gui.tabs.data_export_tab import DataExportTab
    from gui.tabs.rumble_tab import RumbleTab
    print("✅ All tab classes imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_tab_creation():
    """Test creating tab instances"""
    root = tk.Tk()
    root.title("Modular Tab Test")
    root.geometry("800x600")
    
    # Create notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    
    # Test each tab
    tabs = []
    
    try:
        # Test LightbarTab
        lightbar_frame = ttk.Frame(notebook)
        notebook.add(lightbar_frame, text='Lightbar')
        lightbar_tab = LightbarTab(lightbar_frame, None)  # No HID device for test
        tabs.append(('LightbarTab', lightbar_tab))
        print("✅ LightbarTab created successfully")
    except Exception as e:
        print(f"❌ LightbarTab error: {e}")
    
    try:
        # Test SettingsTab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text='Settings')
        settings_callbacks = {
            'update_alpha': lambda x: print(f"Alpha: {x}"),
            'update_sensitivity': lambda x: print(f"Sensitivity: {x}"),
            'update_damping': lambda x: print(f"Damping: {x}"),
            'update_polling': lambda x: print(f"Polling: {x}"),
            'reset_settings': lambda: print("Reset settings"),
            'save_settings': lambda: print("Save settings")
        }
        settings_tab = SettingsTab(settings_frame, settings_callbacks)
        tabs.append(('SettingsTab', settings_tab))
        print("✅ SettingsTab created successfully")
    except Exception as e:
        print(f"❌ SettingsTab error: {e}")
    
    try:
        # Test VisualizationTab
        viz_frame = ttk.Frame(notebook)
        notebook.add(viz_frame, text='Visualization')
        viz_callbacks = {
            'toggle_axis_lock': lambda axis: print(f"Toggle axis lock: {axis}")
        }
        viz_tab = VisualizationTab(viz_frame, viz_callbacks)
        tabs.append(('VisualizationTab', viz_tab))
        print("✅ VisualizationTab created successfully")
    except Exception as e:
        print(f"❌ VisualizationTab error: {e}")
    
    try:
        # Test DataExportTab
        export_frame = ttk.Frame(notebook)
        notebook.add(export_frame, text='Data Export')
        export_callbacks = {
            'export_data': lambda: print("Export data"),
            'export_json': lambda: print("Export JSON")
        }
        export_tab = DataExportTab(export_frame, export_callbacks)
        tabs.append(('DataExportTab', export_tab))
        print("✅ DataExportTab created successfully")
    except Exception as e:
        print(f"❌ DataExportTab error: {e}")
    
    try:
        # Test RumbleTab
        rumble_frame = ttk.Frame(notebook)
        notebook.add(rumble_frame, text='Rumble')
        rumble_callbacks = {
            'update_strong_rumble': lambda x: print(f"Strong rumble: {x}"),
            'update_weak_rumble': lambda x: print(f"Weak rumble: {x}"),
            'set_preset_rumble': lambda s, w: print(f"Preset rumble: {s}, {w}"),
            'apply_rumble': lambda: print("Apply rumble"),
            'test_rumble': lambda: print("Test rumble"),
            'toggle_tactile_feedback': lambda: print("Toggle tactile feedback")
        }
        rumble_tab = RumbleTab(rumble_frame, None, rumble_callbacks)  # No HID device for test
        tabs.append(('RumbleTab', rumble_tab))
        print("✅ RumbleTab created successfully")
    except Exception as e:
        print(f"❌ RumbleTab error: {e}")
    
    print(f"\n📊 Summary: {len(tabs)} tabs created successfully")
    
    # Test some basic methods
    print("\n🧪 Testing basic methods...")
    for name, tab in tabs:
        try:
            # Test if tab has common methods
            if hasattr(tab, 'update_visualizations'):
                print(f"✅ {name} has update_visualizations method")
            if hasattr(tab, 'update_ui_from_settings'):
                print(f"✅ {name} has update_ui_from_settings method")
            if hasattr(tab, 'draw_canvas'):
                print(f"✅ {name} has draw_canvas method")
        except Exception as e:
            print(f"❌ {name} method test error: {e}")
    
    # Show the window for a few seconds
    print("\n🪟 Showing test window for 5 seconds...")
    root.after(5000, root.destroy)
    root.mainloop()
    
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    test_tab_creation() 