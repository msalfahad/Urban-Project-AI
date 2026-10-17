# 07 Post-S4 frozen backlog

These are R9.1 lessons, recorded and **not implemented** in this round. None of them blocks S4 or changes a footing quantity.

| # | Item | R9.1 evidence | Fixture (R9.1 17) | Trigger |
|---|---|---|---|---|
| 1 | Multi-partner ground-beam pairing (fragmented mate) | 03 S008: one strip missed, 1.000 m | GB-03 | next GB change |
| 2 | Curved-beam arc angular overlap | 03 S044: +0.718 m | GB-05 | next GB change |
| 3 | S-OPENING edges as slab barriers | 10: GF void merged with a labelled cell (27.08 = 20.15 + 6.98 m²) | SL-01 | next slab change |
| 4 | Lift-pit outline (S-BW box) excluded from the ground slab | 05: +0.880 m² (URBAN_FALSE_POSITIVE) | SL-02 | next ground-slab change |
| 5 | Wall pairs at arbitrary widths | 07: 400 mm wall + fragmented mate, 2.485 m | WL-04 | next wall change |
| 6 | Structural-beam tag tie-break (orientation + width ± 30 mm, R4 as gate) | 06: 6 AMBIGUOUS tags | BM-01 | next beam-binding change |
| 7 | Raster slab oracle (test-only) | 05: raster converges to 0.11 % at 10 mm, under-reads by the edge band | — | QA lane, never a quantity |
| 8 | Wall-opening convention reconciliation | 07: Urban 53.96 m against christiannp 9.94 m opening deduction | WL-01 | with the convention profiles |
| 9 | Full bar-grammar unification | 11: 6 split patterns / 52 rows, none of them footing tokens; this round's guard fails closed on them | RB-01 (all classes) | before S4 reads slab / column-tie / detail notes |

Also after S4:
- Convention profiles beyond the `CONVENTION_ID` field (column split, strap length, column storey, beam depth).
- PyMuPDF: `COMMERCIAL_ARCHITECTURE_ACTION_REQUIRED` (00 §PyMuPDF).
