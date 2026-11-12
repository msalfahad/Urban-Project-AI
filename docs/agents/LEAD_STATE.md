# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 1370c295..`,
`git -C .work/board log <board commit of this run>..`, `git log d24e4497..` on main, RUN_LOG lines after 16:14Z 12 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 1370c295 (T-742). Merges since a91a1dfe: 01f060bd T-741, 0f0e0cd0 T-740, 0d3bf6a1 T-739 r2,
  1370c295 T-742. Checker record DG-a429c160 issued (L-636fd3ff 115.832 m2 RELEASED -> HELD). No owner commit.
- main: d24e4497 unchanged. Last Lead run: 2026-11-12 16:14 UTC (session_01E6cPnerJ1msLuZNiTBaT8V).
- Verifier run session_01E6cPndRu2x62YBGWB8KoeH STARTED 15:51 (T-729 Gate B + T-743), open at 16:20: check its final line.
- Drive: no file in the private folders modified after 12:00 12 Nov.

## Governing
- OWNER RULE 2026-11-12 PAINT: paint m2 = plaster m2 of same faces minus false-ceiling band (Q-72) minus tiled faces;
  corners / window-door edges lm. UP-FIN-PAINT-002 (rulebook 1.2.0) MERGED; Lead ruling: opening edges = lm (reading B),
  no owner question (T-746).
- OWNER 2026-11-12: only the main chat merges PRs, in this repo only.
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); join approved work
  first; version reservation in the row; ONE designer list DESIGNER_QUESTIONS.md (15 items); idle slots draft missing
  families, one per run.
- Order 2026-11-09: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing
  families (MEP last). UPM untouched.
- Hub order: T-729 (V3.0.75) -> T-736 -> T-749 paint wiring (after T-746) -> T-738 -> T-314 r3 -> H4 WP -> T-509 H5.

## Baseline (V3.0.74; V3.0.75 pending T-729)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN 11.80007 .. 15.5015; GB beside >= 5.099845; ring >= 0.115155;
  lift >= 1.903; LINTEL AT_MOST 1.322146; strips blank. T-729 stage: FW released 1,027.977 -> 1,061.104 m2.
- FIN.PLASTER held 1,106.949 .. 1,302.169 m2; FIN.PAINT held 604.990 .. 710.006 m2 (rule restatement 841.261 ..
  929.205, unwired); released unchanged.
- WP 53 HELD + 5 MISSING; roof membrane now HELD by DG-a429c160.
- All-trade (T-739 r2, V3.0.74): 5,155 lines, 2,797 HELD with cause; B4 m2 released 1,353.36 + bounded 1,711.94 ..
  2,012.18 + 27 blank.
- Parapet blocks 4 lines HELD 0 .. 101.464 m2 (Q-65 C / D-39). Sanitary census (T-743 READY): WC 12, basin 17, tray 3
  + walk-in 3, FD 19.

## Live rows (16:20)
- READY: T-729 (Gate B, CHECKER-RUNS), T-743 (CHECKER-RUNS). CLAIMED: none.
- TODO: W1: T-744 (after T-743), T-745; W2: T-746 FIRST, T-747; W3: T-748 FIRST.
  QUEUED: T-736 (after T-729), T-749 (after T-736 + T-746), T-738, T-314 r3, T-509, T-363, T-424, T-364, T-513, T-502.
  PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 20 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-729 Gate B (V3.0.75) -> SCOREBOARD v2 restated; T-748 scorecard on V3.0.75 (milestone 13 Nov).
2. T-746 opening edges lm -> T-749 paint wiring.
3. T-736 beads + ceiling r3 as soon as T-729 merges.
4. T-744 tag-not-fixture fix (wet-room classes feed WP / tiles / skirting).
5. T-747 exterior paint; T-738 tiles; T-314 r3; WP H4; T-509.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; ids after it parse into the last lane, so write
  nothing with ids after the lane order; 'after T-xxx' makes a row WAITING. Status word FIRST; 7 cells; no '|' in a
  cell. `board check` pulls first: commit before. Workers claim by lowest gate within their lane, then board order.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm (A); sanitary fixture by content/geometry, tag never a fixture,
  FD pcs B12-01 / collar WP / run B12-02; parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S,
  finish faces A; voids B2-05 union once.
- Lessons: union-not-sum, L-T703-1, F-T725-1, L-T717-1, F-T730-1/-2 ADOPTED; L-T727-1, L-T743-1 PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Scheduled-task edits approved but not
  possible under repo settings. Scout paused. Designer list 15 items.
