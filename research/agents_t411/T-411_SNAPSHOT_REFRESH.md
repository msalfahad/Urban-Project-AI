# T-411: T-374 downgrade snapshot refresh (gate fix F-T328-3)

Worker 1, 2026-11-01. Research / test change only: no engine module, rule, knowledge, registry or candidate line changed.

## 1. The red test and its cause

`tests/t374_straight_bbs::test_snapshot_equals_the_board_verdict_files_when_the_board_is_present` compared
`snapshot_downgrades(board verdicts)` with the committed `research/agents_t374/T374_BOUND_DOWNGRADES.json`. Diff (run on
the task head before any change, board `agents/control` @ 2cc630ee):

| item | committed snapshot | board | cause |
|---|---|---|---|
| records | 20 | 21 | `DG-df07eb3d6ccec0e9` added to `verdicts/V3.0.29/DOWNGRADES.json` by the Verifier 2026-10-31 07:47 (board commit 309e0e2a) |
| V3.0.29 DOWNGRADES.json sha256 | 53a3f5e7cd15.. | 4ed94bf466f3.. | the same addition |
| every other record / verdict set | equal | equal | none |

So the failure is a stale snapshot, not a code defect: one record, nothing else.

## 2. What the record is

`DG-df07eb3d6ccec0e9` (state HELD, resolved false, basis label UNSUPPORTED BASIS, unit kg, candidate ARCH_TAKEOFF_V3.0.29)
was issued on the T-374 r2 proposal DGP-T374-FTGM. It names 10 footing bottom-mesh lines (BOTTOM_LONG + BOTTOM_SHORT,
FOOTING_REBAR_POPULATION_V1) of the five '/m' footings F8, F12, F13, F14, FF: straight runs `side - 2 x 70 mm` (note-22
MINIMUM cover used as the bar-end position, boxed bottom bar of unprinted diameter between bar end and face) and count
readings A .. A + 1 from a bars-per-metre rate (owner Q-71).

Engineering question of the row: does it bind any bar population the schedule emits, and is every scheduled bar still on
a non-downgraded line? Answer: **its 10 line ids are exactly the 10 lines T-374 r2 already booked HELD_SAME_BASIS** (all
10 of 10 are among the 442 schedulable lines; each still satisfies the R-T374-6b basis signature `ftg_mesh_basis`). No
scheduled, bounded-scheduled or run-part line is in it.

## 3. Bar bending schedule before / after (442 lines, refreshed snapshot, `snapshot_downgrades()` only)

| line id | footing / component | before | after | audit kg (low .. high), unchanged |
|---|---|---|---|---|
| L-55a024d5cf6a30603ca6 | F12 BOTTOM_LONG | HELD_SAME_BASIS (DG-a97ec2ea66e02194 basis) | HELD_DOWNGRADE DG-df07eb3d6ccec0e9 | 188.491852 .. 195.223704 |
| L-07225364bf44991b4a0d | F12 BOTTOM_SHORT | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 188.586667 .. 193.422222 |
| L-975f0ab35bd28f84d21e | F13 BOTTOM_LONG | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 124.902716 .. 131.476543 |
| L-ab39f3628f11bf5d54fc | F13 BOTTOM_SHORT | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 121.426173 .. 124.997531 |
| L-fedaa3ad72d10ce9973f | F14 BOTTOM_LONG | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 128.416296 .. 132.844444 |
| L-74ae176a1705ba030c4f | F14 BOTTOM_SHORT | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 126.165926 .. 129.989136 |
| L-9b7c59f231d7eb52805b | F8 BOTTOM_LONG | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 149.443951 .. 154.114074 |
| L-91e7c49c6cbcbe632286 | F8 BOTTOM_SHORT | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 146.516049 .. 150.702222 |
| L-6d2ebc1dec38cb0b95c0 | FF BOTTOM_LONG | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 215.841975 .. 221.238025 |
| L-fdd86d183bdcb7647858 | FF BOTTOM_SHORT | HELD_SAME_BASIS | HELD_DOWNGRADE DG-df07.. | 216.277531 .. 221.552593 |
| | **sum** | | | **1,606.069136 .. 1,655.560494** |

Every other column of every other of the 432 rows: identical (checked column by column).

Scheduled (installed, shape 00) net kg per diameter, SCHEDULED + RUN_PART rows, before = after:

| d (mm) | before kg | after kg | change |
|---|---|---|---|
| 14 | 354.734956 | 354.734956 | 0.000 |
| 16 | 3,159.764378 | 3,159.764378 | 0.000 |
| 18 | 734.955600 | 734.955600 | 0.000 |
| total (population 6 dp figures) | 4,249.454940 | 4,249.454940 | 0.000 kg |

Procurement per diameter (12 m stock, ASSUMED - OWNER-APPROVED OD-V3-3), FFD nesting and the six through-column runs:
unchanged. Reason for 0.000 kg: the 10 lines were never scheduled (R-T374-6b already withheld them); the record only
replaces the schedule's own same-basis inference by the Checker's record, which is the intended direction
(downgrade-only, owner 2026-10-24 23:57 (1)).

FTG-BOT-MESH row states: HELD 3 / HELD_DOWNGRADE 38 / HELD_SAME_BASIS 10 -> HELD 3 / HELD_DOWNGRADE 48 (records
DG-a97ec2ea66e02194 38 lines 874.862227 kg audit, DG-df07eb3d6ccec0e9 10 lines 1,606.069136 .. 1,655.560494 kg audit).
HELD_SAME_BASIS lines: 0. The R-T374-6b code stays: it is the general rule for the next villa.

## 4. Changes

- `research/agents_t374/t374_straight_bbs.py`: `snapshot_downgrades()` also writes `source_record_count` per verdict set
  and `record_count`, and refuses a record whose state is not HELD / CONFLICT (a promotion) by its id;
  `load_snapshot()` refuses the same in a committed snapshot; new `snapshot_drift()` / `check_snapshot()` name each
  differing record id and verdict-set file. No change to schedule logic.
- `T374_BOUND_DOWNGRADES.json`, `T374_STRAIGHT_BBS.csv`, `T374_SUMMARY.json`: regenerated by
  `python -I research/agents_t374/t374_straight_bbs.py --snapshot-from ../board/docs/agents/verdicts --csv ... --json ...`
  (the same command reproduced the previous committed CSV and summary byte for byte with the old snapshot before the change).
- `tests/t374_straight_bbs`: pins moved with the reason stated in the test (38 -> 48 held lines, the 10 lines under their
  own record with the same audit figures, 0 HELD_SAME_BASIS); the board test now calls `check_snapshot` first, so the next
  drift fails naming the record. New tests: snapshot carries shas and counts; a snapshot missing one board record fails
  naming `DG-df07eb3d6ccec0e9`; a changed line list / source file is named; a promoting record refused (board file and
  committed snapshot); hand-built verdict files normal case; the board comparison skips cleanly without the board.
  No test weakened or deleted.

## 5. Not done / for the Checker

- The schedule stays bound to its merged basis (V3.0.16 extract projected to V3.0.27, downgrade sets up to V3.0.29); the
  verdict sets end at V3.0.29, so no later set exists to bind. Re-binding the BBS to V3.0.34 is not in this row.
- Observation F-T411-1 (no change made): `DG-df07eb3d6ccec0e9` stores `engine_qty 0.0` while its lines carry a BOUNDED
  1,606.069136 .. 1,655.560494 kg (stated in its reason text); the schedule takes the audit figures from the candidate
  lines, never from `engine_qty`, so nothing here depends on it.
- Lesson (ERS s.7) proposed: a committed snapshot of board records is a dated copy; it must carry its source shas and
  counts and its comparison must name the drifting record, so a new Checker record turns into a named refresh task, not
  an anonymous red test carried for days.
