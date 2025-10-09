#!/bin/zsh
# ============================================================
# run_karaoke.sh — CLI wrapper for Karaoke Time
# ============================================================

set -e

# --- Default values ---
FONT_SIZE=52
BUFFER=0.5
OVERLAP_BUFFER=0.05
LYRIC_OFFSET=0.0
OFFSET=0.0
PREFIX="non_interactive_"
AUTO_PLAY=false

# --- Parse CLI arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --font-size) FONT_SIZE="$2"; shift 2 ;;
    --buffer) BUFFER="$2"; shift 2 ;;
    --overlap-buffer) OVERLAP_BUFFER="$2"; shift 2 ;;
    --lyric-offset) LYRIC_OFFSET="$2"; shift 2 ;;
    --offset) OFFSET="$2"; shift 2 ;;
    --prefix|--output-prefix) PREFIX="$2"; shift 2 ;;
    --auto-play) AUTO_PLAY=true; shift ;;
    --no-auto-play) AUTO_PLAY=false; shift ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options (alphabetical):"
      echo "  --auto-play           Pause media + open video in QuickTime after render"
      echo "  --buffer S            Default fade buffer seconds (default 0.5)"
      echo "  --font-size N         Subtitle font size points (default 52)"
      echo "  --lyric-offset S      Shift lyric blocks by S seconds (default 0.0)"
      echo "  --offset S            Global A/V offset (default 0.0)"
      echo "  --output-prefix STR   Prefix for output files (default 'non_interactive_')"
      echo "  --overlap-buffer S    Overlap fade buffer seconds (default 0.05)"
      echo "  --no-auto-play        Skip preview playback (default)"
      echo "  -h, --help            Show this help message"
      exit 0 ;;
    *)
      echo "❌ Unknown argument: $1"
      echo "Run '$0 --help' for options."
      exit 1 ;;
  esac
done

# --- Detect latest lyric files ---
lyrics_dir="lyrics"
csv_file=$(ls -t ${lyrics_dir}/*.csv 2>/dev/null | head -1)
ass_file=$(ls -t ${lyrics_dir}/*.ass 2>/dev/null | head -1)
mp3_file=$(ls -t ${lyrics_dir}/*.mp3 2>/dev/null | head -1)

if [[ -z "$csv_file" || -z "$ass_file" || -z "$mp3_file" ]]; then
  echo "❌ Missing required files (.csv, .ass, or .mp3) in ${lyrics_dir}/"
  exit 1
fi

# --- Display summary ---
echo ""
echo "🎤 Running Karaoke Time..."
echo "----------------------------------------------------"
echo "  CSV:            $csv_file"
echo "  ASS:            $ass_file"
echo "  MP3:            $mp3_file"
echo "  Font size:      ${FONT_SIZE} pt"
echo "  Buffers:        default=${BUFFER}s, overlap=${OVERLAP_BUFFER}s"
echo "  Lyric offset:   ${LYRIC_OFFSET}s"
echo "  Global offset:  ${OFFSET}s"
echo "  Prefix:         ${PREFIX}"
echo "  Auto-play:      ${AUTO_PLAY}"
echo "----------------------------------------------------"
echo ""

# --- Run Python generator ---
python3 karaoke_time.py \
  --csv "$csv_file" \
  --ass "$ass_file" \
  --mp3 "$mp3_file" \
  --font-size "$FONT_SIZE" \
  --buffer "$BUFFER" \
  --overlap-buffer "$OVERLAP_BUFFER" \
  --lyric-offset "$LYRIC_OFFSET" \
  --offset "$OFFSET" \
  --output-prefix "$PREFIX" \
  $( [[ "$AUTO_PLAY" == true ]] && echo "--auto-play" || echo "--no-auto-play" )

echo ""
echo "✅ Karaoke video successfully generated!"
