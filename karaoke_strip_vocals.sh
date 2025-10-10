#!/usr/bin/env bash
# =============================================================
# 🎤 Karaoke Vocal Remover (FFmpeg)
# by Miguel Cázares 🎸
# -------------------------------------------------------------
# Removes or reduces vocals from a song using only ffmpeg filters.
# Designed for living-room karaoke: clean, simple, and fast.
#
# Levels of vocal removal:
#   0 → Least aggressive  | Keeps song full and natural; vocals still present
#   1 → Light reduction   | Lowers vocals slightly; subtle karaoke feel
#   2 → Mild removal      | Noticeably reduces vocals; keeps musical body
#   3 → Balanced (default)| Great overall karaoke balance
#   4 → Aggressive        | Strong vocal removal; thinner mix
#   5 → Maximum           | Mono mix; highest removal but flattest sound
#
# Usage Examples:
#   ./karaoke_strip.sh "Song.mp3"
#   ./karaoke_strip.sh "Song.mp3" --vocal-strip-level 4
#   ./karaoke_strip.sh "Song.mp3" --all-levels
#   ./karaoke_strip.sh -h
# =============================================================

set -e

show_help() {
  echo ""
  echo "🎤 Karaoke Vocal Remover (FFmpeg)"
  echo "----------------------------------------"
  echo "Removes vocals from any stereo MP3 to make karaoke tracks."
  echo ""
  echo "Usage:"
  echo "  ./karaoke_strip.sh \"input.mp3\" [options]"
  echo ""
  echo "Options:"
  echo "  --vocal-strip-level [0–5]   Process one aggressiveness level (default: 3)"
  echo "  --all-levels                Generate all levels 0–5 for A/B testing"
  echo "  -h, --help                  Show this help message"
  echo ""
  echo "Levels of vocal removal:"
  echo "  0 → Least aggressive  | Full original sound; vocals mostly intact"
  echo "  1 → Light reduction   | Vocals softened slightly"
  echo "  2 → Mild removal      | Balanced karaoke sound, minimal artifacts"
  echo "  3 → Balanced default  | Ideal mix for most songs"
  echo "  4 → Aggressive        | Strong vocal removal, some thinness"
  echo "  5 → Maximum removal   | Mono mix, vocals nearly gone"
  echo ""
  echo "Examples:"
  echo "  ./karaoke_strip.sh \"Californication.mp3\""
  echo "  ./karaoke_strip.sh \"Californication.mp3\" --vocal-strip-level 4"
  echo "  ./karaoke_strip.sh \"Californication.mp3\" --all-levels"
  echo ""
  echo "Output Files:"
  echo "  input_karaoke_L#.mp3  → one per chosen level"
  echo ""
  exit 0
}

# --- Show help if requested or missing input ---
if [[ "$1" == "--help" || "$1" == "-h" || -z "$1" ]]; then
  show_help
fi

INPUT="$1"
EXT="${INPUT##*.}"
BASENAME="$(basename "$INPUT" .${EXT})"

# --- Default parameters ---
LEVEL=3
RUN_ALL=false

# --- Parse optional flags ---
if [[ "$2" == "--vocal-strip-level" && "$3" =~ ^[0-9]+$ ]]; then
  LEVEL=$3
elif [[ "$2" == "--all-levels" ]]; then
  RUN_ALL=true
fi

# --- Define filter bank function ---
get_filter_for_level() {
  local L=$1
  case $L in
    0) echo "highpass=f=100,lowpass=f=14000,volume=1.4" ;;
    1) echo "pan=stereo|c0=0.9*c0-0.6*c1|c1=0.9*c1-0.6*c0,highpass=f=100,lowpass=f=12000,alimiter=limit=0.95,volume=1.6" ;;
    2) echo "pan=stereo|c0=0.8*c0-0.7*c1|c1=0.8*c1-0.7*c0,highpass=f=120,lowpass=f=11000,alimiter=limit=0.95,volume=1.7" ;;
    3) echo "pan=stereo|c0=0.7*c0-0.7*c1|c1=0.7*c1-0.7*c0,highpass=f=120,lowpass=f=10000,alimiter=limit=0.95,volume=1.8" ;;
    4) echo "pan=stereo|c0=0.7*c0-0.9*c1|c1=0.7*c1-0.9*c0,highpass=f=140,lowpass=f=9500,alimiter=limit=0.9,volume=2.0" ;;
    5) echo "pan=mono|c0=0.9*c0-0.9*c1,highpass=f=150,lowpass=f=9000,alimiter=limit=0.9,volume=2.2" ;;
    *) echo "pan=stereo|c0=0.7*c0-0.7*c1|c1=0.7*c1-0.7*c0,volume=1.8" ;;
  esac
}

# --- Process one or all ---
process_level() {
  local L=$1
  local FILTER
  FILTER=$(get_filter_for_level "$L")
  local OUTPUT="${BASENAME}_karaoke_L${L}.mp3"
  echo "🎧 Processing level $L ..."
  ffmpeg -loglevel error -i "$INPUT" -af "$FILTER" -y "$OUTPUT"
  echo "✅ Created: $OUTPUT"
}

# --- Run ---
if [ "$RUN_ALL" = true ]; then
  echo "🎶 Generating all karaoke levels (0–5)..."
  for L in 0 1 2 3 4 5; do
    process_level "$L"
  done
  echo "🎤 Done! Compare each _karaoke_L#.mp3 and pick your favorite."
else
  process_level "$LEVEL"
fi
