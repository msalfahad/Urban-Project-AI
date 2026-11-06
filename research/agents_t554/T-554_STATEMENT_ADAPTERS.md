# T-554 reconciled-quantities statement: adapters T-543 / T-546 / T-542 + Checker corrections (lane I, research)

Worker 3, 2026-11-06, branch agents/task-T-554, base engine a615fa41. Files: `statement_adapters.py` (adapters,
CORRECTIONS table, R-T554-1), `t554_build.py` (`--write` / `--check`), `out/RECONCILED_STATEMENT_T554.{json,md}`,
`tests/t554_statement_adapters/` (19 tests). research/agents_t548 is imported read only (its builder closes every
section). No engine module, rule / knowledge version, registry or candidate file changed; 0 released quantities move.

## 1. Statement on the five merged sources (difference = reference - engine valued; exact Decimal)

| Section | Unit | Reference | Engine valued | Diff. | E_RIGHT | E_WRONG | RULE_DIFF | HELD | TOL | UNRES |
|---|---|---|---|---|---|---|---|---|---|---|
| T-541 roof WP membrane | m2 | 285 (his row) | 209.65844 | +75.34156 | -5.54644 | 0 | +45.992784 | +34.390242 | -0.018026 | +0.523 |
| T-541 roof WP upturn | lm | 194 (his row) | 187.83416 | +6.16584 | -6.24516 | 0 | -27.785396 | +28.300 | +0.003396 | +11.893 |
| T-534 stair bed (+ T-542 beside) | m2 | 39.485 (Q-53 figure, no freelancer row) | 35.4313 | +4.0537 | +4.08 | **+1.4375** | **-14.8694** | +13.405 | +0.0006 | 0 |
| T-543 blockwork | m2 | 1,260.6895 (his rows) | 467.7925 | +792.897 (62.89 %) | +41.05128 (H1) | 0 | +69.625508 | +582.807578 | -2.0193005 | +101.4319345 |
| T-546 wet-room floor WP | m2 | 72.01 (his H39) | 85.57571 | -13.56571 (-18.84 %) | -0.307294 | 0 | -13.235 | 0 | -0.023416 | 0 |
| T-546 wet-room upturn | lm (his 'm.l') | 144.61 (his G40) | 126.072925 | +18.537075 (12.82 %) | -0.5183 | 0 | +3.556 | +13.900 | -0.000625 | +1.600 |

Engine bounded range: AT_LEAST valued .. OPEN on every section with a held line (no held line carries an engine bound
in the statement's unit); the wet floor has no held line (85.57571 .. 85.57571). m2 and lm are separate totals
(builder `merge_totals` refuses them); the stair bed stays an owner-question figure, never a freelancer pair.

## 2. Corrections applied (CORRECTIONS table; a missing or changed target is refused, a dropped one fails the build)

- **F-C-T548-1**: T-534 MS1-LD 1.500 ENGINE_WRONG -> ENGINE_WRONG 1.4375 (drawn 1.250 x 1.150, Checker own DXF
  re-measure; fix row T-502) + RULE_DIFFERENCE 0.0625 (the Q-53 / T-086 reference's 1.20 x 1.25); sum unchanged 1.500.
  T-542's drawing-derived MS1-LD (STAIR_LANDING, Q-53 C) is 1.4375: cross-checked.
- **F-C-T543-1 / F-C-T548-2**: the parapet RC upstand ENGINE_RIGHT 41.05128 m2 carries `depends_on: H1` and the note
  "rests on H1" (his parapet heights from the slab top; with a finish base only (upstand - b_edge) is inside his face,
  HELD on b_edge D-39).
- **F-C-T543-2** (advisory): the height (k) and wall-length residual (m) rows carry "one 'height x length' cause:
  quote together".

## 3. Adapter findings for the Checker (the T-548 guards forced a choice; both named, no number invented)

- **F-T554-2 (T-543)**: the 2F height-convention row (-4.476873 m2) lies wholly on HELD walls (every 2F wall HELD on
  the roof datum D-39; its engine mean height is the b_r = 0.05 what-if). R-T548-1 (e) refuses RULE_DIFFERENCE on a
  HELD engine side, so it is HELD here (source cause RULE_DIFFERENCE kept): HELD 587.284451 -> 582.807578, RULE_DIFF
  65.148635 -> 69.625508; every other T-543 class total is the report's own (test). The GF / 1F height rows also span
  held walls (L_eng includes held walls) but have valued walls too; kept RULE_DIFFERENCE as T-543 classed them (named).
- **F-T554-1 (T-546)**: 2 of T-546's 19 HELD doorway segments have NO candidate line holding them: the GF lobby wash's
  second door and the 1F W.C. by the laundry (no FIN.WP.DOORWAY_TRANSITION line or transition count record in those
  rooms; candidates GF OP-018 / 1F OP-010 are not bound). Under R-T554-1 (d) they are UNRESOLVED (engine NONE), 1.60
  lm, not HELD; a silent-omission candidate (T-493 F-3 pattern), to be bound or confirmed absent by a lane A row.
  The other 17 segments are held by the 14 HELD transition lines (two rooms on the neighbour's shared closure, the
  lobby's OP-017 on the core W.C. 289 line: element ids and count records, line index V3.0.57).

## 4. R-T554-1 (proposed, every villa): cross-family hold

A row's element may be held by a HELD line of another family and unit (parapet above the upstand: STR.CONC.PARAPET m3
under masonry m2; doorway segments: FIN.WP.DOORWAY_TRANSITION m2 under upturn lm). The line is bound HELD in the
index with its item code and unit, listed beside (`held_cross_family`), never valued, and enters the T-548 range with no
bound (it can only open the high end; its own bounds are never converted). A same-unit line is refused (own held line).
No line at all -> never HELD (UNRESOLVED with cause, or ENGINE_WRONG with a fix row). An engine m2 line enters an lm
section only through the engine's own rule height with its source (R-T546-1 (e)), checked exact (lm x 0.20 == m2).

## 5. T-542 beside (no reference figure)

Attached to the stair-bed section, outside every total: whole AT_LEAST 56.35861 m2 = in the V7 wire 35.4325 (= the
section's 11 valued lines 35.4313 + polygon 0.0012) + beyond 20.92611 (7 risers on HELD lines, 4 landings with no line:
MS1-LD, MS2-LD, 2F arrival, RS-LD -> T-502); 6 parts HELD by name; GF hall / lobby in the floor-bed family beside.

## 6. Tests and missing

19 tests: S554 by hand per adapter (blockwork 60.00 = 20 + 4 + 6 + 12 + 9 + 9; wet floor / upturn 1.80 lm with an
unbound doorway; stair beside 3.70), adverse (dropped correction refused, changed correction target refused, HELD given
0 refused, HELD row at 0 refused, m2 + lm refused, lm without height source refused, his m2-labelled lm refused, cross-
family same unit / not HELD refused, unknown parapet row refused), training-villa pins, `--check` reproduces.
Pending adapters: T-545, T-547, T-550..T-553 as they merge.

Lesson row (proposed, ERS s.7): | 2026-11-06 | a held element whose candidate line is in another family and unit could
not be named in a one-unit statement, and two 'HELD' doorway segments had no line at all | R-T548-1 needed held lines in
the section unit | R-T554-1 cross-family hold (beside, never summed, high OPEN only) + no line is never HELD | tests/
t554_statement_adapters | proposed |
