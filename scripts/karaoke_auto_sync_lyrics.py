#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_auto_sync_lyrics.py — auto-sync lyrics to vocals using Demucs + Whisper
Part of 🎤 Karaoke Time by Miguel Cázares.

Steps:
  1. Separate vocals using Demucs
  2. Transcribe vocals with Whisper (JSON)
  3. Align Genius lyrics with timestamps (CSV output)

Includes:
  ✅ Live streaming + logging
  ✅ Smart caching (skip heavy steps if outputs exist)
  ✅ --clear-cache flag to force full reprocessing
  ✅ Auto Whisper output detection for cross-version compatibility
"""

import os, sys, subprocess, csv, re, datetime, shutil
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "karaoke_auto_sync_lyrics.log"

# -------------------------------------------------------------------------
# Helper: Stream live output and log it
# -------------------------------------------------------------------------
def run_with_progress(cmd, label=""):
    print(f"\n▶️ {label}: {' '.join(cmd)}\n")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n=== {label} started at {datetime.datetime.now()} ===\n")
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in process.stdout:
                sys.stdout.write(line)
                log.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {line}")
                log.flush()
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
        except Exception as e:
            log.write(f"❌ {label} failed: {e}\n")
            raise
        log.write(f"✅ {label} complete at {datetime.datetime.now()}\n")
        log.flush()
    print(f"✅ {label} complete.\n")

# -------------------------------------------------------------------------
# Step 0: Dependency check
# -------------------------------------------------------------------------
for tool in ["demucs", "whisper"]:
    if not shutil.which(tool):
        print(f"❌ Missing dependency: {tool}\n"
              f"→ Install it with:\n"
              f"   pip3 install {'openai-whisper' if tool=='whisper' else 'demucs'}\n")
        sys.exit(1)

# -------------------------------------------------------------------------
# Step 1: Vocal separation (Demucs)
# -------------------------------------------------------------------------
def separate_vocals(song_path: str, clear_cache: bool = False):
    stem_dir = Path("separated") / "htdemucs_ft" / Path(song_path).stem
    vocals_path = stem_dir / "vocals.wav"

    if vocals_path.exists() and not clear_cache:
        print(f"🌀 Using cached Demucs output → {vocals_path}")
        return vocals_path

    print(f"🎶 Step 1: Separating vocals with Demucs...")
    run_with_progress(["demucs", song_path, "-n", "htdemucs_ft"], "Demucs")

    if not vocals_path.exists():
        raise FileNotFoundError(f"❌ Expected vocals track not found: {vocals_path}")
    print(f"✅ Demucs output: {vocals_path}")
    return vocals_path

# -------------------------------------------------------------------------
# Step 2: Transcription (Whisper)
# -------------------------------------------------------------------------
def transcribe_with_whisper(vocals_path: Path, output_dir: Path, clear_cache: bool = False):
    expected_base = vocals_path.stem
    json_out_custom = output_dir / f"{expected_base}_whisper.json"
    json_out_default = output_dir / f"{expected_base}.json"

    # If existing transcript found, skip unless --clear-cache
    if (json_out_custom.exists() or json_out_default.exists()) and not clear_cache:
        found = json_out_custom if json_out_custom.exists() else json_out_default
        print(f"🌀 Using cached Whisper transcript → {found}")
        return found

    print(f"🧠 Step 2: Transcribing vocals with Whisper (medium model)...")
    cmd = [
        "whisper",
        str(vocals_path),
        "--model", "medium",
        "--language", "en",
        "--output_format", "json",
        "--output_dir", str(output_dir)
    ]
    run_with_progress(cmd, "Whisper")

    # Detect whichever Whisper filename convention was used
    if json_out_custom.exists():
        json_out = json_out_custom
    elif json_out_default.exists():
        json_out = json_out_default
    else:
        raise FileNotFoundError(
            f"❌ Whisper output not found: expected {json_out_custom} or {json_out_default}"
        )

    print(f"✅ Whisper JSON transcript: {json_out}")
    return json_out

# -------------------------------------------------------------------------
# Step 3: Rough alignment stub (placeholder)
# -------------------------------------------------------------------------
def align_lyrics_to_audio(lyrics_file: Path, json_file: Path, csv_out: Path):
    """
    Placeholder for alignment logic.
    For now, just creates CSV headers and line-per-lyric to mimic real sync format for karaoke_time.py.
    """
    print(f"🪄 Step 3: Aligning lyrics (stub implementation)...")
    with open(lyrics_file, "r", encoding="utf-8") as f:
        lyrics_lines = [l.strip() for l in f if l.strip()]
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "text"])
        t = 0.0
        for line in lyrics_lines:
            start = t
            end = t + 4.0  # placeholder timing
            writer.writerow([f"{start:.2f}", f"{end:.2f}", line])
            t = end
    print(f"✅ Lyrics aligned → {csv_out}")

# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto-sync lyrics to vocals using Demucs + Whisper")
    parser.add_argument("--artist", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--clear-cache", action="store_true", help="Force re-run Demucs & Whisper even if outputs exist")
    args = parser.parse_args()

    artist_slug = re.sub(r"[^A-Za-z0-9_]+", "_", args.artist.strip())
    title_slug = re.sub(r"[^A-Za-z0-9_]+", "_", args.title.strip())

    song_path = Path("songs") / f"{artist_slug}_{title_slug}.mp3"
    lyrics_path = Path("lyrics") / f"{artist_slug}_{title_slug}.txt"
    csv_out = Path("lyrics") / f"{artist_slug}_{title_slug}_synced.csv"

    print(f"\n🎤 Processing: {args.artist} — {args.title}")
    print(f"   Lyrics: {lyrics_path}")
    print(f"   Audio : {song_path}")
    print(f"   Cache : {'CLEAR' if args.clear_cache else 'use existing where possible'}")

    # 1. Demucs
    vocals_path = separate_vocals(str(song_path), clear_cache=args.clear_cache)

    # 2. Whisper
    json_out = transcribe_with_whisper(vocals_path, Path("lyrics"), clear_cache=args.clear_cache)

    # 3. Alignment stub
    align_lyrics_to_audio(lyrics_path, json_out, csv_out)

    print("\n✅ Auto-sync complete!")

# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()

# end of karaoke_auto_sync_lyrics.py
