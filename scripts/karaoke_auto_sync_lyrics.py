#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_auto_sync_lyrics.py
-----------------------------------
Auto-aligns lyrics and audio into a time-synced CSV for Karaoke Time.

Usage:
    python3 karaoke_auto_sync_lyrics.py --artist "John Frusciante" --title "The Past Recedes"
"""

import os, sys, argparse, subprocess, json, re
from pathlib import Path
from rapidfuzz import process, fuzz

def slugify(text: str) -> str:
    return text.lower().replace(" ", "_").replace("'", "").replace('"', '')

def run_with_progress(cmd: list[str], label: str):
    print(f"\n▶️ {label}: {' '.join(cmd)}\n")
    process_ = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pattern = re.compile(r'(\d{1,3}\.\d+)%|size=.*time=.*bitrate=')
    while True:
        line = process_.stdout.readline()
        if not line:
            break
        line = line.strip()
        if pattern.search(line):
            print(f"   {label}: {line}", flush=True)
    process_.wait()
    if process_.returncode != 0:
        raise subprocess.CalledProcessError(process_.returncode, cmd)
    print(f"✅ {label} complete.\n")

def separate_vocals(mp3_path: Path) -> Path:
    print("🎶 Step 1: Separating vocals with Demucs...")
    run_with_progress(["demucs", str(mp3_path), "-n", "htdemucs_ft"], "Demucs")
    vocals = Path("separated/htdemucs_ft") / mp3_path.stem / "vocals.wav"
    if not vocals.exists():
        vocals = Path("separated/htdemucs") / mp3_path.stem / "vocals.wav"
    if not vocals.exists():
        raise FileNotFoundError("❌ Vocals file not found after Demucs run.")
    return vocals

def transcribe_with_whisper(vocals_path: Path, json_out: Path):
    print("🧠 Step 2: Transcribing vocals with Whisper (medium model)...")
    cmd = [
        "whisper", str(vocals_path),
        "--model", "medium",
        "--language", "en",
        "--output_format", "json",
        "--output_dir", str(json_out.parent)
    ]
    run_with_progress(cmd, "Whisper")
    generated = json_out.parent / f"{vocals_path.stem}.json"
    if not generated.exists():
        raise FileNotFoundError("❌ Whisper output JSON not found.")
    generated.rename(json_out)
    return json_out

def align_lyrics_to_transcript(lyrics_txt: Path, transcript_json: Path, csv_out: Path):
    print("🪄 Step 3: Aligning lyrics to Whisper transcript...")
    with open(lyrics_txt, "r", encoding="utf-8") as f:
        lyrics_lines = [line.strip() for line in f if line.strip()]
    with open(transcript_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments", data)

    rows = []
    for line in lyrics_lines:
        best = process.extractOne(line, [s["text"] for s in segments], scorer=fuzz.partial_ratio)
        if best:
            seg = next(s for s in segments if s["text"] == best[0])
            start = seg.get("start", 0)
            end = seg.get("end", start + 2)
            rows.append((start, end, line))
        else:
            rows.append(("", "", line))

    with open(csv_out, "w", encoding="utf-8") as f:
        for start, end, text in rows:
            f.write(f"{start},{end},{text}\n")

    print(f"✅ Synced CSV written to: {csv_out}")
    return csv_out

def main():
    parser = argparse.ArgumentParser(description="Auto-sync lyrics and audio for Karaoke Time")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    artist_slug = slugify(args.artist)
    title_slug = slugify(args.title)
    base = f"{artist_slug}_{title_slug}"

    lyrics_txt = Path("lyrics") / f"{base}.txt"
    mp3_path = Path("songs") / f"{base}.mp3"
    json_out = Path("lyrics") / f"{base}_transcript.json"
    csv_out = Path("lyrics") / f"{base}_synced.csv"

    if not lyrics_txt.exists():
        print(f"❌ Lyrics file not found: {lyrics_txt}")
        sys.exit(1)
    if not mp3_path.exists():
        print(f"❌ MP3 file not found: {mp3_path}")
        sys.exit(1)

    print(f"\n🎤 Processing: {args.artist} — {args.title}")
    print(f"   Lyrics: {lyrics_txt}")
    print(f"   Audio : {mp3_path}")

    vocals_path = separate_vocals(mp3_path)
    transcript_json = transcribe_with_whisper(vocals_path, json_out)
    align_lyrics_to_transcript(lyrics_txt, transcript_json, csv_out)

    print("\n🎯 Next step:")
    print(f"python3 karaoke_time.py --csv \"{csv_out}\" --mp3 \"{mp3_path}\" --autoplay")

if __name__ == "__main__":
    main()

# end of karaoke_auto_sync_lyrics.py
