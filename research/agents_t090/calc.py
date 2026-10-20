"""T-090 hand calculation: wall m2 per Alsenan room under each owner wall-height option (Q-52 A / B / C, Q-54 A).

Run: python3 -I research/agents_t090/calc.py  -> writes ROOMS_T090.csv next to this file and prints the sums.
Inputs are typed here from the drawings (sheet references in SOURCES); nothing is read from the engine or from the
freelancer's workbook except the FREELANCER column, which is shown for comparison only and never used in a sum.
Standard library only. No client names, no coordinates.
"""
import csv, os

DECOR = 0.15        # owner Q-48 A: decor ceiling 0.15 m in every room
FLOOR_FIN = 0.10    # owner heights rule 2026-10-19 21:40: 0.10 m floor finishing
STD_BEAM = 0.60     # owner standard beam deduction (heights rule; Q-52 option A)

# floor-to-floor (slab to slab) from the level marks; T-088 section 1 (sections A-A sheet 10, B-B page 11)
FTF = {'GF_MAIN': 4.50, 'GF_ANNEX': 4.00, '1F': 4.20, '2F': 4.20}
FTF_SRC = {
    'GF_MAIN': "+1.00 to +5.50 = 4.50 (A-A sheet 10 '450'; B-B page 11 '450')",
    'GF_ANNEX': "+0.30 to +4.30 = 4.00 (B-B page 11 '400'): ONLY under owner Q-54 A; Q-54 B holds it",
    '1F': "+5.50 to +9.70 = 4.20 (A-A, B-B '420')",
    '2F': "+9.70 to +13.90 = 4.20 (A-A '420')",
}

# One row per drawn room (the 32 rooms of T-088, same ids).
# zone, room, kind (DRY = plaster + paint, UP-FIN-PAINT-001; WET = full-height wall tile, UP-FIN-WALL-001 / Q-48 A),
# deepest beam at the room (m) and whether a beam deeper than 0.60 CROSSES the ceiling (T-088 beam table, ST7757 roof
# slab plans), wall length (m, gross perimeter of the printed rectangle / outline) and its source, hold reason.
R = [
 # id, zone, room, kind, deepest, crossing_deep (m or None), length, length_src, hold
 ('GF-01','GF_ANNEX','dewaneya','DRY',0.75,0.75,20.128,"sheet 03: 400 x 630 printed; corner arc R1.10 (inner arc 1.728, DXF): 2x(4.00+6.30)-2x1.10+1.728 (T-088); DXF faces checked (T-090)",None),
 ('GF-02','GF_ANNEX','wash by the dewaneya (basin-only, Q-06 wet)','WET',0.75,None,7.20,"sheet 03: 150 x 210 (T-074); DXF 4-sided check (T-090)",None),
 ('GF-03','GF_ANNEX','W.C. by the dewaneya','WET',0.75,None,7.50,"sheet 03: 150 x 225; DXF 4-sided check (T-090)",None),
 ('GF-04','GF_ANNEX','driver room','DRY',0.75,None,12.50,"sheet 03: 175 x 450 printed; DXF faces checked (T-090)",None),
 ('GF-05','GF_ANNEX','driver W.C. 130 x 150','WET',0.75,None,5.60,"sheet 03: 130 x 150; DXF 4-sided check (T-090)",None),
 ('GF-06','GF_ANNEX','kitchen (Q-30 wet)','WET',0.75,None,14.50,"sheet 03: 300 x 270 + 105 x 150 less two piers (T-074)",None),
 ('GF-07','GF_MAIN','pantry (open to the dining, Q-37)','WET',0.85,0.85,None,"sheet 03: 450 x 300 with one side open","NOT_CLOSED: no wall on the dining side (owner Q-37)"),
 ('GF-08','GF_MAIN','dining / reception / saloon open room','DRY',0.85,0.85,None,"sheet 03: partial runs 1082 / 1597 / 790 / 745 / 895 / 515 / 381 / 347; no closed run","NOT_CLOSED + DOUBLE_HEIGHT: open to the stair, the garden strip and the 1F void (reception); no owner rule for a double-height wall"),
 ('GF-09','STAIR','GF stair hall','DRY',0.75,None,None,"sheet 03: landings 125 / 195 / 250 / 330 / 120","STAIR_SHAFT: walls run +0.30 to +13.90; no owner height rule for a stair-shaft wall"),
 ('GF-10','GF_LEVEL_HELD','W.C. 175 x 135 by the stair','WET',0.50,None,6.20,"sheet 03: 175 x 135; DXF 4-sided check (T-090)","LEVEL_UNCLEAR (+0.30 or +1.00; owner Q-43: unclear stays held)"),
 ('GF-11','GF_LEVEL_HELD','basin space 110 x 135 by the stair (Q-06 wet)','WET',0.40,None,4.90,"sheet 03: 110 x 135; DXF: NOT a closed rectangle (open to the passage on one side): 4.90 is an upper bound (T-090)","LEVEL_UNCLEAR (as GF-10)"),
 ('GF-12','GF_MAIN','W.C. core wedge 289 x 167','WET',0.50,None,7.414,"drawn wall faces (T-074 hand trace)",None),
 ('GF-13','GF_MAIN','W.C. core wedge 245 x 167','WET',0.50,None,6.810,"drawn wall faces (T-074)",None),
 ('GF-14','GF_MAIN','wash, core lobby with 2 basins (Q-06 wet)','WET',0.75,0.75,9.500,"drawn outline (T-074)",None),
 ('GF-15','GF_MAIN','master bed room','DRY',0.75,None,None,"sheet 03: straight runs 482 / 558 / 400 / 185 / 200 printed; curved pool wall: arc 657 printed (W03 glazing)","NOT_CLOSED: the 1.85 m lobby and the curved pool wall are not closed by printed runs (the 657 arc is the glazing line, Q-38 A; the solid wall stubs beside it are not dimensioned)"),
 ('GF-16','GF_MAIN','bath of the master bed room','WET',0.75,None,7.6245,"T-074 (210 x 200 less the diagonal corner)",None),
 ('1F-01','1F','master bed room west 425 x 450','DRY',0.75,None,17.50,"sheet 04: 425 x 450 printed; DXF faces checked (T-090)",None),
 ('1F-02','1F','bath west upper 245 x 205','WET',0.50,None,9.00,"sheet 04: 245 x 205; DXF 4-sided check (T-090)",None),
 ('1F-03','1F','bath west lower 245 x 205','WET',0.50,None,9.00,"sheet 04: 245 x 205; DXF 4-sided check (T-090)",None),
 ('1F-04','1F','master bed room 500 x 365','DRY',0.75,None,17.30,"sheet 04: 500 x 365 printed; DXF faces checked (T-090)",None),
 ('1F-05','1F','corridor / stair landing','DRY',0.75,None,None,"sheet 04: runs 195 / 125 / 240 / 305 / 147","NOT_CLOSED: open to the stair and the living area"),
 ('1F-06','STAIR','1F stair hall','DRY',0.75,None,None,"-","STAIR_SHAFT (as GF-09)"),
 ('1F-07','1F','laundry','WET',0.50,None,16.94,"T-074 (347 x 300 / 185 less the W.C. corner)",None),
 ('1F-08','1F','W.C. 147 x 180','WET',0.50,None,6.54,"sheet 04: 147 x 180; DXF 4-sided check (T-090)",None),
 ('1F-09','1F','bath by the laundry 200 x 180','WET',0.50,None,7.60,"T-074 (200 x 180 less a jamb)",None),
 ('1F-10','1F','master bed room 380 x 430','DRY',0.75,0.75,16.20,"sheet 04: 380 x 430 printed (room rectangle; the 1.47 x 3.05 passage not in it); DXF 4-sided check (T-090)",None),
 ('1F-11','1F','master bed room east 420 x 400 + 1.80 passage','DRY',0.75,None,None,"sheet 04: runs 420 / 400 / 345 / 180; curved glazing W17 to the void","NOT_CLOSED: the curved wall around W17 is not dimensioned as a wall run"),
 ('1F-12','1F','bath east 210 x 225','WET',0.75,None,8.70,"sheet 04: 210 x 225; DXF 4-sided check (T-090)",None),
 ('1F-13','1F','living area','DRY',0.75,None,None,"sheet 04: runs 480 / 520 / 365 / 240","NOT_CLOSED: open to the void and the curved stair"),
 ('2F-01','STAIR','2F stair lobby 450 x 195','DRY',1.20,None,None,"page 5: 450 x 195 printed, open to the stair","STAIR_SHAFT + NOT_CLOSED (B15 1.20 deep on its edge)"),
 ('2F-02','2F','W.C. 300 x 185','WET',0.75,None,9.70,"page 5: 300 x 185; DXF 4-sided check (T-090)",None),
 ('2F-03','2F','maid room 300 x 645','DRY',0.75,None,18.90,"page 5: 300 x 645 printed; DXF faces checked (T-090)",None),
]

# Freelancer per-room plaster rows (his internal plaster sheet, rows 4-20), same rows in his paint sheet. Shown only.
FREELANCER = {'GF-01': (20.0, 3.60), 'GF-04': (12.5, 3.60), '1F-01': (17.5, 3.40), '1F-04': (17.3, 3.40),
              '1F-10': (22.3, 3.40), '2F-03': (18.9, 3.40), 'GF-08': (54.25, 3.60), 'GF-15': (21.05, 3.60),
              '1F-11': (21.9, 3.40), '1F-13': (40.25, 3.50), '2F-01': (9.0, 3.40), 'GF-02': (6.75, 3.60)}

# Windows with a printed height (T-083 OPENINGS.csv) in a room of this table: width, sill and head above the room's floor
# (m). UP-OPEN-SCHED-001 wall_finish_deduction = width x (min(head, H) - max(sill, 0)).
PRINTED_WINDOWS = {
    '1F-01': [('W14', 2.4498, 1.20, 2.80, "SE elevation p.6 chain 220/160/139: sill +6.70, head +8.30 on the 1F +5.50")],
    '1F-12': [('W18', 0.50, 0.84, 3.00, "NW elevation p.8 chain 84/216/230: sill +6.34, head +8.50 on the 1F +5.50")],
}

# Ceiling area of the closed dry rooms from the printed rectangle (URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1: the
# area is published, the finish is BY_SPEC). No Urban rule prices or measures plaster or paint ON a ceiling: HELD.
CEILING = {'GF-01': (round(4.00*6.30 - (1.10**2 - 3.141592653589793*1.10**2/4), 3), "4.00 x 6.30 less the R1.10 corner (1.21 - 0.950)"),
           'GF-04': (round(1.75*4.50, 3), "1.75 x 4.50"), '1F-01': (round(4.25*4.50, 3), "4.25 x 4.50"),
           '1F-04': (round(5.00*3.65, 3), "5.00 x 3.65"), '1F-10': (round(3.80*4.30, 3), "3.80 x 4.30"),
           '2F-03': (round(3.00*6.45, 3), "3.00 x 6.45")}

def height(ftf_key, beam):
    return round(FTF[ftf_key] - beam - DECOR - FLOOR_FIN, 3)

def option_beams(deepest, crossing):
    a = STD_BEAM                                   # Q-52 A: always 0.60
    b = deepest                                     # Q-52 B: deepest drawn beam at the room
    c = crossing if (crossing and crossing > STD_BEAM) else STD_BEAM   # Q-52 C
    return a, b, c

rows = []
for rid, zone, room, kind, deepest, crossing, length, lsrc, hold in R:
    row = {'ROW': rid, 'ROOM': room, 'KIND': kind,
           'TRADE': 'internal plaster + paint (same m2, UP-FIN-PAINT-001)' if kind == 'DRY'
                    else 'wall tile to the decor ceiling (Q-48 A, UP-FIN-WALL-001); no plaster / paint line',
           'FLOOR_TO_FLOOR_M': FTF.get(zone, ''), 'FTF_SOURCE': FTF_SRC.get(zone, 'HELD'),
           'DEEPEST_BEAM_M': deepest, 'DEEP_BEAM_CROSSING_M': crossing or '',
           'WALL_LENGTH_M': length if length is not None else 'HELD', 'LENGTH_SOURCE': lsrc}
    heldh = zone in ('STAIR', 'GF_LEVEL_HELD')
    a, b, c = option_beams(deepest, crossing)
    for tag, beam in (('A', a), ('B', b), ('C', c)):
        h = None if heldh else height(zone, beam)
        row[f'H_{tag}_M'] = h if h is not None else 'HELD'
        row[f'BEAM_{tag}_M'] = beam
        row[f'GROSS_{tag}_M2'] = round(length * h, 3) if (h is not None and length is not None) else 'HELD'
    wins = PRINTED_WINDOWS.get(rid, [])
    ded = {}
    for tag in 'ABC':
        h = row[f'H_{tag}_M']
        ded[tag] = round(sum(w * (min(hd, h) - max(s, 0)) for _, w, s, hd, _ in wins), 3) if isinstance(h, float) else 'HELD'
        row[f'WINDOW_DED_PRINTED_{tag}_M2'] = ded[tag] if wins else 0.0
    row['WINDOWS_PRINTED'] = '; '.join(f"{i} {w} x ({hd}-{s}) ({src})" for i, w, s, hd, src in wins) or 'none printed'
    c = CEILING.get(rid)
    row['CEILING_AREA_M2'] = c[0] if c else ('HELD' if kind == 'DRY' else 'see wet-area table T-074')
    row['CEILING_AREA_SOURCE'] = c[1] if c else ''
    row['CEILING_PLASTER_PAINT'] = 'HELD: no Urban rule for plaster or paint on a ceiling (finish BY_SPEC)' if kind == 'DRY' else 'n/a (wet: ceiling finish BY_SPEC)'
    row['DOOR_DED'] = 'HELD: no door height printed (owner Q-55)'
    row['NET'] = 'HELD (door deductions wait on Q-55; other windows of the room unprinted: T-083)'
    status = []
    if hold: status.append(hold)
    if zone == 'GF_ANNEX': status.append('annex 4.00 m only under Q-54 A')
    status.append('all options wait on Q-52')
    row['STATUS'] = 'HELD: ' + '; '.join(status)
    fl = FREELANCER.get(rid)
    row['FREELANCER'] = f"{fl[0]} x {fl[1]} = {round(fl[0]*fl[1],3)}" if fl else 'none'
    rows.append(row)

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'ROOMS_T090.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

def total(kind, tag, only_fl=False):
    s = 0.0; n = 0
    for r in rows:
        if r['KIND'] != kind or not isinstance(r[f'GROSS_{tag}_M2'], float): continue
        if only_fl and r['ROW'] not in FREELANCER: continue
        s += r[f'GROSS_{tag}_M2']; n += 1
    return round(s, 3), n

fl_dry = sum(round(FREELANCER[k][0] * FREELANCER[k][1], 3) for k in ('GF-01','GF-04','1F-01','1F-04','1F-10','2F-03'))
print('rooms', len(rows))
print('ceiling area of the 6 closed dry rooms', round(sum(v[0] for v in CEILING.values()), 3))
# alternative allocation shown in the write-up: the 1.47 x 3.05 passage of 1F-10 (two printed 3.05 walls)
for tag in 'ABC':
    h = [r for r in rows if r['ROW'] == '1F-10'][0][f'H_{tag}_M']
    print(f'passage walls 2 x 3.05 at option {tag}: {round(6.10*h,3)} m2')
for tag in 'ABC':
    d, n = total('DRY', tag); wt, m = total('WET', tag)
    print(f'option {tag}: dry plaster/paint gross {d} m2 on {n} rooms vs freelancer {round(fl_dry,3)} '
          f'({round(d-fl_dry,3)} m2, {round((d-fl_dry)/fl_dry*100,2)} %); wet wall tile gross {wt} m2 on {m} rooms')
for r in rows:
    print(r['ROW'], r['KIND'], r['WALL_LENGTH_M'], r['H_A_M'], r['H_B_M'], r['H_C_M'], r['GROSS_A_M2'], r['GROSS_B_M2'], r['GROSS_C_M2'], r['FREELANCER'])
