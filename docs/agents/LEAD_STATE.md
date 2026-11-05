# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log ee91e8b9..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 04:12Z 5 Nov, rows changed since), then rewrite.

## Last seen
- engine: ee91e8b9 (T-514 merge; candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / BOQ_FAMILY_MASTER 1.55.0;
  released V2.9 + route G unchanged). t485 cleared by 1.55.0.
- board: this run's final commit (Lead 2026-11-05 04:15)
- last Lead run: 2026-11-05 04:12-04:30 UTC (run session_01E6cPne2GFfJiH4vuFGZfGa)

## Run health
- Since 00:15 every run closed with a final line; no UNCLOSED run. 1 empty worker run (W1 03:21): T-423 status cell
  began with REJECTED, so it was not read as TODO (corrected; status word first, always).
- CRITICAL: the run wrapper refuses research/agents_t*/ scripts; W3 03:07 temporary pytest runner refused by the
  classifier ('[Auto-Mode Bypass]'). Every Gate B package needs those scripts; the Checker cannot reproduce chains.
  Owner notified 04:15 (NEEDS FIXING). Never bypass (no bare venv python, no throwaway runners).
- Recurring: venv install cut off at session start (selfcheck 'No module named pytest'), setup re-run fixes it.

## Live rows (04:15)
- READY 0. CLAIMED 0. TODO 3: T-516 (W1 first), T-517 (W2 first), T-518 (W3) - all Gate A, research + tests only.
- BLOCKED (wrapper allow-list): T-498 (W3, staged e3e2ebb5 = V3.0.59 on V3.0.58), T-423 r2 (W1: 3 fixes + renumber).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513 (after T-517 + wrapper), T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-516, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-517, T-513, T-314, T-502 | I (worker 3): T-518, T-498, T-509, T-382, T-474

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (W3) and T-423 r2 (W1) FIRST; T-513 (W2) after T-517.
2. Checker: Gate A T-516 / T-517 / T-518 in READY order (each within 2 runs); then T-498 Gate B, then T-423 r2.
3. Board is thin (3 TODO): next run add 1 non-candidate TODO per lane if the wrapper is still blocked (candidates:
   STAIR_BED_V1 producer binding prep, F-T514-1 display rounding, lintel precast-length check after T-516).
4. 10 Nov: HIGH RISK (8 Gate B since 00:20 4 Nov, about 10 left, all blocked by the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least one non-candidate TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line.
- Queue check: status word FIRST in the status cell ('BLOCKED (...)', 'TODO r2 (...)'), never 'REJECTED r1 -> TODO';
  'after T-nnn' = WAITING; 9-field rows; 'behind ... (history, met)'. `board check` pulls first: commit before it.
- Owner questions on non-critical material parameters become level-4 estimate tasks unless every source was read.
- F-C-T443-1: 'merged' only when the commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Research scripts only through committed package tests or the wrapper (never bare venv python, never a throwaway runner).
- Element register rulings: RC LINTEL vs host masonry + LINTEL REINFORCEMENT; FOUNDATION BACKFILL; TOP-STOREY WALL
  HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP; STAIR SKIRTING vs ROOM
  SKIRTING; EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY; STAIR GUARDRAIL vs SLAB-EDGE BALUSTRADE; BAND-PATH PIER FACE.
- Lessons 2026-11-04/05: trench overlap, R-T499-1, disposal balance, skirting under sills, one producer per key, skirting
  only on a floor, WP applicability, stair rail by flight, gap by bounding elements, held top datum, guard class in the
  same package; PROPOSED 05 Nov: a printed minimum is never a measured value (F-C-T515-1); waste never inside installed.
- Materials: FINISH_MATERIALS_TABLE_V5, PLASTER_MATERIALS_TABLE_V3; producers T-506 / T-511 / T-514; disposal loss
  never inside payable; lintel bars T-515 (span AT_LEAST), bearings T-516.

## Blockers
- Wrapper allow-list (owner, main branch scripts/agent_env.sh line 211). Designer items (D-27, D-33, D-35, D-39, D-43)
  keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15); venv install cut off at session start (recurring).
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
