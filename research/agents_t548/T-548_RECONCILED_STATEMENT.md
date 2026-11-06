# T-548 reconciled-quantities statement builder (lane I, research, unwired)

Worker 3, 2026-11-06, branch agents/task-T-548, base engine ac3c77b2. Files: `statement.py` (R-T548-1, any villa),
`adapters.py` (T-541, T-534), `t548_build.py` (`--write` / `--check`), `out/RECONCILED_STATEMENT_T548.{json,md}`,
`tests/t548_reconciled_statement/` (16 tests). No engine module, rule / knowledge version, registry or candidate file
changed; 0 released quantities move; the builder computes no new quantity (it reads merged tables and line ids).

## 1. What the builder does (R-T548-1, docstring of statement.py)

Each merged report is normalised into SECTIONS (one item family, one unit, one reference figure). Per section it checks:
units m2 / lm / m3 / nr / kg only and identical on every row and line; engine valued = exact Decimal sum of the valued
line ids (a declared total that differs is refused); a line is valued, held or excluded, never two; the signed rows
(+ = in the reference only) close EXACTLY to reference - engine, otherwise refused; classes ENGINE_RIGHT / ENGINE_WRONG /
RULE_DIFFERENCE / HELD / UNRESOLVED + TOLERANCE (the merged R-T541-1 class for a geometric approximation, kept apart so it
is never shown as agreement); HELD is never agreement: an engine-HELD row must be class HELD (or UNRESOLVED), name a held
line id of its section and carry a non-zero difference; None is refused (never 0); ENGINE_WRONG names its fix row.
Engine bounded range = valued + the held lines' OWN engine bounds (low AT_LEAST, high OPEN when any held line has no
bound); a report's drawing-derived figure never enters it. Totals are per (trade, unit, reference kind): m2 and lm are
never added, and a freelancer row is never added to an owner-question figure. Valued lines are bound to the V3.0.57 line
index (class and measured net must match; lines absent from it are named, never dropped).

## 2. Statement on the merged reports (difference = reference - engine valued)

| Trade / unit | Reference | Ref. | Engine valued | Bounded | HELD | Diff. | E_RIGHT | E_WRONG | RULE_DIFF | HELD | TOL | UNRES |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B8 roof WP membrane m2 | freelancer row | 285.00 | 209.65844 | >= 209.65844 .. OPEN | 1 | +75.34156 (26.44 %) | -5.54644 | 0 | +45.992784 | +34.390242 | -0.018026 | +0.523 |
| B8 roof WP upturn lm | freelancer row | 194.00 | 187.83416 | >= 187.83416 .. OPEN | 1 | +6.16584 (3.18 %) | -6.24516 | 0 | -27.785396 | +28.300 | +0.003396 | +11.893 |
| B7 stair marble bed m2 | Q-53 figure (freelancer: NO row) | 39.485 | 35.4313 | >= 35.4313 .. OPEN | 20 | +4.0537 (10.27 %) | +4.08 | +1.500 | -14.9319 | +13.405 | +0.0006 | 0 |

Every row sums exactly (tests pin each class). The % is the gap of a single line pair, not an accuracy figure.

## 3. Class assignment (explicit adapter tables; an unknown row is refused)

- T-541: its own causes are kept; the adapter adds the engine status (top roof HELD L-3e8fe55d membrane / L-aac1f35e
  upturn, Q-34; dome footprints NONE by Q-24 / Q-29; dome rings, chords, pool court VALUED).
- T-534 (sign negated: T-534 writes engine - reference): COUNT / WIDTH / DEPTH_OR_HEIGHT -> ENGINE_RIGHT (T-534 s.5,
  B_to_C agreement), POLYGON -> TOLERANCE; SCOPE per key: 5 main riser groups + MS2-TR -> HELD on their candidate HELD
  riser lines (10.28 m2), MS2-LD -> HELD inside the 2F bound L-5d2be30d (3.125); 1F-ARR, E1-LD, RS-S, RS-A -> RULE_DIFFERENCE
  (Q-66 B / Q-50 A answered after the T-086 reference; -14.9319); **MS1-LD 1.500 m2 -> ENGINE_WRONG, fix row T-502**
  (a drawn landing with no candidate line, T-493 F-3 'silent omission'). This last class is this task's proposal: T-534
  wrote it as SCOPE; the Checker confirms or re-classes.
- Checker point (not re-classed): T-534's MS2-U COUNT -0.72 holds two treads; one is the riser onto the landing
  (ENGINE_RIGHT), the other the undrawn 11th going that T-534 keeps HELD beside on its drawing-derived basis (0.345).
  The candidate has no held line for it, so it stays ENGINE_RIGHT here as T-534 classed it.

## 4. Missing / next

T-543 (blockwork), T-545 (beams), T-546 (wet-room WP), T-547 (wall tile): one adapter each when they merge (a table per
row, like T-534's). The stair bed has no freelancer comparison at all (he has no bed rows); the statement says so rather
than show an owner-question figure as a freelancer pair. The SCOREBOARD diagnostic pairs are not rewritten here.

## 5. Lesson row (proposed, ERS s.7)

| 2026-11-06 | each reconciliation used its own sign, its own cause names and its own reference kind (T-534 engine - Q-53 figure; T-541 freelancer - engine) | no common statement schema | R-T548-1: one sign (reference - engine), six classes with the source cause kept beside, totals per trade / unit / reference kind, HELD never agreement, held bound only from engine lines | tests/t548_reconciled_statement | proposed |
