#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_core.py — shared logic for Karaoke Time
Manual tap-to-time workflow + optional reused timing CSV.
Adds --artist, --title, and --offset support.
"""

import csv, os, subprocess, sys, time
from datetime import datetime
from typing import List

FONT_SIZE = 140
SPACING = 0.25
OFFSET_DEFAULT = 0.0
FADE_IN = 0.1
FADE_OUT = 0.1
BUFFER_SEC = 0.5
OUTPUT_DIR = "output"

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

def fmt_time_ass(s: float) -> str:
    if s < 0: s = 0
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

def load_lyrics_txt(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().replace("\\n", "\n") for line in f if line.strip()]

def tap_collect_times(texts: List[str]) -> List[float]:
    print("\n🎤 TAP-TO-TIME MODE\nPress Enter once per lyric. First press starts the clock.")
    input("Ready? Press Enter to ARM the clock… ")
    t0 = time.perf_counter()
    starts = []
    for idx, text in enumerate(texts, start=1):
        print(f"\n==== Block {idx}/{len(texts)} ====\n{text}")
        s = input("Press Enter to timestamp (or 'q' to quit): ")
        if s.strip().lower() == "q":
            print("Aborted."); sys.exit(1)
        starts.append(time.perf_counter() - t0)
    return starts

def compute_rows(starts, texts, spacing, buffer, offset):
    rows = []
    for i, s in enumerate(starts):
        s -= offset
        if s < 0: s = 0
        e = (starts[i+1] - spacing - offset) if i < len(starts)-1 else s + 8.0 - buffer
        rows.append((s, e, texts[i]))
    return rows

def write_ass(rows, ass_path, font_size, fade_in_ms, fade_out_ms):
    print(f"📝 Writing ASS: {ass_path}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header(font_size))
        for (start, end, text) in rows:
            f.write(f"Dialogue: 0,{fmt_time_ass(start)},{fmt_time_ass(end)},Default,,0,0,0,,{{\\fad({fade_in_ms},{fade_out_ms})}}{text}\n")

def render_video(mp3, txt, prefix, out_dir, artist, title, offset):
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = os.path.join(out_dir, f"{prefix}{stamp}_{Path(mp3).stem}.mp4")

    texts = load_lyrics_txt(txt)
    intro = f"{title}\\N\\Nby\\N\\N{artist}" if artist and title else f"{Path(txt).stem}\\N\\Nby\\N\\NUnknown Artist"
    texts.insert(0, intro)

    csv_path = os.path.join(os.path.dirname(txt), "lyrics_timing.csv")
    if os.path.exists(csv_path):
        reuse = input(f"\n🟡 Detected existing timing file:\n{csv_path}\nReuse it? (Y/n): ").strip().lower()
        if reuse in ("", "y", "yes"):
            starts = []
            with open(csv_path) as f:
                next(f)
                for line in csv.reader(f):
                    try: starts.append(float(line[0]))
                    except: pass
        else:
            starts = tap_collect_times(texts)
    else:
        starts = tap_collect_times(texts)

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Start", "Lyric"])
        [w.writerow([f"{s:.3f}", t]) for s, t in zip(starts, texts)]
    rows = compute_rows(starts, texts, SPACING, BUFFER_SEC, offset)
    write_ass(rows, os.path.splitext(txt)[0] + ".ass", FONT_SIZE, int(FADE_IN*1000), int(FADE_OUT*1000))

    subprocess.run([
        "ffmpeg","-y","-f","lavfi","-i","color=c=black:s=1920x1080:r=30",
        "-i", mp3, "-vf", f"ass={os.path.splitext(txt)[0]}.ass",
        "-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","fast",
        "-tune","stillimage","-c:a","aac","-b:a","192k","-shortest",
        "-movflags","+faststart", out_path
    ], check=True)
    print(f"\n✅ Rendered: {out_path}")

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    p = argparse.ArgumentParser()
    p.add_argument("--lyrics-txt", required=True)
    p.add_argument("--mp3", required=True)
    p.add_argument("--artist"); p.add_argument("--title")
    p.add_argument("--prefix", default="non_interactive_")
    p.add_argument("--out-dir", default="output")
    p.add_argument("--offset", type=float, default=OFFSET_DEFAULT)
    p.add_argument("--autoplay", action="store_true")
    a = p.parse_args()
    try:
        render_video(a.mp3, a.lyrics_txt, a.prefix, a.out_dir, a.artist, a.title, a.offset)
        if a.autoplay:
            newest = max((os.path.join(a.out_dir, f) for f in os.listdir(a.out_dir)), key=os.path.getmtime)
            subprocess.run(["open", "-a", "QuickTime Player", newest])
    except Exception as e:
        print("❌", e); sys.exit(1)
