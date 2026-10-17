# Owner decisions register (Phase N10)

## 1. Owner decisions applied (as stated in the N10 program)

| Decision | How N10 applies it | Where |
|---|---|---|
| Heights come from the drawings first | masonry panel from the floor's section T.O.S. → U/S SLAB; facade from its section F.F.L. → next F.F.L.; a stated fact only as a labelled fallback; nothing defaulted | `engine/source/arch_v29.py` masonry_evidence, facade_evidence |
| No invented masonry height; a finishing height is never a masonry height | F.C.L. / plaster heights and floor-to-floor are never used for the panel; without T.O.S. and U/S SLAB the panel is held (MASONRY_HEIGHT_NOT_IN_THE_DRAWING) | `test_no_masonry_height_without_its_evidence` |
| Door fallback height 2.20 m | used only where the V2.8 schedule already falls back to it (labelled HEIGHT_ASSUMED); masonry and facade deductions carry the label | `test_curved_door` (D2 2.20 m, assumed) |
| Wall thickness and reveal depths from geometry | curved reveal depth = strip area / (sweep × mid radius); wall thickness = radius difference | UP-OPEN-CURVED-001 |
| No invented stair dimensions, reinforcement or concrete geometry | the structural N10 module reads route G's register only; it never creates a dimension; necks without a height and columns without a storey height are held | `engine/source/struct_n10.py` |
| Roof and balcony waterproofing kept separate | unchanged (no N10 change) | — |
| Unresolved decisions: set out alternatives and hold the dependent quantities | formwork FW-D1 / FW-D2 kept side by side, never summed; masonry beams over walls held at the upper bound; facade finish held | OQ-06 – OQ-13 |

## 2. Decisions this phase needs from the owner

Each one is in registry 1.5.0 as an owner question (`knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json`).

| id | Question | Alternatives | What waits on it | Engine meanwhile |
|---|---|---|---|---|
| OQ-06 | Which walls carry a beam, and how deep is it? | a stated "no beams over walls" fact; the structural plan's beam layout | ARCH.WALL_PANEL / VOLUME, MAS.BLOCK | held at the upper bound (or a range with a section B.O.B.) |
| OQ-07 | What is each wall thickness built of? | legend / specification; a project fact `masonry.materials` | MAS.BLOCK | RFI naming the family |
| OQ-08 | Is the facade of a floor measured F.F.L. → next F.F.L.? | F.F.L. → F.F.L.; slab top → slab top; a stated height per floor | ARCH.FACADE | F.F.L. → F.F.L. when both levels are on the floor's section band |
| OQ-09 | External ground level, and the exterior finish system? | a section / site level; elevation notes / specification / fact `facade.finish` | ARCH.FACADE plinth, FIN.EXT.FINISH | held |
| OQ-10 | Are footing and ground-beam sides formed, or cast against the excavation? | FORMED / EARTH_CAST | formwork FOOTINGS / GROUND_BEAMS sides | both reported, never summed |
| OQ-11 | Is the schedule beam depth below the slab, or the total depth? | BELOW_SLAB / TOTAL | formwork beam sides (and route G's beam concrete) | both reported |
| OQ-12 | Beam-column adjacency and slab free edges | the structural plan | column sides (upper bound), slab edges (held) | as stated |
| OQ-13 | NGL, founding level and working space | foundation section / soil report / specification | excavation volume, backfill | footprints only |

Earlier open owner questions OQ-01 – OQ-05 are unchanged (registry 1.4.0, carried into 1.5.0 byte for byte).

## 3. Status of the five new rules

Every new rule is **REQUIRES_CONFIRMATION**. It is the engine's reading of the owner program, not an owner statement.
No interpretation was promoted to OWNER_APPROVED.

| Rule | Status |
|---|---|
| UP-OPEN-CURVED-001 | REQUIRES_CONFIRMATION |
| UP-MAS-HEIGHT-001 | REQUIRES_CONFIRMATION |
| UP-FACADE-001 | REQUIRES_CONFIRMATION |
| UP-FW-001 | REQUIRES_CONFIRMATION |
| UP-EXC-001 | REQUIRES_CONFIRMATION |
