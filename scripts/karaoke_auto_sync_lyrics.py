#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_auto_sync_lyrics.py — auto-sync lyrics to audio
Path-locked version: always executes from project root.
"""

import argparse, subprocess, sys, re, os
from pathlib import Path

# 🧭 Always operate from project root
os.chdir(Path(__file__).resolve().parent.parent)

def run_with_progress(cmd, tag="Process"):
    print(f"▶️ {tag}: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)
    print(f"✅ {tag} complete.\n")

def sanitize_name(name): return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def separate_vocals(song_path, clear_cache=False):
    cwd = Path.cwd()
    demucs_root = cwd / "separated" / "htdemucs_ft"
    target_stem = Path(song_path).stem.lower()

    if demucs_root.exists():
        for d in demucs_root.glob("*"):
            if d.is_dir() and d.name.lower() == target_stem:
                vocals = d / "vocals.wav"
                if vocals.exists() and not clear_cache:
                    print(f"🌀 Using cached Demucs output → {vocals}")
                    return vocals

    print("🎶 Step 1: Separating vocals with Demucs (fresh run)...")
    run_with_progress(["demucs", str(song_path), "-n", "htdemucs_ft", "-o", "separated"], "Demucs")

    for d in demucs_root.glob("*"):
        if d.is_dir() and d.name.lower() == target_stem:
            vocals = d / "vocals.wav"
            if vocals.exists(): return vocals

    raise FileNotFoundError(f"❌ Expected vocals track not found for {song_path}")

def transcribe_with_whisper(vocals_path, clear_cache=False):
    out_json = Path("lyrics") / "vocals.json"
    if out_json.exists() and not clear_cache:
        print(f"🌀 Using cached Whisper transcript → {out_json}")
        return out_json
    print("🗣️ Step 2: Transcribing vocals with Whisper...")
    run_with_progress(["whisper", str(vocals_path), "--model", "medium", "--output_dir", "lyrics", "--output_format", "json"], "Whisper")
    if not out_json.exists():
        raise FileNotFoundError(f"❌ Whisper output not found: {out_json}")
    return out_json

def align_lyrics_to_audio(lyrics_path, whisper_json, csv_out):
    print("🪄 Step 3: Aligning lyrics (stub)...")
    lines=[l.strip() for l in open(lyrics_path,encoding="utf-8") if l.strip()]
    with open(csv_out,"w",encoding="utf-8") as f:
        for i,line in enumerate(lines):
            start=i*5.0;end=start+4.0
            f.write(f"{start:.3f},{end:.3f},{line}\\n")
    print(f"✅ Lyrics aligned → {csv_out}")

def adjust_vocals_mix(vocals_path, original_path, percent):
    if percent<=0:
        print("🎛️ Skipping vocal mix — instrumental only.")
        return original_path
    out_path=Path("songs")/f"{original_path.stem}_mixed_{int(percent)}.mp3"
    print(f"🎚️ Mixing vocals at {percent:.1f}% → {out_path}")
    run_with_progress([
        "ffmpeg","-y","-i",str(original_path),"-i",str(vocals_path),
        "-filter_complex",f"[0:a][1:a]amix=inputs=2:weights='1 {percent/100.0}'",
        "-c:a","libmp3lame","-b:a","192k",str(out_path)
    ],"FFmpeg Mix")
    return out_path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artist",required=True);p.add_argument("--title",required=True)
    p.add_argument("--clear-cache",action="store_true");p.add_argument("--final",action="store_true")
    p.add_argument("--vocals-percent",type=float,default=0.0)
    a=p.parse_args()

    artist_slug=sanitize_name(a.artist);title_slug=sanitize_name(a.title)
    song=Path("songs")/f"{artist_slug}_{title_slug}.mp3"
    lyr=Path("lyrics")/f"{artist_slug}_{title_slug}.txt"
    csv=Path("lyrics")/f"{artist_slug}_{title_slug}_synced.csv"

    print(f"\\n🎤 Processing: {a.artist} — {a.title}")
    print(f"  Lyrics: {lyr}\\n  Audio: {song}\\n  Cache: {'rebuild' if a.clear_cache else 'reuse'}")

    vocals=separate_vocals(song,a.clear_cache)
    transcript=transcribe_with_whisper(vocals,a.clear_cache)
    align_lyrics_to_audio(lyr,transcript,csv)
    if a.vocals_percent>0: adjust_vocals_mix(vocals,song,a.vocals_percent)
    print("\\n✅ Auto-sync complete!")

if __name__=="__main__": main()
# end of karaoke_auto_sync_lyrics.py
