# T-216: the floor-area reference line scored with the checker-verified review-set binding (opt-in key-map path)

Worker 3 (lane I), 2026-10-23, run started 19:00 UTC. Tooling only: no method, rule, registry, default or engine
quantity changes; released default stays ARCH_TAKEOFF_V2.9 + route G. Development villa, not an accuracy claim.
**integrates: T-208** (MERGED 54cb4c42, checker 11:08: Q-06 A class right for all three spaces; 3.1325 and 1.485 m2
re-measured 0.0 %, 4.7307 m2 DRAWING-CONFIRMED). ERS applied: s.2 step 1 (element: the internal floor finish key
FLOOR.INTERNAL = FIN.FLOOR.PORCELAIN + FIN.FLOOR.WET_TILE, one physical floor once), s.3 (one floor, one line).

## 1. What changed

| File | Change |
|---|---|
| `tools/alsenan_keymap.py` | additions: `load_set_bindings`, `subject_key_lines`, `bound_set_row`, `set_binding_report`, `set_bindings_markdown`, `with_set_bindings`, CLI `--set-bindings`; `engine_rows` calls the binding hook only when the key map carries `set_bindings` (the flag puts the file there in memory, so `tools/scoreboard_v2.py` v2 / v2.1 use it unchanged) |
| `research/agents_t216/build_set_bindings.py` + `ALSENAN_SET_BINDINGS_T216.json` | the development villa's binding file (URBAN_SCORER_SET_BINDINGS_V1), built from the merged T-208 files (`review_sets.bind_run`, rule Q-06 A) + the verdict commit 54cb4c42; `--check` reproduces it |
| `tests/t216_set_bindings` (34) | villa T216-V hand fixture (not Alsenan) + adverse cases + the development villa's file |

Rules (each a test): a bound set answers its key with the bound scenario's key items, evidence ASSUMED — OWNER-APPROVED
(own column, with rule id and verdict commit; never merged into released or DRAWING-CONFIRMED); an unbound or HELD
binding keeps the HELD row and the whole line HELD (never a partial sum, never 0); refused: wrong schema, rule not an
answered owner rule, no verdict commit / source, no evidence (fixture symbol, printed size), a set of another kind
(non-floor set), a bound scenario that still carries the closure strip of a space with a door closure, quantities
that are not this run's scenario (stale binding), a scenario the set does not have. **One floor, one line (found in
this run):** the V3.0.5 .. V3.0.8 candidates already floor the three spaces as their own lines (wet-room evidence:
WET_TILE PROVISIONAL 4.730695 / 3.1325 / 1.485, room ids = the sets' subjects), and the scorer scores a candidate beside
the BASE run's release report (T-177 finding 1). Applying the binding there would add 9.348 m2 twice; so a set whose
subject already has released line(s) of the key equal to the bound quantity adds nothing ("decided by own line",
listed); own lines that are held or differ keep the set HELD (conflict).

## 2. Runs (own, Python 3.11.17; Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip -> P7757.dxf ab54dd55, "ST7757 dxf.dxf" 9f9d1179)

Released baseline `V29_ROUTEG_NO_PROFILE` **REPRODUCED** (1,455 lines, BOQ_LINES.csv b96185d4, engine 17ed6f92);
T-167 chain + `research/agents_t193/v307_run.py`: V3.0.5 **76d75bde**, V3.0.6 **3e622799**, V3.0.7 **197c5599**
REPRODUCED; `research/agents_t231/v308_run.py` on the merged head: V3.0.8 **57fe219a** REPRODUCED (= T-231 Gate B).
Scorer: `bash scripts/agent_env.sh run tools/alsenan_keymap.py --run A --reference tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json
--key-map tests/alsenan/T001B_KEY_MAP.json --v2-verdicts research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json
--v2-candidate-lines V3_0_x_BOQ_LINES.json ... --set-bindings research/agents_t216/ALSENAN_SET_BINDINGS_T216.json`.
Without the flag every output (v1 JSON / md, v2.1 JSON / md on run A) is byte-identical to the 17ed6f92 tool
(sha256 equal); with it every non-floor row of every state is unchanged.

## 3. Result: floor area (key FLOOR.INTERNAL) vs freelancer 'total floors' FIN:الغلاف:15 = 409.58 m2

| State | Released lines | Bound sets (ASSUMED — OWNER-APPROVED, Q-06 A, 54cb4c42) | Held | Line | vs 409.58 |
|---|---|---|---|---|---|
| A (V2.9 + route G) | 376.2857 on 44 | 9.3482 on 3 (4.7307 + 3.1325 + 1.4850) | none | **COMPARED 385.6339** | **-23.946 (-5.85 %)**, was NOT YET MEASURED |
| V3.0.5 / .6 / .7 / .8 | 340.7645 on 46 (incl. the 3 spaces as own lines 9.3482) | 0 (3 decided by own line, not added again) | 1F living porcelain BOUNDED 38.4585 .. 38.9785 | **HELD** (bound 379.223 .. 379.743, development figure) | not scored |

Reconciliation A -> candidates, by room (all other 43 floor lines equal): 1F living 44.8694 released -> 38.4585 ..
38.9785 bounded (= 44.8694 - the 1F stair footprint 5.8908 (scope S4, T-116 / T-122: his stair sheet) - 0 .. 0.520
foot-of-flight pieces the drawing does not settle); +9.3482 the three hand-wash spaces as lines instead of sets. Like for
like (T-208 scope S1-S3 out of his figure: 409.58 - 13.986 - 8.194 - 7.700 = 379.700): A after S4 = 379.744 (+0.044,
+0.01 %, = T-208); candidates 379.223 .. 379.743 (-0.477 .. +0.043): the candidate's only open floor quantity is the
0.520 m2 at the foot of the 1F flights. The A -5.85 % is scope (S1-S4 -23.990), not accuracy. Floor area Verified share
stays 0 / 1 (whole-line rule; the line holds 376 m2 of released lines no checker re-measured as a whole).

## 4. Missing / held / for the Checker

- Candidate floor line HELD on the 1F living foot-of-flight pieces 0 .. 0.520 m2 (BOUNDED_EXPOSURE line of V3.0.5+):
  the next blocker of a scoreable candidate floor line (owner of that line: the stair-scope work, not this task).
- GF-RDBD4F9 4.7307 m2 stays DRAWING-CONFIRMED (worker reading, not re-measured); the binding file says so per set.
- The kitchen 9.630 m2 is porcelain (dry) in every state against Q-30 A (T-074 / T-218): wet / dry split only, the
  floor total is unaffected.
- Known limit (no output change): in a HELD floor line with a bound set, scoreboard v2's JSON field `released_part`
  counts the bound row with the released lines (it reads the scorer class); the cells and the binding table keep them
  apart. Not reachable in any current state (A is compared; the candidates bind nothing).
- Checker re-measure (Gate A of this tooling): the A floor line 385.6339 = 376.2857 released + 9.3482 bound (the two
  verified spaces 3.1325 / 1.485 are yours from T-208; GF-RDBD4F9 205 / 132 optional); the candidate reconciliation
  44.8694 -> 38.4585 .. 38.9785 (1F living, line L-b06400d4...) and that the three own lines carry the subjects' room ids.

## 5. Rule, test, lessons row

Rule (scope: any villa, any scorer side; provenance: Q-06 A, WORKFLOW_CONTROLS s.4-5, ERS s.3, T-177 finding 1): a
CONDITIONAL review set answers a scored key only through a binding with an answered owner rule and a checker verdict
commit, as ASSUMED — OWNER-APPROVED kept apart; a side that already floors the set's space by its own released line
answers it once by that line; anything else stays HELD and holds the line. Tests: tests/t216_set_bindings (normal:
50.25 m2 hand fixture; adverse: partial binding, held binding, held line, foreign key, no key item, unused binding,
13 refused files, strip carried, stale, other kind, missing scenario, decided by own line, conflicting own line).
Lessons-register row proposal: 2026-10-23 | a candidate scored beside the base run's release report would count the
three hand-wash spaces twice once their sets are bound (9.348 m2) | the scorer took every base-run set as unanswered,
although the candidate's wet-room evidence already floors those spaces as lines | bind only through answered rule +
verdict commit; a space the side already floors by its own released line equal to the bound quantity is answered once
by that line, a differing or held one keeps the set HELD (every villa) | tests/t216_set_bindings | READY.
