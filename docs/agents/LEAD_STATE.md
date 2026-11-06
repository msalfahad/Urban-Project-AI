# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log e3e0ed0e..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 08:15Z 6 Nov, rows changed since), then rewrite.

## Last seen
- engine: e3e0ed0e (T-545 / T-552 / T-554 / T-547 / T-550 / T-555 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-06 08:15)
- last Lead run: 2026-11-06 08:15-08:40 UTC (run unknown)

## Run health
- Since 04:11 every run closed with a final line; 0 empty runs; 6 merged, 0 rejected, 0 blocked.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).
- Checker PARTIAL notes: T-545 (only COUNT B27 re-measured), T-550 (7.63 m2 per-run heights not re-measured -> T-559).

## Live rows (08:15)
- READY 0.
- TODO: S: T-551 columns / footings vs freelancer, T-559 blockwork leftover 25.92 m2 + edge-beam ids, T-560 rebar t vs
  freelancer; A: T-556 plaster height method version (FIRST, ENGINE_WRONG fix), T-553 floor tile, T-561 paint;
  I: T-557 statement adapters (T-545 / T-547 / T-552 / T-550), T-558 manifest V6 + plaster wiring row (after T-557).
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-551, T-559, T-560, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-556, T-553, T-561,
  T-513, T-314, T-502; I (worker 3): T-557, T-558, T-525, T-498, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-513; wire from manifest V6.
2. 12-13 Nov: closed roof WP, blockwork (25.92 UNRESOLVED), wet-room floor WP, stair bed, beams, wall tile, internal plaster;
   open columns / footings, rebar, floor tile, paint, blockwork leftover, external plaster (drawn faces HELD); T-557 adapters
   before milestone text; Q-34 raised with T-541 then.
3. T-556 merges -> adopt the plaster-layer lesson row; T-558 takes its values. Next Lead run: if 1 or fewer TODO remain in a
   lane, add rows (candidates: external plaster / facade vs freelancer, excavation / backfill vs freelancer, doors / windows
   count, T-474 part 2 scope split, lintel links kg basis, beam 0.365 m3 UNRESOLVED + HELD bounds re-measure).
4. 10 Nov: LOW (about 10 Gate B left in 4 days, none can start before the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell; 7-cell rows; `board check` pulls first: commit before.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- Research scripts only through committed package tests or the wrapper (never bare venv python).
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: see ELEMENT_REGISTER (new 08:15: PARAPET EDGE DOWNSTAND MEMBER -> B10; WALL PLASTER HEIGHT vs PAINT
  HEIGHT; earlier: WET-ROOM MEMBRANE vs BEDS, MASONRY TIES, RC LINTEL, LINTEL END VOLUME, FOUNDATION BACKFILL, TOP-STOREY
  WALL HEIGHT, STONE FLOOR, STAIR LANDING, POOL-COURT SLAB WP, STAIR SKIRTING, EXCAVATION ZONES, SKIRTING BEHIND JOINERY,
  GUARDRAIL vs BALUSTRADE, BAND-PATH PIER FACE, WET-ROOM WALL FACE, SHARED FLOOR AREA).
- Lessons 06 Nov 08:15 ADOPTED: class from geometry not hatch (R-T550); net % never agreement (R-T545); bound HELD
  before % (R-T547). PROPOSED: layer height own rule (T-556), loss own account, printed values in DIMENSION blocks,
  end volume owned once, exact owner derivation.
- Materials: FINISH_MATERIALS_TABLE_V7 (stair treads 35.4313 m2; whole stair AT_LEAST 56.3586 m2 per T-542),
  PLASTER_MATERIALS_TABLE_V3 (plaster m2 will move with T-556); Q-45 5 % own account; sand = loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-27, D-33, D-35, D-39, D-43, D-45, lintel
  deficit ends, lintel bar ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (filed 00:16 6 Nov, owner package; 15 walls 175.9 m2 HELD).
- Kuwait 1990 spec over the connector limit (plastering chapter and 04220 unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
