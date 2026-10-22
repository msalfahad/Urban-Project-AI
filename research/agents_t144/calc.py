"""T-144 calc: Alsenan openings for finishes. One row per opening on each room face (sheet + reading), then the net
plaster / paint (dry) and wall-tile (wet) m2 per room by BOTH methods (owner manual G1 and drawing-derived), with the
openings this census releases. Standard library only. Inputs: T128_ROOMS_INPUT.csv (worker 3's T-128 room table,
69c1a0a: face lengths, heights, gross) and the opening readings typed below with their source.

Run: python3 -I calc.py T128_ROOMS_INPUT.csv OPENINGS_T144.csv ROOMS_T144.csv summary.json

Rules: UP-OPEN-SCHED-001 wall_finish_deduction = face length x (min(head, H) - max(sill, 0)); Q-32 A (arched opening =
enclosing rectangle to the crown); Q-55 C (door head 2.20 m ASSUMED only when the drawings are silent; main entrance
2.50 printed); Q-17 status words (INFERRED kept apart, never released); UP-QTY-STATUS-001 (held = bounds, never 0)."""
import csv, json, sys

ASSUMED = 'ASSUMED (Q-55 C: 2.20 m, drawings silent)'
HELD = 'HELD: no head / sill printed on any sheet'
ARCH = 'HELD: arch head not printed; sections draw it without dimension; not to scale (sanitary NOTES, T-091 F2)'

def D(w, oid, src=ASSUMED, sill=0.0, head=2.20, status='ASSUMED'):
    return dict(id=oid, kind='door', w=w, sill=sill, head=head, status=status, src=src)
def W(w, oid, sill=None, head=None, status='HELD', src=HELD, kind='window'):
    return dict(id=oid, kind=kind, w=w, sill=sill, head=head, status=status, src=src)
def A(w, oid):
    return dict(id=oid, kind='arch', w=w, sill=0.0, head=None, status='HELD', src=ARCH)

# --- readings (levels above the room's own finished floor; GF main +1.00, annex +0.30, 1F +5.50, 2F +9.70) ---
SE = 'SE elevation (Pages_05-06 p.6 scan, and DXF SE frame)'
NW = 'NW elevation (Pages_07-08 p.8 scan, and DXF NW frame)'
W03 = W(3.96, 'W03 pool-side glazing (face share)', 0.0, 4.30, 'PRINTED',
        NW + ': chain 115 / 70 / 430 / 20 on the pool axis, +1.00 to +5.30; DXF 4300 from +1.00. Width basis Q-38 A '
        '(printed 6.57) answered; this face carries 3.96 m of it (T-128 trace)')
W14 = W(2.45, 'W14', 1.40, 3.00, 'PRINTED (CORRECTED)',
        SE + ': GF-side chain 85 / 250 / 55 / 65 / 220 / 160 / 139 / 104 / 193 / 155 from +0.15 = +6.90 to +8.50; '
        'DXF 2201.4 / 1598.6 (+6.90 / +8.50). T-083 / T-128 read the 4th part as 45 (sill +6.70, head 2.80): the chain '
        'only closes on the printed 14.40 top with 65')
W15 = W(1.55, 'W15', 0.0, 3.10, 'PRINTED',
        NW + ': chain 300 + 10 starts ON the +5.50 floor line (DXF 3000 from y(+5.50), jamb feet of both twins at '
        '+5.50); crown +8.60 (Q-32 A). T-128 had the sill "not printed"')
W16 = W(1.55, 'W16 (twin of W15)', 0.0, 3.10, 'INFERRED',
        NW + ': width "155" printed; no height chain through it; DXF jamb feet, springing and frame levels identical '
        'to W15 (same 9 level values). Q-17 INFERRED: candidate only, not released (RFI-3 stands)')
W17 = W(3.32, 'W17 (inner face)', 0.0, 3.50, 'PRINTED (CORRECTED)',
        NW + ': chain 115 / 70 / 430 / 20 / 305 / 45: the "20" is the slab band between the pool glazing head +5.30 and '
        'the 1F floor +5.50, so W17 runs +5.50 to +9.00 (DXF 3050.5 + 454.3 from y(+5.50)). T-128 took sill 0.20 / '
        'crown 3.70')
W18 = W(0.50, 'W18', 0.84, 3.00, 'PRINTED', NW + ': chain 84 / 216 / 230: +6.34 to +8.50 (DXF 839.3 / 2160.7)')
W01 = W(1.20, 'W01', 1.00, 3.00, 'PRINTED', SE + ': chain 185 / 200 from +0.15: +2.00 to +4.00 (DXF 1850 / 2000)')
W13 = W(1.20, 'W13', 1.00, 3.30, 'PRINTED', SE + ': chain 250 / 230: +6.50 to +8.80 (DXF 2500 / 2300)')
W26 = W(1.20, 'W26 arched', 1.10, 2.80, 'PRINTED (RFI-1 closed)',
        SE + ': chain 200 / 170 from +8.80: sill +10.80, crown +12.50. DXF SE: opening jambs 1.20 apart (layer 1), '
        'opening arch apex +12.50 (= end of the printed 170); the 12.55 / 12.95 / 13.00 arcs are the surround '
        'mouldings, which T-078 read as the crown. Freelancer also 1.20 x 1.70')
D01 = D(2.00, 'D01 main entrance', SE + ': chain 85 / 250 from +0.15: +1.00 to +3.50 (DXF 850 / 2500)', 0.0, 2.50,
        'PRINTED')

OPEN = {
 'GF-01': [D(1.00, 'D120'), A(1.00, 'arch to wash'), W(1.95, 'W11'), W(1.95, 'W12')],
 'GF-02': [A(1.00, 'arch to dewaneya'), D(0.80, 'D315')],
 'GF-03': [D(0.80, 'D315')],
 'GF-04': [D(0.90, 'd220'), D(0.80, 'D315'), W(0.60, 'W04')],
 'GF-05': [D(0.80, 'D315')],
 'GF-06': [D(1.00, 'D120'), W(1.50, 'W08')],
 'GF-07': [D(1.00, 'D120'), W(1.50, 'W09'), W(1.00, 'W10')],
 'GF-08': [D01, D(1.00, 'D120 to stair hall'), D(1.00, 'D115 to master bed'), W(6.33, 'W02 saloon glazing'),
           W(0.93, 'other glazing (plan)')],
 'GF-15': [D(1.00, 'D115'), D(0.68, 'bath door (loose arc, D15)'), W03],
 'GF-16': [D(0.80, 'bath door'), W(0.60, 'W05-07')],
 'GF-10': [D(0.80, 'D315'), W(0.60, 'W05-07')],
 'GF-12': [D(0.80, 'D315'), W(0.60, 'W05-07')],
 'GF-13': [D(0.80, 'D315')],
 'GF-14': [D(0.80, 'D315'), D(0.80, 'D315')],
 'GF-11': [D(0.80, 'D315 W.C.'), D(1.00, 'D120 to open room')],
 '1F-01': [D(1.00, 'D115'), D(0.80, 'D315'), W14],
 '1F-04': [D(1.00, 'D115'), D(0.80, 'D315'), W(1.55, 'W24')],
 '1F-10': [D(0.90, 'D215'), A(1.00, 'arch120 to the dressing passage')],
 '1F-11': [D(0.90, 'D215'), D(0.80, 'D315'), W17],
 '1F-07': [D(0.90, 'd220'), D(0.80, 'D315'), W(0.60, 'W19-23')],
 '1F-08': [D(0.80, 'D315'), W(0.60, 'W19-23')],
 '1F-02': [D(0.80, 'D315'), W(0.60, 'W19-23')],
 '1F-03': [D(0.80, 'D315'), W(0.60, 'W19-23')],
 '1F-12': [D(0.80, 'D315'), W18],
 '1F-09': [D(0.80, 'D315'), W(0.60, 'W19-23')],
 '1F-13': [D(0.90, 'D215'), D(0.90, 'D215'), D(0.90, 'd220'), D(1.00, 'D115'), W15, W16],
 '2F-03': [D(0.90, 'd220'), D(0.80, 'D315'), W(1.20, 'W29')],
 '2F-02': [D(0.80, 'D315'), W(0.60, 'W28')],
 '2F-01': [D(1.00, 'D26 roof door'), D(0.90, 'd220')],
 'ST-GF': [D(1.00, 'D120 north door'), W01],
 'ST-1F': [D(1.00, 'D115 to bed room'), W13, W(1.00, 'north window')],
 'ST-2F': [W26, W(1.00, 'W27')],
}
# drawing-derived heights (T-128 section 2): paint / tile height range and plaster upper bound per zone
DWG = {'GF_MAIN': (4.09, 4.19, 4.34), 'GF_ANNEX': (3.59, 3.69, 3.84), '1F': (3.79, 3.89, 4.04), '2F': (3.79, 3.89, 4.04)}
SHAFT = {'ST-GF': (4.50, 4.50, 4.50), 'ST-1F': (4.20, 4.20, 4.20), 'ST-2F': (3.79, 3.89, 4.04)}
FLOOR = {'GF_MAIN': 'GF', 'GF_ANNEX': 'GF', 'LEVEL_UNCLEAR': 'GF', '1F': '1F', '2F': '2F'}


def band(o, H):
    """UP-OPEN-SCHED-001: deduction of one opening at wall height H; None when its head is unknown."""
    if o['head'] is None or o['sill'] is None:
        return None
    return o['w'] * max(0.0, min(o['head'], H) - max(o['sill'], 0.0))


def net(gross, ops, H, use_inferred):
    """(lower, upper, candidate) of the net; unknown openings: lower = full band from the floor to H, upper = 0."""
    known = full = 0.0
    cand = 0.0
    for o in ops:
        b = band(o, H)
        if o['status'] == 'INFERRED':
            cand += b
            full += o['w'] * H
        elif b is None:
            full += o['w'] * H
        else:
            known += b
    lo, hi = gross - known - full, gross - known
    return lo, hi, (gross - known - cand if use_inferred else None)


def status(ops):
    if any(o['head'] is None for o in ops):
        return 'HELD'
    if any(o['status'] == 'INFERRED' for o in ops):
        return 'HELD (INFERRED candidate)'
    if any(o['status'] == 'ASSUMED' for o in ops):
        return 'PROVISIONAL (door heads ASSUMED, Q-55 C)'
    return 'MEASURED'


def f2(x):
    return None if x is None else round(x, 2)


def main(inp, out_open, out_rooms, out_sum):
    rows = {r['ROW']: r for r in csv.DictReader(open(inp, encoding='utf-8'))}
    orows, rrows, summ = [], [], {}
    for rid, ops in OPEN.items():
        r = rows[rid]
        L = float(r['FACE_LENGTH_M'])
        kind, zone = r['KIND'], r['ZONE']
        st = status(ops)
        for o in ops:
            orows.append(dict(ROOM_ROW=rid, ROOM=r['ROOM'], OPENING=o['id'], KIND=o['kind'], FACE_WIDTH_M=o['w'],
                              SILL_M=o['sill'] if o['head'] is not None else '', HEAD_OR_CROWN_M=o['head'] if o['head'] is not None else '',
                              STATUS=o['status'], SOURCE=o['src']))
        rec = dict(ROW=rid, ROOM=r['ROOM'], KIND=kind, ZONE=zone, FACE_LENGTH_M=L, OPENINGS_STATUS=st)
        # owner manual method
        if r['OWNER_H_M'] and zone != 'SHAFT':
            Ho = float(r['OWNER_H_M'])
            g = L * Ho
            assert abs(g - float(r['OWNER_GROSS_M2'])) < 0.01, (rid, g, r['OWNER_GROSS_M2'])
            lo, hi, c = net(g, ops, Ho, True)
            rec.update(OWNER_H_M=Ho, OWNER_GROSS_M2=f2(g), OWNER_NET_LO=f2(lo), OWNER_NET_HI=f2(hi),
                       OWNER_NET_CANDIDATE=f2(c), OWNER_STATUS=r['OWNER_STATUS'], T128_OWNER_NET=r['OWNER_NET_M2'])
        else:
            rec.update(OWNER_H_M='HELD', OWNER_STATUS=r['OWNER_STATUS'], T128_OWNER_NET=r['OWNER_NET_M2'])
        # drawing-derived method (paint / tile height; plaster to the soffit as the upper range)
        hz = SHAFT.get(rid) or DWG.get(zone)
        if hz:
            plo, phi, pl = hz
            lo1, _, c1 = net(L * plo, ops, plo, True)
            _, hi2, c2 = net(L * phi, ops, phi, True)
            rec.update(DWG_H_M=f'{plo:.2f} .. {phi:.2f}', DWG_GROSS_LO=f2(L * plo), DWG_GROSS_HI=f2(L * phi),
                       DWG_NET_LO=f2(lo1), DWG_NET_HI=f2(hi2), DWG_NET_CAND_LO=f2(c1), DWG_NET_CAND_HI=f2(c2),
                       DWG_STATUS=r['DWG_STATUS'])
            if kind != 'WET':
                _, hi3, c3 = net(L * pl, ops, pl, True)
                rec.update(DWG_PLASTER_NET_HI=f2(hi3), DWG_PLASTER_CAND_HI=f2(c3))
        else:
            rec.update(DWG_H_M='HELD', DWG_STATUS=r['DWG_STATUS'])
        rrows.append(rec)
        key = f"{'SHAFT' if zone == 'SHAFT' else FLOOR[zone]}|{kind if zone != 'SHAFT' else 'DRY'}"
        s = summ.setdefault(key, dict(rooms=0, rooms_measured_or_provisional=0, rooms_held=0, rooms_inferred=0,
                                      rooms_height_held_owner=0, rooms_height_held_dwg=0,
                                      own_gross=0.0, own_net_known=0.0, own_held_lo=0.0, own_held_hi=0.0,
                                      own_inferred_cand=0.0, dwg_net_known_lo=0.0, dwg_net_known_hi=0.0,
                                      dwg_held_lo=0.0, dwg_held_hi=0.0, dwg_inferred_cand_lo=0.0,
                                      dwg_inferred_cand_hi=0.0))
        s['rooms'] += 1
        inferred = st.startswith('HELD (INFERRED')
        held = st.startswith('HELD') or zone == 'LEVEL_UNCLEAR'
        s['rooms_held'] += held and not inferred
        s['rooms_inferred'] += inferred
        s['rooms_measured_or_provisional'] += not held
        if not inferred:
            for k in ('OWNER_NET_CANDIDATE', 'DWG_NET_CAND_LO', 'DWG_NET_CAND_HI', 'DWG_PLASTER_CAND_HI'):
                if k in rec:
                    rec[k] = None
        if 'OWNER_NET_LO' in rec:
            s['own_gross'] += rec['OWNER_GROSS_M2']
            if not held:
                s['own_net_known'] += rec['OWNER_NET_LO']
            else:
                s['own_held_lo'] += rec['OWNER_NET_LO']; s['own_held_hi'] += rec['OWNER_NET_HI']
                if inferred:
                    s['own_inferred_cand'] += rec['OWNER_NET_CANDIDATE']
        else:
            s['rooms_height_held_owner'] += 1
        if 'DWG_NET_LO' in rec:
            if not held:
                s['dwg_net_known_lo'] += rec['DWG_NET_LO']; s['dwg_net_known_hi'] += rec['DWG_NET_HI']
            else:
                s['dwg_held_lo'] += rec['DWG_NET_LO']; s['dwg_held_hi'] += rec['DWG_NET_HI']
                if inferred:
                    s['dwg_inferred_cand_lo'] += rec['DWG_NET_CAND_LO']; s['dwg_inferred_cand_hi'] += rec['DWG_NET_CAND_HI']
        else:
            s['rooms_height_held_dwg'] += 1
    for s in summ.values():
        for k, v in list(s.items()):
            if isinstance(v, float):
                s[k] = round(v, 2)
    with open(out_open, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(orows[0]))
        w.writeheader(); w.writerows(orows)
    fields = []
    for r in rrows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(out_rooms, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rrows)
    json.dump(summ, open(out_sum, 'w'), indent=1, sort_keys=True)
    for k in sorted(summ):
        print(k, summ[k])


if __name__ == '__main__':
    main(*sys.argv[1:5])
