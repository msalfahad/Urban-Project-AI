# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 3d09bd8f..`,
`git -C .work/board log <board commit of this run>..`, `git log fd71bc30..` on main, RUN_LOG lines after 12:16Z 11 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 3d09bd8f (T-693 maps). Merges since 0b6d1bc2: 6ed575ad T-697, bbda7212 T-695, 3b0e03d4 T-699,
  65083ee7 T-701, f824c4d5 T-698 r2, 8210b549 T-700, b90d85af T-702, 2bfa2fbe T-693 Gate B (V3.0.70). Candidate of
  record ARCH_TAKEOFF_V3.0.70 e8e001de / master 1.71.0 (NOT RELEASED). Released V2.9 + G. No owner commit.
- main: fd71bc30. Last Lead run: 2026-11-11 12:16 UTC (session_01E6cPnesVSXsDpynqQ3D1Mi).
- Verifier run 11:50 (session_01E6cPncdZEPbJjz2ey34pSg) had no final line at 12:25: check it closed (else UNCLOSED).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-09 18:30: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> 38 missing families (MEP last). 11-08 12:40 directive (wire / prove only; Gate B one at a time); UPM
  untouched. No OWNER_SESSION_CHANGES row after 18:30.
- Hub order: T-704 (concrete r8 lintels, V3.0.71) -> T-703 (masonry r4) -> T-705's ordered list -> T-314 / T-364 /
  T-363 -> T-664 if Q-81 answered.

## Baseline (V3.0.70)
- STR.CONC: released 317 = 291.476251 m3; COLUMN held 11.67283 .. 15.5015 (27) + 2 blank (tank, D-44); keyed
  19.7765 + 20.44523 .. 26.8475 + 6 UNKNOWN; LINTEL 1.361 .. 2.050636 (24) + 21 blank (T-699 bounds -> T-704); BEAM
  consultant-blocked; band HELD Q-28; slab -0.77 % UNRESOLVED (T-706); plate +0.133640 NOT APPLIED (T-707).
- B9 as V3.0.68 (T-703 pending). FIN.PLASTER 388.584 + 1,131.966 .. 1,300.694 + 3 blank; FIN.PAINT 217.208 +
  601.645 .. 682.331. Like for like plaster -15.81 .. -9.88 %; shaft 54.00 / returns -8.19 UNRESOLVED (T-709).
- WP 53 HELD + 5 MISSING (T-710); tiles 104 HELD (T-702 r3 merged unwired); earthworks Z2 136.901 .. 163.479 (T-708).
  B11 detailed 9,628.462205 kg; ratio unwired (Q-81). Verified whole lines 1 (CONC.SLAB).

## Live rows (12:25)
- READY: none. CLAIMED: none. TODO: I: T-704 (W3 FIRST), T-705; S: T-706 (W1 FIRST), T-707, T-708; A: T-709 (W2
  FIRST), T-710. QUEUED: T-703 (after T-704), T-363, T-424, T-314, T-364, T-513, T-502, T-382, T-509. BLOCKED-OWNER:
  T-664 (Q-81). IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S: T-706, T-707, T-708, T-363, T-424; A: T-709, T-710, T-314, T-364, T-513, T-502; I: T-704, T-705,
  T-703, T-664, T-382, T-509. Queue check 18 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-704 lintel bounds Gate B; SCOREBOARD v2 restated on V3.0.70 (plaster like for like).
2. T-703 masonry limits after T-704.
3. T-706 slab residual; T-707 column tail (F-T689-1 ruling applied).
4. T-709 paint residuals; T-710 WP r3; T-708 earthworks r3.
5. T-705 wiring map -> beads / earthworks / annex plaster fix / tiles / roof WP packages; Q-81 -> T-664.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; status word FIRST; 7 cells; never a '|'
  inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; the next may be BUILT on a Gate-B-passed task head. L4 may span 2
  Checker runs (T-693 precedent).
- MERGED / scoreboard restatement only after `engine push` success and the sha seen on origin.
- Register rulings: arris once (B4-09 bead lm; T-314 faces m2 only); corner beads -> plaster; column tops under B8;
  wet band above ceiling -> plaster.
- Lead 12:25: F-T689-1 a rule conflict moves no quantity (settle by drawing); scoreboard plaster like for like, wet
  render / bands NOT_COMPARABLE, never blended.
- Lessons PROPOSED 12:25: like for like before calling a discrepancy (T-701); detector label is not a line field
  (F-T693-1); rule conflict settled by drawing (F-T689-1).
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- Q-81 (rebar ratio). ORR-007 stair skirting payable form. Decode wrapper raw-binary; L4 longer than one Checker
  lock on 2 cores (NEEDS FIXING, owner). Q-34 2F top roof. Scout paused. M3 estimate 13-14 Nov. Designer items keep
  lines HELD, never block integration.
