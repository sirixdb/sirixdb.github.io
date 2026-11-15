#!/usr/bin/env python3
"""Re-time captions to the current voice clip windows and caption track placement.

Usage: tools/captions.py
Rewrites only the caption composition, keeping a .bak-<time> copy. Word times are estimated
from the full source speech before applying Studio trims; review phrase boundaries afterwards.
"""
import shutil, time
from common import PROJECT, CFG, align, voice_clips, caption_track, root_duration, clip_cues, duration
from caption_composition import caption_groups, captions

video = PROJECT / "video"
track = caption_track(video)
rows, word_count = [], 0
for c in voice_clips(video):
    if c["volume"] <= 0:
        continue
    words = align(c["src"], CFG["beats"][c["beat"] - 1]["text"], c["start"],
                  c["media_start"], c["beat"] - 1, c["duration"])
    word_count += len(words)
    length = c["duration"] if c["duration"] is not None else duration(c["src"]) - c["media_start"]
    end = c["start"] + length
    rows += clip_cues(caption_groups(words), c["start"], end)
rows = clip_cues(sorted(rows), max(0, track["start"]),
                 min(root_duration(video), track["start"] + track["duration"]))
local_rows = [(round(a - track["start"] + track["media_start"], 3),
               round(b - track["start"] + track["media_start"], 3), text) for a, b, text in rows]
cap = track["src"]
shutil.copy(cap, cap.with_name(f"{cap.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}"))
cap.write_text(captions(local_rows))
print(f"{cap.name} re-timed: {word_count} audible words")
