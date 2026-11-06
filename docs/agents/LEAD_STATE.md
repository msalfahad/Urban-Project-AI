# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 587e47f9..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 20:12Z 6 Nov, rows changed since), then rewrite.

## Last seen
- engine: 587e47f9 (T-560 / T-570 / T-568 / T-572 / T-569 / T-573 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-06 20:14)
- last Lead run: 2026-11-06 20:12-20:30 UTC (run unknown)

## Run health
- Since 16:13 every run closed; 0 empty; 6 merged, 0 rejected.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).
- Privacy: T-560 commit with drawing bar labels refused by the classifier (not retried); T-575 row: computed t + sheet refs only.

## Live rows (20:14)
- READY 0.
- TODO: S: T-571 lintel count (FIRST), T-575 dome / ring / lift-pit rebar, T-576 1F column +21.7 % + GF B7; A: T-574 skirting
  (FIRST), T-577 thresholds / sills / stone, T-578 handrails + nosing; I: T-579 statement V5 (FIRST), T-580 manifest overlay dry run.
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-571, T-575, T-576, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-574, T-577, T-578,
  T-513, T-314, T-502; I (worker 3): T-579, T-580, T-525, T-498, T-563, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513; wire from
   manifests V6 / V7 / V8 in the order T-580 proves (V8: return paint, dressing A08, pier, W17, rebar HELD rows).
2. 12-13 Nov: closed 16 trades (adds rebar NOT_COMPARABLE, doors / windows, ceilings, structural bounds); open lintels,
   skirting, thresholds / sills, handrails / nosing, dome / lift-pit bars, 1F column +21.7 %; T-579 statement V5 before
   milestone text; Q-34 raised then.
3. If 1 or fewer TODO remain in a lane, add rows (T-474 part 2 split, link population, external works, MEP scope census).
   On T-579 merge: adopt 'ceilings by face class'; on T-576 merge: adopt 'printed minimum is a one-sided bound'.
4. 10 Nov: LOW (Gate B queue behind the wrapper; none can start before it).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: ELEMENT_REGISTER (20:14: DOME / RING / LIFT-PIT WALL REINFORCEMENT, COLUMN-BEAM JOINT; 22 earlier).
- Lessons 06 Nov ADOPTED: class from geometry; net % never agreement; bound HELD before %; layer height own rule; enclosed
  space floor; label CONFLICT never by majority; NO_ROW never 0; gross vs gross; plastered face implies paint face;
  benchmark basis first; count by drawn leaves. PROPOSED: re-cut openings at new height (on T-563), ceilings by face
  class (on T-579), printed minimum one-sided bound (on T-576), 4 older (see ERS s.7).
- F-C-T570-1: return paint stays ENGINE_WRONG in the statement until a candidate FIN.PAINT return line exists.
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel deficit ends, lintel bar ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (filed 00:16 6 Nov, owner package; 15 walls 175.9 m2 HELD).
- Kuwait 1990 spec copy under 6 MB; privacy switch; PyMuPDF decision (F-T465-1); PR #3 clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
