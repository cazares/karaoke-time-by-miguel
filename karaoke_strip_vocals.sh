#!/usr/bin/env bash
# =============================================================
# 🎤 Karaoke Vocal Remover (FFmpeg)
# by Miguel Cázares 🎸
# -------------------------------------------------------------
# Removes or reduces vocals from any MP3 and optionally diagnoses
# channel balance / stereo width automatically.
#
# USAGE:
#   ./karaoke_strip.sh "Song.mp3" [options]
#
# OPTIONS:
#   --vocal-strip-level [0–5]   Process one aggressiveness level (default: 3)
#   --all-levels                Generate all 0–5 levels
#   --diagnostic                Run full analysis and output multiple variants
#   -h, --help                  Show help and usage info
#
# LEVEL MEANINGS:
#   0 → Least aggressive  | Natural, vocals intact
#   1 → Light reduction   | Subtle karaoke feel
#   2 → Mild removal      | Balanced reduction
#   3 → Balanced default  | Ideal for most songs
#   4 → Aggressive        | Stronger vocal cut, thinner
#   5 → Maximum removal   | Mono, near-complete cancel (flat)
# =============================================================

set -e

show_help() {
  echo ""
  echo "🎤 Karaoke Vocal Remover (FFmpeg)"
  echo "----------------------------------------"
  echo "Usage:"
  echo "  ./karaoke_strip.sh \"input.mp3\" [options]"
  echo ""
  echo "Options:"
  echo "  --vocal-strip-level [0–5]   Process a specific level (default: 3)"
  echo "  --all-levels                Generate all six levels (0–5)"
  echo "  --diagnostic                Run channel analysis + all levels + widened mix"
  echo "  -h, --help                  Show this help message"
  echo ""
  echo "Each level removes vocals with increasing aggressiveness:"
  echo "  0 → Least aggressive  | Keeps natural sound, vocals mostly intact"
  echo "  1 → Light reduction   | Vocals slightly reduced"
  echo "  2 → Mild removal      | Noticeable reduction, balanced tone"
  echo "  3 → Balanced default  | Ideal karaoke mix (recommended)"
  echo "  4 → Aggressive        | Strong vocal removal, thinner mix"
  echo "  5 → Maximum removal   | Mono, highest removal, flat sound"
  echo ""
  exit 0
}

# --- Help ---
if [[ "$1" == "--help" || "$1" == "-h" || -z "$1" ]]; then
  show_help
fi

INPUT="$1"
EXT="${INPUT##*.}"
BASENAME="$(basename "$INPUT" .${EXT})"

LEVEL=3
RUN_ALL=false
DIAG=false

if [[ "$2" == "--vocal-strip-level" && "$3" =~ ^[0-9]+$ ]]; then
  LEVEL=$3
elif [[ "$2" == "--all-levels" ]]; then
  RUN_ALL=true
elif [[ "$2" == "--diagnostic" ]]; then
  DIAG=true
fi

# --- Filter presets ---
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

process_level() {
  local L=$1
  local FILTER
  FILTER=$(get_filter_for_level "$L")
  local OUTPUT="${BASENAME}_karaoke_L${L}.mp3"
  echo "🎧 Level $L ..."
  ffmpeg -loglevel error -i "$INPUT" -af "$FILTER" -y "$OUTPUT"
  echo "✅ Created: $OUTPUT"
}

diagnostic_mode() {
  echo "🔍 Running diagnostic mode..."
  echo "--------------------------------------------"
  
  # --- Channel info ---
  echo "📊 Channel analysis:"
  ffprobe -hide_banner -show_streams -select_streams a:0 -i "$INPUT" | grep -E "codec_name|channels|sample_rate|bit_rate"
  ffprobe -hide_banner -show_streams -select_streams a:0 -i "$INPUT" > "${BASENAME}_diagnostic.txt" 2>/dev/null
  echo "📝 Saved detailed report: ${BASENAME}_diagnostic.txt"
  echo ""

  # --- Generate all 0–5 ---
  echo "🎶 Generating levels 0–5..."
  for L in 0 1 2 3 4 5; do
    process_level "$L"
  done

  # --- Widened variant for near-mono mixes ---
  echo ""
  echo "🔊 Creating stereo-widened version (for mono-heavy songs)..."
  WIDE_FILTER="stereotools=balance_in=0.2:balance_out=0.8,pan=stereo|c0=0.8*c0-0.8*c1|c1=0.8*c1-0.8*c0,highpass=f=120,lowpass=f=10000,volume=2.0"
  WIDE_OUTPUT="${BASENAME}_karaoke_widened.mp3"
  ffmpeg -loglevel error -i "$INPUT" -af "$WIDE_FILTER" -y "$WIDE_OUTPUT"
  echo "✅ Created widened stereo variant: $WIDE_OUTPUT"

  echo ""
  echo "--------------------------------------------"
  echo "✅ Diagnostic mode complete."
  echo "Compare these output files:"
  echo "  - ${BASENAME}_karaoke_L0.mp3  through  L5.mp3"
  echo "  - ${BASENAME}_karaoke_widened.mp3"
  echo "  - ${BASENAME}_diagnostic.txt (audio info)"
  echo ""
}

# --- Main execution ---
if [ "$DIAG" = true ]; then
  diagnostic_mode
elif [ "$RUN_ALL" = true ]; then
  echo "🎶 Generating all karaoke levels (0–5)..."
  for L in 0 1 2 3 4 5; do
    process_level "$L"
  done
  echo "✅ Done!"
else
  process_level "$LEVEL"
fi
