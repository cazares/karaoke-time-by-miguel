#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karaoke_time.py — auto lyrics fetcher (HTML scraping only)
Adds full diagnostic/debug mode and timestamped logs.
Always allows manual fallback input.
Now supports:
  • --debug: full diagnostic logging
  • --test-lyric-fetching: forces refetch even if local lyrics exist
  • Browser-like User-Agent + retry resilience
  • Outputs full curl commands when --debug is enabled
"""

import os, sys, subprocess, re, html, textwrap, time
from pathlib import Path
import requests

NO_PROMPT = "--no-prompt" in sys.argv
DEBUG = "--debug" in sys.argv
FORCE_REFETCH = "--test-lyric-fetching" in sys.argv
DEBUG_LOG = None

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36"
)

# Timestamped debug log per run
if DEBUG:
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    DEBUG_LOG = f"lyrics_debug_{ts}.log"
    print(f"🧾 Debug log file: {DEBUG_LOG}")

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().replace(" ", "_"))

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

def debug_curl(cmd):
    """Prints and logs the full curl command when debugging."""
    if DEBUG:
        curl_str = " ".join(cmd)
        print(f"\n🐚 DEBUG curl: {curl_str}\n")
        try:
            with open(DEBUG_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n[{time.strftime('%H:%M:%S')}] curl_cmd: {curl_str}\n")
        except Exception:
            pass

def safe_get(url, retries=2, timeout=10):
    """Performs resilient HTTP GET with fake browser headers and retry on 403/429."""
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code in (403, 429):
                print(f"⚠️  Got {r.status_code} for {url} (attempt {attempt}/{retries}) — retrying...")
                time.sleep(2 * attempt)
                continue
            return r.text
        except Exception as e:
            print(f"⚠️  Request error on attempt {attempt}/{retries}: {e}")
            time.sleep(2 * attempt)
    return ""

def log_success(source, url):
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("last_lyrics_debug.log", "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] {source}: {url}\n")
    except Exception:
        pass

def fetch_lyrics(artist, title):
    print(f"\n🎵 Fetching lyrics for: {artist} — {title}")
    artist_q = sanitize_name(artist)
    title_q = sanitize_name(title)

    def is_valid_lyrics(text: str, source: str) -> bool:
        """Rejects non-ASCII, HTML, or error-like junk."""
        if not text or len(text.strip()) < 40:
            debug_print(f"{source}: rejected (too short)", text)
            return False
        if any(x in text.lower() for x in [
            "403", "error", "permission_denied", "api key",
            "{", "}", "[", "]", "not found", "unauthorized"
        ]):
            debug_print(f"{source}: rejected (error-like content)", text)
            return False
        if not all(ord(c) < 128 for c in text):
            debug_print(f"{source}: rejected (non-ASCII characters detected)", text)
            return False
        symbols = sum(not c.isalnum() and not c.isspace() for c in text)
            # ratio of punctuation/symbols to total chars
        ratio = symbols / max(len(text), 1)
        if ratio > 0.25:
            debug_print(f"{source}: rejected (symbol ratio {ratio:.2f})", text)
            return False
        return True

    # ===== 1️⃣ Genius =====
    try:
        search_url = f"https://www.google.com/search?q={artist_q}+{title_q}+site:genius.com"
        print(f"🔍 Searching Genius via Google…")
        cmd = ["curl", "-sL", "-A", USER_AGENT, search_url]
        debug_curl(cmd)
        html_data = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
        debug_print("Google Search HTML (Genius)", html_data)
        match = re.search(r"https://genius\.com/[a-zA-Z0-9\-]+-lyrics", html_data)
        if match:
            url = match.group(0)
            print(f"✅ Found Genius lyrics URL: {url}")
            page = safe_get(url)
            debug_print("Genius page snippet", page)
            blocks = re.findall(r'<div[^>]+Lyrics__Container[^>]*>(.*?)</div>', page, re.DOTALL)
            lyrics_text = "\n".join(re.sub(r"<.*?>", "", b).strip() for b in blocks)
            clean = html.unescape(lyrics_text).strip()
            if is_valid_lyrics(clean, "Genius"):
                print("🎯 Genius returned valid lyrics.")
                log_success("Genius", url)
                return clean
            else:
                print("⚠️ Genius returned invalid or empty content.")
    except Exception as e:
        print(f"⚠️ Genius scrape failed: {e}")

    # ===== 2️⃣ LyricsFreak =====
    try:
        search_url = f"https://www.lyricsfreak.com/search.php?a=search&type=song&q={artist_q}+{title_q}"
        print(f"🔍 Searching LyricsFreak…")
        cmd = ["curl", "-sL", "-A", USER_AGENT, search_url]
        debug_curl(cmd)
        html_data = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
        debug_print("LyricsFreak search HTML", html_data)
        match = re.search(r"/[a-z0-9]/[a-z0-9_\-]+/[a-z0-9_\-]+\.html", html_data)
        if match:
            url = f"https://www.lyricsfreak.com{match.group(0)}"
            print(f"✅ Found LyricsFreak lyrics URL: {url}")
            page = safe_get(url)
            debug_print("LyricsFreak page snippet", page)
            lyrics = re.search(r'<div id="content_h"[^>]*>(.*?)</div>', page, re.DOTALL)
            if lyrics:
                clean = re.sub(r"<.*?>", "", lyrics.group(1))
                clean = html.unescape(clean).strip()
                if is_valid_lyrics(clean, "LyricsFreak"):
                    print("🎯 LyricsFreak returned valid lyrics.")
                    log_success("LyricsFreak", url)
                    return clean
    except Exception as e:
        print(f"⚠️ LyricsFreak scrape failed: {e}")

    # ===== 3️⃣ Lyrics.com =====
    try:
        search_url = f"https://www.lyrics.com/serp.php?st={title_q}+{artist_q}"
        print(f"🔍 Searching Lyrics.com…")
        debug_print("Lyrics.com fetch URL", search_url)
        html_data = safe_get(search_url)
        debug_print("Lyrics.com search HTML", html_data)
        match = re.search(r"/lyric/[0-9]+/[A-Za-z0-9\-_]+", html_data)
        if match:
            url = f"https://www.lyrics.com{match.group(0)}"
            print(f"✅ Found Lyrics.com lyrics URL: {url}")
            page = safe_get(url)
            debug_print("Lyrics.com page snippet", page)
            lyrics = re.search(r'<pre id="lyric-body-text"[^>]*>(.*?)</pre>', page, re.DOTALL)
            if lyrics:
                clean = re.sub(r"<.*?>", "", lyrics.group(1))
                clean = html.unescape(clean).strip()
                if is_valid_lyrics(clean, "Lyrics.com"):
                    print("🎯 Lyrics.com returned valid lyrics.")
                    log_success("Lyrics.com", url)
                    return clean
    except Exception as e:
        print(f"⚠️ Lyrics.com scrape failed: {e}")

    # ===== 4️⃣ Manual fallback (always shown) =====
    print("\n❌ Auto-fetch failed. Please paste lyrics below (press Enter twice to finish):\n")
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

    if not auto_txt.exists() or FORCE_REFETCH:
        if FORCE_REFETCH and auto_txt.exists():
            print("🧪 --test-lyric-fetching active: forcing lyric refetch...")
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

if __name__ == "__main__":
    print("Run karaoke_generator.py instead.")
