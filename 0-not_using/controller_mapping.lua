-- Controller Mapping Module for Hammerspoon
-- This is a standalone module that can be loaded safely

local controller = {}

-- Configuration
controller.config = {
    export_file_path = "/Users/alex/ARfiles/Github/MacScripts/karabinder/ds4_export_latest.json",
    polling_interval = 0.016, -- ~60 FPS
    deadzone = 0.5,
    trigger_threshold = 128,
    enabled = false  -- Start disabled for safety
}

-- Button mappings (example)
controller.mappings = {
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
controller.states = {
    buttons = {},
    dpad = {},
    sticks = {left = {x = 0, y = 0}, right = {x = 0, y = 0}},
    triggers = {l2 = false, r2 = false}
}

-- Read controller data from JSON file
function controller:readData()
    local file = io.open(self.config.export_file_path, "r")
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
function controller:keyPress(key)
    if not self.config.enabled then
        print("Controller mapping disabled - would press:", key)
        return
    end
    
    print("KEY PRESS:", key)
    hs.eventtap.keyStroke({}, key)
end

-- Simulate key release  
function controller:keyRelease(key)
    if not self.config.enabled then
        print("Controller mapping disabled - would release:", key)
        return
    end
    
    print("KEY RELEASE:", key)
    -- Note: Hammerspoon doesn't have a direct key release function
    -- This is a simplified implementation
end

-- Process button inputs
function controller:processButtons(buttons)
    for button, key in pairs(self.mappings.buttons) do
        if buttons[button] then
            local pressed = buttons[button]
            
            if not self.states.buttons[button] then
                self.states.buttons[button] = false
            end
            
            if pressed and not self.states.buttons[button] then
                self:keyPress(key)
                self.states.buttons[button] = true
            elseif not pressed and self.states.buttons[button] then
                self:keyRelease(key)
                self.states.buttons[button] = false
            end
        end
    end
end

-- Process D-pad inputs
function controller:processDpad(dpad)
    for direction, key in pairs(self.mappings.dpad) do
        if dpad[direction] then
            local pressed = dpad[direction]
            
            if not self.states.dpad[direction] then
                self.states.dpad[direction] = false
            end
            
            if pressed and not self.states.dpad[direction] then
                self:keyPress(key)
                self.states.dpad[direction] = true
            elseif not pressed and self.states.dpad[direction] then
                self:keyRelease(key)
                self.states.dpad[direction] = false
            end
        end
    end
end

-- Process analog sticks
function controller:processSticks(sticks)
    for stick_name, mappings in pairs(self.mappings.sticks) do
        if sticks[stick_name] then
            local stick_data = sticks[stick_name]
            local x, y = stick_data.x, stick_data.y
            
            -- Apply deadzone
            if math.abs(x) < self.config.deadzone then x = 0 end
            if math.abs(y) < self.config.deadzone then y = 0 end
            
            local old_x, old_y = self.states.sticks[stick_name].x, self.states.sticks[stick_name].y
            
            -- X-axis
            if x > self.config.deadzone and old_x <= self.config.deadzone then
                self:keyPress(mappings.right)
            elseif x < -self.config.deadzone and old_x >= -self.config.deadzone then
                self:keyPress(mappings.left)
            elseif math.abs(x) <= self.config.deadzone and math.abs(old_x) > self.config.deadzone then
                self:keyRelease(mappings.left)
                self:keyRelease(mappings.right)
            end
            
            -- Y-axis
            if y > self.config.deadzone and old_y <= self.config.deadzone then
                self:keyPress(mappings.down)
            elseif y < -self.config.deadzone and old_y >= -self.config.deadzone then
                self:keyPress(mappings.up)
            elseif math.abs(y) <= self.config.deadzone and math.abs(old_y) > self.config.deadzone then
                self:keyRelease(mappings.up)
                self:keyRelease(mappings.down)
            end
            
            -- Update state
            self.states.sticks[stick_name].x = x
            self.states.sticks[stick_name].y = y
        end
    end
end

-- Process triggers
function controller:processTriggers(triggers)
    local trigger_mappings = {l2 = "3", r2 = "4"}
    
    for trigger, key in pairs(trigger_mappings) do
        if triggers[trigger] then
            local value = triggers[trigger]
            local pressed = value > self.config.trigger_threshold
            
            if pressed and not self.states.triggers[trigger] then
                self:keyPress(key)
                self.states.triggers[trigger] = true
            elseif not pressed and self.states.triggers[trigger] then
                self:keyRelease(key)
                self.states.triggers[trigger] = false
            end
        end
    end
end

-- Main processing function
function controller:process()
    local data = self:readData()
    
    if data then
        if data.buttons then
            self:processButtons(data.buttons)
        end
        if data.dpad then
            self:processDpad(data.dpad)
        end
        if data.sticks then
            self:processSticks(data.sticks)
        end
        if data.triggers then
            self:processTriggers(data.triggers)
        end
    end
end

-- Start the controller mapping
function controller:start()
    print("Starting controller mapping...")
    print("Make sure to export controller data from the GUI first")
    
    -- Create timer for polling
    self.timer = hs.timer.new(self.config.polling_interval, function()
        self:process()
    end)
    
    self.timer:start()
end

-- Stop the controller mapping
function controller:stop()
    if self.timer then
        self.timer:stop()
        print("Controller mapping stopped")
    end
end

-- Enable/disable key simulation
function controller:enable()
    self.config.enabled = true
    print("Controller mapping ENABLED - keys will be pressed")
end

function controller:disable()
    self.config.enabled = false
    print("Controller mapping DISABLED - keys will not be pressed")
end

-- Export for use in Hammerspoon
return controller 