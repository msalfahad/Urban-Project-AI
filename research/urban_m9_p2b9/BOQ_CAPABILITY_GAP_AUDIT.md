# BOQ capability gap audit (Phase 2B-9)

**Statuses.**

- **Supported**: measured from the drawing with a stated rule and a hand-verified test, released when its inputs are
  evidenced.
- **Partial**: measured with a gap: PROVISIONAL, needs evidence the drawings often lack, or only part of the item.
- **Unsupported**: no quantity; the item is absent or BLOCKED by design.

The architectural statuses are for ARCH_TAKEOFF_V2.8. The structural / site statuses come from the earlier stage
reports (route G and the structural stage packages) and were **not re-verified** in this phase. This phase spent its
effort on architectural accuracy, as instructed; no structural work was added.

## Architectural

| Category | Status | Detail / what is missing |
|---|---|---|
| Floor porcelain, dry rooms | Supported | material BY_SPEC; tile layout calculator for rectangles only |
| Wet floor tile | Supported | review spaces conditional (D-17) |
| Skirting | Supported | V2.8: floor glazing excluded, unknown sills a range |
| Wall porcelain, wet rooms | Supported with evidenced heights, else Partial | full height from F.C.L. (UP-FIN-WALL-001); a lower printed tile height governs |
| Internal plaster | Supported with a soffit level, else Partial | heights from sections / notes; the reference plan has none (facts only) |
| Paint | Supported with a ceiling level, else Partial | paint above a part-height tile: Partial |
| Ceilings (area) | Partial | area measured; type, bulkheads, coves and false-ceiling build-up are not in a plan (PROVISIONAL) |
| Window reveals and sills | Partial (new) | jambs / head plaster PROVISIONAL; sill finish by the window detail |
| Door jamb plaster | Partial | PROVISIONAL (frame detail) |
| Marble thresholds | Supported | wet-room doorways (UP-THR-001) |
| Doors: count, class, width | Supported | D-16 owner minimum is conditional |
| Door heights / areas | Partial (new) | schedule / annotation / section; otherwise labelled Urban default |
| Ironmongery, door frames | Unsupported | not in a plan |
| Windows: count, width | Supported | — |
| Windows: height, sill, area, class | Partial (new) | needs a schedule or annotations; elevations not read |
| Aluminium systems, curtain walls, glazing spec | Unsupported | the system is a specification |
| Waterproofing: floor, upturn, doorway, rolls | Supported | V2.5 / V2.6 proofs |
| Waterproofing: corners, penetrations, junction | Partial | counted, treatment withheld without a detail |
| Roof, balcony and terrace waterproofing | Partial | its own scope (UP-WP-ROOF-001) where drawn as spaces |
| Roof screed, insulation, roof tiles | Unsupported | needs the roof build-up |
| Wall run (lm, by thickness) | Partial | PROVISIONAL; V2.8 adds stubs / returns |
| Blockwork (m², m³) | Unsupported | needs the material and the block height to the soffit / beam (T.O.S., beam depths) |
| Stairs: treads, landings | Partial | earlier stair stages |
| Stairs: risers, flights, railings, handrails | Unsupported | heights from sections; rail spec |
| Facade: external plaster, paint, stone cladding | Unsupported | the outer faces are measured (V2.8 outer arcs, wall bands) but no external finish line exists |
| Screed and floor build-up | Unsupported | levels and build-up not read |
| Sanitary fixtures, kitchen units | Unsupported | the fixture census is evidence for wet classification only |
| MEP | Unsupported | out of scope |

## Structural and site (from the earlier stage reports; not re-verified)

| Category | Status | Detail |
|---|---|---|
| Concrete: footings, necks, ground beams, columns, beams, slabs | Partial (generic route G) / Supported (reference-villa stage packages) | depth conventions, schedules |
| Concrete: stairs, lintels, pool, water tank, lift pit / shaft, domes, parapets, boundary walls | Partial | stage-specific engines; generic detection partial |
| Blinding | Partial | — |
| Reinforcement | Partial | bar schedules and completeness register; many components blocked |
| Formwork | Unsupported | catalogue gap |
| Excavation, backfill, disposal | Unsupported | catalogue gap |
| Anti-termite, polythene, foundation bitumen | Unsupported | catalogue gap |
| External works: paving, landscaping, boundary wall finishes | Unsupported | ARCH.EXTERIOR area only |

## Highest-value gaps for architectural completeness

The gaps are listed in order:

1. **Evidence the drawings must carry** (sections, schedules). Without them every wall-area line is held or based
   on facts.
2. **Blockwork m² / m³.** The geometry exists; it needs the block height and the material.
3. **Facade finishes.** The outer faces are already measured.
4. **Ceiling types and bulkheads** (the reflected ceiling plan).
5. **Stair risers and flights** from sections.
