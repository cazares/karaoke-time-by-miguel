#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_lyric_fetcher.py — shared lyric fetching logic for Karaoke Time
Handles Genius, LyricsFreak, and Lyrics.com. Supports --debug logging and override paths.
"""

import os, re, sys, html, textwrap, time, subprocess, requests
from pathlib import Path

DEBUG = "--debug" in sys.argv
DEBUG_LOG = None
if DEBUG:
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    DEBUG_LOG = f"lyrics_debug_{ts}.log"
    print(f"🧾 Debug log file: {DEBUG_LOG}")

def debug_print(label, content):
    if not DEBUG:
        return
    snippet = textwrap.shorten(re.sub(r"\s+", " ", content.strip()), width=400, placeholder="...")
    print(f"\n🔎 DEBUG: {label}\n{snippet}\n")
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%H:%M:%S')}] {label}\n{content[:4000]}\n")
    except Exception:
        pass

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

def fetch_lyrics(artist, title, override_path=None, force_refetch=False):
    """Fetch lyrics from multiple sources or override file if provided."""
    if override_path:
        path = Path(override_path)
        if path.exists():
            print(f"📂 Using override lyric file: {path}")
            return path.read_text(encoding="utf-8")
        else:
            print(f"⚠️ Override lyric file not found: {path}")

    artist_q = sanitize_name(artist)
    title_q = sanitize_name(title)
    print(f"\n🎵 Fetching lyrics for: {artist} — {title}")

    def is_valid_lyrics(text: str, src: str) -> bool:
        if not text or len(text.strip()) < 40:
            debug_print(f"{src}: too short", text)
            return False
        if any(x in text.lower() for x in ["403", "error", "permission_denied", "api key", "{", "}", "[", "]", "not found", "unauthorized"]):
            debug_print(f"{src}: error-like content", text)
            return False
        if not all(ord(c) < 128 for c in text):
            debug_print(f"{src}: non-ASCII", text)
            return False
        return True

    sources = [
        ("Genius", f"https://www.google.com/search?q={artist_q}+{title_q}+site:genius.com", r"https://genius\.com/[a-zA-Z0-9\-]+-lyrics", '<div[^>]+Lyrics__Container[^>]*>(.*?)</div>'),
        ("LyricsFreak", f"https://www.lyricsfreak.com/search.php?a=search&type=song&q={artist_q}+{title_q}", r"/[a-z0-9]/[a-z0-9_\-]+/[a-z0-9_\-]+\.html", '<div id="content_h"[^>]*>(.*?)</div>'),
        ("Lyrics.com", f"https://www.lyrics.com/serp.php?st={title_q}+{artist_q}", r"/lyric/[0-9]+/[A-Za-z0-9\-_]+", '<pre id="lyric-body-text"[^>]*>(.*?)</pre>')
    ]

    for name, search_url, url_regex, content_regex in sources:
        try:
            print(f"🔍 Searching {name}…")
            html_data = subprocess.check_output(["curl", "-sL", search_url, "-A", "Mozilla/5.0"], text=True)
            debug_print(f"{name} search HTML", html_data)
            match = re.search(url_regex, html_data)
            if not match:
                continue
            url = match.group(0)
            if not url.startswith("http"):
                url = f"https://{name.lower()}.com{url}"
            print(f"✅ Found {name} lyrics URL: {url}")
            page = requests.get(url, timeout=10).text
            debug_print(f"{name} page snippet", page)
            block = re.findall(content_regex, page, re.DOTALL)
            text = "\n".join(re.sub(r"<.*?>", "", b).strip() for b in block)
            clean = html.unescape(text).strip()
            if is_valid_lyrics(clean, name):
                print(f"🎯 {name} returned valid lyrics.")
                return clean
        except Exception as e:
            print(f"⚠️ {name} fetch failed: {e}")

    print("❌ Auto-fetch failed — manual input required.")
    return None
