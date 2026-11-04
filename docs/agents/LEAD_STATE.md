# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log ea7d375f..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 08:13Z 4 Nov, rows changed since), then rewrite.

## Last seen
- engine: ea7d375f (T-483 merge; candidate of record ARCH_TAKEOFF_V3.0.51 c0b6d664; registry BOQ_FAMILY_MASTER
  1.48.0; released V2.9 + route G unchanged). t485 green again.
- board: this run's final commit (Lead 2026-11-04 08:20, after 465a04b2)
- last Lead run: 2026-11-04 08:12-08:25 UTC (run unknown)

## Run health
- Every run since 04:14 closed with a final line. OPEN at 08:15: Worker 3 STARTED 07:00 (T-487 CLAIMED 07:01, lock to
  10:00): if it has no final line by the next run, report INCOMPLETE and check agents/task-T-487 for pushed work.
- Checker 07:50 stopped on the overlap guard (06:50 run still on T-483): T-494 has missed 1 Checker run.

## Live rows
- READY 3: T-494 (06:54, Gate A), T-505 (07:28, Gate A), T-310 r3 (MUST REBASE -> r4 rework, worker 2 first).
- CLAIMED 1: T-487 (worker 3, 07:01).
- TODO 6: W1 T-501, T-480; W2 T-500, T-460; W3 T-506, T-468 (+ T-310 r4 rework).
- QUEUED: W1 T-423, T-424, T-364, T-363, T-372; W2 T-314, T-502; W3 T-488, T-498 (after T-488 + T-506), T-382, T-474 p2.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-501, T-480, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-310, T-500, T-460, T-314, T-502 | I (worker 3): T-487, T-506, T-468, T-488, T-498, T-382, T-474
- TODO below 8 by design: one candidate package per worker; no other unblocked row moves a line.

## Top 5 priorities
1. 12:00 REVIEW (next run): Gate B merges since 00:20 = 2 (T-497, T-483). If still fewer than 3 at 12:00, propose the
   owner a scope order for 10 Nov (which trades go in as HELD lines), section 6 format, max 5 items.
2. Stream F: T-310 r4 rebase (worker 2, 08:39) then T-480 handrails (worker 1); whichever READY second rebases.
3. Stream S: T-487 lintels (CLAIMED) -> T-488 blockwork wiring -> T-498 materials (after T-506).
4. Checker: T-494 at 09:49 at the latest, then T-505, T-310 r4, T-487; T-180 rest of every run.
5. After T-494 MERGES: open the B8-06 wiring row (stream F, next free T-, worker 2 after T-310) for 4.907 m2 + upturn.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats 'after T-nnn' / list position as WAITING; status word first; 9-field rows.
- `board check` pulls first: commit the edits before running it. Write stamps from `date -u`.
- Owner questions on non-critical material parameters are withdrawn into level-4 estimate tasks unless every source
  was read in full (Q-79 -> T-489, 2026-11-03 12:18).
- F-C-T443-1: a package is 'merged' only when its commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Element register rulings: RC LINTEL vs host masonry; FOUNDATION BACKFILL; TOP-STOREY WALL HEIGHT vs ROOF BUILD-UP;
  ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP (B8-06); STAIR SKIRTING vs ROOM SKIRTING;
  EXCAVATION ZONES; 2026-11-04 08:15 SKIRTING BEHIND FITTED JOINERY (T-460 classifies the 2.800 lm).
- Lessons rows 2026-11-04 ADOPTED: trench zone overlap, HELD subtotal R-T499-1 (covers R-T504-1), disposal balance,
  skirting under raised sills + partial vs whole range close (T-483).
- Materials wiring reads FINISH_MATERIALS_TABLE_V5 bound_subtotal() and PLASTER_MATERIALS_TABLE_V3; producer roles and
  the mortar ledger choice come from T-506; disposal reuse ends need T-505 loss terms.

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
