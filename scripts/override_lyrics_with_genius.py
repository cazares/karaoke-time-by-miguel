#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
override_lyrics_with_genius.py
Minimal additive edit:
 - Cleans weird rectangle chars
 - Fixes “Pastor Seats” typo
 - Removes Genius metadata lines
 - ✅ Prints first 10 merged lyric lines for debugging
"""

import argparse, csv, re

def clean(s):
    s = re.sub(r'[■□�]+', '', s)
    s = s.replace("Pastor Seats", "The Past Recedes")
    bad_patterns = [
        r"(?i)\bContributors\b", r"(?i)\bProduced by\b", r"(?i)\bEmbed\b",
        r"(?i)\bLyrics\b", r"(?i)\bYou might also like\b",
        r"(?i)\bTranslations\b", r"(?i)\bTrack Info\b",
        r"(?i)\bWritten by\b", r"(?i)^[\d]+\s*$"
    ]
    for pat in bad_patterns:
        if re.search(pat, s): return ""
    return s.strip()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--whisper", required=True)
    p.add_argument("--genius", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    rows = list(csv.reader(open(args.whisper, encoding="utf-8")))
    genius_lines = [clean(l) for l in open(args.genius, encoding="utf-8").read().splitlines() if l.strip()]
    genius_lines = [g for g in genius_lines if g]

    out = csv.writer(open(args.out, "w", newline="", encoding="utf-8"))
    out.writerow(["timestamp", "text"])
    for i, row in enumerate(rows[:len(genius_lines)]):
        text = genius_lines[i].replace("\\n", "\\N")
        out.writerow([row[0], text])

    print(f"✅ Wrote {len(genius_lines)} clean lyric rows to {args.out}")

    # 🩵 Debug: show first 10 merged lines
    try:
        with open(args.out, encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            print("\n🩵 DEBUG MERGED LYRICS (first 99):")
            for i, r in enumerate(rdr):
                print(f"  {r['timestamp']:>7} | {r['text']}")
                if i >= 99: break
    except Exception as e:
        print(f"⚠️ Debug print failed: {e}")

if __name__ == "__main__":
    main()

# end of override_lyrics_with_genius.py
