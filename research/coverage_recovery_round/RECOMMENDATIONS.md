# Coverage recovery: answers and recommendations

Baseline `24bd540`. S4 (footing rebar) has not been started.

## Direct answers (A–M)

**A. Ground beams.**
- Urban never lost the population: all 59 spans and the 110.3 m exterior length were measured.
- The 28 exterior spans have the depth "FOLLOW ARCH." and no printed dimension. The technical release turned the missing depth into BLOCKED, and the comparisons then read the technical layer as zero.
- The V3b commercial layer already held 33.09 m³ (29.8–43.0).

**B. Ground slab.**
- A slab region was released only where a `T=` label sat inside it.
- Nine cells (101.7 m²) between the ground beams of the main footprint carried no label and were never measured.
- This was a genuine loss. It is now recovered as CANDIDATE.

**C. Columns.**
- The census was complete, but the concrete waited for clear height (a beam depth per face) and for the founding level.
- As a result, 47 of 95 occurrences had no technical concrete.
- Measuring B × D × (interval − slab thickness above) needs neither, and gives 95/95. The totals then agree with the donors within about 2%. The remaining difference is the split between the foundation and GF storeys.

**D. Beams: missing vs blocked.**
- Blocked but measurable: 16 residue objects with bands (span-count mismatch, type conflict, no parallel band).
- Missing geometry: 8 tags without any band. These are possibly repeats of measured beams.
- Duplicate removed: 1 (B3/CB3 on the same band).

**E. 200 mm walls.**
- Urban never measured 12 WALL_BAND_AMBIGUOUS bands (44.3 m).
- Urban also excludes column overlap (12.9 m) as a convention.
- Urban best + overlap = 147.0 m.
- christiannp's 183.5 m corresponds to raw parallel pairs including openings, columns and duplicate faces.

**F. Adopt from U-C4N:**
- an independent occurrence census;
- handles on every object;
- face pairing as a second route;
- attribute-first schedules;
- keep measuring when the meaning is open.

**G. Adopt from christiannp:**
- raw LINE / ARC / POLYLINE extraction;
- an independent area route;
- wall-face pairing as a challenger route.

**H. Do not adopt:**
- assumed thicknesses (20 cm);
- unreadable = absent;
- CN propagation;
- simplified ties;
- mixed geometry authorities;
- manual value passing;
- gross-through-openings conventions as the physical quantity.

**I. Where Urban is too conservative:**
- publishing only the technical layer;
- label-scoped slabs;
- clear-height-dependent column concrete;
- ambiguous wall bands never measured;
- faces waiting for finish certification.

**J. Where the donors are too aggressive:**
- ground slab = whole GF outline;
- walls through openings and columns;
- assumed slab thickness;
- exterior ground-beam depth assumed without a source.

**K. Single most valuable generic change:** publish every quantity as scenario layers (verified / lower bound / best / low / high / unquantified) with the release state derived, never chosen. BLOCKED becomes a review state instead of a zero.

**L. Solvable automatically, without the consultant:**
- column concrete (net-of-slab basis);
- ground-slab cell geometry;
- wall-band reconciliation;
- beam continuity / width binding;
- opening provenance;
- physical wall faces;
- the BAND_TYPE_CONFLICT duplicate.

**M. Genuinely needs the consultant:**
- exterior ground-beam depth;
- whether the T=10cm note applies to all ground-slab panels;
- founding level;
- whether the GF T16 "VOID" face is open;
- which ambiguous bands are walls;
- the CB8 span count.

## Ranked recommendations

| Rank | Recommendation | Benefit | Risk | Trade | Effort |
|---|---|---|---|---|---|
| P0 | Adopt the scenario-layer publication (`quantity_scenarios`, `physical_measurement_state`) in the BOQ / dashboard for every trade; drop technical-only totals from comparisons | Removes the systemic "BLOCKED = 0" undercount on every project | Low (layers stay separate; procurement still uses OFFICIAL) | all | M |
| P0 | Column concrete from `column_concrete_geometry` (net of slab); joints included | 95/95 occurrences quantified; rebar blockers decoupled | Low | columns | S |
| P0 | Ground slab from `ground_slab_recovery` cells; label scope as a question, not a filter | +101.7 m² recovered; footprint anomaly closes | Low–Medium (cells may not all be slab-on-grade, so low = official) | ground slab | S |
| P0 | Send the four consultant questions (exterior GB depth, slab-note scope, founding level, GF T16 void) | Converts the largest provisional bands into source facts | None | GB / slab / columns / slabs | S |
| P1 | Measure WALL_BAND_AMBIGUOUS bands as CANDIDATE length and run `wall_band_reconciliation` per project | Explains the 200 mm wall gap metre by metre | Medium (some bands may be kerbs or parapets) | blockwork | M |
| P1 | Physical wall faces before finish semantics (`physical_wall_faces`) feeding plaster / paint | Plaster / paint scope visible without certification | Low | finishes | M |
| P1 | Beam binding ladder (continuity, width match) on the 8 unbound tags; confirm CB8 spans | Closes the beam residue | Medium (duplicates) | beams | M |
| P1 | Store Urban band and cell geometry (coordinates) in the frozen registers | Enables per-segment URBAN_MISSED classification and Method C | Low | walls / slabs | S |
| P2 | Method C (room adjacency) for walls; second route for footings (tag vs closed outline) | Extra confidence through multiple routes | Low | walls / footings | M |
| P2 | Live read-only CAD oracle re-runs instead of figures recorded from the brief | Fresher post-freeze checks | Low | all | M |

## Next

After review: S4 GENERIC FOOTING REBAR ENGINE (accurate parts only), on top of the scenario-layer publication.
