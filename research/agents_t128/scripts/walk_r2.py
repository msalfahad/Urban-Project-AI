"""T-128 r2 hand-measurement aid (research only, NOT engine code): walk the wall faces of every Alsenan room on the
SAME room regions the checker verified (T-147 rooms.py regions, T-147 ceil_ledger.py clips for the open zones; GF master
bed room = 16.557 m2 / 21.537 m contour = checker 16.549 / 21.535, T-153 16.55) and split each contour into
WALL (layer 1), COLUMN (S-COL.BON face: plastered like the wall), WINDOW (layer W, incl. the curved pool glazing band),
DOOR (door-block closure on the face), GAP (an opening between two collinear wall lines with no door block: arch or
doorway) and VIRTUAL (no drawn line: an open side, never plastered). Door width = the DOOR run on the face, so one door
gives one width to both rooms it serves (checked: pairs listed in the output).
Usage: python -I walk_r2.py <rooms.py> <arch.dxf> <out.json>
Writes lengths only (no coordinates) to <out.json>."""
import sys, json, math, io, contextlib
from shapely.geometry import LineString, Point, Polygon, box, MultiLineString
from shapely.ops import unary_union, linemerge
from shapely import wkt

ROOMS_PY = DXF = OUT = SRC = None    # set in __main__ (importable for check_walk_r2.py)
BOXES = {'GF': (-163, -124, -811, -784), '1F': (-208, -169, -811, -784), '2F': (-253, -214, -811, -784)}


def run_floor(fl):
    x0, x1, y0, y1 = BOXES[fl]
    ns = {'__name__': 'rooms_t147'}
    sys.argv = ['rooms.py', DXF, str(x0), str(x1), str(y0), str(y1), f'/dev/null']
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(compile(SRC, 'rooms.py', 'exec'), ns)
        except Exception:
            # json.dump to /dev/null works; anything else is a real error
            raise
    m = ns['m']; B = ns['B']; pts = ns['pts']
    by = {'1': [], 'S-COL.BON': [], 'W': []}
    for e in m:
        if e.dxftype() == 'RTEXT': continue
        L = e.dxf.layer
        if L in by and e.dxftype() in ('LINE', 'LWPOLYLINE', 'ARC', 'POLYLINE', 'CIRCLE'):
            v = pts(e)
            if len(v) >= 2 and any(B.contains(Point(q)) for q in v):
                by[L].append(LineString(v))
    gaps = ns['gaps']; gapset = {g.wkt for g in gaps}
    doorcl = [c for c in ns['closures'] if c.wkt not in gapset]
    faces = {}
    for f in ns['faces']:
        faces[len(faces)] = f
    drawn = unary_union([g for g in (unary_union(by['1']), unary_union(by['S-COL.BON']), unary_union(by['W']),
                                     unary_union(doorcl), unary_union(gaps) if gaps else None) if g is not None])
    return dict(drawn=drawn, walls=unary_union(by['1']), cols=unary_union(by['S-COL.BON']), wins=unary_union(by['W']),
                doors=unary_union(doorcl), gaps=unary_union(gaps) if gaps else None, faces=ns['faces'],
                doorrecs=ns['doors'])


def face_at(F, x, y, min_area=0.3):
    p = Point(x, y)
    c = [f for f in F['faces'] if f.area > min_area and f.contains(p)]
    c.sort(key=lambda f: f.area)
    return c[0]


OPEN_R = {'GF-16': 0.08, 'GF-07': 0.03, 'GF-08': 0.03, 'GF-14': 0.03, '1F-13': 0.03, 'ST-1F': 0.03, '2F-01': 0.03, 'ST-2F': 0.03}
TOL = 0.005  # the T-147 regions sit on the drawn lines (grown back by BUF with mitred joins)


# r3 (checker 2026-10-22 16:11 on 1F-11): the barrier-buffer region can leak into the glazing-frame cavity at a window
# jamb (two frame lines 2 x BUF apart): a zig-zag notch that adds contour length but almost no area. Rule: a walked
# contour is checked against its area-equivalent drawn faces; a direction reversal across an edge under 0.12 m is an
# artefact, never a wall face. SPIKE_MID = the checker's 0.12 m; REVERSAL = outer edges within 30 deg of antiparallel.
SPIKE_MID, REVERSAL_DEG = 0.12, 150.0


def _dirdeg(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _turn(d1, d2):
    t = abs(d2 - d1) % 360.0
    return min(t, 360.0 - t)


def _on_drawn(drawn, a, b, tol=0.01):
    """an edge lies on a drawn barrier line when its quarter, mid and three-quarter points are within tol of one
    (tol 0.01 > the 0.003 sagitta of a 0.2 m chord on the tightest Alsenan glazing arc; < the 0.015 BUF offset of a
    cavity side, which is what an artefact edge shows)."""
    return all(drawn.distance(Point(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)) <= tol for t in (0.25, 0.5, 0.75))


def spikes(ring_coords, drawn=None):
    """notches in a closed ring: edges (i, i+1, i+2) with edge i+1 under SPIKE_MID and edges i, i+2 reversed (within
    30 deg of antiparallel), or two consecutive edges reversed with one under SPIKE_MID. With `drawn` (the union of
    every barrier line), a reversal whose edges ALL lie on drawn lines is a real face (an acute corner where a curved
    glazing band meets a wall, GF-15) and is not reported. Returns [(i, kind, mid_len)]."""
    c = list(ring_coords)[:-1]
    # drop zero-length edges first (duplicate vertices from the region builder)
    c = [p for k, p in enumerate(c) if math.dist(p, c[k - 1]) > 1e-6]
    n = len(c); out = []
    E = [(c[k], c[(k + 1) % n]) for k in range(n)]
    L = [math.dist(a, b) for a, b in E]; D = [_dirdeg(a, b) for a, b in E]
    drawn_ok = (lambda ks: drawn is not None and all(_on_drawn(drawn, *E[j % n]) for j in ks))
    for k in range(n):
        if L[(k + 1) % n] < SPIKE_MID and _turn(D[k], D[(k + 2) % n]) >= REVERSAL_DEG:
            if not drawn_ok((k, k + 1, k + 2)):
                out.append((k, 'U', round(L[(k + 1) % n], 3)))
        elif min(L[k], L[(k + 1) % n]) < SPIKE_MID and _turn(D[k], D[(k + 1) % n]) >= REVERSAL_DEG:
            if not drawn_ok((k, k + 1)):
                out.append((k, 'V', round(min(L[k], L[(k + 1) % n]), 3)))
    return out


def trim_notches(poly, drawn=None):
    """replace each U notch (edges i, i+1, i+2) by the straight chord from the start of edge i to the end of edge i+2
    (the mouth of the cavity, which lies on the drawn face line); repeat until none is left. Returns (poly, trims)."""
    trims = []
    for _ in range(20):
        c = list(poly.exterior.coords)[:-1]
        c = [p for k, p in enumerate(c) if math.dist(p, c[k - 1]) > 1e-6]
        sp = [s for s in spikes(c + [c[0]], drawn) if s[1] == 'U']
        if not sp:
            break
        k = sp[0][0]; n = len(c)
        drop = {(k + 1) % n, (k + 2) % n}           # the two inner vertices of the notch
        before = sum(math.dist(c[(k + j) % n], c[(k + j + 1) % n]) for j in range(3))
        chord = math.dist(c[k], c[(k + 3) % n])
        trims.append({'edge': k, 'removed_m': round(before - chord, 4), 'chord_m': round(chord, 4)})
        c = [p for j, p in enumerate(c) if j not in drop]
        poly = Polygon(c, [list(r.coords) for r in poly.interiors])
    return poly, trims


NOTCH_TRIM = {'1F-11'}   # rooms where the spike scan found a frame-cavity notch (checker 16:11: only 1F-11 of 32)


def classify(F, poly, step=0.005):
    """walk every ring of poly; returns {class: length}, door runs [(length, nearest door block)], window runs."""
    rings = [poly.exterior] + list(poly.interiors)
    out = {}; runs = []
    for ri, ring in enumerate(rings):
        n = max(4, int(ring.length / step))
        seq = []
        for k in range(n):
            a = ring.interpolate((k + 0.5) * ring.length / n)
            d = {c: (F[g].distance(a) if F[g] is not None and not F[g].is_empty else 9)
                 for c, g in (('DOOR', 'doors'), ('GAP', 'gaps'), ('WINDOW', 'wins'), ('WALL', 'walls'), ('COLUMN', 'cols'))}
            best = min(('WINDOW', 'WALL', 'COLUMN'), key=lambda q: d[q])
            if d[best] <= TOL: c = best          # a drawn wall / column / window line on the face wins
            elif d['DOOR'] <= TOL: c = 'DOOR'    # door-block closure (swing face)
            elif d['GAP'] <= TOL: c = 'GAP'      # opening closed between two collinear wall lines
            else: c = 'VIRTUAL'                  # no drawn line: open side
            seq.append((c, a))
        seg = ring.length / n
        # runs (cyclic)
        start = 0
        while start < n and seq[start][0] == seq[-1][0] and start < n - 1: start += 1
        cur = None; ln = 0; ptsrun = []
        for k in list(range(start, n)) + list(range(0, start)):
            c, a = seq[k]
            if c != cur:
                if cur is not None: runs.append((ri, cur, ln, ptsrun))
                cur, ln, ptsrun = c, 0, []
            ln += seg; ptsrun.append(a)
        runs.append((ri, cur, ln, ptsrun))
        for c, a in seq:
            out[c] = out.get(c, 0) + seg
    return out, runs


def nearest_door(F, pt):
    best = min(F['doorrecs'], key=lambda r: math.dist((r['x'], r['y']), (pt.x, pt.y)))
    return best['name'], round(math.dist((best['x'], best['y']), (pt.x, pt.y)), 2)


if __name__ == '__main__':
    ROOMS_PY, DXF, OUT = sys.argv[1:4]
    SRC = open(ROOMS_PY).read()
    FL = {fl: run_floor(fl) for fl in BOXES}
    G, F1, F2 = FL['GF'], FL['1F'], FL['2F']
    # open-zone clips: copied from T-147 ceil_ledger.py (verified 02:40 / 04:05)
    GF0 = face_at(G, -154.102, -797.494)
    gclip = Polygon([(-148.2, -805.094), (-129.07, -805.094), (-129.07, -797.594), (-131.0, -797.594), (-131.0, -795.9),
                     (-145.05, -795.9), (-145.05, -800.45), (-148.2, -800.45)])
    lob168 = face_at(G, -136.818, -793.617)  # T-147 lobby second part = bath? (checked by area below)
    lobby = unary_union([GF0.intersection(box(-140.6, -796.0, -137.85, -793.0)), face_at(G, -137.94, -793.623)])
    gopen = GF0.intersection(gclip).difference(lobby)
    pantry = gopen.intersection(box(-148.2, -805.2, -145.05, -800.45))
    dining = gopen.difference(pantry)
    F1o = face_at(F1, -186.808, -797.786); sh1 = F1o.intersection(box(-189.893, -797.194, -187.393, -791.994))
    open1 = F1o.difference(sh1)
    F2o = face_at(F2, -233.47, -795.244); sh2 = F2o.intersection(box(-234.745, -797.194, -232.245, -791.994))
    lob2 = F2o.difference(sh2)
    R = [
        ('GF-01', G, face_at(G, -158.04, -802.494)), ('GF-02', G, face_at(G, -155.14, -801.883)),
        ('GF-03', G, face_at(G, -155.14, -803.969)), ('GF-04', G, face_at(G, -153.365, -802.676)),
        ('GF-05', G, face_at(G, -151.59, -804.294)), ('GF-06', G, face_at(G, -150.99, -802.144)),
        ('GF-07', G, pantry), ('GF-08', G, dining),
        ('GF-10', G, face_at(G, -141.665, -792.948)), ('GF-11', G, face_at(G, -141.665, -794.544)),
        ('GF-12', G, face_at(G, -140.424, -792.939)), ('GF-13', G, face_at(G, -139.279, -792.465)),
        ('GF-14', G, lobby), ('GF-15', G, face_at(G, -134.449, -793.956)), ('GF-16', G, face_at(G, -136.818, -793.617)),
        ('ST-GF', G, face_at(G, -143.79, -794.619)),
        ('1F-01', F1, face_at(F1, -192.168, -798.286)), ('1F-02', F1, face_at(F1, -191.068, -801.929)),
        ('1F-03', F1, face_at(F1, -193.268, -802.369)), ('1F-04', F1, face_at(F1, -188.068, -801.654)),
        ('1F-07', F1, unary_union([face_at(F1, -186.268, -792.961), face_at(F1, -184.458, -795.594)])),
        ('1F-08', F1, face_at(F1, -184.458, -792.894)), ('1F-09', F1, face_at(F1, -182.573, -793.254)),
        ('1F-10', F1, face_at(F1, -181.673, -796.094)),
        ('1F-11', F1, unary_union([face_at(F1, -177.864, -793.971), face_at(F1, -178.723, -797.381)])),
        ('1F-12', F1, face_at(F1, -176.548, -797.278)), ('1F-13', F1, open1), ('ST-1F', F1, sh1),
        ('2F-01', F2, lob2), ('2F-02', F2, face_at(F2, -231.12, -793.339)), ('2F-03', F2, face_at(F2, -228.545, -796.638)),
        ('ST-2F', F2, sh2),
    ]
    # GF-08: the T-147 clip keeps a 0.85 m2 piece east of the curved W03 glazing band, i.e. the pool court (exterior)
    DROP_SMALL_PART = {'GF-08': 'pool-court piece east of the W03 glazing band (exterior), inside the T-147 clip'}
    CLIPPED = {'GF-07', 'GF-08', 'GF-14', '1F-13', 'ST-1F', '2F-01', 'ST-2F'}
    # 1F-11: the 1.29 m doorless opening between the bed room and its entry is a 0.15 m strip face (< 0.3 m2, not in
    # the T-147 list); it belongs to the same room, so its two jamb faces are wall and its two edges are not
    mouth = face_at(F1, -178.5, -796.075, min_area=0.05)
    # GF-14: the basin niche (T-147 lobby part) opens to the lobby through a 1.9 m gap in the 0.15 m wall: same strip
    niche = face_at(G, -138.2, -794.0, min_area=0.05)
    print('1F-11 mouth strip m2', round(mouth.area, 4), 'GF-14 niche strip m2', round(niche.area, 4))
    ADD = {'1F-11': mouth, 'GF-14': niche}
    R = [(rid, F, unary_union([poly, ADD[rid]]) if rid in ADD else poly) for rid, F, poly in R]
    res = {}; allops = []; SCAN = {}
    for rid, F, poly in R:
        parts_m2 = round(poly.area, 4)
        if poly.geom_type == 'MultiPolygon':
            # parts of one room separated only by a barrier strip (a door closure or gap line, 2 x BUF = 0.03 m wide):
            # close the strip (mitred, so corners stay); the strip edge is inside the room and is not a wall face
            poly = poly.buffer(0.02, join_style=2).buffer(-0.02, join_style=2)
        # strips under 0.16 m wide are not room: clip slivers along walls, and a wall cavity open at one end (the
        # GF master bath leaks into the 0.15 m double-lined diagonal wall of the basin niche). Opening, mitred.
        # only where needed: an opening also trims the acute corners where a curved glazing band meets a wall (it
        # moved GF-15 off its verified 21.537 m contour when tried on every room)
        raw = poly
        r_open = OPEN_R.get(rid, 0.0)
        if r_open:
            poly = poly.buffer(-r_open, join_style=2).buffer(r_open, join_style=2)
        strip_m2 = round(raw.area - poly.area, 4)
        parts = list(poly.geoms) if poly.geom_type == 'MultiPolygon' else [poly]   # separate parts: walked one by one
        parts = [pp for pp in parts if pp.area > 0.05]
        trims = []
        if rid in NOTCH_TRIM:                     # r3: frame-cavity notches at the W17 jambs (checker 16:11)
            tp = []
            for pp in parts:
                q, t = trim_notches(pp, F['drawn']); tp.append(q); trims += t
            notch_m2 = round(sum(pp.area for pp in parts) - sum(q.area for q in tp), 4)
            parts = tp
        # r3 spike scan over EVERY room (any ring of any walked part): must be empty after the trims
        scan = [s for pp in parts for r in [pp.exterior] + list(pp.interiors) for s in spikes(list(r.coords), F['drawn'])]
        SCAN[rid] = scan
        dropped = [pp for pp in parts if rid in DROP_SMALL_PART and pp.area < 1.0]
        parts = [pp for pp in parts if pp not in dropped]
        tot, runs = {}, []
        for pp in parts:
            t1, r1 = classify(F, pp)
            for k, v in t1.items(): tot[k] = tot.get(k, 0) + v
            runs += r1
        # merge: DOOR / GAP pieces in a row = one opening; a VIRTUAL piece under 0.10 m is corner noise (wall)
        groups = []
        for ri, c, ln, pr in runs:
            g = 'OPEN' if c in ('DOOR', 'GAP') else ('WALLISH' if c in ('WALL', 'COLUMN') or (c == 'VIRTUAL' and ln < 0.10) else c)
            if groups and groups[-1][0] == g and groups[-1][1] == ri and g in ('OPEN', 'WINDOW', 'VIRTUAL'):
                groups[-1][2] += ln; groups[-1][3] += pr; groups[-1][4].add(c)
            else:
                groups.append([g, ri, ln, list(pr), {c}])
        ops = []
        for g, ri, ln, pr, cs in groups:
            if g == 'WALLISH' or ln < 0.10: continue
            mid = pr[len(pr) // 2]
            rec = {'kind': g, 'len': round(ln, 3)}
            if g == 'OPEN':
                nm, dist = nearest_door(F, mid)
                rec['kind'] = 'DOOR' if dist <= ln / 2 + 0.6 else 'GAP'
                rec['door_block'] = nm if rec['kind'] == 'DOOR' else None
                rec['hinge_dist_m'] = dist
            if g == 'WINDOW':
                chord = math.dist((pr[0].x, pr[0].y), (pr[-1].x, pr[-1].y))
                rec['curved'] = (ln - chord) > 0.02
            rec['oid'] = f'{rid}/o{len(ops) + 1}'
            ops.append(rec); allops.append((rid, F is G and 'GF' or F is F1 and '1F' or '2F', rec, mid))
        wallish = sum(v for k, v in tot.items() if k in ('WALL', 'COLUMN')) + sum(
            ln for g, ri, ln, pr, cs in groups if g == 'WALLISH' and cs == {'VIRTUAL'})
        small_open = sum(ln for g, ri, ln, pr, cs in groups if g != 'WALLISH' and ln < 0.10)
        res[rid] = {'area_m2': parts_m2, 'removed_strip_m2': strip_m2, 'dropped_part_m2': round(sum(pp.area for pp in dropped), 4), 'walked_area_m2': round(sum(pp.area for pp in parts), 4),
                    'contour_m': round(sum(pp.length for pp in parts), 3), 'parts': len(parts),
                    'by_class_m': {k: round(v, 3) for k, v in sorted(tot.items())},
                    'paintable_m': round(wallish + small_open, 3), 'openings': ops,
                    'virtual_m': round(sum(o['len'] for o in ops if o['kind'] == 'VIRTUAL'), 3)}
        if trims:
            res[rid]['notch_trims'] = trims
            res[rid]['notch_trim_m'] = round(sum(t['removed_m'] for t in trims), 4)
            res[rid]['notch_trim_m2'] = notch_m2
        print(rid, res[rid]['area_m2'], 'strip', strip_m2, res[rid]['contour_m'], 'paintable', res[rid]['paintable_m'],
              [(o['kind'], o['len'], o.get('door_block') or '', 'curved' if o.get('curved') else '') for o in ops])
    # one opening, one width: the same opening seen from its two rooms (midpoints within 0.35 m on one floor)
    pairs = []
    for i, (ra, fa, oa, ma) in enumerate(allops):
        for rb, fb, ob, mb in allops[i + 1:]:
            if fa == fb and ra != rb and oa['kind'] in ('DOOR', 'GAP') and ob['kind'] in ('DOOR', 'GAP') \
                    and ma.distance(mb) < 0.35:
                pairs.append({'oids': [oa['oid'], ob['oid']], 'rooms': [ra, rb], 'len': [oa['len'], ob['len']], 'kind': [oa['kind'], ob['kind']],
                              'door_block': oa.get('door_block') or ob.get('door_block'),
                              'diff_m': round(abs(oa['len'] - ob['len']), 3)})
    for p in pairs: print('PAIR', p)
    bad = {k: v for k, v in SCAN.items() if v}
    print('SPIKE SCAN', len(SCAN), 'rooms;', 'none left' if not bad else f'LEFT {bad}')
    json.dump({'rooms': res, 'opening_pairs': pairs,
               'spike_scan': {'rooms_scanned': len(SCAN), 'rule': f'U / V reversal across an edge < {SPIKE_MID} m',
                              'left': bad}}, open(OUT, 'w'), indent=1)
    sys.exit(1 if bad else 0)
