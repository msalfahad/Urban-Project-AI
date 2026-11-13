> DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md governs and wins over this document wherever they differ. Read it first.

# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since: `git -C .work/engine log 8d3bbf1c..`, board commits after
this run's, RUN_LOG lines after 16:31Z 13 Nov, rows changed since. Check every MERGED claim with
`git merge-base --is-ancestor <sha> origin/...`.

## Last seen
- engine origin head: 8d3bbf1c (T-761 merge). No owner commit on the engine. main d24e4497 unchanged.
- Last Lead run: 2026-11-13 16:31 UTC (session_01E6cPnbKcxVkiLBmNh56Jcy). Drive readable; no new file in the
  private folders since 12 Nov 12:00 (no photos).
- Candidate of record ARCH_TAKEOFF_V3.0.78 (T-738), registry 1.79.0 still PENDING [T-738] (merge 208c5689 did not
  promote). NOT RELEASED; released default V2.9 + route G untouched.

## Hub order (Lead 16:40, written in rows and the LEAD NOTE)
T-314 r4 (W2; V3.0.79; master 1.80.0 promotes T-738 + T-314; registry-only) -> T-770 r2 (W3; rebase by tools,
V3.0.81 kept, master 1.81.0; MAIN_FILL 81 non-formwork rows + formwork per Checker ruling + T-761 concrete if within
three families) -> T-750 (W3; V3.0.80 reservation lapsed, next free at claim) -> T-764 wiring.

## Open dispute (decide next run from the Checker's T-762 verdict)
- MAIN_FILL_ALL formwork 126 rows 472.8 m2 vs T-762 face set 240.6 m2 on the same lines (W1: host ratio applied to
  each partial line, hosts 2-4x). Checker asked to settle on one host by hand. CONFIRMED -> T-770 r2 wires T-762's
  formwork; the owner's fill_from_index.py formwork step needs his fix (told him by push 16:4x).

## Fill state (from handoffs, not yet wired except V3.0.78)
- Concrete: T-761 MERGED fix rows, 80 blank -> 0, +58.42 m3 + 1.00 SAFETY (unwired).
- Formwork: T-762 READY, 336 blank -> 0, 1,098.0 -> 2,226.9 m2 ESTIMATE/DEFAULT (no freelancer row).
- Ext render + paint: T-760 MERGED fix rows 1,054.00 m2 each vs freelancer 1,469.97 = -28.3 % RULE_DIFFERENCE; T-314
  wiring 1,008.58 .. 1,085.61 m2 (verified r3, merge blocked by registry only).
- T-770 r1 (unmerged): blank non-rebar 692 -> 551; roof finish 248.8 vs freelancer 285 m2 (-12.7 %); plaster
  1,254.7 m2 + held; paint 675.8; disposal 105.6 .. 115.5 m3 held.

## Live rows (16:40)
- READY: T-762 (Gate A). TODO: W1 T-757, T-767, T-769, T-772; W2 T-314 r4, T-763, T-765, T-766, T-768, T-774;
  W3 T-770 r2 (waits T-314 r4), T-764, T-750, T-771, T-775, T-773. QUEUED (folded): T-363, T-364, T-424, T-502,
  T-509, T-513. PAUSED: T-382, T-664, T-450 p2, T-451, T-472. IN PROGRESS: T-180.
- Queue check 24 actionable, 0 flagged, 0 stall.
- T-763 sharpened: MAIN_FILL already fills 11 dry-room plaster + 11 paint + bed points; only the rest.

## Rules decided (keep)
- Board check reads the newest line starting `Lead <date> <hh:mm>` that contains 'LANE ORDER:'; lanes separated by ';'.
- Status word FIRST; 7 cells; no '|' in a cell. MERGED only after `engine push` + sha on origin.
- Register: arris once; opening edges in paint = lm; flush parapet screen = one face; railings in the railing family;
  parapet block body -> A masonry, downstand -> B10; stair concrete + formwork S, finish faces A.
- Lessons: no new rows (owner reset). PROPOSED stay: L-T727-1, L-T738-1, L-T755-1.

## Blockers / open owner items
- DESIGNER_QUESTIONS (18) with the owner; ORR-007 stair skirting; Q-34 2F top roof; release switch T-773 is his.
- Scheduled-task frequency change recommended in DELIVERY_MODE s.7 (owner only). Scout paused.
