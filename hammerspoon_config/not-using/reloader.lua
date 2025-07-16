-- reloader.lua
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
    if configWatcher then configWatcher:stop() end
    configWatcher = hs.pathwatcher.new(os.getenv("HOME") .. "/.hammerspoon/", function(files) self:reloadConfig(files) end)
    configWatcher:start()
    print("✅ Auto-reloader enabled.")
end

return reloader