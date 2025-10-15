#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_auto_sync_lyrics.py
Fully automated lyric sync:
- Demucs separates stems
- Whisper transcribes vocals with timestamps
- Filters out [Music]/[Applause]/noise
- Converts to timestamped CSV
- Mixes vocals and renders karaoke video automatically
"""

import os, sys, subprocess, argparse, json, csv, re
from pathlib import Path

# ---------- utilities ----------

def run_with_progress(cmd, desc=None):
    display_cmd = " ".join(cmd)
    if desc:
        print(f"▶️ {desc}: {display_cmd}")
    process = subprocess.run(cmd, text=True)
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, display_cmd)

# ---------- helpers ----------

def find_stems_folder(base_dir, artist, title):
    song_key = f"{artist.lower().replace(' ','_')}_{title.lower().replace(' ','_')}"
    candidates = [
        Path(base_dir) / "separated" / "htdemucs_ft" / song_key,
        Path(base_dir) / "scripts" / "separated" / "htdemucs_ft" / song_key,
    ]
    for c in candidates:
        if (c / "vocals.wav").exists():
            return c
    return candidates[0]

def adjust_vocals_mix(vocals_path, original_path, percent):
    out_path = Path(original_path).with_name(
        Path(original_path).stem + f"_mixed_{int(percent)}.mp3"
    )
    print(f"🎚️ Mixing vocals at {percent:.1f}% → {out_path}")
    run_with_progress([
        "ffmpeg", "-y",
        "-i", str(original_path),
        "-i", str(vocals_path),
        "-filter_complex", f"[0:a][1:a]amix=inputs=2:weights='1 {percent/100.0}'",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_path)
    ], "FFmpeg Mix")
    return out_path

def extract_timestamps_from_whisper(json_path, csv_path):
    print(f"🪄 Extracting timestamps from {json_path} → {csv_path}")
    with open(json_path, "r") as f:
        data = json.load(f)

    filtered_segments = []
    for seg in data.get("segments", []):
        text = seg.get("text", "").strip()
        if not text:
            continue
        # Skip non-lyric or noise segments
        if re.match(r"^\[.*\]$", text):
            continue
        if any(kw in text.lower() for kw in ["[music]", "[applause]", "[silence]", "(music)", "(applause)"]):
            continue
        filtered_segments.append((seg["start"], text))

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "text"])
        for start_time, text in filtered_segments:
            writer.writerow([f"{start_time:.2f}", text])

    print(f"✅ Wrote {len(filtered_segments)} lyric lines to {csv_path}")

# ---------- main ----------

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--artist", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--vocals-percent", type=float, default=30.0)
    args = a.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    print(f"🎤 Processing: {args.artist} — {args.title}")

    lyrics_path = project_root / f"lyrics/{args.artist.replace(' ','_')}_{args.title.replace(' ','_')}.txt"
    audio_path  = project_root / f"songs/{args.artist.replace(' ','_')}_{args.title.replace(' ','_')}.mp3"

    stems_folder = find_stems_folder(project_root, args.artist, args.title)
    vocals = stems_folder / "vocals.wav"
    if not vocals.exists():
        print("🎶 Step 1: Separating vocals with Demucs (fresh run)...")
        run_with_progress([
            "demucs", str(audio_path), "-n", "htdemucs_ft", "-o", "separated"
        ], "Demucs")
    else:
        print(f"🌀 Using cached Demucs output → {vocals}")

    transcript_json = project_root / "lyrics/vocals.json"
    if not transcript_json.exists():
        print("🎧 Step 2: Transcribing vocals with Whisper...")
        run_with_progress([
            "whisper", str(vocals), "--model", "medium",
            "--output_dir", "lyrics", "--output_format", "json"
        ], "Whisper")
    else:
        print(f"🌀 Using cached Whisper transcript → {transcript_json}")

    # Step 3 — Convert Whisper JSON → synced CSV (filtered)
    synced_csv = project_root / f"lyrics/{args.artist.replace(' ','_')}_{args.title.replace(' ','_')}_synced.csv"
    extract_timestamps_from_whisper(transcript_json, synced_csv)

    # Step 4 — Mix vocals into instrumental
    mixed_mp3 = adjust_vocals_mix(vocals, audio_path, args.vocals_percent)

    # Step 5 — Generate karaoke MP4
    print("🎬 Rendering final karaoke video...")
    run_with_progress([
        "python3",
        str(project_root / "scripts/karaoke_core.py"),
        "--csv", str(synced_csv),
        "--mp3", str(audio_path),
        "--font-size", "140"
    ], "Karaoke Render")

    print("✅ Auto-sync complete! 🎉")

if __name__ == "__main__":
    main()

# end of karaoke_auto_sync_lyrics.py