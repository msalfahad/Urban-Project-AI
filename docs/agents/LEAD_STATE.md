# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log d16f4c7a..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 20:13Z 9 Nov,
rows changed since), then rewrite.

## Last seen
- engine: d16f4c7a (T-656 merge; before bfea3449 T-655, dfd7a2cf T-654); candidate of record ARCH_TAKEOFF_V3.0.61 /
  BOQ_FAMILY_MASTER 1.62.0 (t485 green); released V2.9 + route G.
- main: fd71bc30. Gate B OPEN.
- board: this run's final commit (Lead 2026-11-09 20:1x)
- last Lead run: 2026-11-09 20:13-20:2x UTC (run unknown)

## Governing
- OWNER DECISION 2026-11-09 18:30 (BOARD top note; overrides 11-08 ordering): concrete first (B10 held lines measured
  from the drawings) -> rebar by owner-approved ratio (AGENT_BRIEF 'Rebar by ratio') -> masonry -> plaster / paint ->
  tiles -> WP -> earthworks -> 38 missing families (MEP last). Q-79 answered 1:4 / 1:4 / 1:2. READY / CLAIMED Gate B
  packages finish; new rows only for these items; report per trade before / after in units.
- Still in force: 11-08 12:40 delivery directive (wire / prove only; Gate B one at a time); UPM untouched.

## Baseline for "before / after" (trial BOQ r4, candidate V3.0.61)
- B10 m3: released 284.62006 on 294 lines; HELD 140 = 95 bounded 37.518976 .. 73.227539 + 45 blank.
- B11 kg: released 9,628.462205 detailed; HELD 799 blank + 900 bounded 15,130.867712 .. OPEN.
- B10 m2 formwork: released 1,061.104461; 316 HELD blank + 4 bounded.

## Live rows (20:16)
- READY: none. CLAIMED: none.
- TODO: S: T-657 necks (W1 FIRST), T-660 beams (W1 2nd); I: T-658 columns / GB / straps / footing (W3 FIRST);
  A: T-659 small concrete elements (W2 FIRST), T-662 rebar ratio calibration (W2 2nd).
- QUEUED: T-661 concrete Gate B + F-T655-1 helper (W3 after the first concrete piece MERGED); T-314 r3 (W2 after
  T-661); W1 T-372, T-363, T-424; W2 T-364, T-513, T-502; W3 T-382, T-509.
- IN PROGRESS: T-180 (next P17 footings 64.304 m3, then P18 ground slab). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-657, T-660, T-372, T-363, T-424; A (worker 2): T-659, T-662, T-314, T-364, T-513, T-502;
  I (worker 3): T-658, T-661, T-382, T-509.

## Top 5 priorities
1. T-657 / T-658 / T-659 READY and merged (gate 1; each never delayed more than 2 Checker runs).
2. T-661 concrete Gate B as soon as the first piece merges; report B10 before / after.
3. T-660 beams, T-662 rebar ratio calibration; then a rebar-ratio wiring Gate B row (new, after T-662 MERGED).
4. Masonry next: re-scope T-372 against merged T-498 B9 materials before making it TODO; then T-363.
5. T-314 r3 after T-661; 12-13 Nov reconciliation + scorecard on concrete / rebar first.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time. A later Gate B step never holds the shared hub
  while an earlier step is unclaimed (ADOPTED 12:20).
- Status word FIRST; 7 cells: id | gate | title | description | STATUS | branch | verdict. NEVER a '|' inside a cell.
  `board check` pulls first: commit before. Never put T-ids after the lane I list in the Lead note (the check reads
  them as lane order). 'after T-xxx' only for live dependencies. Stamp from `date -u`.
- A Checker finding gets its fix row in the next Lead run. A merge that breaks a gate gets a fix row at the top of its lane.
- Lessons: ADOPTED 20:16 rebased package promotes its merged predecessor; registry tests pick writers among governed
  files. PROPOSED 20:16 an owner re-plan reaches the board before the next worker slot (4 empty slots 18:40-19:51).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80). Plaster: FIN.PLASTER released 363.3738 m2.

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-44, D-45, D-48, D-53 W02, D-02, D-1F-07,
  DOME-3 bars, lift-wall height, F-T583-1, F-T589-2, MS1-T winders, C-ST-4) keep lines HELD, never block integration.

## Open owner items
- ORR-007 stair skirting payable form. Worker prompts still say 'never approximate steel' (owner to align).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
