# T-383: the export-side completeness join for the waterproofing lines (inside the T-471 framework)

Worker 1, run session_01E6cPnbnVUfm6JN2UJzxWaH, 2026-11-02. Read-only on quantities: no candidate line, quantity, state
or V2.9 cell moves; no candidate module changed. Drawings are named by Drive folder and title only.

## 1. Cause (why no WP line could ever count WHOLE)

`tools/boq_export_v1.completeness_from_report` states completeness per PRINCIPAL TRADE. WATERPROOFING is one trade
spanning 20 BOQ lines on the development villa (one per item code and unit), so every WP line carried the blocker
`TRADE WATERPROOFING SPANS n BOQ LINES` whatever the T-301 inventory said (reproduced on a hand villa:
tests/t383_wp_completeness_join::test_the_t236_trade_join_alone_can_never_close_a_wp_line_and_the_overlay_can).

## 2. What changed

- NEW `research/agents_t236/wp_join.py` (rule R-T383-WP-WHOLE-1, project-independent): reads the merged T-301 inventory
  join ONE BOQ LINE (trade + item + unit) at a time and writes the export's own `URBAN_LINE_COMPLETENESS_V1` record per
  WP line; `components()` gives the T-471 rows (T-471 `state_of_kinds` unchanged) with the WP inventory status
  ABSENT / INCOMPLETE / COMPLETE beside them; a component the lines would read VERIFIED stays APPLICABLE_HELD / HELD
  while its inventory is not COMPLETE.
- `tools/boq_export_v1.py`: `wp_overlay()` (join reader only) + `build(..., wp_completeness=None)` + CLI
  `--wp-completeness`. Without the option every byte is as before. With it only WATERPROOFING groups' records are
  replaced; the decision is the unchanged `completeness_passes` (inventory = scope, missing 0, duplicated 0, held 0,
  no blocker) and a WHOLE V2 Checker record is still required. Refused: other schema / project / revision set, a
  record for a non-WP group, a group twice, a WP line the join does not carry.
- NEW `research/agents_t236/wp_join_devvilla.py` + `WP_JOIN_T383_DEVVILLA.json` (development villa, committed data).

## 3. Development villa result (T-301 inventory 416 elements: IN_LINE 320, NA 96, MISSING 0)

| WP line | Scope / inventory (export units) | Faces held | Residual | Record |
|---|---|---|---|---|
| WP.FOUNDATION.LIFT_PIT_SCREED m2 | 1 / 1 | 0 | 20.700 - 20.700 = 0.000 m2 | PASS |
| WP.FOUNDATION.LIFT_PIT_SCREED m3 | 1 / 1 | 0 | 1.035 - 1.035 = 0.000 m3 | PASS |
| FOOTING_MEMBRANE m2, FOOTING_SCREED m2 / m3 | 2 / 2 | 1 each (1B1B two tags, Q-31 C) | 0.000 | HELD 1 |
| LIFT_PIT_MEMBRANE m2, LIFT_PIT_BOARD m2 | 2 / 2 | 1 each (pit walls, D-43) | 0.000 | HELD 1 |
| BURIED_LIQUID m2 | 5 / 5 | 178 | 0.000 (45.4682 m2 released) | HELD 178 |
| FOOTING_SIDES m2 | 1 / 1 | 25 (Q-21 C) | blank | HELD 25 |
| PROCUREMENT item | 1 / 1 | 1 | blank | HELD 1 |
| 10 FIN.WP.* lines (wet area, roof, rolls) | - | - | - | NO WP INVENTORY (blank, never 0) |

Pit screed physical check (Checker T-353 (e), own DXF read): FF lift base 4.600 x 4.500 = 20.700 m2; x 0.05 printed
screed = 1.035 m3. Both lines carry WHOLE V2 records (V3.0.17 set; re-bound by content on V3.0.41: V2-32fea7d28d834cc0,
V2-3f061a0ed6dc5943).

Whole-line count restated: today 1 (CONC.SLAB). With the join read by the export, 2 WP lines close
(LIFT_PIT_SCREED m2 and m3) -> 3, PROVIDED the Checker re-runs the export on the candidate of record with
`--wp-completeness` and the two records still bind (the B8-08 lines are unchanged V3.0.15 .. V3.0.43, T-353 Gate A).
The Lead's expectation "0 WP WHOLE" assumed only wet-area lines; the foundation pit screed is a one-face item that
genuinely closes. Every other WP line stays NOT VERIFIED with a named blocker. T-471 component states unchanged
(C-B8-01/02/03/05/06 HELD, inventory ABSENT; C-B8-08 HELD, inventory INCOMPLETE).

Engine vs freelancer: no quantity moves; the freelancer has no foundation WP rows (FREELANCER_WRONG on scope, T-219 /
T-263, unchanged). Verdict proposal for the Checker: ENGINE_RIGHT on the pit screed scope (20.700 m2 / 1.035 m3, one
face, nothing held or missing).

## 4. Tests

tests/t383_wp_completeness_join (21): hand villa VW-383 normal (2 lines close, export verifies them only, non-WP rows
and summary byte-identical, T-236 trade join alone fails with SPANS) and adverse (face in two lines, NA without
evidence, MISSING as 0, dropped element prints MISSING never WHOLE, residual -0.010 m2, held face, unlinked line,
register-only key, five export-reader refusals, T-471 verified lines with absent inventory stay HELD, CLI); development
villa pinned (committed report reproduced).

## 5. Missing / for T-310

- Wet-area (B8-01/02/03/05) and roof (B8-06) inventories do not exist: those 10 WP lines cannot count WHOLE until the
  T-209 wet-room set / roof planes are built as T-301 inventories (named gap, not this row).
- T-310 consumes it: pass `--wp-completeness WP_JOIN.json` beside `--completeness` (the T-236 report) on the export.

Lessons-register row (proposed, ERS s.7): 2026-11-02 | 7 WP lines with V2 records, 0 counted WHOLE | the trade-level
completeness join cannot close a trade that spans several BOQ lines | completeness of a multi-line trade is read per BOQ
line (item + unit) against its own inventory elements; an absent inventory blocks, never passes (PROJECT-INDEPENDENT;
provenance T-236, T-298, T-301, T-383) | tests/t383_wp_completeness_join | OPEN until merged and T-310 wires it.
