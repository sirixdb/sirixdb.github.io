import re, html, json, sys
SGR = re.compile(r'\x1b\[([0-9;]*)m')
OTHER = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b[=>]')
COLORS = {(66,182,240):'k', (244,123,32):'o', (152,195,121):'s'}
def parse(path):
    raw = open(path,'rb').read().decode('utf-8','replace')
    blocks = raw.split('Enter query string (terminate with Control-D):')
    out = []
    for b in blocks[1:]:
        lines = []
        for ln in b.replace('\r\r\n','\n').replace('\r\n','\n').split('\n'):
            spans = []; cls = None; pos = 0
            # strip non-SGR escapes first, keeping SGR
            tmp = re.sub(r'\x1b\[[0-?]*[ -/]*[@-ln-~]|\x1b\[\?[0-9;]*[hl]|\x1b[=>]', '', ln)
            tmp = re.sub(r'\x1b\[\?2027\$p|\x1b\[c','',tmp)
            for m in SGR.finditer(tmp):
                if m.start() > pos: spans.append((cls, tmp[pos:m.start()]))
                codes = m.group(1)
                if codes in ('0',''): cls = None
                elif codes == '2': cls = 'd'
                elif codes.startswith('38;2;'):
                    r,g,bb = map(int, codes.split(';')[2:5]); cls = COLORS.get((r,g,bb),'x')
                pos = m.end()
            if pos < len(tmp): spans.append((cls, tmp[pos:]))
            text = ''.join(t for _,t in spans)
            if text.startswith('WARNING') or text.startswith('# [StorageProfile]'): continue
            lines.append(spans)
        # drop empty lines
        lines = [l for l in lines if ''.join(t for _,t in l).strip()]
        out.append(lines)
    return out
def to_html(spans):
    return ''.join(f'<span class="a-{c}">{html.escape(t)}</span>' if c else html.escape(t) for c,t in spans)
if __name__ == '__main__':
    for i,b in enumerate(parse(sys.argv[1])):
        print('--- block', i)
        for l in b: print(repr(''.join(t for _,t in l)), [c for c,_ in l][:6])
