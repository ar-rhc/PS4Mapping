-- huion_watcher.lua
-- Watches for Huion tablet connection and launches the driver app.

local huionWatcher = {}

local TOUCHPAD_VENDOR_ID = 9580
local TOUCHPAD_PRODUCT_ID = 109
local usbWatcher

function huionWatcher:handleUSBEvent(device)
    if device and device.vendorID == TOUCHPAD_VENDOR_ID and device.productID == TOUCHPAD_PRODUCT_ID then
        -- A debounce timer ensures we only react once per event burst
        hs.timer.doAfter(1, function()
            if hs.usb.find(TOUCHPAD_VENDOR_ID, TOUCHPAD_PRODUCT_ID) then
                print("🖋️ Huion tablet connected - launching driver.")
                hs.application.launchOrFocus("HuionTablet")
            else
                print("🖋️ Huion tablet disconnected.")
            end
        end)
    end
end

function huionWatcher:start()
    if usbWatcher then usbWatcher:stop() end
    usbWatcher = hs.usb.watcher.new(function(d) self:handleUSBEvent(d) end)
    usbWatcher:start()
    print("✅ Huion tablet watcher active.")
end

return huionWatcher