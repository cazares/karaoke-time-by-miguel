#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — unified entrypoint for Karaoke Time
Now:
- Passes --font-size to karaoke_time.py
- Automatically overrides Whisper CSV with Genius lyrics
- Centers text horizontally and vertically in output video
"""

import argparse, os, sys, subprocess, shlex, re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)
DEFAULT_OUTPUT_DIR = Path("songs")

def warn_if_hardcoded_keys(script_path: str):
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        if re.search(r"AIza[0-9A-Za-z\-_]{20,}", content):
            print("⚠️  WARNING: Hardcoded API key detected.")
    except Exception:
        pass

def run(cmd, debug: bool = True):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "karaoke_generator.log"

    with open(log_file, "a", encoding="utf-8") as f:
        if isinstance(cmd, list):
            display_cmd = " ".join(shlex.quote(c) for c in cmd)
        else:
            display_cmd = cmd
            cmd = shlex.split(cmd)

        safe_cmd = re.sub(r'(--genius-token|--youtube-key)\s+"[^"]+"', r'\1 "****"', display_cmd)
        print(f"\n▶️ {safe_cmd}")
        f.write(f"\n\n▶️ {safe_cmd}\n")
        f.flush()

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            sys.stdout.write(line)
            f.write(line)
            f.flush()
        process.wait()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, display_cmd)

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def fetch_youtube_url(api_key: str, artist: str, title: str) -> str:
    try:
        result = subprocess.run(
            [
                "python3", "scripts/fetch_youtube_url.py",
                "--song", title,
                "--artist", artist,
                "--youtube-key", api_key,
            ],
            capture_output=True, text=True, check=True
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        url_lines = [l for l in lines if l.startswith("http")]
        if url_lines:
            return url_lines[-1]
        print(f"[WARN] fetch_youtube_url.py returned no URL:\n{result.stdout}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[WARN] fetch_youtube_url.py failed:\n{e.stdout or ''}\n{e.stderr or ''}")
        return None

def main():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time — auto lyrics & video generator")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mp3", help="Optional local MP3 path")
    parser.add_argument("--youtube-url", help="Optional YouTube URL to skip auto-fetch")
    parser.add_argument("--youtube-api-key", help="YouTube Data API key (or env $YT_KEY)")
    parser.add_argument("--genius-token", help="Genius API token (or env $GENIUS_TOKEN)")
    parser.add_argument("--offset", type=float, default=0.0, help="Global sync offset (seconds)")
    parser.add_argument("--vocals-percent", type=float, default=0.0, help="Vocals mix % (0 for karaoke)")
    parser.add_argument("--interactive", action="store_true", help="Enable tap-timing mode (default off)")
    parser.add_argument("--final", action="store_true", help="Full-quality mode (slower)")
    parser.add_argument("--clear-cache", action="store_true", help="Force rerun of Demucs/Whisper cache")
    parser.add_argument("--run-all", action="store_true", help="Run full chain through MP4 render")
    parser.add_argument("--font-size", type=int, default=140, help="Font size for subtitles")
    args = parser.parse_args()

    args.youtube_api_key = args.youtube_api_key or os.getenv("YT_KEY")
    args.genius_token = args.genius_token or os.getenv("GENIUS_TOKEN")

    if not args.youtube_api_key or not args.genius_token:
        print("❌ Missing API keys (YouTube / Genius).")
        sys.exit(1)

    Path("songs").mkdir(exist_ok=True)
    Path("lyrics").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    artist_slug = sanitize_name(args.artist)
    title_slug = sanitize_name(args.title)
    mp3_out = Path("songs") / f"{artist_slug}_{title_slug}.mp3"
    lyrics_path = Path("lyrics") / f"{artist_slug}_{title_slug}.txt"
    csv_path = Path("lyrics") / f"{artist_slug}_{title_slug}_synced.csv"
    csv_override = Path("lyrics") / f"{artist_slug}_{title_slug}_synced_genius.csv"

    print("🔎 Fetching YouTube URL automatically…")
    youtube_url = args.youtube_url or fetch_youtube_url(args.youtube_api_key, args.artist, args.title)

    if youtube_url:
        print(f"🎥 Found URL: {youtube_url}")
    elif mp3_out.exists():
        print(f"⚠️ Could not fetch new YouTube URL — using cached MP3: {mp3_out}")
    else:
        print("❌ No YouTube URL found and no cached MP3 available. Aborting.")
        sys.exit(1)

    if not mp3_out.exists() and youtube_url:
        run(f'yt-dlp -x --audio-format mp3 -o "{mp3_out}" "{youtube_url}"')
    else:
        print(f"🌀 Cached MP3: {mp3_out}")

    if not lyrics_path.exists() or args.clear_cache:
        run([
            "python3", "scripts/fetch_lyrics.py",
            "--title", args.title,
            "--artist", args.artist,
            "--output", str(lyrics_path),
            "--genius-token", args.genius_token,
        ])
    else:
        print(f"🌀 Cached lyrics: {lyrics_path}")

    cmd = [
        "python3", "-u", "scripts/karaoke_auto_sync_lyrics.py",
        "--artist", args.artist,
        "--title", args.title,
    ]
    if args.clear_cache:
        cmd.append("--clear-cache")
    if args.final:
        cmd.append("--final")
    if args.vocals_percent > 0:
        cmd += ["--vocals-percent", str(args.vocals_percent)]

    run(cmd)

    # ✅ NEW: Automatically override Whisper CSV with Genius lyrics
    if csv_path.exists() and lyrics_path.exists():
        run([
            "python3", "scripts/override_lyrics_with_genius.py",
            "--whisper", str(csv_path),
            "--genius", str(lyrics_path),
            "--out", str(csv_override)
        ])
    else:
        print("⚠️ Missing Whisper CSV or Genius TXT; skipping lyric override.")

    # ✅ NEW: Pass font-size and use vertically centered alignment
    if args.run_all:
        font_size_arg = getattr(args, "font_size", 140)
        run(
            f'python3 scripts/karaoke_time.py '
            f'--csv "{csv_override if csv_override.exists() else csv_path}" '
            f'--mp3 "{mp3_out}" '
            f'--offset {args.offset} '
            f'--font-size {font_size_arg} '
            f'--center-text'
        )

    print("\n✅ Karaoke generation complete!")

if __name__ == "__main__":
    warn_if_hardcoded_keys(__file__)
    main()

# end of karaoke_generator.py
