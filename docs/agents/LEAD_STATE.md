> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log e121e0b4..`,
`git -C .work/board log` after this run's commit, `git log d24e4497..` on main, RUN_LOG lines after 12:16Z 13 Nov,
rows changed since), then rewrite. Check every MERGED claim with `git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: e121e0b4 (T-756 merge, research). No owner commit.
- main: d24e4497 unchanged. Last Lead run: 2026-11-13 12:16 UTC (session_01E6cPnab3smX4vFuS44KkfF).
- UNCLOSED runs: Verifier 09:52 (merged T-756 10:00, no final line; lock expired 11:51), Worker 1 09:19 (resumed 11:21).
- Drive: no file created / modified in the private folders after 12:00 12 Nov.

## Governing
- OWNER DECISION 2026-11-13 12:00 DELIVERY RESET: materiality UP-QTY-MATERIALITY-001 (< 0.1 m3 ignored + logged,
  allowance max(1 m3, sum); other units < 1 % not worked; report 0.01 m3 / 0.1 m2 / 0.1 lm); company defaults: values
  from the owner only; owner sends DESIGNER_QUESTIONS; agents work ONLY on workbook gaps in order external render ->
  tiles + stairs -> WP -> earthworks -> roof layers -> missing families (MEP last). NO new census / statement /
  reconciliation / lessons rows; every new row moves a BOQ quantity.
- OWNER RULE 2026-11-12 PAINT (UP-FIN-PAINT-002). Rebar PARKED (2026-11-11). Only the main chat merges PRs.
- STACKING (Lead 13 Nov 12:30): T-314 r3 (V3.0.79, W2) and T-750 (V3.0.80, W3) built on T-738 r2 head 49d21678;
  Gate B one at a time T-738 -> T-314 -> T-750 -> T-509, each rebased by tools on its merged predecessor.
  Never write "after T-nnn" in a claimable row (queue_check reads it as WAITING).

## Baseline (V3.0.77 b8524d5c, NOT RELEASED)
- STR.CONC released 291.48 m3; 194 HELD (72 width < 0.1 m3: low 19.69, widths 3.83; 42 wider; 80 blank). Formwork 1,061.10 m2.
- FIN.EXT.FINISH 0 released; T-756 ledger render = paint 1,009.11 .. 1,087.62 m2; corners 176.94 .. 178.14 lm.
- FIN.PAINT released 217.21, held 603.80 .. 687.85 m2. FIN.PLASTER held 1,106.95 .. 1,302.17 m2.
- WP roof released 93.19 m2; WP 53 HELD + 5 MISSING. Roof layers B13-01: insulation / protection unprinted
  (need owner default values), screed AT_LEAST 10.63 m3 (T-646), all blank in the candidate.
- T-738 r2 figures (AGREE): stair wall tile 18.44 .. 44.77 m2, risers 13.09 .. 13.74 m2.

## Live rows (12:30)
- READY: T-738 r2 (Gate B, since 09:46, CHECKER-RUNS), T-755 r2 (Gate A, since 12:12, EVIDENCE).
- TODO: W1 T-757 (materiality, NEW); W2 T-314 r3 (stacked); W3 T-750 (stacked). QUEUED: T-509, T-363, T-424, T-364,
  T-513, T-502. PARKED: T-664, T-382. IN PROGRESS: T-180. PAUSED: T-450 p2, T-451, T-472.
- Queue check 14 actionable, 0 flagged, 0 stall.
- NEXT RUN: if T-738 merged -> SCOREBOARD v2 restate in queue; T-314 r3 Gate B next. If T-755 r2 merged -> counts
  for DESIGNER_QUESTIONS (owner sends it). T-757 merged -> wiring goes into the next free hub package (name it).

## Top 5 priorities
1. T-738 r2 Gate B (waiting a Checker run).
2. T-314 r3 exterior render + paint into the candidate.
3. T-750 WP; then T-509 earthworks.
4. T-757 concrete materiality -> +19.69 m3 released, allowance line.
5. Roof layers once the owner gives default values.

## Rules decided (keep)
- Board check reads the newest Lead note line containing 'LANE ORDER:'. Status word FIRST; 7 cells; no '|' in a cell.
- MERGED only after `engine push` + sha on origin. Keep one claimable row per lane.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A.
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1.

## Blockers / open owner items
- Company default values (roof insulation / protection first). ORR-007 stair skirting payable form. Q-34 2F top roof.
  Scheduled-task edits approved but not possible under repo settings. Scout paused.
