# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log abc71ec6..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 08:18Z 9 Nov,
rows changed since), then rewrite.

## Last seen
- engine: abc71ec6 (T-635 merge; before 92d5d1ff T-648 revert, 89afbd85 T-649, a521da8a T-647 r2, 4c37ce2c T-498);
  candidate of record ARCH_TAKEOFF_V3.0.59 / BOQ_FAMILY_MASTER 1.58.0 (V3.0.59 still pending in it: t485 RED);
  released V2.9 + route G.
- main: fd71bc30 (PR #4 merged by the owner 21:15 8 Nov). Gate B OPEN.
- board: this run's final commit (Lead 2026-11-09 08:2x)
- last Lead run: 2026-11-09 08:17-08:3x UTC (run unknown)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 + OWNER SESSION 21:15: delivery first; no new investigation tasks (fix rows that
  wire or prove a quantity only); report only WIRED quantities and Checker-verified whole lines; Gate B one at a time
  in the order T-525 (MERGED) -> T-498 (MERGED) -> T-423 r2 -> T-563 -> T-314 -> remaining V14 fix rows.
  UrbanProjectsManager untouched.

## Run health
- Since 04:19: 11 runs, all closed; 4 merged, 1 rejected (T-648), 1 INCOMPLETE stage (T-314). No venv failure seen.
- Process fault: W2 claimed T-314 (Gate B 5th) ahead of steps 3-4 and held the m9 hub; written in the T-314 row.

## Live rows (08:20)
- READY: none. CLAIMED: none.
- TODO: S: T-423 r2 (FIRST, Gate B 3); A: T-648 r2 (FIRST, local Decimal context), T-314 r2 (after T-648, Gate B 5,
  Checker after T-563 MERGED); I: T-651 (FIRST, master 1.59.0 promotes T-498, gate 0), T-652 (after T-651: V19 +
  trial BOQ r3), T-563 (after T-652; Checker after T-423 r2 MERGED).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (P12-P14 CLOSED; next CLOSABLE line). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-423, T-424, T-364, T-363, T-372; A (worker 2): T-648, T-314, T-513, T-502;
  I (worker 3): T-651, T-652, T-563, T-509, T-382, T-474.
- TODO 6 (< 8 on purpose). Refill: remaining V14 fix rows after T-314; B8 penetrations 17 pcs HELD blank, B6 shutters.

## Top 5 priorities
1. T-651 to the Checker first (t485 red blocks every Gate B L4).
2. Gate B step 3 T-423 r2, then T-563, then T-314 r2, each rebased on the previous merge.
3. T-652 trial BOQ r3 for 10 Nov (state what it does and does not contain).
4. T-648 r2 small; Checker runs merged suites in one session (Decimal lesson).
5. When a package merges, promote its successor and its registry promotion in the same run.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time. A later Gate B step never holds the shared hub
  while an earlier step is unclaimed (08:20).
- Status word FIRST; 7 cells: id | gate | title | description | STATUS | branch | verdict. NEVER a '|' inside a cell.
  `board check` pulls first: commit before. 'after T-xxx' only for live dependencies. Stamp from `date -u`.
- A Checker finding gets its fix row in the next Lead run. A merge that breaks a gate gets a fix row at the top of its lane.
- Register 04:16: LINTEL BEARING TOLERANCE (F-T650-3). 00:15: PRECAST LINTEL PAYABLE FORM RESTATED.
- Lessons PROPOSED 08:20: no process-global numeric state (T-648); registry promotion travels with the merge (T-651);
  Gate B order is a claim rule (T-314). 04:16: T-644 ADOPTED; PROPOSED T-647 r1, F-T650-3, T-633, T-645, T-636.
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 MERGED (0.15 module, Q-80) -> valued in T-652.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10 width, lintel ends
  incl. D-1F-07 START bearing 0.259, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2,
  MS1-T winder fronts, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- ORR-007 stair skirting payable form. venv incomplete at first use (watch).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
