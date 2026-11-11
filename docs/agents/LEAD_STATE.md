# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 8294c146..`,
`git -C .work/board log <board commit of this run>..`, `git log fc03a1fb..` on main, RUN_LOG lines after 16:15Z 11 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 8294c146 (T-705). Merges since 3d09bd8f: 11489726 T-706, fe461c6e T-709, f34a5baa T-707,
  4a34ced0 T-710, 8294c146 T-705 (all research, unwired). T-704 Gate B REJECTED (firewall). Candidate of record
  ARCH_TAKEOFF_V3.0.70 e8e001de / master 1.71.0 (NOT RELEASED). Released V2.9 + G. No owner commit.
- main: fc03a1fb (PR #5 merged by owner). PR #6 decode fix open. Last Lead run: 2026-11-11 16:15 UTC (run unknown).
- Drive: no file in the private folders modified after 16:00 10 Nov.

## Governing
- OWNER DECISION 2026-11-11 15:30: rebar PARKED (T-664, T-382 parked, out of lane orders; Q-81 DEFERRED; tons at the
  end); join approved work first (next two Gate B = T-704 r2, T-703); version reservation in the row; ONE designer list
  (DESIGNER_QUESTIONS.md, Lead keeps it, owner sends it); idle slots draft the 38 missing families, one per run.
- OWNER DECISION 2026-11-09 18:30 order: concrete -> (rebar parked) -> masonry -> plaster / paint -> tiles -> WP ->
  earthworks -> missing families (MEP last). UPM untouched.
- Hub order: T-704 r2 (V3.0.71) -> T-703 (V3.0.72) -> T-717 (V3.0.73) -> formwork T-638 fix rows / beads H2a / T-314 /
  tiles H3 / WP+roof H4 (needs Checker downgrade record for roof 115.832) / earthworks H5.

## Baseline (V3.0.70)
- STR.CONC released 317 = 291.476251 m3. HELD: COLUMN 27 bd 11.6728 .. 15.5015 + 2 blank (tank LOWER_ONLY 0.3287 each,
  T-707 low 11.80007 not wired); LINTEL 24 bd 1.361 .. 2.0506 + 21 blank; BEAM 14 bd 5.9832 .. 8.4127 + 12 blank;
  GROUND_BEAM 9 bd 1.1784 .. 5.0968 + 20 blank; NECK 32 bd 8.7724 .. 11.346 + 4 blank; STAIR 5 / PARAPET 4 / LIFT 2
  blank; slab 1F -0.556333 UNRESOLVED (typed reference row). FORMWORK 370 HELD blank.
- FIN.PLASTER 388.584 + 1,131.966 .. 1,300.694 + 3 blank; FIN.PAINT 217.208 + 601.645 .. 682.331; like for like
  plaster -15.81 .. -9.88 %; shaft 13.50 m2 UNRESOLVED. WP 53 HELD + 5 MISSING (46 designer, 8 measured unwired);
  recess 0 .. 13.335 (D-41). MAS.BLOCK 15 HELD blank. B11 detailed 9,628.462205 kg (parked). Verified whole lines 1.

## Live rows (16:25)
- READY: none. CLAIMED: none. TODO: I: T-704 r2 (W3 FIRST), T-716; S: T-711 (W1 FIRST), T-712, T-708, T-714;
  A: T-713 (W2 FIRST), T-715. QUEUED: T-703 (after T-704), T-717 (after T-703), T-363, T-424, T-314, T-364, T-513,
  T-502, T-509. PARKED (QUEUED): T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- LANE ORDER: S: T-711, T-712, T-708, T-714, T-363, T-424; A: T-713, T-715, T-314, T-364, T-513, T-502; I: T-704,
  T-716, T-703, T-717, T-509. Queue check 20 actionable, 0 flagged, 0 stall.

## Top 5 priorities
1. T-704 r2 Gate B (lintel AT_MOST, R-T704-2); SCOREBOARD v2 restated after it.
2. T-703 masonry limits, then T-717 plaster / paint + bands.
3. T-711 / T-712 concrete blanks; T-714 formwork limits.
4. T-713 masonry rest; T-715 stair finishes; T-708 earthworks r3.
5. T-716 designer census -> DESIGNER_QUESTIONS.md per item.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'; status word FIRST; 7 cells; never a '|'
  inside a cell. `board check` pulls first: commit before.
- Shared hub: one Gate B package at a time; L4 may span 2 Checker runs. MERGED only after `engine push` + sha on origin.
- Register: arris once (B4-09 bead lm; T-314 faces m2 only); corner beads -> plaster; wet band above ceiling and
  double-height bands -> plaster; stair concrete = S, stair finish faces = A.
- Lead 16:25 rulings: R-T704-2 AT_MOST on one geometry stopper to stopper; F-T705-1 bead takes its host's height
  state (HELD with host bound, released with host); F-T705-2 released roof line downgraded only by a Checker
  downgrade-only record. Lead 12:25: rule conflict moves no quantity (settled by drawing); scoreboard like for like.
- Lessons 16:25: F-V704-1 ADOPTED, F-T689-1 ADOPTED, T-701 ADOPTED; T-706 reference formula, T-709 band PROPOSED.
- Materials: FINISH V7, PLASTER V3; UPC-BLACK-BLOCK-001 1.1.0 (Q-80).

## Blockers / open owner items
- ORR-007 stair skirting payable form. Q-34 2F top roof. Decode PR #6 open; L4 longer than one Checker lock (NEEDS
  FIXING, owner). Scheduled-task edits approved but not possible under repo settings. Scout paused. M3 estimate 13-14
  Nov. Designer items keep lines HELD, never block integration.
