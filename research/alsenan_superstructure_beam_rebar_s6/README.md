# S6 - accurate superstructure beam rebar (simple + continuous beams)

**KNOWN SOURCE-DERIVED SUPERSTRUCTURE BEAM REBAR: 3630.15 kg (lower bound).**
**FINAL SUPERSTRUCTURE BEAM REBAR NOT ESTABLISHED.**

Built blind from the frozen PRE-S6 package only (hash-checked); engine `engine/source/superstructure_beam_rebar.py`,
builder `build_superstructure_beam_rebar_s6.py`, stamp `d39f5f6+code:add76dd5f5e9c59a`. Frozen in `S6_FREEZE_MANIFEST.json`
(FROZEN_BEFORE_REFERENCE_COMPARISON) before any reference was opened.

| | SIMPLE_BEAM | CONTINUOUS_BEAM |
|---|---|---|
| occurrences | 89 | 13 |
| occurrences by state | {'BLOCKED': 18, 'LOWER_BOUND': 71} | {'BLOCKED': 6, 'LOWER_BOUND': 7} |
| VERIFIED_KG | 0.00 | 0.00 |
| LOWER_BOUND_KNOWN_KG | 2824.46 | 805.69 |
| PROVISIONAL_KG | 0.00 | 0.00 |
| BLOCKED_MODELLED_KG | 0.00 | 0.00 |
| BLOCKED_UNQUANTIFIED mass components | 516 | 162 |
| blocked count records | 18 | 17 |
| known straight length (m) | 1725.298 | 440.825 |
| released by component | {'BOTTOM_MAIN': 71, 'STIRRUP_COUNT': 71, 'TOP_MAIN': 71} | {'BOTTOM_MAIN': 14, 'MID_TOP': 9, 'STIRRUP_COUNT': 12} |
| stirrup count records / stirrups (LB) | 71 / 1352 | 12 / 404 |

MID_KNOWN_KG 265.21 kg (CB MID support bars, straight extent only). STIRRUP_COUNT_KNOWN
83 records / 1756 stirrups (lower bound, no +1).
STIRRUP_MASS_KNOWN: 0 records (blocked: legs, path, hooks). Untagged geometry kept
visible: 38 (BLOCKED_TYPE). Diameter distribution: Ø12: 283.53 kg / 318.97 m; Ø14: 243.51 kg / 201.27 m; Ø16: 844.06 kg / 534.13 m; Ø18: 2071.97 kg / 1035.98 m; Ø20: 187.08 kg / 75.77 m.

## What the numbers are

* kg = count x straight run x D^2/162 on the PRE-S6 source segments only: simple beams support face to support
  face; CB bars clear span + through-support widths + 7.5 cm beyond the far face only where PRE-S6 bound that
  typical dimension to that bar; MID bars 0.22 x Ln (axis to axis, the drawing's own symbol) from each face + the
  support width - re-computed by the engine from the span table and checked against PRE-S6.
* Every released row is LOWER_BOUND: the straight segment is SOURCE_VERIFIED where its extent is complete, but no
  bar is called complete (development, hooks, in-span end treatment not established). VERIFIED_KG is 0 by design.
* PROVISIONAL_KG and BLOCKED_MODELLED_KG are 0: candidate bindings, width conflicts and other blocked occurrences
  carry no hidden kg; their counts, diameters and known geometry stay in the registers.
* ELEMENT_FAMILY is BEAM with ELEMENT_SUBFAMILY SIMPLE_BEAM / CONTINUOUS_BEAM: the frozen generic provenance contract
  (rebar_provenance) knows BEAM, not the subfamilies, and is not edited.

## Never released in S6
CB top bars (frame top bars, end-support bars '0.3 Ln2'), hangers, side bars ('2Ø12/30cm' text kept), development
and hooks, stirrup mass, opening extras (no physical opening in any beam), the curved ring beams, the cantilever,
WITH STAIR and planted-column spans, candidate bindings, width conflicts, CB2 / CB3 / CB4 / CB5 / CB8 / CB10, CB13
bottom bars (readings differ) and every untagged geometry. T/M values are design loads: excluded from parsing,
components, mass and BBS (token terminals EXCLUDED_DESIGN_LOAD).

## Scope
Widened components: 0 (must be 0). Narrower than PRE-S6: 0. S6.1 release candidates found
but not released (frozen scope): 2 - see `S6_1_RELEASE_CANDIDATES.csv`.

## Conservation
* component_length_equals_occurrence_known_length: True
* component_kg_equals_occurrence_known_kg: True
* occurrence_kg_equals_project_known_kg: True
* bbs_net_kg_equals_known_parts_kg: True
* bbs_length_equals_known_length: True
* every_component_terminates_per_occurrence: True
* component_records_unique: True
* bar_run_ids_unique_and_each_declared_run_terminates_once: True
* one_bar_run_per_source_frame_bar: True
* stirrup_records_one_per_span: True
* every_mass_component_is_one_accurate_part: True
* population_reconciles: True
* blocked_and_non_mass_components_carry_no_kg: True
* accurate_summary_reconciles: True
* every_component_passes_the_contract: True
* every_released_quantity_traces_to_rebar_tokens: True
* no_verified_complete_bar: True

## Questions
Carried from PRE-S6 (Q1-Q9, R1-R6): `SUPERSTRUCTURE_BEAM_ENGINEERING_QUESTIONS.csv`. An answer becomes a versioned
claim and an S6.1 delta; the S6 baseline is never rewritten.
