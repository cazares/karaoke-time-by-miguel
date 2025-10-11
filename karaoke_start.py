#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_start.py — fully automated bootstrap & restart-safe launcher
Creates or resets 'demucs_env', installs dependencies, purges caches,
and runs karaoke_generator.py. User never has to manage environments.
"""

import os, sys, subprocess, shutil, time

VENV_DIR = "demucs_env"
REQUIREMENTS = "requirements.txt"
CACHE_DIRS = [
    "__pycache__",
    "*/__pycache__",
    "songs/__pycache__",
    "demucs_env/lib/python3.13/site-packages/__pycache__"
]

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
yt-dlp
""")
    print(f"✅ Requirements file ready: {REQUIREMENTS}")

def purge_pycache():
    print("🧹 Clearing stale Python caches...")
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            full = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(full)
                print(f"  🗑️  Removed: {full}")
            except Exception:
                pass
    print("✅ Caches cleared.\n")

def rebuild_env():
    # 🧹 Remove old environment safely
    if os.path.isdir(VENV_DIR):
        print(f"🧹 Removing old virtual environment: {VENV_DIR}")
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    # 🧱 Create a fresh environment
    print(f"🧱 Creating fresh virtual environment: {VENV_DIR}")
    run([sys.executable, "-m", "venv", VENV_DIR])

    pip_exe = os.path.join(VENV_DIR, "bin", "pip")
    print("📦 Installing dependencies...")
    run([pip_exe, "install", "-U", "pip", "wheel", "setuptools"])
    run([pip_exe, "install", "-r", REQUIREMENTS])

def main():
    # ☕ Step 1: Clean up caches first
    purge_pycache()

    # Detect if we’re inside the venv we want to rebuild
    inside_venv = (
        sys.prefix != sys.base_prefix and
        os.path.basename(sys.prefix) == VENV_DIR
    )

    if inside_venv:
        print("⚠️ Detected you’re running inside the environment being rebuilt.")
        print("🔄 Relaunching from system Python…\n")

        envless_python = "/usr/bin/python3" if os.path.exists("/usr/bin/python3") else "python3"
        cmd = [envless_python, __file__] + sys.argv[1:]
        os.execvp(cmd[0], cmd)
        return

    # Normal flow: outside venv, full setup
    ensure_requirements()
    rebuild_env()

    py_exe = os.path.join(VENV_DIR, "bin", "python")

    if len(sys.argv) > 1:
        print("\n🎶 Running karaoke_generator.py with your arguments…\n")
        run([py_exe, "karaoke_generator.py"] + sys.argv[1:])
    else:
        print(f"\n✅ Environment ready!")
        print(f"Run manually:\n   python3 karaoke_start.py \"your_song.mp3\" --artist \"Artist\" --title \"Song Title\" --strip-vocals")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {e}")
        sys.exit(1)
