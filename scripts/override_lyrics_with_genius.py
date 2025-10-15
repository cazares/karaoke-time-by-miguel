#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
override_lyrics_with_genius.py
Minimal additive edit: cleans weird rectangle chars and fixes “Pastor Seats” typo.
"""

import argparse, csv, re

def clean(s):
    s = re.sub(r'[■□�]+', '', s)
    s = s.replace("Pastor Seats", "The Past Recedes")
    return s.strip()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--whisper", required=True)
    p.add_argument("--genius", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    rows = list(csv.reader(open(args.whisper, encoding="utf-8")))
    genius_lines = [clean(l) for l in open(args.genius, encoding="utf-8").read().splitlines() if l.strip()]

    out = csv.writer(open(args.out, "w", newline="", encoding="utf-8"))
    out.writerow(["timestamp", "text"])
    for i, row in enumerate(rows[:len(genius_lines)]):
        out.writerow([row[0], genius_lines[i].replace("\\n", "\\N")])
    print(f"✅ Wrote {len(genius_lines)} rows to {args.out}")

if __name__ == "__main__":
    main()

# end of override_lyrics_with_genius.py
