# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log c906b76d..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 16:15Z 4 Nov, rows changed since), then rewrite.

## Last seen
- engine: c906b76d (T-468 merge; T-480 1b66b719 -> candidate of record ARCH_TAKEOFF_V3.0.54 c85c4630; registry
  BOQ_FAMILY_MASTER 1.51.0; released V2.9 + route G unchanged).
- board: this run's final commit (Lead 2026-11-04 16:17, after d2339eaa)
- last Lead run: 2026-11-04 16:15-16:35 UTC (run session_01E6cPncjTwPsaWxVPdmkwgK)

## Run health
- Since 12:19 every run closed with a final line. OPEN at 16:17: Worker 3 STARTED 15:02 (T-488 CLAIMED 15:02, lock to
  about 17:02, scheduler PENDING). If it has no final line by the next Lead run -> UNCLOSED / INCOMPLETE; check the
  T-488 branch for pushed stages before setting it back to TODO.
- No usage-limit failure since 11:14.

## Live rows
- READY 1: T-500 (worker 2, 14:52, Gate A, CHECKER-RUNS). CLAIMED 1: T-488 (worker 3, 15:02).
- TODO 3: W1 T-508, T-510; W2 T-310 r6.
- QUEUED: W1 T-423, T-424, T-364, T-363, T-372; W2 T-507, T-314, T-502; W3 T-498, T-511 (after T-500 MERGED), T-509,
  T-382, T-474 p2.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-508, T-510, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-310, T-507, T-500, T-314, T-502 | I (worker 3): T-488, T-498, T-511, T-509, T-382, T-474
- TODO below 8 by design: one candidate package per worker; no other unblocked row moves a line.

## Top 5 priorities
1. Stream S: T-488 blockwork wiring (worker 3, now) -> T-498 materials -> T-509 disposal.
2. Stream F: T-310 r6 (worker 2) and T-508 (worker 1) in parallel on V3.0.54, READY second rebases; whichever merges
   first promotes T-480's pending V3.0.54 in the master (F-C-T468-1); then T-507.
3. Checker: T-488 (Gate B), T-500 (Gate A, at most 2 runs' delay), T-310 r6 / T-508, T-510; T-180 rest of every run.
4. 10 Nov: about 13 packages / 6 days; 4 Gate B merges since 00:20. Review again at 20:15.
5. If T-488 dies unclosed, recover from its pushed stages; never restart from zero.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One candidate package per worker at a time.
  Two stream F packages of different workers on the same hub / master are NOT a file conflict (READY second rebases).
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package (W1 T-510, W2 T-500
  READY, W3 T-511 QUEUED).
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats 'after T-nnn' / list position as WAITING; status word first; 9-field rows; history text in a
  status cell must not say 'after T-nnn' for a met wait (write 'behind ... (history, met)').
- `board check` pulls first: commit the edits before running it. Write stamps from `date -u`.
- Owner questions on non-critical material parameters are withdrawn into level-4 estimate tasks unless every source
  was read in full (Q-79 -> T-489, 2026-11-03 12:18).
- F-C-T443-1: a package is 'merged' only when its commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Element register rulings: RC LINTEL vs host masonry; FOUNDATION BACKFILL; TOP-STOREY WALL HEIGHT vs ROOF BUILD-UP;
  ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP (B8-06); STAIR SKIRTING vs ROOM SKIRTING;
  EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY (2.800 lm HELD JOINERY_SCOPE_NOT_PRINTED, T-460); STAIR GUARDRAIL vs
  SLAB-EDGE BALUSTRADE (16:17).
- Lessons rows 2026-11-04 ADOPTED: trench zone overlap, HELD subtotal R-T499-1, disposal balance, skirting under raised
  sills, one producer per material key, skirting only on a floor, WP applicability; 16:17: stair rail by floor + flight +
  treads (T-480), gap by bounding elements (T-460, rule pending T-510).
- Materials wiring reads FINISH_MATERIALS_TABLE_V5 bound_subtotal() and PLASTER_MATERIALS_TABLE_V3; producer roles from
  T-506; disposal loss never inside payable (F-C-T505-1); F-C-T487-1 lintel bars HELD on B9-02 (in T-488).

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
