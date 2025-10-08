#!/bin/zsh
# ============================================================
# run_karaoke.sh — Convenience launcher for Karaoke Time
# Automatically detects .csv, .ass, and .mp3 in ./lyrics
# Runs karaoke_time.py with proper arguments.
# ============================================================

set -e  # stop on error

# --- Locate the latest timestamped files ---
lyrics_dir="lyrics"
csv_file=$(ls -t ${lyrics_dir}/*.csv 2>/dev/null | head -1)
ass_file=$(ls -t ${lyrics_dir}/*.ass 2>/dev/null | head -1)
mp3_file=$(ls -t ${lyrics_dir}/*.mp3 2>/dev/null | head -1)

if [[ -z "$csv_file" || -z "$ass_file" || -z "$mp3_file" ]]; then
  echo "❌ Missing required files (.csv, .ass, or .mp3) in ${lyrics_dir}/"
  exit 1
fi

# --- Optional overrides (can be passed via env vars) ---
FONT_SIZE=${FONT_SIZE:-52}
BUFFER=${BUFFER:-0.5}
OVERLAP_BUFFER=${OVERLAP_BUFFER:-0.05}
PREFIX=${PREFIX:-non_interactive_}

echo "🎤 Running Karaoke Time..."
echo "  CSV:  $csv_file"
echo "  ASS:  $ass_file"
echo "  MP3:  $mp3_file"
echo "  Font size: $FONT_SIZE pt"
echo "  Buffers: default=${BUFFER}s, overlap=${OVERLAP_BUFFER}s"

# --- Run Python script ---
python3 karaoke_time.py \
  --csv "$csv_file" \
  --ass "$ass_file" \
  --mp3 "$mp3_file" \
  --font-size "$FONT_SIZE" \
  --buffer "$BUFFER" \
  --overlap-buffer "$OVERLAP_BUFFER" \
  --output-prefix "$PREFIX"

echo "✅ Karaoke video successfully generated!"

