#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_lyrics.py — fetches lyrics from Genius for a given artist and title.
Now includes safeguard against hardcoded API keys or tokens.
"""

import argparse, os, re, requests, sys

# --- Security safeguard -----------------------------------------------------
def warn_if_hardcoded_keys(script_path: str):
    """
    Scans the current script for any hardcoded API keys or tokens.
    It checks for common patterns like Google (AIza...), Genius, or Bearer tokens.
    """
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        patterns = [
            r"AIza[0-9A-Za-z\-_]{20,}",
            r"(?i)genius[_-]?token\s*=\s*['\"]\w+",
            r"Bearer\s+[A-Za-z0-9\-_]{20,}",
            r"sk-[A-Za-z0-9]{20,}"
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                print("⚠️  WARNING: Hardcoded API key detected in source file! "
                      f"({script_path})\n"
                      "→ Please move all keys to environment variables or command-line arguments.\n")
                break
    except Exception as e:
        print(f"[WARN] Could not scan for hardcoded keys: {e}")

# --- Core logic --------------------------------------------------------------
def fetch_lyrics(title: str, artist: str, genius_token: str, output_path: str):
    headers = {"Authorization": f"Bearer {genius_token}"}
    search_url = "https://api.genius.com/search"
    params = {"q": f"{title} {artist}"}

    print(f"🔎 Searching Genius for '{title}' by {artist}...")
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    hits = response.json()["response"]["hits"]

    if not hits:
        print("❌ No results found on Genius.")
        sys.exit(1)

    song_url = hits[0]["result"]["url"]
    print(f"🎵 Found Genius page: {song_url}")

    # Get raw HTML and extract lyrics (simple scrape)
    page = requests.get(song_url)
    page.raise_for_status()

    match = re.findall(r"<div[^>]+class=\"Lyrics__Container[^>]+>(.*?)</div>", page.text, re.S)
    if not match:
        print("❌ Could not extract lyrics from Genius page.")
        sys.exit(1)

    # Clean and normalize
    lyrics = re.sub(r"<.*?>", "", "\n".join(match))
    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics).strip()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(lyrics)

    print(f"✅ Lyrics saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    warn_if_hardcoded_keys(__file__)

    parser = argparse.ArgumentParser(description="Fetch lyrics from Genius and save to .txt")
    parser.add_argument("--title", required=True, help="Song title")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--output", required=True, help="Output .txt file path")
    parser.add_argument("--genius-token", required=True, help="Genius API token")
    args = parser.parse_args()

    fetch_lyrics(args.title, args.artist, args.genius_token, args.output)

# end of fetch_lyrics.py