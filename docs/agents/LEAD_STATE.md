# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 8a0fc1e1..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 00:13Z 11 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 8a0fc1e1 (T-686 maps). Before: ae9b3d6d T-686, 8563a6fa T-684, 904cdff0 T-685, 85c1d7aa T-683,
  ebd8a77d T-681. Candidate of record ARCH_TAKEOFF_V3.0.66 c411617d / master 1.67.0 (NOT RELEASED); V3.0.67 (T-682,
  head 0bdf3131, chain a29a11a9, master 1.68.0 pending) in Gate B, Verifier run 23:54 open at 00:20. Released V2.9 + G.
- main: fd71bc30. Last Lead run: 2026-11-11 00:13 UTC (session_01E6cPneN1u4k8dc9MBu9Kbn).
- Drive: no file in the Alsenan folder modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-682 (last concrete) -> T-672 (masonry r1 + T-675) -> T-687 (plaster / paint r1: T-676 + T-680 + T-686)
  -> T-664 if Q-81 answered. Concrete research merged after T-682 was claimed (T-683 none to wire; T-688 / T-689 when
  merged) waits for a round 7 behind T-672.

## Baseline (V3.0.66 candidate side; V3.0.67 READY values in brackets)
- STR.CONC 597: released 317 = 291.476251 m3; bounded 101 = 42.014281 .. 66.193191; blank 89 (T-683).
- LINTEL bounded 0.925 .. 1.496412 (17), blank 28 [1.361 .. 2.050636 (24), blank 21]; COLUMN held 9.6702 .. 12.414
  [10.26435 .. 13.27025]; BEAM held 6.023229 .. 8.507710; Band HELD 5.6392 .. 11.0328 (Q-28); GB released 23.760555.
- Slab vs ref 60.280155 / 59.8174 (-0.77 %): 1F -0.556333 UNRESOLVED (T-688). P18 26/26 AGREE, GB part HELD.
- B9 unwired: BLACK pcs AT_LEAST 2,571.27625; MORTAR.BLACK 2.59294; T-675 MAIN_S / ANNEX_S black.
- Plaster (unwired) bounded 1,078.345 .. 1,202.880 (21) + 3 blank; paint 601.645 .. 682.331 (10), 0 blank; wet band
  above ceiling 20.53 m2 no line (T-690). FIN.PLASTER released 363.3738 m2.
- WP 58 = 53 HELD + 5 MISSING (pantry); roof released 115.832 vs band 115.656 .. 115.814 (T-691).
- Tiles 104 HELD; adhesive HELD 148.457 .. 247.428 bags. B11 detailed 9,628.462205 kg; ratio unwired (Q-81).

## Live rows (00:20)
- READY: T-682 (Gate B in review). CLAIMED: none.
- TODO: S: T-688 (W1 FIRST), T-689; A: T-690 (W2 FIRST), T-691; I: T-672 (W3 FIRST once T-682 GATE B PASS), T-692.
- BLOCKED-OWNER: T-664 (Q-81). QUEUED: T-687, T-363, T-424, T-314, T-364, T-513, T-502, T-382, T-509. IN PROGRESS:
  T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-688, T-689, T-363, T-424; A (worker 2): T-690, T-691, T-314, T-364, T-513, T-502;
  I (worker 3): T-672, T-692, T-687, T-664, T-382, T-509. Queue check 18 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-682 Gate B published; SCOREBOARD v2 restated on V3.0.67.
2. T-672 masonry Gate B; then T-687 plaster / paint (with T-686 and, if merged, T-690 (c) wet band).
3. T-688 1F slab cause (12-13 Nov statement); T-689 column / beam ranges.
4. T-690 tiles r2; T-691 WP r2 + F-V685-1 (released outside its band).
5. T-692 missing families census; Q-81 answer -> T-664.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING (write 'once ... is claimed / READY' instead). Status word FIRST; 7 cells; NEVER a '|' inside a cell.
  `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin (ADOPTED).
- Lane S needs two rows W1 can take; W3 has its own lane I research row while the hub is in review.
- Register rulings 00:20: wet-room band above the ceiling -> plaster; MS2 1F NW square RESOLVED (flat landing).
- Lessons PROPOSED 00:20: plan pattern can be the storey below (riser budget + section first, T-684); a released
  figure must lie in its own drawn band (F-V685-1); ceiling-to-soffit band needs a named owner trade (F-T686-1).
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Decode wrapper raw-binary bug (NEEDS FIXING, owner).
  Worker prompts 'never approximate steel'. Q-34 2F top roof at the 12-13 Nov milestone. Scout paused. M3 slips to
  13-14 Nov. Designer items (D-xx) keep lines HELD, never block integration.
