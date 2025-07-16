import tkinter as tk
from PIL import Image, ImageDraw
import pystray

class WindowManager:
    """Handles window visibility, system tray icon, and application lifecycle."""

    def __init__(self, app):
        """
        Initializes the WindowManager.

        Args:
            app: The main DS4ControlUI application instance.
        """
        self.app = app
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_tray_icon()
        self.check_tray_flags()

    def quit_application(self):
        """Cleanly shuts down the application."""
        self.app.is_running = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        if hasattr(self.app, 'h'):
            self.app.h.close()
        if hasattr(self.app, 'udp_manager'):
            self.app.udp_manager.stop()
        self.app.destroy()

    def hide_window(self):
        """Hides the main application window."""
        self.app.withdraw()

    def toggle_window_visibility(self):
        """Toggles the window visibility, ensuring it gains focus."""
        if self.app.state() == 'withdrawn':
            self.app.deiconify()
            self.app.lift()
            self.app.focus_force()
            self.app.attributes("-topmost", True)
            self.app.after(100, lambda: self.app.attributes("-topmost", False))
        else:
            self.app.withdraw()

    def create_tray_icon(self):
        """Creates and configures the system tray icon."""
        image = Image.new('RGB', (64, 64), color='white')
        d = ImageDraw.Draw(image)
        d.rectangle((20, 8, 44, 48), fill='#333333')
        menu = pystray.Menu(
            pystray.MenuItem('Show Window', self.show_window_from_tray, default=True),
            pystray.MenuItem('Quit', self.quit_application)
        )
        self.tray_icon = pystray.Icon('ds4_controller', image, 'DS4 Controller', menu)
        # Run the tray icon in a separate thread
        self.tray_icon.run_detached()

    def show_window_from_tray(self, icon=None, item=None):
        """Sets a flag to show the window from the system tray."""
        self.app.show_window_flag = True

    def check_tray_flags(self):
        """Periodically checks flags set by the tray icon."""
        if self.app.show_window_flag:
            self.app.show_window_flag = False
            self.toggle_window_visibility()
        if self.app.quit_flag:
            self.quit_application()
            return

        # Also check for IPC commands here
        if hasattr(self.app, 'udp_manager'):
            self.app.udp_manager.check_ipc_socket()

        self.app.after(100, self.check_tray_flags)

    def on_closing(self):
        """Called when the window's close button is pressed."""
        self.hide_window() 