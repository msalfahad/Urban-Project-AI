> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log da27f52f..origin/...`, board
commits after this run's commit, RUN_LOG lines after 12:16Z 14 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`. Take every time stamp from `date -u` at the moment of writing.

## Last seen
- engine origin head: da27f52f (T-782 merge). Merged since 08:12: T-770 r7 f9159fac + 60d7202a (V3.0.84 / 1.84.0),
  T-789 7113111b, T-787 21646f39, T-770 r8 c5b79f10 + 65813f8d (V3.0.85 / 1.85.0), T-784 7b5c5382, T-781 44219b97,
  T-782 da27f52f. No owner engine commit; no new OWNER_SESSION_CHANGES row since 13 Nov 15:00.
- Last Lead run: 2026-11-14 12:16 UTC (session_01E6cPnezGV6nNnxiDAVKD6g). Drive readable; no new files (newest 21 Oct).
- Candidate of record ARCH_TAKEOFF_V3.0.85 (master 1.85.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 12:19)
r9 V3.0.86 / 1.86.0 = merged T-787 dome extrados + T-789 parapet / masonry fix rows + any merged of T-786 / T-790 /
T-791 / T-792 / T-788 / T-794 at claim (max three family groups) -> r10 = the rest.

## Fill / difference state
- Blank non-rebar: 124 (V3.0.83) -> 56 (V3.0.84) -> 44 (V3.0.85 package count; blank_lines.py: 40 blank = blockwork
  ARCH.WALL_PANEL / VOLUME 26 + stairs 14, plus 8 HELD ranges). T-790 / T-791 close the 40.
- Open differences: concrete +7.14 beams / -5.84 other (T-786); schedule vs candidate columns 1F -11.4 % (T-792);
  cornice -29.1 % (T-788); roof upturn +20.1 % (T-794); his 1F projections 41.25 m2 UNRESOLVED named (no row: T-789
  found no element; revisit only if the freelancer sheet names it).
- Closed to causes: masonry -22.2 %, plaster, roof finish -16 %, roof membrane +13.7 % (dome curvature), parapet
  masonry (RC, block 0), wet-room WP +18.8 %, windows -14 %, fence, ext render -28.3 % RULE_DIFF.
- Not yet assigned: wall-tile edge range 0 .. 73.1 lm (T-771 NEW line), disposal range (owner MAIN FILL basis).

## Live rows (12:19)
- READY: none. TODO: W1 T-786, T-792, T-791; W2 T-790, T-788, T-783, T-774 (after T-773); W3 T-770 r9, T-793,
  T-794, T-773 (owner authorises). DONE this run: T-424, T-502 (r7). PAUSED: T-382, T-664, T-450 p2, T-451, T-472.
  IN PROGRESS: T-180.
- Queue check 12 actionable, 0 flagged, 0 stall. Next free T-795.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it. Write "Nth in queue (not blocked ...)"; never the words
  "after T-" for pure queue order (makes the row WAITING). Time stamps: from `date -u` at writing, never ahead.
- Status word FIRST; 7 cells (id | gate | lane title | description | status | branch | verdict); no '|' in a cell.
  MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet: all RC on Alsenan sections -> STR.CONC.PARAPET whole, block family = complement (R-T789-1); stair concrete +
  formwork S, finish faces A; boundary wall: under-building band = S (Q-28 A), fence-run foundation = S, fence block /
  plaster above N.G. = A. Dome extrados = roof layers family (T-787), flat roof lines keep the footprint deduction.
  ARCH.WALL_PANEL / VOLUME = views of MAS.BLOCK walls: block m2 counted once (T-790 decides reference vs subtotal).
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1; R-T789-1 proposed by worker 2.

## Blockers / open owner items
- DESIGNER_QUESTIONS (19 incl. D-DOME; item 5 now also the 1F parapet height ~1.63 vs 1.20) with the owner; ORR-007
  stair skirting; Q-34 2F top roof; release switch T-773 is his.
- Scheduled-task frequency change recommended in DELIVERY_MODE s.7 (owner only). Scout paused (last run failed 27 Oct).
