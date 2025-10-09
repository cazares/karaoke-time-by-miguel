#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — Karaoke Time lyric video generator
Final CLI-compatible version (October 2025)
"""

import argparse
import csv
import os
import subprocess
import sys


# =====================================================
# Argument parsing (alphabetically sorted)
# =====================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Karaoke Time lyric video generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--ass", help="ASS subtitle file path", default=None)
    parser.add_argument("--buffer", type=float, default=0.5, help="Default fade buffer (seconds)")
    parser.add_argument("--csv", help="CSV file path", default=None)
    parser.add_argument("--font-size", type=int, default=52, help="Subtitle font size in points")
    parser.add_argument("--lyric-offset", type=float, default=0.0, help="Lyric block timing offset in seconds (positive = later, negative = earlier)")
    parser.add_argument("--mp3", help="MP3 audio file path", default=None)
    parser.add_argument("--offset", type=float, default=0.0, help="Global audio/video offset in seconds")
    parser.add_argument("--output-prefix", default="non_interactive_", help="Prefix for output files")
    parser.add_argument("--overlap-buffer", type=float, default=0.05, help="Overlap buffer (seconds)")

    # Sort args alphabetically in help output
    parser._optionals._actions = sorted(parser._optionals._actions, key=lambda x: x.option_strings[0])
    return parser.parse_args()


# =====================================================
# ASS subtitle header
# =====================================================

def generate_ass_header(font_size: int):
    return f"""[Script Info]
Title: Karaoke Time
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default, Arial, {font_size}, &H00FFFFFF, &H000000FF, &H00000000, &H32000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 2, 10, 10, 30, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


# =====================================================
# Time formatting helper
# =====================================================

def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:01d}:{m:02d}:{s:05.2f}"


# =====================================================
# CSV loading + preview
# =====================================================

def load_csv(csv_path: str):
    lyrics = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            start = float(row[0].strip())
            end = float(row[1].strip())
            text = row[2].strip().replace("\\n", "\n")
            lyrics.append((start, end, text))
    return lyrics


def preview_csv(lyrics):
    print("\nCSV Preview (first 10 rows):")
    print("{:<10} {:<10} {}".format("Start", "End", "Text"))
    print("-" * 50)
    for i, (s, e, t) in enumerate(lyrics[:10]):
        print(f"{s:<10.2f} {e:<10.2f} {t}")
    if len(lyrics) > 10:
        print(f"... ({len(lyrics)} total rows)\n")


# =====================================================
# ASS writing (adaptive buffer, overlap handling)
# =====================================================

def write_ass(lyrics, ass_path, font_size, buffer, overlap_buffer, lyric_offset):
    print(f"📝 Writing ASS file: {ass_path}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(generate_ass_header(font_size))

        for i, (start, end, text) in enumerate(lyrics):
            # Apply lyric offset
            start += lyric_offset
            end += lyric_offset

            next_start = lyrics[i + 1][0] + lyric_offset if i < len(lyrics) - 1 else None

            if next_start:
                # Default 500 ms, overlap 50 ms
                if next_start < end:
                    adjusted_end = next_start - overlap_buffer
                else:
                    adjusted_end = min(end, next_start - buffer)
            else:
                adjusted_end = end

            adjusted_end = max(adjusted_end, start)
            f.write(f"Dialogue: 0,{format_time(start)},{format_time(adjusted_end)},Default,,0,0,0,,{text}\n")


# =====================================================
# FFmpeg invocation
# =====================================================

def generate_video(mp3_path, ass_path, output_prefix, offset):
    output_name = f"{output_prefix}{os.path.splitext(os.path.basename(mp3_path))[0]}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-itsoffset", str(offset),
        "-i", mp3_path,
        "-vf", f"ass={ass_path}",
        "-c:a", "aac",
        "-b:a", "192k",
        output_name
    ]
    print(f"\n🎬 Generating final video: {output_name}")
    subprocess.run(cmd, check=True)
    print("\n✅ Done! Output saved as", output_name)


# =====================================================
# Main
# =====================================================

def main():
    args = parse_args()

    if not args.csv or not args.ass or not args.mp3:
        print("❌ Error: --csv, --ass, and --mp3 are required.")
        sys.exit(1)

    lyrics = load_csv(args.csv)
    preview_csv(lyrics)

    write_ass(
        lyrics,
        args.ass,
        args.font_size,
        args.buffer,
        args.overlap_buffer,
        args.lyric_offset
    )
    generate_video(args.mp3, args.ass, args.output_prefix, args.offset)


if __name__ == "__main__":
    main()
