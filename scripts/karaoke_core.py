#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_core.py — shared logic for Karaoke Time
This version ensures both interactive (tap-to-time) and CSV playback sustain each lyric
until just before the next block starts.
Now includes: live FFmpeg progress, vertical centering, 20pt smaller font, and smart wrapping.
"""

import csv, os, platform, subprocess, sys, tempfile, time
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path

def read_csv_timing(csv_path: str) -> List[Tuple[float, str]]:
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            ts = float(r["timestamp"])
            txt = r["text"].strip()
            if txt:
                rows.append((ts, txt))
    return rows

def generate_ass(timed_lines: List[Tuple[float, str]], ass_path: str, font_size: int = 140):
    header = f"""[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1280
PlayResY: 720
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Open Sans,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3,0,2,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        for i, (ts, text) in enumerate(timed_lines):
            start = time_to_ass(ts)
            end = time_to_ass(timed_lines[i + 1][0] - 0.1 if i + 1 < len(timed_lines) else ts + 3.0)
            line = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
            f.write(line)

def time_to_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def render_video(csv_path: str, mp3_path: str, output_path: str, font_size: int = 140):
    print("\n🎬 Rendering final karaoke video...")

    timed_lines = read_csv_timing(csv_path)

    ass_path = tempfile.mktemp(suffix=".ass")
    generate_ass(timed_lines, ass_path, font_size)

    # ↓ Adjustments: smaller font, centered vertically, and smart wrapping
    font_size = font_size - 20
    ass_alignment = 5  # middle-center
    ffmpeg_cmd = (
        f'ffmpeg -y '
        f'-f lavfi -i "color=c=black:size=1280x720" '
        f'-i "{mp3_path}" '
        f'-vf "subtitles={ass_path}:force_style='
        f"\'FontSize={font_size},Alignment={ass_alignment},WrapStyle=2,MarginV=60\'\" "
        f'-c:v libx264 -preset medium -crf 20 '
        f'-c:a aac -b:a 192k -shortest '
        f'"{output_path}"'
    )

    # 🎥 Demucs-style live output
    process = subprocess.Popen(
        ffmpeg_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, ffmpeg_cmd)

    print(f"\n✅ Render complete! Saved to {output_path}\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render karaoke video from CSV + MP3")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--mp3", required=True)
    parser.add_argument("--font-size", type=int, default=140)
    parser.add_argument("--offset", type=float, default=0.0)
    args = parser.parse_args()

    csv_path = args.csv
    mp3_path = args.mp3
    font_size = args.font_size

    output_name = f"{Path(mp3_path).stem}_karaoke.mp4"
    output_path = Path("output") / output_name

    render_video(csv_path, mp3_path, str(output_path), font_size)

if __name__ == "__main__":
    main()

# end of karaoke_core.py
