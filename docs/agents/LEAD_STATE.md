# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 40ab9061..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 20:12Z 4 Nov, rows changed since), then rewrite.

## Last seen
- engine: 40ab9061 (T-508 merge; candidate of record ARCH_TAKEOFF_V3.0.56 4e25c54f; BOQ_FAMILY_MASTER 1.53.0;
  released V2.9 + route G unchanged). tests/t212 RED on 40ab9061 (F-C-T510-3) -> T-512.
- board: this run's final commit (Lead 2026-11-04 20:15, after d4d03d35)
- last Lead run: 2026-11-04 20:12-20:30 UTC (run session_01E6cPndjcEi9xuR2kCSjWn)

## Run health
- Since 16:15 every run closed with a final line. 3 EMPTY worker runs (W2 18:41, W3 19:00, W1 19:19: 0 TODO).
  Cause: the 16:17 plan left every next row QUEUED behind a READY/CLAIMED package. Rule now: each worker has a
  second TODO (non-candidate) behind its candidate package; promote QUEUED rows the moment their wait is met.
- No usage-limit failure since 11:14.

## Live rows (20:15)
- READY 0. CLAIMED 0.
- TODO 5: W1 T-512 (gate 0), T-423; W2 T-310 r7; W3 T-498, T-511 (any idle worker).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-507, T-513, T-314, T-502; W3 T-509, T-382, T-474 p2.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-512, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-310, T-507, T-513, T-314, T-502 | I (worker 3): T-498, T-511, T-509, T-382, T-474

## Top 5 priorities
1. T-512 gate fix (t212) first: every L4 carries the failure until it merges.
2. Three candidate packages in parallel on V3.0.56: T-498 (S), T-310 r7 (F), T-423 (F); READY second rebases.
3. Checker: T-512 (Gate A, max 2 runs' delay), then Gate B in READY order, T-511, T-180 rest of every run.
4. 10 Nov: 6 Gate B since 00:20, about 11 left in 5.2 days: AT RISK. Next review 00:15.
5. When a package merges, promote its queued successor in the same Lead run (T-507 after T-310; T-509 after T-498;
   T-424 after T-423; T-513 after T-507 + T-512).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and master) allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least one non-candidate TODO behind its stream package (W1 T-512, W3 T-511).
- A worker run that skips its first-in-order stream package must state why in its final line.
- Queue check treats 'after T-nnn' / 'waits for T-nnn' / list position as WAITING; status word first; 9-field rows;
  history text must say 'behind ... (history, met)' for a met wait. `board check` pulls first: commit before it.
- Owner questions on non-critical material parameters become level-4 estimate tasks unless every source was read.
- F-C-T443-1: 'merged' only when the commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Element register rulings: RC LINTEL vs host masonry; FOUNDATION BACKFILL; TOP-STOREY WALL HEIGHT vs ROOF BUILD-UP;
  ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP; STAIR SKIRTING vs ROOM SKIRTING (updated
  20:15, F-C-T508-2); EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY; STAIR GUARDRAIL vs SLAB-EDGE BALUSTRADE;
  BAND-PATH PIER FACE (20:15).
- Lessons 2026-11-04: ADOPTED trench overlap, R-T499-1, disposal balance, skirting under sills, one producer per key,
  skirting only on a floor, WP applicability, stair rail by flight, gap by bounding elements, held top datum (T-488).
  PROPOSED: new engine module declares its guard class in the same package (F-C-T510-3; confirm at T-512 Gate A).
- Materials: FINISH_MATERIALS_TABLE_V5 bound_subtotal(), PLASTER_MATERIALS_TABLE_V3; producer roles T-506; disposal
  loss never inside payable; F-C-T487-1 lintel bars HELD on B9-02; T-498 recomputes from the V3.0.55 MAS.BLOCK base.

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
