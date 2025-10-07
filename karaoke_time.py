#!/usr/bin/env python3
"""
🎤 Karaoke Time by Miguel
Created by Miguel Cazares — https://miguelengineer.com
"""
import os, sys, csv, time, glob, datetime, subprocess, re

def c(t, clr):
    d={"red":"\033[91m","green":"\033[92m","yellow":"\033[93m","blue":"\033[94m",
       "magenta":"\033[95m","cyan":"\033[96m","white":"\033[97m","reset":"\033[0m"}
    return f"{d.get(clr,'')}{t}{d['reset']}"
def log(m,clr="cyan",e="💬"): print(f"{e} {c(m,clr)}")

def parse_blocks(txt):
    with open(txt, "r", encoding="utf-8") as f:
        raw = f.read().replace("\r\n", "\n").strip()

    lines = raw.split("\n")
    blocks, current = [], []

    for line in lines:
        if line.strip().startswith("[") and line.strip().endswith("]") and current:
            # New section marker → start new block
            blocks.append("\n".join(current).strip())
            current = [line]
        elif line.strip() == "" and current:
            # Double newline: separate
            blocks.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current).strip())

    return [b.replace("\n", "\\N") for b in blocks]

def log_timestamps(txt, csvf):
    blocks = parse_blocks(txt)
    log(f"📄 Loaded {len(blocks)} lyric blocks from: {txt}", "magenta")
    log("🕐 Timer started! Waiting for first ENTER…", "cyan")
    start = time.time()
    ts = []

    for i, b in enumerate(blocks):
        pretty = b.replace("\\N", "\n")
        print(c("────────────────────────────────────────────", "blue"))
        log(f"[{i+1}/{len(blocks)}] Ready for:\n{pretty[:300]}", "white", "🎵")
        print(c("────────────────────────────────────────────", "blue"))

        ui = input("> ").strip().lower()
        if ui == "q":
            log("🟥 Quit early.", "red")
            break
        elif ui == "u" and ts:
            r = ts.pop()
            log(f"↩️ Undid {r[0]} | {r[1][:50]}", "red")
            continue

        t = time.time() - start
        tstr = time.strftime("%M:%S.%02d", time.gmtime(t))
        ts.append((tstr, b))
        pretty_block = b.replace("\\N", "\n")
        log(f"✅ Captured at {tstr} for lyric:\n{pretty_block}", "green")

    with open(csvf, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "lyric"])
        w.writerows(ts)
    log(f"💾 Saved {len(ts)} timestamps → {csvf}", "green")

def csv_to_ass(csvf, assf):
    head = """[Script Info]
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
    p = 0.0
    with open(csvf, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            s = row["time"]
            parts = s.split(":")
            try:
                ss = float(parts[0]) * 60 + float(parts[1])
            except:
                ss = p + 3.0
            e = ss + 3.0
            s_str = time.strftime("%H:%M:%S.00", time.gmtime(ss))
            e_str = time.strftime("%H:%M:%S.00", time.gmtime(e))
            txt = row["lyric"].replace("\\N", "\\N")
            lines.append(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{txt}")
            p = ss
    with open(assf, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines))
    log(f"📝 Wrote {len(lines)} cues → {assf}", "green")

def ass_to_mp4(mp3, assf, mp4):
    if not os.path.exists(mp3):
        log(f"❌ MP3 not found: {mp3}", "red")
        return
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-i", mp3,
        "-vf", f"subtitles='{assf}':fontsdir='.'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", mp4
    ]
    log("🎬 Running ffmpeg…", "magenta")
    subprocess.run(cmd)
    log(f"✅ Generated {mp4}", "green")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_time.py [lyrics.txt] [--release]")
        sys.exit(1)
    txt = sys.argv[1]
    release = "--release" in sys.argv
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
    csv_to_ass(csvf, assf)
    ass_to_mp4(mp3, assf, mp4f)
    log(f"🏁 Done! Files in {out}", "green")

if __name__ == "__main__":
    main()
