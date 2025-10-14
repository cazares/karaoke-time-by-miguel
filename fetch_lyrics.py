#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_lyrics.py — fetches lyrics from Genius and writes them to a file.
Automatically prepends:
    [title]\n\nby\n\n[artist]
to the output.
"""

import argparse
import sys
from lyricsgenius import Genius
from bs4 import BeautifulSoup
import requests

def fetch_with_genius(token, title, artist):
    genius = Genius(token, timeout=10, retries=3)
    try:
        song = genius.search_song(title, artist)
    except Exception as e:
        print(f"Error searching song on Genius: {e}", file=sys.stderr)
        return None
    if song and song.lyrics:
        return song.lyrics
    return None

def fallback_scrape(genius_url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; lyric-fetcher/1.0)"}
    try:
        resp = requests.get(genius_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"HTTP error fetching {genius_url}: {e}", file=sys.stderr)
        return None

    html = BeautifulSoup(resp.text, "html.parser")
    parts = html.find_all("div", attrs={"data-lyrics-container": "true"})
    if parts:
        lines = []
        for div in parts:
            for elem in div.strings:
                lines.append(elem)
        return "\n".join(lines).strip()

    div = html.find("div", class_="lyrics")
    if div:
        return div.get_text().strip()

    meta = html.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"]
    return None

def find_genius_url(token, title, artist):
    base = "https://api.genius.com"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": f"{title} {artist}"}
    resp = requests.get(base + "/search", headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    for hit in data.get("response", {}).get("hits", []):
        p = hit.get("result", {}).get("primary_artist", {}).get("name", "")
        if artist.lower() in p.lower():
            return hit["result"].get("url")
    hits = data.get("response", {}).get("hits", [])
    if hits:
        return hits[0]["result"].get("url")
    return None

def main():
    parser = argparse.ArgumentParser(description="Fetch song lyrics via Genius + scraping")
    parser.add_argument("--title", required=True, help="Title of song")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--output", required=True, help="Output filename")
    parser.add_argument("--genius-token", required=True, help="Genius API client access token")
    args = parser.parse_args()

    lyrics = fetch_with_genius(args.genius_token, args.title, args.artist)
    if not lyrics:
        print("lyricsgenius failed, trying fallback scrape...", file=sys.stderr)
        url = find_genius_url(args.genius_token, args.title, args.artist)
        if not url:
            print("Could not find Genius page URL.", file=sys.stderr)
            sys.exit(1)
        lyrics = fallback_scrape(url)
        if not lyrics:
            print("Fallback scrape failed.", file=sys.stderr)
            sys.exit(1)

    # prepend formatted header
    header = f"{args.title}\n\nby\n\n{args.artist}\n\n"
    lyrics = header + lyrics.strip() + "\n"

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(lyrics)
    except Exception as e:
        print(f"Error writing file {args.output}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote lyrics to {args.output}")

if __name__ == "__main__":
    main()

# end of fetch_lyrics.py
