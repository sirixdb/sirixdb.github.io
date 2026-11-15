#!/usr/bin/env bash
# OPTIONAL: rebuild video/ from build/ (script.json, build.py, the raw voice takes).
# This throws away Studio edits in video/ — so it refuses to run without --regenerate,
# and backs video/ up to video.bak-<time>/ first. Free (no credits).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
[ "${1:-}" = "--regenerate" ] || { echo "refusing: this replaces video/ (your Studio edits). Re-run with --regenerate; video/ is backed up first."; exit 2; }
BAK="$HERE/video.bak-$(date +%Y%m%d-%H%M%S)"; cp -r "$HERE/video" "$BAK"; echo "backup: $BAK"
python3 "$HERE/build/audio.py"
python3 "$HERE/build/build.py" "$HERE/video" "$HERE/capture/demo.ansi" "$HERE/audio/work/words.json" --regenerate --backed-up
mv -f "$HERE/video/captions.srt" "$HERE/video/timing.json" "$HERE/audio/work/" 2>/dev/null || true
python3 "$HERE/tools/remix.py"
echo "video/ regenerated; review it in Studio, then ./render.sh"
