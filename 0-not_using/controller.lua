-- Hammerspoon Controller Mapper
-- Receives DS4 data from Python script via UDP and maps it to key presses.

local json = require("hs.json")
local eventtap = require("hs.eventtap")

local controller = {}

-- ##################################################################
-- PASTE YOUR MAPPINGS HERE
-- Run your mapping_config.py and use the "Export for Hammerspoon"
-- button to generate this table. Then paste the contents below.
-- ##################################################################
controller.mappings = {
    buttons = {
        cross = "return",
        circle = "escape",
        square = "space",
        triangle = "tab",
        l1 = "1",
        r1 = "2",
        l2_pressed = "3",  -- L2 trigger press
        r2_pressed = "4",  -- R2 trigger press
        l3 = "f1",
        r3 = "f2",
        share = "cmd+s",
        options = "cmd+o",
        ps_button = "f5",  -- PS button
        touchpad_pressed = "f6",  -- Touchpad press
    },
    dpad = {
        up = "up",
        down = "down",
        left = "left",
        right = "right",
        ne = "e",    -- north-east (up-right)
        se = "c",    -- south-east (down-right)
        sw = "z",    -- south-west (down-left)
        nw = "q",    -- north-west (up-left)
    },
    sticks = {
        left = {
            up = "w",
            down = "s",
            left = "a",
            right = "d",
        },
        right = {
            up = "i",
            down = "k",
            left = "j",
            right = "l",
        }
    }
}
-- ##################################################################

-- State tracking to prevent continuous key presses
local previousState = {
    buttons = {},
    dpad = {},
    sticks = { left = {}, right = {} }
}

-- UDP socket to listen for data from Python
local udpSocket = nil
local UDP_PORT = 12345 -- Must match the port in your Python script

-- ## Core Mapping Logic ## --

-- Function to parse modifier + key combinations
function controller.parseKeyCombination(keyString)
    if not keyString or keyString == "" then
        return {}, ""
    end
    
    local parts = {}
    for part in keyString:gmatch("[^+]+") do
        table.insert(parts, part:lower())
    end
    
    local modifiers = {}
    local key = ""
    
    for i, part in ipairs(parts) do
        if part == "ctrl" then
            table.insert(modifiers, "ctrl")
        elseif part == "alt" then
            table.insert(modifiers, "alt")
        elseif part == "shift" then
            table.insert(modifiers, "shift")
        elseif part == "cmd" then
            table.insert(modifiers, "cmd")
        elseif part ~= "" then
            key = part
        end
    end
    
    -- If we have modifiers but no key, return empty (invalid combination)
    if #modifiers > 0 and key == "" then
        return {}, ""
    end
    
    return modifiers, key
end

function controller.processData(data)
    local status, decoded = pcall(json.decode, data)
    if not status then
        return
    end

    -- TRUE EVENT-BASED PROCESSING
    -- Only process if there's an actual event (button press, d-pad change, stick movement)
    local hasEvent = false
    local events = {}

    -- 1. Check for button events (only process if buttons changed)
    for button, key in pairs(controller.mappings.buttons) do
        local isPressed = decoded.buttons[button]
        local wasPressed = previousState.buttons[button] or false
        
        -- Rising edge detection (false -> true transition)
        if isPressed and not wasPressed then
            hasEvent = true
            table.insert(events, {type = "button", button = button, key = key})
        end
        previousState.buttons[button] = isPressed
    end

    -- 2. Check for D-Pad events (only process if d-pad changed)
    local currentDpad = decoded.dpad
    local previousDpad = previousState.dpad.current or "none"
    
    if currentDpad ~= previousDpad then
        hasEvent = true
        -- Direct mapping from Python script values to directions
        local dpadToDirection = {
            ["up"] = "up",
            ["down"] = "down", 
            ["left"] = "left",
            ["right"] = "right",
            ["ne"] = "ne",    -- diagonal up-right
            ["se"] = "se",    -- diagonal down-right
            ["sw"] = "sw",    -- diagonal down-left
            ["nw"] = "nw"     -- diagonal up-left
        }
        
        -- Trigger on button RELEASE (when going from a direction back to "none")
        if currentDpad == "none" and previousDpad ~= "none" then
            local direction = dpadToDirection[previousDpad]
            if direction and controller.mappings.dpad[direction] then
                table.insert(events, {type = "dpad", direction = direction, key = controller.mappings.dpad[direction]})
            end
        end
        previousState.dpad.current = currentDpad
    end
    
    -- 3. Check for stick events (only process if sticks moved beyond threshold)
    local stickThreshold = 0.8
    local leftStick = decoded.left_stick
    local rightStick = decoded.right_stick
    
    -- Left Stick events
    if leftStick then
        local directions = {
            {name = "up", condition = leftStick.y < -stickThreshold, key = controller.mappings.sticks.left.up},
            {name = "down", condition = leftStick.y > stickThreshold, key = controller.mappings.sticks.left.down},
            {name = "left", condition = leftStick.x < -stickThreshold, key = controller.mappings.sticks.left.left},
            {name = "right", condition = leftStick.x > stickThreshold, key = controller.mappings.sticks.left.right}
        }
        
        for _, dir in ipairs(directions) do
            local wasActive = previousState.sticks.left[dir.name] or false
            if dir.condition and not wasActive then
                hasEvent = true
                table.insert(events, {type = "left_stick", direction = dir.name, key = dir.key})
            end
            previousState.sticks.left[dir.name] = dir.condition
        end
    end
    
    -- Right Stick events
    if rightStick then
        local directions = {
            {name = "up", condition = rightStick.y < -stickThreshold, key = controller.mappings.sticks.right.up},
            {name = "down", condition = rightStick.y > stickThreshold, key = controller.mappings.sticks.right.down},
            {name = "left", condition = rightStick.x < -stickThreshold, key = controller.mappings.sticks.right.left},
            {name = "right", condition = rightStick.x > stickThreshold, key = controller.mappings.sticks.right.right}
        }
        
        for _, dir in ipairs(directions) do
            local wasActive = previousState.sticks.right[dir.name] or false
            if dir.condition and not wasActive then
                hasEvent = true
                table.insert(events, {type = "right_stick", direction = dir.name, key = dir.key})
            end
            previousState.sticks.right[dir.name] = dir.condition
        end
    end
    
    -- 4. Process all events at once (only if there are events)
    if hasEvent then
        for _, event in ipairs(events) do
            if event.type == "button" then
                print("🎮 Button pressed: " .. event.button .. " -> Key: " .. event.key)
            elseif event.type == "dpad" then
                print("🎮 D-pad pressed: " .. event.direction .. " -> Key: " .. event.key)
            elseif event.type == "left_stick" then
                print("🎮 Left stick " .. event.direction .. " -> Key: " .. event.key)
            elseif event.type == "right_stick" then
                print("🎮 Right stick " .. event.direction .. " -> Key: " .. event.key)
            end
            
            -- Parse modifier + key combination
            local modifiers, key = controller.parseKeyCombination(event.key)
            if key and key ~= "" then
                eventtap.keyStroke(modifiers, key)
            end
        end
    end
end


-- ## Socket Control ## --

function controller:start()
    if udpSocket then
        print("Controller mapper already running.")
        return
    end
    
    print("Starting controller mapper...")
    udpSocket = hs.socket.udp.new()
    udpSocket:setCallback(controller.processData)
    
    local success = udpSocket:listen(UDP_PORT)
    if success then
        udpSocket:receive()
        hs.notify.new({title="Controller Active", informativeText="DS4 mapping is ON."}):send()
    else
        hs.notify.new({title="Controller Error", informativeText="Could not listen on port " .. UDP_PORT}):send()
        udpSocket = nil
    end
end

function controller:stop()
    if udpSocket then
        print("Stopping controller mapper...")
        udpSocket:close()
        udpSocket = nil
        hs.notify.new({title="Controller Inactive", informativeText="DS4 mapping is OFF."}):send()
    else
        print("Controller mapper is not running.")
    end
end

-- Start automatically
controller:start()

return controller 