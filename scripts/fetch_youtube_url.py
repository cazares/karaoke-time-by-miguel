#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_youtube_url.py — searches YouTube for a song and artist,
returns the most popular video URL using YouTube Data API v3.
Now includes safeguard against hardcoded API keys or tokens.
"""

import argparse, re, sys
from googleapiclient.discovery import build

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
def get_most_popular_video_url(api_key: str, song: str, artist: str):
    youtube = build('youtube', 'v3', developerKey=api_key)
    query = f"{song} {artist}"

    search_response = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=10
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
    if not video_ids:
        return None

    stats_response = youtube.videos().list(
        part="statistics",
        id=",".join(video_ids)
    ).execute()

    best_video = None
    best_views = -1
    for item in stats_response.get('items', []):
        vid = item['id']
        view_count = int(item.get('statistics', {}).get('viewCount', 0))
        if view_count > best_views:
            best_views = view_count
            best_video = vid

    return f"https://www.youtube.com/watch?v={best_video}" if best_video else None


if __name__ == "__main__":
    warn_if_hardcoded_keys(__file__)

    parser = argparse.ArgumentParser(description="Search YouTube for a song and artist, return most popular video URL.")
    parser.add_argument("--song", required=True, help="Song title")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--youtube-key", required=True, help="YouTube Data API v3 key")
    args = parser.parse_args()

    url = get_most_popular_video_url(args.youtube_key, args.song, args.artist)
    print(url if url else "No video found.")

# end of fetch_youtube_url.py
