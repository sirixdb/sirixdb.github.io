#!/usr/bin/env python3
"""Write the SRT from what the caption composition actually shows (video/compositions/cap.html).

Usage: tools/srt.py > out/sirixdb-60s.srt
"""
import re, sys, pathlib, html
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import PROJECT
src = (PROJECT / "video" / "compositions" / "cap.html").read_text()
texts = {m.group(1): html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
         for m in re.finditer(r'id="cap-g(\d+)"[^>]*>(.*?)</div>', src, re.S)}
show = {m.group(1): float(m.group(2)) for m in re.finditer(r'tl\.set\("#cap-g(\d+)", \{visibility: "visible"\}, ([\d.]+)\)', src)}
hide = {m.group(1): float(m.group(2)) for m in re.finditer(r'tl\.set\("#cap-g(\d+)", \{opacity: 0, visibility: "hidden"\}, ([\d.]+)\)', src)}
def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
rows = sorted((show[k], hide.get(k, show[k] + 2), texts[k]) for k in show if k in texts)
if not rows: sys.exit("no caption groups found in cap.html")
print("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(rows)))
