-- Hammerspoon Controller Mapper (All-in-One HID Version)
--
-- This script directly connects to a DualShock 4 controller, parses its input,
-- and maps buttons to key events based on the active application.
-- The Python script is only needed to configure the mappings below.

local eventtap = require("hs.eventtap")
local hid = require("hs.hid")
local json = require("hs.json") -- Still useful for pretty-printing if needed

local controller = {}

-- Controller identification
local VENDOR_ID = 1356
local PRODUCT_ID = 2508

-- ##################################################################
-- MAPPINGS - THIS TABLE IS MANAGED BY THE PYTHON UI
-- ##################################################################
controller.mappings = {
    ["Default"] = {
        buttons = {},
        dpad = {}
    }
    -- Your Python UI will populate profiles here, e.g.:
    -- ["Code"] = { buttons = { cross = { key = "f5" } } }
}
-- ##################################################################


-- ## --- Application Profile Watcher --- ## --

local activeProfile = controller.mappings["Default"]
local previousState = { buttons = {}, dpad = "none" }

local appWatcher = hs.application.watcher.new(function(appName, eventType, appObject)
    if eventType == hs.application.watcher.activated then
        print("Switched Active App: " .. appName)
        activeProfile = controller.mappings[appName] or controller.mappings["Default"]
        previousState = { buttons = {}, dpad = "none" } -- Reset state on profile switch
    end
end)


-- ## --- Core HID Data Parsing --- ## --

-- Helper to convert a 16-bit unsigned value to a signed one (two's complement)
local function toSigned16(val)
    if val >= 32768 then
        return val - 65536
    end
    return val
end

-- This function parses the raw 64-byte report from the DS4 controller.
-- It's a direct translation of the logic from your Python script.
local function parseInputReport(report)
    local data = {
        buttons = {},
        dpad = "none"
    }

    -- Analog Sticks (Bytes 1-4, Python indices 1-4)
    -- Lua strings are 1-indexed, so we add 1 to Python indices.
    local leftStickX = (string.byte(report, 2) - 128) / 128.0
    local leftStickY = (string.byte(report, 3) - 128) / 128.0
    local rightStickX = (string.byte(report, 4) - 128) / 128.0
    local rightStickY = (string.byte(report, 5) - 128) / 128.0

    -- Button Bytes (Bytes 5-6, Python indices 5-6)
    local buttonByte1 = string.byte(report, 6)
    local buttonByte2 = string.byte(report, 7)

    -- D-Pad (bits 0-3 of buttonByte1)
    local dpadVal = bit32.band(buttonByte1, 0x0F)
    local dpadMap = { "up", "ne", "right", "se", "down", "sw", "left", "nw" }
    data.dpad = dpadMap[dpadVal + 1] or "none" -- Lua tables are 1-indexed

    -- Face Buttons & Shoulder Buttons
    data.buttons.square   = bit32.band(buttonByte1, 0x10) > 0
    data.buttons.cross    = bit32.band(buttonByte1, 0x20) > 0
    data.buttons.circle   = bit32.band(buttonByte1, 0x40) > 0
    data.buttons.triangle = bit32.band(buttonByte1, 0x80) > 0
    data.buttons.l1       = bit32.band(buttonByte2, 0x01) > 0
    data.buttons.r1       = bit32.band(buttonByte2, 0x02) > 0
    data.buttons.l2       = bit32.band(buttonByte2, 0x04) > 0 -- This is the L2 *button click*, not the trigger value
    data.buttons.r2       = bit32.band(buttonByte2, 0x08) > 0 -- This is the R2 *button click*
    data.buttons.share    = bit32.band(buttonByte2, 0x10) > 0
    data.buttons.options  = bit32.band(buttonByte2, 0x20) > 0
    data.buttons.l3       = bit32.band(buttonByte2, 0x40) > 0
    data.buttons.r3       = bit32.band(buttonByte2, 0x80) > 0
    
    -- PS and Touchpad buttons (Byte 7, Python index 7)
    local buttonByte3 = string.byte(report, 8)
    data.buttons.ps = bit32.band(buttonByte3, 0x01) > 0
    data.buttons.touchpad = bit32.band(buttonByte3, 0x02) > 0
    
    -- Gyro (Bytes 13-18, Python indices 13-18)
    local gyroX = toSigned16(string.byte(report, 14) + string.byte(report, 15) * 256)
    local gyroY = toSigned16(string.byte(report, 16) + string.byte(report, 17) * 256)
    local gyroZ = toSigned16(string.byte(report, 18) + string.byte(report, 19) * 256)

    return data
end


-- ## --- Event Handling Logic --- ## --

local function postKeyEvent(mapping)
    if not mapping or not mapping.key then return end
    local keyTranslations = {["backspace"] = "delete", ["enter"] = "return", ["esc"] = "escape"}
    local key = keyTranslations[mapping.key:lower()] or mapping.key:lower()
    hs.eventtap.keyStroke(mapping.modifiers or {}, key)
end

-- The main callback function called by hs.hid when data is received.
local function hidCallback(device, report)
    -- 1. Parse Data
    local currentState = parseInputReport(report)
    if not currentState then return end

    -- 2. Process Buttons
    if activeProfile and activeProfile.buttons then
        for button, isPressed in pairs(currentState.buttons) do
            if isPressed and not previousState.buttons[button] then
                postKeyEvent(activeProfile.buttons[button])
            end
        end
    end

    -- 3. Process D-Pad
    if activeProfile and activeProfile.dpad then
        if currentState.dpad ~= "none" and currentState.dpad ~= previousState.dpad then
            postKeyEvent(activeProfile.dpad[currentState.dpad])
        end
    end

    -- 4. Update State
    previousState = currentState
end


-- ## --- Device Management --- ## --

controller.device = nil

function controller:start()
    if controller.device then
        print("Controller already started.")
        return
    end

    print("Searching for DualShock 4 controller...")
    controller.device = hid.new(VENDOR_ID, PRODUCT_ID)

    if not controller.device then
        print("DS4 Controller not found.")
        hs.notify.new({title="Controller Error", informativeText="DS4 not found."}):send()
        return
    end
    
    print("DS4 Controller Found! Starting listener.")
    hs.notify.new({title="Controller Active", informativeText="DS4 mapping is ON."}):send()
    
    controller.device:setCallback(hidCallback)
    controller.device:start()
    appWatcher:start()
end

function controller:stop()
    if controller.device then
        print("Stopping controller listener.")
        controller.device:stop()
        controller.device = nil
        appWatcher:stop()
        hs.notify.new({title="Controller Inactive", informativeText="DS4 mapping is OFF."}):send()
    end
end


-- Auto-start the controller logic when Hammerspoon loads/reloads
controller:start()

return controller