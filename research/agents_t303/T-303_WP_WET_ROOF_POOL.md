# T-303: waterproofing scope inventory, WET-AREA and ROOF families, and the POOL / TANK presence ruling

Worker 3, claim 2026-10-25 23:02 UTC, run session_01GjHp5dbg4NtMGhMyHTE2Qw. Part 2 of T-301 (F-REC-02: no WP line can read
WHOLE without a face inventory). Read-only: no candidate line, quantity, state or V2.9 cell moves. Drawings named by
Drive folder and title only ("Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip, own decode this run).

## 1. The physical question (ERS s.2.1)

Which physical elements does each family cover, and is each one IN_LINE, NOT_APPLICABLE with evidence, or MISSING
(blank, never 0)? One inventory element = one face of one drawn element for one item code and unit (T-301 schema, its
core imported read-only). Wet-area elements: per wet room its floor, its wall upturn (walls only, Q-35 C), its floor
penetrations, its membrane supply; per PHYSICAL door its threshold piece, its transition (m2 and number); per open side
or leafless opening its membrane edge (termination). Roof elements: per roof face its membrane inside the parapet and its
upturn runs. Pool / tank: one presence element per printed (or not printed) WP layer.

| Elements | Source (merged; none is the engine's line list) |
|---|---|
| 18 wet rooms | T-074 hand table (17 rooms, own polygonisation: floor m2, boundary lm, doorways) + the pantry box (Q-37 A, printed 4500 x 3000, T-286); presence = the T-209 set (18 = 18) |
| 15 doors | T-249 opening inventory (14 doors by DXF insert handle, Checker 2026-10-24 02:48) + the pantry's own D120 (T-128 r3 / T-209, insert not bound); each door's rooms from the T-074 / T-209 door lists (T-074 per-room doorway count = door inventory count, asserted) |
| door widths | drawn block width, re-read this run on P7757.dxf: D315 800, D120 1000, d220 900 mm, all 20 inserts of the three blocks at scale 1 (T-074 wall depths 0.15 / 0.20) |
| open edges | T-074 addendum: lobby to the stair hall 1.26, basin space to the passage 0.90; T-209 / T-128 r3: arch to the dewaneya 1.00 (no leaf), pantry open side 4.49 |
| roofs | T-062 hand trace (merged; Verifier re-multiplied 55.560 / 32.721 / 115.816): 1F west +4.30, 1F south-east +5.50, 2F +9.70, 2F top +13.90 (Q-34 HELD), the 6.130 m2 area round the oval void (+5.50, no ROOF label) |
| pool / tank | T-183 r2 (MERGED 6380294): ST7757.pdf p.7 DETAIL OF SWIMMING POOL, TEXT 1876 '5cm INSULATION MEMBRANE.', TEXT 1874 '5cm SECREED.', hatch 1851; S8.4 water-tank region + T-204 (tank place only) |

Room crosswalk to the candidate's room ids: the T-086 face census (floor + area, exact to 1e-3 here); the two equal 1F
west baths by the T-249 door each line names (C2B / OP-004, C2E / DOOR-1F-0c35dbd6), and every one of the 14 door ids the
candidate names agrees with the room the T-074 / T-209 lists put that door in (asserted, not assumed).

## 2. Result on the candidate of record (V3.0.17 = V3.0.18 for every WP line)

T-266 (V3.0.18, MERGED ceeb5135) changed 5 stair lines and added 5 lines, none a WP line; the 150 WP lines of T-301's
committed V3.0.17 extract are V3.0.18's. Tolerance for "closes": 0.0005 in the unit (prints 0.000), stated.

**WP.WET_AREA: 121 elements, IN_LINE 113, NOT_APPLICABLE 0, MISSING 8; 119 lines: WHOLE 55, COMPONENT 26, HELD 38;
2 doubles; 4 register-only lines.** T-236 schema: WATERPROOFING GAPS, found 121, measured 81, held 32, missing 8.

| Item (unit) | Elements | In line (qty / held) | Missing | Inventory (in line) | Line | Residual | Lines WHOLE |
|---|---|---|---|---|---|---|---|
| FLOOR m2 | 18 | 18 / 0 | 0 | 85.6217 | 85.62071 | +0.00099 | 17 of 18 (lobby +0.001405) |
| WALL_UPTURN m2 | 18 | 17 / 1 (pantry) | 0 | 25.2137 | 25.114585 | +0.099115 | 12 of 17 |
| DOORWAY m2 | 15 | 14 / 0 | 1 (pantry) | 1.82 | 1.930379 | -0.110379 | 12 of 14 |
| DOORWAY_TRANSITION m2 | 15 | 0 / 11 | 4 | blank | blank | n/a | held; 2 doors carried twice |
| DOORWAY_TRANSITION_NR pcs | 15 | 14 / 0 | 1 (pantry) | 14 | 14 | 0 | 14 of 14 |
| PENETRATION pcs | 18 | 0 / 17 | 1 (pantry FD) | blank | blank | n/a | held |
| TERMINATION lm | 4 | 0 / 3 | 1 (pantry open side) | blank | blank | n/a | held; 4 lines register-only |
| MEMBRANE_ROLLS pcs | 18 | 18 / 0 | 0 | not a face | 21 | n/a | procurement count, judged by the strip layout, not here |

Findings (named, nothing changed; each a who-is-right proposal for the Checker):

1. **1F east bath upturn 1.48 vs 1.58 m2 (+0.100 m2, +6.8 %)**: walls only 8.70 - 0.80 = 7.90 lm; the engine stops the
   upturn over 0.50 m more and books three 'glazing' terminations (L-0a7238ed / L-1ef59757 / L-8fb80f62) the room's
   wall-face census does not have. The room's only 0.50 m opening is W18, sill 0.84 PRINTED (T-144): a window above the
   0.20 m upturn leaves the wall below it. Proposal ENGINE_WRONG, subject to the Checker re-reading D2:3123 / 3126 / 3133.
2. **Thresholds**: GF master bath 0.218846 vs 0.80 x 0.15 = 0.12 m2 (+0.098846); 1F west lower bath 0.131977 vs 0.12
   (+0.011977); both closure-derived lines. Proposal UNRESOLVED (re-read the loose door arc 334 / insert C2E and the wall
   depth); the 12 other doorway lines close.
3. **Transitions, one per physical door (Q-35 C, Lead reading 2026-10-19 18:15)**: the doors between the dewaneya wash
   and W.C. (D-GF-02) and between the stair W.C. and the basin space (D-GF-10) each carry TWO transition lines (one per
   room side: a double count, held so no number moves today); the doors from the two core W.C.s to the lobby (D-GF-11 /
   D-GF-12) and from the laundry to its W.C. (D-1F-06) carry NONE. 13 lines = 14 doors - 3 + 2. Proposal ENGINE_WRONG
   (rule application), quantity effect when released: +3 / -2 transition pieces.
4. **Pantry (Q-37 A)**: its door (D120 1.00: threshold, transition, transition number), its floor drain (sanitary drawing
   FD) and the threshold line on the 4.49 m open side to the dining are MISSING (no line); its membrane 13.500 m2 closes
   (WHOLE) and its upturn stays held. Omission, blank, never 0.
5. **GF core W.C. 245 x 167 'other' termination** (L-f78da96a): T-128 r3 reads that diagonal face as WALL (door-closure
   copy; counted in the paintable length). Register-only; proposal ENGINE_WRONG (misread).
6. Small named residuals (< 0.0015 m2 per room): upturn of the stair W.C. / basin space -0.000592 each, lobby -0.0006 (the
   engine reads the drawn gaps 0.897 / 1.257, the hand table 0.90 / 1.26), core W.C. 245 +0.00094; lobby floor
   +0.001405 (hand trace of a room open to its neighbour). Residual risk: the door width is the drawn block width; T-128
   r3's walked jamb gaps (0.74 .. 0.79) are the other reading and would move every upturn and threshold slightly.

**WP.ROOF: 16 elements, IN_LINE 13, MISSING 3 (all SCOPE_UNKNOWN); 12 lines: WHOLE 3, COMPONENT 6, HELD 3.**

| Roof | Membrane inventory / line m2 | Upturn inventory / line lm | Countability |
|---|---|---|---|
| 1F west +4.30 | 55.560332 / 55.559 (+0.001332) | 35.727 / 35.727 | membrane COMPONENT (residual), upturn WHOLE |
| 1F south-east +5.50 | 32.721 / 32.721 | 52.940 / 52.940 | both WHOLE |
| 2F +9.70 | 115.816517 / 115.832 (-0.015483) + dome footprints 30.716 SCOPE_UNKNOWN | 65.140 + rings 27.784 = 92.924 / 92.922 (+0.002245) | both COMPONENT |
| 2F top +13.90 | held (Q-34) | held | HELD |
| area round the oval void +5.50 | 6.130 net SCOPE_UNKNOWN (no ROOF label) | SCOPE_UNKNOWN | no line |

The 2F roof line deducts the two dome footprints as open skylights (scenario S1). The owner's 2026-10-22 instruction keeps
the three concrete domes in the approved baseline S0 and says "do not release the deletion"; whether the membrane runs
under a dome is not settled (Q-24 reading, Q-29 option C, T-185), so the footprints are SCOPE_UNKNOWN, never NA, never 0.
The dome-base upturn rings are in line under both scenarios (owner Q-24: a dome above the slab gets the 0.20 m upturn
round its base). Residuals: circle (inventory) vs the engine's polygon (2 x 15.350 m2, 2 x 13.891 m). Roof vs freelancer
unchanged: 204.112 m2 vs 285.00 m2 (-28.4 %, UNRESOLVED since T-071), 181.589 lm vs 194.00 lm.

**WP.POOL_TANK: 3 elements: MISSING 2, NOT_APPLICABLE 1; no candidate line.**

- POOL-1 membrane, base and outer wall faces: the WP layer IS PRINTED (p.7, TEXT 1876, hatch 1851) and no line carries
  it -> MISSING (blank). T-183 r2's drawn extent 30.932 m2 is DRAWING-CONFIRMED, not verified; the print says
  "INSULATION membrane": waterproofing or insulation is not stated (S8.2 BLOCKED_UNQUANTIFIED), product C3, termination C9.
- POOL-1 protection screed 5 cm (TEXT 1874): printed, no line -> MISSING (T-183 r2 1.591 m3 as drawn, not verified).
- TANK-01 (2F roof): NOT_APPLICABLE with evidence: the 'WATER TANK PLACE' note only, no tank base, wall, member or WP
  layer drawn, noted or scheduled (S8.4; T-204 holds the tank itself). Re-rule when a tank is drawn.

V2 records: no Verifier V2 record exists for any wet-area, roof or pool line (V3.0.17 set: 8 records, all WP.FOUNDATION),
so nothing to compare; the 58 WHOLE lines above become countable as whole verified lines only after a Checker verdict.

Engine vs freelancer: unchanged by this task (no quantity moves). Wet areas: the freelancer's boundary 144.61 lm vs the
hand table 144.73 lm (+0.1 %, T-074); per-line freelancer comparison not measured here; roof as above; pool / tank
WP vs freelancer not measured.

## 3. Rule, tests, files

Rule R-T303-WP-FAMILIES-1 (PROJECT-INDEPENDENT research rule on R-T301-WP-INVENTORY-1, not a rule-file version): wet-area
and roof lines are judged per line (one per room / roof / door): WHOLE only when every element the line carries is
quantified and closes, none of its keys is carried twice, and no element of the same item in the same room / roof is
missing or held; a door between two wet rooms is ONE element (one threshold, one transition); a cell with no door and no
open edge cannot take wet scope (D-C3); a printed WP layer with no line is MISSING, a sheet without one is NOT_APPLICABLE
with its evidence; an unsettled scope is SCOPE_UNKNOWN (MISSING, blank).

Files: research/agents_t303/t303_wp_families.py (core, imports research/agents_t301 read-only), t303_alsenan.py
(adapter), WP_WET_ROOF_POOL_INVENTORY_T303.csv, WP_LINE_COUNTABILITY_T303.csv, WP_FAMILIES_REPORT_T303.json;
tests/t303_wp_families (villa V-303 by hand: normal + adverse; development villa pinned to the committed outputs).

Lessons-register row (proposed, ERS s.7): 2026-10-25 | wet-area doorway transitions: 2 doors booked twice, 3 doors never
| the engine books a transition per room side and only where its closure finds one | a door between two wet rooms is one
physical element: thresholds and transitions are counted per door from an opening inventory, not per room
(PROJECT-INDEPENDENT; provenance Q-35 C, T-249, T-303) | tests/t303_wp_families | OPEN until a lane I piece applies it.
