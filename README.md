# 🎤 Karaoke Time  
*A lyric video generator by Miguel Cázares*

Karaoke Time is a Python + AppleScript tool that creates karaoke-style lyric videos with synchronized subtitles, audio, and smooth fade-outs.  

It’s designed for musicians, performers, and hobbyists who want to quickly generate professional-looking lyric videos from a simple CSV file.

---

## ✨ Features
- **Automatic lyric timing**  
  - Adjustable line spacing (`--lyric-block-spacing`)  
  - Fade-out only (no fade-in) with minimum visibility safeguards  
- **Configurable appearance**  
  - Subtitle font size (`--font-size`)  
  - Global audio offset correction (`--offset`)  
- **High-quality video output**  
  - Generates H.264 + AAC MP4 via `ffmpeg`  
  - Faststart enabled for web streaming  
- **Smart integrations (macOS)**  
  - Pauses/mutes Apple Music, Spotify, QuickTime, and Chrome `<video>/<audio>` tabs during render  
  - Optionally **autoplays the result** in QuickTime (fallback to Preview → Finder)  
- **Cross-platform support**  
  - Works on macOS, Linux, and Windows (autoplay is macOS-specific)  

---

## 📂 File Structure
```
karaoke-time/
├── karaoke_time.py           # Main Python script
├── pause_media.applescript   # Helper script (pauses/mutes other media apps on macOS)
├── lyrics/                   # Place your .csv, .ass, and .mp3 files here
└── output/                   # Generated .mp4 files
```

---

## 🚀 Quick Start

### 1. Install dependencies
- Python 3.8+  
- [ffmpeg](https://ffmpeg.org/download.html) installed and available in `$PATH`  
- macOS only: enable  
  **Chrome > View > Developer > ✔ Allow JavaScript from Apple Events**  
  (required for Chrome tab muting)

### 2. Run the generator
```bash
python3 karaoke_time.py lyrics/lyrics.csv lyrics/lyrics.ass lyrics/song.mp3
```

### 3. Recommended example
```bash
python3 karaoke_time.py "$(pwd)/lyrics/lyrics_2025-10-07_2126.csv" "$(pwd)/lyrics/lyrics_2025-10-07_2126.ass" "$(pwd)/lyrics/song.mp3" --font-size 155 --lyric-block-spacing 0.8 --offset 1.0 --autoplay
```

---

## ⚙️ Command-Line Options
| Flag | Description | Default |
|------|-------------|---------|
| `--font-size <int>` | Subtitle font size | `52` |
| `--lyric-block-spacing <sec>` | Time gap before next lyric | `0.8` |
| `--buffer <sec>` | Trim from last line’s end | `0.5` |
| `--fade-out-ms <ms>` | Fade-out duration | `300` |
| `--offset <sec>` | Global audio offset | `0.0` |
| `--output-prefix <str>` | Output file prefix | `non_interactive_` |
| `--pause-script <file>` | AppleScript to pause other media | `pause_media.applescript` |
| `--autoplay` | Autoplay the final MP4 (macOS only) | `false` |

---

## 📝 Example Workflow
1. Create a `lyrics.csv` with start/end times + lyric text.  
2. Provide an `.ass` subtitle file (can be regenerated from CSV).  
3. Place your `song.mp3` in the `lyrics/` folder.  
4. Run the script with desired options.  
5. Enjoy your synchronized karaoke video in QuickTime! 🎶  

---

## 📸 Example Output
*(Replace this with an actual screenshot or GIF preview)*  
![Example Screenshot](docs/example.png)

---

## 👨‍💻 Author
Created by **Miguel Cázares**  
[Website](https://miguelengineer.com) · [GitHub](https://github.com/mcazares) · [LinkedIn](https://linkedin.com/in/miguelcazares)

---

## 📄 License
MIT License © 2025 Miguel Cázares  
