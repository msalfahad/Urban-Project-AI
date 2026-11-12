# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 6143f30d..`,
`git -C .work/board log <board commit of this run>..`, `git log fc03a1fb..` on main, RUN_LOG lines after 08:14Z 12 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 6143f30d (T-730). Merges since 80e27c10: e9878f39 T-731, 067b0035 T-720, 35c0c09e T-732,
  7146583d T-733, 6143f30d T-730 (all research, unwired). T-717 Gate B REJECTED r1 (t459 binding). No owner commit.
- main: fc03a1fb. PR #6 decode fix open. Last Lead run: 2026-11-12 08:14 UTC (session_01E6cPnbNTrqEhX5GFJq6qcA).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); (2a) join approved
  work first; (2b) version reservation in the row; (2c) ONE designer list DESIGNER_QUESTIONS.md; (2d) idle slots draft
  missing families, one per run.
- OWNER DECISION 2026-11-09 18:30 order: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> missing families (MEP last). UPM untouched.
- Hub order: T-717 r2 (V3.0.74) -> T-729 formwork + C10 (V3.0.75) -> T-736 beads H2a + ceiling r3 (V3.0.76) -> T-738
  tiles H3 + H3s minus ORR-007 (V3.0.77) -> T-314 r3 (after T-737) -> H4 WP (after T-734) -> H5 (after T-708).

## Baseline (V3.0.73, unchanged)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN 11.80007 .. 15.5015; GB beside >= 5.099845; ring >= 0.115155;
  lift >= 1.903; LINTEL AT_MOST 1.322146; strips blank. MS1-L high 1.023763 (T-731, unwired).
- FIN.PLASTER like for like -14.83 .. -8.82 % (his 13.50 row apart). T-717 r1 deltas (pending r2): plaster held
  -25.017279 / +1.474537, paint +3.344721 / +27.675121 m2. B2-03 gross 278.266 / 209.839 / 55.080 m2 VERIFIED.
- FW moved columns 102.914777 .. 127.151372 m2 beside (T-732). Beads 116 HELD. WP 53 HELD + 5 MISSING.

## Live rows (08:16)
- READY: none. CLAIMED: none.
- TODO: S: T-735 (W1 FIRST), T-708; A: T-734 (W2 FIRST), T-737; I: T-717 r2 (W3 FIRST), T-739.
  QUEUED: T-729 (after T-717), T-736 (after T-729), T-738 (after T-736), T-314 r3 (after T-737, T-736), T-363, T-424,
  T-364, T-513, T-502, T-509. PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S: T-735, T-708, T-363, T-424; A: T-734, T-737, T-314, T-364, T-513, T-502; I: T-717, T-739, T-729,
  T-736, T-738, T-509. Queue check 19 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-717 r2 Gate B (rebuild t459 binding by tool, L4) -> V3.0.74; SCOREBOARD v2 restated on merge.
2. T-735 formwork conflict decider (6 column lines + cap-0 L-867e155d) before / for T-729.
3. T-729 formwork + concrete round 10 Gate B (V3.0.75).
4. T-739 all-trade aggregation statement (milestone scorecard); T-734 WP roof downgrade record.
5. T-737 exterior plaster readiness (unblocks T-314 r3 and 43 H2b beads); T-708 earthworks r3.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; it parses every T-id AFTER 'LANE ORDER:' in
  that line into the last lane, so write nothing with task ids after the lane order; a row text 'after T-xxx' makes it
  WAITING. Status word FIRST; 7 cells; never a '|' inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once; corner beads -> plaster; wet band above ceiling and double-height bands -> plaster; stair
  concrete + formwork = S, stair finish faces = A; voids B2-05 owned by the register (A), deducted once (union);
  blank-beam bounds below the slab soffit only (R-CONC-OWN-1). B2-03 = register family without a BOQ line (08:16).
- Rulings: R-T704-2; F-T705-1; F-T705-2 roof downgrade only by Checker record; rule conflict moves no quantity;
  scoreboard like for like; a removed D-id is never cited; plaster like-for-like shows his 13.50 NO_FACE row apart;
  an incoherent alternative reading is never a designer candidate; a CONFLICT line is never picked, decider named.
- Lessons: union-not-sum, L-T703-1, F-T725-1 ADOPTED; L-T727-1, L-T717-1, F-T730-1/-2 PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Decode PR #6 open (workers re-encode by
  hand); scheduled-task edits approved but not possible under repo settings. Scout paused. M3 estimate 14-16 Nov.
  Designer items keep lines HELD, never block integration.
