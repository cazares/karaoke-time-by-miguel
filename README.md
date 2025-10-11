# 🎤 Karaoke Time v3.3  
*Automated lyric fetching, editing & video creation by Miguel Cázares*

Karaoke Time v3.3 takes your favorite songs and turns them into fully timed lyric videos — automatically fetching lyrics, letting you edit them, and generating high-quality karaoke videos with minimal effort.  

---

## ✨ Features
- **One-Command Automation**  
  Fetches lyrics, prompts you to edit line breaks, then times and renders the video automatically.  
- **Optional Vocal Removal**  
  Use `--strip-vocals` to generate an instrumental version via Demucs before timing.  
- **Fully Hands-Free Render**  
  From fetch → edit → timing → video creation with no extra setup.  
- **Smart File Organization**  
  Each song is stored under `songs/Artist__Title/` with subfolders for audio, lyrics, output, and logs.  
- **macOS Integration**  
  Automatically uses AppleScript for pausing other media apps while rendering.  

---

## 🚀 Quick Start
1. 🎧 Place your song MP3 anywhere and run:  
   ```bash
   python3 karaoke_generator.py "path/to/song.mp3"
   ```

2. ✏️ Wait for lyrics to be fetched automatically.  
   Then edit the generated `FINAL_Artist__Title.txt` to insert `\N` line breaks, save, and press **Enter** when prompted.

3. 🎬 Sit back — the script handles timing, rendering, and video generation automatically.

### Optional Instrumental Mode
```bash
python3 karaoke_generator.py "path/to/song.mp3" --strip-vocals
```
Uses **Demucs** to create an instrumental before processing.

---

## 📂 Folder Layout
```
karaoke_time/
├── karaoke_core.py
├── karaoke_time.py
├── karaoke_generator.py
├── karaoke_maker.py
├── pause_media.applescript
└── songs/
    └── Artist__Title/
        ├── audio/
        ├── lyrics/
        │   ├── auto_Artist__Title.txt
        │   └── FINAL_Artist__Title.txt
        ├── output/
        └── logs/
```

---

## ⚙️ Requirements
- 🐍 Python 3.8 or newer  
- 🎥 [ffmpeg](https://ffmpeg.org/download.html) in `$PATH`  
- (Optional) [Demucs](https://github.com/facebookresearch/demucs) for vocal removal  
- macOS users: enable  
  **Chrome › View › Developer › ✔ Allow JavaScript from Apple Events**  
  for tab muting to work.  

---

## 💡 Tips
- Keep file names in `Artist__Title` format for best results.  
- Use `\N` to control line breaks and lyric placement in the final video.  
- Output videos are saved in `songs/Artist__Title/output/`.  

---

## 👨‍💻 Author
Created by **Miguel Cázares**
