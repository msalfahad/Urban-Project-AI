# Prioritized roadmap (Phase 2B-6, Part 13)

**Ranking rule.** Expected real-world BOQ improvement x frequency x importance, against risk and cost (scores in
`BOQ_CAPABILITY_MATRIX.md`). Waterproofing optimisation and single-doorway work are deliberately not at the top: both
are understood, and their remaining exposure is small.

| rank | work | why (measured) | families | proof required | status |
|---|---|---|---|---|---|
| **0 (now, done)** | **run the audit on every architectural run** (`tools/arch_run_audit.py`) | turns tonight's silent failures into findings with evidence: exploded single doors, single-instance layers, turned / exploded columns, nested plans, curved bands, held doors, basin-only wet spaces. On the reference plan it raises only the expected findings | all | `tests/m9_p2b6/test_p2b6_run_audit.py` (9) | **delivered** |
| 1 | **layer-role understanding by geometry** (the next method): single-instance door / window signatures, oriented and exploded column rectangles, door-before-window ordering | benchmark 15 / 15 single-instance cases exact; −3.2 % floor (exploded door) and −10.4 % plaster (turned columns) removed; reference plan, villa and mirror unchanged | rooms → every finish, doors, windows, thresholds | the benchmark; tonight's fixtures; byte identity of V1 - V2.6; reference-plan roles unchanged | proven in the clone (Exp. C) |
| 2 | **heights from sections / schedules**, owner fallbacks labelled ASSUMED (Part 4) | every wall-area line (plaster, wall porcelain, paint, masonry), risers and flights rest on heights; tests use synthetic ones | plaster, tile, paint, masonry, stairs, door / window areas | a section reader verified on synthetic sections; the reference villa's sections (D-04) | design |
| 3 | **formwork** from the existing member geometry | an entire BOQ family is absent | formwork | hand-derived contact areas on synthetic members; an independent solid-boolean check (test tree) | design |
| 4 | **the held door's width and leaf-closed thresholds** (the next method) | 7 of the 8 failing real checks; 5 leaf-closed doorways withheld | thresholds, doorway waterproofing, reveals, wall finishes | real rooms to 0 failing; 7 synthetic variants | width proven (Exp. A); leaf-closed: design |
| 4 | **room types: the basin rule + doorless cells** (the next method + knowledge 1.2.0) | the last failing real check; 9.35 m2 of wet scope on the plan typed from basins; a doorless cell's wet scope silent | wet scope, doorway waterproofing attribution | real rooms; synthetic basin plan; the WC-shape refinement | proven (Exp. G); refinement design |
| 6 | **excavation and backfill** | no measured item; blinding only | earthworks | synthetic footings with levels | design |
| 6 | **windows**: area, glazing, reveals | windows counted only; 26 reveals blocked on the reference plan | aluminium windows, glazing, reveals | heights (rank 2), sill / head from elevations | after rank 2 |
| 6 | **roof, balcony and external works**: roof finishes, parapets, interlock paving | no items; exterior faces already exist | roofing, external works | roof / site-plan regions on synthetic plans | design |
| 9 | waterproofing procurement release | PROVISIONAL until the owner's junction detail (D-01) | procurement rolls | the 2B-4 / 2B-5 examples re-run with the detail | blocked on D-01 |
| 10 | curved walls (polygon + wall run) (the next method, cheap) | 4 of 38 rooms (dry), +0.88 % wall run on the plan | layouts, wall run | B10; the raw arc census | proven (Exp. B) |
| - | per-line source entities (provenance) | faces and walls cannot be traced to DXF handles today | QA | Experiment E | design (cheap) |
| - | a second real plan, verified like Stage C (D-15) | every correction is proven on one real plan | all | Stage C protocol | owner input |
| - | the formal blind evaluation (D-13) | the only basis for an accuracy claim | all | the owner's protocol | not started (instruction) |

## Phases

1. **Next: the opt-in architectural method** (`NEXT_IMPLEMENTATION_PLAN.md`). It bundles ranks 1, 4, 4 and 10, plus
   provenance. All of it is proven in the clone, small, and isolated.
2. **Heights.** A section / schedule reader with ASSUMED fallbacks. It unblocks paint, risers, flights and window
   areas.
3. **Structural completeness.** Formwork, then excavation / backfill, then the missing rebar families. Each is verified
   against hand truth and an independent volume / area check.
4. **Envelope and site.** Roof and balcony finishes, parapets, interlock paving, external walls.
5. **Validation.** A second real plan verified like Stage C, then the blind evaluation when the owner authorises it.
