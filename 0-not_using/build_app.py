#!/usr/bin/env python3
"""
Build script for DS4 Controller UI
Packages the application using PyInstaller
"""

import os
import sys
import subprocess
import shutil

def main():
    print("Building DS4 Controller UI...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check if rumps is installed
    try:
        import rumps
        print("rumps found")
    except ImportError:
        print("rumps not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "rumps"])
    
    # Clean previous builds
    if os.path.exists("build"):
        print("Cleaning previous build...")
        shutil.rmtree("build")
    
    if os.path.exists("dist"):
        print("Cleaning previous dist...")
        shutil.rmtree("dist")
    
    # Build the application
    print("Building application...")
    result = subprocess.run([
        "pyinstaller",
        "--clean",
        "hid_control_ui.spec"
    ])
    
    if result.returncode == 0:
        print("\n✅ Build successful!")
        print("The packaged application is in the 'dist' folder.")
        print("You can run it with: ./dist/DS4_Controller_UI")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 