> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log 3b9f35a6..origin/...`, board
commits after aa666824, RUN_LOG lines after 00:12Z 14 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 3b9f35a6 (CODEMAP after T-776 c4d45e9e + T-765 4b3ad8e4). Merged since 20:20: T-763 r2 2c6a2822,
  T-757 951682c5, T-776, T-765 (all fix rows, unwired). No owner engine commit. Owner main chat on the board 23:41:
  Compare sheet tweak + URBAN_VS_FREELANCER_2026-11-13.md (no OWNER_SESSION_CHANGES row; data only).
- Last Lead run: 2026-11-14 00:12 UTC (session_01E6cPneYnoad5ZL7ALxM8BL). Drive readable; no new private files since
  12 Nov (no photos). Verifier run 23:51 still open at 00:20 (merged T-776 / T-765; T-770 r4 next). If it has no final
  line by the next run, report it INCOMPLETE.
- Candidate of record ARCH_TAKEOFF_V3.0.79 (master 1.80.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 00:20)
T-770 r4 (V3.0.81 / 1.81.0, READY) -> r5 V3.0.82 / 1.82.0 = T-764 + T-767 + T-769 with T-776 superseding the boundary
lines (F-V776-1 named check <= 0.75 m3) -> r6 V3.0.83 / 1.83.0 = T-757 + T-763 + T-765 (F-V765-1 text fix) -> r7
T-766 / T-768 / T-777. Folded rows close: T-750 / T-509 with r5; T-363 / T-364 / T-513 with r6; T-424 / T-502 with r7.

## Fill / difference state
- V3.0.81: blank non-rebar 691 -> 295; formwork 2,226.9 m2.
- Concrete after T-757: 405.60 + 1.20 SAFETY vs 352.4 (+15.1 %): beams +13.15 (T-777), rest ~+40 (T-778).
- Masonry 981.4 vs 1,260.7 m2 (-22.2 %), plaster ex wet 1,236.8 vs 1,169.1 (+5.8 %): T-779.
- Roof membrane 255.4 vs 285 (annex ~54.9 no line), finish 248.8 vs 285: T-780.
- Fence block explained (residual 0); ext render -26..-31 % RULE_DIFFERENCE.

## Open checks for next run
- Checker verdict on T-770 r4 (workbook rebuilt). If MERGED, T-770 r5 claimable at once.
- Owner's fill_from_index.py formwork step still double counts (owner fix; NEEDS FIXING).

## Live rows (00:20)
- READY: T-770 r4. TODO: W1 T-777, T-778, T-780, T-772 (after FILL); W2 T-766, T-768, T-779, T-774 (after T-773);
  W3 T-770 r5/r6, T-771, T-773 (owner authorises). DONE: T-775 (owner session).
  QUEUED (folded): T-363, T-364, T-424, T-502, T-509, T-513, T-750. PAUSED: T-382, T-664, T-450 p2, T-451, T-472.
  IN PROGRESS: T-180.
- Queue check 19 actionable, 0 flagged, 0 stall. Next free T-781.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it.
- Status word FIRST; 7 cells; no '|' in a cell. MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; boundary wall: under-
  building band = S (Q-28 A), fence-run foundation = S, fence block / plaster above N.G. = A family via T-769 / T-776.
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1; T-776 'a typical section through a
  pad gives the pad width, not the run width' noted, not filed.

## Blockers / open owner items
- DESIGNER_QUESTIONS (18) with the owner; ORR-007 stair skirting; Q-34 2F top roof; release switch T-773 is his.
- Scheduled-task frequency change recommended in DELIVERY_MODE s.7 (owner only). Scout paused.
