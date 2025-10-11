#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_core.py — core logic for lyric timing & rendering
Now includes automatic FFmpeg rendering step after .ASS creation.
"""

import csv, os, sys, subprocess, shlex
from pathlib import Path
from datetime import datetime

def seconds_to_ass(ts):
    m, s = divmod(float(ts), 60)
    return f"0:{int(m):02d}:{s:05.2f}".replace('.', ',')

def render_karaoke_video(audio_path, ass_path, output_path, font_name, font_size):
    """Run FFmpeg to render final karaoke MP4 automatically."""
    print(f"\n🎬 Rendering karaoke video to {output_path}...")
    ffmpeg_cmd = f"""
        ffmpeg -f lavfi -i color=c=black:size=1280x720 \
        -i "{audio_path}" \
        -vf "subtitles={ass_path}:force_style='Fontsize={font_size},Fontname={font_name}'" \
        -c:a aac -shortest -movflags +faststart "{output_path}"
    """
    try:
        subprocess.run(shlex.split(ffmpeg_cmd), check=True)
        print(f"✅ Karaoke video created: {output_path}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 karaoke_core.py lyrics_timing.csv test_vocals_audio.mp3")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    audio_path = Path(sys.argv[2])

    # Generate .ass
    ass_path = csv_path.with_suffix(".ass")
    print(f"🪶 Generating ASS from {csv_path} ...")

    with open(csv_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    font_name = "Helvetica Neue Bold"
    font_size = 140
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,5,50,50,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []
    for i, row in enumerate(rows):
        start = seconds_to_ass(row["timestamp"])
        end = seconds_to_ass(rows[i + 1]["timestamp"]) if i + 1 < len(rows) else seconds_to_ass(float(row["timestamp"]) + 3)
        lyric = row["text"].strip().replace("\\N\\N", "\\N\\N").replace("\\N", "\\N").replace(",", "，")
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{lyric}")

    ass_path.write_text(header + "\n".join(lines), encoding="utf-8")
    print(f"✅ ASS file written: {ass_path}")

    # Output file path
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{audio_path.stem}_karaoke.mp4"

    # Auto-render via FFmpeg
    render_karaoke_video(audio_path, ass_path, output_path, font_name, font_size)

if __name__ == "__main__":
    main()

# end of karaoke_core.py
