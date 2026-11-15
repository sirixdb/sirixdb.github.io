"""Shared helpers for the SirixDB promo tools (audio analysis, index.html audio tags)."""
import array, json, pathlib, re, subprocess, wave

PROJECT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.load(open(PROJECT / "build" / "script.json"))
SR = 48000


def run(cmd, check=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")
    return r


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout)


def loudness(path):
    """Integrated loudness (LUFS) of a file."""
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"]).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def speech_regions(path):
    """(duration, [(start, end), ...]) of non-silent stretches."""
    dur = duration(path)
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.12", "-f", "null", "-"]).stderr
    sil, s = [], None
    for ln in err.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", ln)
        if m: s = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", ln)
        if m: sil.append((s if s is not None else 0.0, float(m.group(1)))); s = None
    if s is not None: sil.append((s, dur))
    regs, t = [], 0.0
    for a, b in sil:
        if a > t + 0.02: regs.append((t, a))
        t = b
    if t < dur - 0.02: regs.append((t, dur))
    return dur, regs


def take_pauses(src, cap=None, pauses=None):
    """(speech regions, pause lengths) of a raw take as tighten() lays them out, before tempo.

    Each internal pause keeps its natural length up to `cap`. `pauses` (a beat's "take_pauses" in
    build/script.json) can set single pauses by position: a number is that pause's length in
    seconds, null keeps the natural one. It only applies while it has one entry per pause of the
    take, so a re-recorded take falls back to its natural pauses instead of pausing mid-word.
    """
    cap = CFG["timing"]["max_pause_in_take"] if cap is None else cap
    _, regs = speech_regions(src)
    nat = [regs[i + 1][0] - regs[i][1] for i in range(len(regs) - 1)]
    if pauses is not None and len(pauses) != len(nat):
        print(f"note: take_pauses has {len(pauses)} entries but {pathlib.Path(src).name} has {len(nat)} pauses; using the natural pauses")
        pauses = None
    out = [min(n, cap) if pauses is None or pauses[i] is None else float(pauses[i]) for i, n in enumerate(nat)]
    return regs, out


def tighten(src, dst, cap=None, tempo=None, gain_db=0.0, pauses=None):
    """Trim a raw voice take, set its internal pauses, apply tempo and gain (mono, 48 kHz)."""
    tempo = CFG["timing"]["tempo"] if tempo is None else tempo
    dst = pathlib.Path(dst); tmp = dst.with_suffix(".tmp.raw"); tmpw = dst.with_suffix(".tmp.wav")
    run(["ffmpeg", "-y", "-hide_banner", "-i", src, "-ac", "1", "-ar", SR, "-f", "s16le", tmp])
    pcm = array.array("h"); pcm.frombytes(tmp.read_bytes())
    regs, gaps = take_pauses(src, cap, pauses)
    out = array.array("h")
    out.extend(array.array("h", [0]) * int(0.04 * SR))
    for i, (x, y) in enumerate(regs):
        if i: out.extend(array.array("h", [0]) * int(gaps[i - 1] * SR))
        out.extend(pcm[int(x * SR):int(y * SR)])
    out.extend(array.array("h", [0]) * int(0.12 * SR))
    with wave.open(str(tmpw), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
    # gain, then a peak limiter at -1.5 dBFS: the takes are quiet (about -27 LUFS) but peaky, so
    # reaching -16 LUFS needs ~+11 dB and would otherwise clip (found in the first Studio export).
    af = f"atempo={tempo}" if tempo != 1.0 else "anull"
    run(["ffmpeg", "-y", "-hide_banner", "-i", tmpw, "-af", f"{af},volume={gain_db}dB,alimiter=limit=0.84:attack=3:release=60:level=0", "-c:a", "pcm_s16le", dst])
    tmp.unlink(); tmpw.unlink()


def _attr(tag, name, default=None):
    # whole attribute name only: Studio stamps data-hf-id="..." on every element, and a plain \b
    # would read that as id="..." (then no voice clip is found and remix.py fails)
    m = re.search(rf'(?<![\w-]){name}="([^"]*)"', tag)
    return m.group(1) if m else default


def root_duration(video):
    html = (pathlib.Path(video) / "index.html").read_text()
    m = re.search(r'<div[^>]*data-composition-id="main"[^>]*>', html)
    return float(_attr(m.group(0), "data-duration"))


def voice_clips(video):
    """Voice clips in index.html, as placed (possibly moved or trimmed in Studio)."""
    html = (pathlib.Path(video) / "index.html").read_text()
    clips = []
    for tag in re.findall(r"<audio\b[^>]*>", html):
        cid = _attr(tag, "id", "")
        if not re.fullmatch(r"vo-\d+", cid) or _attr(tag, "data-hidden") is not None:
            continue
        clips.append(dict(id=cid, beat=int(cid[3:]), src=pathlib.Path(video) / _attr(tag, "src"),
                          start=float(_attr(tag, "data-start", "0")),
                          media_start=float(_attr(tag, "data-media-start", "0")),
                          duration=float(_attr(tag, "data-duration")) if _attr(tag, "data-duration") else None,
                          volume=float(_attr(tag, "data-volume", "1"))))
    return sorted(clips, key=lambda c: c["start"])


def align(clip, text, clip_start, media_start=0.0, beat=0):
    """Estimate word times: spread the known words over the clip's speech by character weight."""
    _, regs = speech_regions(clip)
    regs = [(max(x, media_start) - media_start, y - media_start) for x, y in regs if y > media_start]
    ws = text.split()
    wt = [len(re.sub(r"[^\w]", "", w)) + 1.5 for w in ws]
    k = sum(y - x for x, y in regs) / sum(wt)
    def at(s):
        for x, y in regs:
            if s <= (y - x): return x + s
            s -= (y - x)
        return regs[-1][1]
    out, acc = [], 0.0
    for w, q in zip(ws, wt):
        st = at(acc + 0.01); acc += q * k; en = at(acc - 0.01)
        out.append({"text": w, "start": round(clip_start + st, 3), "end": round(clip_start + en, 3), "beat": beat})
    return out
