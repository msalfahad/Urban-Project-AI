# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 4777890b..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 12:18Z 5 Nov, rows changed since), then rewrite.

## Last seen
- engine: 4777890b (T-519..T-524 merges; candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / BOQ_FAMILY_MASTER
  1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-05 12:20)
- last Lead run: 2026-11-05 12:18-12:30 UTC (run session_01E6cPnbtTuNZpzcrPDzZFRg)

## Run health
- Since 08:13 every run closed with a final line; 0 empty runs; 6 merged, 0 rejected.
- CRITICAL (owner, notified 04:15, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B blocked.
- tests/t485 red on engine 9a28e927 and 4777890b (T-507 stale pending in master 1.55.0) -> T-525 gate 0.

## Live rows (12:20)
- READY 0. CLAIMED 0. TODO 7 (Gate A / gate 0, research + tests via pytest, none needs the wrapper except possibly T-525):
  S: T-526 column ends missed by junction censuses (F-T520-1), T-527 LINTEL_BEARING_V3 curved bay (F-C-T519-1),
     T-531 lintel bars on PRODUCED lintels (W18 group HELD until T-527)
  A: T-528 FINISH_MATERIALS_TABLE_V7 stair bed per Q-53 C (engine/source, new file), T-529 ledge membrane exposure V2
  I: T-525 GATE FIX t485 (master 1.56.0 promoting T-507; if only a research script can build it -> BLOCKED, fold into
     T-498), T-530 wiring manifest of the 9 unwired pieces (T-516..T-524)
- BLOCKED (wrapper): T-498 (W3, staged V3.0.59; resume must carry T-507 promotion if T-525 blocks), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-526, T-527, T-531, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-528, T-529, T-513,
  T-314, T-502; I (worker 3): T-525, T-530, T-498, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (W3) and T-423 r2 (W1) FIRST; T-513 (W2); wire from T-530.
2. T-525 gate 0 merged within 2 Checker runs; then Gate A T-526..T-531 in READY order.
3. Next Lead run: if 1 or fewer TODO remain in a lane, add non-candidate rows (candidates: 0.15 m perimeter mortar
   module source; exterior plaster parapet / plinth owner trade (L-N10-02); T-474 part 2 scope split; sand pack source).
4. 10 Nov: HIGH RISK (about 10 Gate B left in 4.5 days, all blocked by the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked; second / third
  rows in a lane carry no 'after T-nnn' unless truly dependent (WAITING rows caused empty runs).
- Status word FIRST in the status cell; 9-field rows; `board check` pulls first: commit before.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- Research scripts only through committed package tests or the wrapper (never bare venv python, never a throwaway runner).
- Register rulings: RC LINTEL vs host masonry + LINTEL REINFORCEMENT + LINTEL END VOLUME (12:20: inside a column = column
  line; lintel-on-lintel once by R-T524-1; unbuildable = designer HELD); FOUNDATION BACKFILL; TOP-STOREY WALL HEIGHT vs
  ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP; STAIR SKIRTING vs ROOM SKIRTING;
  EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY; STAIR GUARDRAIL vs SLAB-EDGE BALUSTRADE; BAND-PATH PIER FACE.
- Lessons proposed 05 Nov: printed minimum never a measured value (ADOPTED); loss factor own account (PROPOSED);
  printed values also in DIMENSION blocks (PROPOSED 12:20); end volume inside another element owned once by it (PROPOSED).
- Materials: FINISH_MATERIALS_TABLE_V6 (-> V7 by T-528), PLASTER_MATERIALS_TABLE_V3; Q-45 5 % ASSUMED - OWNER-APPROVED
  as its own account; Q-53 C CALCULATED PROVISIONAL (9.6 bags + 1.00 m3 sand per m3 1:3); disposal loss never in payable.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh line 211). Designer items (D-27, D-33, D-35, D-39, D-43, lintel
  deficit ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15).
- Kuwait 1990 spec over the connector limit (plastering chapter unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
