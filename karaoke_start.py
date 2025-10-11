#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_karaoke_env.py — automatic bootstrap + optional karaoke generation
Creates 'demucs_env', installs dependencies, verifies setup,
and optionally runs karaoke_generator.py on a given song.
"""

import os, sys, subprocess

VENV_DIR = "demucs_env"
REQUIREMENTS = "requirements.txt"

def run(cmd, **kwargs):
    print("▶️", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)

def ensure_requirements():
    if not os.path.exists(REQUIREMENTS):
        print(f"⚠️ {REQUIREMENTS} not found, creating default one.")
        with open(REQUIREMENTS, "w") as f:
            f.write("""requests
soundfile
demucs
torch
torchaudio
ffmpeg-python
tqdm
""")
    print(f"✅ Requirements file ready: {REQUIREMENTS}")

def main():
    ensure_requirements()

    # 1️⃣ Create virtual environment if missing
    if not os.path.isdir(VENV_DIR):
        print(f"🧱 Creating virtual environment: {VENV_DIR}")
        run([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(f"✅ Virtual environment already exists: {VENV_DIR}")

    pip_exe = os.path.join(VENV_DIR, "bin", "pip")
    py_exe = os.path.join(VENV_DIR, "bin", "python")

    # 2️⃣ Install dependencies
    print("📦 Installing dependencies...")
    run([pip_exe, "install", "-U", "pip", "wheel", "setuptools"])
    run([pip_exe, "install", "-r", REQUIREMENTS])

    # 3️⃣ Verify core imports
    print("🔍 Verifying key imports...")
    run([py_exe, "-c", "import requests, demucs, soundfile, torch; print('✅ All imports OK!')"])

    # 4️⃣ If user passed args, run karaoke_generator immediately
    if len(sys.argv) > 1:
        print("\n🎶 Running karaoke_generator.py with your arguments…\n")
        run([py_exe, "karaoke_generator.py"] + sys.argv[1:])
    else:
        print(f"\n🎉 Setup complete!")
        print(f"To use it manually:\n   source {VENV_DIR}/bin/activate && python3 karaoke_generator.py \"your_song.mp3\" --artist \"Artist\" --title \"Song Title\" --strip-vocals")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {e}")
        sys.exit(1)
