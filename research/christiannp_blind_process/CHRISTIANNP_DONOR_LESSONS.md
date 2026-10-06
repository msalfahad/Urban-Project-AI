# christiannp donor lessons

These lessons are about extraction methods, not quantities. No christiannp total enters any Urban engine or test. The evidence classes are explained in `CHRISTIANNP_BLIND_PROCESS_HANDOFF.md` §0.

## What christiannp genuinely extracted (corroborated by Urban's independent geometry)

| Population | christiannp (RELAYED) | Urban (URBAN_FROZEN) | Agreement |
|---|---|---|---|
| Ground-beam length | 200.036 m, 42 strips | 198.796 m, 59 spans | +0.62 % |
| GF gross slab outline | 324.038 m² (raster) | 322.413 m² (vector) | +0.50 % |
| Built-up area | 598.708 m² | 595.092 m² | +0.61 % |
| 200 mm raw face pairs | 183.497 m | Method B gross 184.897 m | −1.40 m |
| Columns FOU + GF | 32.385 m³ | 32.153 m³ | +0.72 % |
| Footings (schedule L × W × H) | 65.669 m³ | 64.346 released + F/F10 conflict | +1.323 m³, non-unique |
| Slab thickness tags 1F / 2F | 0.16 / 0.18 (implied) | 0.16 / 0.18 | equal |

Where the donor measured raw geometry, it lands within about 1 % of Urban. The large differences all come from what was *done* with that geometry: sections, scopes, heights and classification.

## What was manual reasoning

These are judgement points the method required. Their exact content is NOT_HELD.

- Allocating beam length between labels: sharing remaining length, capping spans, merging repeated marks.
- Continuing CN columns through storeys (A8).
- Splitting column volume between the FOU and GF storeys.
- Classifying raster regions as opening, stair or slab.
- Choosing wall heights.

## What was assumed

- **A1:** GF slab thickness 0.20. This adds +11.622 m³.
- **A5:** ground-beam depth 0.60 on all 42 strips.
- **A7:** ground slab area = GF gross outline.
- **A8:** CN columns continue FOU + GR.

Inferred, but not on the relayed list:

- one wall height of about 4.49 m everywhere;
- stair wells kept in the slab (hypothesis H-SLAB-1);
- 1F / 2F columns measured clear of beams.

A2–A4, A6 and A9–A15 are NOT_HELD.

## Absorb (generic, Urban-native)

1. **Raw primitive reading with handles:** every LINE / ARC / POLYLINE is kept, and a band is a pair of handles. Urban already does this through K2.
2. **Face pairing as an independent geometry route** for beams and walls. Its value is as a *population census*; it is not a quantity.
3. **Raster area as an oracle:** outline, openings and enclosed regions, checked for convergence across resolutions.
4. **Schedule-width vs drawn-width gate** on every beam binding.
5. **Keep measurable geometry when semantics are LOW:** strips, cells and faces survive a missing label or depth. Urban adopted this in the coverage round.
6. **Area and thickness as separate authorities**, each with its own evidence.

## Reject

See `CHRISTIANNP_RECOMMENDATIONS.md` → "What not to learn".

## The single most useful finding

christiannp and Urban see the same physical populations to within about 1 %.

- Urban's historic low numbers came from **publication rules**: technical-only release, label-scoped cells, unmeasured ambiguous bands and finish-gated faces. They did not come from missing extraction.
- The donor's high numbers come from **assumed sections, scopes and heights**.

The coverage round already moved Urban to scenario-layer publication. The donor offers no geometry capability Urban lacks. It offers routes to cross-check that Urban should run as oracles.
