#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — single entrypoint (interactive + non-interactive)
"""
import argparse, os, sys
from karaoke_core import (FONT_SIZE, SPACING, OFFSET, FADE_IN, FADE_OUT, BUFFER_SEC, OUTPUT_DIR, MP3_DEFAULT,
                          load_csv_any, load_lyrics_txt, tap_collect_times, compute_rows_from_starts,
                          write_ass, render_video, fmt_time_mmss)

def parse():
    p = argparse.ArgumentParser(description="Karaoke Time — defaults + tap-to-time")
    p.add_argument("--csv", help="Input CSV: 'time,lyric' or 'start,end,text'")
    p.add_argument("--lyrics-txt", help="Plain text lyrics (one block per line)")
    p.add_argument("--ass", help="ASS output path (optional)")
    p.add_argument("--mp3", default=MP3_DEFAULT)
    p.add_argument("--font-size", type=int, default=FONT_SIZE)
    p.add_argument("--lyric-block-spacing", type=float, default=SPACING)
    p.add_argument("--offset", type=float, default=OFFSET)
    p.add_argument("--fade-in", type=float, default=FADE_IN)
    p.add_argument("--fade-out", type=float, default=FADE_OUT)
    p.add_argument("--buffer", type=float, default=BUFFER_SEC)
    p.add_argument("--output-prefix", help='Defaults: "interactive_" or "non_interactive_"')
    p.add_argument("--output-dir", default=OUTPUT_DIR)
    p.add_argument("--no-pause", action="store_true")
    p.add_argument("--no-autoplay", action="store_true")
    p.add_argument("--count-in", type=float, default=0.0)
    p.add_argument("--export-starts-csv", help="Tap mode only: output starts-only CSV")
    a = p.parse_args()
    if bool(a.csv) == bool(a.lyrics_txt):
        p.error("Provide exactly one of --csv or --lyrics-txt")
    if a.output_prefix is None:
        a.output_prefix = "interactive_" if a.lyrics_txt else "non_interactive_"
    if a.ass is None:
        base = os.path.splitext(a.lyrics_txt or a.csv)[0]
        a.ass = base + ".ass"
    if a.lyrics_txt and not a.export_starts_csv:
        a.export_starts_csv = os.path.splitext(a.lyrics_txt)[0] + ".csv"
    return a

def main():
    a = parse()
    autoplay, do_pause = not a.no_autoplay, not a.no_pause

    if a.lyrics_txt:
        texts = load_lyrics_txt(a.lyrics_txt)
        starts = tap_collect_times(texts, a.count_in)

        lines = ["time,lyric"]
        for s, t in zip(starts, texts):
            escaped = t.replace("\n", "\\N")
            lines.append(f"{fmt_time_mmss(s)},{escaped}")

        with open(a.export_starts_csv, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("📝 Saved:", a.export_starts_csv)

        rows = compute_rows_from_starts(starts, texts, a.lyric_block_spacing, a.buffer)
        write_ass(
            rows, a.ass, a.font_size, a.buffer, a.lyric_block_spacing,
            int(a.fade_in * 1000), int(a.fade_out * 1000)
        )
        render_video(
            a.mp3, a.ass, a.output_prefix, a.output_dir, a.offset,
            autoplay, "pause_media.applescript", do_pause
        )
        return

    # Non-interactive CSV mode
    rows = load_csv_any(a.csv)
    print("🎶 CSV Preview (first 5 rows):")
    for s, e, t in rows[:5]:
        print(f"{s:.2f}-{e:.2f}: {t}")

    write_ass(
        rows, a.ass, a.font_size, a.buffer, a.lyric_block_spacing,
        int(a.fade_in * 1000), int(a.fade_out * 1000)
    )
    render_video(
        a.mp3, a.ass, a.output_prefix, a.output_dir, a.offset,
        autoplay, "pause_media.applescript", do_pause
    )

if __name__ == "__main__":
    main()
