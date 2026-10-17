# Next-phase plan (after N10)

Ranked by the BOQ quantity they would make trustworthy, not by effort.

| # | Work | Unlocks | Size | Depends on |
|---|---|---|---|---|
| 1 | **Section binding on the real plan.** Bind the section bands to plan floors where the floor names are drawn outside the band (nearest band label, a level cross-check), with tests first | masonry panel, facade area, and room heights from the drawing instead of facts | M | — |
| 2 | **Owner answers OQ-06 – OQ-13** | masonry (beams, material), facade convention, formwork conventions, excavation | — | owner |
| 3 | **D-N10-01**: close a glazing-lined gap on the outline at the face line, and detect a window set beside a column | facade run exact on the reference plan (+0.16 m today) | S | — |
| 4 | **D-N10-02**: reader closures for wide glazed openings (glazing lines spanning a wall gap over 2.60 m) | independent facade check on the GF | S | — |
| 5 | **Formwork / excavation into the BOQ workbook** as lines (states kept: MEASURED / CONDITIONAL / UPPER_BOUND / HELD) | one BOQ for both trades | M | 2 for the conditional faces |
| 6 | **Beam-column adjacency in the route G register** (D-N10-04, OQ-12) | column formwork net of beam junctions; slab edge formwork | M | route G (CRITICAL: test first, byte identity of its outputs) |
| 7 | **Reader-side masonry census** (D-N10-03) | independent masonry verification | S | — |
| 8 | **Roof plan reader** (roof slab, parapets, roof waterproofing kept separate from balconies) | roof finishes and waterproofing | L | — |
| 9 | **Second villa** under the sealed protocol (no blind run until the owner authorises it) | the first accuracy measurement | L | owner |

## Resumable checkpoint

- **Branch:** `claude/access-permissions-setup-ii24ws`. The code is final at 4b299ae (validated by the full suite at that commit). Deliverables follow it.
- **Methods:** `ARCH_TAKEOFF_V2.9` (opt-in). Structural: `tools/struct_n10.py --run OUT --out DIR`.
- **Registry:** 1.5.0 (`tools/kb_build_1_5.py --check`).
- **Tests:** `tests/m9_n10/` (70 tests in 6 files). Hand truth is in `tests/m9_n10/n10_truth.py`.
- **Maps:** `python3 -I tools/codemap.py build` after adding files; `check` must report no stale map.
