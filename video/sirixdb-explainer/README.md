# SirixDB explainer video: source

This is the editable source of the 90-second explainer on the sirix.io landing page
(`assets/video/sirixdb-explainer.mp4`). It is a [HyperFrames](https://hyperframes.heygen.com)
0.9.42 project: every scene is HTML and GSAP, rendered frame by frame, so text, colours, timing and
layout are all plain files. The voice and music were generated with Higgsfield. The terminal
scenes show a real `sirix-shell` session.

## Edit it in HyperFrames Studio

1. Install the HyperFrames desktop app (hyperframes.studio), or use the browser preview below.
2. Once after cloning: `python3 tools/remix.py`. This creates the ducked music track
   `video/assets/music-ducked.wav`, which is generated rather than committed.
3. Open the folder `video/sirixdb-explainer/video/` in the app. Without the app, run
   `cd video/sirixdb-explainer/video && npx --yes hyperframes@0.9.42 preview`.
4. Change text, timing or layout. Studio writes straight into `video/`, which is the source of truth.

## Re-render

```bash
cd video/sirixdb-explainer
./render.sh          # captioned MP4, site-clean MP4, SRT and poster in out/
./render.sh --quick  # draft-quality MP4 only
```

Rendering is free. It needs Node 22+, ffmpeg, python3 and Chrome. To publish the new cut on the
site, see "Publishing a new cut on sirix.io" in `EDITING.md`.

## What costs money

Only new audio does, through the Higgsfield CLI. Both scripts show the estimate and ask first.
- `./gen_voice.sh N` re-voices line N, about 1.4-1.7 credits on the configured `seed_audio` voice.
- `./gen_music.sh` makes a new music bed, about 4 credits for 64 s.

The configured voice model (`seed_audio`) has no language setting, and one early take of the last
line came out in Mandarin. After re-voicing, transcribe each new take and check that it is English.
Higgsfield's `qwen_audio_tts` takes `language=en` and costs about 0.06 credits per line, if a switch
is ever wanted.

## Layout

| Path | What |
|---|---|
| `video/` | the HyperFrames project (open this in Studio) |
| `build/script.json` | the spoken script, voice, music and pacing settings |
| `tools/` | free helpers: `remix.py` (music ducking), `voice.py` (process a take), `captions.py`, `srt.py` |
| `audio/takes/` | the raw voice takes, one per line |
| `audio/music.m4a` | the music bed |
| `capture/` | the real sirix-shell sessions behind scenes 3-4 and the scripts that recorded them |
| `build/ansi.py` | converts captured shell output into coloured HTML |

Full how-to: [`EDITING.md`](EDITING.md).
