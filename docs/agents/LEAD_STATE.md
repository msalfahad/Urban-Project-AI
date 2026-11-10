# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log dc1ac41e..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 12:16Z 10 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: dc1ac41e (T-372 research merge). Before: 8cb64551 (T-669), 91a74d45 (T-670). Candidate of record
  ARCH_TAKEOFF_V3.0.63 09ec4c1a / master 1.64.0 (NOT RELEASED); released V2.9 + route G. T-668 READY (V3.0.64 d227173a,
  task head 7c969d87, master 1.65.0 --promote) under Verifier Gate B since 11:50 (session_01E6cPnecfxZDKcNpWkto31r).
- main: fd71bc30. Last Lead run: 2026-11-10 12:16 UTC (session_01E6cPnd8gSf6HozHwRVRmqp).
- Drive: no file in the Alsenan folder created after 04:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-668 -> T-671 (concrete round 4) -> T-672 (masonry round 1) -> T-664 if Q-81 answered.

## Baseline (V3.0.63, B10 m3, candidate side)
- GB released 23.760555, bounded 1.173410 .. 1.571171 (8), blank 21. COLUMN released 19.7765, held 9.168 .. 13.602 (18),
  6 blank <= 2.80125. NECK 32 bnd 8.7724 .. 11.3460 + 4 >= 0.9515. BEAM released 66.870678, held 6.023085 .. 8.507278
  + 12 blank. Footing F10 HELD 2.176 .. 2.275 (Q-31 C / D-43). GS released 21.63846 (Checker own 21.72308).
- T-669 census: 144 B10 HELD = master; 82 bnd 42.203169 .. 62.166947, 62 blank; DESIGNER 103 / OPEN 34 / MEAS NOW 7.
  Outside B10: 49 HELD blank STR.CONC (44 lintel, 5 stair) -> T-673.
- Unwired after V3.0.64: 2F column lows 1.6362 .. 2.295, CN x5 NOT_APPLICABLE, T-642 split, GS fix (T-674) -> T-671.
- B9 (T-670, unwired): BLACK pcs AT_LEAST 2,571.27625 + range, 12 blank; MORTAR.BLACK 2.59294 m3 + range, 12 blank;
  GLUE.AAC / WHITE unchanged. T-372 perimeter 0.176727 .. 0.188035 m3 (8) -> T-672.
- B11 kg: detailed 9,628.462205; ratio ESTIMATE 2,204.24 .. 2,909.02 unwired (Q-81).

## Live rows (12:20)
- READY: T-668 (CHECKER-RUNS). CLAIMED: none.
- TODO: S: T-673 (W1 FIRST), T-674; A: T-675 (W2 FIRST), T-676; I: T-671 (W3 FIRST, after T-668).
- BLOCKED-OWNER: T-664 (Q-81). QUEUED: T-672 (after T-671), T-363, T-424 (W1); T-314 r3, T-364, T-513, T-502 (W2);
  T-382, T-509 (W3). IN PROGRESS: T-180 (P18 closable after T-674 + T-671). PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-673, T-674, T-363, T-424; A (worker 2): T-675, T-676, T-314, T-364, T-513, T-502;
  I (worker 3): T-671, T-672, T-664, T-382, T-509. Queue check 17 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-668 Gate B publish; report B10 before / after; then T-671 READY + Gate B.
2. T-673 (gate 1; never delayed more than 2 Checker runs): the 49 lintel / stair lines for the 12-13 Nov reconciliation.
3. T-674 ground-slab fix -> P18 closable.
4. T-672 masonry wiring after T-671; T-675 / T-676 research.
5. Q-81 answer -> T-664 takes the hub next.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING. Status word FIRST; 7 cells; NEVER a '|' inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin (ADOPTED).
- Keep at least two INDEPENDENT TODO rows per research lane (W1 went empty at 11:20 with one row per lane).
- Lessons PROPOSED: one owner per junction square (T-666); bind to the raw candidate line (T-665); census scoped by
  trade code (F-C-T669-2); corner square to the run drawn across (R-T669-1).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). FIN.PLASTER released 363.3738 m2.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Worker prompts 'never approximate steel'. Freelancer floors /
  rails workbooks + 1990 spec (coming); privacy switch; PyMuPDF review after 10 Nov; Q-34 2F top roof at the 12-13 Nov
  milestone; token plan Stage 2 after 10 Nov; Scout paused. M3 (11 Nov) AT RISK.
