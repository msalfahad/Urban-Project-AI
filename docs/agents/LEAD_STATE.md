# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log b6e52d40..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 12:16Z 6 Nov, rows changed since), then rewrite.

## Last seen
- engine: b6e52d40 (T-556 / T-557 / T-559 / T-551 / T-558 / T-553 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-06 12:18)
- last Lead run: 2026-11-06 12:16-12:30 UTC (run session_01E6cPnaz9RXJ1E6PYwanLJH)

## Run health
- Since 08:15 every run closed with a final line; 0 empty runs; 6 merged, 0 rejected, 0 blocked.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).
- Checker PARTIAL notes: T-551 (GF C1-C3 marks -> T-566), T-553 (rooms 2 / 25), T-559 (per-run heights 0 / 8 -> HELD in T-562).

## Live rows (12:18)
- READY 0.
- TODO: S: T-560 rebar t, T-565 earthworks, T-566 GF column marks + beam 0.365 m3; A: T-561 paint, T-567 external
  plaster, T-568 doors / windows; I: T-562 statement adapters V3, T-564 manifest V7 + floor fix rows + floor census.
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-563 (W3, plaster wiring,
  after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-560, T-565, T-566, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-561, T-567, T-568,
  T-513, T-314, T-502; I (worker 3): T-562, T-564, T-525, T-498, T-563, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513; wire from manifests V6 / V7.
2. 12-13 Nov: closed roof WP, blockwork, wet-room floor WP, stair bed, beams, columns / footings, wall tile, internal plaster,
   floor tile; open rebar, paint, external plaster, earthworks, doors / windows; T-562 statement before milestone text; Q-34 raised then.
3. T-564 merges -> adopt the ENCLOSED SPACE FLOOR lesson; its fix rows become a Gate B row after T-563. Next Lead run: if 1 or
   fewer TODO remain in a lane, add rows (candidates: lintel count / links kg vs freelancer, T-474 part 2 scope split,
   ceiling vs freelancer, skirting vs freelancer, HELD bounds re-measure for the 12-13 Nov scorecard).
4. 10 Nov: LOW (about 11 Gate B left in 4 days, none can start before the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell; 7-cell rows; `board check` pulls first: commit before.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: see ELEMENT_REGISTER (new 12:18: ENCLOSED SPACE FLOOR; 08:15: PARAPET EDGE DOWNSTAND MEMBER, WALL
  PLASTER HEIGHT vs PAINT HEIGHT; 17 earlier).
- Lessons 06 Nov ADOPTED: class from geometry (R-T550); net % never agreement (R-T545); bound HELD before % (R-T547); layer
  height own rule (T-556, 12:18). PROPOSED: enclosed space floor (adopt on T-564), re-cut openings at new height (adopt on
  T-563), loss own account, printed values in DIMENSION blocks, end volume owned once, exact owner derivation.
- Materials: FINISH_MATERIALS_TABLE_V7, PLASTER_MATERIALS_TABLE_V3 (plaster m2 moves with T-563); Q-45 5 % own account;
  sand = loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-27, D-33, D-35, D-39, D-43, D-45, D-48, lintel
  deficit ends, lintel bar ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (filed 00:16 6 Nov, owner package; 15 walls 175.9 m2 HELD).
- Kuwait 1990 spec over the connector limit (plastering chapter and 04220 unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
