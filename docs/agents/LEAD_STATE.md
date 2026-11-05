# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log ba9eba77..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 20:13Z 5 Nov, rows changed since), then rewrite.

## Last seen
- engine: ba9eba77 (T-531 / T-536 / T-535 / T-532 merges; candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / BOQ_FAMILY_MASTER
  1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-05 20:17)
- last Lead run: 2026-11-05 20:13-20:20 UTC (run session_01E6cPnbaRwhAgRs72ThbLjT)

## Run health
- Since 16:16 every run closed with a final line; 0 empty runs; 4 merged, 1 rejected (T-537, narrow), 0 blocked.
- CRITICAL (owner, notified 04:15, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).

## Live rows (20:17)
- READY 1: T-534 (Gate A PASS 18:05; merge waits T-538 gate fix).
- TODO: S: T-533 0.15 module, T-539 ties / mesh lines; A: T-540 sand load / density, T-541 roof WP vs freelancer,
  T-542 stair riser / landing beds (after T-534); I: T-538 gate fix + manifest V3 (FIRST), T-537 r2 (bound direction).
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-533, T-539, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-540, T-541, T-542, T-513,
  T-314, T-502; I (worker 3): T-538, T-537, T-525, T-498, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-513; wire from manifest V3.
2. T-538 first (unblocks T-534 merge), then Gate A in READY order; structural first.
3. Next Lead run: if 1 or fewer TODO remain in a lane, add non-candidate rows (candidates: T-474 part 2 scope split;
   lintel links kg basis; F-C-T526-2 wording only; stream F package prep; 12-13 Nov reconciliation rows per trade like T-541).
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
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: see ELEMENT_REGISTER (RC LINTEL, LINTEL REINFORCEMENT / END VOLUME, FOUNDATION BACKFILL, TOP-STOREY WALL
  HEIGHT, STONE FLOOR, STAIR LANDING, POOL-COURT SLAB WP (slab 4.906867 m2 in FIN.WP.ROOF, ledge 0.639573 m2 MEASURED),
  STAIR SKIRTING, EXCAVATION ZONES, SKIRTING BEHIND JOINERY, GUARDRAIL vs BALUSTRADE, BAND-PATH PIER FACE).
- Lessons 05 Nov: printed minimum never measured / constructed chord never a masonry end / covered-but-open ledge = balcony
  (ADOPTED); loss own account, printed values in DIMENSION blocks, end volume owned once, exact owner derivation, bound
  direction carried, no live commit in tests, sliver never an element (PROPOSED).
- Materials: FINISH_MATERIALS_TABLE_V7 (stair 1:3 bed 35.4313 m2 on merge of T-534), PLASTER_MATERIALS_TABLE_V3; Q-45 5 %
  ASSUMED - OWNER-APPROVED own account; sand = loose m3 (T-535); disposal loss never in payable.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh line 211). Designer items (D-27, D-33, D-35, D-39, D-43, lintel
  deficit ends, lintel bar ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15).
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
