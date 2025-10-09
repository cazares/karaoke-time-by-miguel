-- pause_media.applescript (minimal)
-- Pauses Music, Spotify, QuickTime docs, and all <video>/<audio> in Google Chrome tabs.
-- Requirements: Chrome > View menu > Developer > ✔ Allow JavaScript from Apple Events

-- Native players
try
    tell application "Music" to pause
end try

try
    tell application "Spotify" to pause
end try

try
    tell application "QuickTime Player"
        repeat with d in documents
            try
                pause d
            end try
        end repeat
    end tell
end try

-- Chrome tabs
try
    tell application "Google Chrome"
        repeat with w in windows
            repeat with t in tabs of w
                tell t to execute javascript ¬
                    "document.querySelectorAll('video,audio').forEach(el=>{try{el.pause(); el.muted=true;}catch(e){}});"
            end repeat
        end repeat
    end tell
end try
