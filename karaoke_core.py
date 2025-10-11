#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_core.py — core timing and rendering engine
Handles tap-to-time lyric synchronization and FFmpeg video rendering.
Supports --no-prompt to skip confirmations (auto “n” for reuse timing).
"""

import os, sys, time, csv, subprocess, platform
from pathlib import Path

NO_PROMPT = "--no-prompt" in sys.argv

def ask(prompt, default="y"):
    """Ask user unless --no-prompt is active."""
    if NO_PROMPT:
        print(f"{prompt} (auto-selected '{default}')")
        return default.lower()
    return input(prompt).strip().lower() or default.lower()

def render_video(lyrics_txt, mp3_path, artist=None, title=None, offset=None, autoplay=False):
    """Render final karaoke video with embedded lyrics."""
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{Path(mp3_path).stem}_karaoke.mp4"
    out_path = out_dir / out_name

    print(f"\n🎥 Rendering karaoke video → {out_path}")
    try:
        # Generate FFmpeg subtitle filter
        vf = f"subtitles={lyrics_txt}:force_style='FontSize=48,Alignment=2'"

        cmd = [
            "ffmpeg", "-y",
            "-i", mp3_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_path)
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Rendered successfully: {out_path}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ FFmpeg failed: {e}")

    if autoplay:
        try:
            print("▶️ Autoplay enabled — launching output video...")
            if platform.system() == "Darwin":
                subprocess.run(["open", str(out_path)])
            elif platform.system() == "Windows":
                os.startfile(out_path)
            else:
                subprocess.run(["xdg-open", str(out_path)])
        except Exception:
            print("⚠️ Could not autoplay video.")

def tap_to_time(lyrics_blocks, csv_path):
    """Tap Enter per lyric block to record precise timing."""
    print("\n🎤 TAP-TO-TIME MODE")
    print("Press Enter once per lyric block. First press starts the clock.")
    if not NO_PROMPT:
        input("Ready? Press Enter to ARM the clock… ")

    timestamps = []
    t0 = None
    try:
        for i, block in enumerate(lyrics_blocks, start=1):
            print(f"\n==== Block {i}/{len(lyrics_blocks)} ====")
            print(block)
            if i == 1:
                input("Press Enter to start timing: ")
                t0 = time.time()
                timestamps.append(0.0)
            else:
                input("Press Enter to timestamp: ")
                timestamps.append(round(time.time() - t0, 3))
    except KeyboardInterrupt:
        print("\n⏹ Interrupted by user.")
        return

    # Write timing CSV
    rows = zip(range(1, len(lyrics_blocks)+1), lyrics_blocks, timestamps)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "text", "timestamp"])
        for row in rows:
            writer.writerow(row)
    print(f"\n✅ Saved timing to: {csv_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Core karaoke timing and rendering")
    parser.add_argument("--lyrics-txt", required=True, help="Path to lyrics .txt")
    parser.add_argument("--mp3", required=True, help="Path to MP3 file")
    parser.add_argument("--artist", help="Artist name")
    parser.add_argument("--title", help="Song title")
    parser.add_argument("--offset", type=float, default=0.0, help="Timing offset (seconds)")
    parser.add_argument("--autoplay", action="store_true", help="Auto-play final MP4")
    parser.add_argument("--no-prompt", action="store_true", help="Skip confirmations")
    args = parser.parse_args()

    global NO_PROMPT
    NO_PROMPT = args.no_prompt

    lyrics_path = Path(args.lyrics_txt)
    lyrics_text = lyrics_path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in lyrics_text.splitlines() if b.strip()]

    csv_path = lyrics_path.with_name("lyrics_timing.csv")

    if csv_path.exists():
        choice = ask(f"\n🟡 Detected existing timing file:\n{csv_path}\nReuse it? (Y/n): ", default="n")
        if choice == "y":
            print(f"✅ Reusing timing from {csv_path}")
        else:
            tap_to_time(blocks, csv_path)
    else:
        tap_to_time(blocks, csv_path)

    render_video(
        lyrics_txt=str(lyrics_path),
        mp3_path=str(args.mp3),
        artist=args.artist,
        title=args.title,
        offset=args.offset,
        autoplay=args.autoplay,
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting gracefully.")
        sys.exit(0)
