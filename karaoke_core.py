#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_core.py — tap-to-time and render karaoke videos with ffmpeg.
"""

import csv, os, subprocess, sys, time
from datetime import datetime
from typing import List

# Tuned defaults
FONT_SIZE = 140
SPACING = 0.25
OFFSET = 0.0
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
    texts = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.read().splitlines():
            t = raw.strip()
            if t == "": continue
            t = t.replace("\\n", "\n")
            texts.append(t)
    return texts

def tap_collect_times(texts: List[str]) -> List[float]:
    print("\n🎤 TAP MODE — Press Enter for each lyric line. Type 'q' to quit.\n")
    input("Ready? Press Enter to start… ")
    t0 = time.perf_counter()
    starts = []
    for idx, text in enumerate(texts, start=1):
        print(f"\n==== Block {idx}/{len(texts)} ====")
        print(text)
        s = input("Press Enter to timestamp (or 'q' to quit): ")
        if s.strip().lower() == "q":
            sys.exit("Aborted.")
        t = time.perf_counter() - t0
        starts.append(t)
        print(f"⏱ {t:.2f}s")
    return starts

def compute_rows_from_starts(starts, texts, spacing_sec, buffer_sec):
    rows = []
    for i, s in enumerate(starts):
        if i < len(starts) - 1:
            e = max(s + 0.2, starts[i+1] - spacing_sec)
        else:
            e = s + 8.0 - buffer_sec
        rows.append((s, e, texts[i]))
    return rows

def write_ass(rows, ass_path, font_size, fade_in_ms, fade_out_ms):
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header(font_size))
        for (start, end, text) in rows:
            text = f"{{\\fad({fade_in_ms},{fade_out_ms})}}{text}"
            f.write(f"Dialogue: 0,{fmt_time_ass(start)},{fmt_time_ass(end)},Default,,0,0,0,,{text}\n")

def ensure_dir(path): os.makedirs(path, exist_ok=True)

def render_video(mp3_path, ass_path, prefix, out_dir):
    ensure_dir(out_dir)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    out_name = f"{prefix}{stamp}_{base}.mp4"
    out_path = os.path.join(out_dir, out_name)

    txt_path = ass_path
    ass_path = os.path.splitext(txt_path)[0] + ".ass"
    csv_path = os.path.join(os.path.dirname(txt_path), "lyrics_timing.csv")
    texts = load_lyrics_txt(txt_path)

    # Smart intro block
    parent = os.path.basename(os.path.dirname(txt_path))
    if "__" in parent:
        artist, title = parent.split("__", 1)
        intro_block = f"{title.replace('_',' ')}\\N\\Nby\\N\\N{artist.replace('_',' ')}"
    else:
        intro_block = f"{base}\\N\\Nby\\N\\NUnknown Artist"
    texts.insert(0, intro_block)

    starts = tap_collect_times(texts)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f); writer.writerow(["Start(sec)", "Lyric"])
        for s, lyric in zip(starts, texts): writer.writerow([f"{s:.3f}", lyric])

    rows = compute_rows_from_starts(starts, texts, SPACING, BUFFER_SEC)
    write_ass(rows, ass_path, FONT_SIZE, int(FADE_IN*1000), int(FADE_OUT*1000))

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-i", str(mp3_path),
        "-vf", f"ass={ass_path}",
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "fast", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(out_path)
    ], check=True)

    print(f"\n✅ Rendered: {out_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lyrics-txt", required=True)
    parser.add_argument("--mp3", required=True)
    parser.add_argument("--prefix", default="non_interactive_")
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--autoplay", action="store_true")
    args = parser.parse_args()
    render_video(args.mp3, args.lyrics_txt, args.prefix, args.out_dir)
