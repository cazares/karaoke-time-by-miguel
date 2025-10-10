#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, html, requests
from bs4 import BeautifulSoup
from mutagen.id3 import ID3

def sanitize_name(name):
    return re.sub(r'[^a-zA-Z0-9]+', '_', name.strip())

def get_mp3_metadata(mp3_path):
    tags = ID3(mp3_path)
    artist = tags.get("TPE1")
    title = tags.get("TIT2")
    return (artist.text[0] if artist else "UnknownArtist",
            title.text[0] if title else os.path.splitext(os.path.basename(mp3_path))[0])

def fetch_lyrics(artist, title):
    """
    Try curl-based lyrics.ovh first (with retry),
    then fallback to Google snippet (with retry),
    then fail explicitly.
    """
    base_url = f"https://api.lyrics.ovh/v1/{requests.utils.quote(artist)}/{requests.utils.quote(title)}"

    def try_curl(url):
        """Use curl for more reliable API access."""
        import subprocess, json
        try:
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True, text=True, timeout=8
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if "lyrics" in data and data["lyrics"].strip():
                    return data["lyrics"].strip()
        except Exception as e:
            print(f"[warn] curl attempt failed: {e}")
        return None

    # 1️⃣ Try curl twice
    for attempt in range(2):
        lyrics = try_curl(base_url)
        if lyrics:
            return lyrics
        print(f"[warn] curl attempt {attempt+1} failed, retrying..." if attempt == 0 else "[error] curl failed twice")

    # 2️⃣ Try Google fallback (with retry)
    def try_google(artist, title):
        import html as ihtml
        q = requests.utils.quote(f"{artist} {title} lyrics")
        html_url = f"https://www.google.com/search?q={q}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(html_url, headers=headers, timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                blocks = soup.find_all("div", {"jsname": "YS01Ge"})
                if blocks:
                    return "\n".join(ihtml.unescape(b.get_text("\n")) for b in blocks)
        except Exception as e:
            print(f"[warn] Google attempt failed: {e}")
        return None

    for attempt in range(2):
        lyrics = try_google(artist, title)
        if lyrics:
            return lyrics
        print(f"[warn] Google attempt {attempt+1} failed, retrying..." if attempt == 0 else "[error] Google failed twice")

    print(f"[fatal] Could not fetch lyrics for '{artist} - {title}' after all attempts.")
    return None

def prepare_song_dirs(artist, title, mp3_path):
    base = os.path.join("songs", f"{sanitize_name(artist)}__{sanitize_name(title)}")
    paths = {
        "base": base,
        "audio": os.path.join(base, "audio"),
        "lyrics": os.path.join(base, "lyrics"),
        "output": os.path.join(base, "output"),
        "logs": os.path.join(base, "output", "logs"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths

def handle_auto_lyrics(mp3_path, artist=None, title=None, lyrics_txt=None):
    if lyrics_txt and os.path.exists(lyrics_txt):
        print(f"✅ Using existing lyrics file: {lyrics_txt}")
        with open(lyrics_txt, "r", encoding="utf-8") as f:
            return f.read(), None

    if not artist or not title:
        meta_artist, meta_title = get_mp3_metadata(mp3_path)
        artist = artist or meta_artist
        title = title or meta_title

    paths = prepare_song_dirs(artist, title, mp3_path)
    lyrics = fetch_lyrics(artist, title)
    if not lyrics:
        print(f"[error] Could not fetch lyrics for '{artist} - {title}'. Please create lyrics manually.")
        sys.exit(1)

    auto_path = os.path.join(paths["lyrics"], f"auto_{sanitize_name(artist)}_{sanitize_name(title)}.txt")
    final_path = os.path.join(paths["lyrics"], f"FINAL_{sanitize_name(artist)}_{sanitize_name(title)}.txt")
    with open(auto_path, "w", encoding="utf-8") as f: f.write(lyrics)
    with open(final_path, "w", encoding="utf-8") as f: f.write(lyrics)

    print(f"\n✅ Lyrics fetched and saved:\n  - {auto_path}\n  - {final_path}")
    input(f"\n📝 Please edit the FINAL_ file (insert \\N for line breaks), save, then press Enter to continue...")

    with open(final_path, "r", encoding="utf-8") as f:
        return f.read(), paths

# === CLI ENTRYPOINT ===
if __name__ == '__main__':
    import argparse, subprocess

    parser = argparse.ArgumentParser(description="Karaoke Time v3.3.4 — hybrid lyric fetcher/renderer")
    parser.add_argument("--mp3", required=True, help="Path to MP3 file")
    parser.add_argument("--artist", help="Artist name (optional override)")
    parser.add_argument("--title", help="Song title (optional override)")
    parser.add_argument("--lyrics-txt", help="Path to existing FINAL_ lyrics text (skips fetch)")
    args = parser.parse_args()

    lyrics_text, paths = handle_auto_lyrics(args.mp3, args.artist, args.title, args.lyrics_txt)

    # 🪄 Friendly reminder + optional auto-run
    if paths:
        base = os.path.splitext(os.path.basename(args.mp3))[0]
        final_txt_path = os.path.join(
            paths["lyrics"],
            f"FINAL_{sanitize_name(args.artist or 'ArtistName')}_{sanitize_name(args.title or base)}.txt"
        )

        next_cmd = [
            "python3",
            "karaoke_generator.py",
            args.mp3,
            "--artist", args.artist or "ArtistName",
            "--title", args.title or base,
            "--lyrics-txt", final_txt_path
        ]

        print(f"\n✅ Lyrics ready and saved in:\n   {paths['lyrics']}")
        print(f"\n➡️  Next step:\n   {' '.join(next_cmd)}")

        choice = input("\nPress [Enter] to run this now, or type 'q' to quit: ").strip().lower()
        if choice in ("", "y", "yes"):
            print("\n▶️ Running karaoke_generator.py...\n")
            subprocess.run(next_cmd)
        else:
            print("\n👋 Exiting without running generator. You can run the above command later.")
