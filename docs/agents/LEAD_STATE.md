# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 80e27c10..`,
`git -C .work/board log <board commit of this run>..`, `git log fc03a1fb..` on main, RUN_LOG lines after 04:13Z 12 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 80e27c10 (T-728). Merges since 302e002d: cfca9394 T-724, 8ea912b5 T-727, 931dc8d9 T-722
  (Gate B PASS, V3.0.73 c5a0b128 / master 1.74.0 via fa186f4d, NOT RELEASED), b20fe25c T-725, 63720169 T-726,
  80e27c10 T-728. Released V2.9 + G. No owner commit.
- main: fc03a1fb. PR #6 decode fix open. Last Lead run: 2026-11-12 04:13 UTC (session_01E6cPnc3uB4cgfr1fx9Jyw1).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); (2a) join approved
  work first; (2b) version reservation in the row; (2c) ONE designer list DESIGNER_QUESTIONS.md (Lead keeps, owner
  sends; per item); (2d) idle slots draft the 38 missing families, one per run.
- OWNER DECISION 2026-11-09 18:30 order: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> missing families (MEP last). UPM untouched.
- Hub order: T-717 plaster / paint + bands + voids + shaft row apart (V3.0.74) -> T-729 formwork (T-714 + T-724 +
  T-725 + T-732; V3.0.75) -> beads (T-728) / tiles H3 (T-733) / WP+roof H4 (T-734 record) / earthworks (T-708).

## Baseline (V3.0.73)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN bd 11.80007 .. 15.5015 + tank pair LOWER_ONLY 0.3287 each;
  GB beside >= 5.099845; ring >= 0.115155; lift >= 1.903; LINTEL AT_MOST 1.322146; strips blank (D-05/D-26).
- MAS: 18 blank lines one-ended beside. FIN.PLASTER like for like -14.83 .. -8.82 % with his 13.50 row apart
  (NO_FACE). Floor 1F L-b06400d4 33.411036 ENGINE_RIGHT. WP 53 HELD + 5 MISSING. Beads 116 HELD.

## Live rows (04:20)
- READY: none. CLAIMED: none.
- TODO: S: T-731 (W1 FIRST), T-732, T-708; A: T-720 (W2 FIRST), T-733, T-734; I: T-717 (W3 FIRST), T-730.
  QUEUED: T-729 (after T-717, T-732), T-363, T-424, T-314, T-364, T-513, T-502, T-509. PARKED: T-664, T-382.
  IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S: T-731, T-732, T-708, T-363, T-424; A: T-720, T-733, T-734, T-314, T-364, T-513, T-502;
  I: T-717, T-730, T-729, T-509. Queue check 19 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-717 Gate B (plaster / paint V3.0.74); SCOREBOARD v2 restated with the plaster ruling (row apart).
2. T-731 MS1-L coherent reading + ST-01 flights re-measure; T-732 formwork of moved members.
3. T-729 formwork Gate B (V3.0.75) right after T-717.
4. T-733 tiles H3 readiness; T-734 WP roof downgrade record draft.
5. T-720 gross floor area; T-730 wiring map r5; T-708 earthworks r3.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; status word FIRST; 7 cells; never a '|'
  inside a cell. `board check` pulls first: commit before. Times only from `date -u`.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once; corner beads -> plaster; wet band above ceiling and double-height bands -> plaster; stair
  concrete + its formwork = S, stair finish faces = A; voids B2-05 owned by the register (A), deducted once (union);
  blank-beam bounds below the slab soffit only (R-CONC-OWN-1).
- Rulings: R-T704-2; F-T705-1; F-T705-2 roof downgrade only by Checker record; rule conflict moves no quantity;
  scoreboard like for like; a removed D-id is never cited; 2026-11-12 04:20: plaster like-for-like shows his 13.50
  NO_FACE row apart (never added, never removed from his total); an incoherent alternative reading is never a
  designer candidate.
- Lessons: union-not-sum and L-T703-1 ADOPTED 04:20; L-T727-1 (check the live record) and F-T725-1 (one coherent
  stair reading) PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form. Q-34 2F top roof. Decode PR #6 open (workers re-encode by hand); scheduled-task
  edits approved but not possible under repo settings. Scout paused. M3 estimate 14 Nov.
  Designer items keep lines HELD, never block integration.
