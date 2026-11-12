# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log a91a1dfe..`,
`git -C .work/board log <board commit of this run>..`, `git log d24e4497..` on main, RUN_LOG lines after 12:16Z 12 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: a91a1dfe (T-708). Merges since 6143f30d: 870f15f5 T-735, 3d8185fe T-734, e6481b43 + 10889521
  T-717 r2 (V3.0.74, master 1.75.0), 891c14ea T-737, a91a1dfe T-708. T-739 REJECTED r1 (stale output). No owner commit.
- main: d24e4497 (PR #6 decode fix + PR #7 main-chat merges, owner). Last Lead run: 2026-11-12 12:16 UTC
  (session_01E6cPnbtFVhYShJuDwABKdA).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER RULE 2026-11-12 PAINT: paint m2 = plaster m2 of same faces minus false-ceiling band (Q-72) minus tiled faces;
  corners / window-door edges lm. Applied as T-740 (UP-FIN-PAINT-002 + normal / adverse test).
- OWNER 2026-11-12: only the main chat merges PRs, in this repo only.
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 out of lane orders; Q-81 DEFERRED); join approved work
  first; version reservation in the row; ONE designer list DESIGNER_QUESTIONS.md (now 15 items); idle slots draft
  missing families, one per run.
- Order 2026-11-09: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing
  families (MEP last). UPM untouched.
- Hub order: T-729 (V3.0.75) -> T-736 (V3.0.76) -> T-738 (V3.0.77) -> T-314 r3 -> H4 WP -> T-509 H5; paint wiring after T-740.

## Baseline (V3.0.74)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN 11.80007 .. 15.5015; GB beside >= 5.099845; ring >= 0.115155;
  lift >= 1.903; LINTEL AT_MOST 1.322146; strips blank. MS1-L high 1.023763 (unwired).
- FIN.PLASTER held 1,106.949 .. 1,302.169 m2 (like for like -16.76 .. -8.68 %); FIN.PAINT held 604.990 .. 710.006 m2
  (-31.25 .. -24.48 %); released unchanged. B2-03 gross 278.266 / 209.839 / 55.080 m2 VERIFIED.
- FW: T-735 7 lines one form each (412 4.183916 .. 5.532116; 415 >= 2.8938; 4 annex >= 3.0528; L-867e155d 0.102019).
- WP 53 HELD + 5 MISSING; roof L-636fd3ff released 115.832 vs band 115.656474 .. 115.813974 (record not issued -> T-741).
- Earthworks: Z2 183.948 vs 136.901 .. 163.479 reconciled; densities HELD.

## Live rows (12:20)
- READY: none. CLAIMED: none.
- TODO: W1 (cross-lane): T-741 FIRST, T-743; W2 A: T-740 FIRST, T-742; I: T-729 (W3 FIRST), T-739 r2.
  QUEUED: T-736 (after T-729), T-738 (after T-736), T-314 r3 (after T-736), T-509 (after T-738), T-363, T-424, T-364,
  T-513, T-502. PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 18 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-729 formwork + C10 Gate B (V3.0.75), with the T-735 forms; SCOREBOARD v2 restated on merge.
2. T-740 paint rule version (owner rule today), paint before / after in m2; then a paint wiring package.
3. T-739 r2 all-trade statement on the newest candidate (milestone scorecard, 13 Nov).
4. T-741 downgrade issue path -> Checker issues the T-734 roof record.
5. T-736 beads -> T-738 tiles -> T-314 r3 exterior -> H4 WP -> T-509 earthworks.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; ids after it parse into the last lane, so write
  nothing with ids after the lane order; 'after T-xxx' makes a row WAITING. Status word FIRST; 7 cells; no '|' in a
  cell. `board check` pulls first: commit before. Workers claim by lowest gate within their lane, then board order.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once; corner beads -> plaster; parapet block body -> A masonry from the slab finish (T-742), downstand below -> B10, faces -> plaster; stair
  concrete + formwork = S, stair finish faces = A; voids B2-05 owned by the register (A), deducted once (union).
- Lessons: union-not-sum, L-T703-1, F-T725-1, L-T717-1 ADOPTED (rebuild candidate-bound outputs on origin head just
  before hand-in); L-T727-1, F-T730-1/-2 PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form (27 H3s rows HELD). Q-34 2F top roof. Scheduled-task edits approved but not
  possible under repo settings. Scout paused. Designer items 14 (D-GF-07) and 15 (D-BAND) added today.
