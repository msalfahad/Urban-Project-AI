"""Render a window of the DXF (mm) to PNG, with one level of block expansion.
usage: render.py dxf out.png x0 y0 x1 y1 [cx,cy;cx,cy...]  (crosses in mm)"""
import sys, math, json
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
import dxfscan as S
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

COL = {'1': 'black', '2': 'dimgray', 'S-COL.BON': 'blue', 'S-OPENING': 'orange', 'S-TEXT': 'red',
       'S-AXIS': 'lightgray', 'S-BEAM': 'magenta', 'S-REIN-SLAB': 'palegreen', 'S-TEXT-SLAB': 'green',
       'S-SEC.LINE': 'purple', 'S-DIM': 'teal', 'S-DIM1': 'teal', 'S-BOUN': 'brown', 'S-FOOTINGS': 'navy'}

def xf(p, ins):
    if ins is None: return p
    bx, by, sx, sy, rot = ins
    x, y = p[0] * sx, p[1] * sy
    r = math.radians(rot or 0)
    return (bx + x * math.cos(r) - y * math.sin(r), by + x * math.sin(r) + y * math.cos(r))

def main():
    path, out = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1 = map(float, sys.argv[3:7])
    crosses = [tuple(map(float, c.split(','))) for c in sys.argv[7].split(';')] if len(sys.argv) > 7 else []
    raw = S.entities(path)
    ents = [S.simplify(e) for e in raw if e['t'] != 'BLOCKDEF']
    blocks = {}
    for d in ents:
        if d['blk'] is not None: blocks.setdefault(d['blk'], []).append(d)
    items = []
    for d in ents:
        if d['blk'] is not None: continue
        if d['t'] == 'INSERT':
            g = d
            sx = d.get('sx') or 1.0
            ins = (d['p'][0], d['p'][1], sx, sx, d.get('rot') or 0)
            for b in blocks.get(d['name'], []):
                b2 = dict(b); b2['L'] = b['L'] if b['L'] != '0' else d['L']; b2['ins'] = ins; b2['from'] = d['name']
                items.append(b2)
        else:
            d['ins'] = None; items.append(d)
    fig, ax = plt.subplots(figsize=(14, 14 * (y1 - y0) / (x1 - x0)))
    for d in items:
        L = d['L']; c = COL.get(L, 'silver'); ins = d['ins']
        if d['t'] == 'LINE':
            P = [xf(p, ins) for p in d['p']]
        elif d['t'] == 'LWPOLYLINE':
            P = [xf(p, ins) for p in d['p']] + ([xf(d['p'][0], ins)] if d.get('closed') else [])
        elif d['t'] in ('TEXT', 'MTEXT', 'ATTRIB') and d.get('s'):
            p = xf(d['p'], ins)
            if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
                rot = (d.get('rot') or 0) + ((ins[4] or 0) if ins else 0)
                ax.text(p[0], p[1], d['s'] + ('[%s]' % d['from'] if d.get('from') else ''), color=c,
                        fontsize=7, rotation=rot, rotation_mode='anchor')
            continue
        elif d['t'] in ('CIRCLE', 'ARC'):
            p = xf(d['p'], ins); ax.add_patch(plt.Circle(p, d['r'] or 1, fill=False, color=c, lw=0.4)); continue
        else:
            continue
        if not any(x0 - 2000 <= x <= x1 + 2000 and y0 - 2000 <= y <= y1 + 2000 for x, y in P): continue
        ax.plot([p[0] for p in P], [p[1] for p in P], color=c, lw=0.6 if L == '1' else 0.4)
    for cx, cy in crosses:
        ax.plot([cx], [cy], 'x', color='red', ms=14, mew=2)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    ax.grid(True, lw=0.2); ax.tick_params(labelsize=6)
    fig.savefig(out, dpi=110, bbox_inches='tight')

main()
