# T-723 WIRING READINESS ROUND 4 on ARCH_TAKEOFF_V3.0.71 (worker 3, lane I, 2026-11-11; research only)

No quantity is produced, changed or wired. Candidate of record ARCH_TAKEOFF_V3.0.71 (T-704 r2 Gate B PASS, merge
b211b3a2; `research/agents_t704/out/LINE_INDEX_V3_0_71.json`); released default V2.9 + route G untouched. Rule R-T723-1
1.0.0 (`t723_rules.py`, every villa) on top of R-T705-1 1.0.0 and R-T698-1 1.1.0 (applied unchanged); application
`t723_alsenan.py` (`--check` rebuilds and compares); outputs `out/T723_READINESS.json` (rows, classes, actions, live
state, hub order with line ids, concrete census) and `out/T723_ROWS.csv` (one row per ledger row). Inputs: merged
repository files only, sha256-pinned, plus `in/T703_PENDING.json`, the pinned extract of the READY T-703 package
(`t723_extract_t703.py`, commit af54dee2, doc blob 4de5fedd: 18 ONE_SIDED + 10 BOUND_ROUNDING lines, reconciled with its
own V3_0_72 index difference). No drawing opened. ERS read: s.2.1 (element first: one live statement per line), s.2.4
(reconcile by id and unit), s.3 (notation before arithmetic: a one-sided figure is not a range), s.7 (lesson below).

## R-T723-1 (summary; full text in the module)

(1) ONE_SIDED after-state (AT_LEAST / AT_MOST / CONDITIONAL on a payable form): BESIDE a HELD line, never in it, never a
range, never 0; KEEP when the same figure is already beside, RESTATE_BESIDE when another is, FORM_CONFLICT on a line with
a value or a two-ended range. (2) BLANK-with-cause on a blank line = TEXT (record text only; Gate B still lists it); on a
line with a number = CHANGE. (3) EXCLUDED (not an element of the family): no number, never 0. (4) One live row per line:
equal statements -> DUPLICATE; different -> SUPERSEDED only when the later ledger declares it, else CONFLICT (build
fails); a NO_PROPOSAL row is a STATEMENT. (5) One line per row (a row mapped to two lines fails). (6) A previous map
restated on a new candidate: host absent STALE, index entry or beside record changed HOST_CHANGED, a READY package's
line PENDING. (7) RULING_RESTATE flag when the register reading under a row was replaced. (8) Package size = changed
(CHANGE / BESIDE / RESTATE_BESIDE) + text-only + added, LIVE rows only.

The beside register (figures already beside V3.0.70 / V3.0.71 lines) is rebuilt from the merged concrete Gate B input
builders, rounds 1 .. 8 (T-661 .. T-704, replayed in order; a later range or value clears a figure): 24 lines on V3.0.70,
40 on V3.0.71 (the 16 T-704 lintel AT_MOST). Non-concrete beside records and V3.0.23 parapet / V3.0.46 lift figures are
outside it: those rows carry CONFIRM_ON_LIVE.

## (1) T-705 map restated on V3.0.71 (287 rows; stale 0)

The V3.0.71 index lines equal V3.0.70's (asserted; T-704 moved beside records only). Classes unchanged: MAPPED 191,
HOST_CHANGED 20 (hosts moved since the T-697 ledger, kept), PENDING 49 (H1 / T-314 r3 still unwired), NO_HOST 26,
AMBIGUOUS 1. Actions: 17 KEEP -> TEXT (blank-on-blank rows: earthworks / roof layers, rule 2), others unchanged.
**All 116 B4-09 bead ADD rows carry RULING_RESTATE**: the Lead ruling 2026-11-11 16:25 (CORNER BEAD HEIGHT STATE, the
answer to F-T705-1) makes a bead on a HELD host HELD with its host's bound, so the T-697 G1 lengths (285.03 / 310.6831
m.l) cannot be wired as stated: H2a / H2b need a restated bead ledger first. T-701 GF-01 carries RESTATE_FIRST F-T709-1
(47.949844 .. 66.249856 m2, quoted).

## (2) Pieces merged since T-705 (346 rows; stale 0)

| piece (merge) | rows | classes | actions | live | hub |
|---|---|---|---|---|---|
| T-707 column tail (f34a5baa) | 20 | MAPPED 20 | CHANGE 18, BESIDE 2 | 20 | T-722 (7), T-714 (13 formwork) |
| T-711 concrete blank tail (1e06f656) | 15 | MAPPED 15 | BESIDE 6, KEEP 5, TEXT 4 | 15 | T-722 |
| T-712 ground beams (dfeb0240) | 20 | MAPPED 20 | KEEP 13, RESTATE_BESIDE 3, BESIDE 1, TEXT 3 | 20 | T-722 |
| T-721 beams blank (9e1ed6c5) | 12 | MAPPED 12 | TEXT 11, BESIDE 1 | 12 | T-722 |
| T-709 plaster / paint (fe461c6e) | 34 | MAPPED 32, NO_HOST 2 | ADD 32, NONE 2 | 32 | T-717 |
| T-710 WP round 3 (4a34ced0) | 58 | MAPPED 53, NO_HOST 5 | CHANGE 21, KEEP 32, ADD 5 | 4 (22 DUPLICATE of T-691, 32 STATEMENT) | H4 |
| T-713 masonry rest (aa4d8979) | 95 | MAPPED 67, PENDING 28 | KEEP 67, NONE 28 | wired by T-703 | T-703 |
| T-715 stair finishes (a4e4277a) | 86 | MAPPED 85, NO_HOST 1 | CHANGE 39, BESIDE 42, TEXT 3, KEEP 1, ADD 1 | 81 (4 SUPERSEDED) | H3s |
| T-718 stair finishes r2 (8052ca51) | 6 | MAPPED 6 | CHANGE 4, BESIDE 2 | 4 (2 DUPLICATE) | H3s |

T-706 (slab statement: the drawing settles the engine quantity) and T-716 (designer census) carry no line target.

## (3) Hub packages (owner order 2026-11-09 concrete first; 2026-11-11 (2a) join verified work first)

| # | package | rows | changed | text-only | added | state |
|---|---|---|---|---|---|---|
| 1 | T-703 masonry r4 (READY, V3.0.72) | 95 | 0 | 0 | 0 | the 28 T-713 lines are T-703's own (18 one-sided + 10 rounding) |
| 2 | T-722 concrete r9 (reserves V3.0.73) | 54 | 18 | 18 | 0 | buildable; T-721 is not in the row's list (merged 22:05): add it or round 10 |
| 3 | T-714 formwork | 13 | 13 | 0 | 0 | after T-722 (each follows its column line) |
| 4 | T-717 plaster / paint H1 (V3.0.74) | 36 | 4 | 0 | 32 | 2 band ADDs wait on T-719 VOIDS + the T-147 region check |
| 5 / 6 | H2a / H2b beads | 134 / 51 | 0 | 0 | 14 / 4 | BLOCKED: RULING_RESTATE (116 rows); H2b also T-314 r3 |
| 7 | H3 tiles GF-10 / GF-11 | 2 | 2 | 0 | 0 | buildable |
| 8 | H3s stair finishes | 92 | 81 | 3 | 1 | buildable; 27 CONDITIONAL form figures (ORR-007), 20 EXCLUDED |
| 9 | H4 WP + roof build-up | 99 | 26 | 10 | 5 | buildable; T-705 F-T705-2 form decision stands |
| 10 | H5 earthworks | 41 | 8 | 7 | 1 | unchanged; T-708 round 3 TODO |

Concrete census, index-based (m3; beside figures never summed into released or a range; run-record only):

| code | V3.0.71 released / bounded / blank / excluded | bounded low .. high | beside V3.0.71 -> after T-722 |
|---|---|---|---|
| COLUMN | 30 / 27 / 2 / 13 | 11.67283 .. 15.5015 -> **11.80007** .. 15.5015 | none -> AT_LEAST 2 lines 0.6574 |
| GROUND_BEAM | 32 / 9 / 20 / 0 | 1.178378 .. 5.096771 | AT_LEAST 16 lines 5.092339 -> 17 lines **5.099845** |
| BEAM | 112 / 14 / 12 / 54 | 5.983229 .. 8.41271 | none -> AT_LEAST 1 line 0.115155 |
| NECK | 0 / 32 / 4 / 0 | 8.7724 .. 11.346 | AT_LEAST 4 lines 0.9515 (unchanged: T-711 = V3.0.63) |
| STAIR | 6 / 0 / 5 / 1 | - | 0.355017 -> 2 lines 1.568446 |
| PARAPET / LIFT | 0 / 0 / 4 / 0 and 0 / 0 / 2 / 0 | - | -> 8.050942 (4) / 1.903 (1), CONFIRM_ON_LIVE |

Released m3 moves on no code (asserted). The COLUMN low +0.12724 equals T-707's plate transfer; GROUND_BEAM 5.099845
equals T-712's family figure; BEAM / COLUMN equal the T-704 run's code totals.

## Findings for the Lead / Checker

- **F-T723-1 (T-712 restates three V3.0.63 figures).** L-e16c9807 0.135473 -> 0.135481 (+8e-6: re-measured area),
  L-0bb78acc 0.242309 -> 0.242308 and L-d53e5eb0 0.147657 -> 0.147656 (-1e-6: R-T696-1 floors an AT_LEAST). T-722 must
  RESTATE these beside figures, not add a second one; 13 other T-712 lines and 5 T-711 lines are already beside (KEEP).
- **F-T723-2 (bead hub blocked).** All 116 B4-09 ADD rows need a bead ledger restated under ruling 16:25 before H2a / H2b;
  no package can wire T-697 as merged. Proposed: a lane A row (bead lm per host height state, HELD with host bound).
- **F-T723-3 (census convention).** GROUND_BEAM L-fb7a6431 (boundary G.B at N.G.) carries 0 .. 3.5256 in the index but
  the code totals count it blocked (no bounded_range on the BOQ line): T-712's '9 bounded 1.178378 .. 5.096771' and the
  T-704 summary's '8 bounded .. 1.571171' differ by exactly this line. Gate B states which form the line carries.
- **F-T723-4 (T-709 band host).** Host decided: the GF-08 lines (plaster L-8cecb1d0, paint L-c0ac22c9): the band
  +5.29 / +4.65 .. +5.50 continues GF wall face 336 over its solid 3.997 m; 1F-13 starts at its own floor +5.50, so
  hosting it there would start a 1F face below its floor. Wiring waits on T-719 (void named) and the T-147 region check.
- **F-T723-5 (missing WP transition m2).** T-710 lists MISSING FIN.WP.DOORWAY_TRANSITION m2 (pantry, DESIGNER): T-691
  added the pcs line only; H4 adds it HELD blank (missing is never dropped) or states why not.

Lessons row (ERS s.7, proposed): 2026-11-11 | a readiness map restated after one-sided figures were wired beside lines |
a line index carries class / value / range only, so a figure beside a blank line is invisible to a map built on the
index; ledgers restating a figure already beside looked like new wiring | rebuild the beside register from the merged
package builders, compare each one-sided proposal against it (KEEP / RESTATE / BESIDE), and keep one live statement per
line across pieces | tests/t723_wiring_readiness_r4 | PROPOSED.

Tests: tests/t723_wiring_readiness_r4 (35): synthetic villa W723 by hand (one-sided beside / keep / restate / form
conflict, adverse 0 / negative / range / unknown side; text vs downgrade; excluded never 0; duplicate, declared
supersession, statement, mirror order, undeclared conflict refused; a row mapped to two lines refused; restate classes
incl. stale and a non-state field; package size) and the development villa (rebuild equal, pins, stale 0, every ledger row
once, T-705 287 rows restated, beside register 24 / 40, concrete facts, census vs T-704 and the ledgers, supersession,
WP duplicates, T-703 pending set, blocked hubs, held never 0, adverse row-twice and conflict on real rows).
