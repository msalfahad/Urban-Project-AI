# T-587 reconciled-quantities statement V7 (research, unwired; for the 12-13 Nov milestone)

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-07. Files: `t587_adapters.py` (R-T587-1), `t587_build.py`
-> `out/RECONCILED_STATEMENT_T587.json` / `.md` (`--check` rebuilds identical), `tests/t587_statement_v7/` (14). The
T-586 builder is imported read only; the build first rebuilds V6 and refuses to run unless it equals its committed JSON
and markdown, then checks every V6 key is carried byte-equal (lists extended as a prefix only). Sources sha256-pinned
(T-576, T-578, T-583, T-584 outputs, V8, V6). No drawing, workbook or client data; no candidate, rule, knowledge or
registry file; no quantity moves; nothing released. Sign: reference - engine (T-576 / T-584 print ours - his: negated
once; T-578 prints his - ours: taken as is). T-581 stays pending r2.

## New and restated sections (residual 0 each; evidence per row from the Checker verdict)

| Section | Unit | Reference | Engine | Ref - eng | By class [evidence] |
|---|---|---|---|---|---|
| T-576 columns GF (restates V5 T-572 GF) | m3 | 11.531250 | 12.705000 | -1.173750 (-10.18 %) | ER +0.860 [V COUNT +1.03125, WP depth / base -0.17125]; RD -2.03375 [PV] |
| T-576 columns 1F (restates V5 T-572 1F) | m3 | 2.553 | 3.108 | -0.555 (-21.74 %) | RD -0.460 [PV]; ER -0.095 [WP] |
| T-576 GF, 10E0 C7 reading (CONFLICT, beside) | m3 | 12.46875 | 12.8175 | -0.34875 | ER +0.8825; RD -2.075; UNRES +0.84375 (CONFLICT_BOUNDED, WP) |
| T-576 1F, 10E0 C7 reading (beside) | m3 | 3.174 | 3.864 | -0.690 | RD -0.595 [PV]; ER -0.095 [WP] |
| T-545 beams@V7 (restates V4) | m3 | 66.093875 | 66.321054 | -0.227179 | GF B7 +0.120452 UNRES -> RD (PV, 2 / 14 ends); UNRES now 0 |
| T-578 rails | lm | 18.95 (lone typed constant) | 54.869174 | -35.919174 | ER -36.145174 [V RL-07 -15.953174, PV guards -19.150, WP RL-08 -1.042]; UNRES +0.226 [PV]; HELD 0 (>= 1.118196) |
| T-584 stair steps ST-01 / ST-02 | lm | 109.2 | 67.850 (released STEP_LM) | +41.350 | ER +2.95 width; HELD +20.4; RD +9.6 arrival edges; UNRES +8.4 (ST-01 +7 pieces); all PV |
| T-584 stair steps ST-01 / ST-02 | nr | 91 | 59 | +32 | HELD +17; RD +8; UNRES +7 (PV) |
| T-577 marble lm@V7 (restates V6) | lm | 21.7 | 56.83 | -35.13 | E1 step +11.20 UNRES -> ENGINE_WRONG [V], fix row FR-T584-1; 30A edge RD +2.8 [V]; door steps +7.7 UNRES [PV]; rest WP |

Beside, never added: T-578 nosing lm 123.2 vs census 87.35 (20 HELD), nr 96 vs 69: his stair-step cells are owned once
(ST-01 / ST-02 by T-584 steps, ST-03 E1 by T-577 marble lm@V7; census asserted); the candidate has no nosing line
(T-424). T-583: 4 rows at least 0.767783 t, high OPEN (laps, hooks, anchorage, ring depth), bounded part 1.164174 t is not
a high; 2 HELD_BLANK (DOME-3, lift walls kg(h) = A h + B, A 0.156642 .. 0.212859 t/m); valued 0. Expected after the V8
rows: G5 held at least 1.806943 t, residual vs his TYPED_LUMP at most 2.093057 t (was 1.294397 .. 2.127048), no %.
NOT_COMPARABLE added: his ST-01 / ST-02 count x width 109.2 booked in his area column. Door steps (beside): drawn 3.50 lm /
4 nr / risers 0.390 m2 (+ D-GF-09 0 .. 0.27 HELD), no line until T-592 sets ONE paid length (3.50 vs 3.80 lm).

## Corrections

- F-C-T586-1: `headline_v7` prints every V6 and V7 class split by evidence (V / PV / WP); T-577 ER -11.6888 m2 / -49.13 lm
  / -47 nr now read worker-proposed. V4 / V5 headlines are not restated (out of scope).
- F-T586-1: E1 step lm 11.20 UNRESOLVED -> ENGINE_WRONG (Checker VERIFIED ENGINE_OMISSION 04:05), in marble lm@V7.

## R-T587-1 (proposed, every villa; module docstring)

(a) evidence from the verdict by (report, cause), a row stamped otherwise is refused, headline by class and evidence;
(b) one reference cell, one section; another report's comparison of the same cells is a CROSS_REFERENCE beside;
(c) restate, never rewrite: same totals, a reclass per moved amount, the earlier section byte-equal and superseded;
(d) conflict readings shown under each reading, CONFLICT_BOUNDED -> UNRESOLVED by name; (e) a bounded part that excludes
named components is not a high; units never mixed.

## Findings

- F-T587-1: V5 HEIGHT_OPEN UNRESOLVED (GF -0.150, 1F -0.075 m3) is the JOINT_HEAD at the printed lower depth of the named
  framing member (T-576); RD now; the JOINT_HEAD / GLOBAL_DEPTH split stays bounded where D_ctrl is open.
- F-T587-5: the Checker reads the whole 1F +0.555 m3 as head ownership (RD); the worker's GLOBAL_DEPTH 0.095 ER is
  printed WP. The class split is open, the total is not.
- F-T587-6: his 123.2 lm stair-step cells were compared by T-577, T-578 and T-584 against three engine figures; V7 owns
  them once. Whether B7-05 nosing (census) and B7-06 step lm may both carry one drawn front edge is T-588's census.
- F-T587-7: V6 marble nr beside 'six doors = his six pieces' is a door count only; T-584 draws 4 steps (no id on his 6).

Lesson row proposal (ERS s.7): | 2026-11-07 | his stair-step cells were compared in three reports against three
different engine figures, and a worker-proposed class read as a Checker class in the headline | a statement owns each
reference cell once (others beside) and prints every class with its evidence status from the verdict line | R-T587-1
(a) / (b) (every villa) | tests/t587_statement_v7 | PROPOSED |
