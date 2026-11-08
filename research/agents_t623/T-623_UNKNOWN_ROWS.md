# T-623 B10 beams and columns: the 18 UNKNOWN rows of statement V10 re-measured from the drawing

Worker 1 (lane S, non-candidate, evidence row), 2026-11-08, run session_01E6cPneJu8LgxaYGTncX7fK, branch
`agents/task-T-623`. Research only: no engine module, candidate line, released line, rule register, method version or
frozen file changed; nothing released. Development villa, not an accuracy claim. ERS s.2 - 4, s.7; UP-CONC-JOINT-001
1.0.0; R-T600-1 r2; R-T610-1; R-T614-1; R-T613-1.

## 0. Sources and run

- Rows: statement V10 (T-609) `sections_v10` [2] T-545/beams@V10 and [3] T-551/columns@V10; the rows the scorecard
  (T-613) counts UNKNOWN: beams 12 of 24, columns 6 of 19.
- Drawing (own read this run): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179, `.work/private`
  only). Every length, area, radius and count is read from the raw DXF entities by hex handle (face LINEs on layer
  '1', S-COL.BON outlines, the ring ARCs, the section outlines, S-TEXT tags). Route G is used only as a locator (which
  two faces form a band, which frame is which storey, the schedule depth bound to a band's mark).
- Freelancer: the concrete + rebar workbook (beam sheet, columns sheet), `.work/private` only. Tracked output carries
  handles, m3 / m2 / m and classes; no coordinate, no row, length or count of his.
- Engine: V3.0.57 LINE_INDEX (= V3.0.58 for beams and columns), T-252 ledger runs, T-394 member record.
- Code: `t623_rules.py` (R-T623-1 .. 3), `t623_alsenan.py` -> `out/T623_UNKNOWN_ROWS.json`; tests `tests/t623` (30).

```
.work/venv/bin/python -I research/agents_t623/t623_alsenan.py .work/private/ST7757.dxf .work/private/concrete_rebar.xlsx --check
```

## 1. Result (reference - engine, m3; statement sign)

| Row | Statement | Own re-measure | Drift | Class after | Evidence (raw handles) |
|---|---|---|---|---|---|
| GF B1 RUN_COUNT | -0.210119 | -0.210741 | -0.000622 | ENGINE_RIGHT | 12 drawn B1 pieces, face pairs 429/27A .. 2B5/2B8; his B1 length is shorter than the drawn face-to-face length, so none of it can be run-through |
| GF B11 DRAWING_PRECISION | -0.004050 | -0.003762 | +0.000288 | ENGINE_RIGHT | faces 428 / 28F, trapezoid 0.915016 m2 (oblique end) x 0.75 |
| GF B8 DRAWING_PRECISION | -0.003021 | -0.003021 | 0 | ENGINE_RIGHT | faces 42C / 46D, 0.704028 m2 x 0.75 |
| GF B2 MARK_BOUNDARY | +0.011152 | +0.012000 | +0.000848 | ENGINE_RIGHT | 3 pieces (284/286, 292/296, 29E/2B9) 0.632; end supports 32C, 36B, 32F, 341 (0.50 each), 34A 0.20, 356 0.40 -> allowance 0.208; beyond 0.012 fits the collinear piece BAND0020.1 that the drawing labels B1 (0.064) |
| GF UPSTAND (B20) | -0.120000 | -0.120000 | 0 | ENGINE_RIGHT | section A-A outline 560: 0.340 m2 at scale (base = b 0.40) - 0.40 x 0.75 = 0.040 = 0.20 x 0.20; clear span 3.000 m (faces 458 / 2C6, column faces) |
| 1F B11 DRAWING_PRECISION | -0.007173 | -0.007173 | 0 | ENGINE_RIGHT | faces 5C3 / 6C1 |
| 1F B6 DRAWING_PRECISION | -0.000273 | -0.000273 | 0 | ENGINE_RIGHT | faces 6D5 / 6D6 |
| 1F CB12 BEYOND_EXTENT | +0.160962 | **+0.187500** | **+0.026538** | ENGINE_RIGHT | faces 5DE / 5DF; end supports 69D (0.20) and 676 (0.25): outer-face extent 12.000 m; his row runs 1.000 m beyond it x 0.25 x 0.75 |
| 1F UPSTAND (B23) | -0.120000 | -0.120000 | 0 | ENGINE_RIGHT | section B-B outline 16BF: 0.3775 - 0.45 x 0.75 = 0.040; span 3.000 m |
| 1F DOME_RING | -0.755200 | -0.755240 | -0.000040 | ENGINE_RIGHT | arcs 5FE/5FF + 600..603: r 2.211 / 2.411; bay faces 5E8 / 5C7 / 6DF / 6BB (4.100 x 4.422): ring in bay 1.510481 m2 x 0.50 |
| GF THROUGH_SUPPORT residual | +0.620464 | +0.620464 | 0 | UNRESOLVED (parts) | J re-measured member by member: 20 / 20 GF members agree (A from the outline, D_ctrl = deepest beam framing in), J 2.281250 |
| 1F THROUGH_SUPPORT residual | +1.208362 | +1.208362 | 0 | UNRESOLVED (parts) | 6 / 6 members, J 0.385000 |
| GF C1 COUNT | +0.375 | +0.375 | 0 | ENGINE_RIGHT | 1 drawn C1 (341, 0.20 x 0.50); 1 C1 tag on the GF column plan (1079); his own neck rows carry the same count as the drawing |
| GF C2 COUNT | +0.750 | +0.750 | 0 | ENGINE_RIGHT | 4 drawn (32C, 32F, 33B, 33E); 4 tags (1061, 1063, 1077, 107B); his neck rows = drawing count |
| GF BASE | -0.1925 | -0.1925 | 0 | ENGINE_RIGHT | A 365 0.125, 35F 0.150 (own outlines) x 0.70 (base +0.25, T-287 G1 cited) |
| GF GLOBAL_DEPTH | -0.11875 | -0.11875 | 0 | ENGINE_RIGHT | sum A x (D_ctrl - 0.75) over the 20 members above |
| 1F C3 COUNT | +0.345 | +0.345 | 0 | ENGINE_RIGHT | 2 drawn (68B 0.20 x 0.50, 691 0.25 x 0.50 CONFLICT, held); no 1F column tag sheet read |
| 1F GLOBAL_DEPTH | -0.095 | -0.095 | 0 | ENGINE_RIGHT | 6 members (66A, 66D, 670, 67C, 67F, 682) |

Line totals (UNKNOWN rows only): beams statement +0.781104 -> own +0.808116 (drift +0.027012 = CB12 +0.026538 and four
drifts under 0.001 m3 each, +0.000474); columns +1.063750 = +1.063750. 15 of the 16 measurable rows reproduce the
statement within 0.001 m3 (CB12 differs, named in s.2); the 2 THROUGH_SUPPORT residual rows stay UNRESOLVED (closure terms, R-T600-1 r2: his rows carry no location),
re-measured in the part the drawing settles (J). No row is HELD on a designer item (the D-16 / D-27 / D-02 rows of these
lines are the HELD rows, not UNKNOWN; they stay HELD by name).

## 2. What changed in engineering terms

- **1F CB12 (finding F-T623-1)**: his CB12 row runs 1.000 m beyond the drawn member measured outer face to
  outer face (12.000 m). Statement V10 carries BEYOND +0.160962 and THROUGH_SUPPORT +0.254887 (row 12, PARTIALLY
  VERIFIED); the drawing gives BEYOND +0.187500 and his excess inside the extent over the engine lines
  2.250000 - 2.021651 = +0.228349. Both splits re-add to his - engine = 0.415849. Cause: T-545 took the support
  allowance (ends 0.20 + 0.25, gap at 664 0.899 m) at the full section without netting the beside strip the engine
  already bills in the gap (664 is 0.20 wide under a 0.25 band, R-T614-1). Proposal (fix row for the statement, not
  this task's files): row 17 0.160962 -> 0.187500, row 12 0.254887 -> 0.228349; line total unchanged; class unchanged.
- **Columns**: every compared member's controlling depth was re-derived from the drawing (deepest beam whose drawn end
  stops on the outline or whose band runs over it); a beam running alongside a face is not a framing member (a 1 cm
  proximity test overstates D_ctrl). With the end / overlap test, 26 / 26 members agree with the T-119 record (A and
  D_ctrl), so J and GLOBAL_DEPTH are reproduced member by member.
- No ENGINE_WRONG found. No quantity of the candidate moves.

## 3. Verdict proposals (who is right)

ENGINE_RIGHT 14 rows (drawn solids or drawn heights his rows omit or overstate, hand values above), UNRESOLVED 2 rows
(pair closure; T-600 capacity terms cited), F-T623-1 a statement split correction of +0.026538 between two rows of the
same line (no total change). ERS s.2.7 not met: **no owner question**.

## 4. Rules, tests, lessons row (proposed)

R-T623-1 (row re-measure, drift <= 0.001 m3 or a named physical cause), R-T623-2 (line split exact; BALANCE / SHORT /
REMAINDER / PLUG refused as a class or cause), R-T623-3 (each piece once). `tests/t623` (30): hand villa V623 (beam
0.25 x 0.60 over a wide and a narrow column: own 0.792, reference 0.900, delta 0.108 = 0.060 + 0.048; beside strip 0.02
m2 once), mirror / rotation, oblique drawn end kept and long shared face clipped, ring in a bay, counts and global depth;
adverse (balancing class / cause, open sum, HELD as 0, mm / m2, missing depth, fractional count, open D_ctrl, drift
without a cause, non-parallel faces); development villa from the committed output; private rebuild equals committed.

Lessons row (ERS s.7): | 2026-11-08 | 1F CB12 BEYOND read as 0.161 m3 | the support allowance in the gap was taken at
the full section although the engine bills the beside strip of the narrower gap column | a through-support allowance
is netted of every strip the engine line already bills at that support (narrow column, R-T614-1) before the beyond
term is read (every villa; provenance T-623, R-T623-1) | tests/t623 | PROPOSED |

## 5. Checker re-measure list (rows not read in T-180)

- Beams: 1F CB12 extent (69D / 676 outer faces, faces 5DE / 5DF); 1F ring (arcs 5FE / 600, bay faces 5E8 / 5C7 / 6DF /
  6BB); GF upstand (section outline 560, span between the column faces).
- Columns: GF C2 (32C, 32F, 33B, 33E against the SH12 tags) and the 1F GLOBAL_DEPTH set (66D 0.40, 670 0.50).
- `test_private_rebuild_equals_committed` with `.work/private/ST7757.dxf` and `.work/private/concrete_rebar.xlsx`.
