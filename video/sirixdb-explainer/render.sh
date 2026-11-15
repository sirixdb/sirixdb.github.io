#!/usr/bin/env bash
# Render the film from video/ exactly as it is (your Studio edits included). Free: no credits.
# Render modes and output files: EDITING.md, "Re-render (free)".
# Before rendering, the music is re-ducked under the voice clips where they sit now
# (tools/remix.py) and the SRT is derived from the caption composition (tools/srt.py).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; V="$HERE/video"; OUT="$HERE/out"
HF=(npx --yes hyperframes@0.9.42)
mkdir -p "$OUT"
python3 "$HERE/tools/remix.py"
python3 "$HERE/tools/srt.py" > "$OUT/sirixdb-60s.srt"
if [ "${1:-}" = "--quick" ]; then
  ( cd "$V" && "${HF[@]}" render --quality draft --fps 30 --workers 2 -o "$OUT/sirixdb-60s-draft.mp4" )
  echo "draft: $OUT/sirixdb-60s-draft.mp4"; exit 0
fi
( cd "$V" && "${HF[@]}" render --quality delivery --fps 30 --workers 2 -o "$OUT/sirixdb-60s.mp4" )
TOTAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/sirixdb-60s.mp4")
ffmpeg -y -loglevel error -ss "$(python3 -c "print(max(0, $TOTAL - 1.0))")" -i "$OUT/sirixdb-60s.mp4" -frames:v 1 "$OUT/poster.png"
CLEAN="$HERE/.render-clean"; rm -rf "$CLEAN"; cp -r "$V" "$CLEAN"
sed -E -i 's/(<div( [^>]*)? id="cap" )/\1data-hidden="true" /' "$CLEAN/index.html"   # captions off, nothing else changed (Studio may put data-hf-id before id)
( cd "$CLEAN" && "${HF[@]}" render --quality delivery --fps 30 --workers 2 -o "$OUT/sirixdb-site.mp4" )
rm -rf "$CLEAN"
echo "done: $OUT"
