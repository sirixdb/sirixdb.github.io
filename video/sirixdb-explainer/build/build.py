#!/usr/bin/env python3
"""Regenerate the SirixDB HyperFrames project from the script and word timings (optional).

video/ is the editable source of truth (edit it in HyperFrames Studio). This generator only
recreates it from scratch: it refuses to touch an existing project unless given --regenerate,
and then backs it up first. Normally run it through build/regenerate.sh.

Usage: build.py <project_dir> <capture.ansi> [words.json] [--regenerate] [--captions-only] [--no-captions]
words.json: [{"text": ..., "start": s, "end": s}, ...] matching SCRIPT word-by-position
(absolute seconds in the final video). Without it, timings are estimated.
"""
import json, re, sys, html, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ansi import parse, to_html

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PROJ = pathlib.Path(ARGS[0]); ANSI = ARGS[1]
WORDS_JSON = ARGS[2] if len(ARGS) > 2 else None

CFG = json.load(open(pathlib.Path(__file__).parent / "script.json"))
BEATS = [(b["scene"], b["text"]) for b in CFG["beats"]]
VO_OFFSET = CFG["timing"]["start"]     # first spoken word (estimate only)
END_HOLD = CFG["timing"]["end_hold"]    # end card hold after the last word

# ---------- words ----------
words = []  # dicts: text, start, end, beat
for bi, (_, text) in enumerate(BEATS):
    for w in text.split():
        words.append({"text": w, "beat": bi})
if WORDS_JSON:
    timed = json.load(open(WORDS_JSON))
    assert len(timed) == len(words), (len(timed), len(words))
    for w, t in zip(words, timed):
        w["start"], w["end"] = float(t["start"]), float(t["end"])
else:
    t = VO_OFFSET
    for i, w in enumerate(words):
        core = re.sub(r"[^\w']", "", w["text"])
        d = 0.11 + 0.037 * len(core)
        w["start"], w["end"] = t, t + d
        t += d
        if w["text"][-1] in ".:": t += 0.36
        elif w["text"][-1] == ",": t += 0.15
        else: t += 0.02
        if i + 1 < len(words) and words[i + 1]["beat"] != w["beat"]: t += 0.8
TOTAL = round(words[-1]["end"] + END_HOLD, 2)

beat_words = [[w for w in words if w["beat"] == b] for b in range(len(BEATS))]
LEAD = 0.35
scene_start = [0.0] + [round(bw[0]["start"] - LEAD, 3) for bw in beat_words[1:]]
scene_end = scene_start[1:] + [TOTAL]

def cue(b, word, nth=1, edge="start"):
    """Scene-local time of the nth word in beat b whose text starts with `word`."""
    n = 0
    for w in beat_words[b]:
        if re.sub(r"[^\w']", "", w["text"]).lower().startswith(word.lower()):
            n += 1
            if n == nth:
                return round(w[edge] - scene_start[b], 3)
    raise KeyError((b, word, nth))

def dur(b): return round(scene_end[b] - scene_start[b], 3)

INIT_SET = re.compile(r"^    tl\.set\((.+?), (\{[^{}]*\}), 0\);$", re.M)


# ---------- palette (sirix.io "Ember Night"); change a value here and re-run ----------
# Keys are the site's original colours; values are what the video uses.
PALETTE = {
    "#0e0f11": "#0e0f11",  # ground
    "#17181b": "#17181b",  # surface (cards, panels)
    "#0b0c0e": "#0b0c0e",  # code / terminal background
    "#ecebe8": "#ecebe8",  # ink
    "#a8afba": "#a8afba",  # secondary text
    "#8b93a1": "#8b93a1",  # muted text
    "#F47B20": "#F47B20",  # orange (accent, changed fragments)
    "#F7924A": "#F7924A",  # orange text
    "#42B6F0": "#42B6F0",  # blue (accent, revision 1, keys)
    "#6CC6F3": "#6CC6F3",  # blue text
    "#98C379": "#98C379",  # shell string green (from the real JLine capture)
    "#34d399": "#34d399",  # insert green
    "#f87171": "#f87171",  # delete / overwrite red
}
def recolour(text):
    for k, v in PALETTE.items():
        if k.lower() != v.lower():
            text = re.sub(re.escape(k), v, text, flags=re.I)
    return text

# ---------- shared style ----------
SHARED_CSS = """
#root { position: absolute; inset: 0; font-family: 'Inter', sans-serif; color: #ecebe8; }
.mono { font-family: 'JetBrains Mono', monospace; }
.kicker { font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #F7924A; }
.h1 { font-size: 76px; font-weight: 800; letter-spacing: -.035em; line-height: 1.06; }
.h2 { font-size: 58px; font-weight: 800; letter-spacing: -.03em; line-height: 1.08; }
.grad { background: linear-gradient(100deg, #F47B20 10%, #42B6F0 90%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.sub { font-size: 28px; color: #a8afba; line-height: 1.4; }
.panel { background: #17181b; border: 1px solid rgba(255,255,255,.12); border-radius: 14px; box-shadow: 0 24px 60px -24px rgba(0,0,0,.7); }
.chip { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 28px; padding: 8px 16px; border-radius: 99px; border: 1px solid rgba(255,255,255,.18); color: #a8afba; background: #17181b; }
.a-k { color: #42B6F0; } .a-o { color: #F47B20; } .a-s { color: #98C379; } .a-d { color: #8b93a1; }
"""

def scene(sid, body, script, extra_css="", cues=None):
    cues = cues or {}
    script = INIT_SET.sub(r"    gsap.set(\1, \2);", script)
    return f"""<template>
  <style>{SHARED_CSS}{extra_css}</style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
{body}
  </div>
  <script>
    const C = {json.dumps(cues)};
    const D = {dur(int(sid[1:]) - 1)};
    const tl = gsap.timeline({{ paused: true }});
{script}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""

def blur_in(sel, t, d=0.5, y=0, ease="expo.out", blur=8):
    return f'    tl.fromTo("{sel}", {{opacity: 0, y: {y}, filter: "blur({blur}px)"}}, {{opacity: 1, y: 0, filter: "blur(0px)", duration: {d}, ease: "{ease}"}}, {t});\n'

def blur_out(sel, t, d=0.25):
    return f'    tl.to("{sel}", {{opacity: 0, filter: "blur(8px)", duration: {d}, ease: "power3.in"}}, {t});\n'

# ---------- S1: the overwrite ----------
def s1():
    b = 0
    c = dict(update=cue(b, "update"), record=cue(b, "record"), old=cue(b, "old"), gone=cue(b, "gone"), end=dur(b))
    css = """
#s1-wrap { position: absolute; left: 0; top: 0; width: 1920px; height: 900px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 34px; }
#s1-card { font-size: 66px; line-height: 1.45; padding: 44px 64px; min-width: 820px; }
#s1-card .ind { padding-left: 1.2em; }
#s1-slot { position: relative; display: inline-block; width: 3ch; height: 1.2em; vertical-align: top; }
#s1-old, #s1-new { position: absolute; left: 0; top: 0; white-space: nowrap; }
#s1-old span { display: inline-block; }
#s1-strike { position: absolute; left: -4px; top: 52%; height: 6px; width: calc(100% + 8px); background: #f87171; border-radius: 3px; transform-origin: left center; }
#s1-note { font-size: 28px; color: #f2a3a3; }
"""
    body = """    <div id="s1-wrap">
      <div id="s1-kick" class="kicker">update in place</div>
      <div id="s1-card" class="panel mono">
        <div>{</div>
        <div class="ind"><span class="a-k">"name"</span>: <span class="a-s">"Laptop"</span>,</div>
        <div class="ind"><span class="a-k">"price"</span>: <span id="s1-slot"><span id="s1-old" class="a-o"><span id="s1-d1">9</span><span id="s1-d2">9</span><span id="s1-d3">9</span><span id="s1-strike"></span></span><span id="s1-new" class="a-o">899</span></span></div>
        <div>}</div>
      </div>
      <div id="s1-note" class="mono">previous value: overwritten &middot; no history</div>
    </div>"""
    js = ""
    js += '    tl.set("#s1-new", {opacity: 0, y: -70}, 0);\n    tl.set("#s1-strike", {scaleX: 0}, 0);\n    tl.set("#s1-note", {opacity: 0}, 0);\n'
    # 899 lands on "record"; 999 pushed down and struck through
    js += '    tl.to("#s1-old", {y: 64, duration: 0.45, ease: "power3.out"}, C.record - 0.1);\n'
    js += '    tl.to("#s1-new", {opacity: 1, y: 0, duration: 0.45, ease: "expo.out"}, C.record - 0.1);\n'
    js += '    tl.to("#s1-strike", {scaleX: 1, duration: 0.3, ease: "power2.out"}, C.old);\n'
    js += '    tl.to("#s1-old", {color: "#f87171", duration: 0.2}, C.old);\n'
    # 999 breaks apart on "gone"
    for i, (dx, dy, r) in enumerate([(-60, 90, -24), (10, 130, 14), (70, 80, 30)], 1):
        js += f'    tl.to("#s1-d{i}", {{x: {dx}, y: {dy}, rotation: {r}, opacity: 0, filter: "blur(10px)", duration: 0.9, ease: "power2.in"}}, C.gone + {0.04*i:.2f});\n'
    js += '    tl.to("#s1-strike", {opacity: 0, duration: 0.4}, C.gone + 0.1);\n'
    js += blur_in("#s1-note", "C.old + 0.1", 0.45)
    # exit: card shrinks toward the stack's top layer (scene 2)
    js += '    tl.to(["#s1-kick", "#s1-note"], {opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power3.in"}, D - 0.55);\n'
    js += '    tl.to("#s1-card", {scale: 0.32, x: 370, y: -150, opacity: 0, filter: "blur(4px)", duration: 0.55, ease: "power3.in"}, D - 0.6);\n'
    return scene("s1", body, js, css, c)

# ---------- S2: the revision stack ----------
def iso(cx, cy, u, v, hw=270, hh=135):
    return (cx + (u - v) * hw, cy + (u + v - 1) * hh)

def s2():
    b = 1
    c = dict(sirix=cue(b, "SirixDB"), every=cue(b, "every"), commit=cue(b, "commit"), only=cue(b, "only"),
             shares=cue(b, "shares"), storage=cue(b, "storage"), notw=cue(b, "not"), end=dur(b))
    cx, base, gap = 1300, 715, 100
    frag = {1: (0, 0), 2: (2, 0), 3: (0, 2), 4: (2, 2)}  # cells chosen so no two fragments overlap on screen
    svg = []
    for k in range(5):
        cy = base - k * gap
        g = [f'<g id="s2-L{k}">']
        outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in [iso(cx, cy, 0, 0), iso(cx, cy, 1, 0), iso(cx, cy, 1, 1), iso(cx, cy, 0, 1)])
        g.append(f'<polygon points="{outline}" fill="{"rgba(66,182,240,.06)" if k == 0 else "rgba(14,15,17,.25)"}" stroke="{"#42B6F0" if k == 0 else "rgba(255,255,255,.22)"}" stroke-width="1.5"/>')
        for i in range(3):
            for j in range(3):
                e = 0.025
                pts = [iso(cx, cy, i/3+e, j/3+e), iso(cx, cy, (i+1)/3-e, j/3+e), iso(cx, cy, (i+1)/3-e, (j+1)/3-e), iso(cx, cy, i/3+e, (j+1)/3-e)]
                p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                if k == 0:
                    g.append(f'<polygon points="{p}" fill="rgba(66,182,240,.16)" stroke="#42B6F0" stroke-width="1.4"/>')
                elif frag[k] == (i, j):
                    g.append(f'<polygon id="s2-F{k}" points="{p}" fill="#F47B20"/>')
                else:
                    g.append(f'<polygon points="{p}" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.2" stroke-dasharray="5 5"/>')
        rx, ry = iso(cx, cy, 1, 0)
        g.append(f'<text x="{rx + 34:.0f}" y="{ry + 9:.0f}" class="s2-lab" id="s2-T{k}">rev {k + 1}</text>')
        g.append('</g>')
        svg.append("".join(g))
    css = """
#s2-svg { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
.s2-lab { font-family: 'JetBrains Mono', monospace; font-size: 26px; fill: #a8afba; }
#s2-left { position: absolute; left: 130px; top: 250px; width: 820px; }
#s2-kick { margin-bottom: 28px; }
#s2-fact { margin-top: 34px; font-size: 28px; color: #a8afba; }
#s2-fact b { color: #ecebe8; font-weight: 600; }
#s2-call { position: absolute; right: 110px; top: 96px; width: 420px; padding: 18px 24px; }
#s2-call .q { font-family: 'JetBrains Mono', monospace; font-size: 27px; color: #ecebe8; }
#s2-call .s { font-size: 26px; color: #a8afba; margin-top: 6px; }
"""
    body = f"""    <svg id="s2-svg" viewBox="0 0 1920 1080">{''.join(svg)}</svg>
    <div id="s2-left">
      <div id="s2-kick" class="kicker">SirixDB &middot; every commit is a revision</div>
      <div id="s2-h1" class="h1">Storage grows<br>with the change,</div>
      <div id="s2-h2" class="h1 grad">not the history.</div>
      <div id="s2-fact" class="mono"><b>O(changed records)</b> per revision &middot; unchanged pages shared</div>
    </div>
    <div id="s2-call" class="panel"><div class="q">commit &rarr; new revision</div><div class="s">writes only what changed,<br>shares the rest</div></div>"""
    js = ""
    js += blur_in("#s2-kick", "C.sirix", 0.5)
    js += '    tl.fromTo("#s2-L0", {opacity: 0, y: 40}, {opacity: 1, y: 0, duration: 0.8, ease: "expo.out"}, C.sirix + 0.1);\n'
    span = max(0.6, (c["shares"] - c["commit"]) / 4)
    for k in range(1, 5):
        t = f"C.commit + {span * (k - 1):.2f}"
        js += f'    tl.fromTo("#s2-L{k}", {{opacity: 0, y: -70}}, {{opacity: 1, y: 0, duration: 0.6, ease: "expo.out"}}, {t});\n'
        js += f'    tl.fromTo("#s2-F{k}", {{opacity: 0}}, {{opacity: 1, duration: 0.25, ease: "power2.out"}}, {t} + 0.3);\n'
    js += blur_in("#s2-call", "C.commit + 0.2", 0.5, y=-12)
    js += blur_in("#s2-h1", "C.storage - 0.05", 0.5)
    js += blur_in("#s2-h2", "C.notw - 0.05", 0.5)
    js += blur_in("#s2-fact", "C.storage + 0.5", 0.5)
    # exit: everything but rev 1 lifts away; rev 1 lights up
    js += '    tl.to(["#s2-left", "#s2-call"], {opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power3.in"}, D - 0.5);\n'
    js += '    tl.to(["#s2-L1", "#s2-L2", "#s2-L3", "#s2-L4"], {opacity: 0, y: -60, duration: 0.4, ease: "power3.in", stagger: -0.05}, D - 0.55);\n'
    js += '    tl.to("#s2-L0", {opacity: 0, scale: 1.08, transformOrigin: "50% 50%", duration: 0.35, ease: "power3.in"}, D - 0.35);\n'
    return scene("s2", body, js, css, c)

# ---------- shell panel (S3, S4) ----------
SHELL_CSS = """
.shell { position: absolute; left: 80px; top: 92px; width: 1240px; height: 800px; background: #0b0c0e; border: 1px solid rgba(255,255,255,.12); border-radius: 14px; overflow: hidden; box-shadow: 0 24px 60px -24px rgba(0,0,0,.7); }
.shell-head { height: 52px; display: flex; align-items: center; gap: 10px; padding: 0 22px; background: #17181b; border-bottom: 1px solid rgba(255,255,255,.09); font-family: 'JetBrains Mono', monospace; font-size: 24px; color: #8b93a1; }
.shell-head i { width: 13px; height: 13px; border-radius: 50%; background: rgba(255,255,255,.16); display: inline-block; }
.shell-head span { margin-left: 12px; }
.shell-view { position: absolute; left: 0; top: 52px; right: 0; bottom: 0; overflow: hidden; }
.shell-lines { position: absolute; left: 26px; top: 18px; right: 20px; font-family: 'JetBrains Mono', monospace; font-size: 25px; line-height: 31px; white-space: pre; color: #ecebe8; }
.ln { height: 31px; position: relative; }
.ln .hl { position: absolute; left: -12px; right: -6px; top: 0; bottom: 0; border-radius: 4px; }
.side { position: absolute; left: 1370px; top: 110px; width: 490px; }
.side .h2 { font-size: 52px; }
.side .kicker { margin-bottom: 22px; }
.card { margin-top: 22px; padding: 18px 22px; }
.card .l { font-size: 24px; color: #8b93a1; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }
.card .c { font-family: 'JetBrains Mono', monospace; font-size: 26px; color: #ecebe8; margin-top: 6px; line-height: 1.35; }
"""
LH = 31; VIEW_LINES = 22

def shell_lines(blocks, prefix):
    """Flatten capture blocks into (html, kind) rows; kinds: prompt / out / blank."""
    rows = []
    for bi, blk in enumerate(blocks):
        if rows: rows.append(("", "blank", bi))
        for li, spans in enumerate(blk):
            text = "".join(t for _, t in spans)
            kind = "prompt" if text.startswith("sirix") or (li > 0 and text.startswith("return")) else "out"
            rows.append((to_html(spans), kind, bi))
    return rows

def render_rows(rows, prefix):
    out = []
    for i, (h, kind, bi) in enumerate(rows):
        hl = f'<div class="hl" id="{prefix}-hl{i}"></div>'
        out.append(f'<div class="ln" id="{prefix}-r{i}">{hl}<span class="tx">{h}</span></div>')
    return "".join(out)

def type_rows(rows, prefix, idx_list, t0, cps=55):
    """Typing reveal (clip-path) for prompt rows; returns js and end time expression offset."""
    js = ""; t = 0.0
    for i in idx_list:
        n = len(re.sub(r"<[^>]+>", "", html.unescape(rows[i][0])))
        d = max(0.25, (n - 23 if rows[i][0].find("sirix") >= 0 else n) / cps)
        js += f'    tl.fromTo("#{prefix}-r{i} .tx", {{clipPath: "inset(0 100% 0 0)"}}, {{clipPath: "inset(0 0% 0 0)", duration: {d:.2f}, ease: "none"}}, {t0} + {t:.2f});\n'
        t += d + 0.05
    return js, t

def print_rows(prefix, idx_list, t0, step=0.022):
    return f'    tl.fromTo([{",".join(chr(34)+"#"+prefix+"-r"+str(i)+chr(34) for i in idx_list)}], {{opacity: 0}}, {{opacity: 1, duration: 0.01, stagger: {step}}}, {t0});\n'

def shell_head(prefix):
    return f'<div class="shell-head"><i></i><i></i><i></i><span>sirix-shell &middot; real session capture</span></div>'

def s3(blocks):
    b = 2
    c = dict(any=cue(b, "Any"), number=cue(b, "number"), timestamp=cue(b, "timestamp"), nothing=cue(b, "Nothing"),
             revision=cue(b, "revision", 2), latest=cue(b, "latest"), end=dur(b))
    rows = shell_lines([blocks[3]], "s3")
    body = f"""    <div class="shell" id="s3-shell">{shell_head("s3")}<div class="shell-view"><div class="shell-lines" id="s3-lines">
{render_rows(rows, "s3")}
    </div></div></div>
    <div class="side" id="s3-side">
      <div id="s3-kick" class="kicker">open any revision</div>
      <div id="s3-h" class="h2">Revision 1 reads <span class="grad">like the latest.</span></div>
      <div id="s3-c1" class="card panel"><div class="l">by number</div><div class="c">jn:doc('shop','products',1)</div></div>
      <div id="s3-c2" class="card panel"><div class="l">by timestamp</div><div class="c">jn:open('shop','products',<br>&nbsp;&nbsp;xs:dateTime(<br>&nbsp;&nbsp;&nbsp;&nbsp;'2024-01-15T10:30:00Z'))</div></div>
      <div id="s3-c3" class="card panel"><div class="l">no replay</div><div class="c">&le; 3 page fragments per read<br><span class="a-d">(default sliding-snapshot window)</span></div></div>
    </div>"""
    js = '    tl.fromTo("#s3-shell", {opacity: 0, y: 30, filter: "blur(8px)"}, {opacity: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out"}, 0);\n'
    js += f'    tl.set([{",".join(chr(34)+"#s3-r"+str(i)+chr(34) for i in range(len(rows)))}], {{opacity: 0}}, 0);\n'
    js += '    tl.set("#s3-r0", {opacity: 1}, 0.35);\n'
    tj, tt = type_rows(rows, "s3", [0], "0.35")
    js += tj
    js += print_rows("s3", list(range(1, len(rows))), f"0.35 + {tt + 0.25:.2f}")
    js += blur_in("#s3-kick", "C.any", 0.5)
    js += blur_in("#s3-c1", "C.number - 0.1", 0.5, y=14)
    js += blur_in("#s3-c2", "C.timestamp - 0.1", 0.5, y=14)
    js += blur_in("#s3-c3", "C.nothing - 0.05", 0.5, y=14)
    js += blur_in("#s3-h", "C.revision - 0.05", 0.5)
    js += '    tl.to("#s3-hl5", {background: "rgba(66,182,240,.12)", duration: 0.3}, C.revision);\n'
    js += '    tl.to("#s3-side", {opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power3.in"}, D - 0.3);\n'
    return scene("s3", body, js, SHELL_CSS, c), rows

def s4(blocks):
    b = 3
    c = dict(every=cue(b, "Every"), identity=cue(b, "identity"), follow=cue(b, "Follow"), diff=cue(b, "diff"),
             inserts=cue(b, "inserts"), updates=cue(b, "updates"), deletes=cue(b, "deletes"), end=dur(b))
    rows = shell_lines([blocks[3], blocks[4], blocks[5]], "s4")
    n3 = len(blocks[3]); n4 = len(blocks[4])
    b4 = list(range(n3 + 1, n3 + 1 + n4)); b5 = list(range(n3 + 2 + n4, len(rows)))
    find = lambda s: next(i for i, r in enumerate(rows) if s in re.sub(r"<[^>]+>", "", html.unescape(r[0])))
    up0 = find('"update"'); up1 = up0 + 5; ins0 = find('"insert"'); ins1 = ins0 + 7
    body = f"""    <div class="shell" id="s4-shell">{shell_head("s4")}<div class="shell-view"><div class="shell-lines" id="s4-lines">
{render_rows(rows, "s4")}
    </div></div></div>
    <div class="side" id="s4-side">
      <div id="s4-kick" class="kicker">node-level identity</div>
      <div id="s4-h" class="h2">Every field keeps <span class="grad">its identity.</span></div>
      <div id="s4-c1" class="card panel"><div class="l">one value through time</div><div class="c">jn:all-times(&hellip;)</div></div>
      <div id="s4-c2" class="card panel"><div class="l">any two revisions</div><div class="c">jn:diff('shop','products',1,3)</div></div>
      <div id="s4-kinds" style="margin-top: 26px; display: flex; gap: 12px;">
        <span class="chip" id="s4-k1">insert</span><span class="chip" id="s4-k2">update</span><span class="chip" id="s4-k3">delete</span>
      </div>
    </div>"""
    js = f'    tl.set("#s4-lines", {{y: 0}}, 0);\n'
    js += f'    tl.set([{",".join(chr(34)+"#s4-r"+str(i)+chr(34) for i in b4 + b5)}], {{opacity: 0}}, 0);\n'
    t_a = "C.every"  # all-times query starts typing with the beat
    js += f'    tl.set("#s4-r{b4[0]}", {{opacity: 1}}, {t_a});\n'
    js += f'    tl.set("#s4-r{b4[1]}", {{opacity: 1}}, {t_a});\n'
    tj, tt = type_rows(rows, "s4", b4[:2], t_a, cps=60)
    js += tj
    # scroll so the all-times block ends at the bottom
    s1 = max(0, (b4[-1] + 1) - VIEW_LINES)
    js += f'    tl.to("#s4-lines", {{y: {-s1 * LH}, duration: 0.5, ease: "power2.inOut"}}, {t_a} + 0.2);\n'
    js += print_rows("s4", b4[2:], f"{t_a} + {tt + 0.2:.2f}")
    js += f'    tl.to("#s4-hl{b4[5]}", {{background: "rgba(244,123,32,.14)", duration: 0.25}}, C.follow + 0.2);\n'
    js += f'    tl.to("#s4-hl{b4[8]}", {{background: "rgba(244,123,32,.14)", duration: 0.25}}, C.follow + 0.35);\n'
    js += f'    tl.to("#s4-hl{b4[11]}", {{background: "rgba(244,123,32,.14)", duration: 0.25}}, C.follow + 0.5);\n'
    # diff query
    t_d = "C.diff - 0.35"
    s2_ = max(0, (b5[-1] + 1) - VIEW_LINES)
    js += f'    tl.set("#s4-r{b5[0]}", {{opacity: 1}}, {t_d});\n'
    tj2, tt2 = type_rows(rows, "s4", b5[:1], t_d, cps=60)
    js += tj2
    js += print_rows("s4", b5[1:], f"{t_d} + {tt2 + 0.15:.2f}", step=0.012)
    js += f'    tl.to("#s4-lines", {{y: {-s2_ * LH}, duration: 0.6, ease: "power2.inOut"}}, {t_d} + {tt2 + 0.25:.2f});\n'
    for i in range(ins0, ins1 + 1):
        js += f'    tl.to("#s4-hl{i}", {{background: "rgba(152,195,121,.16)", duration: 0.25}}, C.inserts);\n'
    for i in range(up0, up1 + 1):
        js += f'    tl.to("#s4-hl{i}", {{background: "rgba(244,123,32,.16)", duration: 0.25}}, C.updates);\n'
    js += blur_in("#s4-kick", "C.every", 0.5)
    js += blur_in("#s4-h", "C.identity - 0.1", 0.5)
    js += blur_in("#s4-c1", "C.follow - 0.1", 0.5, y=14)
    js += blur_in("#s4-c2", "C.diff - 0.1", 0.5, y=14)
    js += '    tl.set(["#s4-k1", "#s4-k2", "#s4-k3"], {opacity: 0}, 0);\n'
    js += '    tl.fromTo("#s4-k1", {opacity: 0, scale: .8}, {opacity: 1, scale: 1, color: "#34d399", borderColor: "rgba(52,211,153,.6)", backgroundColor: "rgba(52,211,153,.13)", duration: 0.35, ease: "back.out(1.6)"}, C.inserts);\n'
    js += '    tl.fromTo("#s4-k2", {opacity: 0, scale: .8}, {opacity: 1, scale: 1, color: "#F7924A", borderColor: "rgba(244,123,32,.6)", backgroundColor: "rgba(244,123,32,.14)", duration: 0.35, ease: "back.out(1.6)"}, C.updates);\n'
    js += '    tl.fromTo("#s4-k3", {opacity: 0, scale: .8}, {opacity: 1, scale: 1, color: "#f87171", borderColor: "rgba(248,113,113,.6)", backgroundColor: "rgba(248,113,113,.13)", duration: 0.35, ease: "back.out(1.6)"}, C.deletes);\n'
    js += '    tl.to(["#s4-shell", "#s4-side"], {opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power3.in"}, D - 0.3);\n'
    return scene("s4", body, js, SHELL_CSS, c)

# ---------- S5: bitemporal plane ----------
def s5():
    b = 4
    c = dict(bitemporal=cue(b, "bitemporal"), recorded=cue(b, "recorded"), true=cue(b, "true"),
             correction=cue(b, "correction"), knew=cue(b, "knew"), end=dur(b))
    css = """
#s5-svg { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
#s5-svg text { font-family: 'Inter', sans-serif; }
.s5-ax { stroke: #a8afba; stroke-width: 2; }
.s5-at { font-size: 26px; fill: #a8afba; }
.s5-rt { font-size: 40px; font-weight: 800; letter-spacing: -.02em; }
.s5-rs { font-size: 26px; fill: #a8afba; }
.s5-tick { font-family: 'JetBrains Mono', monospace; font-size: 26px; fill: #ecebe8; }
#s5-left { position: absolute; left: 110px; top: 200px; width: 690px; }
#s5-left .kicker { margin-bottom: 26px; }
#s5-code { margin-top: 30px; font-size: 25px; line-height: 1.5; padding: 18px 22px; }
#s5-ans { margin-top: 26px; padding: 18px 22px; height: 128px; position: relative; }
#s5-ans .q { font-size: 27px; color: #a8afba; }
#s5-ans .a { font-size: 44px; font-weight: 800; letter-spacing: -.02em; margin-top: 4px; }
.s5-ansset { position: absolute; left: 22px; top: 18px; right: 22px; }
"""
    ox, oy, x1, ytop = 840, 800, 1810, 150
    xb = 1430  # Mar 10 in transaction time (the correction is recorded)
    yb = 470   # Mar 1 in valid time (Munich from here up)
    xq1, xq2, yq = 1150, 1660, 360
    svg = f"""    <svg id="s5-svg" viewBox="0 0 1920 1080">
      <g id="s5-regs">
        <rect id="s5-r1" x="{ox+14}" y="{ytop+14}" width="{xb-ox-18}" height="{oy-ytop-28}" rx="8" fill="rgba(66,182,240,.13)" stroke="rgba(66,182,240,.55)" stroke-width="1.5"/>
        <text id="s5-r1t" x="{(ox+xb)/2:.0f}" y="{(ytop+oy)/2 + 40:.0f}" text-anchor="middle"><tspan class="s5-rt" fill="#6CC6F3">Berlin</tspan><tspan class="s5-rs" x="{(ox+xb)/2:.0f}" dy="36">rev 1 &middot; move not reported yet</tspan></text>
        <rect id="s5-r2" x="{xb+4}" y="{ytop+14}" width="{x1-xb-24}" height="{yb-ytop-18}" rx="8" fill="rgba(244,123,32,.15)" stroke="rgba(244,123,32,.6)" stroke-width="1.5"/>
        <text id="s5-r2t" x="{(xb+x1)/2:.0f}" y="{(ytop+yb)/2 - 6:.0f}" text-anchor="middle"><tspan class="s5-rt" fill="#F7924A">Munich</tspan><tspan class="s5-rs" x="{(xb+x1)/2:.0f}" dy="34">rev 2 &middot; from Mar 1</tspan></text>
        <rect id="s5-r3" x="{xb+4}" y="{yb+4}" width="{x1-xb-24}" height="{oy-yb-18}" rx="8" fill="rgba(66,182,240,.13)" stroke="rgba(66,182,240,.55)" stroke-width="1.5"/>
        <text id="s5-r3t" x="{(xb+x1)/2:.0f}" y="{(yb+oy)/2 + 4:.0f}" text-anchor="middle"><tspan class="s5-rt" fill="#6CC6F3">Berlin</tspan><tspan class="s5-rs" x="{(xb+x1)/2:.0f}" dy="34">rev 2 &middot; until Mar 1</tspan></text>
      </g>
      <g id="s5-xax"><line class="s5-ax" x1="{ox}" y1="{oy}" x2="{x1+10}" y2="{oy}"/><polygon points="{x1+18},{oy} {x1+4},{oy-8} {x1+4},{oy+8}" fill="#a8afba"/>
        <text class="s5-at" x="{(ox+x1)/2:.0f}" y="{oy+52}" text-anchor="middle">transaction time &mdash; when SirixDB recorded it &rarr;</text>
        <text class="s5-tick" x="{xb}" y="{oy+26}" text-anchor="middle" id="s5-mar10">Mar 10</text></g>
      <g id="s5-yax"><line class="s5-ax" x1="{ox}" y1="{oy}" x2="{ox}" y2="{ytop-14}"/><polygon points="{ox},{ytop-22} {ox-8},{ytop-8} {ox+8},{ytop-8}" fill="#a8afba"/>
        <text class="s5-at" x="{ox-26}" y="{(ytop+oy)/2:.0f}" text-anchor="middle" transform="rotate(-90 {ox-26} {(ytop+oy)/2:.0f})">valid time &mdash; when it was true &rarr;</text>
        <text class="s5-tick" x="{ox+12}" y="{yb-8}" id="s5-mar1">Mar 1</text></g>
      <g id="s5-xh">
        <line id="s5-v" x1="{xq1}" y1="{oy}" x2="{xq1}" y2="{ytop}" stroke="#ecebe8" stroke-width="2" stroke-dasharray="6 6"/>
        <line id="s5-h" x1="{ox}" y1="{yq}" x2="{x1}" y2="{yq}" stroke="#ecebe8" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/>
        <circle id="s5-dot" cx="{xq1}" cy="{yq}" r="10" fill="#ecebe8"/>
        <circle id="s5-ring" cx="{xq1}" cy="{yq}" r="22" fill="none" stroke="#ecebe8" stroke-width="2" opacity=".5"/>
      </g>
    </svg>"""
    body = svg + """
    <div id="s5-left">
      <div id="s5-kick" class="kicker">native valid time</div>
      <div id="s5-h1" class="h1">Two kinds of time.</div>
      <div id="s5-h2" class="h1 grad">One query.</div>
      <div id="s5-code" class="panel mono"><span class="a-k">jn:open-bitemporal</span>(<span class="a-s">'crm'</span>,<span class="a-s">'customers'</span>,<br>&nbsp;&nbsp;<span class="a-d">recorded,</span> <span class="a-d">valid</span>)</div>
      <div id="s5-ans" class="panel">
        <div class="s5-ansset" id="s5-a1"><div class="q">Alice, recorded Mar 5 &middot; valid Mar 5</div><div class="a" style="color:#6CC6F3">Berlin <span style="font-size:27px;font-weight:500;color:#a8afba">what you knew then</span></div></div>
        <div class="s5-ansset" id="s5-a2"><div class="q">Alice, recorded today &middot; valid Mar 5</div><div class="a" style="color:#F7924A">Munich <span style="font-size:27px;font-weight:500;color:#a8afba">what was true</span></div></div>
      </div>
    </div>"""
    js = ""
    js += blur_in("#s5-kick", 0.0, 0.45)
    js += blur_in("#s5-h1", "C.bitemporal - 0.1", 0.5)
    js += '    tl.fromTo("#s5-xax", {opacity: 0}, {opacity: 1, duration: 0.5, ease: "power2.out"}, C.recorded - 0.2);\n'
    js += '    tl.fromTo("#s5-yax", {opacity: 0}, {opacity: 1, duration: 0.5, ease: "power2.out"}, C.true - 0.3);\n'
    js += '    tl.fromTo("#s5-r1", {opacity: 0, scaleX: 0.6, transformOrigin: "0% 50%"}, {opacity: 1, scaleX: 1, duration: 0.7, ease: "expo.out"}, C.recorded);\n'
    js += '    tl.fromTo("#s5-r1t", {opacity: 0}, {opacity: 1, duration: 0.4}, C.recorded + 0.3);\n'
    js += blur_in("#s5-h2", "C.true - 0.05", 0.5)
    js += blur_in("#s5-code", "C.true + 0.4", 0.5, y=14)
    # the correction arrives (recorded Mar 10, effective Mar 1)
    js += '    tl.fromTo(["#s5-r2", "#s5-r3"], {opacity: 0, scaleX: 0.6, transformOrigin: "0% 50%"}, {opacity: 1, scaleX: 1, duration: 0.7, ease: "expo.out", stagger: 0.08}, C.correction - 0.1);\n'
    js += '    tl.fromTo(["#s5-r2t", "#s5-r3t", "#s5-mar10", "#s5-mar1"], {opacity: 0}, {opacity: 1, duration: 0.4}, C.correction + 0.2);\n'
    # crosshair: what you knew then -> what was true
    js += '    tl.fromTo("#s5-xh", {opacity: 0}, {opacity: 1, duration: 0.35}, C.correction + 0.6);\n'
    js += blur_in("#s5-ans", "C.correction + 0.6", 0.45, y=10)
    js += '    tl.fromTo("#s5-a1", {opacity: 0}, {opacity: 1, duration: 0.3}, C.correction + 0.75);\n'
    js += '    tl.set("#s5-a2", {opacity: 0}, 0);\n'
    move_t = "Math.max(C.knew + 0.35, C.correction + 2.0)"
    js += f'    tl.to("#s5-v", {{attr: {{x1: {xq2}, x2: {xq2}}}, duration: 0.8, ease: "power2.inOut"}}, {move_t});\n'
    js += f'    tl.to(["#s5-dot", "#s5-ring"], {{attr: {{cx: {xq2}}}, duration: 0.8, ease: "power2.inOut"}}, {move_t});\n'
    js += f'    tl.to("#s5-a1", {{opacity: 0, duration: 0.2}}, {move_t} + 0.3);\n'
    js += f'    tl.to("#s5-a2", {{opacity: 1, duration: 0.3}}, {move_t} + 0.6);\n'
    js += '    tl.to(["#s5-svg", "#s5-left"], {opacity: 0, filter: "blur(8px)", duration: 0.3, ease: "power3.in"}, D - 0.3);\n'
    return scene("s5", body, js, css, c)

# ---------- S6: versioned indexes ----------
def s6():
    b = 5
    c = dict(indexes=cue(b, "indexes"), versioned=cue(b, "versioned"), columnar=cue(b, "columnar"),
             analytics=cue(b, "analytics"), revision=cue(b, "revision"), end=dur(b))
    idx = [("path", "navigate JSON paths"), ("CAS", "typed values, range lookups"), ("name", "object keys"),
           ("valid-time", "interval index for valid time")]
    cards = "\n".join(f'      <div class="s6-card panel" id="s6-c{i}"><div class="n">{n}</div><div class="d">{d}</div><div class="rv mono">' +
                      "".join(f'<span class="s6-rv{r}">as of rev {r}</span>' for r in range(1, 6)) + '</div></div>'
                      for i, (n, d) in enumerate(idx))
    cols = ["age", "active", "dept", "city"]
    heights = [[62, 40, 75, 52, 30, 68], [20, 20, 20, 20, 20, 20], [48, 70, 36, 58, 44, 64], [55, 33, 72, 41, 60, 38]]
    colhtml = "".join(f'<div class="col"><div class="bars">' + "".join(f'<i style="height:{h}px"></i>' for h in heights[k]) +
                      f'</div><div class="cn mono">{cols[k]}</div></div>' for k in range(4))
    css = """
#s6-left { position: absolute; left: 120px; top: 230px; width: 700px; }
#s6-left .kicker { margin-bottom: 26px; }
#s6-sub { margin-top: 28px; }
#s6-scrub { position: absolute; left: 900px; top: 120px; display: flex; gap: 10px; align-items: center; }
#s6-scrub .lab { font-family: 'JetBrains Mono', monospace; font-size: 27px; color: #8b93a1; margin-right: 10px; }
#s6-scrub .p { width: 64px; height: 44px; border-radius: 10px; border: 1px solid rgba(255,255,255,.18); display: flex; align-items: center; justify-content: center; font-family: 'JetBrains Mono', monospace; font-size: 24px; color: #a8afba; }
#s6-grid { position: absolute; left: 900px; top: 200px; width: 900px; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.s6-card { padding: 18px 22px; position: relative; height: 128px; }
.s6-card .n { font-size: 32px; font-weight: 700; }
.s6-card .d { font-size: 26px; color: #a8afba; margin-top: 2px; }
.s6-card .rv { position: absolute; right: 18px; top: 20px; font-size: 26px; color: #6CC6F3; width: 220px; height: 30px; text-align: right; white-space: nowrap; }
.s6-card .rv span { position: absolute; right: 0; top: 0; }
#s6-proj { position: absolute; left: 900px; top: 500px; width: 900px; height: 300px; padding: 20px 24px; }
#s6-proj .n { font-size: 32px; font-weight: 700; }
#s6-proj .d { font-size: 26px; color: #a8afba; }
#s6-proj .tag { position: absolute; right: 22px; top: 22px; font-size: 26px; color: #F7924A; }
#s6-cols { position: absolute; left: 24px; right: 24px; bottom: 18px; display: flex; gap: 26px; }
#s6-cols .col { flex: 1; }
#s6-cols .bars { height: 92px; display: flex; align-items: flex-end; gap: 6px; border-bottom: 1px solid rgba(255,255,255,.18); }
#s6-cols .bars i { flex: 1; background: linear-gradient(180deg, #42B6F0, rgba(66,182,240,.35)); border-radius: 3px 3px 0 0; transform-origin: 50% 100%; }
#s6-cols .cn { font-size: 26px; color: #a8afba; margin-top: 8px; }
"""
    body = f"""    <div id="s6-left">
      <div id="s6-kick" class="kicker">versioned indexes</div>
      <div id="s6-h" class="h1">Indexes travel <span class="grad">in time, too.</span></div>
      <div id="s6-sub" class="sub">Opening an index at revision N returns its state as of N &mdash; for every index type.</div>
    </div>
    <div id="s6-scrub"><span class="lab">open at</span>{''.join(f'<div class="p" id="s6-p{r}">{r}</div>' for r in range(1, 6))}</div>
    <div id="s6-grid">
{cards}
    </div>
    <div id="s6-proj" class="panel"><div class="n">projection <span style="font-weight:500;color:#a8afba">&middot; columnar</span></div><div class="d">SIMD kernels for aggregates, group-bys, counts</div><div class="tag mono">experimental</div>
      <div id="s6-cols">{colhtml}</div></div>"""
    js = ""
    js += blur_in("#s6-kick", 0.0, 0.45)
    js += blur_in("#s6-h", "C.indexes - 0.05", 0.5)
    js += blur_in("#s6-sub", "C.versioned + 0.3", 0.5)
    js += '    tl.fromTo(".s6-card", {opacity: 0, y: 24}, {opacity: 1, y: 0, duration: 0.55, ease: "expo.out", stagger: 0.07}, C.indexes);\n'
    js += blur_in("#s6-scrub", "C.versioned - 0.1", 0.4)
    # scrubber steps 1..5; every tag follows
    js += '    for (let r = 1; r <= 5; r++) { gsap.set(".s6-rv" + r, {opacity: r === 1 ? 1 : 0}); }\n'
    js += '    tl.set("#s6-p1", {backgroundColor: "rgba(66,182,240,.18)", borderColor: "#42B6F0", color: "#ecebe8"}, 0);\n'
    js += '    const step = Math.max(0.35, (D - 0.6 - C.versioned) / 6);\n'
    js += '    for (let r = 2; r <= 5; r++) { const t = C.versioned + 0.2 + step * (r - 1);\n'
    js += '      tl.set("#s6-p" + (r - 1), {backgroundColor: "rgba(0,0,0,0)", borderColor: "rgba(255,255,255,.18)", color: "#a8afba"}, t);\n'
    js += '      tl.set("#s6-p" + r, {backgroundColor: "rgba(66,182,240,.18)", borderColor: "#42B6F0", color: "#ecebe8"}, t);\n'
    js += '      tl.set(".s6-rv" + (r - 1), {opacity: 0}, t); tl.set(".s6-rv" + r, {opacity: 1}, t);\n'
    js += '      tl.to("#s6-cols .bars i", {scaleY: (i) => 0.55 + 0.45 * Math.abs(Math.sin(i * 1.7 + r)), duration: 0.3, ease: "power2.out"}, t); }\n'
    js += '    tl.fromTo("#s6-proj", {opacity: 0, y: 30, filter: "blur(8px)"}, {opacity: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out"}, C.columnar - 0.1);\n'
    js += '    tl.fromTo("#s6-cols .bars i", {scaleY: 0}, {scaleY: 1, duration: 0.5, ease: "expo.out", stagger: 0.015}, C.columnar + 0.15);\n'
    js += '    tl.to(["#s6-left", "#s6-scrub", "#s6-grid", "#s6-proj"], {opacity: 0, filter: "blur(8px)", duration: 0.3, ease: "power3.in"}, D - 0.3);\n'
    return scene("s6", body, js, css, c)

# ---------- S7: four ways in ----------
def s7():
    b = 6
    c = dict(embed=cue(b, "Embed"), library=cue(b, "library"), rest=cue(b, "REST"), shell=cue(b, "shell"),
             agents=cue(b, "agents"), mcp=cue(b, "MCP"), end=dur(b))
    tiles = [
        ("t1", "Embedded library", "Java &middot; Maven or Gradle", '<span class="a-k">implementation</span>(<span class="a-s">"io.sirix:sirix-core:1.0.0-beta7"</span>)'),
        ("t2", "REST server", "HTTP &middot; JSON", '<span class="a-k">GET</span> /shop/products/diff<br>&nbsp;&nbsp;?first-revision=<span class="a-o">1</span>&amp;second-revision=<span class="a-o">3</span>'),
        ("t3", "Interactive shell", "JSONiq / XQuery", '<span class="a-o">sirix&gt;</span> <span class="a-k">jn:diff</span>(<span class="a-s">\'shop\'</span>,<span class="a-s">\'products\'</span>,<span class="a-o">1</span>,<span class="a-o">3</span>)'),
        ("t4", "MCP server for AI agents", "read-only by default &middot; audit log", 'time-travel reads &middot; structural diffs &middot; revert'),
    ]
    th = "\n".join(f'      <div class="s7-tile panel" id="s7-{i}"><div class="n">{n}</div><div class="d">{d}</div><div class="code mono">{code}</div></div>' for i, n, d, code in tiles)
    css = """
#s7-top { position: absolute; left: 120px; top: 110px; }
#s7-top .kicker { margin-bottom: 18px; }
#s7-grid { position: absolute; left: 120px; top: 330px; width: 1680px; display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }
.s7-tile { height: 262px; padding: 30px 34px; position: relative; }
.s7-tile .n { font-size: 40px; font-weight: 800; letter-spacing: -.02em; }
.s7-tile .d { font-size: 27px; color: #a8afba; margin-top: 4px; }
.s7-tile .code { position: absolute; left: 34px; right: 30px; bottom: 26px; font-size: 24px; line-height: 1.4; padding: 12px 18px; background: #0b0c0e; border-radius: 8px; border: 1px solid rgba(255,255,255,.09); white-space: nowrap; overflow: hidden; color: #ecebe8; }
"""
    body = f"""    <div id="s7-top"><div id="s7-kick" class="kicker">open source &middot; BSD-3-Clause</div><div id="s7-h" class="h2">One engine. <span class="grad">Four ways in.</span></div></div>
    <div id="s7-grid">
{th}
    </div>"""
    js = ""
    js += blur_in("#s7-kick", 0.0, 0.45)
    js += blur_in("#s7-h", "C.embed - 0.05", 0.5)
    js += '    tl.set(".s7-tile", {opacity: 0.0}, 0);\n'
    for i, k in [(1, "library"), (2, "rest"), (3, "shell"), (4, "mcp")]:
        tt = f"C.{k} - 0.15" if k != "mcp" else "C.agents - 0.1"
        js += f'    tl.fromTo("#s7-t{i}", {{opacity: 0, y: 26, filter: "blur(8px)"}}, {{opacity: 1, y: 0, filter: "blur(0px)", duration: 0.55, ease: "expo.out"}}, {tt});\n'
        js += f'    tl.fromTo("#s7-t{i}", {{borderColor: "rgba(244,123,32,.8)"}}, {{borderColor: "rgba(255,255,255,.12)", duration: 1.2, ease: "power2.out"}}, {tt} + 0.3);\n'
    js += '    tl.to(["#s7-top", "#s7-grid"], {opacity: 0, y: -20, filter: "blur(8px)", duration: 0.3, ease: "power3.in"}, D - 0.35);\n'
    return scene("s7", body, js, css, c)

# ---------- S8: end card ----------
def s8():
    b = 7
    c = dict(sirix=cue(b, "SirixDB"), every=cue(b, "Every"), present=cue(b, "present"), bitemporal=cue(b, "Bitemporal"),
             open=cue(b, "open"), embeddable=cue(b, "embeddable"), end=dur(b))
    css = """
#s8-wrap { position: absolute; left: 0; top: 0; width: 1920px; height: 900px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
#s8-lock { display: flex; align-items: center; gap: 34px; }
#s8-logo { width: 190px; height: 190px; }
#s8-word { font-size: 132px; font-weight: 800; letter-spacing: -.04em; }
#s8-tag { margin-top: 40px; text-align: center; font-size: 54px; font-weight: 800; letter-spacing: -.03em; line-height: 1.15; }
#s8-pills { margin-top: 34px; display: flex; gap: 14px; }
#s8-pills .chip { font-size: 26px; color: #ecebe8; }
#s8-links { margin-top: 38px; font-size: 30px; color: #a8afba; }
#s8-links b { color: #6CC6F3; font-weight: 500; }
"""
    logo = """<svg id="s8-logo" viewBox="0 0 100 100" fill="none">
  <defs><linearGradient id="s8-g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="hsl(25,95%,55%)"/><stop offset="100%" stop-color="hsl(200,85%,60%)"/></linearGradient></defs>
  <ellipse id="s8-e4" cx="50" cy="25" rx="35" ry="12" fill="url(#s8-g)" opacity="0.3"/>
  <ellipse id="s8-e3" cx="50" cy="40" rx="35" ry="12" fill="url(#s8-g)" opacity="0.5"/>
  <ellipse id="s8-e2" cx="50" cy="55" rx="35" ry="12" fill="url(#s8-g)" opacity="0.7"/>
  <ellipse id="s8-e1" cx="50" cy="70" rx="35" ry="12" fill="url(#s8-g)"/>
  <g id="s8-lines"><path d="M50 25 L50 70" stroke="url(#s8-g)" stroke-width="2" opacity="0.5"/><path d="M30 30 L30 75" stroke="url(#s8-g)" stroke-width="1.5" opacity="0.3"/><path d="M70 30 L70 75" stroke="url(#s8-g)" stroke-width="1.5" opacity="0.3"/></g>
</svg>"""
    body = f"""    <div id="s8-wrap">
      <div id="s8-lock">{logo}<div id="s8-word">SirixDB</div></div>
      <div id="s8-tag"><div id="s8-t1">Every version of your data, kept and queryable</div><div id="s8-t2" class="grad">as fast as the present.</div></div>
      <div id="s8-pills"><span class="chip" id="s8-p1">bitemporal</span><span class="chip" id="s8-p2">open source</span><span class="chip" id="s8-p3">embeddable</span></div>
      <div id="s8-links" class="mono"><b>github.com/sirixdb/sirix</b> &nbsp;&middot;&nbsp; <b>sirix.io</b> &nbsp;&middot;&nbsp; BSD-3-Clause</div>
    </div>"""
    js = ""
    for i, e in enumerate(["#s8-e1", "#s8-e2", "#s8-e3", "#s8-e4"]):
        js += f'    tl.fromTo("{e}", {{y: 26, opacity: 0}}, {{y: 0, opacity: {[1, .7, .5, .3][i]}, duration: 0.5, ease: "expo.out"}}, {0.05 + 0.12 * i:.2f});\n'
    js += '    tl.fromTo("#s8-lines", {opacity: 0}, {opacity: 1, duration: 0.4}, 0.55);\n'
    js += '    tl.fromTo("#s8-word", {clipPath: "inset(0 100% 0 0)", x: -20}, {clipPath: "inset(0 0% 0 0)", x: 0, duration: 0.6, ease: "expo.out"}, C.sirix + 0.05);\n'
    js += blur_in("#s8-t1", "C.every - 0.05", 0.5)
    js += blur_in("#s8-t2", "C.present - 0.45", 0.5)
    for i, k in [(1, "bitemporal"), (2, "open"), (3, "embeddable")]:
        js += f'    tl.fromTo("#s8-p{i}", {{opacity: 0, scale: .85}}, {{opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)"}}, C.{k} - 0.05);\n'
    js += blur_in("#s8-links", "C.embeddable + 0.6", 0.5)
    return scene("s8", body, js, css, c)

# ---------- captions ----------
def caption_groups():
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end_sent = w["text"][-1] in ".:!?"
        comma = w["text"][-1] == ","
        gap = (nxt["start"] - w["end"]) if nxt else 9
        rest = 0  # words left in this sentence after w
        for x in words[i + 1:]:
            if x["beat"] != w["beat"]: break
            rest += 1
            if x["text"][-1] in ".:!?": break
        if len(cur) >= 7 and 0 < rest <= 2 and not end_sent and len(cur) < 9: continue
        if (end_sent or nxt is None or nxt["beat"] != w["beat"] or len(cur) >= 7
                or (comma and len(cur) >= 3 and rest > 1)):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    out = []
    for gi, g in enumerate(groups):
        st = g[0]["start"] - 0.05
        en = g[-1]["end"] + 0.25
        if gi + 1 < len(groups): en = min(en, groups[gi + 1][0]["start"] - 0.06)
        out.append((round(st, 3), round(en, 3), " ".join(w["text"] for w in g)))
    return out

def captions():
    gs = caption_groups()
    css = """
#cap-band { position: absolute; left: 0; right: 0; bottom: 92px; height: 70px; }
.cg { position: absolute; left: 0; right: 0; bottom: 0; text-align: center; }
.cg span { display: inline-block; font-family: 'Inter', sans-serif; font-weight: 600; font-size: 42px; line-height: 1.25; color: #ecebe8; background: rgba(8,9,11,.62); padding: 6px 20px; border-radius: 10px; max-width: 1600px; }
"""
    body = '    <div id="cap-band">\n' + "\n".join(f'      <div class="cg" id="cap-g{i}"><span>{html.escape(t)}</span></div>' for i, (_, _, t) in enumerate(gs)) + "\n    </div>"
    js = ""
    for i, (st, en, _) in enumerate(gs):
        js += f'    gsap.set("#cap-g{i}", {{opacity: 0, visibility: "hidden"}});\n'
        js += f'    tl.set("#cap-g{i}", {{visibility: "visible"}}, {st});\n'
        js += f'    tl.to("#cap-g{i}", {{opacity: 1, duration: 0.1}}, {st});\n'
        js += f'    tl.to("#cap-g{i}", {{opacity: 0, duration: 0.1, ease: "power2.in"}}, {en - 0.1:.3f});\n'
        js += f'    tl.set("#cap-g{i}", {{opacity: 0, visibility: "hidden"}}, {en});\n'
    tpl = f"""<template>
  <style>#root {{ position: absolute; inset: 0; }}{css}</style>
  <div id="root" data-composition-id="cap" data-width="1920" data-height="1080">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}    window.__timelines["cap"] = tl;
  </script>
</template>
"""
    return tpl, gs

def srt(gs):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    return "\n".join(f"{i+1}\n{ts(st)} --> {ts(en)}\n{t}\n" for i, (st, en, t) in enumerate(gs))

# ---------- root ----------
def index(audio_html):
    hosts = []
    for i, (sid, _) in enumerate(BEATS):
        hosts.append(f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{scene_start[i]}" data-duration="{dur(i)}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 2"></div>')
    if "--no-captions" not in sys.argv: hosts.append(f'      <div id="cap" data-composition-id="cap" data-composition-src="compositions/cap.html" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index: 5"></div>')
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #0e0f11; }}
      #root {{ width: 100%; height: 100%; position: relative; font-family: 'Inter', sans-serif; }}
      #bg {{ position: absolute; inset: 0; background: #0e0f11; z-index: 0; overflow: hidden; }}
      #bg-grid {{ position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px); background-size: 64px 64px; }}
      #bg-glow-o {{ position: absolute; left: -300px; top: -380px; width: 1300px; height: 1100px; background: radial-gradient(closest-side, rgba(244,123,32,.16), transparent 72%); }}
      #bg-glow-b {{ position: absolute; left: 900px; top: -120px; width: 1400px; height: 1200px; background: radial-gradient(closest-side, rgba(66,182,240,.15), transparent 72%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="bg"><div id="bg-grid"></div><div id="bg-glow-o"></div><div id="bg-glow-b"></div></div>
{chr(10).join(hosts)}
{audio_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#bg-glow-o", {{x: 0, y: 0}}, {{x: 220, y: 90, duration: {TOTAL}, ease: "none"}}, 0);
      tl.fromTo("#bg-glow-b", {{x: 0, y: 0}}, {{x: -260, y: 60, duration: {TOTAL}, ease: "none"}}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    import shutil, time
    if (PROJ / "index.html").exists() and "--regenerate" not in sys.argv:
        sys.exit(f"refusing to overwrite {PROJ}: it is the editable Studio project. "
                 "Use build/regenerate.sh --regenerate (backs it up first).")
    if (PROJ / "index.html").exists() and "--backed-up" not in sys.argv:
        bak = PROJ.with_name(PROJ.name + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
        shutil.copytree(PROJ, bak); print("backup:", bak)
    blocks = parse(ANSI)
    comp = PROJ / "compositions"; comp.mkdir(parents=True, exist_ok=True)
    if "--captions-only" in sys.argv:
        cap, gs = captions(); comp.joinpath("cap.html").write_text(recolour(cap))
        (PROJ / "captions.srt").write_text(srt(gs)); sys.exit(0)
    W = lambda f, t: f.write_text(recolour(t))
    W(comp / "s1.html", s1())
    W(comp / "s2.html", s2())
    s3html, _ = s3(blocks); W(comp / "s3.html", s3html)
    W(comp / "s4.html", s4(blocks))
    W(comp / "s5.html", s5())
    W(comp / "s6.html", s6())
    W(comp / "s7.html", s7())
    W(comp / "s8.html", s8())
    cap, gs = captions(); W(comp / "cap.html", cap)
    audio = ""
    plc = pathlib.Path(WORDS_JSON).with_name("placement.json") if WORDS_JSON else None
    if plc and plc.exists():
        audio = "\n".join(f'      <audio id="{c["id"]}" src="{c["src"]}" data-start="{c["start"]}" data-duration="{c["duration"]}" data-track-index="5" data-volume="1"></audio>' for c in json.load(open(plc)))
        audio += f'\n      <audio id="music" src="assets/music-ducked.wav" data-start="0" data-duration="{TOTAL}" data-track-index="6" data-volume="1"></audio>'
    W(PROJ / "index.html", index(audio))
    (PROJ / "captions.srt").write_text(srt(gs))
    json.dump({"total": TOTAL, "scenes": [[BEATS[i][0], scene_start[i], dur(i)] for i in range(len(BEATS))],
               "words": [{k: w[k] for k in ("text", "start", "end")} for w in words]},
              open(PROJ / "timing.json", "w"), indent=1)
    print("total", TOTAL); [print(BEATS[i][0], scene_start[i], dur(i)) for i in range(len(BEATS))]
