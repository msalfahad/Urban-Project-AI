# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log a7ee000d..`,
`git -C .work/board log <board commit of this run>..`, `git log 134cd005..` on main, RUN_LOG lines after 16:12Z 8 Nov,
rows changed since), then rewrite.

## Last seen
- engine: a7ee000d (T-627 / T-631 / T-628 merges; before 74e52c34 T-632 / T-630 / T-626, 47824e04 T-629 / T-625);
  candidate of record ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged.
- main: 134cd005 (PR #4 allow-list OPEN since 7 Nov 21:05, owner to merge).
- board: this run's final commit (Lead 2026-11-08 16:1x)
- last Lead run: 2026-11-08 16:12-16:2x UTC (run unknown)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 (BOARD top): delivery first; 10 Nov TRIAL BOQ, every trade, every HELD with a cause;
  no new investigation tasks (fix rows that wire or prove a quantity only); report only WIRED quantities and
  Checker-verified whole lines, before / after per trade; Gate B order after PR #4: T-525 -> T-498 -> T-423 r2 -> T-563
  -> T-314 -> V14 fix rows, one at a time.

## Run health
- Since 12:12: 10 runs, all closed, 0 empty; 8 merged, 0 rejected, READY 0.
- W1 15:33 again ran a builder with the venv python after the wrapper refused (also 11:45). In NEEDS FIXING with the
  owner. If it repeats on T-638 / T-639: send that row back (rework: pytest writer) and report again.
- Verifier stamps ahead of the clock (3x today, self-corrected): watch only.
- tests/t485 + t374 x2 (order-dependent) red on the working branch = baseline (T-525).

## Live rows (16:15)
- TODO: S: T-638 (FIRST formwork 370), T-639 (rebar 801), T-633 (backlog); A: T-640 (FIRST finishes 72), T-634
  (backlog); I: T-637 (FIRST master 1.56.0), T-636 (trial BOQ, after T-637), T-641 (V17, after T-636), T-635.
- BLOCKED (PR #4 only): T-525, T-498, T-563 (W3), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- Checker light-run item: rule F-T627-1 (DWF NE / SW elevations, D-GF-01 / -03 / -06 heads 2.20?).
- IN PROGRESS: T-180 (P02 GF 18 / 21; P04..P09 / P12..P14; T-597 trench). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-638, T-639, T-633, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-640, T-634, T-513,
  T-314, T-502; I (worker 3): T-637, T-636, T-641, T-635, T-525, T-498, T-563, T-509, T-382, T-474.
- Next refill candidates (delivery only): earthworks B1 HELD blank 15 (backfill / disposal: T-509, T-350 owner rules
  2 Nov), B9 lintels 54 HELD blank, B7 stair finishes HELD blank (flight 14, riser 13), B13 roof insulation /
  protection / screed 6 each, fence plaster / paint 8 each.

## Top 5 priorities
1. 10 Nov trial BOQ: T-637 -> T-636 (W3) with T-638 / T-640 / T-639 fix rows as overlay columns.
2. PR #4 (owner). The run after it lands: Gate B in the owner's order, one at a time.
3. Checker: T-637 first when READY, T-638 within 2 Checker runs; F-C/F-T627-1 in a light run.
4. 12-13 Nov: T-641 then T-635 statement + scorecard V12; Q-34 raised then.
5. When a package merges, promote its queued successor in the same run.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 7-cell rows; NEVER a '|' inside a cell text; never name another task id inside a TODO status
  cell unless it IS the dependency; `board check` pulls first: commit before. Stamp 'Lead YYYY-MM-DD HH:MM per'.
- A Checker finding gets its fix row in the next Lead run.
- Register 16:15: BLOCKWORK MATERIALS AND REGISTER CODES (B9 owner; units = MATERIAL, mortar / glue = B9-04),
  LIFT LANDING DOOR (B6 own family, HELD), SLAB EDGE STRIP (B10 slab, T-638 D). Earlier: BEAM UPSTAND EXTENT, OPEN-PLAN
  FLOOR BOUNDARY, 0.15 m BLACK BLOCK MODULE, CURVED-BAND OPENING HEAD, LIFT LANDING HEAD.
- Lessons 16:15: T-632, T-625 ADOPTED; PROPOSED T-628 (range from drawn extremes) and T-637 (one work code per
  element and unit; carrier codes NOT_A_BOQ_LINE); T-614 row still PROPOSED (check its merge verdict).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 MERGED (default reader stays 1.0.0).

## Blockers
- PR #4 (owner). Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10
  width, lintel ends, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2, MS1-T winder
  fronts) keep lines HELD, never block integration.

## Open owner items
- PR #4 merge (CRITICAL). ORR-007 stair skirting payable form. W1 wrapper fallback (asked: merge or prompt fix).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
