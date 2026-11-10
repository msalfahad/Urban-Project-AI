# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 169a4df2..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 00:16Z 10 Nov,
rows changed since), then rewrite.

## Last seen
- engine: 169a4df2 (T-662 merge; before 9c91709f T-660, d96a2958 T-657, 907ace46 T-659); candidate of record
  ARCH_TAKEOFF_V3.0.61 / BOQ_FAMILY_MASTER 1.62.0; released V2.9 + route G.
- main: fd71bc30. Gate B OPEN.
- board: this run's final commit (Lead 2026-11-10 00:1x)
- last Lead run: 2026-11-10 00:15-00:2x UTC (session_01E6cPndy5miudu2FdvQfWaF)

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 delivery directive still in force (wire / prove only;
  Gate B one at a time); UPM untouched. No OWNER_SESSION_CHANGES row after 18:30.

## Baseline for "before / after" (trial BOQ r4, candidate V3.0.61) - unchanged this run
- B10 m3: released 284.62006 on 294 lines; HELD 140 = 95 bounded 37.518976 .. 73.227539 + 45 blank.
- B11 kg: released 9,628.462205 detailed; HELD 799 blank + 900 bounded 15,130.867712 .. OPEN.
- Research (merged, unwired): necks 32 bnd 8.7724 .. 11.3460 + 4 lift >= 0.9515; small 6 bnd 13.279574 .. 24.498998;
  beams 1 value 0.549624 + 14 bnd 5.983085 .. 8.412278 + 12 blank; ratio ESTIMATE 2,204.24 .. 2,909.02 kg.

## Live rows (00:16)
- READY: none. CLAIMED: none.
- TODO: S: T-658 r2 (W1 FIRST, exact fault in row); A: T-663 rebar ratio wiring conditions (W2 FIRST);
  I: T-661 concrete Gate B (W3 FIRST; T-657/659/660 now, T-658 r2 only after it merges).
- QUEUED: T-664 ratio Gate B (W3 after T-661 + T-663); T-372 (re-scoped: F-T367-1 perimeter joints only), T-363,
  T-424 (W1); T-314 r3, T-364, T-513, T-502 (W2); T-382, T-509 (W3).
- IN PROGRESS: T-180 (P17 footings after T-661, then P18 ground slab). PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S (worker 1): T-658, T-372, T-363, T-424; A (worker 2): T-663, T-314, T-364, T-513, T-502;
  I (worker 3): T-661, T-664, T-382, T-509. Queue check 14 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-661 READY and merged; report B10 m3 before / after.
2. T-658 r2 (gate 1; never delayed more than 2 Checker runs), then restaged into the concrete package.
3. T-663 then T-664 (rebar ratio wired as ESTIMATE, separate subtotal).
4. Q-81 answer -> ratio for 6 types (new row when answered). PARTIAL members: blank groups HELD (no ratio).
5. Masonry after rebar: T-372 (perimeter joints), T-363; then T-314 r3. 12-13 Nov reconciliation + scorecard.

## Rules decided (keep)
- Board check reads the note line containing the literal 'LANE ORDER:'. Status word FIRST; 7 cells; NEVER a '|' inside
  a cell (Checker verdicts T-660 / T-662 had one: repaired 00:16). `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; second rebases on the first merged candidate; a rebased package promotes its
  merged predecessor. A Checker finding gets its fix row in the next Lead run.
- F-T662-1 ACCEPTED: no ratio on a member with a detailed count (never both ways). Lessons PROPOSED 00:16: a held bound
  of a linear member = drawn outline area x title (adopt when T-658 r2 merges).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). FIN.PLASTER released 363.3738 m2.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- Q-81 (rebar ratio, 6 types; pushed 00:16). ORR-007 stair skirting payable form. Worker prompts 'never approximate
  steel' (owner to align). Freelancer floors / rails workbooks + 1990 spec (coming); privacy switch; PyMuPDF review after
  10 Nov; Q-34 2F top roof at the 12-13 Nov milestone; token plan Stage 2 after 10 Nov; Scout paused.
