# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Lead 2026-11-08 20:15 (since 16:19)

- T-640 B4 / B5 finishes 72 HELD blank (Gate A): WORKED (72 / 72 classed, 33 bounded fix rows 87.234 .. 138.540 m2, F-T627-1 door heights ruled ENGINE_RIGHT 0.580 m2). Decision: wired as overlay in V17 (T-641).
- T-638 formwork 370 HELD blank (Gate A): WORKED (370 / 370 classed; +33.127 m2 fix rows, column shafts 27.002 m2 VERIFIED; split faces stay CALCULATED, F-C-T638-1). Decision: V17 (T-641); slab-edge strip stays HELD (no section).
- T-637 master 1.56.0: PARTIAL r1 (REJECTED narrow: file not registered in RULES_MANIFEST); r2 READY 20ce44b0. Decision: Checker first; T-636 waits for it.
- T-639 rebar 801 + 6 (Gate A): WORKED (807 / 807 classed; FR-T639-1..6 +412.444 kg Checker AGREE). Decision: V17 (T-641); F-T639-1 released bars on HELD concrete -> T-643.
- T-634 internal plaster / paint 31 rows (Gate A): WORKED (29 DRAWING-CONFIRMED, 2 DIFFER, GF-15 -0.015161 m2). Decision: V17 (T-641); statement V12 (T-635).
- Checker T-180 P02 / P04 slots: F-C-P02-13 (arc band, depth unsourced), F-C-P02-14 and F-C-P04-1 (omissions), GF B11 ENGINE_WRONG -0.003159 m3. Decision: one fix row T-642 (S FIRST).

## Lead 2026-11-08 12:13 (since 08:19)

- T-615 Q-80 0.15 m block module (Gate A): WORKED (rule version 1.1.0, 175.871 m2 out of HELD, Checker own count AGREE). Decision: quantities chained in V15 (T-629) behind T-498.
- T-620 statement + scorecard V11: WORKED (no quantity moved; floor tile UNKNOWN 41 -> 1). Decision: V12 (T-635) after the 8 Nov evidence rows merge.
- T-622 wall tile 47 rows (Gate A): WORKED (42 DRAWING-CONFIRMED, 5 DIFFER, 3 rooms Checker-VERIFIED; GF-14 +0.086709 high, pantry -0.0328 short ENGINE_WRONG). Decision: pantry in V15; GF-14 into V16 (T-631).
- T-623 beams / columns 18 rows (Gate A): WORKED (15 / 16 within 0.001 m3; CB12 split corrected; 2 THROUGH_SUPPORT stay UNRESOLVED). Decision: fold into V12 (T-635); Checker's B20 upstand reading later contradicted by F-C-P02-12 -> T-632.
- T-624 beam-end open items (Gate A): WORKED (FR-T624-1..3 +0.009714 m3; B10 66.401795). Decision: V16 (T-631), cut after V15 missed it.
- T-625, T-629: READY. Decision: T-629 first (V15 base for T-631 / T-630), T-625 second.
- Worker 1 11:45: wrapper refused a research script; ran it with the venv python directly. Decision: board note: drive research scripts through pytest or record BLOCKED until PR #4; owner told under NEEDS FIXING.

## Lead 2026-11-08 08:19 (since 04:15)

- T-617 lift landing head (Gate A): WORKED (bounded by ring-beam soffits, low end HELD, 0.000 m2 change). Decision: fold into statement V11 (T-620); FR-T617-1 into manifest V15 (T-629).
- T-614 r2 beam-end census (Gate A): WORKED (billing only inside the line's own extent, +0.061576 m3 fix rows, Checker re-measured 3 pieces). Decision: open items CB4 r2 0.01355 m3 + 5 T-229 add pairs -> T-624.
- T-618 small finishes residuals (Gate A): WORKED (causes or ranges; E1 porch 3.50 lm omission candidate HELD; curved / corridor UNRESOLVED needing his sides). Decision: fold into V11; FR-T618-1 / -2 into V15.
- T-619 manifest V14 (Gate A): WORKED (B10 66.392081 .. 66.393376 m3 as a range, passages 9 -> 6, Checker re-added). Decision: F-T619-1 / -2 -> T-624; next V15 (T-629).
- T-621 floor tile rows (Gate A): PARTIAL (40 / 41 by handle; 3 rooms Checker-VERIFIED; row 0 round-stair footprint unmeasured, open-plan boundaries not closable on wall faces). Decision: T-625 with the boundary-per-open-side rule.
- T-615 Q-80 block walls: READY. Decision: first Gate A item in the next Checker run.
- Worker 3 05:00 BLOCKED (venv pip download 403): environment, self-recovered at 06:59; no action beyond watching for a repeat.
