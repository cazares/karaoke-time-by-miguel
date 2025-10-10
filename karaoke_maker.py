#!/usr/bin/env python3
"""
🎤 Karaoke Maker by Miguel Cázares
---------------------------------
Creates an instrumental (no vocals) MP3 from any song using Demucs.
Requires: python3 -m pip install demucs ffmpeg-python
"""

import os, sys, subprocess, shutil
from pathlib import Path

# === Helpers ===
def run(cmd, check=True):
    print("▶️", " ".join(cmd))
    subprocess.run(cmd, check=check)

def ensure_demucs():
    try:
        subprocess.run(["demucs", "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Demucs found.")
    except FileNotFoundError:
        print("⬇️ Installing Demucs (this may take a few minutes)...")
        run([sys.executable, "-m", "pip", "install", "-U", "demucs", "soundfile"])

# === Main ===
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 karaoke_maker.py <song.mp3>")
        sys.exit(1)

    song = Path(sys.argv[1]).expanduser().resolve()
    if not song.exists():
        sys.exit(f"❌ File not found: {song}")

    ensure_demucs()

    print(f"🎶 Separating vocals from: {song.name}")
    run(["demucs", str(song)])

    # Find output directory (Demucs standard path)
    sep_dir = Path("separated/htdemucs") / song.stem
    if not sep_dir.exists():
        sys.exit("❌ Could not find Demucs output folder. Something went wrong.")

    print(f"✅ Stems created in: {sep_dir}")

    # Define expected stems
    stems = {
        "drums": sep_dir / "drums.wav",
        "bass": sep_dir / "bass.wav",
        "other": sep_dir / "other.wav",
    }
    for name, f in stems.items():
        if not f.exists():
            sys.exit(f"❌ Missing stem: {f}")

    output_file = song.with_name(f"{song.stem}_instrumental.mp3")

    print("🎧 Combining non-vocal stems into one instrumental track...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(stems["drums"]),
        "-i", str(stems["bass"]),
        "-i", str(stems["other"]),
        "-filter_complex",
        "amix=inputs=3:normalize=1,alimiter=limit=0.9",
        "-qscale:a", "2",
        str(output_file)
    ]
    run(ffmpeg_cmd)

    print(f"✅ Instrumental created: {output_file}")
    print("💡 Tip: You can delete the 'separated/' folder to reclaim space.")

if __name__ == "__main__":
    main()
