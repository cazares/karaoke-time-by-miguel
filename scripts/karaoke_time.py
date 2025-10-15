#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — render final MP4 from (timestamp,text) CSV + MP3.
Minimal, surgical fixes:
 - Auto-handle header (timestamp,text) or none
 - Title card (compact if first <2s; spacious otherwise)
 - Centered text (Alignment=5), WrapStyle=2
 - Reliable time conversion; end = next_start - 0.10s
 - ✅ Apply --offset to all lyric timestamps and title card
 - ✅ NEW: Optional --max-seconds for debug preview
 - ✅ NEW: Optional --debug-lyrics to preview loaded text before render
"""

import argparse, csv, re, subprocess, sys, tempfile
from pathlib import Path


def ass_time_from_seconds(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec - h * 3600 - m * 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def parse_timestamp(ts: str) -> float:
    ts = ts.strip()
    if re.match(r"^\d+(\.\d+)?$", ts):
        return float(ts)
    parts = re.split(r"[:]", ts)
    parts = [p.strip() for p in parts]
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        try:
            return float(ts)
        except:
            return 0.0


def read_rows(csv_path: Path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        sample = f.readline()
        f.seek(0)
        first_cell = sample.split(",")[0].strip().strip('"')
        has_header = not re.match(r"^\d+(\.\d+)?$", first_cell)

        if has_header:
            rdr = csv.DictReader(f)
            for r in rdr:
                ts = parse_timestamp(r.get("timestamp", "0"))
                text = (r.get("text", "") or "").strip()
                rows.append({"t": ts, "text": text})
        else:
            rdr = csv.reader(f)
            for row in rdr:
                if len(row) < 2:
                    continue
                ts = parse_timestamp(row[0])
                text = row[1].strip()
                rows.append({"t": ts, "text": text})

    rows = [r for r in rows if r["text"] != ""]
    rows.sort(key=lambda x: x["t"])
    return rows


def build_ass(rows, artist: str, title: str, font_size: int, offset: float, max_seconds: float) -> str:
    # Apply offset
    for r in rows:
        r["t"] = r["t"] + offset

    # Clip for debugging
    if max_seconds > 0:
        rows = [r for r in rows if r["t"] <= max_seconds]

    first_start = rows[0]["t"] if rows else 0.0
    if first_start < 2.0 and rows:
        title_text = f"{title}\\Nby\\N{artist}\\N\\N{rows[0]['text']}"
        skip_first = True
    else:
        title_text = f"{title}\\N\\Nby\\N\\N{artist}"
        skip_first = False

    header = (
        "[Script Info]\n"
        "Title: Karaoke\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1280\nPlayResY: 720\n"
        "ScaledBorderAndShadow: yes\n"
        "\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,5,30,30,40,1\n"
        "\n[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events = []
    tc_start = 0.0 + offset
    tc_end = max(2.5 + offset, first_start)
    events.append((ass_time_from_seconds(tc_start), ass_time_from_seconds(tc_end - 0.05), title_text))

    for i, r in enumerate(rows):
        if skip_first and i == 0:
            continue
        start = r["t"]
        if i + 1 < len(rows):
            next_start = rows[i + 1]["t"]
            end = max(start + 0.10, next_start - 0.10)
        else:
            end = start + 3.0
        if max_seconds > 0 and start > max_seconds:
            break
        events.append((ass_time_from_seconds(start), ass_time_from_seconds(end), r["text"].replace("\r", "").replace("\n", "\\N")))

    body_lines = [f"Dialogue: 0,{st},{et},Default,,0,0,0,,{txt}" for (st, et, txt) in events]
    return header + "\n".join(body_lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Render karaoke MP4 from (timestamp,text) CSV + MP3")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--mp3", required=True)
    ap.add_argument("--artist", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--font-size", type=int, default=140)
    ap.add_argument("--max-seconds", type=float, default=0.0)
    ap.add_argument("--debug-lyrics", action="store_true")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    mp3_path = Path(args.mp3)
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    suffix = "_preview" if args.max_seconds > 0 else ""
    out_path = out_dir / f"{mp3_path.stem}{suffix}_karaoke.mp4"

    rows = read_rows(csv_path)
    if not rows:
        print("❌ No lyric rows found after reading CSV.")
        sys.exit(1)

    if args.debug_lyrics:
        print(f"\n🩵 DEBUG LYRICS (first 10 from {csv_path.name}):")
        for r in rows[:10]:
            print(f"  {r['t']:>7.2f}s | {r['text']}")
        print("...")

    ass_txt = build_ass(rows, args.artist, args.title, args.font_size, args.offset, args.max_seconds)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ass", mode="w", encoding="utf-8") as tf:
        tf.write(ass_txt)
        ass_path = tf.name

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:size=1280x720",
        "-i", str(mp3_path),
        "-vf", f"subtitles={ass_path}:force_style='WrapStyle=2,Alignment=5,FontSize={args.font_size}'",
        "-shortest",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path)
    ]
    print("▶️", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"✅ Render complete! Saved to {out_path}")


if __name__ == "__main__":
    main()

# end of karaoke_time.py
