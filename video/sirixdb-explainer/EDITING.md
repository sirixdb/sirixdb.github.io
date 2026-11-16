# Editing the SirixDB explainer video (Studio first)

The film is a [HyperFrames](https://hyperframes.heygen.com) 0.9.42 project: HTML + GSAP scenes,
rendered frame by frame. **`video/` is the source of truth.** Open it in the HyperFrames Studio
desktop app, change anything, and `./render.sh` renders exactly what Studio shows. Scene and
timeline edits stay in `video/`; the helpers update audio, voice-clip durations and captions.

This folder lives in the website repository at `video/sirixdb-explainer/` (Jekyll does not publish
it; the rendered film is in `assets/video/`). Every edit can be diffed and undone with git:

```bash
git status video/sirixdb-explainer                     # what changed since the last commit
git diff video/sirixdb-explainer/video/                # the exact edits Studio made
git checkout -- video/sirixdb-explainer/video/compositions/s2.html   # throw away an edit
```

## Open it in Studio

Install the HyperFrames desktop app (hyperframes.studio), or use the browser preview below.
From the repository root, run:

```bash
cd video/sirixdb-explainer
python3 tools/remix.py
```

Unless stated otherwise, run the remaining helper and render commands from this directory.
The setup creates `video/assets/music-ducked.wav` (generated rather than committed;
see [Music on/off](#everyday-edits-all-free) for its contents). Then open the folder
**`video/sirixdb-explainer/video/`** (the one with `index.html` and `hyperframes.json`).
Without the desktop app: `(cd video && npm run dev)`
opens the same editor in a browser.

## What is in video/

For current scene times and clip durations, use the Studio timeline or `index.html`.

| File | Scene | What it shows |
|---|---|---|
| `index.html` | root | background (grid + glows), the 8 scene slots, the captions track, the audio clips |
| `compositions/s1.html` | S1 hook | a JSON record; 999 is overwritten by 899 and breaks apart |
| `compositions/s2.html` | S2 keep every version | append-only page tree: each commit adds page fragments + their index path up to a new root; "Storage grows with the change, not the history." |
| `compositions/s3.html` | S3 open any revision | real sirix-shell, four queries typed in step with the voice: by number (`jn:doc(...,1)`), by timestamp (`jn:open(..., xs:dateTime(...))[0].price`), bitemporal (`jn:open-bitemporal('shop','prices', ...)`), and one nested record now vs. its first version (`jn:first($laptop).price`) |
| `compositions/s4.html` | S4 identity and diff | real sirix-shell: `jn:all-times(...)`, then `jn:diff('shop','products',1,3)` with the update, insert and delete entries highlighted as the voice names them |
| `compositions/s5.html` | S5 bitemporal | transaction time x valid time plane (Alice, Berlin to Munich), from the sirix.io diagram |
| `compositions/s6.html` | S6 versioned indexes | path / CAS / name / valid-time indexes "as of rev N", the columnar projection index |
| `compositions/s7.html` | S7 four ways in | embedded library (Java or native C, C++, Rust and Python), REST server, interactive shell, MCP server |
| `compositions/s8.html` | S8 end card | logo, tagline, links |
| `compositions/cap.html` | captions | one spoken phrase at a time (burned in) |
| `assets/vo-scene-1.wav` ... `vo-scene-8.wav` | voice | one clip per scene, `<audio id="vo-1">` ... `<audio id="vo-8">` in `index.html` |
| `assets/music-ducked.wav` | music | generated track for `<audio id="music">`, not committed; see [Music on/off](#everyday-edits-all-free) |

Colours are the sirix.io palette (orange `#F47B20`, blue `#42B6F0`, ground `#0e0f11`), fonts are
Inter and JetBrains Mono. Each scene's styles sit at the top of its file; its animation is the
GSAP timeline at the bottom (`tl.fromTo(...)` / `tl.to(...)`), with times in seconds from the
scene's start. The `C` object at the top of each script holds the moments the voice says key
words (for example `C.storage`); they are plain numbers you can change.

## Everyday edits (all free)

- **Text:** click it in Studio and type, or edit the scene file.
- **Colours, sizes, layout:** the scene file's `<style>`.
- **Timing of an element:** drag its keyframes in Studio, or change the number in its `tl...` line.
- **Scene length:** drag the scene's edges on the timeline, or change `data-start`/`data-duration` of `<div id="s3" ...>` in `index.html`.
- **Voice clips:** move or trim `vo-1` ... `vo-8` on the audio track. `render.sh` rebuilds the music track for their new positions, respecting **Music on/off** below.
- **Captions:** edit the text in `compositions/cap.html`. After moving or trimming voice clips, run `python3 tools/captions.py` to regenerate captions from the beat text in `build/script.json`, using the audible clip windows and current caption-track placement. This replaces manual caption edits and keeps a `cap.html.bak-<time>` copy; review the estimated timings and phrase boundaries afterwards.
- **Music on/off:** set `"enabled"` under `"music"` in `build/script.json`, then run `python3 tools/remix.py`. When `false`, `tools/remix.py` writes a silent `music-ducked.wav`; the music sources stay. Set it to `true` to bring the ducked music back. The published cut is described in [README.md](README.md).
- **Music level:** `"level_db"` under `"music"` in `build/script.json` (default -15; it is read by `tools/remix.py`).

## Re-render (free)

```bash
./render.sh            # out/sirixdb-60s.mp4, sirixdb-site.mp4, sirixdb-60s.srt and poster.png (about 10 min)
./render.sh --quick    # draft-quality MP4 and SRT
```

`render.sh` renders `video/` as it is. Before rendering it rebuilds `assets/music-ducked.wav` for
the current voice positions and film length (`tools/remix.py`). It also derives the SRT from
`compositions/cap.html` (`tools/srt.py`), so the subtitles always match the burned-in captions.

`out/sirixdb-site.mp4` is the clean HyperFrames render, preserving the audio as edited in Studio.
Use it with the separate WebVTT track on sirix.io; `out/sirixdb-60s.mp4` has burned-in captions for other destinations.

## Pace (free)

For the film's current length, use the Studio timeline or `video/index.html`.
The tempo and pause settings under `"timing"` in `build/script.json`
control the voice's pace; after changing one, run `python3 tools/voice.py N` for each line (it rebuilds the clip
from the raw take in `audio/takes/`, no credits), then move the later clips and scenes.

- `"tempo"`: 0.9 plays the voice 10% slower than recorded, pitch unchanged (1.0 = as recorded).
- `"max_pause_in_take"`: pauses inside a line keep their natural length up to this many seconds.
- `python3 tools/voice.py N -16.6` also sets the line's loudness (LUFS); without the number it
  keeps the loudness of the clip it replaces.
- a beat's `"take_pauses"`: sets single pauses of that line by position (seconds before tempo,
  `null` = natural, capped at `"max_pause_in_take"`). Line 3 uses it so each shell query has time
  to run. It is ignored (with a note) when a re-recorded take has a different number of pauses;
  those pauses also use the cap.

The music's source and retiming notes are under `"music"` in `build/script.json`.

Captions show one spoken phrase at a time (a caption that holds a whole list runs seconds ahead of
a slow voice). `tools/captions.py` rebuilds them from the script in coarser groups, so after running
it split the long ones again by hand in `compositions/cap.html`.

## Re-voicing a line (costs Higgsfield credits)

1. In `build/script.json`, change the beat's `"text"` (the caption words) and `"tts"` (what the
   voice reads; "SirixDB" is written "Sirix-DB" so it is spoken as one word, and "bitemporal" as "by-temporal" so it is pronounced right).
2. `./gen_voice.sh 4` (beat 4). It shows the cost estimate and balance and asks first, then:
   - writes the new clip to `video/assets/vo-scene-4.wav` (the old clip is kept in `audio/replaced/`);
   - rebuilds the music track, respecting [Music on/off](#everyday-edits-all-free);
   - tells you whether the line got longer or shorter.

   Observed ElevenLabs v4 cost: about 0.23 credits per line, or about 1.8 credits for all 8.
   Seed Audio costs about 1.4-1.7 credits per line, or about 12-14 credits for all 8.
   Use the displayed estimate before confirming; costs depend on the model and text.
3. In Studio, nudge later clips or scenes if the line's length changed, and fix the caption text
   for that line in `cap.html` (or run `python3 tools/captions.py`).
4. `./render.sh`.

The current model, voice and delivery settings are under `"voice"` in `build/script.json`.
ElevenLabs reads each beat's `"tts"` without a delivery cue.
After re-voicing, transcribe each new take and check that it is English; one early take of the
last line with the previous Seed Audio voice came out in Mandarin.

For the original Seed Audio cut's take provenance, see the historical `"_take"` note on beat 8
in `build/script.json`. Three problems occurred with that voice at the end of a line:
- a list read without "and" ends with the voice lifting the last item as if more followed (the
  pitch of the last word rises);
- a take can say the name with a pause in the middle (a pause inside the first word in the take's
  speech regions);
- the very last word of a recording is often whispered or cut off: below 1 kHz the word "source"
  then has no vowel at all. Giving the voice one more sentence to read after the real ending, and
  cutting that sentence off, keeps the real last word intact; it still took several takes.

For ElevenLabs delivery, edit `"voice"` → `"stability"` and `"similarity_boost"` in
`build/script.json`. For a different voice, use `higgsfield voices list` and update
`"voice"` → `"voice_id"` (and its `"voice_name"` label and `"voice_type"`), then `./gen_voice.sh all`.

To switch back to Seed Audio, set `"voice"` → `"model"` to `"seed_audio"`. That path reads
`"voice"` → `"seed_audio"` → `"voice_id"`, `"voice_type"` and `"delivery"`; edit those nested
fields for a different Seed Audio voice or delivery, then regenerate. The nested configuration
keeps the original Marcus preset. `"delivery"` applies only to Seed Audio and is ignored by ElevenLabs.
Run Higgsfield jobs one at a time: the starter plan rejects a second concurrent job (sometimes as
"not_enough_credits").

## New music (costs Higgsfield credits)

Edit `"music"` → `"prompt"` in `build/script.json`, then `./gen_music.sh`. It shows the estimate (observed: 4
credits for 64 s) and asks first, keeps the old track as `audio/music.<time>.m4a`, and re-ducks the
new one into `video/assets/music-ducked.wav` only when music is enabled; see
[Music on/off](#everyday-edits-all-free). Then `./render.sh`.

## The shell output in scenes 3-4

It is one real `sirix-shell` session (`capture/demo2.ansi`, plain text in `capture/demo2-raw.txt`),
not typed-in text: `python3 capture/capture2.py <out-dir> capture/demo2-queries.json` drove the
shell with the queries in that file (it needs a built sirix checkout's classpath). The coloured
lines in `s3.html`/`s4.html` were generated from it with `build/ansi.py`; scene 4's shell starts
where scene 3's ends (same rows, same scroll position), so change both together. Keep them as they
are unless you re-capture.

Notes from the capture: revision 3 adds the Tablet and deletes the Phone in one commit
(`return (append json ... into $doc, delete json $doc[1])`), so the diff of revisions 1 and 3
holds an update, an insert and a delete; `jn:doc('shop','products')` runs once off screen before
the first shown query so its prompt reads `sirix shop/products@3>`. The `shop/prices` resource is stored with
`{"validFromPath":"validFrom","validToPath":"validTo"}` as the fifth argument of `jn:store`, which
is what `jn:open-bitemporal` needs; the commit timestamp in the queries is the real second between
revision 1 and revision 2 of that run.

## Publishing a new cut on sirix.io

After `./render.sh`, copy the outputs the landing page uses (run from the repository root):

```bash
cp video/sirixdb-explainer/out/sirixdb-site.mp4 assets/video/sirixdb-explainer.mp4   # keep it under ~15 MB
ffmpeg -y -i video/sirixdb-explainer/out/poster.png -q:v 3 assets/video/sirixdb-explainer-poster.jpg
ffmpeg -y -i video/sirixdb-explainer/out/sirixdb-60s.srt assets/video/sirixdb-explainer.en.vtt
```

Re-capturing the shell (`capture/capture2.py`) needs `SIRIX_CLASSPATH_DIR` (a directory with the
`classpath.txt` of a built sirix-query checkout) and `JAVA` (JDK 25).
