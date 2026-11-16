#!/usr/bin/env bash
# New music bed with Higgsfield Sonilo (COSTS CREDITS: 4 credits for 64 s observed).
# Edit "music.prompt"/"duration" in build/script.json first. Shows the estimate, asks, then
# replaces audio/music.m4a (old one kept as audio/music.<time>.m4a) and rebuilds
# video/assets/music-ducked.wav. Music on/off: EDITING.md, "Everyday edits". Then ./render.sh (free).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
P=$(python3 -c "import json;print(json.load(open('$HERE/build/script.json'))['music']['prompt'])")
D=$(python3 -c "import json;print(json.load(open('$HERE/build/script.json'))['music']['duration'])")
higgsfield generate cost sonilo_music --prompt "$P" --duration "$D" --json; higgsfield account status
read -r -p "Generate (spends credits)? [y/N] " ok; [ "$ok" = y ] || exit 1
higgsfield generate create sonilo_music --prompt "$P" --duration "$D" --wait --json > "$HERE/audio/music.json"
url=$(python3 -c "import json;print(json.load(open('$HERE/audio/music.json'))[0]['result_url'])")
cp "$HERE/audio/music.m4a" "$HERE/audio/music.$(date +%Y%m%d-%H%M%S).m4a"
curl -s -o "$HERE/audio/music.m4a" "$url"
python3 "$HERE/tools/remix.py"
echo "If the new track starts without a silent lead-in, set music.skip_lead_in to 0 in build/script.json and re-run tools/remix.py."
