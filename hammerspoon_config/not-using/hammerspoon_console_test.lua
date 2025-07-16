-- Self-contained Hammerspoon Console Test
-- Copy and paste this entire script into Hammerspoon Console

-- Configuration
local config = {
    polling_interval = 0.016, -- ~60 FPS
    deadzone = 0.5,
    trigger_threshold = 128,
    enabled = false  -- Start disabled for safety
}

-- Button mappings (example)
local mappings = {
    buttons = {
        square = "space",
        cross = "return", 
        circle = "escape",
        triangle = "tab",
        l1 = "1",
        r1 = "2",
        l3 = "5",
        r3 = "6",
        share = "7",
        options = "8",
        ps = "9",
        touchpad = "0"
    },
    dpad = {
        up = "up",
        down = "down",
        left = "left", 
        right = "right"
    },
    sticks = {
        left = {
            up = "w",
            down = "s",
            left = "a",
            right = "d"
        },
        right = {
            up = "i",
            down = "k", 
            left = "j",
            right = "l"
        }
    }
}

-- State tracking
local states = {
    buttons = {},
    dpad = {},
    sticks = {left = {x = 0, y = 0}, right = {x = 0, y = 0}},
    triggers = {l2 = false, r2 = false}
}

-- Global timer
local timer = nil

-- Read controller data from JSON file
function readData()
    -- Look for the most recent export file
    local export_dir = "/Users/alex/ARfiles/Github/MacScripts/karabinder"
    local files = hs.fs.dir(export_dir)
    local export_files = {}
    
    if files then
        for file in files do
            if file:match("^ds4_data_export_.*%.json$") then
                table.insert(export_files, file)
            end
        end
    end
    
    if #export_files == 0 then
        print("No export files found. Make sure to export data from the GUI first.")
        return nil
    end
    
    -- Get the most recent file
    table.sort(export_files, function(a, b)
        local path_a = export_dir .. "/" .. a
        local path_b = export_dir .. "/" .. b
        return hs.fs.attributes(path_a, "modification") > hs.fs.attributes(path_b, "modification")
    end)
    
    local latest_file = export_dir .. "/" .. export_files[1]
    print("Reading from:", latest_file)
    
    local file = io.open(latest_file, "r")
    if not file then
        return nil
    end
    
    local content = file:read("*all")
    file:close()
    
    local success, data = pcall(function()
        return hs.json.decode(content)
    end)
    
    if success then
        return data
    else
        print("Error parsing JSON:", data)
        return nil
    end
end

-- Simulate key press (with safety check)
function keyPress(key)
    if not config.enabled then
        print("Controller mapping disabled - would press:", key)
        return
    end
    
    print("KEY PRESS:", key)
    hs.eventtap.keyStroke({}, key)
end

-- Simulate key release  
function keyRelease(key)
    if not config.enabled then
        print("Controller mapping disabled - would release:", key)
        return
    end
    
    print("KEY RELEASE:", key)
    -- Note: Hammerspoon doesn't have a direct key release function
    -- This is a simplified implementation
end

-- Process button inputs
function processButtons(buttons)
    for button, key in pairs(mappings.buttons) do
        if buttons[button] then
            local pressed = buttons[button]
            
            if not states.buttons[button] then
                states.buttons[button] = false
            end
            
            if pressed and not states.buttons[button] then
                keyPress(key)
                states.buttons[button] = true
            elseif not pressed and states.buttons[button] then
                keyRelease(key)
                states.buttons[button] = false
            end
        end
    end
end

-- Process D-pad inputs
function processDpad(dpad)
    for direction, key in pairs(mappings.dpad) do
        if dpad[direction] then
            local pressed = dpad[direction]
            
            if not states.dpad[direction] then
                states.dpad[direction] = false
            end
            
            if pressed and not states.dpad[direction] then
                keyPress(key)
                states.dpad[direction] = true
            elseif not pressed and states.dpad[direction] then
                keyRelease(key)
                states.dpad[direction] = false
            end
        end
    end
end

-- Process analog sticks
function processSticks(sticks)
    for stick_name, stick_mappings in pairs(mappings.sticks) do
        if sticks[stick_name] then
            local stick_data = sticks[stick_name]
            local x, y = stick_data.x, stick_data.y
            
            -- Apply deadzone
            if math.abs(x) < config.deadzone then x = 0 end
            if math.abs(y) < config.deadzone then y = 0 end
            
            local old_x, old_y = states.sticks[stick_name].x, states.sticks[stick_name].y
            
            -- X-axis
            if x > config.deadzone and old_x <= config.deadzone then
                keyPress(stick_mappings.right)
            elseif x < -config.deadzone and old_x >= -config.deadzone then
                keyPress(stick_mappings.left)
            elseif math.abs(x) <= config.deadzone and math.abs(old_x) > config.deadzone then
                keyRelease(stick_mappings.left)
                keyRelease(stick_mappings.right)
            end
            
            -- Y-axis
            if y > config.deadzone and old_y <= config.deadzone then
                keyPress(stick_mappings.down)
            elseif y < -config.deadzone and old_y >= -config.deadzone then
                keyPress(stick_mappings.up)
            elseif math.abs(y) <= config.deadzone and math.abs(old_y) > config.deadzone then
                keyRelease(stick_mappings.up)
                keyRelease(stick_mappings.down)
            end
            
            -- Update state
            states.sticks[stick_name].x = x
            states.sticks[stick_name].y = y
        end
    end
end

-- Process triggers
function processTriggers(triggers)
    local trigger_mappings = {l2 = "3", r2 = "4"}
    
    for trigger, key in pairs(trigger_mappings) do
        if triggers[trigger] then
            local value = triggers[trigger]
            local pressed = value > config.trigger_threshold
            
            if pressed and not states.triggers[trigger] then
                keyPress(key)
                states.triggers[trigger] = true
            elseif not pressed and states.triggers[trigger] then
                keyRelease(key)
                states.triggers[trigger] = false
            end
        end
    end
end

-- Main processing function
function process()
    local data = readData()
    
    if data then
        if data.buttons then
            processButtons(data.buttons)
        end
        if data.dpad then
            processDpad(data.dpad)
        end
        if data.sticks then
            processSticks(data.sticks)
        end
        if data.triggers then
            processTriggers(data.triggers)
        end
    end
end

-- Start the controller mapping
function startMapping()
    print("Starting controller mapping...")
    print("Make sure to export controller data from the GUI first")
    
    if timer then
        timer:stop()
    end
    
    -- Create timer for polling
    timer = hs.timer.new(config.polling_interval, function()
        process()
    end)
    
    timer:start()
    print("✅ Controller mapping started")
end

-- Stop the controller mapping
function stopMapping()
    if timer then
        timer:stop()
        print("Controller mapping stopped")
    end
end

-- Enable/disable key simulation
function enableMapping()
    config.enabled = true
    print("Controller mapping ENABLED - keys will be pressed")
end

function disableMapping()
    config.enabled = false
    print("Controller mapping DISABLED - keys will not be pressed")
end

-- Test function
function testController()
    print("=== Controller Mapping Test ===")
    print("1. Testing data reading...")
    
    local data = readData()
    if data then
        print("✅ Data file found and parsed")
        print("   Buttons:", hs.inspect(data.buttons))
        print("   Sticks:", hs.inspect(data.sticks))
        
        print("2. Starting controller mapping (DISABLED mode)...")
        startMapping()
        print("   Keys will NOT be pressed (safety mode)")
        
        print("3. Available commands:")
        print("   enableMapping()  - Enable key pressing")
        print("   disableMapping() - Disable key pressing")
        print("   stopMapping()    - Stop mapping")
        
        return true
    else
        print("❌ No data file found or parsing error")
        print("   Make sure to export data from the GUI first")
        return false
    end
end

-- Return module table
return {
    start = startMapping,
    stop = stopMapping,
    enable = enableMapping,
    disable = disableMapping,
    test = testController,
    readData = readData,
    process = process
} 