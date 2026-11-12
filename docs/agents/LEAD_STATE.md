# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 302e002d..`,
`git -C .work/board log <board commit of this run>..`, `git log fc03a1fb..` on main, RUN_LOG lines after 00:14Z 12 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 302e002d (T-719). Merges since a4e4277a: dfeb0240 T-712, 17aaab4b T-716, 9e1ed6c5 T-721,
  8052ca51 T-718, da1a8906 T-703 (Gate B PASS, V3.0.72 f9578744 / master 1.73.0 via 9c46c05d, NOT RELEASED),
  e6ebe28a T-714, 5d00f738 T-723, 302e002d T-719. Released V2.9 + G. No owner commit.
- main: fc03a1fb. PR #6 decode fix open. Last Lead run: 2026-11-12 00:14 UTC (session_01E6cPndtVCL8zKTzDKQehC7).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); (2a) join approved
  work first; (2b) version reservation in the row; (2c) ONE designer list DESIGNER_QUESTIONS.md (Lead keeps, owner
  sends; now per item from T-716); (2d) idle slots draft the 38 missing families, one per run.
- OWNER DECISION 2026-11-09 18:30 order: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> missing families (MEP last). UPM untouched.
- Hub order: T-722 concrete round 9 (V3.0.73) -> T-717 plaster / paint + bands + T-719 voids (V3.0.74) -> formwork
  (T-714 rows + T-724) / beads (T-728 ledger) / tiles H3 (T-727 input) / WP+roof H4 (needs Checker downgrade record
  for roof 115.832) / earthworks H5.

## Baseline (V3.0.72)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN 27 bd 11.80007 .. 15.5015 + tank pair LOWER_ONLY 0.3287 each;
  LINTEL 16 AT_MOST beside (family 1.322146); BEAM 14 bd 5.9832 .. 8.4127 + 12 blank (T-721: ring AT_LEAST 0.115155,
  11 strips BLANK_NAMED); GROUND_BEAM 9 bd + 20 blank (T-712: 17 AT_LEAST 5.099845, 3 blank D-35); NECK / STAIR /
  PARAPET / LIFT bounds T-711. All of T-707/711/712/721 unwired until T-722.
- MAS: 18 blank lines one-ended beside (T-703). FIN.PLASTER like for like -15.81 .. -9.88 %; shaft 13.50 m2
  UNRESOLVED (T-726). Floor 1F L-b06400d4 33.411 -> 33.468 candidate (T-727). WP 53 HELD + 5 MISSING.

## Live rows (00:16)
- READY: none. CLAIMED: none.
- TODO: S: T-724 (W1 FIRST), T-725, T-708; A: T-727 (W2 FIRST), T-726, T-720; I: T-722 (W3 FIRST), T-728.
  QUEUED: T-717 (after T-722), T-363, T-424, T-314, T-364, T-513, T-502, T-509. PARKED: T-664, T-382.
  IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S: T-724, T-725, T-708, T-363, T-424; A: T-727, T-726, T-720, T-314, T-364, T-513, T-502;
  I: T-722, T-728, T-717, T-509. Queue check 19 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-722 Gate B (concrete round 9, V3.0.73); SCOREBOARD v2 restated after it.
2. T-724 checker findings (ring depth, soffit ratio, L-fb7a6431, strip in no line); T-725 stair formwork.
3. T-717 plaster / paint + voids (V3.0.74) right after T-722.
4. T-727 void deductions (floor +0.057 m2, ceiling 16.005 risk) -> tiles H3; T-726 shaft 13.50 m2.
5. T-728 bead ledger -> H2a / H2b; T-720 gross floor area; T-708 earthworks r3.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; status word FIRST; 7 cells; never a '|'
  inside a cell. `board check` pulls first: commit before. Times only from `date -u`.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once; corner beads -> plaster; wet band above ceiling and double-height bands -> plaster; stair
  concrete + its formwork = S, stair finish faces = A; voids B2-05 owned by the register (A), deducted once (union) by
  floor / ceiling, never from gross B2-03; blank-beam bounds below the slab soffit only (R-CONC-OWN-1).
- Rulings: R-T704-2 AT_MOST on one geometry stopper to stopper; F-T705-1 bead takes its host's height state;
  F-T705-2 roof downgrade only by Checker record; rule conflict moves no quantity; scoreboard like for like;
  2026-11-12: a removed D-id (D-56) is never cited, the line names the live item.
- Lessons: L-T716-1 and F-V715-1 ADOPTED 00:16; union-not-sum (T-719) and L-T703-1 PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form. Q-34 2F top roof. Decode PR #6 open (workers re-encode by hand); scheduled-task
  edits approved but not possible under repo settings. Scout paused. M3 estimate 13-14 Nov (masonry done 12 Nov).
  Designer items keep lines HELD, never block integration.
