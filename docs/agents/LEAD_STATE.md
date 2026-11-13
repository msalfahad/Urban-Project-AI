# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log c2106988..`,
`git -C .work/board log <board commit of this run>..`, `git log d24e4497..` on main, RUN_LOG lines after 04:14Z 13 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: c2106988 (T-749 master 1.78.0). Merges since f2eb70da: cb9b1444 T-752, e771a5b2 T-753,
  8dc7c0f6 + c2106988 T-749 (V3.0.77). No owner commit.
- main: d24e4497 unchanged. Last Lead run: 2026-11-13 04:14 UTC (session_01E6cPnbmfrrsJWszJiyErG3). Every run since
  00:17 closed. 3 idle worker runs 02:40-03:21 (next rows 'after' just-READY tasks) -> fixed this run.
- Drive: no file created / modified in the private folders after 12:00 12 Nov.
- Checker notes carried: verdict-time from `date -u`; 03:51 STARTED line mistyped run id.

## Governing
- OWNER RULE 2026-11-12 PAINT (UP-FIN-PAINT-002): paint m2 = plaster m2 same faces - false-ceiling band - tiled faces;
  corners / opening edges lm (reading B).
- OWNER 2026-11-12: only the main chat merges PRs, this repo only.
- OWNER 2026-11-11 15:30: rebar PARKED (T-664, T-382; Q-81 DEFERRED); join approved work first; ONE designer list
  (16 items); idle slots draft missing families.
- Order 2026-11-09: concrete -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing families (MEP last).
- LEAD RULING: merged T-380 governs B12-02 (no scaled length from a not-to-scale sheet).
- Hub order: T-738 -> T-314 r3 -> T-750 (H4) -> T-509 (H5).

## Baseline (V3.0.77 b8524d5c, NOT RELEASED)
- STR.CONC released 291.476251 m3 (HELD tail unchanged). STR.FORMWORK released 1,061.104 m2; held 107.201 .. 132.786.
- FIN.PLASTER held 1,106.949 .. 1,302.169 m2; FIN.PLASTER.BEAD 14 HELD 165.45 .. 165.65 + AT_LEAST 128.6328 m.l.
- FIN.PAINT released 217.208 m2; held 603.802 .. 687.847 m2; FIN.PAINT.EDGE 0 .. 33.80 lm (30, 3 blank);
  FIN.EXT.PAINT.EDGE 283.218 .. 284.418 lm; exterior paint m2 1,009.110 .. 1,087.619 waits T-314 r3.
- FIN.WP.ROOF released 93.186867 m2; L-636fd3ff HELD 115.656474 .. 115.813974. WP 53 HELD + 5 MISSING (T-750).
- Censuses (no line): B13-07 9 beam ends pcs (D-M1); B13-06 joinery (D-J1..3); sanitary WC 12, basin 17, FD 19.

## Live rows (04:15)
- READY: none. CLAIMED: none.
- TODO: W1 T-755 FIRST (designer re-census + concrete held sweep); W2 T-754 FIRST (+ annex lattice RL id);
  W3 T-738 FIRST. QUEUED: T-314 r3 (after T-738), T-750, T-509, T-363, T-424, T-364, T-513, T-502.
  PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 14 actionable, 0 flagged, 0 stall.
- NEXT RUN: if T-754 / T-755 went READY, give W1 / W2 a next claimable row (do not leave every row 'after' READY):
  candidates = MEASURABLE_NOW concrete lines from T-755 (lane S piece), T-314 r3 prep once T-738 claims the hub.

## Top 5 priorities
1. T-738 Gate B tiles + stair finishes -> SCOREBOARD v2 restated.
2. T-314 r3 exterior plaster + exterior paint m2 (render host); T-754 feeds it.
3. T-755 designer list refresh on V3.0.77 -> rewrite DESIGNER_QUESTIONS counts; concrete MEASURABLE_NOW -> hub.
4. T-750 WP; T-509 earthworks.
5. Keep every lane with one claimable row.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; nothing with ids after it. Status word FIRST;
  7 cells; no '|' in a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time. MERGED only after `engine push` + sha on origin.
- Never leave every next row 'after' a READY task: keep one claimable non-hub row per lane.
- Register: arris once; opening edges in paint = lm; sanitary fixture by content/geometry, tag never a fixture;
  railings in the railing family (T-164 / T-199 / T-393), excluded from B13-07; basins B12-01, excluded from B13-06;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A; voids B2-05 once.
- Lessons ADOPTED: union-not-sum, L-T703-1, F-T725-1, L-T717-1, F-T730-1/-2, L-T743-1, L-T745-1, L-T748-1, L-T751-1,
  L-T749-1, L-T752-1, L-T753-1.
  PROPOSED: L-T727-1.

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Scheduled-task edits approved but not
  possible under repo settings. Scout paused. Designer list 18 items (17 D-M1, 18 D-J1..3).
