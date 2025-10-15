#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — render MP4 from CSV + MP3 + ASS
Fully verbose, unchanged behavior (just relative path safety).
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run(cmd):
    print(f"\n▶️ {cmd}")
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in p.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    p.wait()
    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd)

def main():
    parser = argparse.ArgumentParser(description="🎬 Karaoke Time Renderer")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--mp3", required=True)
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--autoplay", action="store_true")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    mp3_path = Path(args.mp3)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"{mp3_path.stem}.mp4"
    ass_path = csv_path.with_suffix(".ass")

    print(f"🎨 Rendering {output_path.name} from {csv_path.name} + {mp3_path.name}")
    run(f'ffmpeg -y -i "{mp3_path}" -vf "ass={ass_path}" -c:v libx264 -c:a aac -b:a 192k "{output_path}"')

    if args.autoplay:
        run(f'open -a "QuickTime Player" "{output_path}"')

    print(f"\n✅ Render complete → {output_path}")

if __name__ == "__main__":
    main()

# end of karaoke_time.py
