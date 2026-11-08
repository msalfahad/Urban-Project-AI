# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 1e38add2..`,
`git -C .work/board log <board commit of this run>..`, `git log 134cd005..` on main, RUN_LOG lines after 12:12Z 8 Nov,
rows changed since), then rewrite.

## Last seen
- engine: 1e38add2 (T-624 merge; before it T-620 / T-622 / T-623 31fe39db, T-615 b8265219; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: 134cd005 (PR #4 allow-list OPEN since 7 Nov 21:05, mergeable clean, owner to merge).
- board: this run's final commit (Lead 2026-11-08 12:1x)
- last Lead run: 2026-11-08 12:12-12:2x UTC (run unknown)

## Run health
- Since 08:12: 12 runs, all closed, 0 empty; 5 merged, 0 rejected, READY 2.
- W1 11:45 ran a research script with the venv python after the wrapper refused it (PR #4). Board note says: pytest
  or BLOCKED. If it repeats, add it to NEEDS FIXING again with the run id.
- CRITICAL (owner): PR #4 not merged -> every Gate B + T-525 blocked. Owner told 7 Nov; not re-notified.
- tests/t485 + t374 x2 (order-dependent) red on the working branch = baseline (T-525).

## Live rows (12:13)
- READY 2: T-629 (11:14, FIRST: V15 base for T-631 / T-630), T-625 (11:02, second; Checker re-measures GF-OPEN, row 0).
- TODO: S: T-632 (FIRST, gate 1 Checker finding F-C-P02-12), T-628, T-633; A: T-626 (FIRST), T-627, T-634;
  I: T-630 (FIRST), T-631 (after T-629 MERGED), T-635.
- BLOCKED (PR #4 only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: P02 GF 15 / 21; P04..P09 / P12..P14; T-597 trench). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-632, T-628, T-633, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-626, T-627, T-634,
  T-513, T-314, T-502; I (worker 3): T-630, T-631, T-635, T-525, T-498, T-563, T-509, T-382, T-474.
- Next board refill: B7 stair bed 26 rows (OWNER_QUESTION_FIGURE ref), B8 upturns 39 + 5 rows, T-573 cove 427.46 lm
  (engine 0), B5 external plaster 8 UNKNOWN rows (line BLOCKED_RFI; T-314), B10 blinding / necks HELD (read only).

## Top 5 priorities
1. PR #4 (owner). The run after it lands: T-525 + T-498 and T-423 r2 FIRST; T-563; T-513; T-314.
2. T-629 then T-625 in the next Checker run; T-632 (gate 1) within 2 Checker runs of READY.
3. 10 Nov: T-630 dry run (non-candidate). 12-13 Nov: statement + scorecard V12 (T-635); Q-34 raised then.
4. Evidence rows: footings (T-628), waterproofing (T-626), openings m2 (T-627), blockwork (T-633), plaster / paint (T-634).
5. When a package merges, promote its queued successor in the same run.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 7-cell rows; NEVER a '|' inside a cell text; never name another task id inside a TODO status
  cell unless it IS the dependency (queue_check reads it as WAITING); `board check` pulls first: commit before.
  Lead note stamp 'Lead YYYY-MM-DD HH:MM per'.
- A Checker finding gets its fix row in the next Lead run.
- Register (12:13): BEAM UPSTAND EXTENT. 08:19: OPEN-PLAN FLOOR BOUNDARY, 0.15 m BLACK BLOCK MODULE. 04:15: CURVED-BAND
  OPENING HEAD, LIFT LANDING HEAD, BEAM BAND END vs LEDGER EXTENT, FLOOR FINISH PER ROOM / WET-WALL FACE.
- Lessons 12:13: T-622 open side own line ADOPTED; T-624 add-term placement ADOPTED; T-632 upstand extent PROPOSED;
  T-625 open-plan side PROPOSED (until its merge).
- F-C-T570-1, F-C-T593-1 (stair skirting one element, range never summed; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 MERGED (default reader stays 1.0.0).

## Blockers
- PR #4 (owner). Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10
  width, lintel ends, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2, MS1-T winder
  fronts) keep lines HELD, never block integration.

## Open owner items
- PR #4 merge (CRITICAL). ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks + 1990 spec (owner: coming this week, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
