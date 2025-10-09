#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎤 Karaoke Time by Miguel Cázares

Last known command line usage as of 10/9 at 10:38am (with font-size 84):

    python3 karaoke_time.py "$(pwd)/lyrics/lyrics_2025-10-07_2126.csv" "$(pwd)/lyrics/lyrics_2025-10-07_2126.ass" "$(pwd)/lyrics/song.mp3" --font-size 84

Created by Miguel Cazares — https://miguelengineer.com
"""

import argparse, csv, os, subprocess, tempfile, shutil
from datetime import datetime

# -------------------- CLI --------------------
def parse_args():
    p = argparse.ArgumentParser(description="Karaoke Time lyric video generator")
    p.add_argument("csv", help="CSV file path")
    p.add_argument("ass", help="ASS subtitle file path (will be written/overwritten)")
    p.add_argument("mp3", help="MP3 audio file path")
    p.add_argument("--font-size", type=int, default=52, help="Subtitle font size (pt)")
    p.add_argument("--buffer", type=float, default=0.5, help="Trim this many seconds from each line's end")
    p.add_argument("--offset", type=float, default=0.0, help="Global audio offset (sec, can be negative)")
    p.add_argument("--output-prefix", default="non_interactive_", help="Output filename prefix")
    return p.parse_args()

# -------------------- ASS header --------------------
def ass_header(font_size: int) -> str:
    return f"""[Script Info]
Title: Karaoke Time
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default, Helvetica, {font_size}, &H00FFFFFF, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 5, 10, 10, 30, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# -------------------- utils --------------------
def fmt_time(s: float) -> str:
    if s < 0: s = 0
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

def load_csv(path: str):
    """
    Robust loader: supports both 2-col [time, lyric] and 3-col [start, end, text].
    """
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        for row in r:
            if not row: 
                continue
            # 2-column: mm:ss.xx, lyric
            if len(row) == 2:
                try:
                    parts = row[0].split(":")
                    start = float(parts[0]) * 60 + float(parts[1])
                    end = start + 3.0
                    text = row[1].strip().replace("\\N", "\n")
                    rows.append((start, end, text))
                except:
                    continue
            # 3+ columns: start(float), end(float), text
            elif len(row) >= 3:
                try:
                    start = float(row[0].strip())
                    end   = float(row[1].strip())
                    text  = row[2].strip().replace("\\N", "\n")
                    rows.append((start, end, text))
                except:
                    continue
    return rows

# -------------------- build ASS --------------------
def write_ass(rows, ass_path, font_size, buffer):
    print(f"📝 Writing ASS file: {ass_path}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header(font_size))
        for start, end, text in rows:
            adj_end = max(end - buffer, start + 0.05)
            f.write(f"Dialogue: 0,{fmt_time(start)},{fmt_time(adj_end)},Default,,0,0,0,,{text}\n")

# -------------------- ffmpeg (robust path handling) --------------------
def generate_video(mp3_path, ass_path, prefix, offset):
    mp3_path = os.path.abspath(mp3_path)
    ass_path = os.path.abspath(ass_path)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_name = f"{prefix}{stamp}_{os.path.splitext(os.path.basename(mp3_path))[0]}.mp4"

    print("\n🎬 Generating final video:", out_name)
    print("\n⏳ Starting in:\n  3...\n  2...\n  1...\n🎵 Go!\n")

    # Copy ASS to a temp path with a safe filename (no spaces/quotes)
    tmpdir = tempfile.mkdtemp(prefix="karaoke_")
    safe_ass = os.path.join(tmpdir, os.path.basename(ass_path).replace(" ", "_").replace("'", "_"))
    shutil.copy2(ass_path, safe_ass)

    # Build filter WITHOUT shell quoting—argv handles spaces, and the safe path has no specials.
    vf_arg = f"subtitles={safe_ass}"

    cmd = [
        "ffmpeg", "-loglevel", "info", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-itsoffset", str(offset),
        "-i", mp3_path,
        "-vf", vf_arg,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest",
        out_name
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Done! Output saved as {out_name}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# -------------------- main --------------------
def main():
    a = parse_args()
    rows = load_csv(os.path.abspath(a.csv))

    print("\nCSV Preview (first 10 rows):")
    print("Start      End        Text")
    print("--------------------------------------------------")
    for s, e, t in rows[:10]:
        print(f"{s:<10.2f} {e:<10.2f} {t}")

    write_ass(rows, os.path.abspath(a.ass), a.font_size, a.buffer)
    generate_video(a.mp3, a.ass, a.output_prefix, a.offset)

if __name__ == "__main__":
    main()
