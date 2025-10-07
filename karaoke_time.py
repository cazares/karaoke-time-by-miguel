#!/usr/bin/env python3
"""
🎤 Karaoke Time by Miguel
Created by Miguel Cazares — https://miguelengineer.com

Turns any .txt lyric file into a full karaoke video (.mp4) with timestamps.
"""

import os, sys, csv, time, glob, datetime, subprocess

# === CONFIG ===
FFMPEG_BIN = "ffmpeg"
VIDEO_SIZE = "1920x1080"
FRAME_RATE = 30
AUDIO_BITRATE = "192k"
VIDEO_PRESET = "veryfast"
CRF = 18

# === COLOR HELPERS ===
def c(text, color):  # basic ANSI coloring
    colors = {
        "red": "\033[91m", "green": "\033[92m",
        "yellow": "\033[93m", "blue": "\033[94m",
        "magenta": "\033[95m", "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def log(msg, color="cyan", emoji="💬"):
    print(f"{emoji} {c(msg, color)}")

# === STAGE 1: TIMESTAMP LOGGER ===
def log_timestamps(txtfile, csvfile):
    log(f"Loading lyrics from {txtfile}", "magenta", "📄")
    with open(txtfile, "r", encoding="utf-8") as f:
        raw = [line.strip() for line in f.read().splitlines()]

    # Split into lyric blocks (ignore empty lines)
    blocks, block = [], []
    for line in raw:
        if not line:
            if block:
                blocks.append("\\N".join(block))
                block = []
        else:
            block.append(line)
    if block:
        blocks.append("\\N".join(block))

    log(f"Loaded {len(blocks)} lyric blocks", "green", "🎶")

    timestamps = []
    log("▶ Press ENTER each time a new lyric block begins. 'u'+ENTER = undo | 'q'+ENTER = save & quit", "yellow", "🕐")
    start = time.time()

    for i, block in enumerate(blocks):
        log(f"[{i+1}/{len(blocks)}] Ready for: {block[:70]}...", "blue", "🎵")
        user_input = input("> ").strip().lower()

        if user_input == "q":
            log("Quit early.", "red", "🟥")
            break
        elif user_input == "u" and timestamps:
            removed = timestamps.pop()
            log(f"Undid last timestamp: {removed[0]} | {removed[1][:60]}", "red", "↩️")
            continue

        ts = time.time() - start
        tstr = time.strftime("%M:%S.%02d", time.gmtime(ts))
        timestamps.append((tstr, block))
        pretty_block = block.replace("\\N", " / ")
        log(f"Captured at {tstr} for lyric:\n   {pretty_block}", "green", "✅")

    with open(csvfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "lyric"])
        writer.writerows(timestamps)
    log(f"Saved {len(timestamps)} timestamps → {csvfile}", "green", "💾")

# === STAGE 2: CSV → ASS ===
def csv_to_ass(csvfile, assfile):
    header = """[Script Info]
Title: Karaoke by Miguel
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Alignment, MarginL, MarginR, MarginV
Style: Default,Helvetica,48,&H00FFFFFF,&H00000000,0,0,2,50,50,70

[Events]
Format: Layer, Start, End, Style, Text
"""
    lines = []
    with open(csvfile, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prev_t = 0.0
        for row in reader:
            start = row["time"]
            try:
                parts = start.split(":")
                start_s = float(parts[0]) * 60 + float(parts[1])
            except:
                start_s = prev_t + 3.0
            end_s = start_s + 3.0
            start_str = time.strftime("%H:%M:%S.00", time.gmtime(start_s))
            end_str = time.strftime("%H:%M:%S.00", time.gmtime(end_s))
            text = row["lyric"].replace("\\N", "\\N")
            lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")
            prev_t = start_s

    with open(assfile, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines))
    log(f"Wrote {len(lines)} cues → {assfile}", "green", "📝")

# === STAGE 3: ASS → MP4 ===
def ass_to_mp4(mp3file, assfile, mp4file):
    if not os.path.exists(mp3file):
        log(f"❌ MP3 not found: {mp3file}", "red")
        return
    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={VIDEO_SIZE}:r={FRAME_RATE}",
        "-i", mp3file,
        "-vf", f"subtitles='{assfile}':fontsdir='.'",
        "-c:v", "libx264", "-preset", VIDEO_PRESET, "-crf", str(CRF),
        "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-movflags", "+faststart", "-shortest",
        mp4file
    ]
    log("Running ffmpeg…", "magenta", "🎬")
    subprocess.run(cmd)
    log(f"Generated {mp4file}", "green", "✅")

# === MAIN ===
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_time.py [lyrics.txt] [--release]")
        sys.exit(1)

    txtfile = sys.argv[1]
    release = "--release" in sys.argv

    base_name = os.path.splitext(os.path.basename(txtfile))[0]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    outdir = os.path.join(os.getcwd(), base_name)
    os.makedirs(outdir, exist_ok=True)

    csvfile = os.path.join(outdir, f"{base_name}_{timestamp}.csv")
    assfile = os.path.join(outdir, f"{base_name}_{timestamp}.ass")
    mp4file = os.path.join(outdir, f"{base_name}_{timestamp}.mp4")

    mp3_candidates = sorted(glob.glob(os.path.join(outdir, "*.mp3")), key=os.path.getmtime, reverse=True)
    mp3file = mp3_candidates[0] if mp3_candidates else None

    if not mp3file:
        log("No MP3 found in output directory.", "yellow", "⚠️")
        choice = input("Enter path to your .mp3 file (or press ENTER to open Finder): ").strip()
        if not choice:
            subprocess.run(["open", outdir])
            print("Drop your MP3 in that folder and press ENTER when ready.")
            input()
            mp3_candidates = sorted(glob.glob(os.path.join(outdir, "*.mp3")), key=os.path.getmtime, reverse=True)
            if mp3_candidates:
                mp3file = mp3_candidates[0]
        else:
            mp3file = choice

    if not mp3file:
        log("❌ No MP3 found. Exiting.", "red")
        sys.exit(1)

    log_timestamps(txtfile, csvfile)
    csv_to_ass(csvfile, assfile)
    ass_to_mp4(mp3file, assfile, mp4file)

    log(f"🎉 Done! Files are in {outdir}", "green", "🏁")

if __name__ == "__main__":
    main()

