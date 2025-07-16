# DS4 Controller constants
VENDOR_ID = 1356
PRODUCT_ID = 2508

def set_lightbar_and_rumble(h, r, g, b, left_rumble=0, right_rumble=0):
    """Send output report for lightbar and rumble control (USB, report ID 0x05, 32 bytes)"""
    if h:
        report = [0x05, 0xFF, 0x04, 0x00, left_rumble, right_rumble, r, g, b] + [0]*23
        h.write(bytes(report))

class HIDController:
    """Manages HID connection to DS4 controller"""
    
    def __init__(self):
        self.device = None
        self.connect()
    
    def connect(self):
        """Connect to DS4 controller"""
        try:
            # Try to import hid, but don't fail if it's not available
            import hid
            self.device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
            print(f"✅ Connected to DS4 controller")
        except ImportError:
            print("⚠️  HID library not available - running in simulation mode")
            self.device = None
        except Exception as e:
            print(f"❌ Failed to connect to DS4: {e}")
            self.device = None
    
    def set_lightbar(self, r, g, b):
        """Set lightbar color"""
        if self.device:
            set_lightbar_and_rumble(self.device, r, g, b)
        else:
            print(f"🎨 [SIMULATION] Lightbar set to RGB({r}, {g}, {b})")
    
    def set_rumble(self, left=0, right=0):
        """Set rumble motors"""
        if self.device:
            set_lightbar_and_rumble(self.device, 0, 0, 0, left, right)
        else:
            print(f"📳 [SIMULATION] Rumble set to L:{left}, R:{right}")
    
    def close(self):
        """Close HID connection"""
        if self.device:
            self.device.close()
            print("🔌 HID connection closed") 