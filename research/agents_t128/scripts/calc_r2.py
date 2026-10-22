"""T-128 r2 calc (research only, standard library): plaster / paint / wet-wall tile per Alsenan room by the owner's
manual method (G1) and the drawing-derived method, on the wall faces walked by walk_r2.py over the checker-verified
room regions (T-147 regions, T-153 floors, T-127 court), with the T-144 opening heights and one width per opening.

Usage: python3 -I calc_r2.py <walk_r2.json> <OPENINGS_T144.csv> <trace_lengths.json (r1, roof share only)> <out_dir>
       python3 -I calc_r2.py --check        (synthetic, non-Alsenan fixture; no file read)
Writes <out_dir>/ROOMS_T128_R2.csv, OPENINGS_T128_R2.csv, FLOORS_T128_R2.csv, summary_r2.json.
Statuses (WORKFLOW_CONTROLS s.5): owner manual heights G1 = ASSUMED - OWNER-APPROVED (Q-43, Q-48 A); door head 2.20 m
= ASSUMED - OWNER-APPROVED (Q-55 C); annex datum (G2) and roof datum = HELD with the candidate range; drawing-derived
on a floor slab = DRAWING-CONFIRMED (bounded by the unprinted floor build-up b = 0 .. 0.10 m); stair shaft owner
method HELD (Q-72); an opening with no printed head = HELD (net as bounds: lower = full band, upper = no deduction)."""
import csv, json, sys, os

AOA = 'ASSUMED - OWNER-APPROVED'
DEC, SLAB, B_MAX = 0.15, 0.16, 0.10      # Q-48 A decor depth; ST general note "all slabs 16 cm"; owner Q-43 floor allowance
DOOR_H = 2.20                            # Q-55 C fallback (ASSUMED - OWNER-APPROVED), only where the drawings are silent
ZONE = {  # floor-to-floor on the printed marks; owner manual height; owner status
    'GF_MAIN': (4.50, 3.65, AOA + ' (G1, Q-43 / Q-48 A)'),
    'GF_ANNEX': (4.00, 3.15, 'HELD (G2: +4.30 is a finished roof mark; owner manual 3.15 shown as OWNER MANUAL METHOD - PROVISIONAL)'),
    '1F': (4.20, 3.35, AOA + ' (G1, Q-43 / Q-48 A)'),
    '2F': (4.20, 3.35, AOA + ' (G1, Q-43 / Q-48 A)'),
    'LEVEL_UNCLEAR': (None, None, 'HELD (room level +0.30 or +1.00 not drawn, T-088)'),
    'SHAFT': (None, None, 'HELD (owner Q-72 open: no owner height for a wall through the storeys)')}

# room meta: id, name, kind, zone, r1 trace key (roof share), crossing beams (T-110 / T-112), freelancer gross m2 (his rows)
ROOMS = [
    ('GF-01', 'dewaneya', 'DRY', 'GF_ANNEX', 'GF dewaneya', 'CB6 0.75', 72.00),
    ('GF-02', 'wash by the dewaneya', 'WET', 'GF_ANNEX', 'GF wash by dewaneya', '', 24.30),
    ('GF-03', 'W.C. by the dewaneya', 'WET', 'GF_ANNEX', 'GF WC by dewaneya', '', None),
    ('GF-04', 'driver room', 'DRY', 'GF_ANNEX', 'GF driver', '', 45.00),
    ('GF-05', 'driver W.C.', 'WET', 'GF_ANNEX', 'GF driver WC', '', None),
    ('GF-06', 'kitchen', 'WET', 'GF_ANNEX', 'GF kitchen', '', None),
    ('GF-07', 'pantry (open side to the dining)', 'WET', 'GF_MAIN', 'GF pantry', 'B27 0.85', None),
    ('GF-08', 'open room: dining / entrance / reception / saloon / hall to the master bed room', 'DRY', 'GF_MAIN',
     'GF open room (din)', 'B26 0.85; B27 0.85', 195.30),
    ('GF-15', 'master bed room', 'DRY', 'GF_MAIN', 'GF master bed', '', 75.78),
    ('GF-16', 'bath of the master bed room', 'WET', 'GF_MAIN', 'GF master bath', '', None),
    ('GF-10', 'W.C. 175 x 135 by the stair', 'WET', 'LEVEL_UNCLEAR', 'GF WC 175x135 by stair', '', None),
    ('GF-11', 'basin space 110 x 135', 'WET', 'LEVEL_UNCLEAR', 'GF basin 110x135', '', None),
    ('GF-12', 'W.C. core wedge A (289 x 167)', 'WET', 'GF_MAIN', 'GF WC wedge A', '', None),
    ('GF-13', 'W.C. core wedge B (245 x 167)', 'WET', 'GF_MAIN', 'GF WC wedge B', '', None),
    ('GF-14', 'wash lobby, 2 basins, with the basin niche', 'WET', 'GF_MAIN', 'GF wash lobby', 'B11 0.75', None),
    ('1F-01', 'master bed room west 425 x 450', 'DRY', '1F', '1F mbed W 425x450', 'B6 0.50', 59.50),
    ('1F-04', 'master bed room 500 x 365', 'DRY', '1F', '1F mbed 500x365', '', 58.82),
    ('1F-10', 'master bed room 380 x 430', 'DRY', '1F', '1F mbed 380x430', 'B19 0.75; B6 0.50', 75.82),
    ('1F-11', 'master bed room east (curved W17) with its entry', 'DRY', '1F', '1F mbed E', '', 74.46),
    ('1F-07', 'laundry', 'WET', '1F', '1F laundry', '', None),
    ('1F-08', 'W.C. 147 x 180', 'WET', '1F', '1F WC 147x180', '', None),
    ('1F-02', 'bath west upper 245 x 205', 'WET', '1F', '1F bath W upper', '', None),
    ('1F-03', 'bath west lower 245 x 205', 'WET', '1F', '1F bath W lower', '', None),
    ('1F-12', 'bath east 210 x 225', 'WET', '1F', '1F bath E 210x225', '', None),
    ('1F-09', 'bath by the laundry 200 x 180', 'WET', '1F', '1F bath by laundry', '', None),
    ('1F-13', 'living + corridor + landing + connector (open zone, outside the shaft box)', 'DRY', '1F', '1F living zone',
     'B25 / CB12 0.75 on edges', 140.875 + 31.79),
    ('2F-03', 'maid room 300 x 645', 'DRY', '2F', '2F maid', 'B2 0.40', 64.26),
    ('2F-02', 'W.C. 300 x 185', 'WET', '2F', '2F WC 300x185', '', None),
    ('2F-01', '2F stair lobby (outside the shaft box)', 'DRY', '2F', '2F lobby', 'B15 1.20', 30.60),
    ('ST-GF', 'stair shaft, GF part', 'SHAFT', 'SHAFT', None, '', 40.50),
    ('ST-1F', 'stair shaft, 1F part', 'SHAFT', 'SHAFT', None, '', None),
    ('ST-2F', 'stair shaft, 2F part (to the roof)', 'SHAFT', 'SHAFT', None, '', None),
]
SHAFT_FTF = {'ST-GF': 4.50, 'ST-1F': 4.20, 'ST-2F': None}   # ST-2F: top storey, to the decor ceiling under the roof

# every walked opening -> (opening id, class, T-144 key or None). classes: door / main / arch / doorway / lift /
# window / wall (a walked piece that is a wall face) / virtual (open side, not a wall)
OPS = {
    'GF-01': [('W11', 'window', 'W11'), ('W12', 'window', 'W12'), ('D120 entrance', 'door', None), ('arch to wash', 'arch', None)],
    'GF-02': [('D315 to W.C.', 'door', None), ('arch to dewaneya', 'arch', None)],
    'GF-03': [('D315', 'door', None)],
    'GF-04': [('W04', 'window', 'W04'), ('d220 entrance', 'door', None), ('D315 to W.C.', 'door', None)],
    'GF-05': [('D315', 'door', None)],
    'GF-06': [('W08', 'window', 'W08'), ('D120', 'door', None)],
    'GF-07': [('D120', 'door', None), ('open side to the dining', 'virtual', None), ('W10', 'window', 'W10'), ('W09', 'window', 'W09')],
    'GF-08': [('D01 main entrance', 'main', 'D01 main entrance'), ('D120 to stair hall', 'door', None),
              ('lift landing door', 'lift', None), ('open side to the wash lobby', 'virtual', None),
              ('D115 to master bed', 'door', None), ('W03 pool glazing band (open-room part)', 'window', 'W03'),
              ('W02 saloon glazing', 'window', 'W02 saloon glazing'), ('open side to the pantry', 'virtual', None),
              ('D01 main entrance', 'main', 'D01 main entrance')],
    'GF-10': [('W05-07', 'window', 'W05-07'), ('D315', 'door', None)],
    'GF-11': [('D315 to W.C.', 'door', None), ('doorway to the stair hall (no leaf drawn)', 'doorway', None)],
    'GF-12': [('D315', 'door', None)],
    'GF-13': [('diagonal face with no wall line (door-closure copy; T-074 wall face)', 'wall', None),
              ('W05-07', 'window', 'W05-07'), ('D315', 'door', None)],
    'GF-14': [('open side to the open room', 'virtual', None), ('D315 wedge A', 'door', None), ('D315 wedge B', 'door', None)],
    'GF-15': [('bath door (loose arc)', 'door', None), ('W03 pool glazing band (bed-room part)', 'window', 'W03'),
              ('D115', 'door', None)],
    'GF-16': 'T074',
    'ST-GF': [('D120 north door', 'door', None), ('doorway to the basin space (no leaf drawn)', 'doorway', None),
              ('D120 to the open room', 'door', None), ('W01', 'window', 'W01')],
    '1F-01': [('D115 (landing)', 'door', None), ('D315 to bath', 'door', None), ('W14', 'window', 'W14')],
    '1F-02': [('W19-23', 'window', 'W19-23'), ('D315', 'door', None)],
    '1F-03': [('D315', 'door', None), ('W19-23', 'window', 'W19-23')],
    '1F-04': [('D115', 'door', None), ('W24', 'window', 'W24'), ('D315 to bath', 'door', None)],
    '1F-07': [('W19-23', 'window', 'W19-23'), ('D315 to W.C.', 'door', None), ('d220', 'door', None)],
    '1F-08': [('D315', 'door', None), ('W19-23', 'window', 'W19-23')],
    '1F-09': [('W19-23', 'window', 'W19-23'), ('D315', 'door', None)],
    '1F-10': [('D215', 'door', None), ('arch120 to the dressing passage', 'arch', None)],
    '1F-11': [('W17', 'window', 'W17 (inner face)'), ('D315 to bath', 'door', None), ('D215', 'door', None)],
    '1F-12': [('W18', 'window', 'W18'), ('D315', 'door', None)],
    '1F-13': [('lift landing door', 'lift', None), ('d220 laundry', 'door', None), ('D215 bed 380 x 430', 'door', None),
              ('D215 bed east', 'door', None), ('W15', 'window', 'W15'), ('W16 (twin of W15)', 'window', 'W16 (twin of W15)'),
              ('D115 bed 500 x 365', 'door', None), ('D115 bed west (landing part)', 'door', None),
              ('open side to the stair shaft box', 'virtual', None)],
    'ST-1F': [('W13', 'window', 'W13'), ('north window', 'window', 'north window'),
              ('open side to the landing (clip)', 'virtual', None), ('D115 bed west (shaft part)', 'door', None)],
    '2F-01': [('open side to the stair shaft box', 'virtual', None), ('lift landing door', 'lift', None),
              ('d220 maid', 'door', None), ('D26 roof door', 'door', None)],
    '2F-02': [('W28', 'window', 'W28'), ('D315', 'door', None)],
    '2F-03': [('d220', 'door', None), ('D315 to W.C.', 'door', None), ('W29', 'window', 'W29')],
    'ST-2F': [('W26 arched', 'window', 'W26 arched'), ('W27', 'window', 'W27'), ('open side to the lobby (clip)', 'virtual', None)],
}
# GF-16: the T-147 region leaks into the 0.15 m double-lined walls round the basin niche (4.5958 m2 vs 3.7173); the
# verified T-074 hand outline is used: 2.10 x 2.00 less the 0.982 x 0.983 corner = 3.7173 m2, contour 7.6245 m
T074_GF16 = {'contour': 7.6245, 'ops': [('W05-07', 'window', 'W05-07', 0.60), ('bath door (loose arc)', 'door', None, None)]}
SAMPLE_LOSS = 0.01   # the 5 mm walk loses about 5 mm at each end of an opening run (checked: 0.79 / 0.99 / 0.89 faces
                     # of 0.80 / 1.00 / 0.90 frames = leaf 0.69 / 0.89 / 0.79 + 0.11); the wall runs carry it


def r2(x): return round(x + 1e-9, 2)


def door_widths(walk):
    """one width per opening: the frame width = the wider of its two faces (+ sample loss). A door the shaft clip
    cuts (1F-01 D115: 1F-13 part + ST-1F part) keeps one width, its face parts scaled to it."""
    W = {}
    for rid, v in walk['rooms'].items():
        for o in v['openings']:
            if o['kind'] in ('DOOR', 'GAP'):
                W[o['oid']] = r2(o['len'] + SAMPLE_LOSS)
    groups = {}
    for p in walk['opening_pairs']:
        a, b = p['oids']
        ga = groups.get(a, {a}); gb = groups.get(b, {b}); g = ga | gb
        for x in g: groups[x] = g
    split = {'1F-13/o8', 'ST-1F/o4'}
    out, share = {}, {}
    for oid in W:
        g = groups.get(oid, {oid})
        lens = {x: next(o['len'] for v in walk['rooms'].values() for o in v['openings'] if o['oid'] == x) for x in g}
        parts = [x for x in g if x in split]
        whole = [lens[x] for x in g if x not in split]
        # the clipped door's wide face is the two parts together (1.005 m walked): rounded to the 0.05 m frame size
        width = r2(round(sum(lens[x] for x in parts) / 0.05) * 0.05) if parts else r2(max(whole) + SAMPLE_LOSS)
        out[oid] = width
        share[oid] = r2(width * lens[oid] / sum(lens[x] for x in parts)) if oid in parts else width
        out[oid + '#faces'] = sorted(lens.values())
    return out, share


def band(w, sill, head, H):
    if sill is None or head is None or H is None: return None
    return w * max(0.0, min(head, H) - max(sill, 0.0))


def nets(gross, ops, H):
    """gross - known bands; held openings as bounds (lower = full band 0 .. H, upper = no deduction). Returns
    (net_lo, net_hi, known, held_ids)."""
    if gross is None or H is None: return None, None, None, []
    known = 0.0; held = []; held_full = 0.0
    for o in ops:
        if o['cls'] in ('virtual', 'wall'): continue
        d = band(o['w'], o['sill'], o['head'], H)
        if d is None:
            held.append(o['id']); held_full += o['w'] * H
        else:
            known += d
    return gross - known - held_full, gross - known, known, held


def fmt(lo, hi):
    if lo is None: return 'HELD'
    return f'{lo:.2f}' if abs(hi - lo) < 0.005 else f'{lo:.2f} .. {hi:.2f}'


def heights(zone, rid=None):
    if zone == 'SHAFT':
        f = SHAFT_FTF[rid]
        if f is None: return (4.20 - SLAB - B_MAX - DEC, 4.20 - SLAB - DEC, 4.20 - SLAB)
        return (f, f, f)
    ftf = ZONE[zone][0]
    if ftf is None: return None
    return (ftf - SLAB - B_MAX - DEC, ftf - SLAB - DEC, ftf - SLAB)


def build(walk, t144, trace):
    widths, share = door_widths(walk)
    H144 = {}
    for r in t144:
        H144[(r['ROOM_ROW'], r['OPENING'])] = r
    rows, oprows = [], []
    for rid, name, kind, zone, tkey, beams, fl in ROOMS:
        v = walk['rooms'][rid]
        if OPS[rid] == 'T074':
            face = T074_GF16['contour']; virt = 0.0; ops = []
            for oid, cls, key, w in T074_GF16['ops']:
                if w is None: w = widths['GF-15/o1']      # same opening, walked from the bed room (0.79 / 0.79 faces)
                ops.append(dict(id=oid, cls=cls, key=key, w=w, walked='T-074 outline', faces=''))
            contour = face; src = 'T-074 verified hand outline (T-147 region leaks into the niche walls)'
        else:
            contour = v['contour_m']; ops = []
            assert len(OPS[rid]) == len(v['openings']), (rid, len(OPS[rid]), len(v['openings']))
            for (oid, cls, key), o in zip(OPS[rid], v['openings']):
                if cls in ('door', 'main', 'arch', 'doorway', 'lift'):
                    assert o['kind'] in ('DOOR', 'GAP'), (rid, oid, o)
                    w = share[o['oid']]; faces = widths[o['oid'] + '#faces']
                elif cls == 'window':
                    assert o['kind'] == 'WINDOW', (rid, oid, o); w = o['len']; faces = [o['len']]
                elif cls == 'virtual':
                    assert o['kind'] == 'VIRTUAL', (rid, oid, o); w = o['len']; faces = [o['len']]
                else:
                    w = o['len']; faces = [o['len']]
                ops.append(dict(id=oid, cls=cls, key=key, w=w, walked=o['len'], faces=faces, curved=o.get('curved', False)))
            virt = sum(o['w'] for o in ops if o['cls'] == 'virtual')
            src = 'walked on the T-147 region (verified boundary)'
        # the main entrance is walked as two runs (ring start splits it): one opening of 2.00 m, printed 2.50 high
        mains = [o for o in ops if o['cls'] == 'main']
        if mains:
            wm = r2(round(sum(o['walked'] for o in mains) / 0.05) * 0.05)   # 1.11 + 0.89 walked = the printed 2.00
            ops = [o for o in ops if o['cls'] != 'main'] + [dict(id='D01 main entrance', cls='main', key='D01 main entrance',
                                                                 w=wm, walked=sum(o['walked'] for o in mains), faces=[wm])]
        face = contour - virt                         # wall face incl. openings (gross basis), open sides excluded
        # opening heights (sill / head above the room floor)
        for o in ops:
            o['sill'] = o['head'] = None; o['status'] = ''
            if o['cls'] in ('door',):
                o['sill'], o['head'], o['status'] = 0.0, DOOR_H, AOA + ' (Q-55 C door head 2.20)'
            elif o['cls'] == 'main':
                o['sill'], o['head'], o['status'] = 0.0, 2.50, 'DRAWING-CONFIRMED (printed 2.00 x 2.50, SE p.6, T-144)'
            elif o['cls'] == 'arch':
                o['status'] = 'HELD (arch head not printed, T-144)'
            elif o['cls'] == 'doorway':
                o['status'] = 'HELD (doorless opening: no leaf drawn, head not printed; Q-55 C is a door rule)'
            elif o['cls'] == 'lift':
                o['status'] = 'HELD (lift landing door: head not printed; lift supplier item)'
            elif o['cls'] == 'window':
                r = H144.get((rid, o['key'])) or H144.get(('GF-15', 'W03 pool-side glazing (face share)') if o['key'] == 'W03' else None)
                if r is None or r['STATUS'] in ('HELD', 'INFERRED'):
                    o['status'] = 'HELD (no head / sill printed, T-144)' if (r is None or r['STATUS'] == 'HELD') else \
                        'HELD (INFERRED twin of W15, candidate 0.00 / 3.10; Q-17, RFI-3)'
                else:
                    o['sill'], o['head'] = float(r['SILL_M']), float(r['HEAD_OR_CROWN_M'])
                    o['status'] = 'DRAWING-CONFIRMED (' + r['STATUS'].lower() + ' sill / head, T-144)'
            elif o['cls'] == 'wall':
                o['status'] = 'wall face (counted in the paintable length)'
            elif o['cls'] == 'virtual':
                o['status'] = 'open side: not a wall, not plastered'
        paintable = face - sum(o['w'] for o in ops if o['cls'] not in ('virtual', 'wall'))
        ftf, Ho, ost = ZONE[zone]
        hs = heights(zone, rid)
        roof = 0.0
        if tkey and trace.get(tkey):
            ds = trace[tkey].get('datum_split_m', {}); tot = sum(ds.values())
            roof = ds.get('ROOF', 0.0) / tot if tot else 0.0
        if zone == 'GF_ANNEX': roof = 1.0
        if rid == 'ST-2F': roof = 1.0
        # owner method
        g_own = face * Ho if Ho else None
        n_own = nets(g_own, ops, Ho)
        if g_own is None: own_status = ost
        elif zone == 'GF_ANNEX': own_status = ost
        else: own_status = ost if not n_own[3] else 'HELD (net: ' + ', '.join(n_own[3]) + ' height not printed); gross ' + AOA
        # drawing-derived (paint / tile height range, plaster to the soffit)
        if hs:
            lo, hi, pl = hs
            g_lo, g_hi, g_pl = face * lo, face * hi, face * pl
            n_lo = nets(g_lo, ops, lo); n_hi = nets(g_hi, ops, hi)
            conf_share = 1.0 - roof
            dstat = ('DRAWING-CONFIRMED (bounded: floor build-up 0 .. 0.10 m not printed, DCR-7)' if roof < 0.005 else
                     'HELD (roof datum: ' + f'{roof:.0%}' + ' of the face under a finished roof mark; roof build-up not printed, DCR-6 / G2)'
                     if roof > 0.995 else
                     f'SPLIT: {conf_share:.0%} of the face DRAWING-CONFIRMED (bounded b), {roof:.0%} HELD (roof datum DCR-6)')
            if zone == 'SHAFT' and rid != 'ST-2F':
                dstat = 'DRAWING-CONFIRMED (storey interval on the printed marks; landing-edge bands UNKNOWN, not deducted)'
            dn_stat = dstat if not n_lo[3] else 'HELD (net: ' + ', '.join(n_lo[3]) + ' height not printed)'
        else:
            lo = hi = pl = None; g_lo = g_hi = g_pl = None; n_lo = n_hi = (None, None, None, []); conf_share = None
            dstat = dn_stat = 'HELD (room level not drawn, T-088)'
        # candidate range where the level is not drawn: +0.30 (annex heights) or +1.00 (main) = both ends
        cand = ''
        if zone == 'LEVEL_UNCLEAR':
            cand = f"owner {face * 3.15:.2f} (annex 3.15) .. {face * 3.65:.2f} (main 3.65); drawing {face * heights('GF_ANNEX')[0]:.2f} .. {face * heights('GF_MAIN')[1]:.2f}"
        if zone == 'SHAFT':
            cand = 'owner method HELD on Q-72; candidates: storey interval (drawing-derived) or the room line of the floor'
        rows.append(dict(
            ROW=rid, ROOM=name, KIND=kind, ZONE=zone, SOURCE=src, CONTOUR_M=round(contour, 3), OPEN_SIDES_M=round(virt, 3),
            FACE_M=round(face, 3), PAINTABLE_M=round(paintable, 3), UNDER_ROOF_SHARE=round(roof, 2),
            OPENINGS='; '.join(f"{o['id']} {o['w']:.2f}" for o in ops if o['cls'] not in ('virtual', 'wall')),
            OWNER_H_M=Ho if Ho else 'HELD', OWNER_GROSS_M2=round(g_own, 2) if g_own else 'HELD',
            OWNER_NET_M2=fmt(n_own[0], n_own[1]) if g_own else 'HELD', OWNER_STATUS=own_status,
            DWG_PAINT_TILE_H_M=f'{lo:.2f} .. {hi:.2f}' if hs else 'HELD', DWG_PLASTER_H_TOP_M=f'{pl:.2f}' if hs else 'HELD',
            DWG_GROSS_M2=fmt(g_lo, g_hi) if hs else 'HELD', DWG_NET_M2=fmt(n_lo[0], n_hi[1]) if hs else 'HELD',
            DWG_PLASTER_GROSS_HI_M2=round(g_pl, 2) if (hs and kind != 'WET') else '', DWG_STATUS=dn_stat,
            DWG_GROSS_STATUS=dstat, CANDIDATE_RANGE=cand, CROSSING_BEAMS=beams,
            FREELANCER_GROSS_M2=fl if fl is not None else '',
            _g_own=g_own, _n_own=n_own, _g=(g_lo, g_hi, g_pl), _n=(n_lo, n_hi), _roof=roof, _ops=ops, _face=face))
        for o in ops:
            oprows.append(dict(ROOM_ROW=rid, OPENING=o['id'], CLASS=o['cls'], WIDTH_M=round(o['w'], 3),
                               WALKED_FACE_M=o['walked'], FACES_OF_THIS_OPENING_M='/'.join(f'{x:.3f}' for x in o['faces']) if isinstance(o['faces'], list) else o['faces'],
                               CURVED='yes' if o.get('curved') else '', SILL_M='' if o['sill'] is None else o['sill'],
                               HEAD_M='' if o['head'] is None else o['head'], STATUS=o['status']))
    return rows, oprows


def floors(rows):
    """per floor and kind: owner gross / net bounds, drawing-derived gross / net bounds, each by status bucket."""
    S = {}
    for r in rows:
        fl = r['ROW'][:2] if not r['ROW'].startswith('ST') else 'ST'
        k = (fl, 'DRY' if r['KIND'] in ('DRY', 'SHAFT') else 'WET')
        s = S.setdefault(k, dict(rooms=0, face_m=0, own_gross_aoa=0, own_gross_held=0, own_held_rooms=0, own_net_lo=0, own_net_hi=0,
                                 dwg_gross_conf_lo=0, dwg_gross_conf_hi=0, dwg_gross_held_lo=0, dwg_gross_held_hi=0,
                                 dwg_net_lo=0, dwg_net_hi=0, dwg_held_rooms=0, freelancer_same_rooms=0))
        s['rooms'] += 1; s['face_m'] += r['_face']
        g = r['_g_own']
        if g is None: s['own_held_rooms'] += 1
        elif r['ZONE'] == 'GF_ANNEX': s['own_gross_held'] += g
        else:
            s['own_gross_aoa'] += g; s['own_net_lo'] += r['_n_own'][0]; s['own_net_hi'] += r['_n_own'][1]
        g_lo, g_hi, _ = r['_g']
        if g_lo is None: s['dwg_held_rooms'] += 1
        else:
            c = 1.0 - r['_roof']
            if r['ZONE'] == 'SHAFT' and r['ROW'] != 'ST-2F': c = 1.0
            s['dwg_gross_conf_lo'] += g_lo * c; s['dwg_gross_conf_hi'] += g_hi * c
            s['dwg_gross_held_lo'] += g_lo * (1 - c); s['dwg_gross_held_hi'] += g_hi * (1 - c)
            s['dwg_net_lo'] += r['_n'][0][0]; s['dwg_net_hi'] += r['_n'][1][1]
        if r['FREELANCER_GROSS_M2'] != '': s['freelancer_same_rooms'] += float(r['FREELANCER_GROSS_M2'])
    return {f'{a}|{b}': {kk: round(vv, 2) for kk, vv in v.items()} for (a, b), v in sorted(S.items())}


def check():
    """synthetic villa K (not Alsenan), by hand: room 4.00 x 3.00 m, one side a curved glazing face of 3.20 m (sill 0,
    head 4.00), one door 0.90 seen from two rooms as 0.89 / 0.84 faces, one window 1.20 with no printed head."""
    ok = True
    def eq(a, b, t=1e-6):
        nonlocal ok
        if abs(a - b) > t: ok = False; print('FAIL', a, b)
    walk = {'rooms': {'K-1': {'openings': [{'oid': 'K-1/o1', 'kind': 'DOOR', 'len': 0.89}]},
                      'K-2': {'openings': [{'oid': 'K-2/o1', 'kind': 'DOOR', 'len': 0.84}]}},
            'opening_pairs': [{'oids': ['K-1/o1', 'K-2/o1']}]}
    w, sh = door_widths(walk)
    eq(w['K-1/o1'], 0.90); eq(w['K-2/o1'], 0.90)                        # one door, one width, both rooms
    ops = [dict(id='door', cls='door', w=0.90, sill=0.0, head=2.20), dict(id='glazing', cls='window', w=3.20, sill=0.0, head=4.00),
           dict(id='W-x', cls='window', w=1.20, sill=None, head=None), dict(id='open', cls='virtual', w=1.0, sill=None, head=None)]
    face = 4.0 + 3.0 + 4.0 + 3.2 - 0.0                                   # walls 11.0 + curved face 3.20 (incl. the door)
    H = 3.35; g = face * H
    lo, hi, known, held = nets(g, ops, H)
    eq(known, 0.90 * 2.20 + 3.20 * 3.35)                                 # glazing head above H: full band
    eq(hi, g - known); eq(lo, g - known - 1.20 * 3.35); assert held == ['W-x']
    assert lo is not None and lo > 0                                     # held never becomes 0
    # mirror / rotation do not change a length; a missing height holds, never zero
    assert nets(None, ops, H) == (None, None, None, [])
    assert band(1.0, None, 2.0, H) is None
    eq(band(1.0, 1.40, 3.00, 3.35), 1.60); eq(band(1.0, 0.0, 3.50, 3.35), 3.35)   # head above the wall line is capped
    eq(heights('1F')[0], 4.20 - 0.16 - 0.10 - 0.15); eq(heights('GF_MAIN')[1], 4.50 - 0.16 - 0.15)
    print('check', 'PASS' if ok else 'FAIL'); return ok


if __name__ == '__main__':
    if sys.argv[1:] == ['--check']:
        sys.exit(0 if check() else 1)
    walk = json.load(open(sys.argv[1])); t144 = list(csv.DictReader(open(sys.argv[2]))); trace = json.load(open(sys.argv[3]))
    out = sys.argv[4]; os.makedirs(out, exist_ok=True)
    rows, oprows = build(walk, t144, trace)
    pub = [{k: v for k, v in r.items() if not k.startswith('_')} for r in rows]
    with open(f'{out}/ROOMS_T128_R2.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(pub[0])); w.writeheader(); w.writerows(pub)
    with open(f'{out}/OPENINGS_T128_R2.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(oprows[0])); w.writeheader(); w.writerows(oprows)
    F = floors(rows)
    with open(f'{out}/FLOORS_T128_R2.csv', 'w', newline='') as f:
        keys = list(next(iter(F.values())))
        w = csv.writer(f); w.writerow(['FLOOR|KIND'] + keys)
        for k, v in F.items(): w.writerow([k] + [v[x] for x in keys])
    # engine vs freelancer, same rooms (gross before openings, his rows) and r1 -> r2 per room
    cmp = {}
    for r in rows:
        if r['FREELANCER_GROSS_M2'] == '' or r['KIND'] == 'WET': continue   # his dry plaster rows, as r1
        fl = r['ROW'][:2] if not r['ROW'].startswith('ST') else 'ST'
        c = cmp.setdefault(fl, dict(owner=0.0, owner_has_held=False, dwg_lo=0.0, dwg_hi=0.0, freelancer=0.0, rooms=[]))
        if r['_g_own'] is None: c['owner_has_held'] = True
        else: c['owner'] += r['_g_own']
        if r['_g'][0] is not None: c['dwg_lo'] += r['_g'][0]; c['dwg_hi'] += r['_g'][1]
        c['freelancer'] += float(r['FREELANCER_GROSS_M2']); c['rooms'].append(r['ROW'])
    for c in cmp.values():
        for k in ('owner', 'dwg_lo', 'dwg_hi', 'freelancer'): c[k] = round(c[k], 2)
    house = dict(dwg_gross_lo=round(sum(r['_g'][0] for r in rows if r['KIND'] in ('DRY', 'SHAFT') and r['_g'][0] is not None), 2),
                 dwg_gross_hi=round(sum(r['_g'][1] for r in rows if r['KIND'] in ('DRY', 'SHAFT') and r['_g'][1] is not None), 2),
                 dwg_net_lo=round(sum(r['_n'][0][0] for r in rows if r['KIND'] in ('DRY', 'SHAFT') and r['_n'][0][0] is not None), 2),
                 dwg_net_hi=round(sum(r['_n'][1][1] for r in rows if r['KIND'] in ('DRY', 'SHAFT') and r['_n'][1][1] is not None), 2),
                 owner_gross_dry_excl_shaft=round(sum(r['_g_own'] for r in rows if r['KIND'] == 'DRY' and r['_g_own']), 2),
                 owner_net_dry_lo=round(sum(r['_n_own'][0] for r in rows if r['KIND'] == 'DRY' and r['_g_own']), 2),
                 owner_net_dry_hi=round(sum(r['_n_own'][1] for r in rows if r['KIND'] == 'DRY' and r['_g_own']), 2),
                 wet_owner_gross=round(sum(r['_g_own'] for r in rows if r['KIND'] == 'WET' and r['_g_own']), 2),
                 wet_dwg_gross_lo=round(sum(r['_g'][0] for r in rows if r['KIND'] == 'WET' and r['_g'][0] is not None), 2),
                 wet_dwg_gross_hi=round(sum(r['_g'][1] for r in rows if r['KIND'] == 'WET' and r['_g'][1] is not None), 2),
                 freelancer_plaster_gross=1209.39, freelancer_plaster_net=1151.14, freelancer_paint_net=1191.13,
                 freelancer_wet_spatter=433.83)
    r1 = {}
    r1p = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'ROOMS_T128.csv')
    if os.path.exists(r1p):
        for x in csv.DictReader(open(r1p)): r1[x['ROW']] = x
    ch = []
    for r in rows:
        a = r1.get(r['ROW'])
        if not a: continue
        f1 = float(a['FACE_LENGTH_M']); g1 = a['OWNER_GROSS_M2']
        ch.append(dict(ROW=r['ROW'], ROOM=r['ROOM'], R1_FACE_M=f1, R2_FACE_M=round(r['_face'], 3), DIFF_M=round(r['_face'] - f1, 3),
                       R1_OWNER_GROSS_M2=g1, R2_OWNER_GROSS_M2=r['OWNER_GROSS_M2'],
                       R1_OWNER_NET_M2=a['OWNER_NET_M2'], R2_OWNER_NET_M2=r['OWNER_NET_M2'], R2_SOURCE=r['SOURCE']))
    with open(f'{out}/CHANGES_R1_R2.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(ch[0])); w.writeheader(); w.writerows(ch)
    json.dump({'floors': F, 'vs_freelancer_same_rooms': cmp, 'house': house, 'pairs': walk['opening_pairs']},
              open(f'{out}/summary_r2.json', 'w'), indent=1)
    print(json.dumps(cmp)); print(json.dumps(house))
    for k, v in F.items(): print(k, v)
