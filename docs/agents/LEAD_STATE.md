# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log f05abdd6..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 16:16Z 5 Nov, rows changed since), then rewrite.

## Last seen
- engine: f05abdd6 (T-527 / T-529 / T-530 merges; candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / BOQ_FAMILY_MASTER
  1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-05 16:30)
- last Lead run: 2026-11-05 16:16-16:40 UTC (run unknown)

## Run health
- Since 12:18 every run closed with a final line; 0 empty runs; 5 merged, 0 rejected, T-525 BLOCKED (wrapper, correct stop).
- CRITICAL (owner, notified 04:15, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).

## Live rows (16:30)
- READY 0. CLAIMED 0. TODO 7 (Gate A, research + tests via pytest, none needs the wrapper):
  S: T-531 lintel bars on PRODUCED lintels (V3 bearings now), T-532 END_CENSUS_V3 (F-C-T526-1), T-533 0.15 m block module
  A: T-534 stair bed area 39.49 vs 35.4313 (F-C-T528-1), T-535 sand purchase unit
  I: T-536 WIRING MANIFEST V2 (F-C-T530-1, F-C-T529-1, F-T530-4, T-526..T-528), T-537 R-T498-2 ranged host face (RG-1)
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-531, T-532, T-533, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-534, T-535, T-513,
  T-314, T-502; I (worker 3): T-536, T-537, T-525, T-498, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-513; wire from T-536.
2. Gate A T-531..T-537 merged in READY order; structural first.
3. Next Lead run: if 1 or fewer TODO remain in a lane, add non-candidate rows (candidates: exterior plaster parapet / plinth
   owner trade (L-N10-02); T-474 part 2 scope split; F-C-T526-2 wording only; stream F package prep from T-536).
4. 10 Nov: LOW (about 10 Gate B left in 4.5 days, none can start before the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked; no 'after T-nnn'
  on second / third rows unless truly dependent (WAITING rows caused empty runs).
- Status word FIRST in the status cell; 9-field rows; `board check` pulls first: commit before.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- Research scripts only through committed package tests or the wrapper (never bare venv python, never a throwaway runner).
- Register rulings: RC LINTEL vs host masonry + LINTEL REINFORCEMENT + LINTEL END VOLUME; FOUNDATION BACKFILL; TOP-STOREY
  WALL HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP (16:30 correction:
  slab 4.906867 m2 inside FIN.WP.ROOF by T-507, ledge 0.639573 m2 MEASURED by T-529, joins FIN.WP.ROOF); STAIR SKIRTING vs
  ROOM SKIRTING; EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY; STAIR GUARDRAIL vs SLAB-EDGE BALUSTRADE; BAND-PATH PIER FACE.
- Lessons 05 Nov: printed minimum never measured (ADOPTED); loss factor own account (PROPOSED); printed values in DIMENSION
  blocks (PROPOSED); end volume inside another element owned once (PROPOSED); constructed chord never a masonry end
  (ADOPTED); covered-but-open ledge = balcony rule (ADOPTED); exact derivation over rounded owner figure (PROPOSED).
- Materials: FINISH_MATERIALS_TABLE_V7 (stair 1:3 bed, area pending T-534), PLASTER_MATERIALS_TABLE_V3; Q-45 5 %
  ASSUMED - OWNER-APPROVED as its own account; Q-53 C 9.576 bags + 0.9975 m3 sand per m3; disposal loss never in payable.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh line 211). Designer items (D-27, D-33, D-35, D-39, D-43, lintel
  deficit ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15).
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
