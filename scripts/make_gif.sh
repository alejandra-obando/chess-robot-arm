#!/usr/bin/env bash
# Converts a video (e.g. one recorded on your phone) into a compact,
# repo-friendly GIF using ffmpeg's two-pass palette method, which looks
# noticeably better than a naive single-pass conversion at a similar size.
#
# Usage:
#   scripts/make_gif.sh <input_video> [output.gif] [fps] [width]
#
# Examples:
#   scripts/make_gif.sh media/raw/first_move.mp4 media/demo.gif
#   scripts/make_gif.sh media/raw/first_move.mp4 media/demo.gif 12 480

set -euo pipefail

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required. Install it (e.g. 'sudo apt install ffmpeg') and re-run." >&2
  exit 1
fi

input="${1:?usage: make_gif.sh <input_video> [output.gif] [fps] [width]}"
output="${2:-media/demo.gif}"
fps="${3:-15}"
width="${4:-600}"

if [[ ! -f "$input" ]]; then
  echo "Input file not found: $input" >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"
palette="$(mktemp -t chess_arm_palette_XXXX.png)"
trap 'rm -f "$palette"' EXIT

filters="fps=${fps},scale=${width}:-1:flags=lanczos"

ffmpeg -y -i "$input" -vf "${filters},palettegen" "$palette"
ffmpeg -y -i "$input" -i "$palette" \
  -lavfi "${filters}[x];[x][1:v]paletteuse" \
  "$output"

echo "Wrote $output"
