-- modules/window_management.lua
-- Advanced window management with multi-monitor support and keyboard shortcuts.

local windowManager = {}

-- Cache monitor configuration (only update when screens change)
local monitorCache = {
    left = nil,
    center = nil, 
    right = nil,
    lastUpdate = 0
}

-- Constants for performance
local MONITOR_NAMES = {
    center = "LS27A600U",
    left = "HP E24u G4", 
    right = "S24C31x"
}

local POSITION_TOLERANCE = 30  -- Increased tolerance
local HEIGHT_TOLERANCE = 60    -- Increased tolerance

-- Pre-calculated layout units for performance
local LAYOUTS = {
    left50 = {x=0, y=0, w=0.5, h=1},
    right50 = {x=0.5, y=0, w=0.5, h=1},
    topLeft = {x=0, y=0, w=0.5, h=0.5},
    topRight = {x=0.5, y=0, w=0.5, h=0.5},
    bottomLeft = {x=0, y=0.5, w=0.5, h=0.5},
    bottomRight = {x=0.5, y=0.5, w=0.5, h=0.5},
    topHalf = {x=0, y=0, w=1, h=0.5},
    bottomHalf = {x=0, y=0.5, w=1, h=0.5}
}

-- Local variables
local keyWatcher = nil
local screenWatcher = nil

-- FIXED: Cached screen detection with proper timeout
local function refreshMonitorCache()
    local currentTime = hs.timer.secondsSinceEpoch()
    
    -- FIXED: Changed back to 1 second (was 10000!)
    if currentTime - monitorCache.lastUpdate < 1 then
        return
    end
    
    local screens = hs.screen.allScreens()
    monitorCache.left = nil
    monitorCache.center = nil
    monitorCache.right = nil
    
    for _, screen in ipairs(screens) do
        local name = screen:name()
        if name == MONITOR_NAMES.left then
            monitorCache.left = screen
        elseif name == MONITOR_NAMES.center then
            monitorCache.center = screen
        elseif name == MONITOR_NAMES.right then
            monitorCache.right = screen
        end
    end
    
    monitorCache.lastUpdate = currentTime
    
    -- Debug: Log what we found
  --  print("🔄 Monitor cache refreshed:")
  --  print("   Left: " .. (monitorCache.left and "✅" or "❌"))
  --  print("   Center: " .. (monitorCache.center and "✅" or "❌"))  
  --  print("   Right: " .. (monitorCache.right and "✅" or "❌"))
end

-- Fast screen position detection
local function getCurrentScreenPosition(screen)
    if not screen then return nil end
    local name = screen:name()
    
    if name == MONITOR_NAMES.left then
        return "left"
    elseif name == MONITOR_NAMES.center then
        return "center"
    elseif name == MONITOR_NAMES.right then
        return "right"
    end
    return nil
end

-- IMPROVED: Window state detection with better error handling
local function getWindowState(window)
    if not window then 
        print("❌ No focused window")
        return nil 
    end
    
    local windowFrame = window:frame()
    local screen = window:screen()
    if not screen then 
        print("❌ Window has no screen")
        return nil 
    end
    
    local screenFrame = screen:frame()
    
    -- Pre-calculate commonly used values
    local screenWidth = screenFrame.w
    local screenHeight = screenFrame.h
    local screenX = screenFrame.x
    local halfWidth = screenWidth * 0.5
    
    local state = {
        isVertical = screen:name() == MONITOR_NAMES.left,
        isMaximized = math.abs(windowFrame.w - screenWidth) < POSITION_TOLERANCE and 
                     math.abs(windowFrame.h - screenHeight) < HEIGHT_TOLERANCE,
        isLeftHalf = math.abs(windowFrame.x - screenX) < POSITION_TOLERANCE and 
                    math.abs(windowFrame.w - halfWidth) < POSITION_TOLERANCE,
        isRightHalf = math.abs(windowFrame.x - (screenX + halfWidth)) < POSITION_TOLERANCE and 
                     math.abs(windowFrame.w - halfWidth) < POSITION_TOLERANCE,
        screen = screen,
        position = getCurrentScreenPosition(screen)
    }
    
    -- Debug current state
    print("📍 Window state: " .. (state.position or "unknown") .. 
          " | Vertical: " .. tostring(state.isVertical) ..
          " | MaxSize: " .. tostring(state.isMaximized) ..
          " | LeftHalf: " .. tostring(state.isLeftHalf) ..
          " | RightHalf: " .. tostring(state.isRightHalf))
    
    return state
end

-- IMPROVED: Safe window movement functions
local function moveToLayout(window, layout, description)
    if window and layout then
        print("📐 " .. (description or "Moving window"))
        window:moveToUnit(layout)
    else
        print("❌ Failed to move window: " .. (description or "unknown"))
    end
end

local function moveToScreen(window, targetScreen, layout, description)
    if not window then
        print("❌ No window to move")
        return
    end
    
    if not targetScreen then
        print("❌ No target screen available")
        return
    end
    
    print("🖥️  " .. (description or "Moving to screen"))
    window:moveToScreen(targetScreen)
    
    if layout then
        -- Small delay to ensure screen move completes
        hs.timer.doAfter(0.05, function()
            moveToLayout(window, layout, "Applying layout after screen move")
        end)
    end
end

-- FIXED: Movement handlers with better logic
local function handleLeftArrow()
    local window = hs.window.focusedWindow()
    if not window then 
        print("❌ No focused window")
        return false 
    end
    
    refreshMonitorCache()
    local state = getWindowState(window)
    if not state then return false end
    
    print("⬅️  Handling left arrow")
    
    if state.isVertical then
        if state.isMaximized and monitorCache.center then
            moveToScreen(window, monitorCache.center, LAYOUTS.right50, "Moving from vertical to center (right half)")
        else
            print("📐 Maximizing on vertical screen")
            window:maximize()
        end
    else
        if state.isLeftHalf then
            -- Move to left screen
            if state.position == "center" and monitorCache.left then
                moveToScreen(window, monitorCache.left, nil, "Moving from center to left (maximize)")
                hs.timer.doAfter(0.1, function()
                    window:maximize()
                end)
            elseif state.position == "right" and monitorCache.center then
                moveToScreen(window, monitorCache.center, LAYOUTS.right50, "Moving from right to center (right half)")
            else
                print("📍 No screen to move to on the left")
            end
        else
            moveToLayout(window, LAYOUTS.left50, "Snapping to left half")
        end
    end
    
    return true
end

local function handleRightArrow()
    local window = hs.window.focusedWindow()
    if not window then 
        print("❌ No focused window")
        return false 
    end
    
    refreshMonitorCache()
    local state = getWindowState(window)
    if not state then return false end
    
    print("➡️  Handling right arrow")
    
    if state.isVertical then
        if state.isMaximized and monitorCache.center then
            moveToScreen(window, monitorCache.center, LAYOUTS.left50, "Moving from vertical to center (left half)")
        else
            print("📐 Maximizing on vertical screen")
            window:maximize()
        end
    else
        if state.isRightHalf then
            -- Move to right screen
            if state.position == "left" and monitorCache.center then
                moveToScreen(window, monitorCache.center, LAYOUTS.left50, "Moving from left to center (left half)")
            elseif state.position == "center" and monitorCache.right then
                moveToScreen(window, monitorCache.right, LAYOUTS.left50, "Moving from center to right (left half)")
            else
                print("📍 No screen to move to on the right")
            end
        else
            moveToLayout(window, LAYOUTS.right50, "Snapping to right half")
        end
    end
    
    return true
end

local function handleUpArrow()
    local window = hs.window.focusedWindow()
    if not window then return false end
    
    local state = getWindowState(window)
    if not state then return false end
    
    print("⬆️  Handling up arrow")
    
    if state.isVertical then
        moveToLayout(window, LAYOUTS.topHalf, "Top half on vertical screen")
    else
        if state.isLeftHalf then
            moveToLayout(window, LAYOUTS.topLeft, "Top-left quarter")
        elseif state.isRightHalf then
            moveToLayout(window, LAYOUTS.topRight, "Top-right quarter")
        else
            print("📐 Maximizing window")
            window:maximize()
        end
    end
    
    return true
end

local function handleDownArrow()
    local window = hs.window.focusedWindow()
    if not window then return false end
    
    local state = getWindowState(window)
    if not state then return false end
    
    print("⬇️  Handling down arrow")
    
    if state.isVertical then
        moveToLayout(window, LAYOUTS.bottomHalf, "Bottom half on vertical screen")
    else
        if state.isLeftHalf then
            moveToLayout(window, LAYOUTS.bottomLeft, "Bottom-left quarter")
        elseif state.isRightHalf then
            moveToLayout(window, LAYOUTS.bottomRight, "Bottom-right quarter")
        else
            print("🔽 Minimizing window")
            window:minimize()
        end
    end
    
    return true
end

-- Key watcher
local function createKeyWatcher()
    keyWatcher = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(event)
        local modifiers = event:getFlags()
        
        -- Fast modifier check
        if not (modifiers.shift and modifiers.ctrl) then
            return false
        end
        
        local keyCode = event:getKeyCode()
        
        -- Direct keycode comparison
        if keyCode == 123 then      -- left arrow
            return handleLeftArrow()
        elseif keyCode == 124 then  -- right arrow  
            return handleRightArrow()
        elseif keyCode == 126 then  -- up arrow
            return handleUpArrow()
        elseif keyCode == 125 then  -- down arrow
            return handleDownArrow()
        end
        
        return false
    end)
end

-- Public functions
function windowManager:checkStatus()
    refreshMonitorCache()
    print("=== Window Management Status ===")
    print("Key watcher: " .. (keyWatcher and keyWatcher:isEnabled() and "✅ Active" or "❌ Inactive"))
    print("Current focused window: " .. (hs.window.focusedWindow() and "✅ Available" or "❌ None"))
    if hs.window.focusedWindow() then
        getWindowState(hs.window.focusedWindow())
    end
end

function windowManager:restart()
    if keyWatcher then keyWatcher:stop() end
    createKeyWatcher()
    keyWatcher:start()
    monitorCache.lastUpdate = 0
    refreshMonitorCache()
    print("🔄 Window management restarted")
end

function windowManager:start()
    -- Initialize window management
    refreshMonitorCache()
    createKeyWatcher()
    keyWatcher:start()
    
    -- Screen watcher to automatically refresh monitor cache
    screenWatcher = hs.screen.watcher.new(function()
        print("🖥️  Display configuration changed, refreshing monitors...")
        monitorCache.lastUpdate = 0  -- Force refresh
        refreshMonitorCache()
    end)
    screenWatcher:start()
    
    print("⚡ Window management active")
end

function windowManager:stop()
    if keyWatcher then keyWatcher:stop() end
    if screenWatcher then screenWatcher:stop() end
    print("🛑 Window management stopped")
end

return windowManager
