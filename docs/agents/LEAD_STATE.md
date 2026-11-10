# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log cffefa0c..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 16:15Z 10 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: cffefa0c (T-676 merge). Before: bb4ec90b (T-674), 722a9ea6 (T-671 published), e0984b13 (T-675),
  15d03afc (T-673), 0ed807c3 (T-668 published). Candidate of record ARCH_TAKEOFF_V3.0.65 38af7909 / master 1.66.0
  (NOT RELEASED); released V2.9 + route G.
- main: fd71bc30. Last Lead run: 2026-11-10 16:15 UTC (session_01E6cPnbFmnWx6jnkvLKSD4Z).
- Drive: no file in the Alsenan folder created after 12:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-677 (concrete round 5: T-673 + T-674) -> T-672 (masonry round 1 + T-675) -> T-664 if Q-81 answered ->
  plaster Gate B (OP-009 reveal + T-680) next to write.

## Baseline (V3.0.65, m3, candidate side)
- COLUMN held 9.6702 .. 12.414 (59 lines), 5 CN NOT_APPLICABLE. BEAM held 6.023229 .. 8.507710 + 12 blank; strip
  0.050 released + 0 .. 0.025. Band HELD 5.6392 .. 11.0328 (Q-28). Pool blinding >= 0.915529. GB released 23.760555.
  NECK 32 bnd 8.7724 .. 11.3460 + 4 >= 0.9515. Footing F10 HELD 2.176 .. 2.275. GS released 21.63846.
- Unwired: T-673 16 lintels 0.925 .. 1.496412 + ST-03 steps 0.355017 (22 OPEN BOUND, 10 DESIGNER); T-674 GS
  2.141320 -> 2.143747 + 0.090 m2 triangles -> BAND0038; outline 778 UNRESOLVED; annex C3 low open.
- B9 unwired: BLACK pcs AT_LEAST 2,571.27625; MORTAR.BLACK 2.59294; T-675 MAIN_S / ANNEX_S black (4 AAC retire).
- Plaster / paint (T-676): 57 HELD; plaster 932.726 .. 1006.776 m2 (14) + 10 blank; paint 487.121 .. 542.861 (7) + 3.
- B11 kg: detailed 9,628.462205; ratio ESTIMATE 2,204.24 .. 2,909.02 unwired (Q-81).

## Live rows (16:25)
- READY: none. CLAIMED: none.
- TODO: S: T-678 (W1 FIRST), T-679; A: T-680 (W2 FIRST), T-681; I: T-677 (W3 FIRST).
- BLOCKED-OWNER: T-664 (Q-81). QUEUED: T-672 (after T-677), T-363, T-424; T-314 r3, T-364, T-513, T-502; T-382,
  T-509. IN PROGRESS: T-180 (P18 closable after T-677). PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-678, T-679, T-363, T-424; A (worker 2): T-680, T-681, T-314, T-364, T-513, T-502;
  I (worker 3): T-677, T-672, T-664, T-382, T-509. Queue check 16 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-677 Gate B (last concrete research into the candidate); T-180 P18 closes after it.
2. T-679 concrete reconciliation statement for 12-13 Nov (aggregation proof, reference comparison separate).
3. T-672 masonry Gate B after T-677.
4. T-678 concrete open items (22 OPEN BOUND, 778, C3); T-680 / T-681 finishes research.
5. Checker full SCOREBOARD v2 restatement on V3.0.65 (owed); Q-81 answer -> T-664.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING (write 'independent of T-nnn' for a second row). Status word FIRST; 7 cells; NEVER a '|' inside a cell.
  `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin (ADOPTED).
- Keep TWO INDEPENDENT TODO rows per research lane: W3 takes lane S rows while the hub is in review (W1 empty at
  11:20 and 15:23).
- Lessons PROPOSED: one owner per junction square; bind to the raw candidate line; census scoped by trade code; corner
  square to the run drawn across; own re-measure noded before charging the engine (T-674); oblique-end triangles to
  the member, both lines in one diff (T-674).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). FIN.PLASTER released 363.3738 m2.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Worker prompts 'never approximate steel'. Freelancer floors /
  rails workbooks + 1990 spec (coming); privacy switch; PyMuPDF review after 10 Nov; Q-34 2F top roof at the 12-13 Nov
  milestone; token plan Stage 2 after 10 Nov; Scout paused. M3 (11 Nov) will not be met on its date.
