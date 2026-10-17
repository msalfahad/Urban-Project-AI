# Donor lessons: U-C4N and christiannp blind runs

These are extraction methods, not quantities. No donor total enters any Urban engine or test. Donor figures appear only in `post_freeze_comparison.py`, after the freeze.

## Absorbed (implemented natively, generic)

| Idea | Donor | Where in Urban |
|---|---|---|
| Keep measuring when the engineering meaning is incomplete | both | `physical_measurement_state` (three axes; BLOCKED is not zero), `quantity_scenarios`, `population_conservation` |
| Independent occurrence census, more than one route per element | both | `multi_route_evidence` (CONFIDENCE_UP / ROUTE_CONFLICT, never averaged), `beam_occurrence_recovery` (tag / face / continuity routes) |
| Raw LINE / POLYLINE / ARC parallel-face pairing | both | `wall_band_reconciliation.pair_parallel_faces` (Method B), `ground_slab_recovery.decompose` |
| Beam-face / wall-face pairing as a second geometry route | both | the same; classified against columns, openings and duplicate faces |
| Handles on every source object | U-C4N | terminal records keep `source_handles`; extracts keep the source dxf sha256 |
| Independent area route | christiannp | `ground_slab_recovery` (cell union) and `slab_opening_reconciliation` (gross - openings with an id per opening) |
| Region intersection, not the start point | lesson from U-C4N | `ground_beam_recovery.spans_in_region` uses `cad_guards.segment_intersects_region` (regression test) |
| Attribute-first schedule reading, pagination completeness | U-C4N | already in the S3.1 `cad_oracle` / guards; unchanged |

## Rejected (and why)

| Donor behaviour | Why not |
|---|---|
| GF slab thickness assumed 20 cm (U-C4N) | The project rule is 16 cm unless noted. `evidence_ladder` takes PROJECT_GENERAL_RULE before any fallback (regression test). |
| Unreadable Arabic / SHX notes treated as absent | The TEXT_READING ladder (CAD → PDF vector → decode → visual → human) records every attempt; unreadable never means nonexistent. |
| CN columns propagated from neighbours (U-C4N) | `column_concrete_geometry` uses each occurrence's own section; a column without one stays UNQUANTIFIED (regression test). |
| Simplified perimeter ties, ignoring multi-link topology | `column_rebar` (S3) keeps the tie-topology rules; not changed here. |
| Concrete and rebar from different geometry authorities for one beam | `cad_guards.check_geometry_consistency` refuses it (regression test). |
| Values typed into PowerShell instead of bound automatically | Every value carries a ladder level and a fact origin. |
| Aggressive gross conventions (walls through openings and columns; ground slab = whole GF outline) | Kept visible as convention / scope classes in the difference register. They are not adopted as the Urban physical quantity. |
| Incomplete steel (christiannp: CB support / mid bars, top hangers, slab top / diagonal bars, ground-beam steel, stair steel, BOXED footing bars, CN steel, laps, starters, hooks) | ACCURATE_BOQ_REBAR keeps such components BLOCKED_UNQUANTIFIED, so the project stays FINAL_REBAR_NOT_ESTABLISHED (regression tests). |

## What the comparison taught (after the freeze)

- U-C4N and christiannp give identical ground-beam and column figures. Two independent MCP routes agreeing does not mean the source is resolved: both had to assume the exterior depth.
- Their ground-slab volumes equal the GF gross slab outline × 0.10. That is a scope choice (it includes the beam footprints and the openings), not a measurement.
- christiannp's 183.5 m of 200 mm wall is Method B before classification: paired wall + openings + columns + duplicate faces.
