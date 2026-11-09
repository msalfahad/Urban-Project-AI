# T-538 WIRING MANIFEST V3 on ARCH_TAKEOFF_V3.0.58 + gate fix F-C-T536-1

Worker 3 (lane I, non-candidate, integration dependency), 2026-11-05, claim 21:02 UTC, run
session_01E6cPnatUcaa8L5jsRyqtw3, engine base 509deaf7. Not an integration package: nothing is wired, no candidate,
released (V2.9 + route G), rule, knowledge or registry file is touched. Files: `manifest_v3.py` (builder; V2 builder
imported read only), `WIRING_MANIFEST_V3.json`, `tests/t538_wiring_manifest_v3/` (16 tests), and the ONE adverse case in
`tests/t536_wiring_manifest`. Rebuild: `python3 -I research/agents_t538/manifest_v3.py` (`--check`). Every input is a
committed, numbers-only output of a merged piece (sha256 in `inputs`); no drawing is read by V3.

## 1. Gate fix F-C-T536-1

`test_unmerged_ready_piece_refused_as_source` named T-534's live READY commit f97634e0 as 'unmerged'; any merge of T-534
makes it an ancestor and the test red. It now builds a synthetic repository in a temp folder (base commit on a work
branch + one commit on a task branch, the shape of every READY branch) and asserts: base passes, READY commit refused
STALE_SOURCE, a mixed set refused; strength kept (the rc = 1 'not an ancestor' path is now hit, before it was the rc 128
'unknown object' path). Runs: working branch + fix: t536 21 pass, 0 skip (DXF decoded). Trial merge of
agents/task-T-534 (detached, not pushed; CODEMAP conflict resolved by the tool): t536 21 + t534 pass; on that same tree
the old case `check_sources({'T-534': f97634e0})` is NOT refused (failure reproduced).

## 2. V2 -> V3 (sources: T-531 d9051cce, T-532 ba9eba77, T-535 c4a34358, T-536 5953b91f, T-540 509deaf7)

Candidate lines moved V2 -> V3: **0**. Every V2 line move is carried unchanged (V2 pinned sha 305c2cf0).

| piece | candidate line | before | after (proposed for the S package) | status |
|---|---|---|---|---|
| T-531 lintel bars | none carries lintel bars (STR.REBAR searched by opening id / LINTEL: 0) | no line | ADD `STR.REBAR` kg PRODUCED: HELD, AT_LEAST **38.761728 kg** (6 lintels = the 6 BOUNDED V2 lintel lines), straight ceiling 85.080148 beside | DRAWING-CONFIRMED span; ends / bends / laps / links HELD (RFI) |
| | | no line | ADD `STR.REBAR` kg FLAGGED: HELD, AT_LEAST **24.301496 kg** (10 lintels = the 10 HELD_BY_NAME lines), ceiling 69.534578 beside | same |
| T-532 END_CENSUS_V3 | none (12 + 1 ends set-equal to T-526) | 1F-W09 perimeter 0.010355 m3 | 0.010355 (one write) | ties +30 nr / mesh +40.90 (owner) / +44.10 m.l (drawing): NO LINE (T-539) |
| T-535 / T-540 sand | none (sand is a binding-group key) | group AT_LEAST 17.588682 .. 23.290726 m3 | **17.746996 .. 23.449040 m3** (+0.158314) | HELD (194 / 250 open); t and loads HELD (density / load unsourced) |
| T-534 stair bed | 11 released stair marble lines = 35.4313 m2 | V7 area HELD BY NAME | HELD BY NAME now; **AT_LEAST 35.4313 m2 once T-534 merges** (both branches stated in the file) | V7 1.062939 m3 / 10.18 bags / 1.06 m3 sand after F-T518-2 |

Hand checks: PRODUCED 3.90 x 488/162 + 2.45 x 1356/162 + 1.55 x 680/162 = 38.761728; FLAGGED 8.0673 x 488/162 =
24.301496; T-515 -> T-531 -0.098504 kg = 0.0327 m (W18 strip inside C8) x 3.012346; sand +0.158314 = stair 1.06028 x 1.05
- 1.062939 (+0.050355) + perimeter key 0.107959; stair 35.4313 x 0.03 = 1.062939 m3 (V7). Two rebar parts are never
summed into one value while any part is HELD; HELD never 0.

## 3. R-T538-1: no joint head from a sliver (F-C-T532-1), as a check

Physical element: the head of the block course at a block-to-column joint. Rule: a masonry piece shorter than one joint
(j = 0.010 m, the joint the T-520 ledger uses, ASSUMED - OWNER-APPROVED provisional) holds no block unit, so no head of
its own; the head is that of the nearest full masonry piece on the far side from the column (crossing masonry slivers
only), else HELD by name. 130 LISTED junctions (118 interior + 12 end): OWN 73, sliver with the SAME head 53, sliver
with a CHANGED head **4**, HELD 0; the Checker's 5 mm cut classifies identically (0 differ).

| junction | sliver | own (refused) | head by R-T538-1 | quantity effect today |
|---|---|---|---|---|
| GF-W10 end 1 | 0.001695 m | FACE (cls BEAM) | BEAM BM-GF-046 B24, depth 0.75 | none: end HELD (white block, Q-60) |
| GF-W25 end 0 | 0.000713 m | BEAM CB7 0.75 | FACE slab GF-137, t 0.16 | none: end HELD (annex datum Q-54 B) |
| 1F-W04 piece 2/3 | 0.000444 m | FACE STAIR | BEAM BM-1F-006 B2 0.40 | none: white block HELD (Q-60) |
| GF-W01 piece 11/12 (@17.170) | 0.002599 m | NONE (no soffit) | BEAM BM-GF-014 B1 0.40 | **F-T538-3**: T-355 holds this junction 'block top not established' (column 17.170 .. 17.870, block segment 1.30 m to the next column); T-539 re-derives it on the B1 head |

1F-W09 piece 1 (0.000189 m): same member BM-1F-013, head unchanged.

## 4. Findings, verdicts, lessons

- F-T538-1: no candidate STR.REBAR line carries lintel bars: the S package ADDS two HELD AT_LEAST lines, never one total.
- F-T538-2: ties / mesh at the 12 + 1 ends still have no line (T-539).
- F-T538-3: one T-355 sharmat junction (GF-W01 @17.170) is HELD only because its head was read from a 2.6 mm NONE
  sliver; R-T538-1 gives the B1 soffit. For T-539 (no tie count is computed here).
- Engine vs freelancer: no freelancer lintel-bar, tie, mesh or sand row: UNRESOLVED / RULE_DIFFERENCE unchanged.
- Lessons row (proposed, ERS s.7): | 2026-11-05 | a test pinned a live READY commit as 'unmerged', so the merge it was
  guarding turned it red and blocked a PASS piece for 3 Checker runs; a run census sliver (< 1 joint) was read as a
  joint head | test state taken from the board, not built; a plan-stretch piece read as a physical course | adverse
  cases on synthetic repositories / fixtures only; a manifest states a READY dependency in both branches; a piece
  shorter than one joint carries no head (R-T538-1, every villa) | tests/t536_wiring_manifest, tests/t538_wiring_manifest_v3 | proposed |
