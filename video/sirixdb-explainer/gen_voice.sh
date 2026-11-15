#!/usr/bin/env bash
# Re-voice lines with Higgsfield (COSTS CREDITS: about 1.4-1.7 credits per line observed).
#   ./gen_voice.sh 3       re-voice beat 3 (edit its "tts" and "text" in build/script.json first)
#   ./gen_voice.sh all     re-voice every beat
# Shows the estimate and balance and asks before spending. Writes the new clip straight into
# video/assets/vo-scene-N.wav (old clip kept in audio/replaced/), re-ducks the music, and tells
# you if the line got longer or shorter. Then: check it in Studio, ./render.sh (free).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
which=${1:?beat number or all}
n=$(python3 -c "import json;print(len(json.load(open('$HERE/build/script.json'))['beats']))")
beats=$([ "$which" = all ] && seq 1 "$n" || echo "$which")
field(){ python3 -c "import json;c=json.load(open('$HERE/build/script.json'));print($1)"; }
VID=$(field "c['voice']['voice_id']"); VT=$(field "c['voice']['voice_type']"); CUE=$(field "c['voice']['delivery']")
for b in $beats; do
  echo "beat $b: $(field "c['beats'][$b-1]['tts']")"
  higgsfield generate cost seed_audio --prompt "$CUE $(field "c['beats'][$b-1]['tts']")" --voice_id "$VID" --voice_type "$VT" --json
done
higgsfield account status
read -r -p "Generate (spends credits)? [y/N] " ok; [ "$ok" = y ] || exit 1
mkdir -p "$HERE/audio/takes/old"
for b in $beats; do   # one at a time: the starter plan rejects a second concurrent job
  [ -f "$HERE/audio/takes/b$b.wav" ] && cp "$HERE/audio/takes/b$b.wav" "$HERE/audio/takes/old/b$b.$(date +%Y%m%d-%H%M%S).wav"
  higgsfield generate create seed_audio --prompt "$CUE $(field "c['beats'][$b-1]['tts']")" --voice_id "$VID" --voice_type "$VT" \
    --format wav --sample_rate 48000 --wait --json > "$HERE/audio/takes/b$b.json"
  url=$(python3 -c "import json;print(json.load(open('$HERE/audio/takes/b$b.json'))[0]['result_url'])")
  curl -s -o "$HERE/audio/takes/b$b.wav" "$url"
  python3 "$HERE/tools/voice.py" "$b"
done
python3 "$HERE/tools/remix.py"
higgsfield account status
echo "Next: open video/ in Studio to check timing; tools/captions.py re-times captions if a line changed; ./render.sh"
