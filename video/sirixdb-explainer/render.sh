#!/usr/bin/env bash
# Render the film from video/ exactly as it is (your Studio edits included). Free: no credits.
#   ./render.sh            film + SRT + poster + stems in out/
#   ./render.sh --quick    draft-quality film only
# Before rendering, the music is re-ducked under the voice clips where they sit now
# (tools/remix.py) and the SRT is derived from the caption composition (tools/srt.py).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; V="$HERE/video"; OUT="$HERE/out"
HF=(npx --yes hyperframes@0.9.42)
HEAVY="${HEAVY:-}"   # optional: a wrapper that runs heavy jobs at low priority; empty = run directly
RUN=(); [ -x "$HEAVY" ] && RUN=("$HEAVY")
mkdir -p "$OUT/stems"
"${RUN[@]}" python3 "$HERE/tools/remix.py"
python3 "$HERE/tools/srt.py" > "$OUT/sirixdb-60s.srt"
if [ "${1:-}" = "--quick" ]; then
  ( cd "$V" && "${RUN[@]}" "${HF[@]}" render --quality draft --fps 30 --workers 2 -o "$OUT/sirixdb-60s-draft.mp4" )
  echo "draft: $OUT/sirixdb-60s-draft.mp4"; exit 0
fi
( cd "$V" && "${RUN[@]}" "${HF[@]}" render --quality delivery --fps 30 --workers 2 -o "$OUT/sirixdb-60s.mp4" )
TOTAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/sirixdb-60s.mp4")
"${RUN[@]}" ffmpeg -y -loglevel error -ss "$(python3 -c "print(max(0, $TOTAL - 1.0))")" -i "$OUT/sirixdb-60s.mp4" -frames:v 1 "$OUT/poster.png"
# stems for a normal editor
"${RUN[@]}" ffmpeg -y -loglevel error -i "$OUT/sirixdb-60s.mp4" -an -c:v copy "$OUT/stems/picture-with-captions.mp4"
CLEAN="$HERE/.render-clean"; rm -rf "$CLEAN"; cp -r "$V" "$CLEAN"
sed -E -i 's/(<div( [^>]*)? id="cap" )/\1data-hidden="true" /' "$CLEAN/index.html"   # captions off, nothing else changed (Studio may put data-hf-id before id)
( cd "$CLEAN" && "${RUN[@]}" "${HF[@]}" render --quality delivery --fps 30 --workers 2 -o "$OUT/stems/.clean.mp4" )
"${RUN[@]}" ffmpeg -y -loglevel error -i "$OUT/stems/.clean.mp4" -an -c:v copy "$OUT/stems/picture-clean.mp4"
rm -rf "$CLEAN" "$OUT/stems/.clean.mp4"
"${RUN[@]}" python3 "$HERE/tools/remix.py" --stems "$OUT/stems"
cp "$OUT/sirixdb-60s.srt" "$OUT/stems/"
echo "done: $OUT"
