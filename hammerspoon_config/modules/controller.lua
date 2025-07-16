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

-- New, simplified data processing function for string-based events
function controller.processData(data)
    -- Expected format: "eventType,buttonName" (e.g., "press,cross")
    local eventType, buttonName = data:match("([^,]+),([^,]+)")

    if not eventType or not buttonName then
        -- print("Invalid data format received: " .. data)
        return
    end

    if eventType == "press" then
        local appName = getActiveAppName()
        local profile = getProfile(appName)
        
        if not profile then return end

        local mapping = nil
        local dpadMatch = buttonName:match(dpad_pattern)

        if dpadMatch then
            -- It's a D-pad button
            if profile.dpad then
                mapping = profile.dpad[dpadMatch]
            end
        else
            -- It's a regular button
            if profile.buttons then
                mapping = profile.buttons[buttonName]
            end
        end

        if mapping then
            postKeyEvent(mapping)
        end
    end
    -- "release" events are ignored for now, but can be handled here in the future.
end


-- ## UDP LISTENER ## --
function controller.startListener(host, port)
    -- Stop any existing listener before starting a new one
    controller.stopListener()

    -- Create a UDP server socket, which binds and sets the callback in one step.
    -- This is the correct and most efficient way to create a UDP listener in Hammerspoon.
    local sock = hs.socket.udp.server(port, function(data, from_host, from_port)
        if data and #data > 0 then
            controller.processData(data)
        end
    end)

    if not sock then
        print(string.format("🛑 Failed to create or bind UDP server on port %d", port))
        return
    end
    
    -- Start receiving data.
    sock:receive()

    print(string.format("🎧 Controller UDP listener started on %s:%d", host, port))
    
    -- Store the socket so we can close it later
    controller.listener_socket = sock
end

function controller.stopListener()
    if controller.listener_socket then
        controller.listener_socket:close()
        controller.listener_socket = nil
        print("🛑 Controller UDP listener stopped.")
    end
end

return controller