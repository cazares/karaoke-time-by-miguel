#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — end-to-end karaoke pipeline
Fetches lyrics → optional vocal removal → launches karaoke_core.
Fully supports --no-prompt for unattended runs.
"""

import subprocess, sys, os
from pathlib import Path
from glob import glob
from karaoke_time import handle_auto_lyrics

def run(cmd):
    print("\n▶️", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_generator.py <song.mp3|YouTube URL> "
              "[--strip-vocals] [--artist 'Name'] [--title 'Song'] "
              "[--lyrics-txt path] [--offset seconds] [--no-prompt]")
        sys.exit(1)

    no_prompt = "--no-prompt" in sys.argv
    strip_vocals = "--strip-vocals" in sys.argv

    mp3_arg = sys.argv[1]
    artist = None
    title = None
    offset = None

    if "--artist" in sys.argv:
        artist = sys.argv[sys.argv.index("--artist") + 1]
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    if "--offset" in sys.argv:
        offset = sys.argv[sys.argv.index("--offset") + 1]

    # === Phase 0: Download YouTube audio if URL provided ===
    mp3_path = Path(mp3_arg)
    if mp3_arg.startswith("http"):
        print(f"🎧 Detected YouTube URL — downloading audio...")
        mp3_out = f"{title or 'karaoke_track'}.mp3"
        run(["yt-dlp", "-x", "--audio-format", "mp3", "-o", mp3_out, mp3_arg])
        mp3_path = Path(mp3_out)
    else:
        if not mp3_path.exists():
            sys.exit(f"❌ MP3 not found: {mp3_path}")

    # === Phase 1: Fetch or use lyrics ===
    if "--lyrics-txt" in sys.argv:
        lyrics_txt_path = sys.argv[sys.argv.index("--lyrics-txt") + 1]
        lyrics_dir = os.path.dirname(os.path.abspath(lyrics_txt_path))
        output_dir = os.path.join(os.path.dirname(lyrics_dir), "output")
        paths = {"lyrics": lyrics_dir, "output": output_dir}
        print(f"✅ Using existing lyrics file: {lyrics_txt_path}")
    else:
        lyrics_text, paths = handle_auto_lyrics(str(mp3_path), artist, title)

        candidates = glob(os.path.join(paths["lyrics"], "FINAL_*.txt"))
        if not candidates:
            sys.exit("❌ Could not locate FINAL_ lyrics file.")
        candidates.sort(key=os.path.getmtime, reverse=True)
        lyrics_txt_path = candidates[0]
        print(f"✅ Using lyrics file: {lyrics_txt_path}")

        output_dir = os.path.join(os.path.dirname(paths["lyrics"]), "output")
        os.makedirs(output_dir, exist_ok=True)
        paths["output"] = output_dir

    # === Phase 2: Strip vocals if requested ===
    if strip_vocals:
        instr_mp3 = mp3_path.with_name(f"{mp3_path.stem}_instrumental.mp3")
        if instr_mp3.exists():
            print(f"✅ Instrumental already exists: {instr_mp3}")
        else:
            cmd = ["python3", "karaoke_maker.py", str(mp3_path)]
            if no_prompt: cmd.append("--no-prompt")
            run(cmd)
            if not instr_mp3.exists():
                sys.exit(f"❌ Expected instrumental file not found: {instr_mp3}")
    else:
        instr_mp3 = mp3_path

    # === Phase 3: Generate karaoke video ===
    print(f"\n🎬 Generating karaoke video using: {lyrics_txt_path}\n")
    cmd = [
        "python3", "karaoke_core.py",
        "--lyrics-txt", lyrics_txt_path,
        "--mp3", str(instr_mp3),
    ]
    if artist: cmd += ["--artist", artist]
    if title: cmd += ["--title", title]
    if offset: cmd += ["--offset", str(offset)]
    if no_prompt: cmd.append("--no-prompt")
    cmd.append("--autoplay")

    run(cmd)
    print(f"\n✅ Done! Output in: {os.path.abspath(paths['output'])}\n")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {e}")
        sys.exit(1)
