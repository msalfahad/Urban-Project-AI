# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log bdef4f70..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 04:13Z 11 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: bdef4f70 (T-672 maps). Before: 4d1b254c T-672 merge (V3.0.68), adef31c5 T-690, a62b3024 T-688,
  fe49c91b T-682 published (V3.0.67). Candidate of record ARCH_TAKEOFF_V3.0.68 d1de50cb / master 1.69.0 (NOT
  RELEASED). Released V2.9 + G.
- main: fd71bc30. Last Lead run: 2026-11-11 04:13 UTC (session_01E6cPndMbKxt3CsmXyzq6eB).
- Drive: no file in the Alsenan folder modified after 16:00 10 Nov.
- Verifier run 02:52 (session_01E6cPncHfQZR4jC25WngAEf) had NO final line at 04:20 (work published); check it closed.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-687 (plaster / paint r1 + wet band) -> T-693 (concrete r7: T-689 + R-T688-3; goes first once T-689
  MERGED and T-687 passed) -> T-314 / T-364 / T-363 per T-698 -> T-664 if Q-81 answered.

## Baseline (V3.0.68)
- STR.CONC: released 317 = 291.476251 m3 (unchanged since V3.0.66); LINTEL bounded 1.361 .. 2.050636 (24), blank 21;
  COLUMN held 10.26435 .. 13.27025 (T-689 READY: low +0.0257, 5 blank bounded +1.382780 .. 2.231250, blank 7 -> 2);
  BEAM held 6.023229 .. 8.507710; Band HELD 5.6392 .. 11.0328 (Q-28). Slab vs ref -0.77 % UNRESOLVED (T-688 typed 120).
- B9: BLACK pcs 2,571.27625 + 698.66125 .. 702.91125, blank 12; MORTAR.BLACK 2.59294 + 0.618315 .. 0.622076 m3;
  PERIMETER 20 lines, LINTEL_BEARING 9; GLUE.AAC blank 10; WHITE blank 15; MAS.BLOCK 467.7925 m2.
- Plaster (unwired) bounded 1,078.345 .. 1,202.880 (21) + 3 blank; paint 601.645 .. 682.331; wet band 78.83 .. 123.02
  m2 (18 rooms) -> T-687. FIN.PLASTER released 363.3738 m2.
- WP 58 = 53 HELD + 5 MISSING; roof released 115.832 -> 115.814 proposed (T-691 READY). Tiles 104 HELD.
  B11 detailed 9,628.462205 kg; ratio unwired (Q-81). Verified share CONCRETE 1 / 8.

## Live rows (04:20)
- READY: T-689, T-691, T-692 (all CHECKER-RUNS). CLAIMED: none.
- TODO: S: T-694 (W1 FIRST), T-695; A: T-696 (W2 FIRST), T-697; I: T-687 (W3 FIRST), T-698.
- QUEUED: T-693, T-363, T-424, T-314, T-364, T-513, T-502, T-382, T-509. BLOCKED-OWNER: T-664 (Q-81). IN PROGRESS:
  T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-694, T-695, T-363, T-424; A (worker 2): T-696, T-697, T-314, T-364, T-513, T-502;
  I (worker 3): T-687, T-698, T-693, T-664, T-382, T-509. Queue check 20 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-689 Gate A (blocks T-693); T-687 plaster / paint Gate B; SCOREBOARD v2 restated after it.
2. T-693 concrete round 7 right after T-687 passes.
3. T-694 concrete statement r3 for 12-13 Nov.
4. T-696 masonry r3 (+ F-V672-1 outward rounding), T-697 corner beads, T-695 earthworks.
5. T-698 -> T-314 / T-364 / T-363 wiring; Q-81 answer -> T-664.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING. Status word FIRST; 7 cells; NEVER a '|' inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin.
- Each lane keeps two rows its worker can take; W3 has a research row while the hub is in review.
- Register rulings 04:20: corner beads -> plaster (surround / tiled / lined arrises excluded); column tops under B8
  (column line owns to the soffit; window head evidence only). 00:20: wet band above ceiling -> plaster.
- Lessons rows added PROPOSED 04:20 (ERS s.7): outward bound rounding, typed reference rows, riser budget, released
  inside its drawn band, ceiling-to-soffit band owner.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Decode wrapper raw-binary / zip (NEEDS FIXING, owner).
  Worker prompts 'never approximate steel'. Q-34 2F top roof. Scout paused. M3 estimate 13-14 Nov. Designer items (D-xx)
  keep lines HELD, never block integration.
