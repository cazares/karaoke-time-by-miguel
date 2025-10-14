#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_auto_sync_lyrics.py
-----------------------------------
Bridges fetched lyrics and MP3 into a time-aligned CSV file for Karaoke Time.

Usage:
    python3 karaoke_auto_sync_lyrics.py --artist "John Frusciante" --title "The Past Recedes"

Expected paths:
    lyrics/john_frusciante_the_past_recedes.txt
    songs/john_frusciante_the_past_recedes.mp3

Output:
    lyrics/john_frusciante_the_past_recedes_synced.csv
"""

import os, sys, argparse, subprocess, json
from pathlib import Path
from rapidfuzz import process, fuzz

# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------

def slugify(text: str) -> str:
    return text.lower().replace(" ", "_").replace("'", "").replace('"', '')

def run(cmd: str):
    print(f"\n▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=True)

# ------------------------------------------------------------
# Core processing
# ------------------------------------------------------------

def separate_vocals(mp3_path: Path) -> Path:
    """Run Demucs and return path to vocals.wav"""
    print("🎶 Separating vocals with Demucs...")
    run(f'demucs "{mp3_path}" -n htdemucs_ft')
    vocals = Path("separated/htdemucs_ft") / mp3_path.stem / "vocals.wav"
    if not vocals.exists():
        # fallback to generic folder name
        vocals = Path("separated/htdemucs") / mp3_path.stem / "vocals.wav"
    if not vocals.exists():
        raise FileNotFoundError("❌ Vocals file not found after Demucs run.")
    return vocals

def transcribe_with_whisper(vocals_path: Path, json_out: Path):
    """Run Whisper transcription and save JSON output"""
    print("🧠 Transcribing vocals with Whisper...")
    run(f'whisper "{vocals_path}" --model medium --language en --output_format json --output_dir "{json_out.parent}"')
    generated = json_out.parent / f"{vocals_path.stem}.json"
    if not generated.exists():
        raise FileNotFoundError("❌ Whisper output JSON not found.")
    generated.rename(json_out)
    return json_out

def align_lyrics_to_transcript(lyrics_txt: Path, transcript_json: Path, csv_out: Path):
    """Align Whisper transcript to known lyrics using RapidFuzz"""
    print("🪄 Aligning lyrics to Whisper transcript...")

    # Load lyrics
    with open(lyrics_txt, "r", encoding="utf-8") as f:
        lyrics_lines = [line.strip() for line in f if line.strip()]

    # Load Whisper transcript
    with open(transcript_json, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
    segments = transcript_data.get("segments", transcript_data)  # support both whisper & whisperx JSON formats

    # Build aligned CSV
    rows = []
    for line in lyrics_lines:
        best = process.extractOne(
            line, [seg["text"] for seg in segments],
            scorer=fuzz.partial_ratio
        )
        if best:
            matched_text = best[0]
            matched_seg = next(s for s in segments if s["text"] == matched_text)
            start = matched_seg.get("start", 0)
            end = matched_seg.get("end", start + 2)
            rows.append((start, end, line))
        else:
            rows.append(("", "", line))

    # Write CSV
    with open(csv_out, "w", encoding="utf-8") as f:
        for start, end, text in rows:
            f.write(f"{start},{end},{text}\n")

    print(f"✅ Synced CSV written to: {csv_out}")
    return csv_out

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

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

    vocals_path = separate_vocals(mp3_path)
    transcript_json = transcribe_with_whisper(vocals_path, json_out)
    align_lyrics_to_transcript(lyrics_txt, transcript_json, csv_out)

    print("\n🎯 Next step:")
    print(f"python3 karaoke_time.py --csv \"{csv_out}\" --mp3 \"{mp3_path}\" --autoplay")

if __name__ == "__main__":
    main()

# end of karaoke_auto_sync_lyrics.py
