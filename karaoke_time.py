#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — lyric management and orchestration layer
Bridges between karaoke_generator.py and karaoke_lyric_fetcher.py.
Keeps backward compatibility with --debug, --test-lyric-fetching, and
--override-lyric-fetch-txt. Always provides a ready-to-use lyrics file.
"""

import os, sys, time
from pathlib import Path
from karaoke_lyric_fetcher import handle_auto_lyrics

DEBUG = "--debug" in sys.argv
FORCE_REFETCH = "--test-lyric-fetching" in sys.argv
OVERRIDE_TXT = None

for i, arg in enumerate(sys.argv):
    if arg == "--override-lyric-fetch-txt" and i + 1 < len(sys.argv):
        OVERRIDE_TXT = Path(sys.argv[i + 1]).expanduser()

DEBUG_LOG = None
if DEBUG:
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    DEBUG_LOG = f"lyrics_debug_{ts}.log"
    print(f"🧾 Debug log file: {DEBUG_LOG}")

def debug_write(label, content):
    if DEBUG:
        try:
            with open(DEBUG_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n[{time.strftime('%H:%M:%S')}] {label}\n{content}\n")
        except Exception:
            pass

def main(mp3_path=None, artist=None, title=None):
    """Handles lyric retrieval or override logic."""
    if OVERRIDE_TXT and OVERRIDE_TXT.exists():
        print(f"🎯 Using override lyric file: {OVERRIDE_TXT}")
        lyrics_text = OVERRIDE_TXT.read_text(encoding="utf-8")
        return lyrics_text, {"lyrics": str(OVERRIDE_TXT.parent)}

    print(f"\n🎵 Fetching lyrics for: {artist} — {title}")
    lyrics_text, info = handle_auto_lyrics(
        mp3_path=mp3_path,
        artist=artist,
        title=title,
        force_refetch=FORCE_REFETCH,
        debug_log=DEBUG_LOG,
    )

    if not lyrics_text.strip():
        sys.exit("❌ No lyrics fetched or provided.")

    debug_write("Final Lyrics Text", lyrics_text[:1000])
    print(f"✅ Ready lyrics file located in: {info['lyrics']}")
    return lyrics_text, info

if __name__ == "__main__":
    print("⚙️  karaoke_time.py is a helper; use karaoke_generator.py instead.")