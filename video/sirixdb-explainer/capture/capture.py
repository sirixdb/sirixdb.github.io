import os, pty, select, subprocess, time, json, pathlib, re, struct, fcntl, termios
# NOTE: the classpath (classpath.txt) points at a built sirix checkout; regenerate it for yours.
base = pathlib.Path(os.environ['SIRIX_CLASSPATH_DIR'])  # a dir holding classpath.txt of a built sirix (sirix-query) checkout
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'capture-out').resolve()
cp=(base/'classpath.txt').read_text()
master, slave=pty.openpty()
# JLine renders editing itself. Avoid kernel echo when scripted keys queue between readLine calls.
terminal_attributes=termios.tcgetattr(slave)
terminal_attributes[3] &= ~termios.ECHO
termios.tcsetattr(slave,termios.TCSANOW,terminal_attributes)
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 48, 120, 0, 0))
home=out/'home'
home.mkdir(exist_ok=True)
env=dict(os.environ, TERM='xterm-256color', COLORTERM='truecolor')
env.pop('NO_COLOR',None)
(out/'logback.xml').write_text("<configuration><root level='OFF'/></configuration>")
cmd=[os.environ.get('JAVA', 'java')  # JDK 25,'--enable-preview','--add-modules=jdk.incubator.vector','--enable-native-access=ALL-UNNAMED','-Xmx768m',f'-Dlogback.configurationFile={out}/logback.xml',f'-Duser.home={home}',f'-DdbLocation={home}', '-cp',cp,'io.sirix.query.Main']
# Invoked under heavy.sh; every child JVM inherits the held host limits.
p=subprocess.Popen(cmd,stdin=slave,stdout=slave,stderr=slave,env=env,start_new_session=True)
os.close(slave)
start=time.monotonic()
events=[]
raw=bytearray()
position=0
def read_until(marker,timeout=60,raw_start=None):
    global position
    deadline=time.monotonic()+timeout
    seen=bytearray()
    while time.monotonic()<deadline:
        plain=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',raw)
        if raw_start is not None:
            if raw.find(marker,raw_start)>=0: return
        else:
            found=plain.find(marker,position)
            if found>=0:
                position=found+len(marker)
                return
        ready,_,_=select.select([master],[],[],0.2)
        if ready:
            try: data=os.read(master,65536)
            except OSError: break
            raw.extend(data); seen.extend(data)
            events.append([round(time.monotonic()-start,6),'o',data.decode('utf-8','replace')])
            # Answer JLine's terminal position query so startup does not wait.
            if b'\x1b[6n' in data: os.write(master,b'\x1b[1;1R')
        if p.poll() is not None: break
    raise RuntimeError(f'expected {marker!r}, tail={seen[-1200:]!r}, exit={p.poll()}')
queries=[
"jn:store('shop','products','[{\"name\":\"Laptop\",\"price\":999},{\"name\":\"Phone\",\"price\":699}]')",
"let $doc := jn:doc('shop','products')\nreturn replace json value of $doc[0].price with 899",
"let $doc := jn:doc('shop','products')\nreturn append json {\"name\":\"Tablet\",\"price\":449} into $doc",
"jn:doc('shop','products',1)",
"for $v in jn:all-times(jn:doc('shop','products')[0])\nreturn {\"rev\":sdb:revision($v),\"price\":$v.price}",
"jn:diff('shop','products',1,3)",
"jn:doc('shop','products')"
]
try:
    read_until(b'sirix>')
    for i,q in enumerate(queries):
        for line in q.splitlines():
            # Type in bracketed-paste mode per line: real JLine editor and highlighter.
            line_start=len(raw)
            os.write(master, b'\x1b[200~'+line.encode()+b'\x1b[201~\r')
            read_until(b'\x1b[?2004l',raw_start=line_start)
        os.write(master,b'\r')
        read_until(b'Enter query string')
        read_until(b'>')
    os.write(master,b'\x04')
    p.wait(timeout=30)
finally:
    if p.poll() is None: p.kill(); p.wait()
    (out/'demo.ansi').write_bytes(raw)
    (out/'demo.cast').write_text(json.dumps({'version':2,'width':120,'height':48,'timestamp':int(time.time()),'env':{'TERM':'xterm-256color'}})+'\n'+'\n'.join(json.dumps(e,ensure_ascii=False) for e in events)+'\n')
    (out/'demo-raw.txt').write_text(re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw.decode('utf-8','replace')))
