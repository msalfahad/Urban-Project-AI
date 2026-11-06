# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 8aba0d81..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 16:13Z 6 Nov, rows changed since), then rewrite.

## Last seen
- engine: 8aba0d81 (T-561 / T-562 / T-566 / T-564 / T-565 / T-567 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-06 16:17)
- last Lead run: 2026-11-06 16:13-16:30 UTC (run session_01E6cPnam5sewJiAYNeBkeBa)

## Run health
- Since 12:16 every run closed with a final line; 0 empty runs; 6 merged, 0 rejected, 0 blocked.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).
- Privacy near-miss 15:59: Verifier commit with workbook values refused by the classifier, rewritten (6f0215f7). Watch handoffs.
- Checker PARTIAL notes now owned: T-561 returns + F-C-T564-1 + T-567 pier returns -> T-569; T-565 / T-566 held parts -> T-572.

## Live rows (16:17)
- READY 0.
- TODO: S: T-560 rebar t (FIRST; stall cause fixed), T-571 lintel count, T-572 structural HELD bounds; A: T-568 doors /
  windows, T-573 ceilings, T-574 skirting lm; I: T-570 statement V4, T-569 manifest V8 + 3 fix rows.
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-563 (W3, plaster wiring,
  after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-560, T-571, T-572, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-568, T-573, T-574,
  T-513, T-314, T-502; I (worker 3): T-570, T-569, T-525, T-498, T-563, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513; wire from manifests V6 / V7 / V8.
2. 12-13 Nov: closed 12 trades (roof WP, blockwork, wet-room floor WP, stair bed, beams, columns / footings, wall tile,
   internal plaster, floor tile, paint, external plaster, earthworks NO_ROW); open rebar, doors / windows, lintels,
   ceilings, skirting, structural HELD bounds; T-570 statement before milestone text; Q-34 raised then.
3. On T-569 merge: adopt 'plastered face implies paint face'; on T-570 merge: adopt 'gross vs gross'. Next Lead run: if 1 or
   fewer TODO remain in a lane, add rows (candidates: links kg vs freelancer, T-474 part 2 scope split, waterproofing roof
   vs freelancer re-check after T-563, marble / thresholds vs freelancer, beam residual 4 / 5 marks re-measure).
4. 10 Nov: LOW (Gate B queue behind the wrapper; none can start before it).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order (T-560 stall);
  7-cell rows; `board check` pulls first: commit before.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: see ELEMENT_REGISTER (new 16:17: PLASTERED RETURN FACE, PRECAST LINTEL; 12:18 ENCLOSED SPACE FLOOR; 19 earlier).
- Lessons 06 Nov ADOPTED: class from geometry; net % never agreement; bound HELD before %; layer height own rule; enclosed
  space floor; label CONFLICT never by majority; NO_ROW never 0. PROPOSED: re-cut openings at new height (on T-563),
  gross vs gross (on T-570), plastered face implies paint face (on T-569), loss own account, printed values in DIMENSION
  blocks, end volume owned once, exact owner derivation.
- Materials: FINISH_MATERIALS_TABLE_V7, PLASTER_MATERIALS_TABLE_V3 (plaster m2 moves with T-563); Q-45 5 % own account;
  sand = loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-27, D-33, D-35, D-39, D-43, D-45, D-48, lintel deficit ends, lintel bar ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (filed 00:16 6 Nov, owner package; 15 walls 175.9 m2 HELD).
- Kuwait 1990 spec over the connector limit (plastering chapter and 04220 unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
