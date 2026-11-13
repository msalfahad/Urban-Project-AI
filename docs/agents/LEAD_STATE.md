# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log f2eb70da..`,
`git -C .work/board log <board commit of this run>..`, `git log d24e4497..` on main, RUN_LOG lines after 00:13Z 13 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: f2eb70da (T-736 master 1.77.0). Merges since a3f62c52: 79766703 T-751, a650be13 T-745 r2,
  166fb1fd + f2eb70da T-736 (V3.0.76). No owner commit.
- main: d24e4497 unchanged. Last Lead run: 2026-11-13 00:13 UTC (session_01E6cPncgueebL7UKRgaUPst). Every run since
  20:17 closed. 3 idle worker runs 21:00-23:20 (queue empty after READY) -> fixed this run.
- Drive: no file in the private folders modified after 12:00 12 Nov.
- Checker verdict-time note (T-745 r1 20:25Z vs final 20:00Z) still uncorrected; T-751 cell > 600 chars.

## Governing
- OWNER RULE 2026-11-12 PAINT (UP-FIN-PAINT-002): paint m2 = plaster m2 same faces - false-ceiling band - tiled faces;
  corners / opening edges lm (reading B).
- OWNER 2026-11-12: only the main chat merges PRs, this repo only.
- OWNER 2026-11-11 15:30: rebar PARKED (T-664, T-382; Q-81 DEFERRED); join approved work first; ONE designer list
  (16 items); idle slots draft missing families.
- Order 2026-11-09: concrete -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing families (MEP last).
- LEAD RULING: merged T-380 governs B12-02 (no scaled length from a not-to-scale sheet).
- Hub order: T-749 -> T-738 -> T-314 r3 -> T-750 (H4) -> T-509 (H5).

## Baseline (V3.0.76 9b35725c, NOT RELEASED)
- STR.CONC released 291.476251 m3 (HELD tail unchanged). STR.FORMWORK released 1,061.104 m2; held 107.201 .. 132.786.
- FIN.PLASTER held 1,106.949 .. 1,302.169 m2; FIN.PLASTER.BEAD 14 HELD 165.45 .. 165.65 + AT_LEAST 128.6328 m.l.
- FIN.PAINT held 604.990 .. 710.006 m2 (research: interior 821.011 .. 905.055; exterior = render 1,006.633 .. 1,085.613;
  ext corners 178.136 .. 179.336 lm, windows 103.682 lm; unwired -> T-749).
- FIN.WP.ROOF released 93.186867 m2; L-636fd3ff HELD 115.656474 .. 115.813974. WP 53 HELD + 5 MISSING (T-750).
- Parapet blocks 4 lines HELD 0 .. 101.464 m2. Sanitary census WC 12, basin 17, tray 3 + walk-in 3, FD 19.

## Live rows (00:13)
- READY: none. CLAIMED: none.
- TODO: W1 T-752 FIRST; W2 T-753 FIRST; W3 T-749 FIRST.
  QUEUED: T-754 (after T-753), T-738 (after T-749), T-314 r3 (after T-738), T-750, T-509, T-363, T-424, T-364, T-513,
  T-502. PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 16 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-749 Gate B paint wiring (interior + exterior + T-751 bounds) -> SCOREBOARD v2 restated.
2. T-738 tiles + stair finishes; T-314 r3 exterior plaster.
3. T-754 exterior door / slab edge residuals (feeds T-314 r3 / paint restatement).
4. T-752 metalwork, T-753 joinery censuses (designer items to the list if found).
5. T-750 WP; T-509 earthworks.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; nothing with ids after it. Status word FIRST;
  7 cells; no '|' in a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time. MERGED only after `engine push` + sha on origin.
- Never leave every next row 'after' a READY task: keep one claimable non-hub row per lane.
- Register: arris once; opening edges in paint = lm; sanitary fixture by content/geometry, tag never a fixture;
  railings in the railing family (T-164 / T-199 / T-393), excluded from B13-07; basins B12-01, excluded from B13-06;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; voids B2-05 once.
- Lessons ADOPTED: union-not-sum, L-T703-1, F-T725-1, L-T717-1, F-T730-1/-2, L-T743-1, L-T745-1, L-T748-1, L-T751-1.
  PROPOSED: L-T727-1.

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Scheduled-task edits approved but not
  possible under repo settings. Scout paused. Designer list 16 items.
