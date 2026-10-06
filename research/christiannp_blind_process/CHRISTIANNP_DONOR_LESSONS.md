# christiannp donor lessons (v2)

Evidence classes are REPORT_EXPLICIT / URBAN_FROZEN / ARITHMETIC_INFERENCE / NOT_HELD; see the handoff §0. REPORT_EXPLICIT items are imported from your quotation of the sealed report; the file check is pending. No christiannp total enters any Urban engine or test.

## What christiannp genuinely extracted

These are raw geometry results, each confirmed by an Urban route that shares nothing with the donor (INDEPENDENT_EXTRACTION_AGREEMENT):

| Population | Report | Urban (versioned) | Agreement |
|---|---|---|---|
| Ground-beam network | 85 raw lines → 42 paired strips, 200.036 m, 300 mm | 43 paired bands → 59 spans, 198.796 m | +0.62 % length; 42 vs 43 bands |
| Built-up area | 598.708 m² | 595.092 m² | +0.61 % |
| GF gross slab outline | 324.038 m² (raster) | 322.413 m² (vector) | +0.50 % |
| Columns FOU + GF | 32.385 m³ | 32.153 m³ | +0.72 % (split differs by A2 / A3) |
| 200 mm raw face pairs | 183.497 m | Method-B gross 184.897 m | −1.4 m |
| Slab thickness tags 1F / 2F | 0.16 / 0.18 (implied) | 0.16 / 0.18 | equal |

## What was assumed (REPORT_EXPLICIT A1–A15)

The assumptions fall into four groups by what they decide:

- **Sections and levels:** A1, A2, A3, A4, A5, A12.
- **Scopes:** A7, A11, A14, A15.
- **Heights and openings:** A10, A13.
- **Element models:** A6, A8, A9.

Only A4 (a level derived from printed intervals) and A6 (blinding, matching a source detail Urban reads) survive Urban review. Every large donor-over-Urban difference traces to one of them:

- A1: +11.6 m³ on slabs;
- A5: +4.7 m³ on interior ground beams;
- A7: about +10.7 m³ on the ground slab;
- A10 / A13: plaster;
- A14 / A15: finishes and waterproofing scope.

## What was manual reasoning or rule-based allocation

- The beam rules R1–R5 are REPORT_EXPLICIT. R5 (leftover length shared equally) is arithmetic allocation, not measurement.
- Who applied the rules, and where judgement entered beyond them, is NOT_HELD.

## Absorb (independent Urban implementations only)

1. Face pairing as a population census for beams and walls, followed by per-metre classification.
2. The width check from R4, recorded as a gate rather than a silent re-assignment.
3. Continuous-beam occurrence-once per plan from R1, with any span excess as a conflict, never a truncation.
4. Collinear continuation from R2, as CANDIDATE evidence with a width check and a support stop.
5. A raster area oracle with the report's five output classes, rebuilt independently, run to convergence, oracle-only.
6. Separate thickness and area authorities; a declared storey-boundary convention on every column record.
7. Treating donor-donor agreement as correlated by default, with an explicit agreement class.

## Reject

- R5.
- R3's fixed 2 m merge distance.
- A1, A5, A7, A8, A14, A15 as values.
- A2, A3, A9, A10, A11, A12, A13 as production defaults.
- Comparing 22.916 t (KNOWN_INCOMPLETE_NET_DRAWING_REBAR) with Urban's accurate rebar.

## The most useful finding

christiannp and Urban reconstruct the same physical networks: ground beams, slab outlines, built-up area and face pairs. Every large quantity difference is decided by a named, report-explicit assumption or rule.

Urban's lesson is about publication and classification, not extraction: keep measuring when semantics are missing, classify every metre, and never let an assumption become a section. The coverage round already carries the first part.
