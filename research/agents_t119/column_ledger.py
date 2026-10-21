"""T-119 hand-reading helper (research only, NOT engine code): Alsenan columns per storey to the controlling member.

Inputs (scratchpad, never committed): frames.json / ax.json (prep_frames.py) (column outlines of the three roof-slab plans and the
column-and-axis plan p.1, marks + printed sizes bound by position), bands.json (route G beam bands mapped to drawing
metres, research/agents_t110/scripts/bands.py), the T-110 beam member register, T-139 PANELS.csv + faces.json (slab t).
Every decision below that is not geometry (turn / planted / dead columns, held zones, conflicts) is written out in
DECISIONS, each read by eye on ST p.1 / p.4-6 / p.9.  Rules: URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1,
URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1, UP-QTY-STATUS-001, owner Q-54 B, Q-61 C.
Usage: python -I column_ledger.py <workdir> <t110 register csv> <t139 PANELS.csv> <out dir>"""
import csv, json, math, sys, collections
from shapely.geometry import Polygon, box
from shapely import wkt as W

WD, REG, PAN, OUT = sys.argv[1:5]
F = json.load(open(WD + '/frames.json')); AX = json.load(open(WD + '/ax.json'))
ax = AX['ax']; cm = {int(k): v for k, v in AX['cm'].items()}
bands = json.load(open(WD + '/bands.json'))
faces = json.load(open(WD + '/faces.json'))
pan = {r['id']: r for r in csv.DictReader(open(PAN))}
reg = list(csv.DictReader(open(REG)))

INTERVAL = {'GF': 4.50, '1F': 4.20, '2F': 4.20}   # T-064 DRAWING-VERIFIED (levels +1.00 / +5.50 / +9.70, chain 4200)
# ST p.9 Schedule of Columns, read by eye this run (cm): storey band b x h
SCHED = {'GF': {'C': (20, 50), 'C1': (20, 50), 'C2': (20, 50), 'C3': (25, 50), 'C4': (25, 50), 'C5': (25, 60),
                'C6': (25, 70), 'C7': (25, 80), 'C8': (25, 90), 'C9': (25, 100), 'C10': (25, 70), 'C11': (25, 110)},
         '1F': {'C1': (20, 50), 'C2': (20, 50), 'C3': (20, 50), 'C4': (20, 50), 'C5': (20, 50), 'C6': (20, 60),
                'C7': (20, 80), 'C8': (20, 90), 'C9': (20, 90)},
         '2F': {'C1': (20, 50), 'C2': (20, 50), 'C3': (20, 50), 'C4': (20, 50), 'C5': (20, 50), 'C6': (20, 50),
                'C7': (20, 60), 'C8': (20, 70), 'C9': (20, 70)}}
# named candidate depths of HELD unlabelled pieces (T-110 evidence column); None = depth not settled by any print
HELD_CAND = {'BM-GF-057': [0.40, 0.75], 'BM-GF-058': None, 'BM-GF-059': [0.75], 'BM-1F-032': [0.40],
             'BM-1F-033': None, 'BM-1F-034': None, 'BM-1F-035': [0.50, 0.75], 'BM-2F-015': [0.40, 0.75],
             'BM-2F-016': [0.40, 1.20], 'BM-2F-017': [0.40], 'BM-2F-018': [0.40]}
SCHED_DEPTH = {'BM-GF-054': 0.75, 'BM-GF-055': 0.50, 'BM-GF-056': 0.75, 'BM-1F-030': 0.50, 'BM-1F-031': 0.50}

def offset(sh):
    c = collections.Counter(round(p['cx'] - q['cx'], 2) for q in F[sh] for p in ax if abs(p['cy'] - q['cy']) < 0.2)
    return c.most_common(1)[0][0]

def rect(q): return box(q['cx'] - q['dx'] / 2, q['cy'] - q['dy'] / 2, q['cx'] + q['dx'] / 2, q['cy'] + q['dy'] / 2)

def regrows(sh, bid):
    out = []
    for r in reg:
        c = r['component']
        if not c.startswith(f'BEAMS:{sh}:'): continue
        tail = c.split(':')[2]
        parts = tail.split('+')
        base = parts[0].rsplit('.', 1)[0] if '.' in parts[0] else parts[0]
        if tail == bid or bid in [base + p if p.startswith('.') else p for p in parts] or (len(parts) > 1 and bid.startswith(base)):
            out.append(r)
    return out

def framing(sh, geom):
    fr = {}
    for k, b in bands.items():
        bid, st = k.split('@')
        if st != sh: continue
        P = Polygon(b['pts']);  P = P if P.is_valid else P.buffer(0)
        if P.distance(geom) <= 0.03:
            for r in regrows(sh, bid):
                fr[r['member_id']] = r
    return fr

# pieces with no route G band (T-110 'no engine band', T-139 CB5 span 2 gap), drawn edges from those registers
NOBAND = {'GF': [('BM-GF-061', 'unlabelled outer west strip', 'HELD', None, box(52.493, 41.248, 52.693, 45.348)),
                 ('CB5-span2 (T-139 gap)', 'CB5 span 2', 'IN NO BEAM ROW', [0.40], box(52.693, 41.248, 52.893, 44.948))],
          '1F': [('BM-1F-037', 'unlabelled rounded box outside CB12', 'HELD', None, box(33.239, 43.535, 33.639, 44.535)),
                 ('BM-1F-038', 'unlabelled 0.10 strip outside CB12', 'HELD', None, box(33.239, 37.748, 33.339, 43.535))],
          '2F': []}

def slab_t(sh, geom):
    ts = set()
    for f in faces[sh]:
        p = pan.get(f['id'])
        if p and p['cls'] == 'SLAB' and W.loads(f['wkt']).distance(geom) <= 0.45:
            ts.add(float(p['t']))
    return sorted(ts)

# --- decisions read by eye (ST p.1, p.4-6, legend T.C / D.C / P.C) ---
# turn columns (T.C on p.4): GF column = p.1 orientation; the second outline on the GF sheet is the 1F column start.
TURN_GF = {(67.51, 45.62): 'C9 T.C (p.4): GF column horizontal 1.00 as p.1, 1F column vertical',
           (71.79, 44.12): 'C8 T.C (p.4): GF column horizontal 0.90 as p.1, 1F column vertical'}
PLANTED = {('GF', 57.06, 37.95): ('1F', 'P.C 20x70', (20, 70), 'planted on B27 (p.4 leader "P.C 20x70 10%%c16")'),
           ('GF', 71.71, 37.95): ('1F', 'P.C 20x50', (20, 50), 'planted on B26 (p.4 leader "P.C 20x50 8%%c16")'),
           ('1F', 26.37, 45.03): ('2F', 'P.C 20x50', (20, 50), 'planted on B19 (p.5 text "P.C 20x50")')}
ANNEX = {(44.99, 42.95), (42.19, 42.85), (42.29, 36.45), (46.54, 41.12), (48.14, 36.45), (52.77, 40.95), (52.77, 38.10)}
C8_3080 = 'C8 at the lower neighbour side: p.1 prints 30X80, schedule C8 30 x 90 / 25 x 90 / 20 x 90 (designer D-16)'

rows = []
for sh in ['GF', '1F', '2F']:
    o = offset(sh)
    outl = sorted(F[sh], key=lambda q: (-q['cy'], q['cx']))
    used = set()
    for q in outl:
        cx, cy = round(q['cx'], 2), round(q['cy'], 2)
        g = rect(q)
        note = []
        pk = (sh, round(q['cx'], 2), round(q['cy'], 2))
        if pk in PLANTED:
            continue                               # base of a planted column of the storey above: counted there
        i = min(range(len(ax)), key=lambda i: math.hypot(ax[i]['cx'] - q['cx'] - o, ax[i]['cy'] - q['cy']))
        err = math.hypot(ax[i]['cx'] - q['cx'] - o, ax[i]['cy'] - q['cy'])
        mark, p1 = cm[i][0], cm[i][1]
        if err > 0.30:
            # no column of p.1 under it: the start of a planted column of the storey above (PLANTED) or a planted
            # column of this storey already added below; never a column of this storey by itself
            print('  not on p.1:', sh, round(q['cx'], 3), round(q['cy'], 3), round(err, 2)); continue
        if sh == 'GF':
            tk = next((k for k in TURN_GF if abs(k[0] - cx) < 0.2 and abs(k[1] - cy) < 0.05), None)
            if tk:
                if tk in used: continue            # second outline of the same turn column
                used.add(tk)
                twins = [x for x in outl if abs(x['cx'] - q['cx']) < 0.2 and abs(x['cy'] - q['cy']) < 0.05]
                g = twins[0] and rect(twins[0]).union(rect(twins[1]))
                note.append(TURN_GF[tk] + '; framing read on both outlines (the joint)')
        sec = SCHED[sh].get(mark)
        rows.append(dict(storey=sh, mark=mark, p1=p1, cx=q['cx'], cy=q['cy'], dx=q['dx'], dy=q['dy'], geom=g, sec=sec, note=note, axerr=err))
# planted columns as columns of the storey above, framing on the sheet where they are drawn as columns
for (sh0, x, y), (sh, mk, sec, why) in PLANTED.items():
    q = next(q for q in F[{'GF': '1F', '1F': '2F'}[sh0]] if abs(q['cx'] - (x + (offset(sh0) - offset({'GF': '1F', '1F': '2F'}[sh0])))) < 0.05 and abs(q['cy'] - y) < 0.05)
    rows.append(dict(storey=sh, mark=mk, p1='', cx=q['cx'], cy=q['cy'], dx=q['dx'], dy=q['dy'], geom=rect(q), sec=sec, note=[why], axerr=0))

led = []
for n, r in enumerate(rows, 1):
    sh = r['storey']; fr = framing(sh, r['geom'])
    if r['sec'] is None:
        print('NO SECTION', sh, r['mark'], r['cx'], r['cy']); continue
    b, h = r['sec']; A = b * h / 1e4
    calc, held = [], []
    for mid, m in sorted(fr.items()):
        if m['status'] == 'CALCULATED':
            calc.append((mid, m['mark'], float(m['depth_m'])))
        elif mid in SCHED_DEPTH:
            # width conflict only (Q-61 C(1)); the schedule depth H is the same on both readings, so it is a
            # settled depth for the controlling-member test while the member itself stays CONFLICT
            calc.append((mid, m['mark'] + ' [CONFLICT width]', SCHED_DEPTH[mid]))
            held.append((mid, m['mark'], 'CONFLICT width only', [SCHED_DEPTH[mid]]))
        else:
            held.append((mid, m['mark'] if m['mark'] != '(none)' else 'unlabelled', m['status'], HELD_CAND.get(mid)))
    for mid, mk, st, cd, g2 in NOBAND[sh]:
        if g2.distance(r['geom']) <= 0.03:
            held.append((mid, mk, st, cd))
    D_calc = max([d for _, _, d in calc], default=None)
    ts = slab_t(sh, r['geom'])
    t = ts[0] if len(ts) == 1 else None
    cands = [D_calc] if D_calc else []
    affected = []
    for mid, mk, st, cd in held:
        if cd is None: affected.append(f'{mid} depth not printed'); continue
        if max(cd) > (D_calc or 0) + 1e-9: affected.append(f'{mid} candidate D {max(cd):.2f}')
        cands += cd
    D_lo = D_calc if D_calc else min(cands) if cands else None
    D_hi = max(cands) if cands else None
    iv = INTERVAL[sh]
    status, why = 'CALCULATED', ''
    key2 = (round(r['cx'], 2), round(r['cy'], 2))
    if sh == 'GF' and any(abs(key2[0] - a) < 0.05 and abs(key2[1] - c) < 0.05 for a, c in ANNEX):
        status, why = 'HELD', 'GF annex zone (+0.30 floor, roof +4.30): storey interval waits on owner Q-54 B'
    elif r['mark'] == 'C8' and r['p1'] == '30X80':
        status, why = 'CONFLICT', C8_3080
    elif held:
        status = 'HELD'
        why = 'framing member ' + ', '.join(f'{a} ({b}, {c})' for a, b, c, _ in held) + ('; controlling depth changes: ' + '; '.join(affected) if affected else '; controlling depth NOT changed by it (D_ctrl settled by calculated members)')
    if not calc and not held:
        status, why = 'HELD', 'no framing member found'
    h_lo = iv - (D_hi if D_hi else 0); h_hi = iv - (D_lo if D_lo else 0)
    col_lo, col_hi = A * h_lo, A * h_hi
    if not ts:
        j_lo, j_hi, tt = A * (D_lo or 0), A * (D_hi or 0), 'none within 0.45 m (joint = A x D_ctrl)'
    elif t is None:
        j_lo = A * ((D_lo or 0) - max(ts)); j_hi = A * ((D_hi or 0) - min(ts)); tt = f'{min(ts)}..{max(ts)}' if ts else 'none'
    else:
        j_lo, j_hi, tt = A * ((D_lo or 0) - t), A * ((D_hi or 0) - t), f'{t}'
    if r['mark'] == 'C8' and r['p1'] == '30X80':     # section conflict: give both sections at the settled depth
        b2, h2 = b, 80
        col_lo = b2 * h2 / 1e4 * h_lo
    led.append(dict(id=f'COL-{sh}-{n:02d}', storey=sh, mark=r['mark'], p1_print=r['p1'], x=round(r['cx'], 3), y=round(r['cy'], 3),
                    drawn=f"{r['dx']:.2f}x{r['dy']:.2f}", section=f'{b/100:.2f}x{h/100:.2f}', A_m2=round(A, 4),
                    framing='; '.join(f'{a} {b} D{c:.2f}' for a, b, c in calc) + ('' if not held else ' | held: ' + '; '.join(f'{a} {b} {c} cand {d}' for a, b, c, d in held)),
                    D_ctrl=f'{D_lo:.2f}' if D_lo == D_hi else f'{D_lo:.2f}..{D_hi:.2f}' if D_lo is not None else '',
                    controlling='; '.join(a for a, b, c in calc if D_calc and abs(c - D_calc) < 1e-9),
                    interval=iv, height=f'{h_hi:.2f}' if abs(h_hi - h_lo) < 1e-9 else f'{h_lo:.2f}..{h_hi:.2f}',
                    slab_t=tt, col_m3_lo=round(col_lo, 4), col_m3_hi=round(col_hi, 4), joint_m3_lo=round(j_lo, 4), joint_m3_hi=round(j_hi, 4),
                    full_interval_m3=round(A * iv, 4), status=status, reason=why, notes='; '.join(r['note'])))

import os; os.makedirs(OUT, exist_ok=True)
with open(OUT + '/COLUMNS_TO_CONTROLLING_MEMBER.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(led[0])); w.writeheader(); w.writerows(led)
summ = {}
for sh in ['GF', '1F', '2F', 'ALL']:
    L = [r for r in led if sh == 'ALL' or r['storey'] == sh]
    def s(k, st=None): return round(sum(r[k] for r in L if st is None or r['status'] == st), 4)
    summ[sh] = dict(n=len(L), n_calc=sum(r['status'] == 'CALCULATED' for r in L),
                    col_calc=s('col_m3_lo', 'CALCULATED'), joint_calc=s('joint_m3_lo', 'CALCULATED'),
                    col_all_lo=s('col_m3_lo'), col_all_hi=s('col_m3_hi'), joint_all_lo=s('joint_m3_lo'), joint_all_hi=s('joint_m3_hi'),
                    full_interval=s('full_interval_m3'), held_n=sum(r['status'] != 'CALCULATED' for r in L))
json.dump(summ, open(OUT + '/ledger_summary.json', 'w'), indent=1)
for r in led: print(r['id'], r['mark'], r['section'], r['D_ctrl'], r['height'], r['col_m3_lo'], r['col_m3_hi'], r['joint_m3_lo'], r['slab_t'], r['status'], '|', r['framing'][:120])
print(json.dumps(summ, indent=1))
