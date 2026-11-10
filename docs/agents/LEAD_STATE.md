# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 4c6726ce..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 20:13Z 10 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 4c6726ce (T-679 merge). Before: 11d94e99 (T-677 published, merge 8a28bce5), f8515d4b (T-678),
  707c624e (T-680). Candidate of record ARCH_TAKEOFF_V3.0.66 c411617d / master 1.67.0 (NOT RELEASED); released V2.9 +
  route G.
- main: fd71bc30. Last Lead run: 2026-11-10 20:13 UTC (run unknown).
- Drive: no file in the Alsenan folder created after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-682 (concrete round 6 = T-678, LAST concrete package) -> T-672 (masonry round 1 + T-675) -> T-687
  (plaster / paint round 1: T-676 OP-009 + T-680 + T-686) -> T-664 if Q-81 answered. Concrete research merged after
  T-682 is claimed waits for a round 7 behind T-672.

## Baseline (V3.0.66, m3, candidate side)
- STR.CONC (V3.0.65 statement T-679): 596 lines; released 317 = 291.473824; HELD bounded 84 = 41.084313 .. 64.696779;
  blank 105. V3.0.66 moves: GROUND_SLAB released 21.640885 (+0.002427); BAND0038 0.098008 .. 0.130678; LINTEL 61 =
  16 released + 17 bounded (0.925 .. 1.496412) + 28 blank; ST-03 steps >= 0.355017 beside. Statement round 2 = T-683.
- COLUMN held 9.6702 .. 12.414; BEAM held 6.023229 .. 8.507710; Band HELD 5.6392 .. 11.0328 (Q-28); pool blinding >=
  0.915529; GB released 23.760555; NECK 32 bnd 8.7724 .. 11.3460 + 4 >= 0.9515; F10 HELD 2.176 .. 2.275.
- Unwired: T-678 9 lintels low 0.520 (13 OPEN BOUND with datum), PC-2F L-541c7e56 0.1824 .. 0.350, C3 low 0.41175.
- B9 unwired: BLACK pcs AT_LEAST 2,571.27625; MORTAR.BLACK 2.59294; T-675 MAIN_S / ANNEX_S black (4 AAC retire).
- Plaster / paint: 57 HELD (T-676); T-680 FIN.PLASTER blank 10 -> 9, FIN.PAINT 3 -> 2 (unwired).
- Tiles (T-681 READY): 104 HELD; adhesive HELD 148.457 .. 247.428 bags.
- B11 kg: detailed 9,628.462205; ratio ESTIMATE 2,204.24 .. 2,909.02 unwired (Q-81).

## Live rows (20:20)
- READY: T-681 (18:53; Checker partial, gate e owed; CHECKER-RUNS 1). CLAIMED: none.
- TODO: S: T-683 (W1 FIRST), T-684; A: T-685 (W2 FIRST), T-686; I: T-682 (W3 FIRST).
- BLOCKED-OWNER: T-664 (Q-81). QUEUED: T-672 (after T-682), T-687 (after T-672), T-363, T-424; T-314 r3, T-364,
  T-513, T-502; T-382, T-509. IN PROGRESS: T-180 (P18 CLOSABLE NOW). PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-683, T-684, T-363, T-424; A (worker 2): T-685, T-686, T-314, T-364, T-513, T-502;
  I (worker 3): T-682, T-672, T-687, T-664, T-382, T-509. Queue check 18 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-682 Gate B (last concrete into the candidate).
2. T-672 masonry Gate B after T-682; then T-687 plaster / paint.
3. T-683 concrete statement round 2 for 12-13 Nov (V3.0.66; F-T679-1..3).
4. T-681 gate e (Checker); T-180 P18; SCOREBOARD v2 on V3.0.66.
5. T-684 stair NW corner (cross-trade); T-685 waterproofing census; Q-81 answer -> T-664.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING, even naming the row itself (write 'once this row is claimed'). Status word FIRST; 7 cells; NEVER a '|'
  inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin (ADOPTED).
- Lane S needs two rows W1 can take even when W3 takes one (W1 empty at 11:20, 15:23, 19:21); give W3 its own lane I
  TODO first.
- Lessons PROPOSED: one owner per junction square; bind to the raw candidate line; census scoped by trade code; corner
  square to the run drawn across; own re-measure noded before charging the engine (T-674); oblique-end triangles to
  the member, both lines in one diff (T-674); lintel concrete form follows the drawing's detail, precast pieces beside
  (T-677); every check needs a bounded state (T-677); census reconciles by line id, not count (F-T679-1).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). FIN.PLASTER released 363.3738 m2.
- Register rulings 20:20: MS2 1F NW corner (lane S owns, T-684); cast RC lintels per ST p.13, precast pieces beside.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Worker prompts 'never approximate steel'. Freelancer floors /
  rails workbooks + 1990 spec (coming); privacy switch; PyMuPDF review after 10 Nov; Q-34 2F top roof at the 12-13 Nov
  milestone; token plan Stage 2 after 10 Nov; Scout paused. M3 (11 Nov) will not be met on its date.
