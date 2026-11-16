# SirixDB explainer video: source

This is the editable source of the 95-second explainer on the sirix.io landing page
(`assets/video/sirixdb-explainer.mp4`). It is a [HyperFrames](https://hyperframes.heygen.com)
0.9.42 project: every scene is HTML and GSAP, rendered frame by frame, so text, colours, timing and
layout are all plain files. The narration is ElevenLabs Eleven v4 (voice "Holden") generated
through Higgsfield; the film is voice only, with no music by default. The music sources are kept;
see [Music on/off](EDITING.md#everyday-edits-all-free) to enable them. The terminal scenes show a
real `sirix-shell` session.

## Edit it in HyperFrames Studio

Follow [Open it in Studio](EDITING.md#open-it-in-studio) for setup and browser-preview
instructions. Studio writes straight into `video/`, which is the source of truth.

## Re-render

```bash
cd video/sirixdb-explainer
./render.sh
```

Rendering is free. It needs Node 22+, ffmpeg, python3 and Chrome. See
[Re-render](EDITING.md#re-render-free) for output files and the `--quick` draft mode, and
[Publishing a new cut on sirix.io](EDITING.md#publishing-a-new-cut-on-sirixio) to update the site.

## What costs money

Only new audio does, through the Higgsfield CLI. Both scripts show the estimate and ask first.
See [Re-voicing a line](EDITING.md#re-voicing-a-line-costs-higgsfield-credits) and
[New music](EDITING.md#new-music-costs-higgsfield-credits) for the commands and observed costs.

## Layout

| Path | What |
|---|---|
| `video/` | the HyperFrames project (open this in Studio) |
| `build/script.json` | the spoken script, voice, music and pacing settings |
| `tools/` | free helpers: `remix.py` (music ducking), `voice.py` (process a take), `captions.py`, `srt.py` |
| `audio/takes/` | the raw voice takes, one per line |
| `audio/music.m4a` | the retained music source; see [Music on/off](EDITING.md#everyday-edits-all-free) |
| `capture/` | the real sirix-shell sessions behind scenes 3-4 and the scripts that recorded them |
| `build/ansi.py` | converts captured shell output into coloured HTML |

Full how-to: [`EDITING.md`](EDITING.md).
