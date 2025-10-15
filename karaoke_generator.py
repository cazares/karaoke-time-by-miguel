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

def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")

    parser.add_argument("input", nargs="?", help="YouTube URL or local MP3 path")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--title", required=True, help="Song title")
    parser.add_argument("--strip-vocals", action="store_true", help="Strip vocals using Demucs")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--no-prompt", action="store_true")
    parser.add_argument("--autoplay", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--force-new", action="store_true")
    parser.add_argument("--test-lyric-fetching", action="store_true")
    parser.add_argument("--override-lyric-fetch-txt")
    parser.add_argument("--mp3")

    args = parser.parse_args()

    artist_dir = sanitize_name(args.artist)
    title_dir = sanitize_name(args.title)
    base_path = DEFAULT_OUTPUT_DIR / f"{artist_dir}__{title_dir}"
    lyrics_dir = base_path / "lyrics"
    os.makedirs(lyrics_dir, exist_ok=True)

    # 🧪 Test lyric fetching mode (no-op here; kept for compatibility)
    if args.test_lyric_fetching:
        print("\n🧪 --test-lyric-fetching is not wired in this minimal entrypoint.")
        sys.exit(0)

    # 🧹 Reset lyrics/timing only (if forced)
    if args.force_new:
        print("\n🧹 --force-new enabled: clearing lyrics/timing only…")
        shutil.rmtree(lyrics_dir, ignore_errors=True)
        print(f"🗑️ Removed: {lyrics_dir}")
        print("✅ Preserved original and instrumental MP3 files.\n")

    # 🎵 Determine MP3 path
    mp3_path = None
    if args.mp3 and os.path.exists(args.mp3):
        mp3_path = args.mp3
    elif args.input and args.input.startswith("http"):
        mp3_path = f"{args.title}.mp3"
        if not os.path.exists(mp3_path):
            print("\n🎧 Detected YouTube URL — downloading audio…")
            run(f'yt-dlp -x --audio-format mp3 -o "{mp3_path}" "{args.input}"')
        else:
            print(f"✅ Using existing audio file: {mp3_path}")
    elif args.input and os.path.exists(args.input):
        mp3_path = args.input
    else:
        print("❌ No valid input or --mp3 provided.")
        sys.exit(1)

    # 🎤 Lyrics: require override path (CSV or TXT)
    if not args.override_lyric_fetch_tct and not args.override_lyric_fetch_txt:
        pass  # placeholder to avoid NameError
    # NOTE: argparse stores it as override_lyric_fetch_txt
    if args.override_lyric_fetch_txt and os.path.exists(args.override_lyric_fetch_txt):
        final_txt_path = Path(args.override_lyric_fetch_txt)
        print(f"✅ Using lyrics file: {final_txt_path}")
    else:
        print("❌ No lyrics file provided or found.")
        sys.exit(1)

    # 🎚️ Instrumental handling (optional)
    instrumental_path = mp3_path
    if args.strip_vocals:
        candidate = f"{Path(args.title).stem}_instrumental.mp3"
        if os.path.exists(candidate):
            print(f"✅ Using existing instrumental: {candidate}")
            instrumental_path = candidate
        else:
            print("\n🎙️ Stripping vocals using Demucs...")
            run(f'demucs --two-stems=vocals "{mp3_path}"')
            demucs_dir = Path("separated") / "htdemucs"
            stem_dir = next(demucs_dir.glob("*"), None)
            if stem_dir:
                no_vocals = stem_dir / "no_vocals.wav"
                if no_vocals.exists():
                    candidate = f"{Path(args.title).stem}_instrumental.mp3"
                    run(f'ffmpeg -y -i "{no_vocals}" -vn -ar 44100 -ac 2 -b:a 192k "{candidate}"')
                    instrumental_path = candidate
                    print(f"✅ Saved instrumental: {instrumental_path}")
                else:
                    print("⚠️ Demucs output missing — using original audio.")
            else:
                print("⚠️ Demucs directory missing — using original audio.")

    # 🎬 Render (now passes --offset through to karaoke_core.py)
    print(f"\n🎬 Generating karaoke video from {final_txt_path.name}…")
    run(
        f'python3 karaoke_core.py '
        f'--csv "{final_txt_path}" '
        f'--mp3 "{instrumental_path}" '
        f'--font-size 140 '
        f'--offset {args.offset}'
    )

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
