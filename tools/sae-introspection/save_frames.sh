#!/usr/bin/env bash

# Reads frame data from running SAE / Valkey using echo.py and saves
# them as jpeg files while removing all time-related metadata

set -euo pipefail

SOURCE_CMD="set -o pipefail; poetry run python echo.py -f | jq -r .frame.frameDataJpeg"
OUTDIR="frames"
mkdir -p "$OUTDIR"
FIXED_TIME="200001010000"   # touch -t format: YYYYMMDDhhmm[.ss]

bash -c "$SOURCE_CMD" | while IFS= read -r line; do
  [ -z "$line" ] && continue   # skip stray blank lines

  tmp=$(mktemp)
  if ! printf '%s' "$line" | base64 -d 2>/dev/null | jpegtran -copy none -optimize > "$tmp" 2>/dev/null; then
    echo "warn: failed to decode/strip a frame, skipping" >&2
    rm -f "$tmp"
    continue
  fi

  name=$(sha256sum "$tmp" | cut -d' ' -f1)
  dest="${OUTDIR}/${name}.jpg"

  mv "$tmp" "$dest"
  touch -t "$FIXED_TIME" "$dest"
done
