-- console_hotkeys.lua
-- Adds hotkeys for clearing the console (Cmd+X) and opening config (Cmd+E).

local consoleHotkeys = {}
local keyWatcher

function consoleHotkeys:handleKeyEvent(event)
    local modifiers = event:getFlags()
    local keyPressed = hs.keycodes.map[event:getKeyCode()]
    
    local frontWindow = hs.window.frontmostWindow()
    if not (frontWindow and frontWindow:title() == "Hammerspoon Console") then
        return false
    end

    -- Cmd+X: Clear console
    if modifiers.cmd and not (modifiers.alt or modifiers.shift or modifiers.ctrl) and keyPressed == "x" then
        hs.console.clearConsole()
        return true
    end
    
    -- Cmd+E: Edit config in your preferred editor
    if modifiers.cmd and not (modifiers.alt or modifiers.shift or modifiers.ctrl) and keyPressed == "e" then
        local configPath = os.getenv("HOME") .. "/.hammerspoon/init.lua"
        -- CHANGE "Cursor" to your editor of choice (e.g., "Visual Studio Code", "TextEdit")
        hs.task.new("/usr/bin/open", nil, {"-a", "Cursor", configPath}):start()
        print("📝 Opening config in editor...")
        return true
    end

    return false
end

function consoleHotkeys:start()
    if keyWatcher then keyWatcher:stop() end
    keyWatcher = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(e) self:handleKeyEvent(e) end)
    keyWatcher:start()
    print("✅ Console hotkeys active.")
end

return consoleHotkeys