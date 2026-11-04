# T-512: gate fix (t212 red) + all-blank item code printed as 0.0

## (a) t212 guard property red on 40ab9061
`engine/source/band_gap_classes_v1.py` (T-510, merged 9e86fcf5) carried no default-guard class. Class from the module:
it produces opening deductions (width x printed height, `DEDUCT_MEASURED`) and net wall areas, and no candidate,
released method or CLI imports it (importers: research/agents_t510, tests/t510 only) -> **UNWIRED_PRODUCER**, declared
in the module itself (`DEFAULT_GUARD_CLASS`, line 59), as the T-212 README says for a new module. No test edited.
`guard_property.py check`: problems 0. The class changes to GUARD_HOST / wired when T-513 wires it.

## (b) all-blank code printed as a number (F-C-T508-1, class F-C-T458-2)
Physical meaning: a code subtotal is the installed quantity of its lines. With no established line it is UNKNOWN;
'0.0' asserts the pieces measure nothing. Rule applied: AGENT_BRIEF 'HELD is never 0' + R-T499-1 (a subtotal over a
HELD line is HELD, known part AT_LEAST, held lines listed). A valued line of 0.0 stays a quantity.

`t512_held_totals.py`: `view` / `held_view` (the export view: ALL_VALUED number; PARTIAL 'AT_LEAST x + HELD (n
lines)'; HELD_BOUNDED range; HELD '(n blank lines)'), `check` (codes printing a number with no valued line) and
`census` (every committed research JSON with `totals_moved_by_code` / `by_item_code`, and the candidate method's
`arch_v304.code_totals` run on the committed candidate line index LINE_INDEX_V3_0_55 + the V3.0.56 moved codes).
Cross-check: the index-derived code_totals equals the candidate's own run output on all 4 codes both runs publish
(FIN.SKIRTING V3.0.55; ARCH.WALL_PANEL, ARCH.WALL_VOLUME, MAS.BLOCK from T-488). The index carries the line class
after the T-479 downgrades.

### Census (paths)
| Path | Kind | Codes | Number printed with no valued line | Action |
|---|---|---|---|---|
| `arch_v304.code_totals` -> every arch_v30xx `V3_0_xx_RUN.json` `totals_moved_by_code` (incl. V3.0.56) | candidate method (frozen chain) | 111 at V3.0.56 | 37 (28 HELD with blank lines, 9 HELD_BOUNDED) | NOT edited: handed to the next stream F package (read the totals through `held_view`, or a new code_totals version) |
| research `summary_t*.json` / `V3_0_42_CODE_OVERRIDE.json` `totals_moved_by_code` (19 files) | verbatim copies of the candidate output | 97 rows | 25 rows in 8 files | historical task records, not rewritten; the source is the row above |
| `t469_trade_scoreboard` markdown, keyed cells | research tool, printed view | 4 cells in V3_0_41.md | 4 -> **0** | FIXED: 'released none (0 lines)'; V3_0_41.md regenerated from the committed JSON (test asserts equality) |
| `t469_trade_scoreboard` JSON `by_item_code` | research tool, machine record (`released_lines` 0 beside) | 155 | 54 | named: schema read by t471 (`released_qty or 0.0`); changing it moves t471 / t479 inputs; read through `held_view` |
| T469_SCOREBOARD_V3_0_20.md | historical output, no JSON | - | 4 cells | named, not regenerated |

### V3.0.56 (candidate of record) codes the candidate path prints as 0.0 with no valued line
| item code \| unit | lines | blank | bounded | printed | view |
|---|---|---|---|---|---|
| ARCH.FACADE|m2 | 4 | 4 | 0 | 0.0 | HELD |
| ARCH.SHUTTER|m2 | 3 | 3 | 0 | 0.0 | HELD |
| ARCH.THRESHOLD|m2 | 14 | 8 | 6 | 0.0 | HELD |
| DOOR.MAIN_ENTRANCE|m2 | 1 | 0 | 1 | 0.0 | HELD_BOUNDED |
| DOOR.MAIN_ENTRANCE|pcs | 1 | 0 | 1 | 0.0 | HELD_BOUNDED |
| EXT.FENCE.BLOCK_COUNT|pcs | 1 | 1 | 0 | 0.0 | HELD |
| EXT.FENCE.BLOCK|m2 | 4 | 4 | 0 | 0.0 | HELD |
| EXT.FENCE.GATE|pcs | 2 | 2 | 0 | 0.0 | HELD |
| EXT.FENCE.MASONRY_BELOW_NG|m2 | 1 | 1 | 0 | 0.0 | HELD |
| EXT.FENCE.PAINT|m2 | 8 | 8 | 0 | 0.0 | HELD |
| EXT.FENCE.PLASTER|m2 | 8 | 8 | 0 | 0.0 | HELD |
| EXT.FLOOR.OUTDOOR|m2 | 2 | 0 | 2 | 0.0 | HELD_BOUNDED |
| EXT.POOL.WATER_FACE|m2 | 1 | 1 | 0 | 0.0 | HELD |
| FIN.DOME.SOFFIT|m2 | 2 | 2 | 0 | 0.0 | HELD |
| FIN.EXT.FINISH|m2 | 3 | 3 | 0 | 0.0 | HELD |
| FIN.FLOOR.BED.DRY|m3 | 23 | 0 | 23 | 0.0 | HELD_BOUNDED |
| FIN.FLOOR.BED.WET|m3 | 21 | 0 | 21 | 0.0 | HELD_BOUNDED |
| FIN.MARBLE.LIFT_SURROUND|m2 | 3 | 0 | 3 | 0.0 | HELD_BOUNDED |
| FIN.ROOF.INSULATION|m2 | 4 | 4 | 0 | 0.0 | HELD |
| FIN.ROOF.PROTECTION|m2 | 4 | 4 | 0 | 0.0 | HELD |
| FIN.ROOF.SCREED|m3 | 4 | 4 | 0 | 0.0 | HELD |
| FIN.STAIR.FLIGHT|lm | 14 | 14 | 0 | 0.0 | HELD |
| FIN.STAIR.SKIRTING.SLOPED|lm | 22 | 22 | 0 | 0.0 | HELD |
| FIN.STAIR.SKIRTING.ZIGZAG|lm | 22 | 22 | 0 | 0.0 | HELD |
| FIN.STAIR.SOFFIT|m2 | 2 | 2 | 0 | 0.0 | HELD |
| FIN.WP.DOORWAY_TRANSITION|m2 | 13 | 0 | 13 | 0.0 | HELD_BOUNDED |
| FIN.WP.PENETRATION|pcs | 17 | 17 | 0 | 0.0 | HELD |
| FIN.WP.TERMINATION|lm | 7 | 0 | 7 | 0.0 | HELD_BOUNDED |
| STR.CONC.BOUNDARY_PAD|m3 | 1 | 1 | 0 | 0.0 | HELD |
| STR.CONC.BOUNDARY_WALL|m3 | 1 | 0 | 1 | 0.0 | HELD_BOUNDED |
| STR.CONC.LIFT|m3 | 2 | 2 | 0 | 0.0 | HELD |
| STR.CONC.NECK|m3 | 36 | 1 | 35 | 0.0 | HELD |
| STR.CONC.PARAPET|m3 | 4 | 4 | 0 | 0.0 | HELD |
| STR.EARTH.BACKFILL|m3 | 7 | 6 | 1 | 0.0 | HELD |
| STR.EARTH.DISPOSAL|m3 | 1 | 1 | 0 | 0.0 | HELD |
| WP.FOUNDATION.FOOTING_SIDES|m2 | 1 | 1 | 0 | 0.0 | HELD |
| WP.FOUNDATION.PROCUREMENT|item | 1 | 1 | 0 | 0.0 | HELD |

Quantities: 0 candidate line or total changed (only the printed view). Tests: tests/t512_held_totals (synthetic, not
the training villa: normal mixed -> number + HELD beside; adverse all blank -> HELD, never 0.0; measured 0.0 kept;
bounded-only range; order and mm-scale invariance; inconsistent counts refused).
