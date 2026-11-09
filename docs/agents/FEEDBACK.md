# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Lead 2026-11-09 08:20 (since 04:19)

- T-498 blockwork materials (Gate B step 2): WORKED (V3.0.59 4,999 same + 74 added; Checker own chain + 9 valued lines by hand AGREE). F-C-T498-1 stale cause on the 0.15 m hosts (Q-80 answered) -> T-652 values them from FR-T615. Merge left t485 red (T-498 pending in master 1.58.0) -> T-651 FIRST in lane I.
- T-647 r2 structural causes: WORKED (17 B11 lines HELD COUNT-CONVENTION GAP, 51.574073 kg bound, R-T647-1 (e)/(f) normal + adverse). Decision: into V19 (T-652).
- T-649 V18 + trial BOQ r2: WORKED (Checker own re-add B11 9,628.462205 kg and B7 AGREE; HELD with cause 2,351 / 2,744). Decision: base of V19 + trial BOQ r3 (T-652).
- T-635 statement V12 + scorecard V12: WORKED (VERIFIED rows 24 -> 52, UNKNOWN 295 -> 155; Checker hand re-add AGREE). F-C-T635-1 (B10 beams COUNT rows PARTIALLY VERIFIED) -> T-652 restates.
- T-648 finishes causes: FAILED at the merge gate (global Decimal precision at import broke t647 / t649 rebuilds in one session). Decision: r2 W2 FIRST, local context, one-session run of the merged suites.
- T-314 exterior plaster (Gate B 5th): PARTIAL (INCOMPLETE stage 37bc1c27; claimed ahead of the owner order and blocked T-423 r2 / T-563 on the m9 hub). Decision: TODO r2 after T-648 r2; Checker only after T-563 MERGED.
- T-650 re-measure (Checker light slot): D-1F-07 HELD BY NAME 0.036 .. 0.04377 m3 (START bearing 0.259 < 0.40), L-GF-01 re-measured. Decision: into V19 (T-652).

## Lead 2026-11-09 04:15 (since 00:19)

- T-646 B13 roof layers + fence finishes 43 HELD blank: WORKED (43 / 43 classed; screed AT_LEAST 10.628996 m3 .. OPEN; Checker own ROOF-430 screed and F-NORTH faces AGREE). Decision: rows into V18 (T-649).
- T-525 registry gate fix: WORKED (master 1.57.0 promotes T-507 only, t485 green, Checker reproduced the Drive chain V3.0.58 c9570e6c). Decision: T-649 / T-498 build on master 1.57.0; F-T525-1 stale B8-06 text cleared in T-649.
- T-650 lintel payable form: WORKED (60 / 60 RC cast m3 under the printed schedule; B9-02 low 0.502 -> 0.991692 m3, high OPEN). Decision: V18 (T-649) after the Checker's two missing re-measures (D-1F-07, L-GF-01); F-T650-3 ruled by the Lead this run.
- T-647 structural HELD causes 183: PARTIAL (REJECTED narrow: 17 B11 fix rows 51.574 kg called DRAWING-CONFIRMED on a count the drawing does not print). Decision: r2 TODO W1 FIRST, those 17 rows HELD as a count-convention gap with an adverse test; the rest of ec383e02 kept.
- T-633 blockwork 39 UNKNOWN rows: WORKED (own 231.6726 vs stated 231.6737 m2, residual -0.0011 TOLERANCE; D-GF-06 head class RD -> ER proposed). Decision: class move into statement V12 (T-635).
- T-498 blockwork materials (Gate B, owner order 2nd): CLAIMED W3 03:01, still running at 04:15. Decision: Checker's first Gate B slot when READY; T-423 r2 waits on its files.

## Lead 2026-11-09 00:15 (since 20:19)

- T-637 r2 master 1.56.0: WORKED (registered in RULES_MANIFEST, L4 = 3 pre-existing failures only). Decision: grouping for T-636 / T-649.
- T-641 manifest V17: WORKED (106 ops re-added AGREE). Decision: base of V18 (T-649).
- T-642 Checker P02 / P04 fix rows: WORKED (3 ENGINE_RIGHT, 1 SET 0.050 + HELD 0..0.025, BAND0049 DRAWING-CONFIRMED). Decision: V18 (T-649).
- T-644 lintels 60: PARTIAL (classed, but payable form conflicts with the printed RC schedule, F-T644-1). Decision: Lead ruling (schedule first) -> T-650 restate.
- T-645 stair finishes 31: WORKED (10 fix rows Checker AGREE); F-T645-1 ruled by the Lead. Decision: V18 (T-649) with the ruling.
- T-643 rebar on HELD concrete: WORKED (10 KEEP, 4 downgrade records validated, 208 classed). Decision: downgrades wired in V18 (T-649).
- T-636 the 10 Nov trial BOQ: PARTIAL (delivered, re-adds exact; 436 HELD without committed cause, F-T636-1). Decision: T-647 (S) + T-648 (A), then trial BOQ r2 (T-649).

## Lead 2026-11-08 20:15 (since 16:19)

- T-640 B4 / B5 finishes 72 HELD blank (Gate A): WORKED (72 / 72 classed, 33 bounded fix rows 87.234 .. 138.540 m2, F-T627-1 door heights ruled ENGINE_RIGHT 0.580 m2). Decision: wired as overlay in V17 (T-641).
- T-638 formwork 370 HELD blank (Gate A): WORKED (370 / 370 classed; +33.127 m2 fix rows, column shafts 27.002 m2 VERIFIED; split faces stay CALCULATED, F-C-T638-1). Decision: V17 (T-641); slab-edge strip stays HELD (no section).
- T-637 master 1.56.0: PARTIAL r1 (REJECTED narrow: file not registered in RULES_MANIFEST); r2 READY 20ce44b0. Decision: Checker first; T-636 waits for it.
- T-639 rebar 801 + 6 (Gate A): WORKED (807 / 807 classed; FR-T639-1..6 +412.444 kg Checker AGREE). Decision: V17 (T-641); F-T639-1 released bars on HELD concrete -> T-643.
- T-634 internal plaster / paint 31 rows (Gate A): WORKED (29 DRAWING-CONFIRMED, 2 DIFFER, GF-15 -0.015161 m2). Decision: V17 (T-641); statement V12 (T-635).
- Checker T-180 P02 / P04 slots: F-C-P02-13 (arc band, depth unsourced), F-C-P02-14 and F-C-P04-1 (omissions), GF B11 ENGINE_WRONG -0.003159 m3. Decision: one fix row T-642 (S FIRST).


