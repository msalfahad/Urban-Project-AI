# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log b09d6ed4..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 04:14Z 10 Nov,
rows changed since), then rewrite. FIRST check `git -C .work/engine ls-remote origin` holds the T-661 merge.

## Last seen
- engine origin head: b09d6ed4 (T-663 merge; before 2cec1520 T-658 r2, 169a4df2 T-662). PUBLISHED candidate of record
  ARCH_TAKEOFF_V3.0.61 / master 1.62.0; released V2.9 + route G.
- T-661 (V3.0.62 / master 1.63.0) GATE B PASS 03:43 but merge ea1533e4 + promotion ff93c61e NOT on origin (Verifier
  02:51 run left no final line; lock until 04:50). Row = READY PUBLISH-ONLY; scoreboard 03:48 section describes
  V3.0.62 prematurely (Checker restates after publish).
- main: fd71bc30. Gate B OPEN. Last Lead run: 2026-11-10 04:14 UTC (session_01E6cPnci5MAFPeQHAUuMPvt).

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.

## Baseline for "before / after" (trial BOQ r4, candidate V3.0.61) - unchanged on origin
- B10 m3: released 284.62006 on 294 lines; HELD 140 = 95 bounded 37.518976 .. 73.227539 + 45 blank.
- After T-661 publishes (V3.0.62): NECK 32 bnd 8.7724 .. 11.3460 + 4 blank (>= 0.9515); BEAM released +0.549624,
  held 6.023085 .. 8.507278 + 12 blank.
- B11 kg: released 9,628.462205 detailed; HELD 799 blank + 900 bounded 15,130.867712 .. OPEN; ratio ESTIMATE
  2,204.24 .. 2,909.02 kg unwired (0 of 28 rows wiring-ready, Q-81).
- T-658 r2 (merged research): GB 9 bnd 1.173410 .. 5.096771 + 16 LOWER_ONLY 5.069839 + 4 blank.

## Live rows (04:14)
- READY: T-661 PUBLISH-ONLY (Checker FIRST). CLAIMED: none.
- TODO: S: T-666 (W1 FIRST: F-T661-1 junction squares + boundary band); A: T-667 (W2 FIRST: pool blinding);
  I: T-665 (W3 FIRST: T-658 r2 into the candidate; may base on agents/task-T-661 @ 6d40475f).
- BLOCKED-OWNER: T-664 (Q-81). QUEUED: T-372, T-363, T-424 (W1); T-314 r3, T-364, T-513, T-502 (W2); T-382, T-509 (W3).
- IN PROGRESS: T-180 (P17 footings once T-661 is published, then P18). PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-666, T-372, T-363, T-424; A (worker 2): T-667, T-314, T-364, T-513, T-502;
  I (worker 3): T-661, T-665, T-664, T-382, T-509. Queue check 15 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-661 published on origin (verify sha with ls-remote); scoreboard restated; report B10 before / after.
2. T-665 concrete round 2 READY + Gate B (one hub package at a time).
3. T-666 (gate 1; never delayed more than 2 Checker runs), T-667; then boundary band wiring.
4. Q-81 answer -> T-664 (ratio Gate B). Until then masonry may take the hub after T-665: T-372, T-363, T-314 r3.
5. 12-13 Nov reconciliation + scorecard.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; a status cell with 'after T-nnn' reads as
  WAITING. Status word FIRST; 7 cells; NEVER a '|' inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head, checked only after the
  predecessor is published. A Checker finding gets its fix row in the next Lead run.
- PROPOSED 04:14: MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin.
- F-T662-1 ACCEPTED (never both ways). F-T661-1 lesson PROPOSED (near face unless junction owned by no other line).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). FIN.PLASTER released 363.3738 m2.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- Q-81 (rebar ratio; now blocks all ratio wiring). ORR-007 stair skirting payable form. Worker prompts 'never
  approximate steel'. Freelancer floors / rails workbooks + 1990 spec (coming); privacy switch; PyMuPDF review after
  10 Nov; Q-34 2F top roof at the 12-13 Nov milestone; token plan Stage 2 after 10 Nov; Scout paused.
