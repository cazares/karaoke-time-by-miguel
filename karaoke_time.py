#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎤 Karaoke Time by Miguel Cázares

LKG (saved 2025-10-09 10:49 CT) one-liner:
    python3 karaoke_time.py "$(pwd)/lyrics/lyrics_2025-10-07_2126.csv" "$(pwd)/lyrics/lyrics_2025-10-07_2126.ass" "$(pwd)/lyrics/song.mp3" --font-size 84

NEXT ITERATION (adds --lyric-block-spacing):
Example run:
    python3 karaoke_time.py "$(pwd)/lyrics/lyrics_2025-10-07_2126.csv" "$(pwd)/lyrics/lyrics_2025-10-07_2126.ass" "$(pwd)/lyrics/song.mp3" --font-size 84 --lyric-block-spacing 0.8

• End time of each block = next block start − spacing (seconds).
• Fade-out ends exactly at that end time.
• For the final block (no next), we fall back to CSV end minus --buffer.
• Durations are clamped so each line stays ≥ 0.20s on screen.
"""

import argparse, csv, os, platform, subprocess
from datetime import datetime

# -------------------- CLI --------------------
def parse_args():
    p = argparse.ArgumentParser(description="Karaoke Time lyric video generator")
    p.add_argument("csv", help="CSV file path")
    p.add_argument("ass", help="ASS subtitle file path")
    p.add_argument("mp3", help="MP3 audio file path")
    p.add_argument("--font-size", type=int, default=52, help="Subtitle font size (pt)")
    p.add_argument("--buffer", type=float, default=0.5, help="For final line only: trim this many seconds from end")
    p.add_argument("--lyric-block-spacing", type=float, default=0.5,
                   help="Seconds to leave before the next block (end = next_start - spacing)")
    p.add_argument("--fade-out-ms", type=int, default=300,
                   help="Fade-out length in milliseconds; fade ends exactly at the line's end")
    p.add_argument("--offset", type=float, default=0.0, help="Global audio offset (sec, can be negative)")
    p.add_argument("--output-prefix", default="non_interactive_", help="Output filename prefix")
    p.add_argument("--pause-script", default="pause_media.applescript",
                   help="AppleScript file to pause media after encode")
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
Style: Default, Helvetica, {font_size}, &H00FFFFFF, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 5, 50, 50, 60, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# -------------------- utils --------------------
def fmt_time(s: float) -> str:
    if s < 0: s = 0
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

def load_csv(path: str):
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            if len(row) == 2:  # [time, lyric]
                try:
                    mm, ss = row[0].split(":")
                    start = float(mm) * 60 + float(ss)
                    end = start + 3.0
                    text = row[1].strip().replace("\\n", "\n")
                    rows.append((start, end, text))
                except:
                    continue
            elif len(row) >= 3:  # [start, end, text]
                try:
                    start = float(row[0].strip())
                    end   = float(row[1].strip())
                    text  = row[2].strip().replace("\\n", "\n")
                    rows.append((start, end, text))
                except:
                    continue
    return rows

# -------------------- build ASS (with spacing) --------------------
def write_ass(rows, ass_path, font_size, buffer_sec, spacing_sec, fade_out_ms):
    print(f"📝 Writing ASS file: {ass_path}")
    MIN_VISIBLE = 0.20  # seconds
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header(font_size))
        for i, (start, end, text) in enumerate(rows):
            if i < len(rows) - 1:
                next_start = rows[i+1][0]
                adjusted_end = next_start - spacing_sec
            else:
                adjusted_end = end - buffer_sec
            adjusted_end = max(adjusted_end, start + MIN_VISIBLE)  # clamp

            txt = "{\\fad(0," + str(max(0, int(fade_out_ms))) + ")}" + text
            f.write(f"Dialogue: 0,{fmt_time(start)},{fmt_time(adjusted_end)},Default,,0,0,0,,{txt}\n")

# -------------------- pause media (simple) --------------------
def stop_all_media_simple(script_path: str):
    if platform.system() != "Darwin":
        return
    script_abs = os.path.abspath(script_path)
    if os.path.exists(script_abs):
        subprocess.run(["osascript", script_abs], check=False)
    else:
        print(f"⚠️ pause script not found: {script_abs} (skipping)")

# -------------------- ffmpeg --------------------
def generate_video(mp3_path, ass_path, prefix, offset, pause_script):
    mp3_path = os.path.abspath(mp3_path)
    ass_path = os.path.abspath(ass_path)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_name = f"{prefix}{stamp}_{os.path.splitext(os.path.basename(mp3_path))[0]}.mp4"

    print("\n🎬 Generating final video:", out_name)
    print("\n⏳ Starting in:\n  3...\n  2...\n  1...\n🎵 Go!\n")

    vf_arg = f"subtitles='{ass_path}'"

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-itsoffset", str(offset),
        "-i", mp3_path,
        "-vf", vf_arg,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest",
        out_name
    ]
    subprocess.run(cmd, check=True)

    # Pause media AFTER encode
    stop_all_media_simple(pause_script)

    print(f"\n✅ Done! Output saved as {out_name}")

# -------------------- main --------------------
def main():
    a = parse_args()
    rows = load_csv(os.path.abspath(a.csv))

    print("\nCSV Preview (first 10 rows):")
    print("Start      End        Text")
    print("--------------------------------------------------")
    for s, e, t in rows[:10]:
        print(f"{s:<10.2f} {e:<10.2f} {t}")

    write_ass(
        rows,
        os.path.abspath(a.ass),
        a.font_size,
        a.buffer,
        a.lyric_block_spacing,
        a.fade_out_ms
    )
    generate_video(a.mp3, a.ass, a.output_prefix, a.offset, a.pause_script)

if __name__ == "__main__":
    main()
