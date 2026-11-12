# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log a3f62c52..`,
`git -C .work/board log <board commit of this run>..`, `git log d24e4497..` on main, RUN_LOG lines after 20:14Z 12 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: a3f62c52 (T-747). Merges since 1370c295: 05ca1a46 + 0963e4a1 T-729 (V3.0.75, master 1.76.0),
  e9c61254 T-743, faf8afcd T-746, e22534af T-744, 071dc837 T-748, a3f62c52 T-747. T-745 REJECTED r1. No owner commit.
- main: d24e4497 unchanged. Last Lead run: 2026-11-12 20:14 UTC (run unknown). Every run since 16:20 closed.
- Drive: no file in the private folders modified after 12:00 12 Nov.
- Checker verdict times T-745 20:25Z / T-747 20:20Z are later than its 20:00Z final line: asked to correct.

## Governing
- OWNER RULE 2026-11-12 PAINT (UP-FIN-PAINT-002): paint m2 = plaster m2 same faces - false-ceiling band - tiled faces;
  corners / opening edges lm (reading B, T-746).
- OWNER 2026-11-12: only the main chat merges PRs, this repo only.
- OWNER 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); join approved work first;
  ONE designer list (16 items now: D-DRAIN added for T-745); idle slots draft missing families.
- Order 2026-11-09: concrete -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing families (MEP last).
- LEAD RULING 20:14: merged T-380 governs B12-02 on every villa (no scaled length from a not-to-scale sheet).
- LEAD RULING 20:14: roof membrane record DG-98cbadebaecc5ede (board text DG-a429c160 was wrong) applied in T-736.
- Hub order: T-736 -> T-749 -> T-738 -> T-314 r3 -> T-750 (H4) -> T-509 (H5).

## Baseline (V3.0.75 a1eba08f, NOT RELEASED)
- STR.CONC released 291.476251 m3. HELD: COLUMN 11.80007 .. 15.5015; GB beside >= 5.099845; ring >= 0.115155;
  lift >= 1.903; LINTEL AT_MOST 1.322146; strips blank. STR.FORMWORK released 1,061.104 m2; held 107.201 .. 132.786.
- FIN.PLASTER held 1,106.949 .. 1,302.169 m2; FIN.PAINT held 604.990 .. 710.006 m2 (research: interior rule
  821.011 .. 905.055; exterior = render 1,006.633 .. 1,085.613; unwired).
- WP 53 HELD + 5 MISSING; roof membrane L-636fd3ff still RELEASED 115.832 in V3.0.75 (record not applied; T-736).
- Parapet blocks 4 lines HELD 0 .. 101.464 m2. Sanitary census WC 12, basin 17, tray 3 + walk-in 3, FD 19.

## Live rows (20:14)
- READY: none. CLAIMED: none.
- TODO: W1 T-745 r2; W2 T-751 FIRST; W3 T-736 FIRST.
  QUEUED: T-752 (after T-745), T-749 (after T-736), T-738, T-314 r3, T-750, T-509, T-363, T-424, T-364, T-513, T-502.
  PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 17 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-736 Gate B (beads + ceiling + roof record line) -> SCOREBOARD v2 restated.
2. T-751 exterior edges lm closure -> feeds T-749 / T-314 r3.
3. T-749 paint wiring (interior + exterior) right after T-736.
4. T-745 r2 (status fix), then T-752 metalwork census.
5. T-738 tiles; T-314 r3; T-750 WP; T-509.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; nothing with ids after it. Status word FIRST;
  7 cells; no '|' in a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time. MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; sanitary fixture by content/geometry, tag never a fixture;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; voids B2-05 once.
- Lessons: union-not-sum, L-T703-1, F-T725-1, L-T717-1, F-T730-1/-2 ADOPTED; L-T727-1, L-T743-1, L-T745-1,
  L-T748-1 PROPOSED.

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Scheduled-task edits approved but not
  possible under repo settings. Scout paused. Designer list 16 items.
