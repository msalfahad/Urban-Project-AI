# PRE-S6: superstructure beam rebar readiness (simple + continuous beams)

**No kg is calculated in this round.** S5 is frozen and was not reopened; the S4 / S5 manifests are untouched.

```
python3 -I research/pre_s6_superstructure_beam_readiness/build_pre_s6.py
```

The builder reads ST7757.dxf (sha256-checked) through the S1 lab census, the R3 continuous-beam frame parser and the
schedule reader V2, plus the frozen S1 registers (checked against the S1 INDEX) and the R4 rule / visual-claim
registers. No other package, reference quantity or old total is opened. Every decision is made by
`engine/source/beam_rebar_readiness.py`.

## Results

| | Count | State |
|---|---|---|
| Beam tags (GF / 1F / 2F roof) | 119 | 105 BOUND_VERIFIED, 5 BOUND_CANDIDATE, 9 BOUND_SOURCE_CONFLICT, 0 DUPLICATE_TAG, 0 unbound |
| Member spans | 143 | 98 verified, 5 candidate, 8 conflict, 32 without tag |
| Arc bands | 13 | 7 verified, 6 without tag |
| Short band fragments | 9 | NOT_BEAM |
| Rule populations (lintels, lift ties) | 2 | OUT_OF_SCOPE_FAMILY |
| Simple-beam occurrences | 89 | 71 LOWER_BOUND, 18 BLOCKED, 0 READY |
| Continuous-beam occurrences | 13 | 7 LOWER_BOUND, 6 BLOCKED, 0 READY |
| Untagged geometry | 38 | NO_APPLICABLE_DETAIL (18 of them were silently dropped by S1 and now terminate) |

Every tag, span, arc band, fragment and rule population terminates exactly once
(286 objects, 146 S1 superstructure rows mapped, 0 unmapped).

### Simple beams (component families)

| Component | READY | READY_LOWER_BOUND | PROVISIONAL_ONLY | SOURCE_CONFLICT | BLOCKED_COMPONENT | NO_APPLICABLE_DETAIL | NOT_APPLICABLE |
|---|---|---|---|---|---|---|---|
| BOTTOM_MAIN |  | 71 | 4 | 3 | 11 |  |  |
| TOP_MAIN |  | 71 | 4 | 3 | 11 |  |  |
| TOP_SUPPORT_EXTRA |  |  |  |  |  |  | 89 |
| BOTTOM_EXTRA |  |  |  |  |  |  | 89 |
| HANGER |  |  |  |  |  |  | 89 |
| SIDE_REBAR |  |  |  |  | 32 |  | 57 |
| STIRRUP_COUNT |  | 71 | 4 | 3 | 11 |  |  |
| STIRRUP_MASS |  |  |  |  | 89 |  |  |
| DEVELOPMENT_ANCHORAGE |  |  |  |  | 89 |  |  |
| HOOKS |  |  |  |  | 89 |  |  |
| OPENING_EXTRA |  |  |  |  |  |  | 89 |
| PLANTED_COLUMN_EXTRA |  |  |  |  | 1 |  |  |
| STAIR_EXTRA |  |  |  |  | 2 |  |  |

### Continuous beams (component families; one row per bar run / span)

| Component | READY | READY_LOWER_BOUND | PROVISIONAL_ONLY | SOURCE_CONFLICT | BLOCKED_COMPONENT | NO_APPLICABLE_DETAIL | NOT_APPLICABLE |
|---|---|---|---|---|---|---|---|
| BOTTOM |  | 14 |  | 11 | 2 |  |  |
| MID_SUPPORT_TOP | 9 |  |  | 6 |  |  |  |
| TOP |  |  |  | 10 | 16 |  |  |
| LONGITUDINAL |  |  |  |  | 1 |  |  |
| HANGER |  |  |  |  | 13 |  |  |
| SIDE_REBAR |  |  |  |  | 7 |  | 6 |
| STIRRUP_COUNT |  | 12 |  | 11 | 6 |  |  |
| STIRRUP_MASS |  |  |  |  | 29 |  |  |
| DEVELOPMENT_ANCHORAGE |  |  |  |  | 13 |  |  |
| HOOKS |  |  |  |  | 13 |  |  |
| OPENING_EXTRA |  |  |  |  |  |  | 13 |

## What was established

1. **Binding.** One evidence ladder for every tag against every band / arc band in reach: extent, distance window,
   span already claimed by another mark, orientation, schedule width, same-mark continuity. Distance never ranks;
   text rotation alone never verifies (an alternative excluded only by rotation leaves the tag a CANDIDATE, unless the
   tag lies off that member's end or that member already carries the same mark). Claims are iterated to a fixed point
   (GFRS 2 passes, FFRS 1, SFRS 1).
   Changes against S1: 45D AMBIGUOUS  -> BOUND_CANDIDATE BL016; 472 AMBIGUOUS  -> BOUND_VERIFIED BL031; 474 BOUND BL017 -> BOUND_CANDIDATE BL008; 4D2 BOUND BA004 -> BOUND_VERIFIED BL046; 6BD AMBIGUOUS  -> BOUND_VERIFIED BL013; 6D4 AMBIGUOUS  -> BOUND_VERIFIED BL031; 6D7 AMBIGUOUS  -> BOUND_VERIFIED BL030; 76C AMBIGUOUS  -> BOUND_VERIFIED BL012.
2. **Width.** 5 marks have a drawn width that conflicts with the schedule (FFRS B6, FFRS CB10, GFRS B21, GFRS B29, GFRS CB2). The geometry stays
   known; the type-specific rebar is SOURCE_CONFLICT.
3. **T/M-n** are design line loads: the unit ' t/m' is printed beside every value on the frame's load line
   (SOURCE_EXPLICIT, NOT_REBAR). They never feed S6.
4. **CB spans.** Sequence states: {'MATCH': 10, 'SPAN_LENGTH_SOURCE_CONFLICT': 2, 'SPAN_COUNT_CONFLICT': 1}; reading direction: {'FORWARD': 6, 'AMBIGUOUS': 3, 'REVERSED': 1, 'NONE': 3}. CBO-FFRS-CB9-BL023 match only
   when read right to left (plan spans re-ordered into schedule order). CBO-FFRS-CB13-BL004, CBO-GFRS-CB2-BL038, CBO-GFRS-CB7-BL003 match in both directions (the span-to-schedule mapping is not
   decided; only candidate-invariant families release). Length conflicts keep both values: CBO-GFRS-CB4-BL016, CBO-GFRS-CB5-BL008;
   count conflicts: CBO-GFRS-CB8-BL024.
5. **CB typical headers.** Each parametric dimension was bound by its defpoints (16 bound, 7 unresolved).
   In this drawing `L*` are face-to-face spans and `Ln*` are axis-to-axis spans (both from the dimensions themselves).
   MID support bars: 0.22 x Ln of each adjacent span from the support face (bound in all three typicals). End-span bottom
   bars: 7.5 cm beyond the far face of the interior support. The left end top bar of every typical is not
   dimensioned. Unresolved dimensions:
   - TYP-272B (2-span) 2785 '0.3 Ln2': 'Ln2' names no span of this 2-span typical
   - TYP-272B (2-span) 2798 '0.15L': a defpoint hits no bar end of the typical (the dimension is not bound)
   - TYP-206B (2-span) 20C6 '0.3 Ln2': 'Ln2' names no span of this 2-span typical
   - TYP-206B (2-span) 20D9 '0.15L': a defpoint hits no bar end of the typical (the dimension is not bound)
   - TYP-2035 (3-span) 2267 '7.5cm': a defpoint hits no bar end of the typical (the dimension is not bound)
   - TYP-2035 (3-span) 2282 '0.15L': 'L' is span 1 in the typical, but the bar end lies in span 3
   - TYP-2035 (3-span) 228F '7.5cm': a defpoint hits no bar end of the typical (the dimension is not bound)
6. **MID bars** with a printed count, a template-shaped frame bar and both sides bound are VERIFIED complete bars
   (9 READY). An edited frame bar (CB3 support 1) or an empty schedule cell (CB3 MID2, CB8 MID1) stays
   blocked; a known count with no bound extent is BLOCKED_UNQUANTIFIED, never given a length.
7. **Bottom bars of CB** are one bar run per frame bar, crossing their supports once (14
   READY_LOWER_BOUND): clear span + support width + bound extension; end anchorage stays blocked.
8. **CB top bars** stay blocked (26 runs): the frames draw one top bar per span from the end support, the
   typical draws an end bar plus a second lapping row; no extent rule binds to the frame bar.
9. **Hangers.** SBT: no hanger field or detail (TOP BARS exist; their hanger role is not asserted). CB: the typical
   draws an unlabelled second top row - no count / diameter / extent, so HANGER is blocked, never invented.
10. **Simple beams.** SBT 'BOTTOM BARS' / 'TOP BARS' run support face to support face as the straight run (VERIFIED),
    development and hooks separate and blocked, so the complete bar is a LOWER_BOUND (71 occurrences). The
    straight portion is not demoted. Curved ring beams (7), the cantilever, stair-qualified spans
    (2) and a span carrying a planted column (1) stay blocked.
11. **Stirrups.** Diameter and rate per metre are SOURCE_EXPLICIT; the count is a LOWER_BOUND ceil(rate x clear run)
    with no +1 (71 simple + 12 CB spans). Legs, hooks, path, end zones and the first / last rule are not
    printed, so all 118 stirrup-mass rows are blocked.
12. **Side bars.** SBT REMARKS and the CB 'MIDDLE REINT.' column print '2Ø12/30cm'-type tokens on every beam deeper
    than 60 cm; faces, vertical arrangement, length and ends are not stated, so side rebar is BLOCKED_COMPONENT
    (32 simple, 7 CB occurrences). '/30 cm' is not interpreted.
13. **Openings.** 26 S-OPENING / void objects: 3 closed outlines, 23 open line work
    (dome radials, shaft diagonals, three-sided slots closing on beam faces). 0 reach inside a beam band,
    so every OPENING_EXTRA_* is NOT_APPLICABLE.
14. **Provenance.** 165 S6 provenance templates (generic ELEMENT_* identity, BAR_RUN_ID on every CB run) in
    `S6_PROVENANCE_TEMPLATES.json`; each passes `provenance_ready`.

## Deliverables

`01_BEAM_OCCURRENCE_CONSERVATION.csv`, `02_BEAM_BINDING_READINESS.csv` (every alternative of every tag),
`03_SIMPLE_BEAM_SCHEDULE_SEMANTICS.csv`, `04_CONTINUOUS_BEAM_SCHEDULE_SEMANTICS.csv`, `05_CB_SPAN_SEQUENCE.csv`,
`06_BEAM_BAR_RUN_READINESS.csv`, `07_BEAM_SIDE_REBAR_READINESS.csv`, `08_BEAM_OPENING_OCCURRENCES.csv`,
`09_BEAM_TOKEN_CORPUS.csv`, `10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv`, `11_ENGINEERING_QUESTIONS.md`,
`12_S6_SCOPE_RECOMMENDATION.md`, `PRE_S6_SUMMARY.json`, `S6_PROVENANCE_TEMPLATES.json`, `INDEX.json`, `TEST_RUN.md`.
