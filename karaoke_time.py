#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
🎤 Karaoke Time — robust edition (CSV: time,lyric → ASS → MP4)

- Handles \N safely (raw strings everywhere).
- Validates CSV headers before proceeding.
- Normalizes times (MM:SS.xx or seconds).
- Uses temp copy of ASS for ffmpeg to avoid quoting bugs.
"""

import os, sys, csv, time, datetime, subprocess, tempfile, shutil

def log(msg): print(msg)

# ---------- CSV → ASS ----------
def csv_to_ass(csvf, assf, hold_gap=0.5):
    head = r"""[Script Info]
Title: Karaoke by Miguel
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Helvetica,56,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,1,0,5,50,50,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    times = []
    with open(csvf, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not {"time","lyric"}.issubset(reader.fieldnames or []):
            raise RuntimeError(f"CSV must have headers 'time,lyric'. Got: {reader.fieldnames}")
        for row in reader:
            t = (row.get("time") or "").strip()
            lyr = (row.get("lyric") or "").strip()
            if not t or not lyr: continue
            try:
                parts = t.split(":")
                if len(parts) == 2:
                    mm = float(parts[0]); ss = float(parts[1])
                    start_s = mm*60 + ss
                else:
                    start_s = float(t)
            except Exception:
                start_s = times[-1][0] + 3.0 if times else 0.0
            times.append((start_s, lyr))

    if not times:
        raise RuntimeError("No valid rows in CSV")

    def fmt(v):
        h = int(v // 3600)
        m = int((v % 3600) // 60)
        s = v % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    lines = []
    for i, (ss, lyric) in enumerate(times):
        next_start = times[i+1][0] if i+1 < len(times) else ss + 3.0
        e = max(next_start - hold_gap, ss + 0.30)
        txt = r"{\fad(0,300)}" + lyric.replace(r"\N", r"\N")
        lines.append(f"Dialogue: 0,{fmt(ss)},{fmt(e)},Default,,0,0,0,,{txt}")

    with open(assf, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines))
    log(f"📝 Wrote {len(lines)} cues → {assf}")

# ---------- ASS+MP3 → MP4 ----------
def ass_to_mp4(mp3, assf, mp4):
    if not os.path.exists(mp3): raise FileNotFoundError(f"MP3 not found: {mp3}")
    if not os.path.exists(assf): raise FileNotFoundError(f"ASS not found: {assf}")

    tmpdir = tempfile.mkdtemp(prefix="karaoke_")
    safe_ass = os.path.join(tmpdir, os.path.basename(assf).replace("'", "_"))
    shutil.copy(assf, safe_ass)

    cmd = [
        "ffmpeg","-y",
        "-f","lavfi","-i","color=c=black:s=1920x1080:r=30",
        "-i", mp3,
        "-vf", f"subtitles='{safe_ass}':charenc=UTF-8",
        "-c:v","libx264","-preset","veryfast","-crf","18",
        "-c:a","aac","-b:a","192k",
        "-movflags","+faststart","-shortest", mp4
    ]
    log("🎬 Running ffmpeg…")
    subprocess.run(cmd, check=True)
    log(f"✅ Generated {mp4}")
    shutil.rmtree(tmpdir, ignore_errors=True)

# ---------- main ----------
def main():
    if len(sys.argv) != 4:
        print("Usage: python3 karaoke_time.py <csv_path> <ass_path> <mp3_path>")
        sys.exit(1)

    csvf, assf, mp3f = map(os.path.abspath, sys.argv[1:4])
    csv_to_ass(csvf, assf, hold_gap=0.5)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    mp4f = os.path.join(os.getcwd(), f"non_interactive_{stamp}_{os.path.splitext(os.path.basename(mp3f))[0]}.mp4")

    ass_to_mp4(mp3f, assf, mp4f)
    log("🏁 Done.")

if __name__ == "__main__":
    main()
