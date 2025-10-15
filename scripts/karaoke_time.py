#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — single entrypoint (interactive + non-interactive)
Now supports:
  --center-text : vertically + horizontally centers subtitles
"""

import argparse, csv, os, subprocess, platform, tempfile
from datetime import datetime
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="🎤 Karaoke Time")
    parser.add_argument("--lyrics-txt", help="Path to plain-text lyrics file")
    parser.add_argument("--csv", help="Path to timestamped lyrics CSV")
    parser.add_argument("--mp3", required=True, help="Audio file path")
    parser.add_argument("--offset", type=float, default=0.0, help="Global timing offset (sec)")
    parser.add_argument("--font-size", type=int, default=140, help="Font size for subtitles")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--center-text", action="store_true", help="Center subtitles vertically + horizontally")
    return parser.parse_args()

def read_csv(csv_path):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append(r)
    return rows

def make_ass(csv_path, font_size, center_text):
    rows = read_csv(csv_path)
    ass_path = Path(csv_path).with_suffix(".ass")

    alignment = 5 if center_text else 2  # 5 = center both, 2 = bottom center
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("Title: Karaoke Time\n")
        f.write("ScriptType: v4.00+\n")
        f.write("Collisions: Normal\n")
        f.write("PlayResX: 1280\n")
        f.write("PlayResY: 720\n")
        f.write("WrapStyle: 2\n")
        f.write("\n[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
                "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(f"Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3,0,{alignment},20,20,20,1\n")
        f.write("\n[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for row in rows:
            start = row["timestamp"]
            text = row["text"].replace("\\n", "\\N")
            end_time = next_end(rows, row, start)
            f.write(f"Dialogue: 0,{start},{end_time},Default,,0,0,0,,{text}\n")

    print(f"✅ Created ASS: {ass_path}")
    return ass_path

def next_end(rows, current_row, start):
    """Estimate the end timestamp as the next row's timestamp or +3s fallback."""
    idx = rows.index(current_row)
    if idx + 1 < len(rows):
        return rows[idx + 1]["timestamp"]
    else:
        parts = [int(float(x)) for x in start.replace('.', ':').split(':')]
        # add 3 seconds fallback
        h, m, s = parts if len(parts) == 3 else (0, 0, 0)
        s += 3
        if s >= 60:
            s -= 60
            m += 1
        return f"{h:01d}:{m:02d}:{s:02d}.00"

def render_video(mp3_path, ass_path):
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / (Path(mp3_path).stem + "_karaoke.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:size=1280x720",
        "-i", str(mp3_path),
        "-vf", f"subtitles='{ass_path}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Render complete! Saved to {out_path}")

def main():
    args = parse_args()
    csv_path = args.csv
    if not csv_path and args.lyrics_txt:
        print("⚠️  Only CSV input supported for sync at this stage.")
        return

    ass_path = make_ass(csv_path, args.font_size, args.center_text)
    render_video(args.mp3, ass_path)
    print("✅ Auto-sync complete! 🎉")

if __name__ == "__main__":
    main()

# end of karaoke_time.py
