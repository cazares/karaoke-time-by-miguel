#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — interactive tap-timing helper for Karaoke Time
Handles ENTER-based timing capture and ASS/MP4 generation.
"""

import argparse, csv, sys, os, time, subprocess
from pathlib import Path

# 🧭 Always operate from project root
os.chdir(Path(__file__).resolve().parent.parent)

def tap_mode(lyrics_path: Path, output_csv: Path, offset: float = 0.0):
    print("\\n🎹 Tap mode: Press ENTER in rhythm with each lyric line.")
    print("Press ENTER to start...")
    input()

    start_time = time.time()
    timestamps = []
    lines = [l.strip() for l in lyrics_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    for idx, line in enumerate(lines):
        input(f"🎵 {line}\\n")
        ts = time.time() - start_time + offset
        timestamps.append((ts, line))
        print(f"🕒 {ts:.2f}s — recorded")

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "text"])
        writer.writeheader()
        for ts, line in timestamps:
            writer.writerow({"timestamp": f"{ts:.3f}", "text": line})

    print(f"\\n✅ Tap timing complete — saved to {output_csv}")
    return output_csv

def render_ass_and_video(csv_path: Path, mp3_path: Path, font_size: int = 140):
    cmd = (
        f'python3 scripts/karaoke_core.py '
        f'--csv "{csv_path}" '
        f'--mp3 "{mp3_path}" '
        f'--font-size {font_size}'
    )
    print(f"\\n🎬 Running FFmpeg render pipeline:\\n▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=False)

def main():
    parser = argparse.ArgumentParser(description="Interactive tap-timing for Karaoke Time")
    parser.add_argument("--lyrics-txt", required=True)
    parser.add_argument("--mp3", required=True)
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--font-size", type=int, default=140)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    lyrics_path = Path(args.lyrics_txt)
    csv_path = lyrics_path.with_suffix(".csv")

    tap_mode(lyrics_path, csv_path, offset=args.offset)
    render_ass_and_video(csv_path, Path(args.mp3), font_size=args.font_size)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n👋 Exiting tap mode gracefully.")
        sys.exit(0)

# end of karaoke_time.py
