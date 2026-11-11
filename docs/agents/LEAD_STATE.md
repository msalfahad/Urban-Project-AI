# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 0b6d1bc2..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 08:14Z 11 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 0b6d1bc2 (T-687 maps). Merges since bdef4f70: 66ffd421 T-689, 5e4fdc33 T-691, 8678ddfb T-692,
  510f069d T-694, 5b51924e T-696, 12bf5b8c T-687 Gate B (V3.0.69). Candidate of record ARCH_TAKEOFF_V3.0.69 7ea65f9b /
  master 1.70.0 (NOT RELEASED). Released V2.9 + G. No owner commit.
- main: fd71bc30. Last Lead run: 2026-11-11 08:14 UTC (session_01E6cPneb3ySEPpCBJSrMoo1).
- Drive: no file in the Alsenan folder modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-693 (concrete r7, V3.0.70) -> T-703 (masonry r4, T-696 limits) -> T-314 / T-364 / T-363 per T-698 r2
  -> T-664 if Q-81 answered. Later hub rows to open once merged: T-697 corner beads, T-695/T-700 earthworks, T-691 WP.

## Baseline (V3.0.69)
- STR.CONC: released 317 = 291.476251 m3; LINTEL bounded 1.361 .. 2.050636 (24), blank 21 (T-699); COLUMN held
  10.26435 .. 13.27025 (T-689 merged, unwired: -> 11.67283 .. 15.5015, blank 7 -> 2 via T-693); BEAM 6.023229 ..
  8.507710 (consultant); Band HELD 5.6392 .. 11.0328 (Q-28). Slab vs ref -0.77 % UNRESOLVED.
- B9: BLACK pcs 2,571.27625 + 698.66125 .. 702.91125, blank 12; MORTAR 2.59294 + 0.618315 .. 0.622076 m3; T-696
  one-sided limits unwired (T-703).
- FIN.PLASTER 388.584 + HELD 1,131.966 .. 1,300.694 + 3 blank; FIN.PAINT 217.208 + 601.645 .. 682.331, 0 blank.
  Vs freelancer plaster >= +32.09 %, paint -31.25 .. -24.48 % -> T-701.
- WP 58 = 53 HELD + 5 MISSING; roof 115.814 proposed (merged, unwired). Tiles 104 HELD (T-702).
  B11 detailed 9,628.462205 kg; ratio unwired (Q-81). Verified share CONCRETE 1 / 8.

## Live rows (08:25)
- READY: T-695 (W1 earthworks census), T-697 (W2 corner beads), both CHECKER-RUNS. CLAIMED: none.
- TODO: S: T-699 (W1 FIRST), T-700 (after T-695 MERGED); A: T-701 (W2 FIRST), T-702; I: T-693 (W3 FIRST), T-698 r2.
- QUEUED: T-703, T-363, T-424, T-314, T-364, T-513, T-502, T-382, T-509. BLOCKED-OWNER: T-664 (Q-81). IN PROGRESS:
  T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-699, T-700, T-363, T-424; A (worker 2): T-701, T-702, T-314, T-364, T-513, T-502;
  I (worker 3): T-693, T-698, T-703, T-664, T-382, T-509. Queue check 19 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-693 column wiring Gate B (concrete first); T-697 / T-695 Gate A; SCOREBOARD v2 restated on V3.0.69.
2. T-703 masonry limits wiring after T-693.
3. T-701 plaster / paint vs freelancer reconciliation (material discrepancy).
4. T-699 lintel limits; T-700 earthworks r2; T-702 tiles r3.
5. T-698 r2 -> T-314 / T-364 / T-363 wiring; Q-81 answer -> T-664.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING. Status word FIRST; 7 cells; NEVER a '|' inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin.
- Register rulings: 08:25 arris once (B4-09 bead lm, plaster; B4-04 faces m2 only, T-314 r3 excludes arris lm);
  04:20 corner beads -> plaster; column tops under B8; 00:20 wet band above ceiling -> plaster.
- Lessons PROPOSED 08:25: ledger HELD fields carried by every derived map; arris once.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Decode wrapper raw-binary (NEEDS FIXING, owner).
  Q-34 2F top roof. Scout paused. M3 estimate 13-14 Nov. Designer items (D-xx) keep lines HELD, never block integration.
