# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log e04d99d9..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 16:16Z 9 Nov,
rows changed since), then rewrite.

## Last seen
- engine: e04d99d9 (T-563 merge; before db8898c1 T-653, 62e18eed T-423 r3); candidate of record ARCH_TAKEOFF_V3.0.61 /
  BOQ_FAMILY_MASTER 1.61.0 (t485 RED: V3.0.60 + V3.0.61 pending); released V2.9 + route G.
- main: fd71bc30. Gate B OPEN.
- board: this run's final commit (Lead 2026-11-09 16:2x)
- last Lead run: 2026-11-09 16:16-16:3x UTC (run unknown)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 + OWNER SESSION 21:15: delivery first; no new investigation tasks (fix rows that
  wire or prove a quantity only); report only WIRED quantities and Checker-verified whole lines; Gate B one at a time:
  T-525, T-498, T-423, T-563 all MERGED -> T-314 (step 5) -> remaining V14 fix rows (T-424 first). UPM untouched.

## Run health
- 12:19-16:16: 12 runs, all closed; 3 merged, 0 rejected, 1 INCOMPLETE stage (T-314 r2, correct), 2 Checker overlap
  guards (correct), 3 empty worker runs (no claimable row; all lanes now have a TODO).

## Live rows (16:17)
- READY: none. CLAIMED: none.
- TODO: A: T-655 (W2 FIRST, gate 0: master 1.62.0 promotes T-423 / T-563 + t199 helper F-T314-2), T-314 r3 (after
  T-655 MERGED; master 1.63.0, V3.0.62); I: T-654 (W3 FIRST, trial BOQ r4, research only); S: T-656 (W1, gate 0,
  F-T653-1 t627 local context).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (next P15 ext GB trench, then P16 B10 COUNT rows). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-656, T-424, T-364, T-363, T-372; A (worker 2): T-655, T-314, T-513, T-502;
  I (worker 3): T-654, T-509, T-382, T-474.

## Top 5 priorities
1. T-655 merged at the first Checker run after READY (t485 green).
2. T-654 trial BOQ r4 merged by 10 Nov end (10 Nov milestone).
3. T-314 r3 built right after T-655 merges; Checker Gate B step 5 next.
4. After T-314 merges: T-424 (W1) to TODO, then the remaining V14 fix rows; check each master promotes every merged
   version (new PROPOSED lesson).
5. T-656 small gate-0 fix; then ADOPT the two 16:17 PROPOSED lessons when T-655 / T-314 r3 show them.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time. A later Gate B step never holds the shared hub
  while an earlier step is unclaimed (ADOPTED 12:20).
- Status word FIRST; 7 cells: id | gate | title | description | STATUS | branch | verdict. NEVER a '|' inside a cell.
  `board check` pulls first: commit before. 'after T-xxx' only for live dependencies. Stamp from `date -u`.
- A Checker finding gets its fix row in the next Lead run. A merge that breaks a gate gets a fix row at the top of its lane.
- Lessons: ADOPTED 16:17 no process-global numeric state (T-653); ADOPTED registry promotion with the merge (T-651),
  Gate B claim order (T-314), every HELD carries a committed cause; PROPOSED 16:17 rebased package promotes its merged
  predecessor (T-563), registry tests pick writers among governed files (F-T314-2); T-647 r1, F-T650-3, T-633, T-645.
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80): 0.15 hosts 2,194.1375 pcs.
- Plaster: candidate FIN.PLASTER released 363.3738 m2; 4 lines HELD 262.018 .. 262.052 (D-39 / DCR-6).

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10 width, lintel ends
  incl. D-1F-07 START bearing 0.259, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2,
  MS1-T winder fronts, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- ORR-007 stair skirting payable form. venv incomplete at first use (watch).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
