#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎤 Karaoke Time by Miguel Cázares — Named Args Edition

Changes in this version:
- Uses explicit named args for inputs: --csv, --ass, --mp3
- Adds --fade-in (seconds) and --fade-out (seconds); keeps --fade-out-ms for backward compatibility
- Resolves paths via os.path.abspath so you never need "$(pwd)"
- Adds --output-dir (default: output) and ensures it exists
- Keeps all previous behavior (spacing logic, autoplay, AppleScript pause, etc.)

LKG (example):
    python3 karaoke_time_namedargs.py \      --csv lyrics/lyrics_2025-10-07_2126.csv \      --ass lyrics/lyrics_2025-10-07_2126.ass \      --mp3 lyrics/song.mp3 \      --font-size 155 --lyric-block-spacing 0.8 --offset 1.0 \      --fade-in 0.3 --fade-out 0.8 --autoplay
"""

import argparse, csv, os, subprocess, platform, tempfile
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description="Karaoke Time lyric video generator (named-args)")

    # Explicit input paths
    p.add_argument("--csv", required=True, help="CSV file path (timings + lyrics)")
    p.add_argument("--ass", required=True, help="ASS subtitle file path (will be (re)written)")
    p.add_argument("--mp3", required=True, help="Instrumental MP3 audio file path")

    # Visual + timing
    p.add_argument("--font-size", type=int, default=52, help="Subtitle font size (pt)")
    p.add_argument("--buffer", type=float, default=0.5, help="Final line only: trim this many seconds from end")
    p.add_argument("--lyric-block-spacing", type=float, default=0.8,
                   help="End time = next start − spacing (s); last line uses --buffer")

    # Fades
    p.add_argument("--fade-in", type=float, default=0.0, help="Fade-in duration in seconds (default: 0.0)")
    p.add_argument("--fade-out", type=float, default=None,
                   help="Fade-out duration in seconds (default: None; falls back to --fade-out-ms if not set)")
    p.add_argument("--fade-out-ms", type=int, default=300,
                   help="(Backward-compat) Fade-out length in ms; ignored if --fade-out is provided")

    # Output
    p.add_argument("--output-prefix", default="non_interactive_", help="Output filename prefix")
    p.add_argument("--output-dir", default="output", help="Directory to place the generated .mp4 (default: output)")

    # Audio sync
    p.add_argument("--offset", type=float, default=0.0, help="Global audio offset (sec)")

    # macOS niceties
    p.add_argument("--pause-script", default="pause_media.applescript",
                   help="AppleScript file to pause/mute other media apps (macOS)")
    p.add_argument("--autoplay", action="store_true", help="Automatically open the generated MP4 after creation")

    return p.parse_args()


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


def fmt_time(s: float) -> str:
    if s < 0:
        s = 0
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def load_csv(path: str):
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            if len(row) == 2:
                # "MM:SS","text"
                try:
                    mm, ss = row[0].split(":")
                    start = float(mm) * 60 + float(ss)
                    end = start + 3.0
                    text = row[1].strip().replace("\\n", "\n")
                    rows.append((start, end, text))
                except:
                    pass
            elif len(row) >= 3:
                # "start","end","text"
                try:
                    start = float(row[0].strip())
                    end   = float(row[1].strip())
                    text  = row[2].strip().replace("\\n", "\n")
                    rows.append((start, end, text))
                except:
                    pass
    return rows


def write_ass(rows, ass_path, font_size, buffer_sec, spacing_sec, fade_in_ms, fade_out_ms):
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
            adjusted_end = max(adjusted_end, start + MIN_VISIBLE)

            # \fad(in_ms, out_ms)
            txt = "{\\fad(" + str(max(0, int(fade_in_ms))) + "," + str(max(0, int(fade_out_ms))) + ")}" + text
            f.write(f"Dialogue: 0,{fmt_time(start)},{fmt_time(adjusted_end)},Default,,0,0,0,,{txt}\n")


def run_pause_script(pause_script_path: str):
    if platform.system() != "Darwin":
        return
    if not os.path.isfile(pause_script_path):
        print(f"ℹ️ pause script not found: {pause_script_path} (skipping)")
        return
    subprocess.run(["osascript", pause_script_path], check=False)


def open_video_mac(path_to_mp4: str):
    """Open MP4 in QuickTime Player, bring to front & play; fallback to Preview; finally reveal in Finder."""
    if platform.system() != "Darwin":
        return

    path_to_mp4 = os.path.abspath(path_to_mp4)
    applescript = f'''
set theFile to POSIX file "{path_to_mp4}"

on playWithQuickTime(theFile)
    tell application "QuickTime Player"
        activate
        open theFile
        -- wait up to ~2s for a document to appear
        repeat 20 times
            if (count of documents) > 0 then exit repeat
            delay 0.1
        end repeat
        try
            play document 1
        end try
    end tell
end playWithQuickTime

try
    my playWithQuickTime(theFile)
on error errMsg number errNum
    -- Fallback to Preview if QT fails
    tell application "Preview"
        activate
        open theFile
    end tell
end try
'''
    # run the script from a temp file (avoids shell quoting issues)
    try:
        with tempfile.NamedTemporaryFile('w', suffix='.applescript', delete=False) as f:
            f.write(applescript)
            script_path = f.name
        subprocess.run(["osascript", script_path], check=False)
    finally:
        try:
            os.unlink(script_path)
        except Exception:
            pass

    # Last-resort: reveal in Finder if neither app comes to front
    subprocess.run(["open", "-R", path_to_mp4], check=False)


def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def generate_video(mp3_path, ass_path, prefix, out_dir, offset, autoplay, pause_script_path):
    mp3_path = os.path.abspath(mp3_path)
    ass_path = os.path.abspath(ass_path)
    out_dir = os.path.abspath(out_dir)
    ensure_dir(out_dir)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    out_name = f"{prefix}{stamp}_{base}.mp4"
    out_path = os.path.join(out_dir, out_name)

    print("\n🎬 Generating final video:", out_path)
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
        out_path
    ]
    subprocess.run(cmd, check=True)

    # Pause/mute others (AFTER render, BEFORE opening)
    run_pause_script(pause_script_path)

    # Autoplay if requested
    if autoplay:
        open_video_mac(out_path)

    # Reveal folder & open the new file (macOS nicety)
    if platform.system() == "Darwin":
        subprocess.run(["open", out_dir], check=False)
        if not autoplay:
            subprocess.run(["open", "-a", "QuickTime Player", out_path], check=False)
    else:
        # cross-platform best-effort
        try:
            if os.name == "nt":
                os.startfile(out_path)  # type: ignore
            else:
                subprocess.run(["xdg-open", out_path], check=False)
        except Exception:
            pass

    print(f"\n✅ Done! Output saved as {out_path}")


def main():
    a = parse_args()

    # Resolve to absolute paths so $(pwd) is never required
    csv_path = os.path.abspath(a.csv)
    ass_path = os.path.abspath(a.ass)
    mp3_path = os.path.abspath(a.mp3)

    # Parse CSV
    rows = load_csv(csv_path)

    print("\nCSV Preview (first 10 rows):")
    print("Start      End        Text")
    print("--------------------------------------------------")
    for s, e, t in rows[:10]:
        print(f"{s:<10.2f} {e:<10.2f} {t}")

    # Fade handling (seconds -> ms); --fade-out seconds wins over --fade-out-ms if provided
    fade_in_ms = int(max(0.0, float(a.fade_in)) * 1000)
    if a.fade_out is not None:
        fade_out_ms = int(max(0.0, float(a.fade_out)) * 1000)
    else:
        fade_out_ms = int(max(0, int(a.fade_out_ms)))

    # Write ASS
    write_ass(
        rows,
        ass_path,
        a.font_size,
        a.buffer,
        a.lyric_block_spacing,
        fade_in_ms,
        fade_out_ms
    )

    # Generate video
    generate_video(
        mp3_path=mp3_path,
        ass_path=ass_path,
        prefix=a.output_prefix,
        out_dir=a.output_dir,
        offset=a.offset,
        autoplay=a.autoplay,
        pause_script_path=a.pause_script
    )


if __name__ == "__main__":
    main()
