#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — fetches lyrics automatically via curl (HTML parse only)
No API keys required. Filenames are sanitized (spaces → underscores).
--no-prompt skips confirmations but still allows manual lyrics entry.
"""

import os, sys, subprocess, re, html
from pathlib import Path
import requests

NO_PROMPT = "--no-prompt" in sys.argv

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def fetch_lyrics(artist, title):
    print(f"\n🎵 Fetching lyrics for: {artist} — {title}")
    artist_q = sanitize_name(artist)
    title_q = sanitize_name(title)

    # Try Genius
    try:
        search_url = f"https://www.google.com/search?q={artist_q}+{title_q}+site:genius.com"
        print(f"🔍 Searching Genius: {search_url}")
        html_data = subprocess.check_output(["curl", "-sL", search_url]).decode("utf-8", errors="ignore")
        match = re.search(r"https://genius\.com/[a-zA-Z0-9\-]+-lyrics", html_data)
        if match:
            url = match.group(0)
            print(f"✅ Found Genius lyrics: {url}")
            page = requests.get(url, timeout=10).text
            blocks = re.findall(r'<div[^>]+Lyrics__Container[^>]*>(.*?)</div>', page, re.DOTALL)
            lyrics_text = "\n".join(re.sub(r"<.*?>", "", b).strip() for b in blocks)
            clean = html.unescape(lyrics_text).strip()
            if clean:
                return clean
    except Exception as e:
        print(f"⚠️ Genius scrape failed: {e}")

    # Try LyricsFreak
    try:
        search_url = f"https://www.lyricsfreak.com/search.php?a=search&type=song&q={artist_q}+{title_q}"
        print(f"🔍 Searching LyricsFreak: {search_url}")
        html_data = subprocess.check_output(["curl", "-sL", search_url]).decode("utf-8", errors="ignore")
        match = re.search(r"/[a-z0-9]/[a-z0-9_\-]+/[a-z0-9_\-]+\.html", html_data)
        if match:
            path = match.group(0)
            url = f"https://www.lyricsfreak.com{path}"
            print(f"✅ Found LyricsFreak lyrics: {url}")
            page = requests.get(url, timeout=10).text
            lyrics = re.search(r'<div id="content_h"[^>]*>(.*?)</div>', page, re.DOTALL)
            if lyrics:
                clean = re.sub(r"<.*?>", "", lyrics.group(1))
                return html.unescape(clean).strip()
    except Exception as e:
        print(f"⚠️ LyricsFreak scrape failed: {e}")

    # Try Lyrics.com
    try:
        search_url = f"https://www.lyrics.com/serp.php?st={title_q}+{artist_q}"
        print(f"🔍 Searching Lyrics.com: {search_url}")
        html_data = requests.get(search_url, timeout=10).text
        match = re.search(r"/lyric/[0-9]+/[A-Za-z0-9\-_]+", html_data)
        if match:
            url = f"https://www.lyrics.com{match.group(0)}"
            print(f"✅ Found Lyrics.com lyrics: {url}")
            page = requests.get(url, timeout=10).text
            lyrics = re.search(r'<pre id="lyric-body-text"[^>]*>(.*?)</pre>', page, re.DOTALL)
            if lyrics:
                clean = re.sub(r"<.*?>", "", lyrics.group(1))
                return html.unescape(clean).strip()
    except Exception as e:
        print(f"⚠️ Lyrics.com scrape failed: {e}")

    # Manual fallback — still allowed even in --no-prompt
    print("\n❌ Auto-fetch failed. Please paste lyrics below (Enter twice to finish):\n")
    lines = []
    while True:
        try:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        except EOFError:
            break
    manual_lyrics = "\n".join(lines).strip()
    if manual_lyrics:
        print("✅ Manual lyrics accepted.")
        return manual_lyrics

    sys.exit("❌ Could not fetch or input lyrics.")

def handle_auto_lyrics(mp3_path, artist, title):
    base = Path(f"songs/{sanitize_name(artist)}__{sanitize_name(title)}")
    lyrics_dir = base / "lyrics"
    os.makedirs(lyrics_dir, exist_ok=True)

    auto_txt = lyrics_dir / f"auto_{sanitize_name(artist)}_{sanitize_name(title)}.txt"
    final_txt = lyrics_dir / f"FINAL_{sanitize_name(artist)}_{sanitize_name(title)}.txt"

    if not auto_txt.exists():
        text = fetch_lyrics(artist, title)
        with open(auto_txt, "w", encoding="utf-8") as f:
            f.write(text)
        with open(final_txt, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n✅ Lyrics fetched and saved:\n  - {auto_txt}\n  - {final_txt}")
    else:
        print(f"✅ Using existing lyrics in: {auto_txt}")
        with open(final_txt, "r", encoding="utf-8") as f:
            text = f.read()

    if NO_PROMPT:
        print("🚀 --no-prompt enabled: skipping edit confirmation.")
    else:
        print("\n📝 Please edit the FINAL_ file (insert \\N for line breaks), then press Enter to continue…")
        input()

    return text, {"lyrics": str(lyrics_dir)}

def auto_no_prompt_choice(prompt_text: str, default: str = "n"):
    """Auto-answer 'n' when --no-prompt is active."""
    if NO_PROMPT:
        print(f"{prompt_text} (auto-selected '{default}' due to --no-prompt)")
        return default.lower()
    else:
        return input(prompt_text).strip().lower() or default.lower()

if __name__ == "__main__":
    print("Run karaoke_generator.py instead.")
