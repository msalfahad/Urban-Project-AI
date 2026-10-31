# T-387 Structural element ownership and overlap census on the candidate of record V3.0.29 (lane S, research only)

Worker 1, 2026-10-31 05:24 .. UTC, branch `agents/task-T-387`. No quantity, line, state, method, rule or released cell is
changed. Development villa (Alsenan), not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Run and sources

Own run, Python 3.11.18, Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`), decoded into `.work/private` only. `research/agents_t167/v304_run.py`, then
`research/agents_t327/v3029_run.py`: **V3_0_29_BOQ_LINES.json `6b5dc44f` / csv `09b3493b` = the candidate of record**
(the Checker's reproduction of 2026-10-30 23:40, T-385). Downgrades: `verdicts/V3.0.29/DOWNGRADES.json` on agents/control.
Geometry: route G's own plan records (generic_route.detect + items_from, conventions URBAN_M8_GENERIC_CONVENTIONS_V6 +
the M4 profile = the call tools/urban_boq_m2.route_generic makes), exported privately by `t387_geometry.py`; its 1,108
items carry exactly the candidate's route G element ids (all 430 route G concrete lines found by id).

```
python3 -I research/agents_t387/t387_geometry.py <private>/ST7757.dxf <private>/t387/geometry.json
python3 -I research/agents_t387/t387_alsenan.py --lines <run>/v3029/V3_0_29_BOQ_LINES.json \
    --geometry <private>/t387/geometry.json --downgrades <board>/docs/agents/verdicts/V3.0.29/DOWNGRADES.json \
    --out research/agents_t387
```

Outputs (engine ids, codes, states, m2 / m3 only; no coordinate, polygon or name): `BINDING_T387.csv` (a),
`PAIR_REGISTER_T387.csv` (b, one row per family pair), `MEMBERS_T387.csv` (per plan member: drawn / owned / billed plan,
residual, verdict, the merged-ledger adjustment that explains it), `PAIRS_T387.csv` (plan overlaps > 1e-4 m2),
`summary_t387.json`. Rules `t387_rules.py` R-T387-1 .. 6; tests `tests/t387_overlap_census/` (23 rule tests on the
hand villa T387-K + 6 on the committed outputs).

## 1. Physical question (ERS s.2.1)

Every structural concrete line of V3.0.29 must rest on ONE physical element and ONE owner trade, and the concrete of two
intersecting elements (column / footing-neck, column / beam, beam / beam junction, beam / slab, column / slab, stair /
beam B20 / B23, strap / footing, ground beam / footing, neck / ground beam, parapet / slab, pool / footing) must be in
exactly one line: shared volume = sum - union = 0 within 0.001 m3, or a named DOUBLE / GAP with its cause and line ids.
Owner precedence used (route G basis, R-CONC-OWN-1 / -1a, owner Q-20, Q-62 A cond): COLUMN > BEAM > SLAB > STAIR; one band
owns a beam / beam junction; a neck runs footing top -> GF level, the GF column from there.

## 2. (a) Binding: 525 STR.CONC lines, 525 BOUND, 0 UNBOUND

| Family (owner trade CONCRETE) | Lines | VALUED lines | VALUED m3 (contractual) | HELD lines (never 0) | NOT_APPLICABLE (retired / superseded) |
|---|---|---|---|---|---|
| Blinding (plain) | 4 | 0 | 0.0000 | 4 | 0 |
| Footings | 26 | 25 | 64.3040 | 1 | 0 |
| Straps | 10 | 3 | 3.3905 | 2 | 5 |
| Necks | 36 | 0 | 0.0000 | 36 | 0 |
| Ground beams (incl. boundary-wall GB) | 60 | 38 | 27.6254 | 22 | 0 |
| Ground slab | 25 | 24 | 17.2407 | 1 | 0 |
| Columns (incl. 3 planted) | 72 | 45 | 28.2155 | 19 | 8 |
| Beams | 191 | 110 | 66.3179 | 27 | 54 (superseded by T-252 runs / the T-160 ring) |
| Slabs | 75 | 62 | 60.2802 | 0 | 13 (T-234 'not slab') |
| Stairs | 12 | 6 | 5.3689 | 5 | 1 (the 1F ring zone, not a stair) |
| Domes | 5 | 2 | 5.0814 | 1 | 2 |
| Pool | 5 | 2 | 7.2023 | 1 | 2 |
| Parapet RC | 4 | 0 | 0.0000 | 4 | 0 |
| **Total** | **525** | **317** | **285.0266** | **123** | **85** |

Footings + straps 67.6945, ground 44.8661, columns 28.2155, beams 66.3179, slabs 60.2802, stairs + domes 10.4502, pool
7.2023 m3 = the T-385 family figures to 0.0001 m3 (independent binding, same candidate). Every line under an unresolved
downgrade record (DG-3521554d2fd011b9 blinding, DG-6dd9f1caba1ca77d boundary lower band, DG-a31a0d7e9dd564ad 9 D-34
ground beams) is HELD with its figure in the audit column only (R-T387-2). No two lines bill one element id under one
code (split parts carry their suffix).

## 3. (b) Overlap per family pair (PAIR_REGISTER_T387.csv)

| Pair | Method | Result | m3 |
|---|---|---|---|
| Column / beam / slab / beam-beam, 2F (SH02) | R-T387-3 on the route G plan, billed plan from the line | PASS_HELD (14 held members) | 0.000 |
| same, 1F (SH04) | " | PASS_HELD; 8 beam groups' residuals = their T-229 adjustments (support cut beside, square ends) 0.2526 m3, unexplained 0.000 | 0.000 |
| same, GF (SH06) | " | as merged: 14 groups = T-229 adjustments 0.1783 m3 net; GAP 0.0014 (BAND0003); RECHECK 0.8010 (6 groups). T-392 re-run: 16 groups ledger-adjusted 0.1992; named GAP 0.005972 + DOUBLE 0.002767 (T-392); ring LOCATED; RECHECK 0.5593 (B26 / B27, T-229 rows; B27 closed by the Checker's own measure) | see below |
| same, ground (SH08: ground beams, ground slab, necks) | " | PASS_HELD (47 held, necks all HELD) | 0.000 |
| Arc-edge slab faces vs curved bands (1F 4, GF 4, ground 2) | R-T387-3a | polygon 'overlap' = the chord excess (to 0.001 m2): true overlap 0 | 0.000 |
| Neck / GF column; GF / 1F / 2F columns | R-T387-4 (line formulas: neck top = GF level +1.00; storey floor to floor) | OK | 0.000 |
| Column / column (drawn outlines) | foundation plan 34, column plan 23 outlines | 0 overlapping pairs | 0.000 |
| Buried: footing / neck / strap / ground beam / blinding / pool | R-T387-5, T-347 (MERGED: 256 components, double 0) | CARRIED_OK: 71 bound STR.CONC lines present with the T-347 figure | 0.000 |
| Stair / beam (ST-01 heads in B20 / B23, MS2-L foot in B20) | R-T387-5, T-192 rev3 (MERGED) | CARRIED_OK: MS1-U 0.997552 (inside the MS1 closable 1.227952 = MS1-U + MS1-LD 0.2304), MS2-U 1.001373, MS2-L 1.033445; B20 span 2 0.40 x 0.75 x 3.30 = 0.990, B23 span 2 0.45 x 0.75 x 3.30 = 1.11375 | 0.000 |
| Parapet RC / beam, slab | listed | UNDETERMINED: 4 lines HELD blank (T-319: measured above the beam's scheduled depth) | HELD |
| Neck / ground beam, ground slab | listed | UNDETERMINED: the ground beams and slab are net of the neck outlines (PASS); the shared volume is in the 36 HELD necks | HELD |
| Dome shell / ring / slab zone | listed | UNDETERMINED: T-160 ring + T-185 shells merged; DOME-3, east ring HELD; 1F ring-zone face retired | HELD |
| Pool base / walls / steps, pool / F8 | listed | UNDETERMINED: walls above the base (foot once); steps HELD; F8 / pool CONFLICT 0 .. 1.121 m3 (T-320) | HELD |
| Strap inside a footing (SB1 in F10 / F, SB3 in F3) | listed | UNDETERMINED: HELD, bounds 0 .. 0.385 and 0.0295 .. 0.2683 (T-347) | HELD |
| Blinding / footing, GB, strap | listed | UNDETERMINED: all 4 lines HELD | HELD |

### GF residuals not closed by the line's own adjustment text (RECHECK, bounded; not a quantity change)

| Beam group (GF) | Lines | Residual vs route G band m3 | In the line's ledger_adds | Cause traced | Remaining |
|---|---|---|---|---|---|
| B27 (BAND0048.1 + .2) | 2 | 0.8457 | +0.4046 (vs T-110) | T-229 table row 'GF B27': +0.8487 on the route G pieces (cut at the carried P.C 0.4418, oblique ends square-cut 0.1787 + 0.2282); the drawn edges run on to the C11 / D.C faces | 0.0030 (route G pieces' released figure vs the polygon) |
| B26 (BAND0047.1 + .2) | 2 | 0.2980 | +0.1798 (vs T-110) | T-229 'GF B26': +0.2975 on the pieces (cut at the P.C 0.1163, T.C end 0.1812) | 0.0005 |
| B7 ring (BAND0050 .. 0053) | 1 | 0.2182 | none | T-252 r2 RING-B7 0.499805 m3 is the drawn ring between its arcs; route G's arc bands cover 0.3747 of its 0.6664 m2 (0.00075 of their 0.3755 lies outside it) | T-392 LOCATED: west crescent 0.1736, east-north 0.0590, east-south 0.0592 m2 outside the arc bands, no other line in the ring |
| BAND0021.1, BAND0018, BAND0039 | 3 | 0.0135, 0.0074, 0.0026 | T-252 r2 +0.0136 / +0.0074 (read since T-392) / -0.0600 | T-392: the two T-252 r2 R-BEAM-END-OBLIQUE-2 corrections; CB8: the census gave B27's band overlap 0.00345 m2 to B27 while the line bills its rectangle (own drawing: DOUBLE 0.002767 / GAP 0.003406) | 0.000 open (named) |

BAND0003 (run BM-GF-003): the line bills 0.526665 m3 = the T-252 ledger's 0.528 less the **T-146 ring-overlap
deduction** 0.001335 m3 (its formula field; Checker F-CHK-T387-1: the original text here said 'no documented
deduction', which was wrong); BAND0006 (0.000353) and BAND0041.2 (0.000878) carry the same T-146 deduction and are not
rounding. Updated by T-392 (outputs re-run 2026-10-31 on the reproduced candidate 6b5dc44f): R-T387-7 names every merged
ledger item (formula, T-229 ledger_adds / deducts, T-252 r2 runs), and T-392's own drawing measure turns the three
T-146 deductions into a named **GAP 0.002566 m3** (the drawn cells hold 0 m2 of the ring: the overlap came from a
fitted band set), the CB8 end into DOUBLE 0.002767 + GAP 0.003406 (R-T392-2), and locates the ring B7 0.2182 m3
(LOCATED_EXTENSION, R-T392-4); BAND0018 / BAND0021.1 are the T-252 r2 oblique-end corrections (LEDGER_ADJUSTED).
See research/agents_t392/T-392_RING_POOL_OWNERSHIP.md.

## 4. Findings

- F-T387-1 (closure): on V3.0.29 no structural intersection is billed twice: every plan level band closes to 0.000 m3
  within 0.001 on the valued members; 22 beam-group residuals are exactly the Checker-merged T-229 adjustments (support
  cut beside, oblique / short ends, column owns: 0.4309 m3 net on 1F + GF). Open: 0.8010 m3 RECHECK, of which 0.5558
  is traced to the T-229 B26 / B27 rows (to 0.0035 m3) and 0.2452 is not located (ring B7 0.2182, three small residuals
  0.0235, the B26 / B27 remainders 0.0035), and one GAP 0.0014 m3.
- F-T387-2 (route G column outlines on the slab plans are not the column lines): the GF slab plan has two overlapping
  outline clusters (0.1249 / 0.0500 m2 shared) while the column plan's outlines never overlap; the deductions use the
  union, so nothing is billed twice; but column outlines are bound to column lines only by storey count here (GF 30
  lines / 28 outlines on SH06). Element-level column binding by position is a gap of this census (listed, not assumed).
- F-T387-3 (arc chords): 10 slab faces whose route G polygon is a chord across a curved band 'overlap' the band by
  0.0022 .. 0.7498 m2; in every case the overlap equals the chord excess (within 0.001 m2) and the face's exact area
  already stops at the band face: no double. A census that used the polygons as drawn would report about 0.18 m3 of false
  doubles (measured on the V3.0.4 lines of the same run) (R-T387-3a and its test).
- F-T387-4: 123 HELD lines keep 13 family pairs UNDETERMINED (necks, parapets, domes, pool steps, straps in footings,
  blinding); none is counted as 0 or as agreement.

## 5. (c) ELEMENT_REGISTER proposals for the Lead (no register edit)

| Element | Drawing reference | Owner trade (proposal) | Basis |
|---|---|---|---|
| Beam / beam junction squares (all floors) | ST slab plans SH02 / SH04 / SH06, route G bands | CONCRETE, the band whose line keeps it (read from the two lines, R-T387-3) | 3 GF junctions owned once (PAIRS_T387.csv) |
| B26 / B27 extensions beyond the route G pieces (P.C cut, oblique ends, T.C end) | ST p.4 GF roof plan; T-229 rows | CONCRETE beam line (T-252 runs) | T-229 MERGED; RECHECK 0.0035 residual |
| B7 dome ring between its arcs (GF) | ST p.4; T-252 r2 RING-B7, T-308 | CONCRETE beam (ring) line; adjoining arc-edge slab faces stop at its face | 0.2182 m3 location open |
| 1F dome ring zone (route G 'stair zone' face, 17.127 m2) | ST p.5 (SH04) | CONCRETE dome ring (T-160) for the in-bay ring; the zone is neither stair nor slab | retired line L-14f885e9... |
| Ground-sheet stair face SITE-4df8 | ST SH08 | CONCRETE stair (closable line 1.536225) | not a ground-slab face |
| Necks through ground beams / ground slab | ST SH08 / SH10 | NECK (column) owns; GB / ground slab net of the outline | necks HELD (Q-21 C) |

## 6. Verdict proposals and what is missing

- Proposed: STAIR / BEAM, buried pairs, column chains, column outlines, every closed level band: AGREE (0.000 m3, by
  method above). B26 / B27: ENGINE_RIGHT-consistent with T-229 (Checker to confirm the 0.0035 m3 residual as route G
  rounding). Ring B7 0.2182 and 0.0235 m3 of small residuals: UNRESOLVED (location of the drawn extension). BAND0003
  GAP 0.0014: UNRESOLVED. No freelancer comparison here (T-385 has it).
- Not done: column lines bound to outlines by position (F-T387-2); geometry of the ledger-only families (pool, domes,
  parapets, ring) re-measured here (carried from their merged ledgers only); a 3-D check of the free-space test
  (R-T387-6 bounds the RECHECK by unbilled plan within 1.5 m, it does not locate it).

## 7. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | An overlap census on route G polygons reports false doubles on every slab face with an arc edge (10 faces, up to 0.75 m2) and false DOUBLE / GAP on 22 beam groups whose lines were corrected by a merged ledger (T-387) | route G stores a curved face as a chord polygon (its exact area is on the face record), and a ledger run's figure differs from its route G band by the documented adjustments | an overlap census measures each member on its exact outline (chord excess across a curved member face is not shared volume) and reconciles each residual to the adjustments its merged ledger documents before calling it a double or a gap; what remains is RECHECK with its bound, never OK and never netted (scope: every villa, every structural overlap check; provenance T-387) | tests/t387_overlap_census (arc chord normal / real overlap beyond the excess / refused without excess; junction owned by either band; rounding vs a real residual) | PROPOSED |
