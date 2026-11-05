# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 94b2e502..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 00:12Z 5 Nov, rows changed since), then rewrite.

## Last seen
- engine: 94b2e502 (T-511 merge; candidate of record ARCH_TAKEOFF_V3.0.57 25a8b406; BOQ_FAMILY_MASTER 1.54.0;
  released V2.9 + route G unchanged). t212 green; t485 red pre-existing (T-310 pending in newest registry) until the
  next master promotes it.
- board: this run's final commit (Lead 2026-11-05 00:15)
- last Lead run: 2026-11-05 00:12-00:30 UTC (run session_01E6cPncpdVtQy6dWYTp4s7p)

## Run health
- Since 20:12 every run closed with a final line; OPEN at 00:15 inside their locks: W3 23:00 (T-498, lock to 02:00),
  W1 23:20 (T-423, lock to 01:20). If either has no final line by the next run: UNCLOSED -> INCOMPLETE, check the
  task branch before anyone takes it over.
- 0 empty runs since the 20:15 fix. W2 bypassed the run wrapper with venv python for a research script (NEEDS FIXING).
- Recurring: venv install cut off at session start (first selfcheck 'No module named pytest'), setup re-run fixes it.

## Live rows (00:15)
- READY 0. CLAIMED 2: T-498 (W3, resume of 4821c0cc; renumbers from V3.0.57 to the next free), T-423 (W1).
- TODO 3: W2 T-507 (first), T-514; W1 T-515 (second). T-514 / T-515 open to any idle worker.
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474 p2.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-423, T-515, T-424, T-364, T-363, T-372 |
  A (worker 2): T-507, T-514, T-513, T-314, T-502 | I (worker 3): T-498, T-509, T-382, T-474

## Top 5 priorities
1. Three candidate packages in parallel on V3.0.57: T-498 (S), T-423 (F), T-507 (F); READY second rebases.
2. Checker: T-498 first on a tie, then T-423 / T-507 in READY order; T-515 / T-514 Gate A within 2 runs.
3. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423;
   T-513 after T-507). Each worker keeps a non-candidate TODO behind its package (W3 needs one after T-498).
4. 10 Nov: 7 Gate B since 00:20 4 Nov, about 10 left in 5.0 days: AT RISK. Next review 04:15.
5. Code_totals 0.0 path (37 codes) closed inside T-507; STAIR_BED_V1 wiring still unrowed (later stream F package).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and master) allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least one non-candidate TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line.
- Queue check treats 'after T-nnn' / 'waits for T-nnn' / list position as WAITING; status word first; 9-field rows;
  history text must say 'behind ... (history, met)' for a met wait. `board check` pulls first: commit before it.
- Owner questions on non-critical material parameters become level-4 estimate tasks unless every source was read.
- F-C-T443-1: 'merged' only when the commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Research scripts run through pytest or the wrapper only (never a bare venv python) until the owner widens `run`.
- Element register rulings: RC LINTEL vs host masonry + LINTEL REINFORCEMENT (00:15); FOUNDATION BACKFILL; TOP-STOREY
  WALL HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP; STAIR SKIRTING vs
  ROOM SKIRTING; EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY; STAIR GUARDRAIL vs SLAB-EDGE BALUSTRADE; BAND-PATH
  PIER FACE.
- Lessons 2026-11-04: ADOPTED trench overlap, R-T499-1, disposal balance, skirting under sills, one producer per key,
  skirting only on a floor, WP applicability, stair rail by flight, gap by bounding elements, held top datum (T-488),
  guard class in the same package (F-C-T510-3, confirmed by T-512 Gate A).
- Materials: FINISH_MATERIALS_TABLE_V5 bound_subtotal(), PLASTER_MATERIALS_TABLE_V3; producer roles T-506; cement /
  sand census T-511 (one producer per key); disposal loss never inside payable; lintel bars -> T-515.

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list for research scripts (new); venv install cut off at session start (recurring).
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
