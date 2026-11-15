"""Build only the caption composition from timed, identified words."""
import html


def caption_groups(words):
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end_sent = w["text"][-1] in ".:!?"
        comma = w["text"][-1] == ","
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

def captions(gs):
    css = """
#cap-band { position: absolute; left: 0; right: 0; bottom: 92px; height: 70px; }
.cg { position: absolute; left: 0; right: 0; bottom: 0; text-align: center; }
.cg span { display: inline-block; font-family: 'Inter', sans-serif; font-weight: 600; font-size: 42px; line-height: 1.25; color: #ecebe8; background: rgba(8,9,11,.62); padding: 6px 20px; border-radius: 10px; max-width: 1600px; }
"""
    body = '    <div id="cap-band">\n' + "\n".join(f'      <div class="cg" id="cap-g{i}"><span>{html.escape(t)}</span></div>' for i, (_, _, t) in enumerate(gs)) + "\n    </div>"
    js = ""
    for i, (st, en, _) in enumerate(gs):
        fade = min(0.1, (en - st) / 2)
        js += f'    gsap.set("#cap-g{i}", {{opacity: 0, visibility: "hidden"}});\n'
        js += f'    tl.set("#cap-g{i}", {{visibility: "visible"}}, {st});\n'
        js += f'    tl.to("#cap-g{i}", {{opacity: 1, duration: {fade:.3f}}}, {st});\n'
        js += f'    tl.to("#cap-g{i}", {{opacity: 0, duration: {fade:.3f}, ease: "power2.in"}}, {en - fade:.3f});\n'
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
    return tpl
