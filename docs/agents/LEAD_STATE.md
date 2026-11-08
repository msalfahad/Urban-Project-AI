# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 52230429..`,
`git -C .work/board log <board commit of this run>..`, `git log 134cd005..` on main, RUN_LOG lines after 20:14Z 8 Nov,
rows changed since), then rewrite.

## Last seen
- engine: 52230429 (T-639 / T-634 merges; before 175443b8 T-638, 36f53264 T-640); candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged.
- main: 134cd005. PR #4 OPEN on GitHub (checked 20:15 8 Nov, head fd71bc30, mergeable clean) although the 12:40 owner
  directive row says "merged by the owner": reported in NEEDS FIXING, not treated as merged.
- board: this run's final commit (Lead 2026-11-08 20:1x)
- last Lead run: 2026-11-08 20:14-20:3x UTC (run unknown)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 (BOARD top): delivery first; 10 Nov TRIAL BOQ, every trade, every HELD with a cause;
  no new investigation tasks (fix rows that wire or prove a quantity only); report only WIRED quantities and
  Checker-verified whole lines; Gate B order after PR #4: T-525 -> T-498 -> T-423 r2 -> T-563 -> T-314 -> V14 fix rows.

## Run health
- Since 16:12: 10 runs, all closed, 0 empty; 4 merged, 1 rejected narrow (T-637 r1), READY 1 (T-637 r2).
- No wrapper bypass since W1 15:33. venv 'No module named pytest' at W1 19:21 / Verifier 19:51, fixed by setup: watch.
- Verifier wrote T-627 ruling into an extra cell (fixed by Lead 20:15): watch row format in verdicts.
- tests/t485 + t374 x2 red on the working branch = baseline (T-525).

## Live rows (20:15)
- READY: T-637 r2 (W3 20ce44b0; delay cause CHECKER-RUNS).
- TODO: S: T-642 (FIRST Checker fixes + parapet 4), T-643 (rebar on HELD concrete, 208 unbound), T-633; A: T-644
  (FIRST lintels as pcs), T-645 (B7 stair finishes 31), T-646 (B13 roof / fence 43); I: T-641 (FIRST V17 incl.
  T-634/638/639/640 + F-T627-1), T-636 (trial BOQ, after T-641 + T-637 MERGED), T-635.
- BLOCKED (PR #4 only): T-525, T-498, T-563 (W3), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (P02 GF 18 / 21 + B3 / B4; P04 closed; next P05..P09 / P12..P14; T-597 trench).
  PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-642, T-643, T-633, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-644, T-645, T-646,
  T-513, T-314, T-502; I (worker 3): T-641, T-636, T-635, T-525, T-498, T-563, T-509, T-382, T-474.
- Next refill candidates (delivery only): B1 earthworks 15 HELD blank (T-509 / owner 2 Nov rules), B7-13 stair
  formwork 20 HELD blank, B8 penetrations 17 pcs HELD blank, B6 shutters 3 m2, B3 thresholds 8 m2.

## Top 5 priorities
1. 10 Nov trial BOQ: T-637 r2 merge + T-641 V17 -> T-636 (W3), with T-642..T-646 fix rows following as overlay.
2. PR #4 (owner). The run after it lands: Gate B in the owner's order, one at a time.
3. Checker: T-637 first, T-642 within 2 Checker runs once READY; T-180 light-run slots.
4. 12-13 Nov: T-635 statement + scorecard V12 (after T-636); Q-34 raised then.
5. When a package merges, promote its queued successor in the same run.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 7-cell rows; NEVER a '|' inside a cell text; `board check` pulls first: commit before.
  Stamp 'Lead YYYY-MM-DD HH:MM per' from `date -u` (never a placeholder).
- A Checker finding gets its fix row in the next Lead run.
- Register 20:15: PRECAST LINTEL PAYABLE FORM (B9-02 pcs; m3 HELD), ROOF BUILD-UP LAYERS (one roof area; B13-01 / B8-06),
  REBAR-TO-CONCRETE BINDING. 16:15: BLOCKWORK MATERIALS, LIFT LANDING DOOR, SLAB EDGE STRIP.
- Lessons 20:15: T-628 ADOPTED; PROPOSED T-637 (one work code per element and unit), T-643 (bar never more certain than
  its length inputs); T-614 row still PROPOSED (check its merge verdict).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 MERGED (default reader stays 1.0.0).

## Blockers
- PR #4 (owner). Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10
  width, lintel ends, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2, MS1-T winder
  fronts) keep lines HELD, never block integration.

## Open owner items
- PR #4 merge (CRITICAL; directive text says merged, GitHub says open). ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
