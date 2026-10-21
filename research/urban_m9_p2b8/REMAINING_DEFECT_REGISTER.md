# Remaining defect register (Phase 2B-8)

This register carries `research/urban_m9_p2b7/ENGINEERING_DEFECT_REGISTER.md` forward.

- **"Fixed in V2.7.1"** means corrected in ARCH_TAKEOFF_V2.7.1, with an acceptance test against hand truth or the independent reader.
- V1 – V2.7 keep every defect as found. They are frozen, and their as-found tests (`test_v2_7_as_found`, `test_v2_7_turned_column_as_found`, `test_v2_7_is_unchanged`) still assert them.

## Closed in Phase 2B-8

| id | defect (as found) | status | evidence |
|---|---|---|---|
| L-P7-01 | the WC-shape rule missed a round bowl | **fixed in V2.7.1** (UP-WET-002 1.3.0): a pan-size circle centred on a wall cistern | ROUND_BOWL and its rot30 / mirror / metres variants → WET |
| L-P7-02 | an armchair drawn with a WC outline passed the WC-shape rule | **fixed in V2.7.1** for a seat wider than a pan and for a free-standing chair: BOWL_WIDER_THAN_A_WC_PAN / CISTERN_NOT_ON_A_WALL. A WC-sized chair against a wall is L-P8-01 | SEAT_LOOKALIKE, ARMCHAIR_AT_WALL → REVIEW |
| L-P7-03 | a basin block's own linework compared ids of two forms (ineffective exclusion) | **fixed in V2.7.1**: matched by the decimal handle of every insert path | BASIN_OWN_WC_LIKE → REVIEW; on the reference plan 43 / 86 / 86 entities excluded as the basin |
| L-P7-04 | a space under wet review carried no finish line at all | **fixed in V2.7.1** (UP-REVIEW-001): the invariant ceiling is released; the wall face is reported as geometry; everything else is conditional and never summed. Plaster stays held (a different system behind porcelain) | 18 tests; reference plan +9.348195 m² ceiling, 3 lines |
| L-P7-05 | 10 reference-plan lines carried no source entity | **fixed in V2.7.1**: all 10 are threshold strips, now traced through the strip (STRIP basis); a line still untraced must state why | reference plan 0 untraced |
| D-P6-04 (limitation) | a turned column was no opening jamb and no wall cut | **fixed in V2.7.1** (UP-COL-ORIENT-001) | COLUMN_JAMB rot30 / rot90 / mirror / rot37 metres: 0.877 m, invariant; wall run 12.30 m turned or not |
| D-P8-01 | **V2.7.1 draft**: REVIEW_INVARIANT_RELEASE and TURNED_COLUMN records were appended after the ids were given (no id), and the summary was overwritten in another shape | fixed before release: the records continue the numbering | found by the attribution tool |

## Found in Phase 2B-8, still open

| id | defect | class | found by | proposed fix | effect on the reference plan |
|---|---|---|---|---|---|
| **L-P8-01** | a seat of a WC pan's size touching a back on the wall face is read as a WC outline | ALLOCATION (bounded: the space is typed with a review flag, never released silently) | adversarial fixture WC_SIZED_CHAIR (strict xfail) | needs a second source: a block name, a schedule, a sanitary layer, or the drain / soil-pipe symbol | none (no WC shape on the plan) |
| **D-P8-03** | a wall stretch with both faces drawn over less than 0.30 m (a pier, a stub beside an opening) is not in the wall run, straight or curved | GEOMETRY / CONVENTION | the independent arc census (0.209947 m of curved stubs either side of a curved window) | measure stubs between openings as wall (QS practice); version it in the next method; the census already lists them apart | wall run short by about 0.21 m on one floor (of about 97.6 m); straight stubs not yet counted |
| **D-P8-04** | a space closed on one side by a line of a non-wall layer (1.256 m) cannot be verified independently: the wall lines alone do not enclose it | VERIFICATION GAP | the attribution tool | identify what that line is (counter, glazed screen, zone line); if it is a boundary, give the reader its role from a declared rule, never from the engine | 13 of 55 V2.6 → V2.7.1 differences EXPLAINED_UNVERIFIED; one of the three released ceilings unverified |
| **D-P8-05** | a face with a gap that carries no door or window symbol (a passage) has no independent wall-finish check | VERIFICATION GAP | the attribution tool | add an independent passage rule (gap closure with no symbol = passage, deducted by its width) and test it on hand truth | 4 differences unverified |
| **D-P8-06** | skirting and wall tile on a face with a window cannot be checked or decided from a plan: floor glazing vs sill window, sill height | INPUT | the attribution tool (one skirting deducted a window) | read sill heights from sections or a window schedule (as D-04 heights) | 2 differences unverified |
| **O-P8-01** | in the DRY_SCOPE scenario, a lobby's external door becomes a main-entrance candidate (the door class depends on the space type, UP-DOOR-CLS-004) | OBSERVATION (by design) | review-space tests | none: it is reported as a conditional effect of the scenario, never in the main BOQ | none |
| **O-P8-02** | every ceiling line is PROVISIONAL (the ceiling type is not in a plan); a released invariant ceiling is still a provisional quantity | INPUT | benchmark scorer design | a ceiling-type rule or schedule per room | the benchmark scores ceilings as PROVISIONAL answers |

## Still open from earlier phases

| id | defect | status |
|---|---|---|
| D-C2 / D-C2b | leaf-closed doorways: threshold withheld; two leaf-closed pieces take their whole face | open |
| D-C3 | a doorless cell merged into a wet room takes the wet scope silently | open |
| D-C5 | wall-area lines rest on synthetic heights unless sections are read | open (D-04) |
| D-P6-03 | a drain of column size still needs a second source | open (bounded: audit A04) |
| D-D1 | one or two columns on a layer: refused unless wall-bound | by design (never guessed) |
| L-01 | a sheet frame turned with its plan is refused at admission | by design (safe) |
| G-* | catalogue gaps: formwork, excavation, glazing areas, roof / balcony / paving, block-wall areas (BLOCKED_RFI), stair risers / flights / rails (BLOCKED_RFI), combined export | next phase plan |

## Tooling defects found and fixed during this phase (not engine defects)

These were found when the new independent reader met the real plan. They are recorded so that no verification result is trusted beyond what was tested.

| id | defect | fix |
|---|---|---|
| T-P8-01 | the reader read an entity's layer before checking its type; an RTEXT entity has no layer attribute | types filtered first |
| T-P8-02 | arcs were flattened through ezdxf's Bezier path (0.0003 m² high on the B10 bathroom) | the entity's own `flattening()` on the true curve (2×10⁻⁵ m²) |
| T-P8-03 | T-junctions lost after a 30° rotation (faces leaked) | one snap-rounding union on a 1 µm grid; invariance tests rot30 / mirror / metres |
| T-P8-04 | an unclosed face (986 m²) compared with a 4.73 m² room read as a contradiction | an unclosed face is EXPLAINED_UNVERIFIED (NOT_CLOSED_BY_WALL_LINES); a merely larger face stays CONTRADICTED |
