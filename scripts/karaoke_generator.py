#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time
Fully verbose, relative-path safe edition (no functional changes, just reliability fixes).
"""

import argparse
import os
import sys
import subprocess
import shlex
import re
from pathlib import Path
from datetime import datetime

DEFAULT_OUTPUT_DIR = Path("songs")

def warn_if_hardcoded_keys(script_path: str):
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        if re.search(r"AIza[0-9A-Za-z\-_]{20,}", content):
            print("⚠️ WARNING: Hardcoded API key detected.")
    except Exception:
        pass

def run(cmd: str, debug: bool = True):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "karaoke_generator.log"

    with open(log_file, "a", encoding="utf-8") as f:
        safe_cmd = re.sub(r'(--genius-token|--youtube-key)\s+"[^"]+"', r'\1 "****"', cmd)
        f.write(f"\n\n▶️ {safe_cmd}\n")
        print(f"\n▶️ {safe_cmd}")
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            sys.stdout.write(line)
            f.write(line)
            f.flush()
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def fetch_youtube_url(api_key: str, artist: str, title: str) -> str:
    try:
        result = subprocess.run(
            [
                "python3",
                "fetch_youtube_url.py",
                "--song",
                title,
                "--artist",
                artist,
                "--youtube-key",
                api_key,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        url_lines = [l for l in lines if l.startswith("http")]
        return url_lines[-1] if url_lines else None
    except Exception as e:
        print(f"[WARN] fetch_youtube_url.py failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mp3")
    parser.add_argument("--youtube-url")
    parser.add_argument("--youtube-api-key")
    parser.add_argument("--genius-token")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--vocals-percent", type=float, default=0.0)
    parser.add_argument("--interactive", action="store_true", help="Enable tap timing mode (default off)")
    parser.add_argument("--final", action="store_true", help="Full high-quality mode (slower)")
    parser.add_argument("--clear-cache", action="store_true", help="Force rerun of Demucs/Whisper cache")
    parser.add_argument("--run-all", action="store_true", help="Run through to MP4 render")
    args = parser.parse_args()

    args.youtube_api_key = args.youtube_api_key or os.getenv("YT_KEY")
    args.genius_token = args.genius_token or os.getenv("GENIUS_TOKEN")

    if not args.youtube_api_key or not args.genius_token:
        print("❌ Missing API keys.")
        sys.exit(1)

    for d in ["songs", "lyrics", "output", "separated", "logs"]:
        Path(d).mkdir(exist_ok=True)

    print("🔎 Fetching YouTube URL automatically…")
    youtube_url = args.youtube_url or fetch_youtube_url(args.youtube_api_key, args.artist, args.title)
    if not youtube_url:
        print("❌ No YouTube URL found and no cached MP3 available. Aborting.")
        sys.exit(1)

    print(f"🎥 Found URL: {youtube_url}")
    mp3_out = Path("songs") / f"{sanitize_name(args.artist)}_{sanitize_name(args.title)}.mp3"

    if not mp3_out.exists():
        run(f'yt-dlp -x --audio-format mp3 -o "{mp3_out}" "{youtube_url}"')
    else:
        print(f"🌀 Cached MP3: {mp3_out}")

    lyrics_path = Path("lyrics") / f"{sanitize_name(args.artist)}_{sanitize_name(args.title)}.txt"
    if not lyrics_path.exists() or args.clear_cache:
        run(
            f'python3 fetch_lyrics.py --title "{args.title}" --artist "{args.artist}" '
            f'--output "{lyrics_path}" --genius-token "{args.genius_token}"'
        )
    else:
        print(f"🌀 Cached lyrics: {lyrics_path}")

    cmd = [
        "python3",
        "-u",
        "karaoke_auto_sync_lyrics.py",
        "--artist",
        f"'{args.artist}'",
        "--title",
        f"'{args.title}'",
    ]
    if args.clear_cache:
        cmd.append("--clear-cache")
    if args.final:
        cmd.append("--final")
    if args.vocals_percent > 0:
        cmd += ["--vocals-percent", str(args.vocals_percent)]

    run(" ".join(cmd))

    csv_path = Path("lyrics") / f"{sanitize_name(args.artist)}_{sanitize_name(args.title)}_synced.csv"
    if args.run_all:
        run(f'python3 karaoke_time.py --csv "{csv_path}" --mp3 "{mp3_out}" --offset {args.offset} --autoplay')

if __name__ == "__main__":
    warn_if_hardcoded_keys(__file__)
    main()

# end of karaoke_generator.py
