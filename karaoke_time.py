#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — fetches lyrics automatically via curl → Google API fallback
"""

import os, sys, subprocess, requests, re, html
from pathlib import Path

def fetch_lyrics(artist, title):
    print(f"\n🎵 Fetching lyrics for: {artist} — {title}")
    query = f"{artist} {title} lyrics"
    tmp = "/tmp/lyrics_fetch.html"

    # curl first
    curl_cmd = ["curl", "-s", f"https://www.google.com/search?q={query}+site:genius.com"]
    try:
        html_data = subprocess.check_output(curl_cmd).decode("utf-8")
        match = re.search(r'>([^<]+) Lyrics \| Genius Lyrics<', html_data)
        if match:
            url = f"https://genius.com/{match.group(1).replace(' ', '-')}-lyrics"
            print(f"✅ Found Genius page: {url}")
            page = requests.get(url, timeout=10).text
            text = re.sub(r"<.*?>", "", page)
            lines = re.findall(r"[A-Za-z0-9 ,.'?!()]+", text)
            return "\n".join(lines)
    except Exception as e:
        print(f"⚠️ curl fetch failed, fallback to Google API ({e})")

    # fallback: Google Custom Search
    try:
        resp = requests.get(f"https://www.googleapis.com/customsearch/v1?q={query}", timeout=10)
        return html.unescape(re.sub(r"<.*?>", "", resp.text))
    except Exception as e:
        sys.exit(f"❌ Failed to fetch lyrics: {e}")

def handle_auto_lyrics(mp3_path, artist, title):
    base = Path(f"songs/{artist.replace(' ', '_')}__{title.replace(' ', '_')}")
    lyrics_dir = base / "lyrics"
    os.makedirs(lyrics_dir, exist_ok=True)

    auto_txt = lyrics_dir / f"auto_{artist.replace(' ', '_')}_{title.replace(' ', '_')}.txt"
    final_txt = lyrics_dir / f"FINAL_{artist.replace(' ', '_')}_{title.replace(' ', '_')}.txt"

    if not auto_txt.exists():
        text = fetch_lyrics(artist, title)
        with open(auto_txt, "w", encoding="utf-8") as f: f.write(text)
        with open(final_txt, "w", encoding="utf-8") as f: f.write(text)
        print(f"\n✅ Lyrics fetched and saved:\n  - {auto_txt}\n  - {final_txt}")
    else:
        print(f"✅ Using existing lyrics in: {auto_txt}")

    print("\n📝 Please edit the FINAL_ file (insert \\N for line breaks), then press Enter to continue…")
    input()
    return text if 'text' in locals() else open(final_txt).read(), {"lyrics": str(lyrics_dir)}

if __name__ == "__main__":
    print("Run karaoke_generator.py instead.")
