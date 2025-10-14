#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_auto_sync_lyrics.py — auto-sync lyrics using Demucs + Whisper
Optimized for iterative runs, with caching, clear-cache, and final mode.
"""

import os, sys, subprocess, csv, re, datetime, shutil
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "karaoke_auto_sync_lyrics.log"

def run_with_progress(cmd, label=""):
    print(f"\n▶️ {label}: {' '.join(cmd)}\n")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {line}")
            log.flush()
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
    print(f"✅ {label} complete.\n")

def separate_vocals(song_path: str, clear_cache=False, final=False):
    model = "htdemucs_ft" if not final else "hdemucs_mmi"
    stem_dir = Path("separated") / model / Path(song_path).stem
    vocals_path = stem_dir / "vocals.wav"
    if not clear_cache and vocals_path.exists():
        print(f"🌀 Using cached Demucs output → {vocals_path}")
        return vocals_path
    run_with_progress(["demucs", song_path, "-n", model], "Demucs")
    if not vocals_path.exists():
        raise FileNotFoundError(f"❌ Expected vocals track not found: {vocals_path}")
    return vocals_path

def transcribe_with_whisper(vocals_path: Path, output_dir: Path, clear_cache=False, final=False):
    json_out = output_dir / f"{vocals_path.stem}_whisper.json"
    if not clear_cache and json_out.exists():
        print(f"🌀 Using cached Whisper transcript → {json_out}")
        return json_out
    model = "medium" if not final else "large"
    cmd = ["whisper", str(vocals_path), "--model", model, "--language", "en",
           "--output_format", "json", "--output_dir", str(output_dir)]
    run_with_progress(cmd, "Whisper")
    if not json_out.exists():
        raise FileNotFoundError(f"❌ Whisper output not found: {json_out}")
    return json_out

def align_lyrics_to_audio(lyrics_file: Path, json_file: Path, csv_out: Path):
    with open(lyrics_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "text"])
        t = 0.0
        for line in lines:
            writer.writerow([f"{t:.2f}", f"{t+4.0:.2f}", line])
            t += 4.0
    print(f"✅ Lyrics aligned → {csv_out}")

def mix_vocals(vocals_path: Path, percent: float):
    if percent <= 0:
        return None
    base_dir = vocals_path.parent
    full_mix = base_dir / "mixed.wav"
    print(f"🎚 Mixing vocals at {percent:.1f}% volume…")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(base_dir / "no_vocals.wav"),
        "-i", str(vocals_path),
        "-filter_complex",
        f"[1:a]volume={percent/100:.2f}[v];[0:a][v]amix=inputs=2:normalize=0[out]",
        "-map", "[out]", str(full_mix)
    ])
    print(f"✅ Mixed track saved to {full_mix}")
    return full_mix

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto-sync lyrics with Demucs + Whisper")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--clear-cache", action="store_true")
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--vocals-percent", type=float, default=0.0)
    args = parser.parse_args()

    artist_slug = re.sub(r"[^A-Za-z0-9_]+", "_", args.artist.strip())
    title_slug = re.sub(r"[^A-Za-z0-9_]+", "_", args.title.strip())
    song_path = Path("songs") / f"{artist_slug}_{title_slug}.mp3"
    lyrics_path = Path("lyrics") / f"{artist_slug}_{title_slug}.txt"
    csv_out = Path("lyrics") / f"{artist_slug}_{title_slug}_synced.csv"

    print(f"\n🎤 Processing: {args.artist} — {args.title}")
    vocals_path = separate_vocals(str(song_path), args.clear_cache, args.final)
    json_out = transcribe_with_whisper(vocals_path, Path("lyrics"), args.clear_cache, args.final)
    align_lyrics_to_audio(lyrics_path, json_out, csv_out)
    mix_vocals(vocals_path, args.vocals_percent)
    print("\n✅ Auto-sync complete!")

if __name__ == "__main__":
    main()

# end of karaoke_auto_sync_lyrics.py
