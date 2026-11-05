# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 7f7b7564..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 08:13Z 5 Nov, rows changed since), then rewrite.

## Last seen
- engine: 7f7b7564 (T-516 / T-517 / T-518 merges; candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / BOQ_FAMILY_MASTER
  1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-05 08:15)
- last Lead run: 2026-11-05 08:13-08:35 UTC (run session_01E6cPncEtjJ2XrPHVaX4o4T)

## Run health
- Since 04:12 every run closed with a final line; no UNCLOSED run.
- 3 EMPTY worker runs (W2 06:44, W3 07:01, W1 07:20): Lead fault, 0 TODO after the 06:09 merges. Rule now: leave at
  least 2 TODO per lane that need no candidate wiring while the wrapper item is open.
- CRITICAL (owner, notified 04:15, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B blocked.
- Recurring: venv install cut off at session start (selfcheck 'No module named pytest'); setup re-run fixes it.

## Live rows (08:15)
- READY 0. CLAIMED 0. TODO 6 (all Gate A, research/module + tests, no candidate wiring):
  S: T-519 lintel pieces + LINTEL_BEARING_V2, T-520 perimeter joint mortar (F-T367-1)
  A: T-521 FINISH_MATERIALS_TABLE_V6 (engine/source, new file), T-522 pool-court ledge / window-run WP
  I: T-523 material binding V2 + purchasing-group ceiling, T-524 lintel concrete at deficit ends
- BLOCKED (wrapper): T-498 (W3, staged e3e2ebb5 = V3.0.59 on V3.0.58; resume must take T-523 / T-520 results if merged),
  T-423 r2 (W1: 3 fixes + renumber).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-519, T-520, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-521, T-522, T-513,
  T-314, T-502; I (worker 3): T-523, T-524, T-498, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (W3) and T-423 r2 (W1) FIRST; T-513 (W2).
2. Checker: Gate A T-519..T-524 in READY order, each within 2 runs.
3. Next Lead run: if 2 or fewer TODO remain in a lane, add non-candidate rows (candidates: STAIR_BED_V1 binding prep;
   FINISH V6 wiring prep list; exterior plaster parapet / plinth owner trade (L-N10-02); T-474 part 2 scope split).
4. 10 Nov: HIGH RISK (about 10 Gate B left in 4.7 days, all blocked by the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell; 'after T-nnn' = WAITING; 9-field rows; `board check` pulls first: commit before.
- Lane order note: no T- ids in the sentence right after the lane order (the parser runs on).
- Owner questions on non-critical material parameters become level-4 estimate tasks unless every source was read.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Research scripts only through committed package tests or the wrapper (never bare venv python, never a throwaway runner).
- Register rulings: RC LINTEL vs host masonry + LINTEL REINFORCEMENT; FOUNDATION BACKFILL; TOP-STOREY WALL HEIGHT vs
  ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP; STAIR SKIRTING vs ROOM SKIRTING;
  EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY; STAIR GUARDRAIL vs SLAB-EDGE BALUSTRADE; BAND-PATH PIER FACE.
  Pending (T-524): owner trade of lintel end volume inside a column.
- Lessons 05 Nov in register: printed minimum never a measured value (ADOPTED); loss factor its own account in every
  producer and binding (PROPOSED).
- Materials: FINISH_MATERIALS_TABLE_V5 (-> V6 by T-521), PLASTER_MATERIALS_TABLE_V3; Q-45 5 % ASSUMED - OWNER-APPROVED
  (2026-10-20 12:15) as its own account; disposal loss never inside payable.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh line 211). Designer items (D-27, D-33, D-35, D-39, D-43, lintel
  deficit ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15); venv install cut off at session start (recurring).
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
