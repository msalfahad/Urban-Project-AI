# T-561 B6 wall paint (internal + external) vs the freelancer, by face class (research, unwired)

Worker 2 (lane A), 2026-11-06, claim 12:41 UTC. Files: `t561_paint_rules.py` (R-T561-1, any villa; reuses the R-T552-1
bridge unchanged), `t561_inputs.py` (candidate line ids, his paint cells as numbers by sheet row, merged ledgers cited;
no coordinate, no client name), `t561_alsenan.py` -> `out/T561_PAINT_RECONCILE.json` (`--check` rebuilds
byte-identical), `tests/t561_paint_reconcile/` (19 tests). No engine module, method, rule / knowledge version, registry
or candidate file changed; no quantity moves. Drawing values are the merged T-128 r3 / T-173 / T-281 / T-552 ledgers,
cited and sha256-pinned, not re-measured this run.

## 1. Physical element and face classes (ERS s.2.1)

A painted face is a DRY wall face from the finished floor to the FINISHED CEILING (owner 2026-11-02; Q-48 A / Q-52 C),
net of every opening inside that height (Q-73 full). A shaft is painted at its full exposed height to the decor line
under the roof (Q-72 B, T-173). A full-height porcelain face is never painted (UP-FIN-PAINT-001; owner wet-area rule
2026-11-02); a part-height tile leaves a band. Returns (jambs / head) are their own class. A flight soffit is a CEILING
face (Q-57, FIN.STAIR.SOFFIT). Coats are a rate (material / labour), never an area factor.

Candidate V3.0.58 (= V3.0.57 paint lines): FIN.PAINT 45 lines, valued **217.2081 m2** = 4 released dry rooms (GF-15
56.0131, 1F-01 51.415, 1F-04 52.005, 2F-03 57.775); 7 dry room lines HELD; 3 shaft lines HELD; 17 wet "paint above wall
tile" lines EXCLUDED (tile runs to the decor ceiling, Q-48 A: no band exists); 14 superseded route lines EXCLUDED. No
FIN.PAINT return line. Every FIN.PAINT value equals its FIN.PLASTER twin (asserted line by line).

His paint workbook: wall statement rows 4-27, gross **1,249.375** (J28); half of his opening list 116.495 (same list as
his plaster) -> net **1,191.1275**; decor paint 452.325 (ceilings, listed beside); NO external row.

## 2. Internal: his gross 1,249.375 - engine valued 217.2081 = +1,032.1669 m2, by pair, residual named

| Pair | his gross | engine | gap | HELD | RULE_DIFF | ENGINE_RIGHT | UNRESOLVED |
|---|---|---|---|---|---|---|---|
| DRY (11 lines + his wash row 9) | 948.505 | 217.2081 | +731.2969 | +587.71805 | +90.15325 | +53.4256 | 0 |
| SHAFT (rows 24, 25, 8) | 244.920 | 0 | +244.920 | +175.14 | +1.93 | +13.85 | +54.00 |
| RETURN (row 27) | 15.960 | 0 | +15.960 | +23.070 | - | - | -7.110 |
| CEILING: stair soffits in his wall paint (rows 18-19) | 39.990 | 0 | +39.990 | +22.149034 | - | - | +17.840966 |
| **Total** | **1,249.375** | **217.2081** | **+1,032.1669** | **+808.077084** | **+92.08325** | **+67.2756** | **+64.730966** |

- His paint = his plaster + 39.99 exactly (rows 18-19 'for the stair soffits': 1.20 x 20.20 + 2.10 x 7.50, absent
  from his plaster sheet); every other row is his plaster row 1:1 (F, H asserted). So the DRY pair is T-552's DRY pair
  number for number, but for PAINT its causes are right: the line heights (owner G1 3.65 / 3.35 / 3.15) ARE the paint
  basis, so his flat 3.60 / 3.40 / 3.50 is a RULE_DIFFERENCE (Q-48 A), not an engine error (for plaster the same
  height was ENGINE_WRONG, T-552 s.3).
- DRY: HELD = 7 HELD lines at engine-basis gross; RULE_DIFFERENCE = openings of the 4 released lines in his gross
  (42.30195) + height (+21.93) + his GF annex wash row 9 (7.20 x 3.60 = 25.92): a WET space he paints AND tiles (his
  ceramic row 51, T-547): one finish per face (UP-FIN-PAINT-001); ENGINE_RIGHT = his lengths vs the drawn faces
  (1F-13 +34.59, 1F-10 +20.74, others -1.75 .. +3.82; T-128 two traces).
- SHAFT: T-173 paint gross 175.14 (b 0; 171.88 at b 0.10; net 154.87 .. 159.03, 135.26 with every held item
  deducted); his box south +20.11, north -2.64, west / east -3.62 (ENGINE_RIGHT, T-173); paint top +1.93
  RULE_DIFFERENCE (paint stops at the decor line under the roof: plaster gross 177.07 - paint 175.14); RESIDUAL 54.00
  named (his row 25 2.50 x 5.40 and row 8 'stair wall' 11.25 x 3.60: no drawn face).
- RETURN: **ENGINE_OMISSION**: no FIN.PAINT return line although all 26 door returns are plastered (FIN.PLASTER
  OPENING lines 23.070 m2) and their exposed part is painted. HELD, bounded above by 23.070 (painted part = return face
  - the frame-covered depth, frame detail not printed); RESIDUAL -7.11 (his 14 doors x 0.20 x 5.70, not by id).
- CEILING: his rows read as ST-01 (service / shaft stair, 1.20 wide) and ST-02 (hall stair); T-281 measured true soffit
  17.243246 + 4.905788 (method D); candidate FIN.STAIR.SOFFIT lines HELD blank; RESIDUAL 17.840966 named (his sizes vs
  the T-281 rows + T-281 rows still HELD: ST-01 1.50 m2 plan, ST-02 RS-C curved flight 4.443156 m2 plan).

Net view: his net 1,191.1275 - 217.2081 = +973.9194 = the gross gap - his half deduction 58.2475 (his step, never a
component).

## 3. Two methods side by side (ERS s.2.2): paint height of the 11 dry lines

| Column | basis | gross, 11 lines |
|---|---|---|
| Owner G1 (candidate) | interval - 0.60 - 0.15 - 0.10 (Q-48 A) | 847.2281 |
| Drawing-derived (T-128 r3) | interval - slab 0.16 - b 0 .. 0.10 - decor 0.15 | 956.43 .. 981.24 (+109.20 .. +134.01) |
| Freelancer, same rooms (no wash) | flat 3.60 / 3.40 / 3.50 | 924.205 |

Released lines, net: GF-15 56.0131 vs 63.24 .. 64.89; 1F-01 51.415 vs 59.20 .. 60.97; 1F-04 52.005 vs 56.11 .. 63.73;
2F-03 57.775 vs 63.34 .. 69.78. The finished-ceiling level is printed nowhere (no reflected ceiling plan, O-P8-02), so
the drawing-derived column is an UPPER bound (a crossing beam or bulkhead lowers it) and the owner column is the
approved fallback that Q-52 C calls an approximation. Status proposal: the 4 released paint lines PROVISIONAL (ASSUMED -
OWNER-APPROVED, Q-48 A) with the bound beside; designer item (ceiling level per room), not an owner question (s.2.7).

Register 'WALL PLASTER HEIGHT vs PAINT HEIGHT' (JSON `plaster_vs_paint_height`, 11 rows): plaster to the slab / roof
underside (3.74 .. 4.34, T-552 / T-556), paint to the finished ceiling (3.15 / 3.35 / 3.65 owner). Today the code path
writes one height for both (FIN.PLASTER = FIN.PAINT per room); the plaster restatement must not move paint.

## 4. External paint

His paint workbook prices no exterior face (row 29 'windows external spaces' is an opening of his internal list). His
exterior coating (Sigma) is his exterior plaster area (OWNER_NOTES_SIGMA_2026-10-21: 1,502.84 gross / 1,469.97 net),
reconciled once in T-552 s.4 / T-567. Engine valued 0: FIN.EXT.FINISH 3 + ARCH.FACADE 4 HELD blank (T-314 QUEUED);
EXT.FENCE.PAINT 8 HELD (Q-65 C, another trade). Gap on the paint workbook 0. Ceiling paint beside: his decor 452.325 vs
31 FIN.PAINT.CEILING lines 394.825677 valued (not reconciled here: ceiling family).

## 5. Verdict proposals, rule, lesson, missing

- DRY: ENGINE_RIGHT on lengths and height basis; RULE_DIFFERENCE heights / half deductions / wash row; not comparable
  as a whole while 7 of 11 lines are HELD (587.72 of 731.30). SHAFT: ENGINE_RIGHT on scope, 54.00 UNRESOLVED. RETURN:
  ENGINE_OMISSION (HELD <= 23.070), -7.11 UNRESOLVED. Soffits: RULE_DIFFERENCE of class (CEILING, not wall paint).
- R-T561-1 (module docstring): paint to the finished ceiling, plaster basis refused for paint; two methods side by
  side; coats a rate; one finish per face across his workbooks; soffits CEILING; bridge = R-T552-1.
- Tests: villa P561 (4.00 x 5.00, ceiling 3.00, door 0.90 x 2.20, two coats -> 52.02 not 104.04; part-height tile band
  22.74; G1 3.15 vs drawing 3.59 .. 3.69; order invariance) + adverse (coats multiplied, plaster basis for paint, full-
  height tile painted, unknown sill in a band, soffit in a wall pair, HELD as 0, freelancer figure as a component, lm
  in an m2 pair, missing term / source) + development-villa pins.
- Lesson proposal (ERS s.7): "paint lines copy the plaster lines one for one | one height and one face set per room in
  the code path, and no return paint line | keep plaster and paint heights as two fields and give every plastered
  return a paint line HELD on the frame detail | tests/t561_paint_reconcile | OPEN until integration".
- Missing: finished-ceiling level per room; frame detail (painted return depth); his door list by id; T-281 HELD rows;
  build-up b and roof datum (D-39); an independent re-measure this run.
