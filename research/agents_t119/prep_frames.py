"""T-119 hand-reading helper (research only): column outlines per sheet window and p.1 mark / size binding.
Usage: python -I prep_frames.py <dump.json from dump.py> <workdir>   (writes frames.json, ax.json)
Windows are drawing metres of the Alsenan ST sheet: 2F / 1F / GF roof-slab plans and the column-and-axis plan (p.1)."""
import json, math, re, sys, collections
d = json.load(open(sys.argv[1])); WD = sys.argv[2]
F = {"2F": (-27, -2), "1F": (11.5, 36), "GF": (40.5, 74.5), "AX": (154, 192)}
def rect(r):
    xs = [p[0] for p in r['pts']]; ys = [p[1] for p in r['pts']]
    return dict(cx=(min(xs) + max(xs)) / 2, cy=(min(ys) + max(ys)) / 2, dx=max(xs) - min(xs), dy=max(ys) - min(ys))
C = collections.defaultdict(list)
for r in d['R']:
    if r['layer'] != 'S-COL.BON': continue
    q = rect(r)
    if not 35 < q['cy'] < 51.5: continue
    for k, (a, b) in F.items():
        if a <= q['cx'] <= b: C[k].append(q)
json.dump(C, open(WD + '/frames.json', 'w'))
ax = C['AX']; inax = lambda t: 154 <= t['x'] <= 192 and 35 < t['y'] < 52
marks = [t for t in d['T'] if inax(t) and re.match(r'^(C\d*|CN)$', t['s'])]
sizes = [t for t in d['T'] if inax(t) and re.match(r'^\d+X\d+$', t['s'])]
for m in marks:   # p.1 prints the size under the mark
    m['size'] = min(sizes, key=lambda s: math.hypot(s['x'] - m['x'], s['y'] - m['y']) if s['y'] < m['y'] else 99)['s']
def rd(q, x, y):
    return math.hypot(max(abs(x - q['cx']) - q['dx'] / 2, 0), max(abs(y - q['cy']) - q['dy'] / 2, 0))
cm, used = {}, set()
for dd, i, j in sorted((rd(q, t['x'], t['y']), i, j) for i, q in enumerate(ax) for j, t in enumerate(marks)):
    if i in cm or j in used: continue
    cm[i] = (marks[j]['s'], marks[j]['size'], round(dd, 2)); used.add(j)
json.dump(dict(ax=ax, cm={str(k): v for k, v in cm.items()}), open(WD + '/ax.json', 'w'))
print({k: len(v) for k, v in C.items()}, 'marks', len(marks), 'bound', len(cm))
