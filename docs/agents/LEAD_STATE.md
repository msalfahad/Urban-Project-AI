# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 9dc3c2d3..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 20:15Z 7 Nov, rows changed since), then rewrite.

## Last seen
- engine: 9dc3c2d3 (T-604 / T-606 / T-599 r2 merges; candidate of record ARCH_TAKEOFF_V3.0.58 /
  BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-07 20:18)
- last Lead run: 2026-11-07 20:15-20:18 UTC (run session_01E6cPncMKBGEmf2gDLrgNcd)

## Run health
- Since 16:12: 10 runs, all closed; 0 empty; 3 merged; 0 rejected; Verifier 19:51 overlap-guard skip (by design).
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 + t374 x2 (order-dependent) red on the working branch = baseline (T-507 stale pending in master 1.55.0; T-525).

## Live rows (20:18)
- READY 3: T-605 (W1 19:28, gate 1, first), T-607 (W2 18:59), T-609 (W3 19:12); cause CHECKER-RUNS.
- TODO: S: T-600 (FIRST, 2.369278 m3 + 1F 0.385/0.460), T-610 beam overlap census; A: T-612 skirting remainder (FIRST),
  T-608 lift landing openings; I: T-611 manifest V13 + FR-T606-1 (FIRST), T-613 scorecard tables (after T-609).
- BLOCKED (wrapper only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: P04..P09 / P12..P14; T-597 trench re-measure; 1F CB10 / CB11 / CB12). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-600, T-610, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-612, T-608, T-513, T-314, T-502;
  I (worker 3): T-611, T-613, T-525, T-498, T-563, T-509, T-382, T-474.
- Board thin (6 TODO): when T-605 / T-607 / T-609 merge add fix-row follow-ups (manifest V14 for their FR rows) and 1 S row.

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513;
   wire from manifests V6..V13 in T-580's order; Gate B diff targets = overlay after-totals (V13 when merged).
2. T-605 within 2 Checker runs of READY (gate 1); then T-607, T-609.
3. 12-13 Nov: statement V10 (T-609) -> scorecard tables (T-613); Q-34 raised then with T-541's reconciliation.
4. Residuals by size: T-612 GF 16.914 lm, T-600 2.369 m3, T-610 beam crossings; FR-T606-1 wired in T-611.
5. When a package merges, promote its queued successor in the same run (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register (20:18): BEAM BAND OVERLAP (union of drawn bands, owner per UP-CONC-JOINT-001), SKIRTING AT STAIR-OPENING
  WALLS (none where no floor). 16:17: FOOTING OVERLAP (whole outline owns; drawn, not schedule), LIFT LANDING DOOR (not a passage; supply
  HELD), STAIR STEP / NOSING EDGE (one edge once per line). 12:16: COLUMN-BEAM JOINT CORRECTED, DOORLESS OPENING JAMB.
- UP-CONC-JOINT-001 1.0.0 MERGED (LEAD_ADOPTED, not owner-approved). GF matched source T-551 2.28125 m3; other readings -> T-600.
- Lessons 16:17 ADOPTED: matched-part-only reclass; plot-boundary gaps in step census; label not evidence; drawn
  outlines for overlaps; restatement bounds; statement reclass = class move only.
- F-C-T570-1, F-C-T593-1 (stair skirting one element, range never summed; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel ends, DOME-3 bars, lift-wall height, F-T583-1 note 9,
  F-T589-2, MS1-T winder fronts) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (15 walls 175.9 m2 HELD); ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks over 6.2 MB; Kuwait 1990 spec copy under 6 MB; privacy switch; PyMuPDF (F-T465-1); PR #3.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
