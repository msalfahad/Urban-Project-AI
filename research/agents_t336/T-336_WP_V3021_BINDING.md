# T-336: wet-area and pool waterproofing bound to the V3.0.21 WP line ids (integration dependency of T-310)

Worker 2 (lane A), 2026-10-29. Development villa, not an accuracy claim. Research only: no engine module, candidate
line or released line changes; V2.9 + route G stays the default; lane I (T-310) applies the FILL table. Drawings are
named by Drive folder and title only ("Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip, sha256
ab54dd55..; "ST7757 dxf.dxf" 9f9d1179..). ERS s.2 - s.4 and s.7 applied.

## 1. Run and identity

Own run of research/agents_t167/v304_run.py then research/agents_t315/v3021_run.py on the two Drive copies (decoded into
the private folder only). Extract (`t336_alsenan.py --extract`, the T-301 extract fields: ids, item codes, element ids,
units, states, quantities; no coordinates, no names) -> CANDIDATE_V3021_WP.json. **V3_0_21 json `be22a4e4` / csv
`3548e39c` and V3_0_20 json `097a80b6` / csv `ca90351b` REPRODUCED** (= the candidates of record, T-315 r2 / T-244 Gate
B). LINE_REBIND_T336.csv: all **150 WP lines of V3.0.21 are SAME** as the V3.0.17 extract T-303 was verified on (id,
item, unit, state, quantity, element id, components; 0 changed / added / removed), so the T-303 inventory binds to the
candidate of record unchanged and the line ids below are V3.0.21's.

## 2. Physical pieces (ERS s.2.1)

One piece = one physical face or one physical door item, once: per wet room its floor membrane (m2), its wall upturn
(walls only, Q-35 C, 0.20 m, m2), its floor penetrations (pcs), its membrane supply (pcs, procurement only); per
PHYSICAL door its threshold (width x wall depth, m2), its transition (m2) and its transition count (pcs); per open side
or leafless opening its membrane edge (lm); for the pool its membrane (m2 on the protected concrete face) and its
protection screed (m3); the tank a presence ruling. Source of every piece: the Checker-verified T-303 inventory
(MERGED 1d3f69b0) and T-309 ledger (MERGED 834ada3e); five readings are added here from the drawing, each by entity
handle (section 3).

## 3. Readings added by this task (own read on P7757.dxf)

| Piece | Reading | Result | Line | Effect |
|---|---|---|---|---|
| GF pantry floor (O-T303-01) | printed box DIMENSION 5E1 4500 / 5D5 3000 to wall faces 158 / A6 and AE / B3; column 2FAE (S-COL.BON, hatch 2FAD, cross 2FAC) 0.250 deep in the 0.200 north wall (faces 158 / 15A), 0.050 proud of face 158 over 0.900 from face AE | 13.500 - 0.900 x 0.050 = **13.455 m2** (= T-286 MERGED closure) | L-f32abcdb 13.500 | -0.045 m2 (-0.33 %), ENGINE_WRONG |
| GF pantry door threshold (Q-37 A) | insert 33E block D120 rot 180, leaf into the pantry; faces 158 / 159 and 15A / 15B stop at the jambs, gap 1.000; wall 0.200 | 1.000 x 0.200 = **0.200 m2**; its transition count **1** | none | NEW rows (MISSING in T-303) |
| GF master bath threshold D-GF-14 (T-303 UNRESOLVED) | loose arc 334 r 0.690; faces 2E5 / 2E6 end at the jambs, gap 0.800; 2E7 / 2E8 the other face, depth 0.150; frame lines 32B .. 331 | 0.800 x 0.150 = **0.120 m2** | L-0f04f1a4 0.218846 | -0.098846 m2, ENGINE_WRONG (closure piece, not drawn) |
| 1F west lower bath threshold D-1F-04 (T-303 UNRESOLVED) | insert C2E D315 rot 90; faces C1B / C1D (0.150 apart) end at the south jamb, C1C / C1E start at the north jamb, gap 0.800 | **0.120 m2** | L-0627bac3 0.131977 | -0.011977 m2, ENGINE_WRONG |
| 1F east bath upturn (Checker T-303 own re-measure) | walls only 8.700 - 0.800 door; the 0.500 east opening is window W18, sill 0.84 printed (DIMENSION 2EEC / 2EFA), above the 0.20 upturn | 7.900 lm x 0.20 = **1.580 m2** | L-60f10010 1.480 | +0.100 m2 (+6.8 % of the line), ENGINE_WRONG |

Column rule (rule 4): the printed 4500 runs to the wall face 158, not to the column face, so the box is wall face to wall
face and the column footprint inside it is not floor; the other 17 rooms already follow the drawn outline (dewaneya wash
steps round a 0.0175 m2 column corner, T-074 / T-303). The membrane turns up the column's 0.050 returns as part of the
pantry upturn, which stays HELD (T-286: wall heights and closure of the open side).

## 4. Result (filled from the committed outputs; section 5 statuses)

132 pieces on the 119 wet-area lines + 3 pool / tank pieces, each once (WP_PIECES_T336.csv); FILL_T310_T336.csv (132
rows): KEEP 108, CORRECT 4, REPLACE_BY_DOOR_ROW 4, ADD_ROW 12, SET_NOT_APPLICABLE 4. Statuses: DRAWING-CONFIRMED 57,
ASSUMED - OWNER-APPROVED 10, HELD 43 (blank), NOT_APPLICABLE_WITH_EVIDENCE 4, PROCUREMENT 18 (rolls, not re-measured).

| Item (unit) | V3.0.21 lines before | After (FILL) | Change | Note |
|---|---|---|---|---|
| FLOOR m2 (18 rooms) | 85.620710 | **85.575710** | -0.045 | pantry column 2FAE; 17 rooms without the pantry 72.121 vs freelancer 72.01 (+0.15 %, T-074); pantry 13.455 is Q-37 A scope he does not carry (RULE_DIFFERENCE) |
| WALL_UPTURN m2 (18) | 25.114585 | **25.214585** | +0.100 | 1F east bath; pantry upturn HELD blank (unchanged) |
| DOORWAY threshold m2 (15 doors) | 1.930379 (14 lines) | **2.019556** (15 rows) | +0.089177 | D-GF-14 -0.098846, D-1F-04 -0.011977, pantry D120 +0.200 NEW |
| DOORWAY_TRANSITION m2 (15 doors) | 13 lines, all BOUNDED | 15 door rows, all HELD blank | none | 4 room-side lines (D-GF-02: L-1c36054a / L-b60811f6; D-GF-10: L-77a630d7 / L-e0c34550) REPLACED by 2 door rows; 4 door rows NEW (D-GF-11, D-GF-12, D-1F-06, pantry) |
| DOORWAY_TRANSITION_NR pcs | 14 | **15** | +1 | pantry door NEW (DRAWING-CONFIRMED) |
| PENETRATION pcs | 17 held | 17 held + pantry NEW held | blank | sanitary FD count not tabled |
| TERMINATION lm | 7 held | 3 kept held (open edges GF-02 / GF-11 / GF-14) + pantry open side NEW held; 3 W18 lines NOT_APPLICABLE_WITH_EVIDENCE; L-f78da96a held by name | blank | rule 3 |
| POOL membrane m2 | no line | **29.582355** NEW + HELD 0 .. 1.349668 | +29.582 | T-309; function HELD (S8.2) |
| POOL screed m3 | no line | **1.524503** NEW + HELD 0 .. 0.068072 | +1.525 | T-309 |
| TANK | no line | NOT_APPLICABLE_WITH_EVIDENCE (register only) | none | TEXT 1A85 place note only |

**Owner method and drawing method side by side (new finding, no quantity moves).** Ten wet rooms have a window whose sill
is printed on no sheet (T-144 s.5: W05-07 in GF-10 / GF-13 / GF-16, W08 1.50 in the kitchen GF-06, W19-23 in 1F-02 /
1F-03 / 1F-07 / 1F-08 / 1F-09, W28 in 2F-02; widths T-128 r3): 6.90 lm of wall under windows. Their upturn lines (and
the T-303 inventory) run the 0.20 upturn under those windows, which is the OWNER METHOD (Q-30 kitchen example: upturn on
the whole wall boundary; Q-35 C: doors only left out), so the ten lines keep their quantity as **ASSUMED -
OWNER-APPROVED**, not DRAWING-CONFIRMED; the DRAWING METHOD leaves 6.90 x 0.20 = **1.380 m2 HELD (0 .. 1.380)** beside
them until a sill is printed (rule 3; designer window schedule, T-144). Not an owner question (ERS 2.7: the owner method
is answered; the drawing gap is a designer item).

Who is right (proposals for the Checker): pantry floor ENGINE_WRONG -0.045 m2; D-GF-14 / D-1F-04 thresholds
ENGINE_WRONG (closure pieces 0.218846 / 0.131977 vs drawn 0.120 each, was UNRESOLVED); 1F east bath upturn ENGINE_WRONG
(Checker's own T-303 re-measure, carried); transitions ENGINE_WRONG on rule application (Q-35 C), no quantity (blank);
pool rows RULE / SCOPE difference vs the freelancer (no pool membrane row, T-309). Freelancer wet-area floor 72.01 m2 /
boundary 144.61 lm (T-074) unchanged by this task. Not re-measured here: the 108 KEEP rows rest on the T-303 inventory
(Checker-verified join, own re-measures only where named), the roof family (T-303, not T-310's scope) and the
foundation family (T-301): their 31 V3.0.21 lines are SAME as V3.0.17 (LINE_REBIND).

## 5. Rule, tests, files

R-T336-WP-BIND-1 (PROJECT-INDEPENDENT research rule, not a rule-file version; provenance Q-35 C, UP-WP-003, T-303 /
T-309 verdicts): one physical piece, one line (a piece in two lines is refused); a door is one element, its threshold,
transition and count keyed by the door, two room-side lines replaced by one door row, a door with none gets a door row
(blank when held, never 0); an opening is deducted from a layer only where it reaches it (sill at or below the 0.20
upturn), an unprinted sill keeps the upturn HELD; a column inside a printed box is not floor; HELD / UNKNOWN blank, NA
with evidence, procurement counts never re-measured.

Files: research/agents_t336/t336_wp_binding.py (core), t336_alsenan.py (adapter: --extract / --write / --check, imports
research/agents_t303 read-only), CANDIDATE_V3021_WP.json, LINE_REBIND_T336.csv, WP_PIECES_T336.csv, FILL_T310_T336.csv,
summary.json; tests/t336_wp_binding (villa W336 by hand: normal + adverse; development villa pinned to the committed
outputs).

Lessons-register row (proposed, ERS s.7): 2026-10-29 | three wet-area WP quantities stayed UNRESOLVED / unruled for three
days (thresholds 0.218846 / 0.131977 vs 0.120; pantry 13.500 vs 13.455) although each is settled by four drawn lines
and an insert | closure-derived pieces were compared with a hand table but the drawing entities at the jamb were never
read; a column drawn over a wall face was taken as wall | a door piece is read at its jambs (wall-face line ends, gap =
width, face pair = depth) before any closure reading; a column outline proud of a printed wall face inside a printed
box is deducted from the floor and turned up by the membrane (every villa) | tests/t336_wp_binding (column notch normal;
window below its sill deducted refused; door row twice refused; held as 0 refused) | PROPOSED.
