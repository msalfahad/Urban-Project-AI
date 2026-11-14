> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log eff624c2..origin/...`, board
commits after f7341372, RUN_LOG lines after 04:11Z 14 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: eff624c2 (T-778 merge). Merged since 00:20: T-770 r4 ba6fafe0 (V3.0.81 / master 1.81.0 promoted),
  T-777 + T-766 + T-771 (88e4b912), T-768 eda8232a, T-778 eff624c2. No owner engine commit.
- Owner main chat 14 Nov 00:28 / 00:35: ACCURACY_PLAN_2026-11-14.md + PROCEED_PLAN_2026-11-14.md (+ reference/
  EXTERNAL_HANDOFF_2026-11-14.md). Acted on: GENERALISE rows T-781..T-784, T-772 sharpened. No OWNER_SESSION_CHANGES row.
- Last Lead run: 2026-11-14 04:11 UTC (session_01E6cPndgLT5zk1Mx2na7rb1). Drive readable; newest project file 21 Oct
  (no photos). Verifier run 03:51 (session ...nbK7x1...) still open at 04:20 (merged T-778; T-770 r5 next). If no
  final line by the next run, report it INCOMPLETE. Verifier 23:51 run closed by its 01:05 line.
- Candidate of record ARCH_TAKEOFF_V3.0.81 (master 1.81.0). NOT RELEASED; V2.9 + route G untouched.

## Hub order (LEAD NOTE 04:14)
T-770 r5 (V3.0.82 / 1.82.0, READY; Checker's own Drive chain is the evidence: the worker's did not finish) -> r6
V3.0.83 / 1.83.0 = T-757 + T-763 + T-765 + 1 deferred T-776 row (F-V765-1 text fix) -> r7 V3.0.84 / 1.84.0 = T-766 +
T-768 + T-771. Folded rows close: T-750 / T-509 with r5; T-363 / T-364 / T-513 with r6; T-424 / T-502 with r7.

## Fill / difference state
- Blank non-rebar: 295 (V3.0.81) -> 211 (V3.0.82 READY); r6 + r7 carry the rest.
- Concrete 406.79 vs 352.44 (+15.4 %) closed to causes (T-777 / T-778): scope +55.47; UNRESOLVED +7.14 beams /
  -5.84 other; RULE joint ownership -8.32 / +5.78.
- Masonry -22.2 % / plaster +5.8 %: T-779. Roof -10 / -12.7 %: T-780. Wet-room WP +19 % + upturn unit: T-785.
  Ext doors 12 vs 6: inside T-781. Cornice 302.9 vs 427.5 lm (-29.1 %) UNRESOLVED: next difference row (not yet made).
- Fence explained; ext render -26..-31 % RULE_DIFFERENCE; windows -14.4 % split to 0.

## Open checks for next run
- Checker verdict on T-770 r5. If MERGED, T-770 r6 claimable at once.
- New GENERALISE rows: check each claims only its new files (tools/urban_boq_run.py, engine/source/opening_table_v1.py,
  project_inputs_v1.py, schedule_tables_v1.py, wall_band_masonry_v1.py); no candidate line may change in them.
- Owner's fill_from_index.py formwork step still double counts (owner fix; NEEDS FIXING).

## Live rows (04:20)
- READY: T-770 r5. TODO: W1 T-780, T-772, T-784; W2 T-779, T-785, T-781, T-783 (after T-781 + T-782), T-774 (after
  T-773); W3 T-770 r6/r7, T-782, T-773 (owner authorises). MERGED since 00:20: T-777, T-766, T-771, T-768, T-778.
  QUEUED (folded): T-363, T-364, T-424, T-502, T-509, T-513, T-750. PAUSED: T-382, T-664, T-450 p2, T-451, T-472.
  IN PROGRESS: T-180.
- Queue check 19 actionable, 0 flagged, 0 stall. Next free T-786.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
  `board check` pulls first: commit edits before running it. Write "Nth in queue (not blocked ...)" not "after T-nnn"
  for pure queue order: "after T-" makes the row WAITING.
- Status word FIRST; 7 cells; no '|' in a cell. MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; boundary wall: under-
  building band = S (Q-28 A), fence-run foundation = S, fence block / plaster above N.G. = A family via T-769 / T-776.
  Column / beam joint: engine gives it to the beam / column per T-777 / T-778; freelancer stops columns under beams
  (RULE_DIFFERENCE; compare beams + columns together).
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1; T-778 'a mark tagged once may be
  drawn more than once' noted, not filed.

## Blockers / open owner items
- DESIGNER_QUESTIONS (18) with the owner; ORR-007 stair skirting; Q-34 2F top roof; release switch T-773 is his.
- Scheduled-task frequency change recommended in DELIVERY_MODE s.7 (owner only). Scout paused (last run failed 27 Oct).
