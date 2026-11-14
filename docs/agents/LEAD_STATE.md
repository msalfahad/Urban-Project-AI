> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log 8f558cef..origin/...`, board
commits after this run's commit, RUN_LOG lines after 16:12Z 14 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`. Take every time stamp from `date -u` at the moment of writing.

## Last seen
- engine origin head: 8f558cef (T-794 merge). Merged since 12:16: T-790 28d6336e, T-786 a2001238, T-770 r9 9be5f69a +
  promotion cb3d2fb1 (V3.0.86 / 1.86.0), T-792 9ff810ac, T-794 8f558cef. No owner engine commit; no new
  OWNER_SESSION_CHANGES row since 13 Nov 15:00.
- Last Lead run: 2026-11-14 16:12 UTC (session_01E6cPncF9bUSRZTRJ8ri7cw). Drive readable; no new files since 12:00.
- Candidate of record ARCH_TAKEOFF_V3.0.86 (master 1.86.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 16:13)
r10 V3.0.87 / 1.87.0 = CONCRETE (T-786 + F-V786-1 -0.141 + T-792) + ROOF UPTURN (T-794) + CORNICE T-788 if merged at
claim (else STAIRS T-791 if merged) -> r11 = T-791 / T-795 / T-796 (+ T-788 if not in r10).

## Fill / difference state
- Blank non-rebar V3.0.86: 18 = stairs 14 BLANK (T-791) + HELD ranges: tile door-jamb edge 0 .. 73.1 lm, floor corner
  0 .. 0.23, two ARCH.SPACE low = high (T-795). Disposal: index = 10.476796 m3 RELEASED ESTIMATE; blank_lines.py /
  build_boq.py overlay MAIN_FILL_ALL unconditionally -> shows HELD 105.6 .. 115.5 (T-796 fixes tool + reconciles).
- Open differences: beams 76.19 vs 65.97 (+15.5 %, UNRESOLVED 3.48); columns 33.83 vs 28.55 (planted P.C);
  upturn 228.99 vs 194 (his lump -11.89 UNRESOLVED named); his 1F projections 41.25 m2 UNRESOLVED (no row unless his
  sheet names it); cornice +0.70 % pending Checker.
- Number (b): decided 16:13 = workbook Compare sheet (build_boq.py), not alsenan_scoreboard.py.

## Live rows (16:13)
- READY: T-788 (EVIDENCE: worker 2 print script first). TODO: W1 T-791, T-796, T-797; W2 T-788 ev., T-795, T-783,
  T-774 (after T-773); W3 T-770 r10, T-793, T-773 (owner authorises). PAUSED: T-382, T-664, T-450 p2, T-451, T-472.
  IN PROGRESS: T-180. Next free T-798.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it. Write "Nth in queue (not blocked ...)"; never the words
  "after T-" for pure queue order (makes the row WAITING). Time stamps: from `date -u` at writing, never ahead.
- Status word FIRST; 7 cells (id | gate | lane title | description | status | branch | verdict); no '|' in a cell.
  MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet all RC on Alsenan sections -> STR.CONC.PARAPET whole, block = complement (R-T789-1); stair concrete +
  formwork S, finish faces A; boundary wall: under-building band = S, fence-run foundation = S, fence block / plaster
  above N.G. = A. Dome extrados = roof layers family; flat roof keeps footprint deduction. ARCH.WALL_PANEL / VOLUME =
  REFERENCE views of MAS.BLOCK (block m2 once, T-790). Upturn door / glazing gaps = transition / termination lines (T-794).
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1, R-T789-1, MARK_BY_OUTLINE_FIT_V1.

## Blockers / open owner items
- DESIGNER_QUESTIONS (19 incl. D-DOME, 1F parapet ~1.63 vs 1.20) with the owner; ORR-007 stair skirting; Q-34 2F top
  roof; release switch T-773 is his. Scout paused. Wrapper run allow-list refuses older research scripts for the Checker.
