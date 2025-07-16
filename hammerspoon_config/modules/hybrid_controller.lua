-- Hybrid PS4 Controller - Hammerspoon Receiver
-- This script handles events from the hybrid controller

local eventtap = require("hs.eventtap")
local json = require("hs.json")
local fs = require("hs.fs")
local pathwatcher = require("hs.pathwatcher")

local hybrid_controller = {}
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
function hybrid_controller.loadMappings()
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
hybrid_controller.mappings = hybrid_controller.loadMappings()

-- Watch for changes to the mappings file and reload them automatically
local watcher = pathwatcher.new(MAPPINGS_FILE, function()
    hybrid_controller.mappings = hybrid_controller.loadMappings()
    -- Clear profile cache when mappings change
    hybrid_controller.profileCache = {}
end):start()

-- ## OPTIMIZATION: PROFILE CACHE ## --
hybrid_controller.profileCache = {}

-- ## EVENT PROCESSING LOGIC ## --

local buttonStates = {}  -- Track button states for press/release events
local bttTriggerTimestamps = {}

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
    if hybrid_controller.profileCache[appName] then
        return hybrid_controller.profileCache[appName]
    end
    
    -- Try exact match first
    local profile = hybrid_controller.mappings[appName]
    
    -- If no exact match, try fuzzy matching
    if not profile then
        for profileName, profileData in pairs(hybrid_controller.mappings) do
            if profileName ~= "Default" and fuzzyMatch(profileName, appName) then
                profile = profileData
                break
            end
        end
    end
    
    -- Fall back to Default profile
    if not profile then
        profile = hybrid_controller.mappings["Default"]
    end
    
    -- Cache the result
    hybrid_controller.profileCache[appName] = profile
    return profile
end

function postKeyEvent(mapping)
    if not mapping then return end

    if mapping.bttnamekey then
        local now = hs.timer.secondsSinceEpoch()
        local lastTriggered = bttTriggerTimestamps[mapping.bttnamekey] or 0
        local cooldown = 0.05  -- Ultra-low latency: 50ms cooldown

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
        if mods.opt then table.insert(hsMods, "alt") end  -- 'opt' becomes 'alt' in Hammerspoon
        if mods.shift then table.insert(hsMods, "shift") end
        
        hs.eventtap.keyStroke(hsMods, key)
    end
end

-- Handle hybrid controller events
local function handleHybridEvent(event)
    local eventType = event.event_type
    local button = event.button
    local timestamp = event.timestamp
    
    -- Get current active app
    local activeApp = hs.application.frontmostApplication()
    local appName = activeApp and activeApp:name() or "Default"
    local profile = getProfile(appName)
    
    if not profile then 
        print("DEBUG: No profile found for app:", appName)
        return 
    end
    
    print("DEBUG: Processing", eventType, "event for", button, "in app:", appName)
    
    -- Handle button events
    if eventType == "press" then
        -- Check if button is mapped
        local mapping = profile.buttons[button]
        if mapping then
            -- Process critical buttons immediately
            local criticalButtons = {cross=true, circle=true, triangle=true, square=true, options=true}
            if criticalButtons[button] then
                postKeyEvent(mapping)
            else
                -- Use timer for non-critical buttons
                hs.timer.doAfter(0.001, function() postKeyEvent(mapping) end)
            end
        end
        
        -- Handle d-pad events
        if button:match("^dpad_") then
            local dpadDirection = button:match("^dpad_(.+)")
            local dpadMapping = profile.dpad[dpadDirection]
            if dpadMapping then
                postKeyEvent(dpadMapping)
            end
        end
        
        -- Update button state
        buttonStates[button] = true
        
    elseif eventType == "release" then
        -- Update button state
        buttonStates[button] = false
    end
end

function hybrid_controller.processData(data)
    if not data then 
        print("DEBUG: No data received")
        return 
    end
    print("DEBUG: Received data, length:", #data)
    
    local decoded
    local status, result = pcall(json.decode, data)
    if status and result then
        print("DEBUG: JSON parsing succeeded")
        decoded = result
    else
        print("DEBUG: JSON parsing failed")
        return
    end
    
    -- Handle hybrid controller event
    if decoded.event_type and decoded.button then
        handleHybridEvent(decoded)
    else
        print("DEBUG: Invalid event format")
    end
end

-- ## UDP SOCKET FOR HYBRID CONTROLLER ## --
local udpSocket = nil
local UDP_PORT = 12345

function hybrid_controller:start()
    if udpSocket then return end
    print("Starting hybrid controller listener...")
    
    -- Create UDP socket
    udpSocket = hs.socket.udp.new()
    
    -- Set up the callback
    udpSocket:setCallback(function(data, host, port)
        print("DEBUG: UDP callback from", host, "port", port, "data length:", data and #data or "nil")
        if data then
            hybrid_controller.processData(data)
        end
    end)
    
    -- Listen on the port
    local listenSuccess = udpSocket:listen(UDP_PORT)
    if listenSuccess then
        udpSocket:receive()
        print("✅ Hybrid controller UDP socket listening on port", UDP_PORT)
        hs.notify.new({title="Hybrid Controller Active", informativeText="PS4 mapping is ON."}):send()
    else
        print("❌ Failed to listen on port", UDP_PORT)
        hs.notify.new({title="Hybrid Controller Error", informativeText="Could not listen on port " .. UDP_PORT}):send()
        udpSocket = nil
    end
end

function hybrid_controller:stop()
    if udpSocket then
        udpSocket:close()
        udpSocket = nil
    end
    if watcher then
        watcher:stop()
    end
end

hybrid_controller:start()
return hybrid_controller 