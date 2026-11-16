#!/usr/bin/env bash
# Re-voice lines with Higgsfield (COSTS CREDITS: ElevenLabs v4 about 0.23 per line, Seed Audio about 1.4-1.7).
#   ./gen_voice.sh 3       re-voice beat 3 (edit its "tts" and "text" in build/script.json first)
#   ./gen_voice.sh all     re-voice every beat
# The voice comes from build/script.json "voice": model "elevenlabs_v4" (default; voice_id, stability,
# similarity_boost) or "seed_audio" (set "model": "seed_audio" and the fields under voice.seed_audio).
# Shows the estimate and balance and asks before spending (YES=1 skips the question). Writes the new clip
# straight into video/assets/vo-scene-N.wav (old clip kept in audio/replaced/), re-ducks the music, and
# tells you if the line got longer or shorter. Then: check it in Studio, ./render.sh (free).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
which=${1:?beat number or all}
n=$(python3 -c "import json;print(len(json.load(open('$HERE/build/script.json'))['beats']))")
beats=$([ "$which" = all ] && seq 1 "$n" || echo "$which")
field(){ python3 -c "import json;c=json.load(open('$HERE/build/script.json'));print($1)"; }
MODEL=$(field "c['voice']['model']")
case "$MODEL" in
  elevenlabs_v4)
    VID=$(field "c['voice']['voice_id']"); VT=$(field "c['voice']['voice_type']")
    ST=$(field "c['voice']['stability']"); SB=$(field "c['voice']['similarity_boost']")
    args(){  # $1 = beat; the dialogue is one {text, voice_id, voice_type} entry
      python3 - "$HERE/build/script.json" "$1" <<'PY'
import json, sys
c = json.load(open(sys.argv[1])); v = c["voice"]; b = int(sys.argv[2])
print(json.dumps([{"text": c["beats"][b-1]["tts"], "voice_id": v["voice_id"], "voice_type": v["voice_type"]}]))
PY
    } ;;
  seed_audio)
    S="c['voice']['seed_audio']"
    VID=$(field "$S['voice_id']"); VT=$(field "$S['voice_type']"); CUE=$(field "$S['delivery']") ;;
  *) echo "unknown voice.model: $MODEL"; exit 1 ;;
esac
common_el=(--stability "${ST:-0}" --similarity_boost "${SB:-0}")
cost(){
  if [ "$MODEL" = elevenlabs_v4 ]; then
    timeout 60 higgsfield generate cost elevenlabs_v4 "${common_el[@]}" --dialogue "$(args "$1")" --json </dev/null
  else
    timeout 60 higgsfield generate cost seed_audio --prompt "$CUE $(field "c['beats'][$1-1]['tts']")" --voice_id "$VID" --voice_type "$VT" --json </dev/null
  fi
}
for b in $beats; do echo "beat $b: $(field "c['beats'][$b-1]['tts']")"; cost "$b"; done
higgsfield account status
if [ "${YES:-}" != 1 ]; then read -r -p "Generate (spends credits)? [y/N] " ok; [ "$ok" = y ] || exit 1; fi
mkdir -p "$HERE/audio/replaced"
for b in $beats; do   # one at a time: the starter plan rejects a second concurrent job
  [ -f "$HERE/audio/takes/b$b.wav" ] && cp "$HERE/audio/takes/b$b.wav" "$HERE/audio/replaced/seed-b$b.$(date +%Y%m%d-%H%M%S).wav"
  # create WITHOUT --wait, then wait by id: "create --wait" sometimes hangs without ever submitting the job
  if [ "$MODEL" = elevenlabs_v4 ]; then
    jid=$(timeout 60 higgsfield generate create elevenlabs_v4 "${common_el[@]}" --dialogue "$(args "$b")" --json </dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  else
    jid=$(timeout 60 higgsfield generate create seed_audio --prompt "$CUE $(field "c['beats'][$b-1]['tts']")" --voice_id "$VID" --voice_type "$VT" \
      --format wav --sample_rate 48000 --json </dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  fi
  timeout 300 higgsfield generate wait "$jid" --quiet --json </dev/null > "$HERE/audio/takes/b$b.json"
  url=$(python3 -c "import json;j=json.load(open('$HERE/audio/takes/b$b.json'));print((j[0] if isinstance(j,list) else j)['result_url'])")
  curl -s -o "$HERE/audio/takes/b$b.raw" "$url"
  ffmpeg -y -loglevel error -i "$HERE/audio/takes/b$b.raw" -ar 48000 "$HERE/audio/takes/b$b.wav"; rm -f "$HERE/audio/takes/b$b.raw"   # Eleven v4 returns mp3
  python3 "$HERE/tools/voice.py" "$b"
done
python3 "$HERE/tools/remix.py"
higgsfield account status
echo "Next: open video/ in Studio to check timing; tools/captions.py re-times captions if a line changed; ./render.sh"
