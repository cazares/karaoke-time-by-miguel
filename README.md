# 🎤 Karaoke Time  
*A lyric video generator by Miguel Cázares*

Karaoke Time is a Python + AppleScript toolkit that creates karaoke-style lyric videos with synchronized subtitles, smooth fade-outs, and optional instrumental separation.  
It’s designed for musicians, performers, and hobbyists who want to quickly generate professional-quality lyric videos from a simple CSV or plain text file.

---

## ✨ Features

### 🎵 Audio & Timing
- **Automatic lyric timing**
  - Tap-to-time mode for manual synchronization
  - Adjustable line spacing (`--lyric-block-spacing`)
  - Fade-out only (no fade-in) for clean transitions  
- **Offset correction** (`--offset`) for global sync tuning

### 🎨 Visual Output
- **Configurable subtitles**
  - Font size (`--font-size`)
  - Line spacing and fade duration  
- **High-quality render**
  - H.264 + AAC MP4 output via `ffmpeg`
  - Faststart enabled for instant web playback

### 🧠 Smart Automation
- **Lyric fetching** from Genius, LyricsFreak, or Lyrics.com (with retries)
- **Instrumental separation** powered by [Demucs](https://github.com/facebookresearch/demucs)
- **Automatic AppleScript integration (macOS)**
  - Pauses/mutes Music, Spotify, QuickTime, and Chrome `<video>/<audio>` tabs during render
  - Optionally autoplays result in QuickTime

### ⚙️ Developer Options
- `--debug` writes detailed logs (`lyrics_debug_*.log`)
- `--test-lyric-fetching` tests lyric sources without downloading or processing audio
- `--override-lyric-fetch-txt <file>` bypasses fetch logic and uses your local lyrics file
- `--no-prompt` runs everything automatically with zero manual steps

---

## 🚀 Quick Start

### 1️⃣ Environment setup
Run once — creates `demucs_env`, installs dependencies, and ensures everything is ready.

```bash
python3 karaoke_start.py
```

### 2️⃣ Generate Karaoke Video
Example full command:

```bash
python3 karaoke_generator.py   --artist "Vicente Fernandez"   --title "El Caballo de mi Padre"   --strip-vocals   --offset -1.75   --no-prompt   --autoplay
```

### 3️⃣ Manual Lyric Timing (if needed)
If auto-fetch fails or you want to customize timing:

```bash
python3 karaoke_core.py   --lyrics-txt songs/Vicente_Fernandez__El_Caballo_de_mi_Padre/lyrics/FINAL_Vicente_Fernandez_El_Caballo_de_mi_Padre.txt   --mp3 El_Caballo_de_mi_Padre_instrumental.mp3   --artist "Vicente Fernandez"   --title "El Caballo de mi Padre"   --offset -1.75   --no-prompt   --autoplay
```

---

## 📁 Project Structure

```
karaoke-time-by-miguel/
├── karaoke_start.py
├── karaoke_generator.py
├── karaoke_core.py
├── karaoke_time.py
├── karaoke_lyric_fetcher.py
├── pause_media.applescript
├── songs/
│   └── Artist__Title/
│       ├── lyrics/
│       │   ├── auto_*.txt
│       │   ├── FINAL_*.txt
│       │   └── lyrics_timing.csv
│       └── *_instrumental.mp3
└── output/
    └── *.mp4
```

---

## 🧩 Dependencies

Automatically installed via `karaoke_start.py`:

```
requests
soundfile
demucs
torch
torchaudio
ffmpeg-python
tqdm
yt-dlp
```

---

## 💡 Tips
- If you see JSON or “403 Forbidden” errors, try again with `--test-lyric-fetching` to isolate lyric sources.
- When `--no-prompt` is active, lyrics fetching will **still allow manual entry** if all sources fail.
- Reuse previous instrumentals to save time — don’t delete `_instrumental.mp3` unless you need to re-separate.

---

## 🧑‍💻 Author
**Miguel Cázares**  
[http://miguelengineer.com](http://miguelengineer.com)

---