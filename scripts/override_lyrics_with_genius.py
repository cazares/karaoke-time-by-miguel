#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
override_lyrics_with_genius.py
Replace the text in a Whisper-generated timestamped CSV with lyrics fetched from Genius,
preserving Whisper's timestamps. Uses fuzzy matching (difflib) to align lines where counts differ.

Usage:
    python3 override_lyrics_with_genius.py \
      --whisper ./lyrics/song_synced.csv \
      --genius ./lyrics/song_genius.txt \
      --out ./lyrics/song_synced_genius.csv
"""
import argparse, csv, sys, re
from pathlib import Path
from difflib import SequenceMatcher

def normalize(s):
    s = s.strip().replace("’", "'")
    s = re.sub(r"[“”\"(),.?!:;—–\[\]\{\}]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def read_whisper_csv(p):
    rows = []
    with open(p, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append({"timestamp": r["timestamp"], "text": r["text"]})
    return rows

def read_genius_txt(p):
    txt = Path(p).read_text(encoding='utf-8')
    return [ln.strip() for ln in txt.splitlines() if ln.strip()]

def best_match_for(line, genius_lines, used):
    best_idx, best_score = None, 0.0
    n1 = normalize(line)
    for i, gl in enumerate(genius_lines):
        if i in used:
            continue
        score = SequenceMatcher(None, n1, normalize(gl)).ratio()
        if score > best_score:
            best_idx, best_score = i, score
    return best_idx, best_score

def main():
    p = argparse.ArgumentParser(description="Replace Whisper CSV lyrics with Genius lyrics, keep timings.")
    p.add_argument("--whisper", required=True)
    p.add_argument("--genius", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--min-similarity", type=float, default=0.30)
    args = p.parse_args()

    whisper_rows = read_whisper_csv(args.whisper)
    genius_lines = read_genius_txt(args.genius)
    used, out_rows = set(), []

    for w in whisper_rows:
        idx, score = best_match_for(w["text"], genius_lines, used)
        if idx is not None and score >= args.min_similarity:
            chosen = genius_lines[idx]; used.add(idx)
        else:
            # fallback: first unused
            remaining = [i for i in range(len(genius_lines)) if i not in used]
            if remaining:
                chosen = genius_lines[remaining[0]]; used.add(remaining[0])
            else:
                chosen = w["text"]
        out_rows.append({"timestamp": w["timestamp"], "text": chosen.replace("\\n", "\\N")})

    with open(args.out, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "text"])
        for r in out_rows:
            writer.writerow([r["timestamp"], r["text"]])
    print(f"✅ Wrote {len(out_rows)} rows to {args.out}")

if __name__ == "__main__":
    main()

# end of override_lyrics_with_genius.py
