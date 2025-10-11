#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — end-to-end karaoke pipeline
Fetches lyrics → optional vocal removal → launches karaoke_core.
"""

import subprocess, sys, os
from pathlib import Path
from karaoke_time import handle_auto_lyrics
from glob import glob

def run(cmd):
    print("\n▶️", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_generator.py <song.mp3> [--strip-vocals] [--artist 'Name'] [--title 'Song'] [--lyrics-txt path]")
        sys.exit(1)

    mp3 = Path(sys.argv[1]).resolve()
    if not mp3.exists():
        sys.exit("❌ MP3 not found.")

    strip_vocals = "--strip-vocals" in sys.argv
    artist = None
    title = None
    if "--artist" in sys.argv:
        artist = sys.argv[sys.argv.index("--artist") + 1]
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]

    # === Phase 1: Fetch or use lyrics ===
    if "--lyrics-txt" in sys.argv:
        lyrics_txt_path = sys.argv[sys.argv.index("--lyrics-txt") + 1]
        lyrics_dir = os.path.dirname(os.path.abspath(lyrics_txt_path))
        output_dir = os.path.join(os.path.dirname(lyrics_dir), "output")
        paths = {"lyrics": lyrics_dir, "output": output_dir}
        print(f"✅ Using existing lyrics file: {lyrics_txt_path}")
    else:
        lyrics_text, paths = handle_auto_lyrics(str(mp3), artist, title)

        # 🔧 FIXED: auto-detect correct FINAL_ file
        candidates = glob(os.path.join(paths["lyrics"], "FINAL_*.txt"))
        if not candidates:
            sys.exit("❌ Could not locate FINAL_ lyrics file in " + paths["lyrics"])
        elif len(candidates) > 1:
            print(f"⚠️ Multiple FINAL_*.txt files found, using the newest one.")
            candidates.sort(key=os.path.getmtime, reverse=True)
        lyrics_txt_path = candidates[0]
        print(f"✅ Using lyrics file: {lyrics_txt_path}")

        # 🧱 Ensure output dir always defined
        output_dir = os.path.join(os.path.dirname(paths["lyrics"]), "output")
        os.makedirs(output_dir, exist_ok=True)
        paths["output"] = output_dir

    # === Phase 2: Strip vocals if requested ===
    if strip_vocals:
        instr_mp3 = mp3.with_name(f"{mp3.stem}_instrumental.mp3")
        if instr_mp3.exists():
            print(f"✅ Instrumental already exists: {instr_mp3}")
        else:
            run(["python3", "karaoke_maker.py", str(mp3)])
            if not instr_mp3.exists():
                sys.exit(f"❌ Expected instrumental file not found: {instr_mp3}")
    else:
        instr_mp3 = mp3

    # === Phase 3: Generate karaoke video ===
    print(f"\n🎬 Generating karaoke video using: {lyrics_txt_path}\n")
    run([
        "python3", "karaoke_core.py",
        "--lyrics-txt", lyrics_txt_path,
        "--mp3", str(instr_mp3),
        "--autoplay"
    ])

    print(f"\n✅ Done! Output in: {os.path.abspath(paths['output'])}\n")

if __name__ == "__main__":
    main()
