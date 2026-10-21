# T-130: BOQ family registry 1.1.0 re-derived from the code and the runs (plan P-02)

New file `rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json`; `1.0.0` untouched. Nothing reads 1.1.0 yet
(`engine/source/rule_store.py:104` and the coverage census keep 1.0.0), so no run, census line or quantity changes.

## How each status was derived

1. Released configuration = the scored one: `ARCH_TAKEOFF_V2.9` + route G, conventions V6, no facts file. Run on the
   development villa's Drive DXFs (sha256 = SOURCE_MANIFEST) at working head 1513f1d (the later merges T-105 / T-135 add modules read by no method): exit 0, 1455 lines,
   `BOQ_LINES.csv` sha256 b96185d4..., the same line count the verifier scored.
2. Candidate = `ARCH_TAKEOFF_V2.13` with the T-120 project inputs (fixture reading, exterior spaces, pantry
   4.50 x 3.00 m typed): 579 architectural lines; wet-area floor membrane 85.621 m2 (= verifier run 44, 85.62).
3. Per family: which module emits its item codes (file:line), which method reads it (released / opt-in / none), which
   merged piece and verifier run checked it, what the two runs give (released lines and quantity, held lines with their
   bounded range, not-applicable lines), what is missing, and whether ARCH_TAKEOFF_V3.0 (T-131, READY) produces it.
4. Vocabulary kept (six states); definitions written into the file. INTEGRATED_AND_TESTED now also requires that no
   verifier-confirmed defect or unwired verified correction touches the released path.

The rule store admits only files its manifest lists (tests/m9_kb/test_kb_registry.py
`test_the_rule_store_gains_no_file`; the full suite caught this on the first commit): 1.1.0 is registered as an AUTHORED
file (`tools/m9_rules_manifest.py:31`, one tuple entry) and `rules/RULES_MANIFEST.json` rebuilt with
`tools/m9_rules_manifest.py build` (only the new entry is added; copies, exports and rule-set digests unchanged).
Regenerating 1.1.0 therefore needs the same manifest rebuild.

Builder: `build_master.py` (checks every file:line exists and every commit with git; exits 1 otherwise); run
summaries: `summ.py`; candidate runs: `run_facts.py`. They need the Drive DXFs in a scratch folder; nothing from Drive
is in the repository.

## Result

| State | 1.0.0 | 1.1.0 r1 | 1.1.0 r2 |
|---|---|---|---|
| INTEGRATED_AND_TESTED | 8 | 3 | 1 (footings) |
| PARTIAL | 11 | 42 | 46 |
| IMPLEMENTED_NOT_INTEGRATED | 21 | 11 | 13 |
| EXPERIMENTAL | 13 | 4 | 4 |
| BLOCKED_BY_SOURCE | 17 | 17 | 17 |
| NOT_IMPLEMENTED | 29 | 22 | 18 |

r2: 33 raised (each with a file:line in the released or opt-in path), 7 lowered, 59 unchanged. In V3.0 (merged b1a6d6d): 48 yes, 51 no. r1 figures: 29 raised, 5 lowered, 46 yes.

Raised because the released run emits the family's lines although 1.0.0 called them research or not implemented:
room register, room floor area, gross floor plate (file), voids, dry / wet floor tiles, threshold marble, skirting, wall
tile, plaster, paint, external facade run and finish (held), ceiling area (29 lines, 403.163 m2 released), door classes
(15 PVC, 2 aluminium), windows (27), stair treads (27.324 m2), risers (held), landings (bounded), step metres
(91.028 lm), guardrail (held), wet floor / doorway / wall-upturn membrane, blockwork wall run (216.931 lm, panels held).
Raised to IMPLEMENTED_NOT_INTEGRATED (opt-in only): pantry wet zone (V2.13), tile bed / screed (finish materials
table), membrane rolls (V2.11 .. V2.13: 52 rolls released, 1 held in the candidate run).

Lowered (verifier evidence; the code is unchanged, the 1.0.0 claim was too strong):
stair concrete (compared line UNRESOLVED; the flight piece, merged with T-105 as e74c182, is read by no method), blinding (only one bounded line; T-100 / T-126
scope), straps / ground beams (all 59 ground-beam lines bounded; T-073 strap correction not wired), columns (all 82
lines BLOCKED_RFI; T-100 phantom columns in the typed path), beams (24 spans bounded; T-085 binding correction about
+4.30 m3 and concrete ledger V3 (e74c182) not wired).

## Census gaps found (coverage_census.py, not changed here)

- B8-03 maps only `FIN.WP.UPTURN`; V2.4+ emits `FIN.WP.WALL_UPTURN`, so the released run reports the wet-room upturn
  NOT_FOUND_IN_SOURCE although 14 lines, 22.065 m2, are released.
- B6-02 / B6-03 / B6-04 count nothing (door classes and windows are all under B6-01).
- B9-01 maps `MAS.BLOCK` only (wall run, panel and volume lines are not counted).
- B3-04 threshold marble and B2-02 / B2-03 have no entry.
A census version that reads 1.1.0 and fixes these maps is a separate task (it changes run output).

## Engine vs freelancer (context only; never written into the rule store)

Unchanged by this task, from the verifier's scored rows: concrete compared lines 92.77 vs 111.81 m3 (-17.0 %);
plaster, paint and floor area HELD; door / window m2 unit-refused (engine gives pcs). The registry now says which of
these families the released method can quantify at all, which only an opt-in method can, and which none can.

## Rework r2 (verifier 2026-10-21 02:30, gate d / P-02)

Both runs repeated on working head 0dec24c (Drive DXFs, same sha256): released BOQ_LINES.csv byte-identical to r1
(sha b96185d4, 1455 lines); V2.13 candidate again 579 lines. The merge commit of the working head into the r1 branch
was refused by the session permission check ("[Untrusted Code Integration]"), so r2 is a fresh branch
`agents/task-T-130-r2` from the working head with the r1 files re-applied and the maps rebuilt with the tool.

| Family | r1 | r2 | Evidence (file:line, test, development villa) |
|---|---|---|---|
| B1-02 Excavation | NOT_IMPLEMENTED | IMPLEMENTED_NOT_INTEGRATED | `engine/source/struct_n10.py:216` excavation(), `tools/struct_n10.py:42`, commit 40f3184, tests/m9_n10 (14 pass). Villa (tool on the released route G registers): 26 pits + 3 trenches, footprint 139.299 m2; volume HELD (working space and depth not stated); the 59 UNRESOLVED ground-beam rows give no trench. |
| B10-13 Formwork | NOT_IMPLEMENTED | IMPLEMENTED_NOT_INTEGRATED | `struct_n10.py:184` formwork(). Villa: slab soffit 379.041 m2, beam soffit 99.123 m2, beam sides 337.405 (TOTAL) / 458.025 m2 (BELOW_SLAB) side by side, footing sides 93.260 m2 FORMED or 0 EARTH_CAST, 311 faces HELD; owner conventions FW-D1..D4 open. |
| B8-07 Balconies | NOT_IMPLEMENTED | PARTIAL | Higher than the verifier asked: the RELEASED V2.9 (owner scope, V2.3+) already waterproofs a balcony drawn as a space, `engine/source/arch_measure.py:349` -> `owner_finish_scope.py:231`, FIN.WP.FLOOR PROVISIONAL, upturn held by specification; tested end to end `tests/m9_kb/test_kb_wp5.py:80` (8.0 m2). Opt-in V2.11+ FIN.WP.BALCONY `arch_v211.py:537`. Villa: no balcony label, 0 lines in both runs. Planters not measured. |
| B9-02 Lintels | INTEGRATED_AND_TESTED | PARTIAL | `generic_route.py:2028`: lintels only with a printed lintel schedule. Villa: 0 lintel lines, family NO_EVIDENCE_FOUND, while the same run counts 27 windows, 17 doors, 11 passages; no hand check. |
| B10-08 Slabs | INTEGRATED_AND_TESTED | PARTIAL | Villa: 75 released lines 61.551 m3 + 1 held 2.740 m3 (dome opening / ring face, not slab per the hand ledger, Q-44 A); the slab hand ledger (T-139) is READY, not merged. |
| B4-08 Reveals | NOT_IMPLEMENTED | PARTIAL | r1 missed the released reveal path: `arch_v28.py:734` window_strip_lines() emits FIN.PLASTER 'window reveals' (:816, UP-REVEAL-001, PROVISIONAL) via `tools/urban_boq_m9.py:714` in V2.8+, tested `tests/m9_p2b9/test_p2b9_openings.py:101`. Villa: all 27 ARCH.WINDOW_REVEAL lines BLOCKED_RFI (floor status / sill not established), 0 reveal records, 0 m2 released; door / passage reveals (`opening_reveals.py:46`) read by no method. |

New in the file: `item_codes` per family (every quoted item code written in engine/source and tools/urban_boq_m9.py
has exactly one owner, or is listed in `item_codes_without_family`: ARCH.EXTERIOR, STR.CONC.OTHER (declared only),
FIN.FLOOR (a label)); `name_terms` per NOT_IMPLEMENTED family. New tests (tests/t130_family_master, 14 pass):
every written code owned once and none invented; no NOT_IMPLEMENTED family owns a written code or has a function in
engine/source carrying one of its name terms; INTEGRATED_AND_TESTED needs released lines and no held line on the
development villa; the six named families. 11 mutations caught, including the r1 file itself. A sweep of the 18
remaining NOT_IMPLEMENTED families found `FIN.HANDRAIL` (B7-10) declared in the item master
(engine/source/boq_line.py:91) but written by no module, so B7-10 stays NOT_IMPLEMENTED; struct_n10 holds stair
faces (B7-13) and backfill (B1-03) without measuring them, so both stay NOT_IMPLEMENTED.

Footings (the one family left INTEGRATED_AND_TESTED): 26 released lines, none held, in the released run. Worth a
verifier look: T-126 reads footing F10 as HELD under owner Q-31 C in the unwired scope piece, while the released route G
releases it (1 PROVISIONAL line); if the verifier counts that as an open defect on the released path, B10-02 is PARTIAL
too.
