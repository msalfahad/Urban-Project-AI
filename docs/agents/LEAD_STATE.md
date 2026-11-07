# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log e8db39da..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 00:13Z 7 Nov, rows changed since), then rewrite.

## Last seen
- engine: e8db39da (T-571 / T-579 / T-574 / T-575 / T-580 / T-577 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-07 00:15)
- last Lead run: 2026-11-07 00:13-00:30 UTC (run session_01E6cPnep25ihcWo6ew24dn1)

## Run health
- Since 20:18 every run closed; 0 empty; 6 merged, 0 rejected.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).
- Privacy: Verifier 23:57 first T-577 verdict text refused by the session check (workbook cell values), rewritten; no leak.

## Live rows (00:15)
- READY 0.
- TODO: S: T-576 1F column +21.7 % (FIRST), T-581 lintel width basis, T-583 dome / lift bar laps + strict low; A: T-578 handrails
  + nosing (FIRST), T-584 steps, T-585 skirting yard / stairs; I: T-582 Gate B readiness F-T580-1..4 (FIRST, gate 1), T-586 statement V6.
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, + after T-582), T-563 (W3, after T-498), T-423 r2 (W1, + after T-582).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-576, T-581, T-583, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-578, T-584, T-585,
  T-513, T-314, T-502; I (worker 3): T-582, T-586, T-525, T-498, T-563, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands AND T-582 merged: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563;
   T-513; wire from manifests V6 / V7 / V8 in T-580's order; Gate B diff targets = T-580 after-totals.
2. On T-582 merge: open the F-package Gate B row from T-582's row list (F-T580-5).
3. 12-13 Nov: closed 19 trades; open handrails / nosing, 1F columns, steps, yard skirting, lintel width basis, dome-bar laps;
   T-586 statement V6 before milestone text; Q-34 raised then.
4. Lessons to adopt on merge: overlay (T-498 Gate B), cell unit (T-584), bar sphere (T-583), outline vs deduction (T-585),
   reference row first (T-581), statement restated (T-586), printed minimum one-sided (T-576), re-cut openings (T-563).
5. 10 Nov: LOW (Gate B queue behind the wrapper). When a package merges, promote its queued successor in the same run
   (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: ELEMENT_REGISTER (00:15: EXTERNAL DOOR STEP (open), YARD SKIRTING, LINTEL WIDTH BASIS; 24 earlier).
- F-C-T570-1: return paint stays ENGINE_WRONG in the statement until a candidate FIN.PAINT return line exists.
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel deficit ends, lintel bar ends, DOME-3 bars, lift-wall height)
  keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (filed 00:16 6 Nov, owner package; 15 walls 175.9 m2 HELD).
- Kuwait 1990 spec copy under 6 MB; privacy switch; PyMuPDF decision (F-T465-1); PR #3 clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
