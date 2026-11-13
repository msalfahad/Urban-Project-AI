> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log f8319feb..origin/...`, board
commits after this run's, RUN_LOG lines after 20:13Z 13 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: f8319feb (T-769 merge). Merged since 16:31: T-762 43eae30a, T-767 9de1dcd5, T-764 61a65c42,
  T-314 r4 57e4a49f + promotion e8170c56 (master 1.80.0, candidate V3.0.79), T-769 f8319feb. No owner engine commit.
- Last Lead run: 2026-11-13 20:13 UTC (session_01E6cPndvE82FTgmHLajsoee). Drive readable; no new private files
  since 12 Nov (no photos). Verifier run 19:51 was still open at 20:20 (T-769 merged; T-770 r2 under check).
- Candidate of record ARCH_TAKEOFF_V3.0.79 (master 1.80.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 20:20)
T-770 r2 (V3.0.81 / 1.81.0, READY) -> T-770 r3 (T-764 + T-767 + T-769 sets, V3.0.82 / 1.82.0, stack allowed)
-> T-770 r4 (T-763 r2 / T-765 / T-766 as they merge). T-750 folded into r3 (QUEUED, closes with r3).

## Fill state
- V3.0.81 (READY): blank non-rebar 691 -> 295; concrete +58.42 m3 + 1.00 SAFETY; formwork 2,226.9 m2; roof 248.8 vs
  285 (-12.7 %).
- Merged fix rows not wired: T-764 earthworks (exc 336.5, disposal 9.0 m3; boundary 47.09 PROVISIONAL), T-767 WP 50
  -> 0, T-769 fence / site 37 -> 0.
- Freelancer differences open: beams +18 % (T-777), fence block +28.3 % (T-776), plaster +3.7 % (T-763 r2), roof
  -12.7 %; ext render -26..-31 % RULE_DIFFERENCE.

## Open checks for next run
- Checker verdict on T-770 r2 (and workbook rebuilt). If MERGED, T-770 r3 claimable at once.
- F-V764-1 boundary base 0.90 (ST p.14 A-A) vs 0.40 dig: T-776 decides per run type; owner only if p.2 and p.14
  contradict on one run.
- Owner's fill_from_index.py formwork step still double counts (owner fix; NEEDS FIXING).

## Live rows (20:20)
- READY: T-770 r2. TODO: W1 T-757 (sharpened: ranges -> points, 0.05 rule, reuse T-761 IGNORED_SMALL), T-776,
  T-777 (after T-757), T-772; W2 T-763 r2, T-765, T-766, T-768, T-774; W3 T-770 r3, T-771, T-775, T-773.
  QUEUED (folded): T-363, T-364, T-424, T-502, T-509, T-513, T-750. PAUSED: T-382, T-664, T-450 p2, T-451, T-472.
  IN PROGRESS: T-180.
- Queue check 20 actionable, 0 flagged, 0 stall. Next free T-778.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it (or run queue_check.py from the venv).
- Status word FIRST; 7 cells; no '|' in a cell. MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; boundary wall: under-
  building band = S (Q-28 A), fence-run foundation = S, fence block / plaster above N.G. = A family via T-769.
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1.

## Blockers / open owner items
- DESIGNER_QUESTIONS (18) with the owner; ORR-007 stair skirting; Q-34 2F top roof; release switch T-773 is his.
- Scheduled-task frequency change recommended in DELIVERY_MODE s.7 (owner only). Scout paused.
