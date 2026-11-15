#!/usr/bin/env python3
"""Turn a raw Higgsfield voice take into the clip the video uses.

Usage: tools/voice.py <beat number> [loudness in LUFS]
Reads audio/takes/b<N>.wav, trims it, sets its pauses (natural up to max_pause_in_take, or the
beat's take_pauses) and applies the tempo from build/script.json,
matches the loudness of the clip it replaces (or the loudness given), and writes
video/assets/vo-scene-<N>.wav (the old clip is kept in audio/replaced/). Free: local ffmpeg only.
"""
import sys, pathlib, shutil, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import PROJECT, CFG, tighten, loudness, duration

n = int(sys.argv[1])
raw = PROJECT / "audio" / "takes" / f"b{n}.wav"
dst = PROJECT / "video" / "assets" / f"vo-scene-{n}.wav"
target = float(sys.argv[2]) if len(sys.argv) > 2 else loudness(dst) if dst.exists() else CFG["timing"].get("voice_lufs", -16.0)
old_len = duration(dst) if dst.exists() else 0.0
if dst.exists():
    keep = PROJECT / "audio" / "replaced"; keep.mkdir(parents=True, exist_ok=True)
    shutil.copy(dst, keep / f"vo-scene-{n}.{time.strftime('%Y%m%d-%H%M%S')}.wav")
tmp = dst.with_name(f"vo-scene-{n}.new.wav")
pauses = CFG["beats"][n - 1].get("take_pauses")
tighten(raw, tmp, pauses=pauses)
gain = target - loudness(tmp)
tighten(raw, dst, gain_db=gain, pauses=pauses); tmp.unlink()
# the peak limiter takes a little loudness back; make up for it, or every rebuild of a line
# (which matches the clip before it) would come out a bit quieter than the last
for _ in range(3):
    miss = target - loudness(dst)
    if abs(miss) < 0.15: break
    gain += miss; tighten(raw, dst, gain_db=gain, pauses=pauses)
new_len = duration(dst)
# keep the clip's length in index.html in step with the new file (only this attribute changes)
import re
idx = PROJECT / "video" / "index.html"; html = idx.read_text()
html2, k = re.subn(rf'(<audio\b[^>]*\bid="vo-{n}"[^>]*\bdata-duration=")[\d.]+(")', rf"\g<1>{new_len:.3f}\g<2>", html)
if k: idx.write_text(html2)
print(f"vo-scene-{n}.wav: {new_len:.2f} s (was {old_len:.2f} s, {new_len - old_len:+.2f} s); loudness matched to {target:.1f} LUFS")
if abs(new_len - old_len) > 0.15:
    print("The line's length changed: in Studio, nudge the later clips/scenes if needed, then run tools/captions.py to re-time the captions.")
