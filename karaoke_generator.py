#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_generator.py — fully automated Karaoke pipeline 🎤
Author: Miguel Cázares
Version: 3.0
----------------------------------------------------------
Usage Examples:
  python3 karaoke_generator.py god_lyrics.txt --offset 1.0
  python3 karaoke_generator.py god_lyrics.txt --offset 1.0 --strip-vocals

Flow:
1️⃣ Optionally strips vocals from the main MP3 using Demucs
2️⃣ Captures lyric timings interactively
3️⃣ Automatically finds the correct CSV/ASS outputs
4️⃣ Generates the karaoke video with the instrumental
5️⃣ Opens Finder on completion
"""

import subprocess, sys, time, os, datetime
from pathlib import Path

# ------------------------------------------------------
def run(cmd):
    print("\n▶️", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)

def find_mp3s(base_name):
    parent = Path(base_name).parent
    stem = Path(base_name).stem.replace("_lyrics", "").replace("-lyrics", "")
    all_mp3s = list(parent.glob("*.mp3"))
    orig = inst = None
    for f in all_mp3s:
        lower = f.name.lower()
        if stem in lower and "instrumental" not in lower and "karaoke" not in lower:
            orig = f
        if stem in lower and ("instrumental" in lower or "karaoke" in lower):
            inst = f
    return orig, inst

def latest_matching_file(pattern, stem):
    matches = [f for f in Path(".").rglob(pattern) if stem in f.name]
    if not matches:
        return None
    return max(matches, key=lambda f: f.stat().st_mtime)

# ------------------------------------------------------
def auto_strip_vocals(original_mp3, stem):
    """Use Demucs to strip vocals and build a true instrumental mix."""
    print(f"🎛️  Stripping vocals from {original_mp3.name} using Demucs...")
    try:
        subprocess.run(["demucs", str(original_mp3)], check=True)
    except FileNotFoundError:
        sys.exit("❌ Demucs not installed. Run: python3 -m pip install demucs")

    sep_dir = Path("separated/htdemucs") / stem
    instr_out = original_mp3.with_name(f"{stem}_instrumental.mp3")

    parts = []
    for name in ("drums", "bass", "other"):
        f = sep_dir / f"{name}.wav"
        if f.exists():
            parts.append(f)
    if not parts:
        sys.exit("❌ No instrumental stems found in separated folder.")

    print("🎚️  Combining stems (drums + bass + other)...")
    cmd = ["ffmpeg", "-y"]
    for p in parts:
        cmd += ["-i", str(p)]
    cmd += ["-filter_complex", f"amix=inputs={len(parts)}:normalize=0", str(instr_out)]
    subprocess.run(cmd, check=True)
    print(f"✅  Created: {instr_out}")
    return instr_out

# ------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_generator.py lyrics.txt [--offset 1.0] [--strip-vocals]")
        sys.exit(1)

    # Parse basic args
    lyrics_txt = Path(sys.argv[1]).resolve()
    opts = sys.argv[2:]
    strip_vocals = "--strip-vocals" in opts
    opts = [o for o in opts if o != "--strip-vocals"]

    mp3_args = [a for a in opts if a.lower().endswith(".mp3")]
    non_mp3_opts = [a for a in opts if not a.lower().endswith(".mp3")]

    # Locate MP3s
    if len(mp3_args) == 2:
        original_mp3 = Path(mp3_args[0]).resolve()
        instr_mp3 = Path(mp3_args[1]).resolve()
    else:
        original_mp3, instr_mp3 = find_mp3s(lyrics_txt)
        if not original_mp3:
            sys.exit("❌ Could not find original MP3 (e.g. god.mp3).")

        if not instr_mp3 and strip_vocals:
            instr_mp3 = auto_strip_vocals(original_mp3, original_mp3.stem)
        elif not instr_mp3:
            sys.exit("❌ No instrumental found. Try again with --strip-vocals.")

    stem = Path(lyrics_txt).stem.replace("_lyrics", "").replace("-lyrics", "")

    print("🎤  Phase 1: Capture lyric timings\n")
    run(["python3", "karaoke_time.py", "--lyrics-txt", str(lyrics_txt),
         "--mp3", str(original_mp3)] + non_mp3_opts)

    print("\n⏳  Waiting for timing CSV/ASS to appear...")
    csv_path = latest_matching_file("*.csv", stem)
    ass_path = latest_matching_file("*.ass", stem)

    if not csv_path or not ass_path:
        print("⚠️  No timing files found — searching for recent ones...")
        all_csvs = sorted(Path(".").rglob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if all_csvs:
            csv_path = all_csvs[0]
            ass_path = csv_path.with_suffix(".ass")
            print(f"🕵️  Using latest CSV: {csv_path.name}")
        else:
            ans = input("\n⚠️  No timing CSV found — redo tap phase? (Y/n): ").strip().lower()
            if ans in ("y", ""):
                return main()
            else:
                print("🚫  Skipping re-tap phase.")
                return

    print(f"\n🎬  Phase 2: Generate karaoke video using {instr_mp3.name}\n")
    run(["python3", "karaoke_time.py", "--csv", str(csv_path),
         "--ass", str(ass_path), "--mp3", str(instr_mp3)] + non_mp3_opts)

    print(f"\n✅  Done! Output video synced to: {instr_mp3.stem}")
    os.system("open .")

# ------------------------------------------------------
if __name__ == "__main__":
    main()
