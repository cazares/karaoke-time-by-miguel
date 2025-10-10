#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_core.py — shared logic for Karaoke Time
This version ensures both interactive (tap-to-time) and CSV playback sustain each lyric
until just before the next block starts.
"""

import csv, os, platform, subprocess, sys, tempfile, time
from datetime import datetime
from typing import List, Tuple, Optional

# Tuned defaults
FONT_SIZE = 140
SPACING = 0.25
OFFSET = 0.0  # Updated default (was 1.5)
FADE_IN = 0.1
FADE_OUT = 0.1
BUFFER_SEC = 0.5
OUTPUT_DIR = "output"
MP3_DEFAULT = "lyrics/song.mp3"
PAUSE_SCRIPT_DEFAULT = "pause_media.applescript"

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

def fmt_time_mmss(s: float) -> str:
    if s < 0: s = 0
    m = int(s // 60); sec = s - 60 * m
    return f"{m:02d}:{sec:05.2f}"

def parse_time_token(tok: str) -> Optional[float]:
    tok = tok.strip()
    if not tok: return None
    if ":" in tok:
        parts = tok.split(":")
        try:
            if len(parts) == 2: return float(parts[0]) * 60 + float(parts[1])
            if len(parts) == 3: return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except: return None
    else:
        try: return float(tok)
        except: return None
    return None

def load_csv_any(path: str) -> List[Tuple[float, float, str]]:
    """Supports time,lyric or start,end,text formats."""
    rows: List[Tuple[float, float, str]] = []
    with open(path, "r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        for row in r:
            if not row: continue
            if row[0].strip().lower().startswith("time"):
                if len(row) == 1 or (len(row) > 1 and row[1].strip().lower().startswith("lyric")):
                    continue
            try:
                if len(row) == 2:
                    start = parse_time_token(row[0])
                    end = start  # placeholder; real sustain computed later
                    text = row[1]
                else:
                    start = float(row[0]); end = float(row[1]); text = row[2]
            except:
                continue
            text = (text or "").replace("\\n", "\n")
            rows.append((float(start or 0.0), float(end), text))
    return rows

def load_lyrics_txt(path: str) -> List[str]:
    texts: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.read().splitlines():
            t = raw.strip()
            if t == "": continue
            t = t.replace("\\n", "\n")
            texts.append(t)
    return texts

def tap_collect_times(texts: List[str], count_in_sec: float = 0.0) -> List[float]:
    print("\nTAP-TO-TIME\n• Press Enter once per lyric.\n• First press arms the clock.\n• Type 'q' + Enter to abort.\n")
    input("Ready? Press Enter to ARM the clock… ")
    if count_in_sec > 0:
        print(f"Counting in {count_in_sec:.2f}s…"); time.sleep(count_in_sec)
    t0 = time.perf_counter()
    starts: List[float] = []
    for idx, text in enumerate(texts, start=1):
        print(f"\n==== Block {idx}/{len(texts)} ====")
        print(text)
        s = input("Press Enter to timestamp (or 'q' to quit): ")
        if s.strip().lower() == "q":
            print("Aborted."); sys.exit(1)
        t = time.perf_counter() - t0
        starts.append(t)
        print(f"⏱ {t:.2f}s")
    return starts

def compute_rows_from_starts(starts, texts, spacing_sec, buffer_sec):
    """Sustains each lyric until just before next start."""
    rows = []
    for i, s in enumerate(starts):
        if i < len(starts) - 1:
            e = max(s + 0.2, starts[i+1] - spacing_sec)
        else:
            e = s + 8.0 - buffer_sec
        rows.append((s, e, texts[i]))
    return rows

def write_ass(rows, ass_path, font_size, buffer_sec, spacing_sec, fade_in_ms, fade_out_ms):
    print(f"📝 Writing ASS: {ass_path}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header(font_size))
        for i, (start, end, text) in enumerate(rows):
            text = f"{{\\fad({fade_in_ms},{fade_out_ms})}}{text}"
            f.write(f"Dialogue: 0,{fmt_time_ass(start)},{fmt_time_ass(end)},Default,,0,0,0,,{text}\n")

def ensure_dir(path): os.makedirs(path, exist_ok=True)

def render_video(mp3_path, ass_path, prefix, out_dir, offset, autoplay, pause_script_path, do_pause):
    ensure_dir(out_dir)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    out_name = f"{prefix}{stamp}_{base}.mp4"
    out_path = os.path.join(out_dir, out_name)

    # ✅ Create black background video, overlay lyrics, and sync with audio
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-i", str(mp3_path),
        "-vf", f"ass={ass_path}",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_path)
    ], check=True)

    print(f"✅ Rendered: {out_path}")
