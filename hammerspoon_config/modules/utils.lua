 
-- modules/utils.lua
-- Utility and debugging functions to inspect system state.

local utils = {}

-- Function to show all available monitors
function utils.showMonitors()
    print("=== Available Monitors ===")
    local screens = hs.screen.allScreens()
    
    for i, screen in ipairs(screens) do
        local frame = screen:frame()
        local name = screen:name()
        local mode = screen:currentMode()
        
        print(string.format("Monitor %d: %s", i, name))
        print(string.format("  Resolution: %dx%d", mode.w, mode.h))
        print(string.format("  Position: x=%d, y=%d", frame.x, frame.y))
        print(string.format("  Size: w=%d, h=%d", frame.w, frame.h))
        print(string.format("  Orientation: %s", (mode.w > mode.h) and "Horizontal" or "Vertical"))
        print("---")
    end
    
    print("Primary screen: " .. hs.screen.primaryScreen():name())
    print("==================")
end

-- Function to list all input devices
function utils.listInputDevices()
    print("=== Input Devices ===")
    local devices = hs.usb.attachedDevices()
    for i, device in ipairs(devices) do
        if device.productName and (
            string.find(device.productName:lower(), "keyboard") or
            string.find(device.productName:lower(), "keypad") or
            device.vendorID == 9494  -- Your QuickFire keyboard vendor ID
        ) then
            print(string.format("Keyboard %d: %s (Vendor: %s, Product: %s)", 
                i, device.productName or "Unknown", 
                device.vendorID or "Unknown", 
                device.productID or "Unknown"))
        end
    end
    print("-- Done.")
end

print("✅ Utility functions loaded (utils.showMonitors, utils.listInputDevices).")

return utils