> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log d3367f7e..origin/...`, board
commits after this run's commit, RUN_LOG lines after 08:12Z 14 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`. Take every time stamp from `date -u` at the moment of writing.

## Last seen
- engine origin head: d3367f7e (T-772 merge). Merged since 04:20: T-770 r5 26a82725 (V3.0.82 / 1.82.0), T-779 0d3c07bb +
  92b00ef0, T-780 09f8f0b2, T-770 r6 35963c4d + eab65f0e (V3.0.83 / 1.83.0), T-785 fcdc94cb, T-772 d3367f7e. No owner
  engine commit. Main chat 04:34 daily audit: fill_from_index.py formwork step fixed (overlay formwork dropped, T-762).
- Last Lead run: 2026-11-14 08:12 UTC (session_01E6cPneLBXjpenSNg9tg7SE). Drive readable; no new files (newest 21 Oct).
- Verifier run 07:51 (session ...nc1RcFNw...) still open at 08:16 (merged T-785, T-772; T-770 r7 next). If no final
  line by the next run, report it INCOMPLETE.
- Candidate of record ARCH_TAKEOFF_V3.0.83 (master 1.83.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 08:15)
r7 V3.0.84 / 1.84.0 (READY; Checker's own Drive chain = evidence; folded T-424 / T-502 close with it) -> r8 V3.0.85 /
1.85.0 = T-760 ext render / paint (81 lines, never wired) + T-771 spatter line + T-780 roof + T-785 WP, worker's own
Drive chain required -> r9 = fix rows of T-786..T-789 as they merge.

## Fill / difference state
- Blank non-rebar: 211 (V3.0.82) -> 124 (V3.0.83) -> 56 (V3.0.84 READY); r8 about -12 more; then parapet / dome rows.
- Open differences: concrete UNRESOLVED +7.14 beams / -5.84 other (T-786); cornice -29.1 % (T-788); his 1F
  projections 41.25 m2 + parapet masonry HELD 0..101.46 (T-789); dome extrados ~83.2 m2 no line (T-787).
- Closed to causes: masonry -22.2 %, plaster, roof -16 %, wet-room WP +18.8 %, windows -14 %, fence, ext render RULE_DIFF.

## Live rows (08:16)
- READY: T-770 r7. TODO: W1 T-787, T-784, T-786; W2 T-789, T-781, T-788, T-783 (after T-781 + T-782), T-774 (after
  T-773); W3 T-770 r8, T-782, T-773 (owner authorises). QUEUED (folded): T-424, T-502 (close with r7).
  DONE this run: T-750, T-509 (r5), T-363, T-364, T-513 (r6). PAUSED: T-382, T-664, T-450 p2, T-451, T-472.
  IN PROGRESS: T-180.
- Queue check 14 actionable, 0 flagged, 0 stall. Next free T-790.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it. Write "Nth in queue (not blocked ...)" not "after T-nnn"
  for pure queue order: "after T-" makes the row WAITING.
- Status word FIRST; 7 cells (id | gate | lane title | description | status | branch | verdict); no '|' in a cell.
  MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; boundary wall: under-
  building band = S (Q-28 A), fence-run foundation = S, fence block / plaster above N.G. = A family via T-769 / T-776.
  Column / beam joint per T-777 / T-778; dome extrados = roof layers family (T-787), flat roof lines keep the footprint
  deduction (no double count).
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1. Noted, not filed: 'a merged fix-row
  set can be skipped by the wiring rounds' (T-760 found at r7): the Lead checks every merged fix-row set against the hub.

## Blockers / open owner items
- DESIGNER_QUESTIONS (18) with the owner (+ dome build-up when T-787 adds it); ORR-007 stair skirting; Q-34 2F top
  roof; release switch T-773 is his.
- Scheduled-task frequency change recommended in DELIVERY_MODE s.7 (owner only). Scout paused (last run failed 27 Oct).
