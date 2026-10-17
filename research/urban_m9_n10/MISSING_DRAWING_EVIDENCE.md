# Missing drawing evidence (Phase N10)

What the drawings must carry for the held N10 quantities to be measured. The counts are reference-plan aggregates. Each row names the evidence, never a value to assume.

| Quantity | Held on the reference plan | Evidence needed (on the drawing) | Accepted fallback (a stated project fact, labelled) |
|---|---|---|---|
| masonry panel height per floor | 3 floors × families (7 panel + 7 volume lines) | a section whose band is bound to the floor, with T.O.S. (top of the structural slab, at most 0.30 m below F.F.L.) and U/S SLAB | `masonry.{floor}.panel_height_m` + `floor_buildup_m` |
| beams over walls | every family (held at the upper bound) | the structural plan's beam layout and depths, or a section B.O.B. (gives a range) | `masonry.{floor}.beams_over_walls` = NONE / DEPTH |
| wall material by thickness | every family (MAS.BLOCK RFI) | a wall legend / specification | `masonry.materials.{family}` |
| facade height per floor | 3 floors | the floor's section band and the next floor's F.F.L. (or a parapet top above the top floor) | `facade.{floor}.height_m` |
| exterior finish | 3 floors | elevation notes / specification | `facade.finish` |
| plinth (below the lowest F.F.L.) | 1 | the external ground level (section / site plan) | — |
| a second exterior outline per floor | 3 (thin drawing element on a wall layer) | confirmation that it is not part of the building (or a separate layer) | — |
| curved window's sill / head | 1 (reveal BLOCKED, skirting range) | a schedule row or annotation for the curved window | `opening_heights` |
| excavation depth and working space | the structural drawing's 29 pits / trenches | NGL, founding level / blinding thickness (foundation section), working space (specification) | `excavation.{depth_m, ngl_m, founding_level_m, working_space_m}` |
| column formwork height | 115 columns (storey heights not printed) | storey heights / levels on the structural sections | the route G profile (`STOREY_HEIGHT_*`) |
| neck heights | the structural drawing's necks | foundation section levels | — |

**Why sections do not bind on the reference plan.** The section sheets exist, but their F.F.L. bands are not bound to plan floors: the floor names inside the bands, or a plan level, are missing (the binding rules of V2.8). This is the same finding as in Phase 2B-9: room heights there came from the facts file, not the drawing.
