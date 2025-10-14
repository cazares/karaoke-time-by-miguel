#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time

Default behavior:
  • Auto-fetches YouTube audio (via fetch_youtube_url.py) if no URL given
  • Auto-fetches lyrics (via fetch_lyrics.py) if no text provided
  • Auto-syncs lyrics & audio into CSV (via karaoke_auto_sync_lyrics.py)
  • Defaults to interactive tap mode for manual lyric timing override
  • When --no-tap is used with no --vocals-percent, vocals default to 0% (true karaoke mode)

Flags overview:
  --no-tap            → skip manual timing, go straight to auto-sync CSV
  --vocals-percent N  → scale vocals volume after Demucs separation (0–100)
"""

import argparse, os, sys, subprocess, shlex, re
from pathlib import Path
from datetime import datetime

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
def run(cmd: str, debug: bool = True):
    """Runs a shell command with live output and logs to logs/karaoke_generator.log."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "karaoke_generator.log"

    safe_cmd = re.sub(r'(--genius-token|--youtube-key)\s+"[^"]+"', r'\1 "****"', cmd)
    print(f"\n▶️ {safe_cmd}")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n▶️ {safe_cmd}\n=== Started at {datetime.now()} ===\n")
        f.flush()
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            sys.stdout.write(line)
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")
            f.flush()
        process.wait()
        if process.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            f.write(f"❌ Exit code {process.returncode}\n")
            sys.exit(process.returncode)
        f.write(f"✅ Completed at {datetime.now()}\n")

def fetch_youtube_url(api_key: str, artist: str, title: str) -> str:
    """Fetch most relevant YouTube video for artist/title pair."""
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
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        url_lines = [l for l in lines if l.startswith("http")]
        if url_lines:
            url = url_lines[-1]
            print(f"🎥 Auto-fetched YouTube URL: {url}")
            return url
        print(f"[WARN] fetch_youtube_url.py returned unexpected output:\n{result.stdout}")
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
    parser.add_argument("--youtube-api-key", help="YouTube Data API v3 key (defaults to $YT_KEY)")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--genius-token", help="Your Genius API token (defaults to $GENIUS_TOKEN)")
    parser.add_argument("--override-lyric-fetch-txt", help="Optional: existing lyrics .txt or .csv path")
    parser.add_argument("--no-tap", action="store_true", help="Skip manual tap mode and use auto-synced CSV")
    parser.add_argument("--vocals-percent", type=float, help="Adjust vocal stem volume (0–100)")
    args = parser.parse_args()

    # --- Key setup ---
    args.youtube_api_key = args.youtube_api_key or os.getenv("YT_KEY")
    args.genius_token = args.genius_token or os.getenv("GENIUS_TOKEN")

    if not args.youtube_api_key:
        print("❌ Missing YouTube API key. Provide --youtube-api-key or set $YT_KEY.")
        sys.exit(1)
    if not args.genius_token:
        print("❌ Missing Genius token. Provide --genius-token or set $GENIUS_TOKEN.")
        sys.exit(1)

    # --- Logic for karaoke UX ---
    if args.no_tap and args.vocals_percent is None:
        args.vocals_percent = 0.0  # true karaoke mute
    elif args.vocals_percent is None:
        args.vocals_percent = 100.0  # default full vocals

    print(f"\n🎚️ Vocal level set to {args.vocals_percent:.1f}%")

    # --- Step 0: Fetch YouTube URL ---
    if not args.youtube_url and args.youtube_api_key:
        print("🔎 Fetching YouTube URL automatically…")
        args.youtube_url = fetch_youtube_url(args.youtube_api_key, args.artist, args.title)

    # --- Step 1: Download audio ---
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
    elif not args.mp3 or not os.path.exists(args.mp3):
        print("❌ No YouTube URL or MP3 file provided.")
        sys.exit(1)

    # --- Step 2: Directory setup ---
    for d in ["songs", "lyrics", "output"]:
        Path(d).mkdir(exist_ok=True)

    # --- Step 3: Fetch lyrics ---
    artist_slug = sanitize_name(args.artist)
    title_slug = sanitize_name(args.title)
    lyrics_path = Path("lyrics") / f"{artist_slug}_{title_slug}.txt"

    if args.override_lyric_fetch_txt and os.path.exists(args.override_lyric_fetch_txt):
        lyrics_path = Path(args.override_lyric_fetch_txt)
        print(f"✅ Using provided lyrics: {lyrics_path}")
    else:
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
        "--title", args.title,
        "--vocals-percent", str(args.vocals_percent)
    ], check=True)

    csv_path = Path("lyrics") / f"{artist_slug}_{title_slug}_synced.csv"

    # --- Step 4: Render video ---
    if args.no_tap:
        print("\n🚀 Skipping manual tap — using auto-synced CSV timings.\n")
    else:
        print("\n🖱️ Manual tap mode enabled — override or refine timing if needed.\n")

    run(
        f'python3 karaoke_time.py '
        f'--csv "{csv_path}" '
        f'--mp3 "{args.mp3}" '
        f'--offset {args.offset} '
        f'--autoplay'
    )

    print("\n✅ Karaoke generation complete!")

if __name__ == "__main__":
    warn_if_hardcoded_keys(__file__)
    main()

# end of karaoke_generator.py
