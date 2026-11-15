"""Drive a real sirix-shell session in a pty and save what it prints.
Usage: capture2.py <out_dir> <queries.json>   queries: list of {"q": "...", "sleep": seconds_after, "stamp": name}
A query may contain {T}: replaced by the UTC second chosen 1.5 s after the query stamped "rev1" returned."""
import os, pty, select, subprocess, time, json, pathlib, re, struct, fcntl, termios, sys, datetime
base = pathlib.Path(os.environ['SIRIX_CLASSPATH_DIR'])  # a dir holding classpath.txt of a built sirix (sirix-query) checkout
out = pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True, exist_ok=True)
queries = json.load(open(sys.argv[2]))
cp = (base / 'classpath.txt').read_text()
master, slave = pty.openpty()
attrs = termios.tcgetattr(slave); attrs[3] &= ~termios.ECHO; termios.tcsetattr(slave, termios.TCSANOW, attrs)
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 48, 120, 0, 0))
home = out / 'home'
if home.exists():
    import shutil; shutil.rmtree(home)
home.mkdir()
env = dict(os.environ, TERM='xterm-256color', COLORTERM='truecolor'); env.pop('NO_COLOR', None)
(out / 'logback.xml').write_text("<configuration><root level='OFF'/></configuration>")
cmd = [os.environ.get('JAVA', 'java')  # JDK 25, '--enable-preview', '--add-modules=jdk.incubator.vector', '--enable-native-access=ALL-UNNAMED', '-Xmx768m', f'-Dlogback.configurationFile={out}/logback.xml', f'-Duser.home={home}', f'-DdbLocation={home}', '-cp', cp, 'io.sirix.query.Main']
p = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, env=env, start_new_session=True)
os.close(slave)
start = time.monotonic(); events = []; raw = bytearray(); position = 0
def read_until(marker, timeout=40, raw_start=None):
    global position
    deadline = time.monotonic() + timeout; seen = bytearray()
    while time.monotonic() < deadline:
        plain = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', raw)
        if raw_start is not None:
            if raw.find(marker, raw_start) >= 0: return
        else:
            found = plain.find(marker, position)
            if found >= 0: position = found + len(marker); return
        ready, _, _ = select.select([master], [], [], 0.2)
        if ready:
            try: data = os.read(master, 65536)
            except OSError: break
            raw.extend(data); seen.extend(data)
            events.append([round(time.monotonic() - start, 6), 'o', data.decode('utf-8', 'replace')])
            if b'\x1b[6n' in data: os.write(master, b'\x1b[1;1R')
        if p.poll() is not None: break
    raise RuntimeError(f'expected {marker!r}, tail={seen[-1200:]!r}, exit={p.poll()}')
stamps = {}; T = None
try:
    read_until(b'sirix>')
    for item in queries:
        q = item['q']
        if '{T}' in q: q = q.replace('{T}', T)
        for line in q.splitlines():
            line_start = len(raw)
            os.write(master, b'\x1b[200~' + line.encode() + b'\x1b[201~\r')
            read_until(b'\x1b[?2004l', raw_start=line_start)
        os.write(master, b'\r')
        read_until(b'Enter query string')
        read_until(b'>')
        if item.get('stamp'):
            stamps[item['stamp']] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if item['stamp'] == 'rev1':
                T = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=1.5)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
                stamps['T'] = T
        if item.get('sleep'): time.sleep(item['sleep'])
    os.write(master, b'\x04'); p.wait(timeout=30)
finally:
    if p.poll() is None: p.kill(); p.wait()
    (out / 'demo.ansi').write_bytes(raw)
    (out / 'demo.cast').write_text(json.dumps({'version': 2, 'width': 120, 'height': 48, 'timestamp': int(time.time()), 'env': {'TERM': 'xterm-256color'}}) + '\n' + '\n'.join(json.dumps(e, ensure_ascii=False) for e in events) + '\n')
    (out / 'demo-raw.txt').write_text(re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', raw.decode('utf-8', 'replace')))
    (out / 'stamps.json').write_text(json.dumps(stamps, indent=1))
    import shutil; shutil.rmtree(home, ignore_errors=True)
