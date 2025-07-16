-- modules/device_watchers.lua
-- Watches for specific USB devices and triggers actions.

local deviceWatchers = {}

-- Huion Tablet Configuration
local HUION_VENDOR_ID = 9580
local HUION_PRODUCT_ID = 109
local huionConnected = false

-- DualShock 4 Controller Configuration
local DS4_VENDOR_ID = 1356
local DS4_PRODUCT_ID = 2508
local ds4Task = nil

-- A helper for the hs.usb.find deprecation
local function isDeviceAttached(vendor, product)
    for _, dev in ipairs(hs.usb.attachedDevices()) do
        if dev.vendorID == vendor and dev.productID == product then
            return true
        end
    end
    return false
end

function deviceWatchers:handleUSBEvent(device)
    if not device then return end

    -- Debounce timer to handle event "bouncing"
    hs.timer.doAfter(0.5, function()
        -- Handle Huion Tablet
        if device.vendorID == HUION_VENDOR_ID and device.productID == HUION_PRODUCT_ID then
            local isConnected = isDeviceAttached(HUION_VENDOR_ID, HUION_PRODUCT_ID)
            if isConnected and not huionConnected then
                print("🖋️ Huion tablet connected - launching driver.")
                hs.application.launchOrFocus("HuionTablet")
            elseif not isConnected and huionConnected then
                print("🖋️ Huion tablet disconnected.")
            end
            huionConnected = isConnected
        end

        -- Handle DS4 Controller
        if device.vendorID == DS4_VENDOR_ID and device.productID == DS4_PRODUCT_ID then
            local isConnected = isDeviceAttached(DS4_VENDOR_ID, DS4_PRODUCT_ID)
            if isConnected and (not ds4Task or not ds4Task:isRunning()) then
                print("🎮 DS4 Controller connected. Launching Python script...")
                hs.notify.new({title="DS4 Controller", informativeText="Connected, starting mapper."}):send()
                local py_executable = "/opt/homebrew/bin/python3.11"
                local script_path = "/Users/alex/ARfiles/Github/MacScripts/karabinder/main_scripts/hid_control_ui_hybrid.py"
                ds4Task = hs.task.new(py_executable, nil, {script_path})
                ds4Task:start()
            elseif not isConnected and (ds4Task and ds4Task:isRunning()) then
                print("🎮 DS4 Controller disconnected. Stopping Python script.")
                ds4Task:terminate()
                ds4Task = nil
            end
        end
    end)
end

function deviceWatchers:start()
    -- Initialize states on start
    huionConnected = isDeviceAttached(HUION_VENDOR_ID, HUION_PRODUCT_ID)

    self.usbWatcher = hs.usb.watcher.new(function(d) self:handleUSBEvent(d) end)
    self.usbWatcher:start()
    print("✅ USB Device Watchers active.")
end

return deviceWatchers