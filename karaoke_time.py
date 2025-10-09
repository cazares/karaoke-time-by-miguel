#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎤 Karaoke Time by Miguel Cázares
Final CLI-compatible version — October 2025
"""

import argparse, csv, os, subprocess, sys, platform
from datetime import datetime


# =====================================================
# Argument parsing
# =====================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Karaoke Time lyric video generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--ass", help="ASS subtitle file path", required=True)
    parser.add_argument("--auto-play", action="store_true",
                        help="Automatically pause media and preview video in QuickTime after generation")
    parser.add_argument("--buffer", type=float, default=0.5,
                        help="Default fade buffer in seconds")
    parser.add_argument("--csv", help="CSV file path", required=True)
    parser.add_argument("--font-size", type=int, default=52,
                        help="Subtitle font size in points")
    parser.add_argument("--lyric-offset", type=float, default=0.0,
                        help="Shift all lyric blocks by N seconds (positive=later, negative=earlier)")
    parser.add_argument("--mp3", help="MP3 audio file path", required=True)
    parser.add_argument("--no-auto-play", action="store_true",
                        help="Disable automatic playback after generation (default)")
    parser.add_argument("--offset", type=float, default=0.0,
                        help="Global audio/video offset in seconds")
    parser.add_argument("--output-prefix", default="non_interactive_",
                        help="Prefix for output files")
    parser.add_argument("--overlap-buffer", type=float, default=0.05,
                        help="Overlap fade buffer seconds")

    # sort alphabetically for --help
    parser._optionals._actions = sorted(parser._optionals._actions,
                                        key=lambda x: x.option_strings[0])
    return parser.parse_args()


# =====================================================
# ASS header
# =====================================================

def generate_ass_header(font_size: int):
    return f"""[Script Info]
Title: Karaoke Time
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default, Helvetica, {font_size}, &H00FFFFFF, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 2, 10, 10, 30, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


# =====================================================
# Helpers
# =====================================================

def abspath(path: str) -> str:
    """Return absolute path if relative."""
    return os.path.abspath(path) if path else path


def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


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
# Write ASS with fade buffer and overlap logic
# =====================================================

def write_ass(lyrics, ass_path, font_size, buffer, overlap_buffer, lyric_offset):
    print(f"📝 Writing ASS file: {ass_path}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(generate_ass_header(font_size))
        for i, (start, end, text) in enumerate(lyrics):
            start += lyric_offset
            end += lyric_offset
            next_start = lyrics[i + 1][0] + lyric_offset if i < len(lyrics) - 1 else None
            if next_start:
                adjusted_end = next_start - (overlap_buffer if next_start < end else buffer)
            else:
                adjusted_end = end
            adjusted_end = max(adjusted_end, start)
            f.write(f"Dialogue: 0,{format_time(start)},{format_time(adjusted_end)},Default,,0,0,0,,{text}\n")


# =====================================================
# ffmpeg encode + optional playback
# =====================================================

def generate_video(mp3_path, ass_path, output_prefix, offset, auto_play=False):
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_name = f"{output_prefix}{date_str}_{os.path.splitext(os.path.basename(mp3_path))[0]}.mp4"

    width, height = 1920, 1080
    with open(ass_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip().startswith("PlayResX:"):
                width = int(line.split(":")[1].strip())
            elif line.strip().startswith("PlayResY:"):
                height = int(line.split(":")[1].strip())

    print("\n🎬 Generating final video:", output_name)
    print("\n⏳ Starting in:\n  3...\n  2...\n  1...\n🎵 Go!\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r=30",
        "-itsoffset", str(offset),
        "-i", mp3_path,
        "-vf", f"subtitles={ass_path}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest",
        output_name
    ]
    subprocess.run(cmd, check=True)
    print(f"\n✅ Done! Output saved as {output_name}")

    if auto_play and platform.system() == "Darwin":
        print("⏸️  Pausing any active media players...")
        try:
            subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to key code 16 using {command down, option down}'
            ])
        except Exception as e:
            print(f"⚠️ Could not send global pause key event: {e}")

        print("🎞️  Opening in QuickTime...")
        try:
            subprocess.run(["open", "-a", "QuickTime Player", output_name])
            subprocess.run([
                "osascript", "-e",
                f'tell application "QuickTime Player" to play (first document whose name contains "{os.path.basename(output_name)}")'
            ])
        except Exception as e:
            print(f"⚠️ QuickTime auto-play failed: {e}")


# =====================================================
# Main
# =====================================================

def main():
    args = parse_args()

    # Convert all paths to absolute
    args.csv = abspath(args.csv)
    args.ass = abspath(args.ass)
    args.mp3 = abspath(args.mp3)

    auto_play = args.auto_play and not args.no_auto_play
    lyrics = load_csv(args.csv)
    preview_csv(lyrics)
    write_ass(lyrics, args.ass, args.font_size, args.buffer,
              args.overlap_buffer, args.lyric_offset)
    generate_video(args.mp3, args.ass, args.output_prefix,
                   args.offset, auto_play=auto_play)


if __name__ == "__main__":
    main()
