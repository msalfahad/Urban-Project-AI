# T-564 WIRING MANIFEST V7 + FLOOR-FINISH COMPLETENESS CENSUS on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-06, engine base 33a5833f. Not an integration package:
nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is touched. Files:
`floor_census.py` (R-T564-1, any villa), `manifest_v7.py` (builder; V6 pinned by sha256), `WIRING_MANIFEST_V7.json`,
`tests/t564_wiring_manifest_v7/` (21 tests). Rebuild: `python3 -I research/agents_t564/manifest_v7.py` (`--check`).
No drawing read: inputs are the committed line index (LINE_INDEX_V3_0_57 + the 5 T-507 lines) and merged outputs.

## 1. Coverage (R-T549-1)

Range (V6 base 431ac67f, V7 base 33a5833f], first-parent: 6 merges, all covered. Wiring sources: T-553 (F-T553-1,
F-T553-2), T-561 (return-paint ENGINE_OMISSION). NO_WIRING: T-551 (B10 to cause, ENGINE_WRONG none), T-558 (V6),
T-562 (statement adapters), T-566 (the 2 CONFLICT column positions' lines are already HELD).

## 2. Census R-T564-1 (physical element: the finished floor of every enclosed space)

Rules, from the line records only (no room-id list accepted; a keyed call is refused):
C1 a space with a live ceiling or skirting line and no live floor-finish line (B3 finish or the B7 marble that owns
it); C2 a finish whose own bed pair is of the other scope (PORCELAIN on BED.WET, WET_TILE on BED.DRY); C3 per storey,
WP-floor m2 covered by wet finishes (own space + uncovered wet pieces of the storey), residual named; C4 every released
finish has its bed m2 (same area) and bed m3 (HELD). Ceiling / skirting lines with no space key must match a declared
scope (5 exterior slab soffits, 6 B7 stair skirtings) or the census refuses (UNSCOPED).

Candidate (43 space keys): C1 2 hits, C2 1, C3 GF RESIDUAL 9.630133 m2, C4 0.

| Hit | Rule | Verdict | Expected after |
|---|---|---|---|
| 1F-RFFE7AF dressing (ceiling 2.970, ceiling paint, skirting 5.10 lm; ARCH.SPACE 2.970) | C1 | ENGINE_WRONG (F-T553-1) | + FIN.FLOOR.FINISH_HELD 2.970 m2 (area released, material HELD by name); + BED.DRY 2.970 m2; + BED.DRY m3 HELD 0.0891 .. 0.1188 (the candidate's own dry depth 0.03 .. 0.04, Q-45) |
| 2F-ST-ARRIVAL skirting 4.15 lm | C1 | ENGINE_RIGHT | none: floor = B7 landing L-5d2be30d (Q-70 A; T-443) |
| GF kitchen L-83609efc PORCELAIN 9.630001 on BED.WET + WP 9.630001 | C2 | ENGINE_WRONG class (F-T553-2) | re-code to FIN.FLOOR.WET_TILE, 0 m2 |
| GF WP cover residual 9.630133 | C3 | explained | = kitchen 9.630001 + 0.000132 rounding (pantry membrane 13.455 printed 3 dp vs wet pieces 8.954867 + 2.800001 + 0.6 + 1.1 = 13.454868); after the re-code every storey COVERED |

After the expected fixes the census re-runs clean (C1 only the ENGINE_RIGHT arrival; C2 / C4 empty; C3 COVERED).

## 3. Effect (T-553's own figures, restated)

Floor tile engine 387.094050 -> 390.064050 m2 vs freelancer 409.58 (-5.49 % -> -4.76 %). Class split DRY 305.020973
-> 295.390972, WET 75.945577 -> 85.575578, FINISH_HELD 6.1275 -> 9.0975. T-455 bindings: kitchen ADH / TILE rows
code-only (bound 1.926 .. 3.21 bags unchanged; rule net/5 .. net/3 reproduced on 42 released rows, class-independent);
per-code adhesive bound PORCELAIN 61.004 .. 101.674 -> 59.078 .. 98.464, WET_TILE 15.189 .. 25.315 -> 17.115 .. 28.525,
project total unchanged; dressing ADH / TILE new, HELD blank (as the 3 existing FINISH_HELD lines).

## 4. Return paint (T-561 ENGINE_OMISSION)

30 plastered return lines (OPENING / REVEAL), 23.070 m2 valued: one FIN.PAINT return line each, HELD blank, bound
beside 0 .. its plaster m2 (3 have no plaster figure: blank). FIN.PAINT released 217.2081 unchanged. Owner row: none
yet (Lead).

## 5. Wiring rows (Gate B, after T-498 / T-423 r2 / T-563; one package at a time)

FLOOR_FINISH_COMPLETENESS_WIRING (3 adds, 1 re-code, 4 bindings, census re-run in the package) and
PAINT_RETURN_MISSING (30 HELD lines). Every other line byte-identical.

## 6. Lesson proposal (ERS s.7)

"A floor-finish line is complete only when the finished floor of every enclosed space exists once and sits on the bed
of its own scope: join ceiling / skirting / bed / WP by space key, by rule, before reconciling" (scope: any villa on the
engine's id scheme; provenance T-223 / T-435 / T-553 / T-564; test tests/t564_wiring_manifest_v7).

Missing: the dressing's floor material (not printed: HELD); the return-paint depth (frame detail); the package itself.
