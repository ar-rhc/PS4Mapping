-- ~/.hammerspoon/init.lua
-- Main configuration file - loads all modules.




hs.ipc.cliInstall() -- Ensure Hammerspoon CLI is available
require("hs.ipc")
hs.ipc.cliInstall()


require("modules.controller")

-- Load and start the auto-reloader first
local reloader = require("modules.reloader")
reloader:start()

-- Load and start your DS4 controller mapping script
require("modules.controller")
-- require("modules.lightbar_manager")
local hybrid_controller = require("modules.hybrid_controller")

-- Load and start the device watchers (Huion Tablet and DS4 Controller)
local deviceWatchers = require("modules.device_watchers")
deviceWatchers:start()

-- Load and start the advanced window management module
local windowManager = require("modules.window_management")
windowManager:start()

-- Load utilities (they don't need to be started, just loaded for console use)
require("modules.utils")

print("✅ All Hammerspoon modules loaded successfully.") 



function sendCommandToUI(command)
    -- This is the single, correct line for sending a UDP packet.
    hs.socket.udp.sendto('127.0.0.1', 12346, command)
end

-- Global hotkey to TOGGLE the DS4 configurator window
hs.hotkey.bind({"shift", "ctrl", "cmd"}, "-", function()
    print("Hotkey pressed, telling DS4 Configurator to toggle visibility.")
    sendCommandToUI("toggle_window")
end)