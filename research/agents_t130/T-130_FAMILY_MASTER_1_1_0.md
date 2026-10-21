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

Builder: `build_master.py` (checks every file:line exists, holds the symbol named after it (r3) and every commit
with git; exits 1 otherwise); run
summaries: `summ.py`; candidate runs: `run_facts.py`. They need the Drive DXFs in a scratch folder; nothing from Drive
is in the repository.

## Result

| State | 1.0.0 | 1.1.0 r1 | 1.1.0 r2 | 1.1.0 r3 |
|---|---|---|---|---|
| INTEGRATED_AND_TESTED | 8 | 3 | 1 (footings) | 0 |
| PARTIAL | 11 | 42 | 46 | 47 (+ footings) |
| IMPLEMENTED_NOT_INTEGRATED | 21 | 11 | 13 | 13 |
| EXPERIMENTAL | 13 | 4 | 4 | 4 |
| BLOCKED_BY_SOURCE | 17 | 17 | 17 | 17 |
| NOT_IMPLEMENTED | 29 | 22 | 18 | 18 |

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
| B1-02 Excavation | NOT_IMPLEMENTED | IMPLEMENTED_NOT_INTEGRATED | `engine/source/struct_n10.py:216` excavation(), `tools/struct_n10.py:40` build() (r3; r2 said :42), commit 40f3184, tests/m9_n10 (14 pass). Villa (tool on the released route G registers): 26 pits + 3 trenches, footprint 139.299 m2; volume HELD (working space and depth not stated); the 59 UNRESOLVED ground-beam rows give no trench. |
| B10-13 Formwork | NOT_IMPLEMENTED | IMPLEMENTED_NOT_INTEGRATED | `struct_n10.py:184` formwork(). Villa: slab soffit 379.041 m2, beam soffit 99.123 m2, beam sides 337.405 (TOTAL) / 458.025 m2 (BELOW_SLAB) side by side, footing sides 93.260 m2 FORMED or 0 EARTH_CAST, 311 faces HELD; owner conventions FW-D1..D4 open. |
| B8-07 Balconies | NOT_IMPLEMENTED | PARTIAL | Higher than the verifier asked: the RELEASED V2.9 (owner scope, V2.3+) already waterproofs a balcony drawn as a space, `engine/source/arch_measure.py:349` -> `owner_finish_scope.py:231`, FIN.WP.FLOOR PROVISIONAL, upturn held by specification; tested end to end `tests/m9_kb/test_kb_wp5.py:81` test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed() (r3; r2 said :80, a blank line) (8.0 m2). Opt-in V2.11+ FIN.WP.BALCONY `arch_v211.py:537`. Villa: no balcony label, 0 lines in both runs. Planters not measured. |
| B9-02 Lintels | INTEGRATED_AND_TESTED | PARTIAL | `generic_route.py:2030` _lintel_items() (r3; r2 said :2028, a blank line): lintels only with a printed lintel schedule. Villa: 0 lintel lines, family NO_EVIDENCE_FOUND, while the same run counts 27 windows, 17 doors, 11 passages; no hand check. |
| B10-08 Slabs | INTEGRATED_AND_TESTED | PARTIAL | Villa: 75 released lines 61.551 m3 + 1 held 2.740 m3 (dome opening / ring face, not slab per the hand ledger, Q-44 A); the slab hand ledger (T-139) is READY, not merged. |
| B4-08 Reveals | NOT_IMPLEMENTED | PARTIAL | r1 missed the released reveal path: `arch_v28.py:734` window_strip_lines() emits FIN.PLASTER 'window reveals' (:816, UP-REVEAL-001, PROVISIONAL) via `tools/urban_boq_m9.py:720` (r3: the call; r2 said :714, which the T-133 merge moved) in V2.8+, tested `tests/m9_p2b9/test_p2b9_openings.py:101`. Villa: all 27 ARCH.WINDOW_REVEAL lines BLOCKED_RFI (floor status / sill not established), 0 reveal records, 0 m2 released; door / passage reveals (`opening_reveals.py:46`) read by no method. |

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

## Rework r3 (verifier 2026-10-21 16:45, gate d: exact capability)

Fresh branch `agents/task-T-130-r3` from working head 8a22eec (T-133 V3.0.1, T-141, T-145, T-148, T-153 merged since
r2) with the r2 files re-applied; maps and the rules manifest rebuilt with the tools.

Counts (also in the file: capability_counts, capability_change_counts, in_v3_0_candidate_counts, tested to equal the families): changes 1.0.0 -> 1.1.0 r3: 33 raised, 8 lowered (footings added), 58 unchanged; in V3.0 / V3.0.1: 48 yes, 51 no.

| Verifier item | r3 |
|---|---|
| B10-02 footings must be PARTIAL | PARTIAL, with the evidence in the file: route G releases the conflict footing labelled F10 + F PROVISIONAL at the larger type (`engine/source/generic_route.py:542` FOOTING_LABEL_CONFLICT, CONVENTION_ONLY) while the verified T-126 piece holds it under owner Q-31 C (`engine/source/route_g_scope_v1.py:321` FOOTING_HELD_OR_IN_CONFLICT, merge cd34bd0; read only by the opt-in V3.0.1, merge 967d6d5); the verified T-060 ledger holds the footing edge band under owner Q-28 (`engine/source/concrete_ledger_v2.py:296` _band(), merge 9671133, read by no method); compared footing line UNRESOLVED (owner Q-12). States: INTEGRATED_AND_TESTED 0, PARTIAL 47 (both in the JSON counts and above). Development villa unchanged: 26 released footing lines, 66.264 m3, none held. |
| 3 wrong citations | generic_route.py:2028 -> :2030 _lintel_items(); tools/struct_n10.py:42 -> :40 build() (twice: B1-02, B10-13); test_kb_wp5.py:80 -> :81 with the test name. |
| `_resolves()` must check the named symbol | Every line citation must name a symbol right after it (name(), a dotted / underscored name, an UPPER name or a quoted string), and that symbol must stand on the cited line or the next 2 (anywhere in a cited range); a ':N' short citation binds to the file before it. Same check in the builder (exits 1) and in the test. Run on the r2 file against head 8a22eec it rejects 99 of 170 citations: 85 name no symbol (prose follows the line number; among them the verifier's test_kb_wp5.py:80) and 14 name a symbol that is not there: tools/struct_n10.py:42 build() x2 (the verifier's), 9 in tools/urban_boq_m9.py and 3 generic_route range citations whose family names sit above the range (GROUND_SLAB / SLABS at :1080, BEAMS at :834). The urban_boq_m9 lines were written on r1's base 05e2eab and never re-pointed: the file grew 8 lines by r2's base 0dec24c and 6 more in the T-133 merge (ARCH_ROOMS.json 246 -> 260, ARCH_FLOOR_AREAS.json 252 -> 266, _v29_facade 1260 -> 1274 x2, FACADE.json 2704 -> 2718, _v21_doors 2575 -> 2589 x3, _v29_masonry 1158 -> 1172; also the window_strip_lines call 714 -> 720, a no-symbol citation). generic_route.py:2028 passes the 'next 2 lines' rule (the def is at :2030) but is re-pointed to :2030 as asked. All 170 now name and hold their symbol. Limit, by the rule's own tolerance: a citation 1-2 lines above its symbol still passes. |
| I&T test checks the open-defect / unwired-correction clause | New test: an INTEGRATED_AND_TESTED family needs released lines, no held line AND no evidence / missing / note naming an open defect or an unwired correction ('read by no method', 'not wired', 'UNRESOLVED', 'HELD', 'read only by the opt-in'); the r2 B10-02 record is fed to it and refused on two counts, the same record without them passes. |

Also refreshed to the current head (no status change from these; the field "v3_0_planned_tasks" said T-133 on 12
families, which is now merged): pieces T-133 wired are named with their V3.0.1 evidence (B10-01 blinding 15.179 m3
released + 3 HELD lines and the verifier's defect D3; B10-06 columns 36.714 -> 34.446 m3, defect D1; B8-05 roll lines
with the V5 audit, 21 AGREES + 1 NOT_COMPARABLE); pieces it left waiting cite `engine/source/arch_v301.py:88` WAITING
(T-122 / T-129 landings, T-135 flights once, T-111 / T-105 stair concrete, T-105 / T-102 beams); B10-04 cites T-141
(6ab7719, not wired), B10-08 records T-139 REJECTED and T-145 (d0b91a4), plans T-139 / T-146; B11-01 cites T-136
(6d532c5, not wired) and T-148 (research), plans T-142 / T-151; B4-04 / B4-07 lose a T-133 plan that T-133 never had.
New item code without family: 'STR.CONC', a prefix filter of the V3.0.1 blinding total (`engine/source/arch_v301.py:489`).

Development-villa figures: the runs were NOT repeated (the session runs no engine tool on the Drive drawings except
through the project wrapper). The builder's reuse mode takes them from the r2 file and refuses unless the only modified
engine / tools file since the runs (0dec24c) is tools/urban_boq_m9.py, whose change is the opt-in V3.0.1 flag; the
added files (arch_v301.py, ground_system_spans_v2.py) are read by no released method. No quantity changes: the file is
read by no method (rule_store keeps 1.0.0); concrete compared lines unchanged.
