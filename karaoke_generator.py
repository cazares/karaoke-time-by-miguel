#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — end-to-end karaoke pipeline
Fetches lyrics → optional vocal removal → launches karaoke_core.
Supports YouTube URLs automatically.
"""

import subprocess, sys, os, glob
from pathlib import Path
from karaoke_time import handle_auto_lyrics

def run(cmd):
    print("\n▶️", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_generator.py <song.mp3 | YouTube_URL> [--strip-vocals] [--artist 'Name'] [--title 'Song'] [--offset 1.5]")
        sys.exit(1)

    # === Phase 0: Allow YouTube URL ===
    if sys.argv[1].startswith("http"):
        url = sys.argv[1]
        print(f"🎧 Downloading audio from YouTube: {url}")
        run([
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "--output", "%(title)s.%(ext)s",
            url
        ])
        mp3_files = glob.glob("*.mp3")
        if not mp3_files:
            sys.exit("❌ No MP3 produced by yt-dlp.")
        mp3_files.sort(key=os.path.getmtime, reverse=True)
        sys.argv[1] = mp3_files[0]
        print(f"✅ Using downloaded MP3: {sys.argv[1]}")

    mp3 = Path(sys.argv[1]).resolve()
    if not mp3.exists():
        sys.exit("❌ MP3 not found.")

    strip_vocals = "--strip-vocals" in sys.argv
    artist = None
    title = None
    offset_val = 0.0
    if "--artist" in sys.argv:
        artist = sys.argv[sys.argv.index("--artist") + 1]
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    if "--offset" in sys.argv:
        offset_val = float(sys.argv[sys.argv.index("--offset") + 1])

    # === Phase 1: Fetch or use lyrics ===
    if "--lyrics-txt" in sys.argv:
        lyrics_txt_path = sys.argv[sys.argv.index("--lyrics-txt") + 1]
        lyrics_dir = os.path.dirname(os.path.abspath(lyrics_txt_path))
        output_dir = os.path.join(os.path.dirname(lyrics_dir), "output")
        paths = {"lyrics": lyrics_dir, "output": output_dir}
        print(f"✅ Using existing lyrics file: {lyrics_txt_path}")
    else:
        lyrics_text, paths = handle_auto_lyrics(str(mp3), artist, title)
        candidates = glob.glob(os.path.join(paths["lyrics"], "FINAL_*.txt"))
        if not candidates:
            sys.exit("❌ Could not locate FINAL_ lyrics file in " + paths["lyrics"])
        candidates.sort(key=os.path.getmtime, reverse=True)
        lyrics_txt_path = candidates[0]
        print(f"✅ Using lyrics file: {lyrics_txt_path}")
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
        "--artist", artist or "",
        "--title", title or "",
        "--offset", str(offset_val),
        "--autoplay"
    ])

    print(f"\n✅ Done! Output in: {os.path.abspath(paths['output'])}\n")

if __name__ == "__main__":
    main()
