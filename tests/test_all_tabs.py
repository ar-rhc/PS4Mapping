#!/usr/bin/env python3
"""
Test script for all modular tab classes
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the gui directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gui'))

from gui.tabs.lightbar_tab import LightbarTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.data_export_tab import DataExportTab
from gui.tabs.visualization_tab import VisualizationTab
from gui.tabs.rumble_tab import RumbleTab

def test_all_tabs():
    """Test all modular tab classes"""
    
    # Create root window
    root = tk.Tk()
    root.title("All Tabs Test")
    root.geometry("800x600")
    
    # Create a notebook for the tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Mock HID device (None for testing)
    mock_hid_device = None
    
    # Test LightbarTab
    try:
        lightbar_frame = ttk.Frame(notebook)
        notebook.add(lightbar_frame, text="Lightbar")
        lightbar_tab = LightbarTab(parent_frame=lightbar_frame, hid_device=mock_hid_device)
        print("✓ LightbarTab created successfully")
    except Exception as e:
        print(f"✗ Error creating LightbarTab: {e}")
    
    # Test SettingsTab
    try:
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        settings_tab = SettingsTab(parent_frame=settings_frame)
        print("✓ SettingsTab created successfully")
    except Exception as e:
        print(f"✗ Error creating SettingsTab: {e}")
    
    # Test DataExportTab
    try:
        data_export_frame = ttk.Frame(notebook)
        notebook.add(data_export_frame, text="Data Export")
        data_export_tab = DataExportTab(parent_frame=data_export_frame)
        print("✓ DataExportTab created successfully")
    except Exception as e:
        print(f"✗ Error creating DataExportTab: {e}")
    
    # Test VisualizationTab
    try:
        visualization_frame = ttk.Frame(notebook)
        notebook.add(visualization_frame, text="Visualization")
        visualization_tab = VisualizationTab(parent_frame=visualization_frame)
        print("✓ VisualizationTab created successfully")
    except Exception as e:
        print(f"✗ Error creating VisualizationTab: {e}")
    
    # Test RumbleTab
    try:
        rumble_frame = ttk.Frame(notebook)
        notebook.add(rumble_frame, text="Rumble")
        rumble_tab = RumbleTab(parent_frame=rumble_frame, hid_device=mock_hid_device)
        print("✓ RumbleTab created successfully")
    except Exception as e:
        print(f"✗ Error creating RumbleTab: {e}")
    
    # Add a status label
    status_label = tk.Label(root, text="All tabs created. Test the UI elements.", fg="green")
    status_label.pack(pady=10)
    
    print("All tabs test window created. Close the window to exit.")
    root.mainloop()

if __name__ == "__main__":
    test_all_tabs() 