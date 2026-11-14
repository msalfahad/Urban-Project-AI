> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log 939bb281..origin/...`, board
commits after this run's commit, RUN_LOG lines after 20:12Z 14 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`. Take every time stamp from `date -u` at the moment of writing.

## Last seen
- engine origin head: 939bb281 (T-793 merge). Merged since 16:12: T-795 26c0b41b, T-796 de1aa003, T-788 r2 c12c8eb4,
  T-770 r10 91072069 + promotion df770b00 (V3.0.87 / 1.87.0), T-793 939bb281. T-791 r1 REJECTED. No owner engine commit;
  no new OWNER_SESSION_CHANGES row since 13 Nov 15:00.
- Last Lead run: 2026-11-14 20:12 UTC (session_01E6cPne4SyXg6zcdVFH9sJg). Drive readable; no new files since 16:00.
- Candidate of record ARCH_TAKEOFF_V3.0.87 (master 1.87.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 20:14)
r11 V3.0.88 / 1.88.0 = CORNICE T-788 + HELD RANGES T-795 (+ STAIRS T-791 if merged at claim) + commit
BLANK_LINES_V3.0.88.md and COMPARE_V3.0.88.md (number (b)) -> r12 = T-791 (if not in r11) + T-798 + T-799 fix rows.

## Fill / difference state
- Blank non-rebar V3.0.87: 18 = stairs 14 BLANK (T-791 r2) + 4 HELD ranges closed by T-795 rows (r11) -> 14 -> 0.
- Open differences: beams 76.05 vs 65.97 (+15.3 %, UNRESOLVED 3.48 -> T-798); columns 33.83 vs 28.55 (planted P.C);
  upturn 228.99 vs 194 (his lump -11.89 UNRESOLVED named); plaster shaft rows 54.00 UNRESOLVED (T-799); masonry -22.2 %
  (T-783 second method); his 1F projections 41.25 m2 UNRESOLVED (no row unless his sheet names it).
- Already reconciled (do not re-queue): windows -14.4 % split to 0 (04:20), external doors '12 vs 6' = his m2 cell (12:19).
- Number (b) = COMPARE_V3.0.x.md from build_boq.py (decided 16:13); not yet produced on .86 / .87.

## Live rows (20:14)
- READY: none. TODO: W1 T-791 r2, T-798, T-797; W2 T-799, T-783, T-774 (after T-773); W3 T-770 r11, T-800, T-773
  (owner authorises). PAUSED: T-382, T-664, T-450 p2, T-451, T-472. IN PROGRESS: T-180. Next free T-801.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it. Write "Nth in queue (not blocked ...)"; never the words
  "after T-" for pure queue order (makes the row WAITING). Time stamps: from `date -u` at writing, never ahead.
- Status word FIRST; 7 cells (id | gate | lane title | description | status | branch | verdict); no '|' in a cell.
  MERGED only after `engine push` + sha on origin. T-770 row has extra legacy cells: prepend to cell 5 only.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet all RC on Alsenan sections -> STR.CONC.PARAPET whole, block = complement (R-T789-1); stair concrete +
  formwork S, finish faces A; boundary wall: under-building band = S, fence-run foundation = S, fence block / plaster
  above N.G. = A. Dome extrados = roof layers family; flat roof keeps footprint deduction. ARCH.WALL_PANEL / VOLUME =
  REFERENCE views of MAS.BLOCK (T-790). Upturn door / glazing gaps = transition / termination lines (T-794). A closed
  double outline on a rail layer is classified once, rail or divider (F-V791-1, T-791 r2).
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1, R-T789-1, MARK_BY_OUTLINE_FIT_V1,
  L-T791-1.

## Blockers / open owner items
- DESIGNER_QUESTIONS (19 incl. D-DOME, 1F parapet ~1.63 vs 1.20) with the owner; ORR-007 stair skirting; Q-34 2F top
  roof; release switch T-773 is his. Scout paused. Wrapper run allow-list refuses older research scripts for the Checker.
