
tell application "Music" to pause
tell application "Spotify" to pause
tell application "QuickTime Player" to pause
tell application "Google Chrome"
    repeat with t in tabs of windows
        execute t javascript "document.querySelectorAll('video,audio').forEach(m => {m.pause(); m.muted = true;})"
    end repeat
end tell
