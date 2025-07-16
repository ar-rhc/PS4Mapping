-- modules/console_hotkeys.lua
-- Adds hotkeys for clearing the console (Cmd+X) and opening config (Cmd+E).

local consoleHotkeys = {}

function consoleHotkeys:handleKeyEvent(event)
    local modifiers = event:getFlags()
    local keyPressed = hs.keycodes.map[event:getKeyCode()]
    
    local frontWindow = hs.window.frontmostWindow()
    if not (frontWindow and frontWindow:title() == "Hammerspoon Console") then
        return false -- Event was not for the console, let it pass
    end

    -- Cmd+X: Clear console
    if modifiers.cmd and not (modifiers.alt or modifiers.shift or modifiers.ctrl) and keyPressed == "x" then
        hs.console.clearConsole()
        return true -- Event handled
    end
    
    -- Cmd+E: Edit config in your preferred editor
    if modifiers.cmd and not (modifiers.alt or modifiers.shift or modifiers.ctrl) and keyPressed == "e" then
        local configPath = os.getenv("HOME") .. "/.hammerspoon/init.lua"
        hs.task.new("/usr/bin/open", nil, {"-a", "Cursor", configPath}):start()
        print("📝 Opening config in editor...")
        return true -- Event handled
    end

    return false
end

function consoleHotkeys:start()
    self.keyWatcher = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(e) return self:handleKeyEvent(e) end)
    self.keyWatcher:start()
    print("✅ Console hotkeys active.")
end

return consoleHotkeys