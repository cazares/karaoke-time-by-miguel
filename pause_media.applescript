-- pause_media.applescript
-- Chrome must have: View > Developer > Allow JavaScript from Apple Events

-- Music / iTunes
try
    tell application "Music" to if it is running then pause
end try
try
    tell application "iTunes" to if it is running then pause
end try

-- Spotify
try
    tell application "Spotify" to if it is running then pause
end try

-- QuickTime Player
try
    tell application "QuickTime Player" to if it is running then pause (every document)
end try

-- Google Chrome: pause all <video>/<audio> elements in all tabs
try
    tell application "Google Chrome"
        if it is running then
            repeat with w in windows
                repeat with t in tabs of w
                    tell t to execute javascript ¬
"document.querySelectorAll('video,audio').forEach(el=>{try{el.pause(); el.muted=true;}catch(e){}});"
                end repeat
            end repeat
        end if
    end tell
end try

