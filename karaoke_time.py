#!/usr/bin/env python3
"""
🎤 Karaoke Time by Miguel
Created by Miguel Cazares — https://miguelengineer.com
"""
import os, sys, csv, time, glob, datetime, subprocess, tempfile, shutil

# 🎨 Colors + logging helper
def c(t, clr):
    d = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
        "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
        "white": "\033[97m", "reset": "\033[0m"
    }
    return f"{d.get(clr, '')}{t}{d['reset']}"

def log(m, clr="cyan", e="💬"):
    print(f"{e} {c(m, clr)}")

# 🧠 DUMB PARSER — each non-blank line is a lyric block
def parse_blocks(txt):
    with open(txt, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip().replace("\\N", "\\N") for line in lines if line.strip()]

# 🕐 Step 1: Interactive timestamp logger
def log_timestamps(txt, csvf):
    blocks = parse_blocks(txt)
    log(f"📄 Loaded {len(blocks)} lyric lines from: {txt}", "magenta")
    input(c("🎬 Ready to begin! Press ENTER when the music starts playing to start timer...", "yellow"))
    start = time.time()
    log("🕐 Timer started! 0.5s sync buffer before first lyric...", "cyan")
    time.sleep(0.5)

    ts = []
    for i, b in enumerate(blocks):
        os.system("clear")
        pretty = b.replace("\\N", "\n")
        divider = c("────────────────────────────────────────────", "blue")

        print(divider)
        log(f"[{i+1}/{len(blocks)}] Ready for:", "white", "🎵")
        print(divider)
        print(pretty)
        print(divider)

        ui = input(c("[Press Enter to Sync @ Current Song Time] > ", "cyan")).strip().lower()

        if ui == "q":
            log("🟥 Quit early.", "red")
            break
        elif ui == "u" and ts:
            r = ts.pop()
            log(f"↩️ Undid {r[0]} | {r[1][:50]}", "red")
            continue

        t = time.time() - start
        tstr = f"{int(t//60):02}:{t%60:05.2f}"
        ts.append((tstr, b))
        log(f"✅ Captured at {tstr} for lyric:\n{pretty}", "green")

    with open(csvf, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "lyric"])
        w.writerows(ts)
    log(f"💾 Saved {len(ts)} timestamps → {csvf}", "green")

# 🧩 Step 2: CSV → ASS subtitles (instant show, fade-out only)
def csv_to_ass(csvf, assf, offset_sec=0.0):
    head = """[Script Info]
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
    lines = []
    times = []

    # Read all timestamps into memory first
    with open(csvf, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            parts = row["time"].split(":")
            try:
                ss = float(parts[0]) * 60 + float(parts[1]) + offset_sec
            except:
                ss = (times[-1][0] if times else 0) + 3.0 + offset_sec
            times.append((ss, row["lyric"]))

    # Generate ASS lines with hold-until-next logic (minus 1s)
    for i, (ss, lyric) in enumerate(times):
        next_start = times[i + 1][0] if i + 1 < len(times) else ss + 3.0
        e = max(next_start - 1.0, ss + 1.0)  # ensure at least 1s visible
        s_str = time.strftime("%H:%M:%S.00", time.gmtime(ss))
        e_str = time.strftime("%H:%M:%S.00", time.gmtime(e))
        txt = "{\\fad(0,300)}" + lyric.replace("\\N", "\\N")
        lines.append(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{txt}")

    with open(assf, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines))
    log(f"📝 Wrote {len(lines)} cues → {assf}", "green")

# 🎬 Step 3: Generate MP4 via ffmpeg
def ass_to_mp4(mp3, assf, mp4):
    if not os.path.exists(mp3):
        log(f"❌ MP3 not found: {mp3}", "red")
        return
    tmpdir = tempfile.mkdtemp(prefix="karaoke_")
    safe_ass = os.path.join(tmpdir, os.path.basename(assf).replace("'", "_").replace(" ", "_"))
    shutil.copy(assf, safe_ass)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-i", mp3,
        "-vf", f"subtitles={safe_ass}:fontsdir='.'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", mp4
    ]
    log("🎬 Running ffmpeg…", "magenta")
    subprocess.run(cmd)
    log(f"✅ Generated {mp4}", "green")
    shutil.rmtree(tmpdir, ignore_errors=True)

# 🚀 Orchestrator
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_time.py [lyrics.txt] [--offset N]")
        sys.exit(1)

    txt = sys.argv[1]
    offset = 0.0
    if "--offset" in sys.argv:
        try:
            offset = float(sys.argv[sys.argv.index("--offset") + 1])
        except Exception:
            log("⚠️ Invalid offset; using 0s.", "yellow")

    base = os.path.splitext(os.path.basename(txt))[0]
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    out = os.path.join(os.getcwd(), base)
    os.makedirs(out, exist_ok=True)

    csvf = os.path.join(out, f"{base}_{stamp}.csv")
    assf = os.path.join(out, f"{base}_{stamp}.ass")
    mp4f = os.path.join(out, f"{base}_{stamp}.mp4")

    mp3s = sorted(glob.glob(os.path.join(out, "*.mp3")), key=os.path.getmtime, reverse=True)
    mp3 = mp3s[0] if mp3s else None

    if not mp3:
        log("⚠️ No MP3 found. Drop it in folder & press ENTER.", "yellow")
        subprocess.run(["open", out])
        input()
        mp3s = sorted(glob.glob(os.path.join(out, "*.mp3")), key=os.path.getmtime, reverse=True)
        if mp3s:
            mp3 = mp3s[0]

    if not mp3:
        log("❌ No MP3 found. Exiting.", "red")
        sys.exit(1)

    log_timestamps(txt, csvf)
    csv_to_ass(csvf, assf, offset)
    ass_to_mp4(mp3, assf, mp4f)
    log(f"🏁 Done! Files in {out}", "green")

if __name__ == "__main__":
    main()
