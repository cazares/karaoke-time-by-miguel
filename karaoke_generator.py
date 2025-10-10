#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — fully automated Karaoke pipeline 🎤
Author: Miguel Cázares
Version: 2.0
----------------------------------------------------------
Usage Examples:
  python3 karaoke_generator.py ricky_lyrics.txt
  python3 karaoke_generator.py ricky_lyrics.txt --font-size 155 --offset 1.0

Flow:
1️⃣ Captures lyric timings interactively using the original song (lyrics.txt + song.mp3)
2️⃣ Immediately generates karaoke video using the instrumental version (instrumental.mp3)
3️⃣ Auto-detects matching MP3s based on filename patterns
"""

import subprocess, sys, datetime
from pathlib import Path

# --- Helper function ---
def run(cmd):
    print("\n▶️", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)

# --- Detect matching MP3s ---
def find_mp3s(base_name):
    """
    Given a lyrics file like 'ricky_lyrics.txt', look for:
      - original:   'ricky.mp3' or 'ricky_original.mp3'
      - instrumental: 'ricky_instrumental.mp3' or 'ricky-karaoke.mp3'
    """
    parent = Path(base_name).parent
    stem = Path(base_name).stem.replace("_lyrics", "").replace("-lyrics", "")
    all_mp3s = list(parent.glob("*.mp3"))

    orig = None
    inst = None
    for f in all_mp3s:
        lower = f.name.lower()
        if stem in lower and "instrumental" not in lower and "karaoke" not in lower:
            orig = f
        if stem in lower and ("instrumental" in lower or "karaoke" in lower):
            inst = f

    return orig, inst

# --- Main logic ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_generator.py lyrics.txt [original.mp3] [instrumental.mp3] [--font-size 140] [--offset 0.0]")
        sys.exit(1)

    lyrics_txt = Path(sys.argv[1]).resolve()
    opts = sys.argv[2:]

    # auto-detect MP3s if not explicitly given
    mp3_args = [a for a in opts if a.lower().endswith(".mp3")]
    non_mp3_opts = [a for a in opts if not a.lower().endswith(".mp3")]

    if len(mp3_args) == 2:
        original_mp3 = Path(mp3_args[0]).resolve()
        instr_mp3 = Path(mp3_args[1]).resolve()
    else:
        original_mp3, instr_mp3 = find_mp3s(lyrics_txt)
        if not original_mp3:
            sys.exit("❌ Could not find original MP3 (e.g. ricky.mp3).")
        if not instr_mp3:
            sys.exit("❌ Could not find instrumental MP3 (e.g. ricky_instrumental.mp3).")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"lyrics_{timestamp}"
    csv_path = lyrics_txt.with_name(f"{prefix}.csv")
    ass_path = lyrics_txt.with_name(f"{prefix}.ass")

    print("🎤  Phase 1: Capture lyric timings\n")
    run(["python3", "karaoke_time.py", "--lyrics-txt", str(lyrics_txt), "--mp3", str(original_mp3)] + non_mp3_opts)

    print("\n🎬  Phase 2: Generate karaoke video\n")
    run(["python3", "karaoke_time.py", "--csv", str(csv_path), "--ass", str(ass_path), "--mp3", str(instr_mp3)] + non_mp3_opts)

    print(f"\n✅  Done! Output video synced to: {instr_mp3.stem}_karaoke.mp4")

if __name__ == "__main__":
    main()
