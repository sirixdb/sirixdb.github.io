"""Exercise CLI subtitle output against worked film-clock examples.

Four seconds of continuous sound and four equally weighted words give one word per second.
The SRT examples use independently authored local cues to reject wrong track transforms.
"""
import array
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

PROJECT = Path(__file__).resolve().parents[1]


class CaptionToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=PROJECT)
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        shutil.copytree(PROJECT / 'tools', self.project / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        (self.project / 'build').mkdir()
        (self.project / 'build/script.json').write_text(json.dumps({
            'beats': [{'text': 'One two six ten.'}, {'text': 'Red tan sky sun.'}],
            'music': {'file': 'video/voice.wav', 'skip_lead_in': 0, 'level_db': -15}
        }))
        self.video = self.project / 'video'
        self.video.mkdir()
        (self.video / "assets").mkdir()
        self.cap = self.video / 'cap.html'
        self.cap.write_text('<template></template>')
        self.audio = self.video / 'voice.wav'
        with wave.open(str(self.audio), 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            wav.writeframes((array.array('h', [6000] * 24 + [-6000] * 24) * 4000).tobytes())

    def index(self, clips='', start=0, offset=0, length=10, total=10, hidden=''):
        (self.video / 'index.html').write_text(f'''
<div data-composition-id="main" data-duration="{total}">
<div data-hf-id="studio-cap" id="cap" data-composition-src="cap.html"
 data-start="{start}" data-media-start="{offset}" data-duration="{length}" {hidden}></div>
{clips}
</div>''')

    def clip(self, beat=1, start=0, offset=0, length=4, extra=''):
        return (f'<audio data-hf-id="studio-voice" id="vo-{beat}" src="voice.wav" '
                f'data-start="{start}" data-media-start="{offset}" '
                f'data-duration="{length}" {extra}></audio>')

    def cli(self, command):
        result = subprocess.run([sys.executable, self.project / 'tools' / command],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_retiming_preserves_both_trim_edges_and_reordered_identity(self):
        self.index(self.clip(1, start=5, length=1) + self.clip(2, start=1, offset=1.5, length=1),
                   start=1, offset=0.5, length=6)
        self.cli('captions.py')
        self.assertEqual(self.cli('srt.py').strip(),
                         '1\n00:00:01,000 --> 00:00:02,000\ntan sky\n\n'
                         '2\n00:00:05,000 --> 00:00:06,000\nOne')

    def test_untrimmed_ordinary_path(self):
        self.index(self.clip())
        self.cli('captions.py')
        self.assertEqual(self.cli('srt.py').strip(),
                         '1\n00:00:00,000 --> 00:00:04,000\nOne two six ten.')

    def test_hidden_zero_length_and_muted_clips_have_no_captions(self):
        for clip in [self.clip(length=0), self.clip(extra='data-hidden="true"'),
                     self.clip(extra='data-volume="0"')]:
            with self.subTest(clip=clip):
                self.index(clip)
                self.cli('captions.py')
                self.assertEqual(self.cli('srt.py').strip(), '')

    def test_silent_source_has_no_captions(self):
        with wave.open(str(self.audio), 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            wav.writeframes(bytes(48000 * 4 * 2))
        self.index(self.clip())
        self.cli('captions.py')
        self.assertEqual(self.cli('srt.py').strip(), '')

    def authored_cues(self):
        self.cap.write_text('''<template>
<div id="cap-g0">Before</div><div id="cap-g1">Middle</div><div id="cap-g2">Last &amp; final</div>
<script>
tl.set("#cap-g0", {visibility: "visible"}, 0.25);
tl.set("#cap-g0", {opacity: 0, visibility: "hidden"}, 0.75);
tl.set("#cap-g1", {visibility: "visible"}, 1);
tl.set("#cap-g1", {opacity: 0, visibility: "hidden"}, 2);
tl.set("#cap-g2", {visibility: "visible"}, 3.5);
tl.set("#cap-g2", {opacity: 0, visibility: "hidden"}, 6);
</script></template>''')

    def test_export_applies_track_offset_and_clips_track_and_film_edges(self):
        self.authored_cues()
        for length, total in [(3, 3.75), (2.75, 10)]:
            with self.subTest(length=length, total=total):
                self.index(start=1, offset=1.5, length=length, total=total)
                self.assertEqual(self.cli('srt.py').strip(),
                                 '1\n00:00:01,000 --> 00:00:01,500\nMiddle\n\n'
                                 '2\n00:00:03,000 --> 00:00:03,750\nLast & final')

    def test_export_shifts_cues_when_track_moves(self):
        self.authored_cues()
        self.index(start=1)
        self.assertIn('00:00:01,250 --> 00:00:01,750\nBefore', self.cli('srt.py'))
        self.index(hidden='data-hidden="true"')
        self.assertEqual(self.cli('srt.py').strip(), '')

    def test_audio_stem_uses_the_same_trim_windows(self):
        self.index(self.clip(length=0) + self.clip(2, start=2, offset=1.5, length=1))
        self.cli('remix.py')
        with wave.open(str(self.project / 'audio/work/vo-full.wav'), 'rb') as wav:
            samples = array.array('h', wav.readframes(wav.getnframes()))
            rate = wav.getframerate()
        self.assertFalse(any(samples[:2 * rate]))
        self.assertTrue(any(samples[2 * rate:3 * rate]))
        self.assertFalse(any(samples[3 * rate:]))

    def render_fixture(self, sound, name='renderer-output.mp4', color='black'):
        renderer_output = self.project / name
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
                        f'color=c={color}:s=64x64:r=30:d=1', '-f', 'lavfi', '-i', sound,
                        '-t', '1', '-c:v', 'libx264', '-c:a', 'aac', str(renderer_output)], check=True)
        return renderer_output

    def render_script(self, renderer_output, quick=False):
        shutil.copy(PROJECT / 'render.sh', self.project / 'render.sh')
        captioned = self.render_fixture('sine=frequency=660:sample_rate=48000',
                                        name='captioned-render.mp4', color='orange')
        bin_dir = self.project / 'bin'
        bin_dir.mkdir()
        renderer = bin_dir / 'npx'
        renderer.write_text(f'''#!{sys.executable}
import os, pathlib, shutil, sys
from html.parser import HTMLParser
class CaptionState(HTMLParser):
    hidden = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id") == "cap":
            self.hidden = "data-hidden" in attrs
state = CaptionState()
state.feed(pathlib.Path("index.html").read_text())
source = os.environ["RENDERER_OUTPUT" if state.hidden else "CAPTIONED_OUTPUT"]
shutil.copyfile(source, sys.argv[sys.argv.index("-o") + 1])
''')
        renderer.chmod(0o755)
        wrapper = bin_dir / 'unused-wrapper'
        wrapper.write_text('#!/bin/sh\nexit 79\n')
        wrapper.chmod(0o755)
        self.index(self.clip(length=1), total=1, length=1)
        result = subprocess.run(['bash', self.project / 'render.sh', *(['--quick'] if quick else [])],
                                capture_output=True, text=True,
                                env=dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'],
                                         RENDERER_OUTPUT=str(renderer_output), CAPTIONED_OUTPUT=str(captioned),
                                         HEAVY=str(wrapper)))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.project / 'out'

    def test_site_export_preserves_silent_renderer_audio(self):
        renderer_output = self.render_fixture('anullsrc=r=48000:cl=stereo')
        out = self.render_script(renderer_output)
        self.assertEqual((out / 'sirixdb-site.mp4').read_bytes(), renderer_output.read_bytes())
        self.assertFalse((self.project / '.render-clean').exists())
        streams = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                                      '-of', 'json', str(out / 'stems/picture-clean.mp4')]))['streams']
        self.assertEqual([s['codec_type'] for s in streams], ['video'])

    def test_site_export_preserves_audible_renderer_audio(self):
        renderer_output = self.render_fixture('sine=frequency=440:sample_rate=48000')
        out = self.render_script(renderer_output)
        self.assertEqual((out / 'sirixdb-site.mp4').read_bytes(), renderer_output.read_bytes())

    def test_quick_render_still_exports_a_draft(self):
        renderer_output = self.render_fixture('sine=frequency=440:sample_rate=48000')
        out = self.render_script(renderer_output, quick=True)
        self.assertEqual((out / 'sirixdb-60s-draft.mp4').read_bytes(),
                         (self.project / 'captioned-render.mp4').read_bytes())
        self.assertFalse((out / 'sirixdb-site.mp4').exists())


if __name__ == '__main__':
    unittest.main()
