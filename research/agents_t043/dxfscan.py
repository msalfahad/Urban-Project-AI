"""Stdlib DXF scanner: modelspace entities as (type, layer, coords, short text).
Prints a layer census, or entities inside a window. Long texts are dropped
(only marks up to 12 chars are kept) so no notes/title block are printed."""
import sys, re, json, collections

def pairs(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.read().split('\n')
    for i in range(0, len(lines) - 1, 2):
        yield lines[i].strip(), lines[i + 1].rstrip('\r')

def entities(path):
    sec = None; cur = None; in_ent = False; blk = None
    out = []
    it = pairs(path)
    for code, val in it:
        if code == '0' and val == 'SECTION':
            c, n = next(it); sec = n; continue
        if code == '0' and val == 'ENDSEC':
            sec = None; continue
        if sec not in ('ENTITIES', 'BLOCKS'):
            continue
        if code == '0':
            if cur: out.append(cur)
            cur = None
            if val == 'BLOCK':
                cur = {'t': 'BLOCKDEF', 'g': collections.defaultdict(list)}
                continue
            if val == 'ENDBLK':
                blk = None; continue
            cur = {'t': val, 'g': collections.defaultdict(list), 'blk': blk, 'sec': sec}
            continue
        if cur is None: continue
        cur['g'][code].append(val)
        if cur['t'] == 'BLOCKDEF' and code == '2':
            blk = val
    if cur: out.append(cur)
    return out

def f(g, c, i=0):
    try: return float(g[c][i])
    except Exception: return None

def simplify(e):
    g = e['g']; t = e['t']
    d = {'t': t, 'L': g.get('8', [''])[0], 'blk': e.get('blk')}
    if t in ('TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF'):
        s = ''.join(g.get('3', [])) + (g.get('1', [''])[0])
        s = re.sub(r'\\[A-Za-z][^;]*;|[{}]', '', s).strip()
        d['s'] = s if len(s) <= 12 else '<long>'
        d['p'] = (f(g, '10'), f(g, '20'))
        d['h'] = f(g, '40'); d['rot'] = f(g, '50')
    elif t == 'LINE':
        d['p'] = [(f(g, '10'), f(g, '20')), (f(g, '11'), f(g, '21'))]
    elif t == 'LWPOLYLINE':
        d['p'] = [(float(x), float(y)) for x, y in zip(g['10'], g['20'])]
        d['closed'] = (int(g.get('70', ['0'])[0]) & 1) == 1
    elif t == 'INSERT':
        d['name'] = g.get('2', [''])[0]; d['p'] = (f(g, '10'), f(g, '20'))
        d['sx'] = f(g, '41'); d['rot'] = f(g, '50')
    elif t in ('CIRCLE', 'ARC'):
        d['p'] = (f(g, '10'), f(g, '20')); d['r'] = f(g, '40')
    elif t == 'DIMENSION':
        d['p'] = [(f(g, '13'), f(g, '23')), (f(g, '14'), f(g, '24'))]
        d['m'] = f(g, '42'); s = g.get('1', [''])[0]; d['s'] = s if len(s) <= 12 else '<long>'
    else:
        d['p'] = None
    return d

def pts(d):
    p = d.get('p')
    if p is None: return []
    if isinstance(p, tuple): return [p]
    return p

if __name__ == '__main__':
    path, mode = sys.argv[1], sys.argv[2]
    ents = [simplify(e) for e in entities(path) if e['t'] != 'BLOCKDEF']
    ms = [d for d in ents if d['blk'] is None]
    if mode == 'census':
        c = collections.Counter((d['L'], d['t']) for d in ms)
        for k, v in sorted(c.items()): print(v, k)
        xs = [p[0] for d in ms for p in pts(d) if p[0] is not None]
        ys = [p[1] for d in ms for p in pts(d) if p[1] is not None]
        print('extent', min(xs), max(xs), min(ys), max(ys))
    elif mode == 'window':
        x0, y0, x1, y1 = map(float, sys.argv[3:7])
        layers = sys.argv[7].split(',') if len(sys.argv) > 7 and sys.argv[7] != '*' else None
        for d in ms:
            P = pts(d)
            if not P or P[0][0] is None: continue
            if not any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in P if x is not None): continue
            if layers and d['L'] not in layers: continue
            print(json.dumps({k: v for k, v in d.items() if k != 'blk'}))
    elif mode == 'marks':
        rx = re.compile(sys.argv[3])
        for d in ents:
            if d.get('s') and rx.fullmatch(d['s']):
                print(json.dumps(d))

def find(path, rx):
    import re as _re
    r = _re.compile(rx)
    for e in entities(path):
        if e['t'] not in ('TEXT', 'MTEXT', 'ATTRIB'): continue
        g = e['g']; s = ''.join(g.get('3', [])) + g.get('1', [''])[0]
        s = _re.sub(r'\\[A-Za-z][^;]*;|[{}]', '', s)
        if r.search(s):
            print(e['t'], g.get('8', [''])[0], e.get('blk'), s[:60], (round(float(g['10'][0])), round(float(g['20'][0]))))
