# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 2f103248..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 04:13Z 9 Nov,
rows changed since), then rewrite.

## Last seen
- engine: 2f103248 (T-633 merge; before 2a2e28ca T-650, c7565fb9 T-525 master 1.57.0, af50c864 T-646); candidate of
  record ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.57.0; released V2.9 + route G.
- main: fd71bc30 (PR #4 merged by the owner 21:15 8 Nov). Gate B OPEN.
- board: this run's final commit (Lead 2026-11-09 04:1x)
- last Lead run: 2026-11-09 04:13-04:3x UTC (run session_01E6cPndfy8CYAfU6erUi3md)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 + OWNER SESSION 21:15: delivery first; no new investigation tasks (fix rows that
  wire or prove a quantity only); report only WIRED quantities and Checker-verified whole lines; Gate B one at a time
  in the order T-525 (MERGED) -> T-498 -> T-423 r2 -> T-563 -> T-314 -> remaining V14 fix rows. UrbanProjectsManager untouched.

## Run health
- Since 00:19: 10 runs closed, 0 empty; 4 merged, 1 rejected (T-647 narrow). W3 03:01 running at 04:16 (PENDING):
  if no final line by the next Lead run (> 4 h since claim), report INCOMPLETE and return T-498 to TODO.
- venv 'No module named pytest' at first use ~half of runs (setup rebuilds): NEEDS FIXING note each report.

## Live rows (04:16)
- READY: none. CLAIMED: T-498 (W3 03:01, Gate B step 2).
- TODO: S: T-647 r2 (FIRST), T-423 r2 (after T-498 READY: file dependency); A: T-648 (FIRST), T-314 (after T-648;
  Gate B 5th); I: T-649 (after T-498; scope extended 04:16), T-563 (after T-498), T-635 (after T-649).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (P12, P13, P14 CLOSED; next CLOSABLE line). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-647, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-648, T-314, T-513, T-502;
  I (worker 3): T-498, T-649, T-563, T-635, T-509, T-382, T-474.
- TODO count 7 (< 8 on purpose: directive + one-at-a-time Gate B). Refill: remaining V14 fix rows once T-314 is
  claimed; B8 penetrations 17 pcs HELD blank, B6 shutters, B3 thresholds only if T-648 leaves them without a quantity.

## Top 5 priorities
1. Gate B: T-498 to the Checker first when READY; then T-423 r2 (W1) -> T-563 (W3) -> T-314 (W2).
2. T-647 r2 (gate 1, never delayed more than 2 Checker runs) + T-648 -> trial BOQ r2 in T-649.
3. Checker light slot: re-measure D-1F-07 and L-GF-01 (T-650) before T-649 wires R-T650-1.
4. 12-13 Nov: T-635 statement + scorecard V12 (after T-649); Q-34 raised then.
5. When a package merges, promote its successor in the same run.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 7-cell rows; NEVER a '|' inside a cell text; `board check` pulls first: commit before. Never write
  'after T-xxx' (or 'waits on') in history text unless it is a live dependency: queue_check reads the whole cell.
  Stamp 'Lead YYYY-MM-DD HH:MM per' from `date -u`.
- A Checker finding gets its fix row in the next Lead run.
- Register 04:16: LINTEL BEARING TOLERANCE (F-T650-3). 00:15: PRECAST LINTEL PAYABLE FORM RESTATED.
- Rulings: F-T650-3 (04:16), F-T644-1 (T-650 MERGED, ADOPTED), F-T645-1 (T-649).
- Lessons 04:16: T-644 ADOPTED; PROPOSED T-647 r1, F-T650-3, T-633, T-645, T-636.
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 MERGED (default reader stays 1.0.0).

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10 width, lintel ends,
  DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2, MS1-T winder fronts, C-ST-4) keep
  lines HELD, never block integration.

## Open owner items
- ORR-007 stair skirting payable form. venv incomplete at first use (NEEDS FIXING, agent code).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
