-- lightbar_manager.lua (Final, Command-Line Version)
-- This script uses hs.window.filter and executes an external Python script to set the lightbar color.

local json = require("hs.json")
local fs = require("hs.fs")
local application = require("hs.application")
local task = require("hs.task")
local windowFilter = require("hs.window.filter")

-- ## PERSISTENT STATE ## --
-- These are stored in the global table to survive script reloads.
if _G.lightbarManager == nil then
    _G.lightbarManager = {
        lastProfileName = "",
        forceUpdate = false
    }
end

-- ## CONFIGURATION ## --
local MAPPINGS_FILE = os.getenv("HOME") .. "/.hammerspoon/mappings.json"
local PYTHON_EXECUTABLE = "/opt/homebrew/bin/python3.11"
local SET_LIGHTBAR_SCRIPT = "/Users/alex/ARfiles/Github/MacScripts/karabinder/main_scripts/set_lightbar.py"

-- ## STATE (local to this script's execution) ## --
local mappings = {}
local profileCache = {}

-- ## HELPER FUNCTIONS ## --

-- Reads a file and returns its content.
local function readFile(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local content = f:read("*a")
    f:close()
    return content
end

-- Executes the python script to set the lightbar color.
local function sendLightbarCommand(r, g, b)
    local args = {
        SET_LIGHTBAR_SCRIPT,
        tostring(r),
        tostring(g),
        tostring(b)
    }

    -- hs.task is asynchronous and will not block Hammerspoon.
    task.new(PYTHON_EXECUTABLE, function(exitCode, stdOut, stdErr)
        if exitCode ~= 0 then
            print("LightbarManager: ❌ Script execution failed! Exit Code: " .. tostring(exitCode))
            if stdOut and #stdOut > 0 then print("LightbarManager: stdout: " .. stdOut) end
            if stdErr and #stdErr > 0 then print("LightbarManager: stderr: " .. stdErr) end
        end
    end, args):start()
end

-- Loads and decodes the mappings from the JSON file.
local function loadMappings()
    local content = readFile(MAPPINGS_FILE)
    if not content then
        print("LightbarManager: Mappings file not found.")
        return {}
    end
    local ok, decoded = pcall(json.decode, content)
    if not ok then
        print("LightbarManager: Error decoding mappings.json: " .. tostring(decoded))
        return {}
    end
    return decoded
end

-- Finds a matching profile for the given application name.
local function fuzzyMatch(profileName, appName)
    if not profileName or not appName then return false end
    local profileLower, appLower = profileName:lower(), appName:lower()
    if profileLower == appLower then return true end
    -- Also check if the profile name is a substring of the app name, or vice-versa.
    return profileLower:find(appLower, 1, true) or appLower:find(profileLower, 1, true)
end

-- Gets the profile for the current application, using a cache for efficiency.
local function getProfile(appName)
    if profileCache[appName] then
        return profileCache[appName].data, profileCache[appName].name
    end
    local profileData, profileName = nil, nil
    if mappings[appName] then
        profileData, profileName = mappings[appName], appName
    else
        for pName, pData in pairs(mappings) do
            if pName ~= "Default" and fuzzyMatch(pName, appName) then
                profileData, profileName = pData, pName
                break
            end
        end
    end
    if not profileData then
        profileData, profileName = mappings["Default"], "Default"
    end
    profileCache[appName] = { data = profileData, name = profileName }
    return profileData, profileName
end

-- ## CORE LOGIC ## --

-- This is the main function that triggers when an application changes.
local function updateLightbarForApp(appName)
    if not appName then return end

    local profile, profileName = getProfile(appName)

    -- Only update if the profile has actually changed, or if an update is forced.
    if _G.lightbarManager.forceUpdate or (profileName and profileName ~= _G.lightbarManager.lastProfileName) then
        print(string.format("LightbarManager: Profile changed to '%s'. Updating color.", profileName))
        _G.lightbarManager.lastProfileName = profileName -- Store the new profile name
        _G.lightbarManager.forceUpdate = false -- Consume the force flag

        if profile and profile.lightbar then
            local r, g, b
            if profile.lightbar[1] then -- Check if it's an array
                r, g, b = table.unpack(profile.lightbar)
            else -- Assume it's a dictionary with r,g,b keys
                r, g, b = profile.lightbar.r, profile.lightbar.g, profile.lightbar.b
            end
            sendLightbarCommand(r, g, b)
        end
    end
end

-- ## INITIALIZATION AND WATCHERS ## --

-- Load initial mappings
mappings = loadMappings()

-- Watchers must be stored in variables to prevent garbage collection.

-- Watch for window focus changes, which is often more reliable than watching applications.
local windowWatcher = windowFilter.new()
windowWatcher:subscribe(windowFilter.windowFocused, function(window, appName)
    -- DEBUG: Print every time the focus changes to see what's triggering the event.
    print(string.format("LightbarManager: DEBUG - Window focused. App: '%s'", tostring(appName)))
    updateLightbarForApp(appName)
end)

-- On reload, clear the cache to pick up any manual changes to mappings.json
profileCache = {}

-- Set the initial color when the script is first loaded/reloaded.
local currentApp = application.frontmostApplication()
if currentApp then
    updateLightbarForApp(currentApp:name())
end

print("LightbarManager: ✅ Started/Reloaded.") 