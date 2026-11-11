# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log a4e4277a..`,
`git -C .work/board log <board commit of this run>..`, `git log fc03a1fb..` on main, RUN_LOG lines after 20:13Z 11 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: a4e4277a (T-715). Merges since 8294c146: 1e06f656 T-711, aa4d8979 T-713, b211b3a2 T-704 r2
  (Gate B PASS, V3.0.71 fc0bd98f / master 1.72.0, NOT RELEASED), a4e4277a T-715. Released V2.9 + G. No owner commit.
- main: fc03a1fb. PR #6 decode fix open. Last Lead run: 2026-11-11 20:13 UTC (session_01E6cPndcKMVFz6NvBpbpGdT).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); (2a) join approved
  work first; (2b) version reservation in the row; (2c) ONE designer list DESIGNER_QUESTIONS.md (Lead keeps, owner
  sends); (2d) idle slots draft the 38 missing families, one per run.
- OWNER DECISION 2026-11-09 18:30 order: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> missing families (MEP last). UPM untouched.
- Hub order (Lead 20:25): T-703 masonry + T-713 bounds (V3.0.72) -> T-722 concrete round 9 T-707/T-711/T-712
  (V3.0.73, needs T-712 MERGED) -> T-717 plaster / paint + bands (V3.0.74) -> formwork T-638 rows / beads H2a /
  T-314 / tiles H3 / WP+roof H4 (needs Checker downgrade record for roof 115.832) / earthworks H5.

## Baseline (V3.0.71)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN 27 bd 11.80007 .. 15.5015 + tank pair LOWER_ONLY 0.3287 each;
  LINTEL 24 bd 1.361 .. 2.0506 + 21 blank (16 AT_MOST beside, family 1.322146); BEAM 14 bd 5.9832 .. 8.4127 + 12
  blank (T-721); GROUND_BEAM 9 bd 1.1784 .. 5.0968 + 20 blank (T-712 READY: 17 AT_LEAST 5.099845, 3 blank);
  NECK / STAIR / PARAPET / LIFT blanks: T-711 bounds merged, unwired (T-722). Slab 1F -0.556333 UNRESOLVED.
- FIN.PLASTER like for like -15.81 .. -9.88 %; shaft 13.50 m2 UNRESOLVED. WP 53 HELD + 5 MISSING. MAS.BLOCK 15 HELD
  blank (T-696 + T-713 bounds unwired -> T-703). Stair finishes 85 lines by cause (T-715), F-V715-1 open (T-718).

## Live rows (20:25)
- READY: T-712 (CHECKER-RUNS, Gate A first), T-716 (CHECKER-RUNS, second). CLAIMED: none.
- TODO: S: T-721 (W1 FIRST), T-714, T-708; A: T-718 (W2 FIRST), T-719, T-720; I: T-703 (W3 FIRST), T-723.
  QUEUED: T-722 (after T-703 + T-712 MERGED), T-717 (after T-722), T-363, T-424, T-314, T-364, T-513, T-502, T-509.
  PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S: T-721, T-714, T-708, T-363, T-424; A: T-718, T-719, T-720, T-314, T-364, T-513, T-502;
  I: T-703, T-723, T-722, T-717, T-509. Queue check 22 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-703 Gate B (masonry + T-713), SCOREBOARD v2 restated after it.
2. T-712 Gate A then T-722 concrete round 9.
3. T-721 blank beams; T-714 formwork limits.
4. T-716 merge -> DESIGNER_QUESTIONS.md per item (settle 19 uncited seed D-ids, D-56 cited by 3).
5. T-717 plaster / paint; T-718 stair finishes r2; T-719 / T-720 missing families.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; status word FIRST; 7 cells; never a '|'
  inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once; corner beads -> plaster; wet band above ceiling and double-height bands -> plaster; stair
  concrete = S, stair finish faces = A; voids B2-05 owned by the register (A), deducted once by floor / ceiling,
  never from gross B2-03; blank-beam bounds below the slab soffit only (R-CONC-OWN-1).
- Rulings: R-T704-2 AT_MOST on one geometry stopper to stopper; F-T705-1 bead takes its host's height state;
  F-T705-2 roof downgrade only by Checker record; rule conflict moves no quantity; scoreboard like for like.
- Lessons 20:25: T-706 ADOPTED; L-T716-1 (cause as id) and F-V715-1 PROPOSED; T-709 band PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form. Q-34 2F top roof. Decode PR #6 open (cost W2 a drawing read 18:54); L4 about
  1 h of a Checker run (NEEDS FIXING, owner). Scheduled-task edits approved but not possible under repo settings.
  Scout paused. M3 estimate 13-14 Nov. Designer items keep lines HELD, never block integration.
