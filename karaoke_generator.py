#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time
Coordinates lyric fetching, vocal stripping, tap timing, and video rendering.

Features:
  • --strip-vocals: isolate instrumental track using Demucs
  • --test-lyric-fetching: fetch lyrics only (no downloads or separation)
  • --override-lyric-fetch-txt: use an existing lyrics .txt instead of scraping
  • --no-prompt: skip confirmations (auto “n” on timing reuse)
  • --debug: enables diagnostic logging across all modules
  • --autoplay: open finished video in QuickTime/Preview on macOS
"""

import argparse, os, sys, subprocess, shutil
from pathlib import Path
from karaoke_lyric_fetcher import handle_auto_lyrics
import time

DEFAULT_OUTPUT_DIR = Path("songs")

def run(cmd: str):
    """Run a shell command with visible logging."""
    print(f"\n▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=False)

def run_tap_mode(lyrics_txt_path, mp3_path, offset=0.0, debug=False):
    """Run interactive tap mode via karaoke_time.py."""
    print("\n🎹 Entering tap-timing mode (press ENTER in rhythm with lyrics)...")
    cmd = (
        f'python3 karaoke_time.py '
        f'--lyrics-txt "{lyrics_txt_path}" '
        f'--mp3 "{mp3_path}" '
        f'--offset {offset} '
    )
    if debug:
        cmd += "--debug "
    run(cmd)

def sanitize_name(name: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")

    parser.add_argument("input", nargs="?", help="YouTube URL or local MP3 path")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--title", required=True, help="Song title")
    parser.add_argument("--strip-vocals", action="store_true", help="Strip vocals using Demucs")
    parser.add_argument("--offset", type=float, default=0.0, help="Global timing offset (seconds)")
    parser.add_argument("--no-prompt", action="store_true", help="Skip all interactive prompts")
    parser.add_argument("--autoplay", action="store_true", help="Auto-play final video when done")
    parser.add_argument("--debug", action="store_true", help="Enable detailed debug logging")
    parser.add_argument("--force-new", action="store_true", help="Clear lyrics/timing files before run (keep audio)")
    parser.add_argument("--test-lyric-fetching", action="store_true",
                        help="Fetch lyrics only (no downloads, separation, or video generation).")
    parser.add_argument("--override-lyric-fetch-txt", help="Use existing lyrics .txt instead of fetching")
    parser.add_argument("--mp3", required=False, help="Path to the MP3 file to use for karaoke generation")

    args = parser.parse_args()

    artist_dir = sanitize_name(args.artist)
    title_dir = sanitize_name(args.title)
    base_path = DEFAULT_OUTPUT_DIR / f"{artist_dir}__{title_dir}"
    lyrics_dir = base_path / "lyrics"
    os.makedirs(lyrics_dir, exist_ok=True)

    # 🧪 Test lyric fetching mode
    if args.test_lyric_fetching:
        print("\n🧪 --test-lyric-fetching mode active — skipping downloads and Demucs.")
        lyrics_text = handle_auto_lyrics(args.artist, args.title, debug=args.debug)
        print("\n========== LYRICS FETCHED ==========\n")
        print(lyrics_text.strip())
        print("\n====================================\n")
        sys.exit(0)

    # 🧹 Reset lyrics/timing only (if forced)
    if args.force_new:
        print("\n🧹 --force-new enabled: clearing lyrics/timing only…")
        shutil.rmtree(lyrics_dir, ignore_errors=True)
        print(f"🗑️ Removed: {lyrics_dir}")
        print("✅ Preserved original and instrumental MP3 files.\n")

    # 🎵 Determine MP3 path
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

    # 🎤 Fetch lyrics (or override)
    if args.override_lyric_fetch_txt and os.path.exists(args.override_lyric_fetch_txt):
        print(f"\n📝 Overriding lyric fetch with: {args.override_lyric_fetch_txt}")
        lyrics_txt_path = Path(args.override_lyric_fetch_txt)

        # 🔹 If it's a .txt file, enter tap mode
        if lyrics_txt_path.suffix.lower() == ".txt":
            run_tap_mode(lyrics_txt_path, args.mp3 or mp3_path, offset=args.offset, debug=args.debug)
            csv_path = lyrics_txt_path.with_suffix(".csv")
            if csv_path.exists():
                final_txt_path = csv_path
                print(f"✅ Tap mode complete — generated CSV: {csv_path}")
            else:
                print("❌ CSV generation failed — aborting.")
                sys.exit(1)
        else:
            lyrics_text = lyrics_txt_path.read_text(encoding="utf-8")
            final_txt_path = lyrics_txt_path


    print(f"✅ Using lyrics file: {final_txt_path}")

    # 🎚️ Strip vocals if requested
    instrumental_path = f"{args.title}_instrumental.mp3"
    if args.strip_vocals:
        if os.path.exists(instrumental_path):
            print(f"✅ Instrumental already exists: {instrumental_path}")
        else:
            print("\n🎙️ Stripping vocals using Demucs...")
            run(f'demucs --two-stems=vocals "{mp3_path}"')
            demucs_dir = Path("separated") / "htdemucs"
            stem_dir = next(demucs_dir.glob("*"), None)
            if stem_dir:
                src = stem_dir / "no_vocals.wav"
                if src.exists():
                    run(f'ffmpeg -y -i "{src}" -vn -ar 44100 -ac 2 -b:a 192k "{instrumental_path}"')
                    print(f"✅ Saved instrumental: {instrumental_path}")
                else:
                    print("⚠️ Demucs output missing — using original audio.")
                    instrumental_path = mp3_path
    else:
        if os.path.exists(instrumental_path):
            print(f"✅ Using existing instrumental: {instrumental_path}")
        else:
            instrumental_path = mp3_path

    # 🎬 Generate karaoke video
    print("\n🎬 Generating karaoke video using:", final_txt_path)
    core_cmd = (
        f'python3 karaoke_core.py '
        f'--csv "{final_txt_path}" '
        f'--mp3 "{instrumental_path}" '
    )
    run(core_cmd)

    if args.autoplay:
        print("\n🎵 Autoplay enabled — opening in QuickTime…")
        run(f'open -a "QuickTime Player" "output/{Path(instrumental_path).stem}_karaoke.mp4"')
    else:
        print("\n📂 Opening Finder where the MP4 lives…")
        run('open output')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting gracefully.")
        sys.exit(0)

# end of karaoke_generator.py
