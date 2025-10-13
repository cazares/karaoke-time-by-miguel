#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time
"""

import argparse, os, sys, subprocess, shutil
from pathlib import Path
import time

DEFAULT_OUTPUT_DIR = Path("songs")

def run(cmd: str):
    print(f"\n▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=False)

def sanitize_name(name: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def convert_txt_to_csv(txt_path: Path) -> Path:
    """Generate evenly spaced CSV from plain lyrics.txt"""
    csv_path = txt_path.with_suffix(".csv")
    lines = [l.strip() for l in txt_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    spacing = 3.5  # seconds between lines
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("timestamp,text\n")
        for i, line in enumerate(lines, start=1):
            f.write(f"{i * spacing:.2f},{line}\n")
    print(f"✅ Auto-converted {txt_path.name} → {csv_path.name}")
    return csv_path

def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")
    parser.add_argument("input", nargs="?", help="YouTube URL or local MP3 path")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--strip-vocals", action="store_true")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--no-prompt", action="store_true")
    parser.add_argument("--autoplay", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--force-new", action="store_true")
    parser.add_argument("--override-lyric-fetch-txt", dest="override_lyric_fetch_txt")
    parser.add_argument("--mp3")
    args = parser.parse_args()

    artist_dir = sanitize_name(args.artist)
    title_dir = sanitize_name(args.title)
    base_path = DEFAULT_OUTPUT_DIR / f"{artist_dir}__{title_dir}"
    lyrics_dir = base_path / "lyrics"
    os.makedirs(lyrics_dir, exist_ok=True)

    # 🎵 MP3 path
    if args.mp3 and os.path.exists(args.mp3):
        mp3_path = args.mp3
    elif args.input and args.input.startswith("http"):
        mp3_path = f"{args.title}.mp3"
        if not os.path.exists(mp3_path):
            print("\n🎧 Downloading audio…")
            run(f'yt-dlp -x --audio-format mp3 -o "{mp3_path}" "{args.input}"')
        else:
            print(f"✅ Using existing audio file: {mp3_path}")
    elif args.input and os.path.exists(args.input):
        mp3_path = args.input
    else:
        sys.exit("❌ No valid input or --mp3 provided.")

    # 🎤 Lyrics
    final_txt_path = None
    if args.override_lyric_fetch_txt and os.path.exists(args.override_lyric_fetch_txt):
        txt = Path(args.override_lyric_fetch_txt)
        print(f"\n📝 Overriding lyric fetch with: {txt}")
        if txt.suffix.lower() == ".txt":
            final_txt_path = convert_txt_to_csv(txt)
        else:
            final_txt_path = txt
    else:
        sys.exit("❌ No lyrics file provided or found.")

    print(f"✅ Using lyrics file: {final_txt_path}")

    # 🎚️ Strip vocals
    instrumental_path = f"{args.title}_instrumental.mp3"
    if args.strip_vocals:
        if not os.path.exists(instrumental_path):
            print("\n🎙️ Stripping vocals using Demucs…")
            run(f'demucs --two-stems=vocals "{mp3_path}"')
            demucs_dir = Path("separated") / "htdemucs"
            stem_dir = next(demucs_dir.glob("*"), None)
            if stem_dir:
                src = stem_dir / "no_vocals.wav"
                if src.exists():
                    run(f'ffmpeg -y -i "{src}" -vn -ar 44100 -ac 2 -b:a 192k "{instrumental_path}"')
                    print(f"✅ Saved instrumental: {instrumental_path}")
                else:
                    instrumental_path = mp3_path
        else:
            print(f"✅ Using existing instrumental: {instrumental_path}")
    else:
        instrumental_path = mp3_path

    # 🎬 Render
    print(f"\n🎬 Generating karaoke video from {final_txt_path.name}…")
    run(f'python3 karaoke_core.py --csv "{final_txt_path}" --mp3 "{instrumental_path}" --font-size 140')

    # 🎵 Output
    if args.autoplay:
        run(f'open -a "QuickTime Player" "output/{Path(instrumental_path).stem}_karaoke.mp4"')
    else:
        run("open output")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting gracefully.")
        sys.exit(0)

# end of karaoke_generator.py
