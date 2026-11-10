# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log b5df949c..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 08:16Z 10 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: b5df949c (T-665 merge 12acd3d4 + promotion 2a69cbe0). Candidate of record ARCH_TAKEOFF_V3.0.63
  09ec4c1a / master 1.64.0 (NOT RELEASED); released V2.9 + route G. Before: 7a9ccbff (T-661 published), b89ea23f
  (T-667), 06e2e736 (T-666).
- main: fd71bc30. Gate B OPEN (hub free). Last Lead run: 2026-11-10 08:16 UTC (session_01E6cPnbB7yYqasMjyHHQxuP).
- Drive: no file in the Alsenan folder created after 04:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Lead decision 08:16: rebar wiring waits on Q-81, so masonry RESEARCH starts (own files only); hub order after T-668:
  T-664 if Q-81 answered, else T-372 wiring.

## Baseline (V3.0.63, B10 m3, candidate side)
- GB released 23.760555, bounded 1.173410 .. 1.571171 (8), blank 21 (16 with >= 5.069839 beside). COLUMN released
  19.7765, held 9.168 .. 13.602 (18), 6 blank <= 2.80125. NECK 32 bnd 8.7724 .. 11.3460 + 4 >= 0.9515. BEAM released
  66.870678 (+0.549624), held 6.023085 .. 8.507278 + 12 blank. Footing F10 HELD 2.176 .. 2.275 (D-43).
- Unwired: T-666 (5 pieces 0.626400 .. 1.879200, band 5.6392 .. 11.0328 HELD), T-667 (pool blinding >= 0.915529 new).
- B11 kg: detailed 9,628.462205; ratio ESTIMATE 2,204.24 .. 2,909.02 unwired (Q-81).
- B9 (Checker V3.0.59 note): BLACK pcs >= 1,075.80 + 18 blank; MORTAR.BLACK >= 1.269444 + 18 blank; GLUE.AAC >= 43.596
  + 15 held (3 bnd 842.06025 .. 861.32025); WHITE 17 blank.

## Live rows (08:16)
- READY: none. CLAIMED: none.
- TODO: S: T-669 (W1 FIRST), T-372 (W1 next, research part); A: T-670 (W2 FIRST); I: T-668 (W3 FIRST).
- BLOCKED-OWNER: T-664 (Q-81). QUEUED: T-363, T-424 (W1); T-314 r3, T-364, T-513, T-502 (W2); T-382, T-509 (W3).
- IN PROGRESS: T-180 (P18 ground slab next). PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-669, T-372, T-363, T-424; A (worker 2): T-670, T-314, T-364, T-513, T-502;
  I (worker 3): T-668, T-664, T-382, T-509. Queue check 14 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-668 READY + Gate B (V3.0.64); report B10 before / after.
2. T-669 (gate 1; never delayed more than 2 Checker runs): census = plan for 12-13 Nov concrete reconciliation.
3. T-670 masonry materials; then a masonry wiring row (lane I) after T-668.
4. Q-81 answer -> T-664 takes the hub next.
5. 12-13 Nov reconciliation + scorecard.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING. Status word FIRST; 7 cells; NEVER a '|' inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head.
- ADOPTED: MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin. The Verifier
  may leave a row READY after publishing: the Lead corrects the status word (did so for T-661).
- PROPOSED lessons 08:16: one owner per junction square (T-666); bind to the raw candidate line (T-665).
- F10 + F third reading: no row (D-43 designer item; no released quantity moves).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). FIN.PLASTER released 363.3738 m2.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- Q-81 (rebar ratio; blocks all ratio wiring). ORR-007 stair skirting payable form. Worker prompts 'never approximate
  steel'. Freelancer floors / rails workbooks + 1990 spec (coming); privacy switch; PyMuPDF review after 10 Nov; Q-34 2F
  top roof at the 12-13 Nov milestone; token plan Stage 2 after 10 Nov; Scout paused.
