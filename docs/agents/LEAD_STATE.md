# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 2e80c03f..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 12:19Z 9 Nov,
rows changed since), then rewrite.

## Last seen
- engine: 2e80c03f (T-652 merge; before 26af97af T-651, 57db7053 T-648 r2); candidate of record ARCH_TAKEOFF_V3.0.59 /
  BOQ_FAMILY_MASTER 1.59.0 (t485 green); released V2.9 + route G.
- main: fd71bc30. Gate B OPEN.
- board: this run's final commit (Lead 2026-11-09 12:2x)
- last Lead run: 2026-11-09 12:19-12:3x UTC (session_01E6cPndykD62vE8uJCsPCG1)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 + OWNER SESSION 21:15: delivery first; no new investigation tasks (fix rows that
  wire or prove a quantity only); report only WIRED quantities and Checker-verified whole lines; Gate B one at a time
  in the order T-525 (MERGED) -> T-498 (MERGED) -> T-423 (r3 READY) -> T-563 -> T-314 -> remaining V14 fix rows.
  UrbanProjectsManager untouched.

## Run health
- 08:22-12:19: 11 runs, all closed; 3 merged, 0 rejected, 1 INCOMPLETE stage (T-423 r2, correct). venv incomplete
  once more (W3 11:05, setup rerun fixed it).

## Live rows (12:20)
- READY: T-423 r3 (bdbbb8db, V3.0.60 / master 1.60.0, text-only 22 lines). CLAIMED: none.
- TODO: A: T-653 (FIRST, gate 0, F-T648-2: 19 research files global Decimal prec), T-314 r2 (after T-653 and T-563
  CLAIMED; renumber its V3.0.60 stage at rebase); I: T-563 (FIRST, Checker after T-423 r3 MERGED).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-502; W3 T-654 (trial BOQ r4, after T-563), T-509, T-382, T-474.
- IN PROGRESS: T-180 (next P15 ext GB trench 1.069267 .. 1.176467 m3, then P16 B10 COUNT rows). PAUSED: T-450 p2,
  T-451, T-472.
- Lane order: S (worker 1): T-423, T-424, T-364, T-363, T-372; A (worker 2): T-653, T-314, T-513, T-502;
  I (worker 3): T-563, T-654, T-509, T-382, T-474.
- W1 has no claimable row until T-314 is claimed (expected empty runs; T-424 waits on the Gate B order).

## Top 5 priorities
1. T-423 r3 Gate B at the next Checker run (merge head as is; T-651 already in it).
2. T-563 built by W3 now, Checker right after T-423 r3 merges; then T-314 r2.
3. T-653 gate fix (W2) so L4 shows only the t374 pair; then ADOPT the numeric-state lesson.
4. T-654 trial BOQ r4 on the newest master after steps 3-4.
5. When a package merges, promote its successor in the same run; after T-314, row the remaining V14 fix rows (W1 T-424).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time. A later Gate B step never holds the shared hub
  while an earlier step is unclaimed (ADOPTED 12:20).
- Status word FIRST; 7 cells: id | gate | title | description | STATUS | branch | verdict. NEVER a '|' inside a cell.
  `board check` pulls first: commit before. 'after T-xxx' only for live dependencies. Stamp from `date -u`.
- A Checker finding gets its fix row in the next Lead run. A merge that breaks a gate gets a fix row at the top of its lane.
- Lessons 12:20: ADOPTED registry promotion with the merge (T-651), Gate B claim order (T-314), every HELD carries a
  committed cause (T-636/T-648); PROPOSED no process-global numeric state (T-653), T-647 r1, F-T650-3, T-633, T-645.
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80) valued in T-652: 0.15 hosts 2,194.1375 pcs.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10 width, lintel ends
  incl. D-1F-07 START bearing 0.259, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2,
  MS1-T winder fronts, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- ORR-007 stair skirting payable form. venv incomplete at first use (watch).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
