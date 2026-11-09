# T-579 reconciled-quantities statement V5 (research, unwired; for the 12-13 Nov milestone)

Worker 3 (lane I, non-candidate, integration dependency, backlog-permitted), 2026-11-06. Files: `t579_adapters.py`
(R-T579-1), `t579_build.py` -> `out/RECONCILED_STATEMENT_T579.json` / `.md` (`--check` rebuilds byte-identical),
`tests/t579_statement_v5/` (15). The T-570 builder is imported read only; the build first rebuilds statement V4 and
refuses to run unless it equals its committed JSON and markdown. Every source is sha256-pinned (T-560, T-568, T-569 V8,
T-572, T-573 outputs, V4, LINE_INDEX_V3_0_57). No drawing, workbook or client data; no candidate, rule, knowledge or
registry file; no quantity moves; nothing released. Statement sign: reference - engine. T-571 / T-574 not merged at
claim: pending.

## What each merged report adds (every new section re-sums from its source JSON, residual 0)

| Report | Section(s) | Unit | Reference | Engine valued | Net (ref - engine) | Classes / status |
|---|---|---|---|---|---|---|
| T-560 | T-560/rebar (6 scope groups) | t | 44.190000 (TYPED_LUMP) | 9.375306 | +34.814694 | RULE_DIFFERENCE, quantity UNRESOLVED, **no %**; held 14.278249 .. 19.646878 + 799 blank beside; lift-pit walls (G2) and dome shells + rings (G5) ENGINE_OMISSION of a line, no bound, fix row V8 REBAR_OMISSION; tank NOT_COMPARABLE |
| T-568 | alu-doors nr / m2 | nr, m2 | 5 / 12.000 | 6 / 12.760 | -1 / -0.760 | count ENGINE_RIGHT -1 (CONFIRMED); m2 ER -1.720, RD +0.960 (Q-55 C heads); -20.00 % / -6.33 % (no HELD) |
| T-568 | windows nr / m2 | nr, m2 | 29 / 116.900 | 28 / 76.256 | +1 / +40.644 | HELD 1 (W02 count 1 .. 2); HELD 36.669 (W02, W17) + ER 3.975; like for like 80.231 vs 76.256 (-4.95 % engine vs ref.); EXPECTED with the V8 W17 row 89.681 vs 86.126 (-3.96 %), beside only |
| T-568 | internal-doors nr / m2 (COUNT CROSS-CHECK, his masonry deduction rows) | nr, m2 | 18 / 36.96 | 15 settled / 28.600 | +3 / +8.36 | nr: HELD +5 (5 drawn leaves on HELD-width lines) + ER -2 (CONFIRMED: 20 drawn vs his 18); m2: HELD 9.84, ER -3.960, RD 2.480 |
| T-568 | T-543/blockwork (V4) 8 T-559 opening rows | m2 | unchanged | unchanged | unchanged | **F-T579-1** UNRESOLVED +6.30 -> ER +6.54 / RD -0.24 (class only); section UNRESOLVED 58.506437 -> 52.206437 |
| T-572 | held-bounds (8 families) | m3 | - | as V4 | - | necks family AT_LEAST 9.7239 (high OPEN); pits backfill lower end AT_LEAST 99.645011; others not stateable (items named); every family's valued equals its V4 section / T-565 block |
| T-572 | measured set GF / 1F columns, pads | m3 | 11.53125 / 2.553 / 67.0665 | 12.705 / 3.108 / 67.6945 | -1.17375 / -0.555 / -0.628 | -10.18 / -21.74 / -0.94 % (like for like); net of JOINT_HEAD RD +0.710 (+6.16 %) / -0.170 (-6.66 %) |
| T-572 | measured-necks | m3 | 8.805 | AT_LEAST 8.8695 | none | BELOW_DRAWN_LOWER; no %, never a point |
| T-573 | ceiling-board | m2 | 409.58 | 366.891177 | +42.688823 | ER -0.1162, HELD 36.52, TOL 0.124317, UNRES 6.160706; headline -10.42 % NOT a verdict; like for like 110.05 vs 109.691183 (-0.33 %) |
| T-573 | ceiling-cove | lm | 427.46 | 0 (no line) | +427.46 | **F-T579-2** HELD -> UNRESOLVED (no candidate line, R-T554-1 (d)); T-283 ledger 288.64 m beside |
| T-573 | ceiling-paint | m2 | 452.325 | 394.825677 | +57.499323 | board classes + RD 42.745 (cove strips) + **F-T579-3** bulkhead faces -27.9345 NOT_IN_HIS_ROWS -> UNRESOLVED |
| T-573 | bulkhead, dome: NOT_COMPARABLE; stair soffit, exterior soffit: CROSS_REFERENCE | | | | | stair soffits checked equal to V4 T-561/stair-soffit; his row 73 (19.154) checked equal to its V4 T-552/plaster-external rows (RD 12.834 + ER 6.32) |
| T-569 | manifest V8 rows beside | | | | | 5 rows, candidate_line false, 36 planned element ids (30 return paint + 6 rebar) checked absent from the index; switch conditions named (F-C-T570-1: return paint stays ENGINE_WRONG 23.07 until the 30 FIN.PAINT return lines exist) |

## R-T579-1 (proposed, every villa; module docstring)

(a) TYPED_LUMP reference: smallest common scope group, RULE_DIFFERENCE, no %, a line omission rides on the group; (b)
a one-sided bound is AT_LEAST x / high OPEN; a family total only when every held component has that end; never a low of
one subset beside a high of another; % only on the like-for-like measured set; (c) a manifest row is beside, its
element ids absent from the index, its figure never valued; (d) kg inside, t once; one unit per section; (e) a
headline % with HELD / scope causes is printed NOT a verdict; (f) a reference row that is a term of another section is
a CROSS_REFERENCE checked equal, never added twice; (g) non-class verdicts mapped once by name (F-T579 tags); a later
report restates a V4 row's class only.

## Findings for the Checker

- F-T579-1: V4 still carried T-559's +6.30 m2 opening counts UNRESOLVED inside T-543/blockwork; T-568 settles them
  (counts 3.94 + 1.98 CONFIRMED by the Checker's leaf census; widths / W18 size worker-proposed, ACCEPTED).
- F-T579-4 (double count guard): his pool-court soffit row 73 and his door deduction rows are already terms of V4
  sections; V5 shows them by face class / as count checks only, never in a second total.
- F-T579-5: T-572 `bounded_part_low` 38.644269 for B1-02 adds the lower-only 37.575 to the both-ends low 1.069269
  while `bounded_part_high` 1.176467 is the both-ends part alone; V5 prints the two parts apart (no 38.6 .. 1.2 range).
- The T-572 split classes other than JOINT_HEAD (COUNT, BASE, GLOBAL_DEPTH -> ENGINE_RIGHT; HEIGHT_OPEN -> UNRESOLVED)
  use the T-570 COUNT_VERDICT map of the same split vocabulary: worker-proposed.
- F-T579-3 bulkhead paint: owner Q-57 A mod (6) paints BOARD + BULKHEAD, so RULE_DIFFERENCE is the likely class;
  printed UNRESOLVED until the Checker classes it (no verdict invented).

Lesson row proposal (ERS s.7): | 2026-11-06 | statement V4 kept T-559's opening counts UNRESOLVED after T-568 settled
them, and two reference rows (pool soffit, door deductions) were about to enter a second section | a statement is
restated row by row when a later report settles a cause, and a reference row already in one section is only
cross-referenced | each later report names the V4 rows it settles (class only, delta kept) and every reference row is
checked to sit in one total (every villa; T-579, R-T579-1 (f) / (g)) | tests/t579_statement_v5 | PROPOSED |
