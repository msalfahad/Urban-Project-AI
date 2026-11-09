# T-633 B9 blockwork UNKNOWN rows to evidence (research, unwired)

Worker 1 (lane S), 2026-11-09, run session_01E6cPndHxoWSrPpZud2rn4Y. Files: `t633_extract.py` (drawing read),
`T633_DRAWN.json` (metres + DXF handles only), `t633_rules.py` (R-T633-1, any villa), `t633_alsenan.py` (builder),
`out/T633_ROW_EVIDENCE.{json,md}` (the 39-row table), `tests/t633_blockwork_row_evidence/` (16 tests). No engine,
method, rule / knowledge version, registry, candidate or statement file changed; no quantity moves.

## 1. What the 39 rows are

Scorecard V11 (T-620, pinned sha 4e26155f), section T-543/blockwork: reference 1,260.6895 vs engine 467.7925 m2,
difference 792.8970; 50 HELD rows 561.2232755 (untouched) and 39 UNKNOWN rows 231.6737245 m2. The UNKNOWN rows are not
walls: they are the reconciliation components of the 792.90 gap: 22 opening rows (his door / window size vs the
engine's), 1 his-only opening, 8 storey-wall identity rows (drift, height convention, length residual), 1 boundary
wall, 6 parapet rows, 1 'projections' row. Each was given an own value (R-T633-1).

## 2. Own evidence (P7757.dxf sha ab54dd55, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip)

- Door masonry widths, both wall faces agreeing, by insert: D-GF-03 0.900, D-GF-06 1.000, D-GF-08 1.000, D-GF-09
  0.900, D-GF-10 **0.797** (engine nominal 0.80), D-GF-13 1.000, D-1F-02 1.000, D-1F-03 1.000, D-1F-04 0.800, D-1F-07
  0.800, D-1F-08 0.900, D-1F-09 0.900, D-1F-10 0.800 (face handles in the table). Heads: no printed door head; Q-55 C
  2.20 (ASSUMED - OWNER-APPROVED); D-GF-06 head 2.201 drawn in the DWF NE elevation (T-627 binding, cited).
- Window jambs: W13 1.200 / W14 2.450 / W18 0.500 (plan DIMENSIONs 1126 / 1198 / 11ED), W24 **1.552**, W25 1.000.
  Printed heights: W13 230 (SE 2A9C), W14 160 (SE 2B47, measured 1.599), W18 216 (NW 2EFA). W24 / W25 heads 1.50
  from the T-627 DWF binding (cited).
- W15 / W16 (twin arched, NW): plan jambs 1.552 (shown 155); NW elevation jamb verticals 2566 / 256A and 2889 / 288A
  2.161 m, width chains 2E22 / 2DE7 = 1552 exactly between them: rectangle 3.3539 m2; arch segment 1.0088 cited
  (T-227 r2 Checker-verified outline): 4.3627 vs engine 4.363.
- 1F straight-window census: 12 distinct jamb pairs, five at 0.600 (W19 .. W23): his sixth 0.60 x 0.80 has no drawn
  opening (ENGINE_RIGHT -0.48 confirmed).
- Projections: the only printed 7.50 m (GF plan 4E9) spans the east facade holding W02 (HELD, D-53); the only 5.50
  (NW 29D0) is the GF storey chain; no 7.50 x 5.50 masonry element exists in the DXF: stays UNRESOLVED.

## 3. Result: 39 / 39 rows, statement 231.6737245 -> own 231.6726105 m2 (residual -0.001114, all TOLERANCE)

| Class | Statement (39 rows) | Own | Rows |
|---|---|---|---|
| ENGINE_RIGHT | 113.541080 | 113.339424 | 18 |
| RULE_DIFFERENCE | 67.945508 | 68.146050 | 11 |
| UNRESOLVED | 52.206437 | 52.206437 | 6 |
| TOLERANCE | -2.0193005 | -2.0193005 | 4 |

One class move proposed: D-GF-06 height row -0.20 RULE_DIFFERENCE -> ENGINE_RIGHT (head drawn at 2.20, so his 2.40 is
not an owner-rule difference; height evidence cited from T-627). Residuals: D-GF-10 +0.0006 (drawn 0.797 vs nominal
0.80), W15 / W16 -0.000328 each (1.552 vs 1.55 and 2.161), W24 -0.001 (1.552 vs 1.55), GF / 1F height rows +0.000024 /
-0.000082 (6 dp stored mean heights x length): all within R-T633-1 (c); no FINDING. Evidence levels (signed m2):
REPRODUCED 190.0520 (12 rows), OWN_DXF+CITED 39.1993 (6), OWNER_RULE 4.4606 (13), OWN_DXF -0.0200 (4), CITED -2.0193 (4).

Verdict proposals: opening rows ENGINE_RIGHT (widths and printed heights re-measured) or RULE_DIFFERENCE (his flat
2.40 door head vs Q-55 C 2.20, 0.20 x width each); identity rows keep their class (arithmetic reproduced from the T-543
decomposition; their inputs, i.e. wall lengths, are the engine's and NOT re-measured here); boundary RULE_DIFFERENCE
(EXT.FENCE family); parapet height rows ENGINE_RIGHT (concrete / build-up), parapet length census and projections
UNRESOLVED. ENGINE_WRONG: none.

## 4. What is not done (honest scope)

The row-by-row WALL re-measure (length by handle x clear height per member, net of openings) the task text describes
applies to the HELD walls and the length residuals (rows 62 / 69 / 75: +5.52 / +11.24 / -1.76 m2), which rest on the
engine's wall-length census; that census was not re-derived from the DXF this run. Parapet centrelines (58.555 /
49.233 / 29.050 / 136.838 m) are cited from T-319 / T-488, not re-measured. The .dwf was not opened (W24 / W25 /
D-GF-06 heights cited). The Checker should re-measure the three largest rows: 76 boundary 74.40, 88 projections
41.25, 78 RC upstand 41.05.

## 5. Lesson row (proposed, ERS s.7)

| 2026-11-09 | the B9 'UNKNOWN' rows were read as walls; they are reconciliation components | a statement row is a component of the gap, not a physical element | R-T633-1: give each row an own value by its kind (width / height / count / outline / identity), keep the width + height identity per opening, a residual is TOLERANCE only for a <= 5 mm drawn-vs-nominal width or stated input rounding, else a FINDING | tests/t633_blockwork_row_evidence (panel under a beam with a door and a window by hand; adverse: opening not deducted, height to the slab under a beam, missing value, mm units, his-only without census, tampered statement) | proposed |
