#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_youtube_url.py
-----------------------------------
Fetches the top YouTube video URL for a given song + artist using the YouTube Data API v3.

Usage:
    export YT_KEY="AIzaSyXXXX..."   # set once (in ~/.zshrc or current session)
    python3 fetch_youtube_url.py --song "The Past Recedes" --artist "John Frusciante" --debug
"""

import argparse, sys, os, requests, json, urllib.parse

# --- Colors for readability ---
C = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "reset": "\033[0m",
}

def log(msg, color="cyan"):
    print(f"{C[color]}{msg}{C['reset']}")

def main():
    parser = argparse.ArgumentParser(description="Fetch top YouTube video URL for a song + artist")
    parser.add_argument("--song", required=True, help="Song title")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--youtube-key", help="(optional) YouTube Data API v3 key; defaults to $YT_KEY")
    parser.add_argument("--debug", action="store_true", help="Print full API response JSON")
    args = parser.parse_args()

    # --- Pull from env if not given ---
    api_key = args.youtube_key or os.getenv("YT_KEY")
    if not api_key:
        log("❌ Missing API key. Provide --youtube-key or set $YT_KEY.", "red")
        sys.exit(1)

    query = f"{args.artist} {args.song}"
    encoded_query = urllib.parse.quote_plus(query)
    api_url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&maxResults=1&q={encoded_query}&key={api_key}"
    )

    log(f"🔎 Searching YouTube for: {query}")
    log(f"→ Request URL: {api_url}", "yellow")

    try:
        resp = requests.get(api_url, timeout=10)
    except Exception as e:
        log(f"❌ Network error: {e}", "red")
        sys.exit(1)

    log(f"HTTP {resp.status_code}", "yellow")
    if args.debug:
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)

    if resp.status_code != 200:
        log("❌ YouTube API error — check your key, quota, or API enablement.", "red")
        sys.exit(1)

    data = resp.json()
    if not data.get("items"):
        log("❌ No results found.", "red")
        sys.exit(1)

    first = data["items"][0]
    video_id = first["id"]["videoId"]
    video_title = first["snippet"]["title"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    log(f"✅ Found video: {video_title}", "green")
    log(f"🔗 {video_url}", "cyan")

    # Print plain URL for subprocess consumption
    print(video_url)

if __name__ == "__main__":
    main()

# end of fetch_youtube_url.py
