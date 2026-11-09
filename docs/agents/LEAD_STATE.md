# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log f136248f..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 00:12Z 9 Nov,
rows changed since), then rewrite.

## Last seen
- engine: f136248f (T-643 / T-636 merges; before ebc5a76a T-645, cc7f9a48 T-644, 57620ab8 T-641, 1c7411a5 T-642,
  deb7b86a T-637 r2); candidate of record ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.56.0; released V2.9 + route G.
- main: fd71bc30 = PR #4 MERGED by the owner 21:15 8 Nov (OWNER SESSION note). Gate B OPEN.
- board: this run's final commit (Lead 2026-11-09 00:1x)
- last Lead run: 2026-11-09 00:12-00:3x UTC (run session_01E6cPncJiAfQsqR4SGuXYmt)

## Governing
- OWNER DIRECTIVE 2026-11-08 12:40 + OWNER SESSION 21:15: delivery first; no new investigation tasks (fix rows that
  wire or prove a quantity only); report only WIRED quantities and Checker-verified whole lines; Gate B one at a time
  in the order T-525 -> T-498 -> T-423 r2 -> T-563 -> T-314 -> remaining V14 fix rows. UrbanProjectsManager untouched.

## Run health
- Since 20:14: 11 runs, all closed, 0 empty; 7 merged, 0 rejected, READY 0.
- venv 'No module named pytest' at first try W1 21:40, Verifier 23:04 / 23:59 (setup rebuilt): NEEDS FIXING note.
- tests/t485 + t374 x2 red on the working branch = baseline (T-525 fixes t485).

## Live rows (00:15)
- READY: none.
- TODO: S: T-423 r2 (FIRST, claimable, Gate B after T-498), T-647 (F-T636-1 structural 183), T-633; A: T-646 (FIRST),
  T-650 (lintel payable form, F-T644-1 ruling), T-648 (F-T636-1 finishes 183), T-314 (Gate B 5th); I: T-525 (FIRST,
  gate 0), T-498 (Gate B 2nd), T-649 (V18 + trial BOQ r2, F-T645-1 ruling, T-643 downgrades), T-635 (12-13 Nov), T-563.
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (P08 PARTIAL, P09 CLOSED; next P12..P14; T-597 trench). PAUSED: T-450 p2, T-451, T-472.
- Lane order: S (worker 1): T-423, T-647, T-633, T-424, T-364, T-363, T-372; A (worker 2): T-646, T-650, T-648, T-314,
  T-513, T-502; I (worker 3): T-525, T-498, T-649, T-635, T-563, T-509, T-382, T-474.
- Next refill candidates (delivery only): B1 earthworks 15 HELD blank (T-509 / owner 2 Nov rules), B7-13 stair
  formwork 20 HELD blank, B8 penetrations 17 pcs HELD blank, B6 shutters 3 m2, B3 thresholds 8 m2.

## Top 5 priorities
1. Gate B in the owner's order: T-525 then T-498 (W3), T-423 r2 built in parallel (W1); Checker one at a time.
2. Every HELD with a cause: T-647 / T-648 -> trial BOQ r2 in T-649 (W3 after T-498).
3. 12-13 Nov: T-635 statement + scorecard V12 (after T-649); Q-34 raised then.
4. Checker: T-525 first when READY; T-647 / T-650 (gate 1) never delayed more than 2 runs; T-180 light slots.
5. When a package merges, promote its queued successor in the same run (T-563 after T-498; T-314 after T-563).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 7-cell rows; NEVER a '|' inside a cell text; `board check` pulls first: commit before. Never write
  'after T-xxx' for a Gate-B-order-only dependency of a claimable row (makes it WAITING).
  Stamp 'Lead YYYY-MM-DD HH:MM per' from `date -u` (never a placeholder).
- A Checker finding gets its fix row in the next Lead run.
- Register 00:15: PRECAST LINTEL PAYABLE FORM RESTATED (printed RC schedule first, precast rule the rest). 20:15: ROOF
  BUILD-UP LAYERS, REBAR-TO-CONCRETE BINDING. 16:15: BLOCKWORK MATERIALS, LIFT LANDING DOOR, SLAB EDGE STRIP.
- Rulings 00:15: F-T644-1 (T-650), F-T645-1 (T-649: tread on held riser count released only on an independent edge census).
- Lessons 00:15: T-643, T-637, T-614 ADOPTED; PROPOSED T-644 (schedule before company rule), T-645 (shared stair
  inputs), T-636 (every HELD with a committed cause).
- F-C-T570-1, F-C-T593-1 (stair skirting; ORR-007 open with owner). F-C-T638-1 split faces stay CALCULATED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 MERGED (default reader stays 1.0.0).

## Blockers
- Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10 width, lintel ends,
  DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2, MS1-T winder fronts, C-ST-4) keep
  lines HELD, never block integration.

## Open owner items
- ORR-007 stair skirting payable form. venv incomplete at first use (NEEDS FIXING, agent code).
- Freelancer floors / rails workbooks + 1990 spec (coming, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
