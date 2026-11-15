#!/usr/bin/env python3
"""Regenerator step (optional): place the raw voice takes on a fresh timeline.

Usage: build/audio.py   (called by build/regenerate.sh; not needed for normal Studio editing)
Reads audio/takes/b1..bN.wav, tightens each (pause cap + tempo from build/script.json), gives all
clips one common gain so the voice sits at -16 LUFS, writes video/assets/vo-scene-N.wav, and
writes audio/work/words.json + placement.json for build.py. Word times are estimated from
silence detection (no speech recogniser is installed).
"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
from common import PROJECT, CFG, SR, run, tighten, loudness, duration, align

work = PROJECT / "audio" / "work"; work.mkdir(parents=True, exist_ok=True)
assets = PROJECT / "video" / "assets"; assets.mkdir(parents=True, exist_ok=True)
T = CFG["timing"]; beats = CFG["beats"]
clips = []
for i in range(len(beats)):
    out = work / f"clip-{i+1}.wav"
    tighten(PROJECT / "audio" / "takes" / f"b{i+1}.wav", out)
    clips.append(out)
# place: first word at T.start; each clip begins with 40 ms of silence
t, place, words = T["start"] - 0.04, [], []
for i, c in enumerate(clips):
    place.append({"id": f"vo-{i+1}", "src": f"assets/vo-scene-{i+1}.wav", "start": round(t, 3), "duration": round(duration(c), 3)})
    words += align(c, beats[i]["text"], t, beat=i)
    t += duration(c) - 0.16 + T["gap"] + beats[i].get("pause_after", 0.0)
# one gain for all clips: measure the voice on its timeline
inputs, filt = [], []
for n, (c, p) in enumerate(zip(clips, place)):
    inputs += ["-i", str(c)]; filt.append(f"[{n}:a]adelay={int(p['start'] * 1000)}:all=1[d{n}]")
filt.append("".join(f"[d{n}]" for n in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0[v]")
run(["ffmpeg", "-y", "-hide_banner", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]", work / "vo-raw.wav"])
gain = T.get("voice_lufs", -16.0) - loudness(work / "vo-raw.wav")
for i, c in enumerate(clips):
    run(["ffmpeg", "-y", "-hide_banner", "-i", c, "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=0", "-ar", SR, "-c:a", "pcm_s16le", assets / f"vo-scene-{i+1}.wav"])
json.dump(words, open(work / "words.json", "w"), indent=1)
json.dump(place, open(work / "placement.json", "w"), indent=1)
print(json.dumps({"voice_gain_db": round(gain, 2), "last_word_end": words[-1]["end"], "placement": place}, indent=1))
