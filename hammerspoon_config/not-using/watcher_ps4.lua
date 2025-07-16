-- ds4_watcher.lua
-- Watches for a DualShock 4 controller and launches the Python UI script.

local ds4Watcher = {}

-- Controller identification
local DS4_VENDOR_ID = 1356
local DS4_PRODUCT_ID = 2508

-- Path to your Python script
-- NOTE: Uses 'pythonw' for proper GUI execution on macOS
local PYTHON_EXECUTABLE = "/opt/homebrew/bin/python3.11" 
local SCRIPT_PATH = "/Users/alex/ARfiles/Github/MacScripts/karabinder/main_scripts/hid_control_ui.py"

local usbWatcher = nil
local ds4_task = nil

function ds4Watcher:handleUSBEvent(event, device)
    -- Check if the event is for our specific controller
    if not (device and device.vendorID == DS4_VENDOR_ID and device.productID == DS4_PRODUCT_ID) then
        return
    end

    if event == "added" then
        -- Check if the task is already running to avoid launching duplicates
        if ds4_task and ds4_task:isRunning() then
            print("🎮 DS4 Controller connected, but script is already running.")
            return
        end
        
        print("🎮 DS4 Controller connected. Launching UI script...")
        hs.notify.new({title="DS4 Controller", informativeText="Controller connected, launching script."}):send()
        
        -- Use hs.task to run the Python script in the background
        ds4_task = hs.task.new(PYTHON_EXECUTABLE, nil, {SCRIPT_PATH})
        ds4_task:start()

    elseif event == "removed" then
        print("🎮 DS4 Controller disconnected.")
        hs.notify.new({title="DS4 Controller", informativeText="Controller disconnected."}):send()
        
        -- Optionally, you can stop the script when the controller is disconnected
        if ds4_task and ds4_task:isRunning() then
            print("   Stopping UI script...")
            ds4_task:terminate()
            ds4_task = nil
        end
    end
end

function ds4Watcher:start()
    if usbWatcher then usbWatcher:stop() end
    
    usbWatcher = hs.usb.watcher.new(function(d, e) self:handleUSBEvent(e, d) end)
    usbWatcher:start()
    print("✅ DS4 Controller watcher active.")
end

return ds4Watcher