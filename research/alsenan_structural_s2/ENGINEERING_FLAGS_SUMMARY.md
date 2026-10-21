# ENGINEERING FLAGS SUMMARY - Alsenan (S2)

Front-summary lines (generated):

- 71 structural flags open
- 53 affect concrete
- 50 affect formwork
- 1 affect other
- 67 affect reinforcement
- affected measured quantity = 650.97 m beam (summed per flag; an element in several flags counts once per flag - use component_release for de-duplicated totals)
- affected measured quantity = 995.383 m2 plan (summed per flag; an element in several flags counts once per flag - use component_release for de-duplicated totals)
- affected measured quantity = 44.0 nr (summed per flag; an element in several flags counts once per flag - use component_release for de-duplicated totals)
- affected measured quantity = 251.0 nr occurrences (summed per flag; an element in several flags counts once per flag - use component_release for de-duplicated totals)
- final quantity pending consultant = yes

| Discipline | Total | Open | Provisional | Resolved |
|---|---|---|---|---|
| STRUCTURAL | 71 | 47 | 24 | 0 |
| ARCHITECTURAL | 0 | 0 | 0 | 0 |
| MEP | 0 | 0 | 0 | 0 |

Open flags by effect (structural):

- BLOCKED_QUANTITY: 41
- NO_QUANTITY_IMPACT: 5
- LOWER_BOUND_QUANTITY: 4
- QUANTITY_AFFECTED: 21

Open flags by issue type:

- AMBIGUOUS_APPLICABILITY: 17
- ENGINEERING_METHOD_REQUIRED: 2
- MISSING_DETAIL: 2
- MISSING_DIMENSION: 7
- MISSING_SCHEDULE: 4
- RULE_GAP: 3
- SOURCE_CONFLICT: 30
- UNBOUND_OCCURRENCE: 6

Component release over the census (measured-quantity basis: occurrences / m / m2 - no kg):

| Trade / unit | Released | Provisional | Lower bound | Audit only | Blocked |
|---|---|---|---|---|---|
| CONCRETE|m beam | 193.016 | 0 | 396.517 | 70.281 | 40.102 |
| CONCRETE|m2 plan | 370.501 | 30.278 | 167.636 | 0 | 56.327 |
| CONCRETE|nr | 25.0 | 0 | 0 | 0 | 1.0 |
| CONCRETE|nr occurrences | 61.0 | 29.0 | 0 | 0 | 5.0 |
| REINFORCEMENT|m beam | 1124.686 | 0 | 0 | 140.562 | 134.584 |
| REINFORCEMENT|m2 plan | 517.662 | 0 | 502.908 | 0 | 853.656 |
| REINFORCEMENT|nr | 34.0 | 0 | 0 | 0 | 44.0 |
| REINFORCEMENT|nr occurrences | 90.0 | 0 | 0 | 0 | 100.0 |

| Flag | Issue | Element | Effect | Severity | Status | Summary |
|---|---|---|---|---|---|---|
| STR-BEA-001 | AMBIGUOUS_APPLICABILITY | BEAM (9) | BLOCKED | MEDIUM | OPEN | P13 ground-beam typical details (<2.5 / <5 / >5 m): 9 beam(s) change class depending on the length basis (centre-to-centre / clear span). |
| STR-BEA-002 | AMBIGUOUS_APPLICABILITY | BEAM (1) | NO_QUANTITY_IMPACT | LOW | PROVISIONAL_INTERPRETATION | Schedule row B.W (beam) is defined but no plan occurrence carries this mark. |
| STR-BEA-003 | AMBIGUOUS_APPLICABILITY | BEAM (1) | NO_QUANTITY_IMPACT | LOW | PROVISIONAL_INTERPRETATION | Schedule row B10 (beam) is defined but no plan occurrence carries this mark. |
| STR-BEA-004 | AMBIGUOUS_APPLICABILITY | BEAM (1) | NO_QUANTITY_IMPACT | LOW | PROVISIONAL_INTERPRETATION | Schedule row B12 (beam) is defined but no plan occurrence carries this mark. |
| STR-BEA-005 | ENGINEERING_METHOD_REQUIRED | BEAM (16) | BLOCKED | MEDIUM | OPEN | 16 beam occurrence(s) depend on P8-N21 (Side bars 2Ø12 / 3Ø12 / 4Ø12 in beams deeper than 60 cm, according to the beam width, unless stated otherwise. |
| STR-BEA-006 | MISSING_DIMENSION | BEAM (2) | BLOCKED | LOW | OPEN | 2 beams: curved ground-beam span - support length not measured. |
| STR-BEA-007 | MISSING_DIMENSION | BEAM (113) | LOWER_BOUND | MEDIUM | OPEN | 113 beam occurrence(s) depend on P8-N11 (Beams crossed by service pipes are widened by 5 cm.), whose extent is not established (BLOCKED_METHOD). |
| STR-BEA-008 | MISSING_SCHEDULE | BEAM (6) | AUDIT_ONLY | MEDIUM | OPEN | 6 beam member(s) at 1F_ROOF are drawn without a type mark (dome ring (curved)). |
| STR-BEA-009 | MISSING_SCHEDULE | BEAM (13) | AUDIT_ONLY | MEDIUM | OPEN | 13 beam member(s) at 1F_ROOF are drawn without a type mark (no mark). |
| STR-BEA-010 | MISSING_SCHEDULE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | 1 beam member(s) at 2F_ROOF are drawn without a type mark (no mark). |
| STR-BEA-011 | MISSING_SCHEDULE | BEAM (5) | AUDIT_ONLY | MEDIUM | OPEN | 5 beam member(s) at GF_ROOF are drawn without a type mark (no mark). |
| STR-BEA-012 | SOURCE_CONFLICT | BEAM (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 beam occurrence(s) of type B21: schedule width (cm) differs from drawn width (cm) (45.0 vs 40.0). |
| STR-BEA-013 | SOURCE_CONFLICT | BEAM (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 beam occurrence(s) of type B29: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0). |
| STR-BEA-014 | SOURCE_CONFLICT | BEAM (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 beam occurrence(s) of type B6: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0). |
| STR-BEA-015 | SOURCE_CONFLICT | BEAM (2) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 2 beam occurrence(s) of type CB10: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0). |
| STR-BEA-016 | SOURCE_CONFLICT | BEAM (2) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 2 beam occurrence(s) of type CB2: schedule width (cm) differs from drawn width (cm) (20.0 vs 25.0). |
| STR-BEA-017 | SOURCE_CONFLICT | BEAM (1) | BLOCKED | HIGH | OPEN | One drawn beam carries 2 different type marks (CB3, B3); both marks sit on the same drawn span. |
| STR-BEA-018 | SOURCE_CONFLICT | BEAM (1) | BLOCKED | MEDIUM | OPEN | beam CB4: schedule spans [3.3, 3.7] but plan spans [2.724, 3.75] (SPAN_LENGTH_CONFLICT). |
| STR-BEA-019 | SOURCE_CONFLICT | BEAM (1) | BLOCKED | MEDIUM | OPEN | beam CB5: schedule spans [2.5, 4.5] but plan spans [2.85] (SPAN_COUNT_CONFLICT). |
| STR-BEA-020 | SOURCE_CONFLICT | BEAM (1) | BLOCKED | MEDIUM | OPEN | beam CB5: schedule spans [2.5, 4.5] but plan spans [4.2] (SPAN_COUNT_CONFLICT). |
| STR-BEA-021 | SOURCE_CONFLICT | BEAM (1) | BLOCKED | MEDIUM | OPEN | beam CB8: schedule spans [3.7, 6.4, 6.8] but plan spans [6.545, 6.95] (SPAN_COUNT_CONFLICT). |
| STR-BEA-022 | SOURCE_CONFLICT | BEAM (1) | BLOCKED | HIGH | OPEN | Schedule key SB2 is defined 2 times with different values. |
| STR-BEA-023 | UNBOUND_OCCURRENCE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | Mark B6 sits between 3 members at similar distance; the member it names is not certain. |
| STR-BEA-024 | UNBOUND_OCCURRENCE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | Mark B6 sits between 3 members at similar distance; the member it names is not certain. |
| STR-BEA-025 | UNBOUND_OCCURRENCE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | Mark B6 sits between 3 members at similar distance; the member it names is not certain. |
| STR-BEA-026 | UNBOUND_OCCURRENCE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | Mark B6 sits between 3 members at similar distance; the member it names is not certain. |
| STR-BEA-027 | UNBOUND_OCCURRENCE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | Mark B1 sits between 2 members at similar distance; the member it names is not certain. |
| STR-BEA-028 | UNBOUND_OCCURRENCE | BEAM (1) | AUDIT_ONLY | MEDIUM | OPEN | Mark B8 sits between 2 members at similar distance; the member it names is not certain. |
| STR-COL-001 | AMBIGUOUS_APPLICABILITY | COLUMN (6) | PROVISIONAL | LOW | PROVISIONAL_INTERPRETATION | Type CN occurs only at FOUNDATION (6 occurrence(s)) while other columns continue upward. |
| STR-COL-002 | AMBIGUOUS_APPLICABILITY | COLUMN (29) | BLOCKED | HIGH | OPEN | ST. OF COLUMN- 6Ø8/m (column ties) gives a count per metre, but 2 band(s) use more than one closed tie per level; whether the count is of tie SETS or  |
| STR-COL-003 | AMBIGUOUS_APPLICABILITY | COLUMN (11) | BLOCKED | LOW | OPEN | Type C10 (FOUNDATION), C10 (GF), C5 (FOUNDATION), C5 (GF), C6 (FOUNDATION), C6 (GF), C9 (2F) has 10 main bars but the detail sketch for its band shows |
| STR-COL-004 | AMBIGUOUS_APPLICABILITY | COLUMN (8) | BLOCKED | LOW | OPEN | Type C11 (FOUNDATION), C11 (GF), C9 (FOUNDATION), C9 (GF) has 14 main bars but the detail sketch for its band shows 12; which bars each tie encloses i |
| STR-COL-005 | AMBIGUOUS_APPLICABILITY | COLUMN (10) | BLOCKED | LOW | OPEN | Type C1 (1F), C1 (2F), C2 (2F), C3 (1F), C3 (2F), C5 (2F) has 6 main bars but the detail sketch for its band shows 4; which bars each tie encloses is  |
| STR-COL-006 | AMBIGUOUS_APPLICABILITY | COLUMN (45) | BLOCKED | LOW | OPEN | Type C (FOUNDATION), C (GF), C1 (FOUNDATION), C1 (GF), C2 (1F), C2 (FOUNDATION), C2 (GF), C3 (FOUNDATION), C3 (GF), C4 (1F), C4 (FOUNDATION), C4 (GF), |
| STR-COL-007 | ENGINEERING_METHOD_REQUIRED | COLUMN (95) | BLOCKED | HIGH | OPEN | ST. OF COLUMN- 6Ø8/m (column ties) gives ties per metre but not over which height: full storey height, clear height below the beams, or including the  |
| STR-COL-008 | RULE_GAP | COLUMN (3) | BLOCKED | HIGH | OPEN | column tie rule (arrangement by long side L): value 80.0 cm (C7) is on a limit no band includes. |
| STR-COL-009 | SOURCE_CONFLICT | COLUMN (2) | BLOCKED | HIGH | OPEN | column at grid X04/Y01: equal-authority sources give different types (C3 vs C). |
| STR-COL-010 | SOURCE_CONFLICT | COLUMN (3) | BLOCKED | HIGH | OPEN | column at grid X12/Y02: equal-authority sources give different types (C8 vs C7). |
| STR-COL-011 | SOURCE_CONFLICT | COLUMN (1) | PROVISIONAL | LOW | PROVISIONAL_INTERPRETATION | column CN is drawn on FOUNDATION PLAN, GROUND BEAMS PLAN but not on COLUMN & AXIS PLAN. |
| STR-COL-012 | SOURCE_CONFLICT | COLUMN (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 column occurrence(s) of type C1: schedule section (storey band) differs from drawn outline ([30.0, 50.0] vs [20.0, 50.0]). |
| STR-COL-013 | SOURCE_CONFLICT | COLUMN (2) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 2 column occurrence(s) of type C2: schedule section (storey band) differs from drawn outline ([30.0, 50.0] vs [20.0, 50.0]). |
| STR-COL-014 | SOURCE_CONFLICT | COLUMN (4) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 4 column occurrence(s) of type C3: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [25.0, 50.0] vs [20.0, 40. |
| STR-COL-015 | SOURCE_CONFLICT | COLUMN (3) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 3 column occurrence(s) of type C4: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [30.0, 50.0] vs [25.0, 50. |
| STR-COL-016 | SOURCE_CONFLICT | COLUMN (4) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 4 column occurrence(s) of type C5: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [20.0, 60.0]; [20.0, 50.0] vs [25.0, 60. |
| STR-COL-017 | SOURCE_CONFLICT | COLUMN (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 column occurrence(s) of type C6: schedule section (storey band) differs from drawn outline ([20.0, 60.0] vs [25.0, 70.0]). |
| STR-COL-018 | SOURCE_CONFLICT | COLUMN (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 column occurrence(s) of type C7: schedule section (storey band) differs from drawn outline ([20.0, 80.0] vs [25.0, 80.0]). |
| STR-COL-019 | SOURCE_CONFLICT | COLUMN (3) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 3 column occurrence(s) of type C8: schedule section (storey band) differs from drawn outline ([20.0, 90.0] vs [25.0, 80.0]; [25.0, 90.0] vs [25.0, 80. |
| STR-COL-020 | SOURCE_CONFLICT | COLUMN (3) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 3 column occurrence(s) of type C9: schedule section (storey band) differs from drawn outline ([20.0, 90.0] vs [20.0, 100.0]; [20.0, 90.0] vs [25.0, 10 |
| STR-COL-021 | SOURCE_CONFLICT | COLUMN (5) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 5 column occurrence(s) of type C: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [20.0, 40.0]). |
| STR-COL-022 | SOURCE_CONFLICT | COLUMN (1) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 1 column occurrence(s) of type P.C: schedule section (storey band) differs from drawn outline ([20, 50] vs [20.0, 40.0]). |
| STR-COL-023 | SOURCE_CONFLICT | COLUMN (10) | PROVISIONAL | MEDIUM | PROVISIONAL_INTERPRETATION | 10 column occurrence(s) (C, C1, C2) at GF: schedule gives 20.0 cm but minimum column thickness for the storey height (p.9) requires at least 25. |
| STR-DOM-001 | AMBIGUOUS_APPLICABILITY | DOME (8) | PROVISIONAL | MEDIUM | OPEN | 8 dome occurrence(s) depend on P7-DOME (Dome reinforcement.), whose applicability is not established (CANDIDATE). |
| STR-FOO-001 | AMBIGUOUS_APPLICABILITY | FOOTING (17) | BLOCKED | MEDIUM | OPEN | The schedule field 'BOXED' is printed for 11 type(s) (e.g. F=3+4, F10=3+5, F11=3+8, F15=3+4) but its meaning is not stated. |
| STR-FOO-002 | AMBIGUOUS_APPLICABILITY | FOOTING (1) | NO_QUANTITY_IMPACT | LOW | PROVISIONAL_INTERPRETATION | Schedule row F7 (footing) is defined but no plan occurrence carries this mark. |
| STR-FOO-003 | MISSING_DIMENSION | FOOTING (26) | BLOCKED | MEDIUM | OPEN | 26 footing occurrence(s) depend on P13-FOOTING-DEEP (Where the upper ground beam is more than 2.5 m above the footing, an additional LOWER ground beam |
| STR-FOO-004 | SOURCE_CONFLICT | FOOTING (2) | PROVISIONAL | LOW | PROVISIONAL_INTERPRETATION | Two footing outlines overlap by 0.14 m2 plan. |
| STR-FOO-005 | SOURCE_CONFLICT | FOOTING (1) | BLOCKED | HIGH | OPEN | One drawn footing carries 2 different type marks (F, F10); one outline holding columns C, C10. |
| STR-GRO-001 | MISSING_DIMENSION | GROUND_SLAB (21) | LOWER_BOUND | MEDIUM | OPEN | 21 ground slab occurrence(s) depend on P3-GROUND-SLAB (Ground slab note: 10 cm, 5Ø10/m each way.), whose extent is not established (CANDIDATE). |
| STR-LIF-001 | MISSING_DIMENSION | LIFT_PIT (1) | BLOCKED | MEDIUM | OPEN | 1 lift pit occurrence(s) depend on P14-LIFT (Lift pit on the FF raft: 20 cm walls with 6Ø12/m and 6Ø16/m, pit depth by the lift manufacturer.), whose  |
| STR-LIF-002 | MISSING_DETAIL | LIFT_TIE_BEAM (1) | BLOCKED | MEDIUM | OPEN | Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m. requires lift tie beam (storey height > 4.30 m) but none  |
| STR-LIN-001 | MISSING_DETAIL | LINTEL (1) | BLOCKED | MEDIUM | OPEN | Lintels by opening width; width = wall width; 40 cm minimum bearing each side. requires lintel (one lintel per architectural opening, type by opening  |
| STR-PAR-001 | MISSING_DIMENSION | PARAPET (3) | BLOCKED | LOW | OPEN | 3 parapets: parapet height / length follow the architectural drawings (not on the structural set). |
| STR-PLA-001 | AMBIGUOUS_APPLICABILITY | PLANTED_COLUMN (3) | LOWER_BOUND | MEDIUM | OPEN | 3 planted column occurrence(s) depend on P15-PLANTED (Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.), whose appl |
| STR-POO-001 | MISSING_DIMENSION | POOL (1) | BLOCKED | LOW | OPEN | pool SPC-POOL: pool lengths and depths are 'AS PER ARCH' on the detail. |
| STR-PRO-001 | SOURCE_CONFLICT | PROJECT_RULE (1) | BLOCKED | LOW | OPEN | boundary wall definition: P14-BOUNDARY says TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T& |
| STR-PRO-002 | SOURCE_CONFLICT | PROJECT_RULE (1) | NO_QUANTITY_IMPACT | LOW | OPEN | formwork rule: P8-N17 says formwork >= 14 days, P1-NOTE-C says formwork >= 21 days. |
| STR-SLA-001 | AMBIGUOUS_APPLICABILITY | SLAB (49) | BLOCKED | MEDIUM | OPEN | 49 slab occurrence(s) depend on P4-6-NOTE-2 (Top steel 5Ø10/m over beams for the slabs, length one third of the span, in both directions.), whose appl |
| STR-SLA-002 | RULE_GAP | SLAB (47) | BLOCKED | MEDIUM | OPEN | temperature reinforcement table (p.15) has no row for 160 mm (47 element(s)); rows are [100, 125, 150, 175, 200, 250, 300]. |
| STR-SLA-003 | RULE_GAP | SLAB (2) | BLOCKED | MEDIUM | OPEN | temperature reinforcement table (p.15) has no row for 180 mm (2 element(s)); rows are [100, 125, 150, 175, 200, 250, 300]. |
| STR-STA-001 | AMBIGUOUS_APPLICABILITY | STAIR (5) | BLOCKED | MEDIUM | OPEN | 5 stair occurrence(s) depend on P16-STAIR (Typical stair and stair-beam reinforcement (N.T.S.).), whose applicability is not established (BLOCKED_METH |
| STR-TUR-001 | AMBIGUOUS_APPLICABILITY | TURN_COLUMN (2) | LOWER_BOUND | MEDIUM | OPEN | 2 turn column occurrence(s) depend on P15-TWISTED (Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.), whose app |

Pricing is not integrated. No reinforcement weight is calculated in S2.
