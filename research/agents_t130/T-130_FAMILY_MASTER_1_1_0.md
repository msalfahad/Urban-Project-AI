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

| State | 1.0.0 | 1.1.0 |
|---|---|---|
| INTEGRATED_AND_TESTED | 8 | 3 (lintels, footings, suspended slabs) |
| PARTIAL | 11 | 42 |
| IMPLEMENTED_NOT_INTEGRATED | 21 | 11 |
| EXPERIMENTAL | 13 | 4 |
| BLOCKED_BY_SOURCE | 17 | 17 |
| NOT_IMPLEMENTED | 29 | 22 |

29 raised (each with a file:line in the released or opt-in path), 5 lowered, 65 unchanged. In V3.0: 46 yes, 53 no.

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
