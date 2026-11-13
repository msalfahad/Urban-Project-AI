# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 4bfa0e9f..`,
`git -C .work/board log <board commit of this run>..`, `git log d24e4497..` on main, RUN_LOG lines after 08:14Z 13 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 4bfa0e9f (T-754 merge, research). No owner commit.
- main: d24e4497 unchanged. Last Lead run: 2026-11-13 08:14 UTC (session_01E6cPnd6BNiHNAjcy3bRpFs). Every run since
  04:17 closed. Verifier 06:53 run took 65 min (07:53 overlap guard INCOMPLETE NOLOCK = correct). 3 idle worker runs
  06:41-07:20 (each lane's only row READY) -> fixed this run.
- Drive: no file created / modified in the private folders after 12:00 12 Nov.

## Governing
- OWNER RULE 2026-11-12 PAINT (UP-FIN-PAINT-002): paint m2 = plaster m2 same faces - false-ceiling band - tiled faces;
  corners / opening edges lm (reading B).
- OWNER 2026-11-12: only the main chat merges PRs, this repo only.
- OWNER 2026-11-11 15:30: rebar PARKED (T-664, T-382; Q-81 DEFERRED); join approved work first; ONE designer list.
- Order 2026-11-09: concrete -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing families (MEP last).
- LEAD RULING: merged T-380 governs B12-02 (no scaled length from a not-to-scale sheet).
- Hub order: T-738 r2 -> T-314 r3 -> T-750 (H4) -> T-509 (H5).

## Baseline (V3.0.77 b8524d5c, NOT RELEASED)
- STR.CONC released 291.476251 m3 (194 HELD lines, 0 MEASURABLE_NOW per T-755 r1). STR.FORMWORK released 1,061.104 m2.
- FIN.PLASTER held 1,106.949 .. 1,302.169 m2; FIN.PLASTER.BEAD 14 HELD 165.45 .. 165.65 + AT_LEAST 128.6328 m.l.
- FIN.PAINT released 217.208 m2; held 603.802 .. 687.847 m2; FIN.PAINT.EDGE 0 .. 33.80 lm;
  FIN.EXT.PAINT.EDGE 283.218 .. 284.418 lm (T-754 research: corners -2.60 -> wire via T-756 / T-314 r3);
  exterior paint m2 1,009.110 .. 1,087.619 waits T-314 r3.
- FIN.WP.ROOF released 93.186867 m2; L-636fd3ff HELD 115.656474 .. 115.813974. WP 53 HELD + 5 MISSING (T-750).
- T-738 r1 figures (AGREE, not merged): stair wall tile 18.44 .. 44.765 m2, risers 13.087 .. 13.740, pitch 20.235 lm,
  nosings 19.55 .. 24.653 lm; width 1.150 ENGINE_RIGHT vs 1.20.

## Live rows (08:25)
- READY: none. CLAIMED: none.
- TODO: W1 T-755 r2 FIRST (live cause fields only); W2 T-756 FIRST (exterior face ledger re-based, NEW);
  W3 T-738 r2 FIRST (t459 binding rebuild). QUEUED: T-314 r3 (after T-738), T-750, T-509, T-363, T-424, T-364, T-513,
  T-502. PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 14 actionable, 0 flagged, 0 stall.
- NEXT RUN: if T-755 r2 merged -> rewrite DESIGNER_QUESTIONS counts from it; adopt L-T755-1. If T-738 r2 merged ->
  adopt L-T738-1, T-314 r3 TODO (W2 per lane order) with T-756 table. Keep one claimable non-hub row per lane:
  candidates W1 = none obvious (concrete tail all designer-held) -> consider T-363 / T-424 prep research; W2 = T-756.

## Top 5 priorities
1. T-738 r2 Gate B -> SCOREBOARD v2 restated (tile + stair cells).
2. T-314 r3 exterior plaster + exterior paint m2 (T-756 feeds it).
3. T-755 r2 -> designer list counts on V3.0.77.
4. T-750 WP; T-509 earthworks.
5. Keep every lane with one claimable row.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; nothing with ids after it. Status word FIRST;
  7 cells; no '|' in a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time. MERGED only after `engine push` + sha on origin.
- Never leave every next row 'after' a READY task: keep one claimable non-hub row per lane.
- Register: arris once; opening edges in paint = lm; parapet screen flush with wall below = one face, no corner;
  sanitary fixture by content/geometry; railings in the railing family (RL-03 annex / RL-10 fence), excluded from
  B13-07; basins B12-01; parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A.
- Lessons ADOPTED: union-not-sum, L-T703-1, F-T725-1, L-T717-1, F-T730-1/-2, L-T743-1, L-T745-1, L-T748-1, L-T751-1,
  L-T749-1, L-T752-1, L-T753-1. PROPOSED: L-T727-1, L-T738-1, L-T755-1.

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Scheduled-task edits approved but not
  possible under repo settings. Scout paused. Designer list 18 items (17 D-M1, 18 D-J1..3); counts stale until T-755 r2.
