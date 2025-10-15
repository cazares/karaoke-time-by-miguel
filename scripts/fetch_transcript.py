#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_transcript.py — get YouTube captions for karaoke (timed CSV)
Skips Whisper entirely if captions exist.
"""

import argparse, csv, sys
from youtube_transcript_api import YouTubeTranscriptApi

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--youtube-id", required=True)
    ap.add_argument("--artist", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        transcript = YouTubeTranscriptApi.get_transcript(args.youtube_id, languages=['en'])
    except Exception as e:
        print(f"❌ No transcript found: {e}")
        sys.exit(1)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "text"])
        for line in transcript:
            txt = line["text"].replace("\n", " ").strip()
            w.writerow([f"{line['start']:.2f}", txt])

    print(f"✅ Transcript saved to {args.out}")

if __name__ == "__main__":
    main()
