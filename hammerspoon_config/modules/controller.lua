-- Hammerspoon Controller - Optimized Version
-- This script contains all logic and now loads its mappings from an external mappings.json file.

local eventtap = require("hs.eventtap")
local json = require("hs.json")
local fs = require("hs.fs")
local pathwatcher = require("hs.pathwatcher")

local controller = {}
local MAPPINGS_FILE = os.getenv("HOME") .. "/.hammerspoon/mappings.json"

-- Add a portable file read function
local function readFile(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local content = f:read("*a")
    f:close()
    return content
end

-- ## MAPPING LOADER ## --
function controller.loadMappings()
    local content = readFile(MAPPINGS_FILE)
    if not content then
        print("⚠️ Controller mappings file not found at: " .. MAPPINGS_FILE)
        return {}
    end
    
    local status, decoded = pcall(json.decode, content)
    if not status then
        print("🛑 Error decoding mappings.json: " .. tostring(decoded))
        return {}
    end
    
    print("✅ Controller mappings reloaded.")
    return decoded
end

-- Load mappings on start
controller.mappings = controller.loadMappings()

-- Watch for changes to the mappings file and reload them automatically
local watcher = pathwatcher.new(MAPPINGS_FILE, function()
    controller.mappings = controller.loadMappings()
    -- Clear profile cache when mappings change
    controller.profileCache = {}
end):start()

-- ## OPTIMIZATION: PROFILE CACHE ## --
controller.profileCache = {}

-- ## EVENT PROCESSING LOGIC ## --

local previousState = {}
local bttTriggerTimestamps = {}

-- Pre-compiled regex patterns for faster matching
local dpad_pattern = "^dpad_(.+)$"

-- Critical buttons for immediate processing
local criticalButtons = {cross=true, circle=true, triangle=true, square=true, options=true}

-- Cache for active app name to avoid repeated calls
local lastActiveApp = nil
local lastActiveAppTime = 0
local APP_CACHE_DURATION = 0.1 -- Cache app name for 100ms

local function translateKey(key)
    local keyTranslations = {['backspace'] = 'delete', ['enter'] = 'return', ['esc'] = 'escape'}
    return keyTranslations[key:lower()] or key:lower()
end

-- Optimized fuzzy matching function for profile names
local function fuzzyMatch(profileName, appName)
    if not profileName or not appName then return false end
    
    -- Convert to lowercase for comparison
    local profileLower = profileName:lower()
    local appLower = appName:lower()
    
    -- Exact match
    if profileLower == appLower then return true end
    
    -- Check if profile name contains app name or vice versa
    if profileLower:find(appLower, 1, true) or appLower:find(profileLower, 1, true) then
        return true
    end
    
    -- Split into words and check for word matches
    local profileWords = {}
    for word in profileLower:gmatch("%S+") do
        table.insert(profileWords, word)
    end
    
    local appWords = {}
    for word in appLower:gmatch("%S+") do
        table.insert(appWords, word)
    end
    
    -- Check if any significant words match (ignore common words)
    local commonWords = {["the"] = true, ["a"] = true, ["an"] = true, ["and"] = true, ["or"] = true, ["of"] = true, ["in"] = true, ["on"] = true, ["at"] = true, ["to"] = true, ["for"] = true, ["with"] = true, ["by"] = true, ["classic"] = true, ["pro"] = true, ["lite"] = true, ["adobe"] = true}
    
    for _, profileWord in ipairs(profileWords) do
        if not commonWords[profileWord] and #profileWord > 2 then
            for _, appWord in ipairs(appWords) do
                if not commonWords[appWord] and #appWord > 2 then
                    if profileWord == appWord or profileWord:find(appWord, 1, true) or appWord:find(profileWord, 1, true) then
                        return true
                    end
                end
            end
        end
    end
    
    return false
end

-- Optimized profile lookup with caching
local function getProfile(appName)
    -- Check cache first
    if controller.profileCache[appName] then
        return controller.profileCache[appName]
    end
    
    -- Try exact match first
    local profile = controller.mappings[appName]
    
    -- If no exact match, try fuzzy matching
    if not profile then
        for profileName, profileData in pairs(controller.mappings) do
            if profileName ~= "Default" and fuzzyMatch(profileName, appName) then
                profile = profileData
                break
            end
        end
    end
    
    -- Fall back to Default profile
    if not profile then
        profile = controller.mappings["Default"]
    end
    
    -- Cache the result
    controller.profileCache[appName] = profile
    return profile
end

-- Optimized active app lookup with caching
local function getActiveAppName()
    local now = hs.timer.secondsSinceEpoch()
    
    -- Return cached app name if still valid
    if lastActiveApp and (now - lastActiveAppTime) < APP_CACHE_DURATION then
        return lastActiveApp
    end
    
    -- Get fresh app name
    local activeApp = hs.application.frontmostApplication()
    local appName = activeApp and activeApp:name() or "Default"
    
    -- Update cache
    lastActiveApp = appName
    lastActiveAppTime = now
    
    return appName
end

function postKeyEvent(mapping)
    if not mapping then return end

    if mapping.bttnamekey then
        local now = hs.timer.secondsSinceEpoch()
        local lastTriggered = bttTriggerTimestamps[mapping.bttnamekey] or 0
        local cooldown = 0.05  -- Ultra-low latency: 50ms cooldown for immediate response

        if (now - lastTriggered) > cooldown then
            bttTriggerTimestamps[mapping.bttnamekey] = now
            local appleScriptCommand = 'tell application "BetterTouchTool" to trigger_named "' .. mapping.bttnamekey .. '"'
            hs.osascript.applescript(appleScriptCommand)
        end
        return
    end

    if mapping.key then
        local mods = mapping.modifiers or {}
        local key = translateKey(mapping.key)
        
        -- Convert modifier names to Hammerspoon format
        local hsMods = {}
        if mods.cmd then table.insert(hsMods, "cmd") end
        if mods.ctrl then table.insert(hsMods, "ctrl") end
        if mods.alt then table.insert(hsMods, "alt") end
        if mods.shift then table.insert(hsMods, "shift") end
        
        hs.eventtap.keyStroke(hsMods, key)
    end
end

-- Ultra-low latency button event handling with immediate activation
local function handleButtonEvents(newButtons, oldButtons, buttonMappings)
    if not buttonMappings then return end
    for button, isPressed in pairs(newButtons) do
        local wasPressed = oldButtons[button] or false
        
        -- Immediate activation: trigger on button press (rising edge)
        if isPressed and not wasPressed then
            -- OPTIMIZATION: Process critical buttons immediately
            if criticalButtons[button] then
                -- Use immediate execution for critical buttons
                postKeyEvent(buttonMappings[button])
            else
                -- Use timer for non-critical buttons to avoid blocking
                hs.timer.doAfter(0.001, function() postKeyEvent(buttonMappings[button]) end)
            end
        end
    end
end

-- Optimized D-pad event handling with press-down activation
local function handleDpadEvents(newDpad, oldDpad, dpadMappings)
    if not dpadMappings then return end
    if newDpad ~= "none" and newDpad ~= oldDpad then
        postKeyEvent(dpadMappings[newDpad])
    end
end

-- Binary packet parser for DS4 (8 bytes)
local function parseBinaryPacket(data)
    if not data or #data ~= 8 then return nil end
    local bytes = {string.byte(data, 1, 8)}
    local header = bytes[1]
    if header ~= 0x44 then return nil end -- 'D' for DS4
    local button_low = bytes[2]
    local button_high = bytes[3]
    local dpad_value = bytes[4]
    local timestamp_low = bytes[5] + bytes[6] * 256
    local timestamp_high = bytes[7] + bytes[8] * 256
    local button_flags = button_low + (button_high * 256)
    local button_names = {
        'square', 'cross', 'circle', 'triangle',
        'l1', 'r1', 'l2_pressed', 'r2_pressed',
        'share', 'options', 'l3', 'r3',
        'ps_button', 'touchpad_pressed', 'unused1', 'unused2'
    }
    local buttons = {}
    for i, name in ipairs(button_names) do
        buttons[name] = (button_flags & (1 << (i-1))) ~= 0
    end
    local dpad_names = {'none', 'up', 'down', 'left', 'right', 'ne', 'se', 'sw', 'nw'}
    local dpad = dpad_names[dpad_value+1] or 'none'
    local timestamp = timestamp_low + (timestamp_high * 65536)
    return {buttons = buttons, dpad = dpad, timestamp = timestamp / 1000.0}
end

function controller.processData(data)
    if not data then 
        return 
    end
    
    local decoded
    local status, result = pcall(json.decode, data)
    if status and result then
        decoded = result
    else
        -- Try binary protocol
        decoded = parseBinaryPacket(data)
        if not decoded then 
            return 
        end
    end
    
    local appName = getActiveAppName()
    local profile = getProfile(appName)
    if not profile then 
        return 
    end
    
    -- Handle event-based format from hybrid controller
    if decoded.event_type and decoded.button then
        
        -- Handle button press events
        if decoded.event_type == "press" then
            -- Check if it's a d-pad button using pre-compiled pattern
            local dpad_direction = decoded.button:match(dpad_pattern)
            if dpad_direction then
                if profile.dpad and profile.dpad[dpad_direction] then
                    postKeyEvent(profile.dpad[dpad_direction])
                end
            else
                -- Regular button - check if it's critical for immediate processing
                if profile.buttons and profile.buttons[decoded.button] then
                    if criticalButtons[decoded.button] then
                        -- Immediate execution for critical buttons
                        postKeyEvent(profile.buttons[decoded.button])
                    else
                        -- Deferred execution for non-critical buttons
                        hs.timer.doAfter(0.001, function() 
                            postKeyEvent(profile.buttons[decoded.button]) 
                        end)
                    end
                end
            end
        end
        -- Note: We ignore release events for now to avoid double-triggering
        return
    end
    
    -- Handle legacy format with buttons/dpad objects
    local oldState = previousState[appName] or {buttons={}, dpad="none"}
    handleButtonEvents(decoded.buttons, oldState.buttons, profile.buttons)
    handleDpadEvents(decoded.dpad, oldState.dpad, profile.dpad)
    previousState[appName] = decoded
end

-- ## UDP SOCKET FOR PYTHON SCRIPT ## --
local udpSocket = nil
local UDP_PORT = 12345 -- Must match the port in your Python script

function controller:start()
    if udpSocket then return end
    print("Starting controller listener...")
    
    -- Create UDP socket
    udpSocket = hs.socket.udp.new()
    
    -- Set up the callback
    udpSocket:setCallback(function(data, host, port)
        if data then
            controller.processData(data)
        end
    end)
    
    -- Listen on the port
    local listenSuccess = udpSocket:listen(UDP_PORT)
    if listenSuccess then
        udpSocket:receive()
        print("✅ UDP socket listening on port", UDP_PORT)
        hs.notify.new({title="Controller Active", informativeText="DS4 mapping is ON."}):send()
    else
        print("❌ Failed to listen on port", UDP_PORT)
        hs.notify.new({title="Controller Error", informativeText="Could not listen on port " .. UDP_PORT}):send()
        udpSocket = nil
    end
end

function controller:stop()
    if udpSocket then
        udpSocket:close()
        udpSocket = nil
    end
    if watcher then
        watcher:stop()
    end
end

controller:start()
return controller