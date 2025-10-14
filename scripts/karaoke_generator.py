#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time

Default behavior:
  • Auto-fetches YouTube audio (via fetch_youtube_url.py) if no URL given
  • Auto-fetches lyrics (via fetch_lyrics.py) if no text provided
  • Auto-syncs lyrics & audio into CSV (via karaoke_auto_sync_lyrics.py)
  • Defaults to interactive tap mode for manual lyric timing override
Disable tapping with --no-tap to skip straight to .csv → .ass → .mp4.
Also includes runtime safeguard against hardcoded API keys or tokens.
"""

import argparse, os, sys, subprocess, shlex, re
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("songs")

# --- Security safeguard -----------------------------------------------------
def warn_if_hardcoded_keys(script_path: str):
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        patterns = [
            r"AIza[0-9A-Za-z\-_]{20,}",
            r"(?i)genius[_-]?token\s*=\s*['\"]\w+",
            r"Bearer\s+[A-Za-z0-9\-_]{20,}",
            r"sk-[A-Za-z0-9]{20,}"
        ]
        for pattern in patterns:
            if re.search(pattern, content):
                print(f"⚠️  WARNING: Hardcoded API key detected in {script_path}\n"
                      "→ Move keys to environment variables or command-line args.\n")
                break
    except Exception as e:
        print(f"[WARN] Could not scan for hardcoded keys: {e}")

# --- Helpers ----------------------------------------------------------------
def run(cmd: str):
    print(f"\n▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def fetch_youtube_url(api_key: str, artist: str, title: str) -> str:
    try:
        result = subprocess.run(
            [
                "python3", "fetch_youtube_url.py",
                "--song", title,
                "--artist", artist,
                "--youtube-key", api_key
            ],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()
        if url.startswith("http"):
            print(f"🎥 Auto-fetched YouTube URL: {url}")
            return url
        print(f"[WARN] fetch_youtube_url.py returned unexpected output: {url}")
        return None
    except Exception as e:
        print(f"[WARN] Could not fetch YouTube URL automatically: {e}")
        return None

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

# --- Main -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mp3", help="Local MP3 path (optional if using --youtube-url)")
    parser.add_argument("--youtube-url", help="Optional YouTube URL to auto-download audio")
    parser.add_argument("--youtube-api-key", help="YouTube Data API v3 key (used if no --youtube-url provided)")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--genius-token", help="Your Genius API token for lyrics fetch")
    parser.add_argument("--override-lyric-fetch-txt", help="Optional: existing lyrics .txt or .csv path")
    parser.add_argument("--no-tap", action="store_true", help="Skip manual tap mode and use auto-synced CSV")

    args = parser.parse_args()

    # --- Step 0: Fetch YouTube URL if not provided ---
    if not args.youtube_url and args.youtube_api_key:
        print("🔎 Fetching YouTube URL automatically…")
        args.youtube_url = fetch_youtube_url(args.youtube_api_key, args.artist, args.title)

    # --- Step 1: Handle YouTube download ---
    if args.youtube_url:
        print(f"🎧 Downloading audio from YouTube…")
        yt_out = f"songs/{sanitize_name(args.artist)}_{sanitize_name(args.title)}.mp3"
        yt_cmd = f'yt-dlp -x --audio-format mp3 -o "{yt_out}" "{args.youtube_url}"'
        result = subprocess.run(shlex.split(yt_cmd))
        if result.returncode != 0:
            print("❌ Failed to download from YouTube — aborting.")
            sys.exit(1)
        args.mp3 = yt_out
        print(f"✅ Download complete → {args.mp3}\n")
    else:
        if not args.mp3 or not os.path.exists(args.mp3):
            print("❌ No YouTube URL or MP3 file provided.")
            sys.exit(1)

    # --- Step 2: Directory setup ---
    Path("songs").mkdir(exist_ok=True)
    Path("lyrics").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    # --- Step 3: Fetch lyrics ---
    artist_slug = sanitize_name(args.artist)
    title_slug = sanitize_name(args.title)
    lyrics_path = Path("lyrics") / f"{artist_slug}_{title_slug}.txt"

    if args.override_lyric_fetch_txt and os.path.exists(args.override_lyric_fetch_txt):
        lyrics_path = Path(args.override_lyric_fetch_txt)
        print(f"✅ Using provided lyrics: {lyrics_path}")
    else:
        if not args.genius_token:
            print("❌ No lyrics file or Genius token provided.")
            sys.exit(1)
        print(f"🎵 Fetching lyrics for '{args.title}' by {args.artist}…")
        run(
            f'python3 fetch_lyrics.py '
            f'--title "{args.title}" '
            f'--artist "{args.artist}" '
            f'--output "{lyrics_path}" '
            f'--genius-token "{args.genius_token}"'
        )

    # --- Step 3.5: Auto-sync lyrics to audio ---
    print("\n🪄 Auto-syncing lyrics and audio into CSV (karaoke_auto_sync_lyrics.py)...")
    subprocess.run([
        "python3", "karaoke_auto_sync_lyrics.py",
        "--artist", args.artist,
        "--title", args.title
    ], check=True)

    csv_path = Path("lyrics") / f"{artist_slug}_{title_slug}_synced.csv"

    # --- Step 4: Render video ---
    if not args.no_tap:
        print("\n🖱️ Manual tap mode enabled — override or refine timing if needed.\n")
    else:
        print("\n🚀 Skipping manual tap — using auto-synced CSV timings.\n")

    run(
        f'python3 karaoke_time.py '
        f'--csv "{csv_path}" '
        f'--mp3 "{args.mp3}" '
        f'--offset {args.offset} '
        f'--autoplay'
    )

    print("\n✅ Karaoke generation complete!")

# --- Entry point ------------------------------------------------------------
if __name__ == "__main__":
    warn_if_hardcoded_keys(__file__)
    main()

# end of karaoke_generator.py
