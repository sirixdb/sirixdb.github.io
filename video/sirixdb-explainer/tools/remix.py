#!/usr/bin/env python3
"""Rebuild the music track so it ducks under the voice clips where they sit now.

Usage: tools/remix.py
Reads video/index.html (voice clips vo-1..vo-N, possibly moved/trimmed in Studio) and the music
source audio/music.m4a; writes video/assets/music-ducked.wav (fitted to the film's length,
faded out under the end card). Free: local ffmpeg only.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import PROJECT, CFG, SR, run, root_duration, voice_clips

video = PROJECT / "video"; assets = video / "assets"
total = root_duration(video)
clips = voice_clips(video)
work = PROJECT / "audio" / "work"; work.mkdir(parents=True, exist_ok=True)

# voice on the film clock
inputs, filt = [], []
for n, c in enumerate(clips):
    trim = ["-ss", str(c["media_start"])] + (["-t", str(c["duration"])] if c["duration"] is not None else [])
    inputs += trim + ["-i", str(c["src"])]
    filt.append(f"[{n}:a]aresample={SR},volume={c['volume']},adelay={int(round(c['start'] * 1000))}:all=1[d{n}]")
if clips:
    filt.append("".join(f"[d{n}]" for n in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{total}[v]")
else:
    inputs = ["-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono"]
    filt = [f"[0:a]atrim=0:{total}[v]"]
run(["ffmpeg", "-y", "-hide_banner", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]", "-ar", SR, "-ac", 1, "-c:a", "pcm_s16le", work / "vo-full.wav"])

if not CFG["music"].get("enabled", True):   # voice-only cut: keep the music sources, write a silent bed
    run(["ffmpeg", "-y", "-hide_banner", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo", "-t", total, "-c:a", "pcm_s16le", assets / "music-ducked.wav"])
    print(f"music-ducked.wav: {total:.2f} s, silent (music.enabled is false), {len(clips)} voice clips")
    sys.exit(0)

# music fitted to the film: skip the source's silent lead-in, fade in, fade out under the end card
m = CFG["music"]; fade = 2.6
run(["ffmpeg", "-y", "-hide_banner", "-ss", m["skip_lead_in"], "-i", PROJECT / m["file"], "-af",
     f"afade=t=in:st=0:d=1.2,afade=t=out:st={max(0, total - fade)}:d={fade},apad,atrim=0:{total}",
     "-ar", SR, "-ac", 2, "-c:a", "pcm_s16le", work / "music-bed.wav"])
# duck: bed at -15 dB, a further ~8 dB under speech (sidechain on the voice)
level = CFG["music"].get("level_db", -15)
run(["ffmpeg", "-y", "-hide_banner", "-i", work / "music-bed.wav", "-i", work / "vo-full.wav", "-filter_complex",
     f"[0:a]volume={level}dB[m];[m][1:a]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=450:makeup=1,apad,atrim=0:{total}[d]",   # the compressor can drop the last frames; keep the film's exact length
     "-map", "[d]", "-ar", SR, "-c:a", "pcm_s16le", assets / "music-ducked.wav"])
print(f"music-ducked.wav: {total:.2f} s, ducked under {len(clips)} voice clips")
