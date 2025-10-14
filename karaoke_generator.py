#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time
Now automatically fetches lyrics via fetch_lyrics.py if no --override-lyric-fetch-txt provided.
"""

import argparse, os, sys, subprocess, shutil, shlex
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("songs")

def run(cmd: str):
    print(f"\n▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def sanitize_name(name: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mp3", help="Local MP3 path (optional if using --youtube-url)")
    parser.add_argument("--youtube-url", help="Optional YouTube URL to auto-download audio")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--genius-token", help="Your Genius API token for lyrics fetch")
    parser.add_argument("--override-lyric-fetch-txt", help="Optional: existing lyrics .txt or .csv path")

    args = parser.parse_args()

    # --- Step 0: Handle YouTube URL auto-download ---
    if args.youtube_url:
        print(f"🎧 Detected YouTube URL — downloading audio…\n")
        yt_cmd = f'yt-dlp -x --audio-format mp3 -o "{args.title}.mp3" "{args.youtube_url}"'
        result = subprocess.run(shlex.split(yt_cmd))
        if result.returncode != 0:
            print("❌ Failed to download from YouTube — aborting.")
            sys.exit(1)
        args.mp3 = f"{args.title}.mp3"
        print(f"✅ Download complete → {args.mp3}\n")

    if not args.mp3 or not os.path.exists(args.mp3):
        print("❌ No MP3 file found or provided.")
        sys.exit(1)

    artist_dir = sanitize_name(args.artist)
    title_dir = sanitize_name(args.title)
    base_path = DEFAULT_OUTPUT_DIR / f"{artist_dir}__{title_dir}"
    base_path.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Fetch lyrics if no file provided ---
    if args.override_lyric_fetch_txt and os.path.exists(args.override_lyric_fetch_txt):
        lyrics_path = Path(args.override_lyric_fetch_txt)
        print(f"✅ Using provided lyrics: {lyrics_path}")
    else:
        if not args.genius_token:
            print("❌ No lyrics file or Genius token provided.")
            sys.exit(1)
        lyrics_path = base_path / f"{title_dir}_lyrics.txt"
        print(f"🎵 Fetching lyrics for '{args.title}' by {args.artist}…")
        run(
            f'python3 fetch_lyrics.py '
            f'--title "{args.title}" '
            f'--artist "{args.artist}" '
            f'--output "{lyrics_path}" '
            f'--genius-token "{args.genius_token}"'
        )

    # --- Step 2: Generate karaoke video ---
    print(f"\n🎬 Generating karaoke video with offset {args.offset}…")
    run(
        f'python3 karaoke_core.py '
        f'--csv "{lyrics_path}" '
        f'--mp3 "{args.mp3}" '
        f'--font-size 140 '
        f'--offset {args.offset}'
    )

    print("\n✅ Done!")

if __name__ == "__main__":
    main()

# end of karaoke_generator.py
