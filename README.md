# 🎤 Karaoke Time by Miguel

Turn any `.txt` lyric file into a full karaoke video (1080p) with **one Python command**.

🧠 Created by [Miguel Cazares](https://miguelengineer.com)

---

## 🚀 Quick Start

1. Place your lyrics in a `.txt` file (use `\N` for line breaks between verses)
2. Run:

   ```bash
   python3 karaoke_time.py your_lyrics.txt
   ```

3. Drop your `.mp3` file into the newly created folder when prompted
4. Press **ENTER** as the song plays to log each lyric block

---

## 🧩 Features
- Auto-creates output directory
- Auto-detects most recent `.mp3` if none selected
- Emoji & colorized debug logs (default)
- Outputs `.csv`, `.ass`, `.mp4` (1080p)
- Re-run safe with timestamped versions
- `--release` flag for quiet mode

---

## 🧱 Output
Example output for `calif_lyrics_annotated.txt`:

```
calif_lyrics_annotated/
├── calif_lyrics_annotated_2025-10-07_1452.csv
├── calif_lyrics_annotated_2025-10-07_1452.ass
└── calif_lyrics_annotated_2025-10-07_1452.mp4
```

---

## 🪄 Perfect for
- Musicians building karaoke versions
- Developers showcasing automation projects
- Recruiter demos on [miguelengineer.com](https://miguelengineer.com)

---

## ⚙️ License
MIT © Miguel Cazares
