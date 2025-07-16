-- modules/reloader.lua
-- Automatically reloads Hammerspoon config on file changes.

local reloader = {}
local configWatcher

function reloader:reloadConfig(files)
    for _, file in ipairs(files) do
        if file:sub(-4) == ".lua" then
            print("🔄 Config file changed, reloading...")
            hs.reload()
            return -- Reload only once
        end
    end
end

function reloader:start()
    -- Making the watcher a key in the module's table prevents it from being garbage collected
    self.configWatcher = hs.pathwatcher.new(os.getenv("HOME") .. "/.hammerspoon/", function(f) self:reloadConfig(f) end)
    self.configWatcher:start()
    print("✅ Auto-reloader enabled.")
end

return reloader
