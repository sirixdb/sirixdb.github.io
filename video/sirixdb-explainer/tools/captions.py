#!/usr/bin/env python3
"""Re-time the burned-in captions to the voice clips where they sit now.

Usage: tools/captions.py
Aligns the words of build/script.json to each voice clip in video/index.html and rewrites only
video/compositions/cap.html (the old one is kept as cap.html.bak-<time>). Use it after
re-voicing a line or moving voice clips in Studio. Free.
"""
import sys, pathlib, json, shutil, subprocess, tempfile, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import PROJECT, CFG, align, voice_clips

words = []
for c in voice_clips(PROJECT / "video"):
    words += align(c["src"], CFG["beats"][c["beat"] - 1]["text"], c["start"], c["media_start"], c["beat"] - 1)
cap = PROJECT / "video" / "compositions" / "cap.html"
with tempfile.TemporaryDirectory() as tmp:
    wj = pathlib.Path(tmp) / "words.json"; json.dump(words, open(wj, "w"))
    subprocess.run([sys.executable, PROJECT / "build" / "build.py", tmp, PROJECT / "capture" / "demo.ansi", wj, "--captions-only"], check=True, capture_output=True)
    shutil.copy(cap, cap.with_name(f"cap.html.bak-{time.strftime('%Y%m%d-%H%M%S')}"))
    shutil.copy(pathlib.Path(tmp) / "compositions" / "cap.html", cap)
print(f"cap.html re-timed: {len(words)} words over {len(set(w['beat'] for w in words))} voice clips")
