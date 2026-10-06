# christiannp forensic: recommendations

Rule: no idea is recommended because it brings a total closer to the freelancer, U-C4N or christiannp. Each idea is ranked by the generic problem it solves. Nothing here is implemented in this round.

## Ranked reusable ideas

| Rank | Idea | Donor source | Problem solved | Generic implementation | Risk | False-positive risk | Required tests | Production / oracle | Trades |
|---|---|---|---|---|---|---|---|---|---|
| P0 | **Candidate geometry when semantic authority is missing** | both donors (kept LOW-confidence measurable quantities) | a missing depth, label or finish erases a measured population | already in `physical_measurement_state` / `quantity_scenarios`; extend to every trade's publication | low | none (layers stay separate) | blocked object with measured geometry publishes best > 0, official unchanged | PRODUCTION | all |
| P0 | **Schedule-width vs drawn-width gate** | beam rules (relayed behaviour) | wrong label binds to a strip | when the drawn band width differs from the schedule B beyond tolerance, record WIDTH_MISMATCH on the binding; never force | low | low | B=0.30 tag on a 0.20 band is flagged, not bound | PRODUCTION | beams, GB |
| P0 | **Wall-face pairing + classification as a required cross-route** | wall pairing | unexplained wall-length gaps between routes | `wall_band_reconciliation` per project; every metre gets a class (PAIRED_WALL / OPENING_SPAN / COLUMN_OVERLAP / DUPLICATE) | low | medium (finish lines at wall width) | door gap → OPENING_SPAN; column face → COLUMN_OVERLAP; duplicate face → DUPLICATE; finish line pair at 15 mm → rejected | PRODUCTION cross-check (never a quantity source) | blockwork, plaster |
| P0 | **Physical wall-face preservation** | plaster lesson (as a counter-example) | finish gating hides face area | `physical_wall_faces` feeds plaster / paint; finish is an attribute, not a gate | low | low | face area = length × (interval − member) − openings, per face; no assumed storey height | PRODUCTION | finishes |
| P1 | **Beam edge pairing as an occurrence census** | GB / beam strips | unbound tags and missed beams | pair faces on the beam layer, then compare strips with tag-bound occurrences: STRIP_WITHOUT_TAG → CANDIDATE, TAG_WITHOUT_STRIP → UNQUANTIFIED with identity | medium | medium (slab-edge lines, kerbs) | strip with no tag survives as CANDIDATE; tag with no strip stays UNQUANTIFIED; curved strips use arc length | PRODUCTION census, quantity via the normal section ladder | beams, GB |
| P1 | **Unlabelled-member recovery** | GB strips, slab cells | label scope drops real members | already for GB / slab cells; extend to beams with the width gate | medium | medium | unlabelled strip between two supports quantified as CANDIDATE with B from geometry, D from ladder | PRODUCTION | beams, slabs |
| P1 | **Schedule ATTRIB-first reading** | both donors | text-matching errors on schedules | read INSERT ATTRIB values before TEXT; paginate; record handles | low | low | ATTRIB value wins over a nearby TEXT; missing ATTRIB falls back with a record | PRODUCTION | footings, columns, beams |
| P1 | **Outline / tag dual route for footings** | footing extraction | F3 count, F/F10, FN irregular outlines | route 1: closed outlines; route 2: tags; reconcile each outline to one tag, or to a conflict record (`multi_route_evidence`) | low | low | outline without tag → CANDIDATE; two tags in one outline → SOURCE_CONFLICT; irregular FN → polygon area, not bbox | PRODUCTION cross-check | footings |
| P1 | **Multi-route agreement confidence** | both donors vs Urban | single-route false confidence | CONFIDENCE_UP only when routes are independent (different primitives / algorithms); identical outputs from two routes must be checked for shared inputs | low | n/a | two routes reading the same helper do not raise confidence; FOU / GF identical in both donors flagged | PRODUCTION metadata | all |
| P2 | **Raster / flood-fill slab reconstruction** | 50 mm raster | an independent area check of the vector topology | layer-filtered raster at 100 / 50 / 25 / 10 mm, two origins; classes outside / slab / opening / unresolved; compare with vector per region | medium | high at coarse cells (gap closure, leaks) | convergence < 0.5 % from 25 to 10 mm; component count stable; leak test (1-cell gap at a door); thin-void test (< 1 cell) | **ORACLE ONLY** | slabs, ground slab, BUA |
| P2 | **Coordinate alignment between sheets** | column floor membership | wrong floor or plan assignment | per-sheet frame from grid lines / sheet frames (Urban FLOOR_PLAN_REGISTER); transform recorded per object | medium | low | same grid bubble maps to the same world point on every plan | PRODUCTION (already partly in K2 region frames) | columns, beams |

## What not to learn

| Technique | Why rejected |
|---|---|
| Hard-coding a 0.60 m ground-beam depth (A5) | It contradicts the printed details on 27 of 31 interior spans and has no source on the exterior. Urban keeps a BOUNDED scenario and asks the consultant. |
| GF slab 0.20 m (A1) | The project rule is 0.16 m unless locally noted. A general note outranks an assumed value (+11.6 m³ error). |
| Carrying CN columns upward automatically (A8) | Continuation must come from each storey's own plan occurrence. It conflicts with the human review. |
| Ground slab = whole GF outline as verified truth (A7) | A suspended-slab outline is not slab-on-grade evidence. It includes beam and column footprints. At most it is a HIGH scenario. |
| Uniform default wall height (≈ 4.49 m inferred) | A height is a per-face fact (interval − member), and a storey height is not a wall height. |
| Raw face pairs as wall length | Openings, column faces and duplicate faces are not wall (≈ 73 m of the 200 mm figure). |
| Keeping stair wells in the slab plate (H-SLAB-1, if confirmed) | It double-counts with stair concrete. |
| Sharing remaining beam length among labels by arithmetic | Allocation must follow geometry. Arithmetic sharing hides binding errors. |
| Gross stirrup perimeter as final BBS | It ignores tie topology (multi-link). ACCURATE_BOQ_REBAR keeps such components BLOCKED. |
| Interpreting unreadable source as absent | Unreadable is a TEXT_READING-ladder state, never "no note". |
| Manual value passing between tools | Every value needs a ladder level and a handle. |

## Top 10 generic Urban improvements

1. Scenario-layer publication in every BOQ / dashboard view (P0, carried from the coverage round).
2. Schedule-width vs drawn-width gate on bindings.
3. Wall-band reconciliation as a mandatory cross-route with per-metre classes.
4. Physical wall faces feeding finishes.
5. Beam face-pair census vs tag census (STRIP_WITHOUT_TAG / TAG_WITHOUT_STRIP).
6. Footing outline / tag dual route.
7. ATTRIB-first schedule reading with pagination completeness.
8. Route-independence check before CONFIDENCE_UP.
9. Raster area oracle with a convergence protocol (oracle only).
10. A per-object donor intake format (handles, section, rule id), so future blind runs can be compared object by object and not by totals.

## Exact tests required (when implemented)

- `test_uniform_depth_never_overrides_detail_depth`: a span with a DETAIL depth keeps it when a project-wide fallback exists.
- `test_width_gate_flags_mismatched_binding`
- `test_strip_without_tag_is_candidate` / `test_tag_without_strip_keeps_identity`
- `test_ground_slab_area_excludes_beam_and_column_footprints`
- `test_floor_outline_never_verified_as_slab_on_grade`
- `test_pairs_across_door_classify_as_opening_span`, `test_pairs_along_column_face_classify_as_column_overlap`, `test_duplicate_face_pairs_counted_once`, `test_finish_line_pair_rejected`
- `test_wall_face_height_is_interval_minus_member` (no storey constant)
- `test_stair_well_deducted_from_slab_plate`
- `test_footing_outline_two_tags_is_source_conflict`, `test_irregular_footing_uses_polygon_area`
- `test_identical_routes_do_not_raise_confidence`
- Raster oracle:
  - `test_raster_convergence_25_to_10mm`
  - `test_raster_origin_shift_within_edge_band`
  - `test_flood_fill_leak_through_one_cell_gap_detected`
  - `test_thin_void_below_cell_size_reported_unresolved`
- Package: `tests/christiannp_blind_process/test_package.py` (added in this round): evidence classes present, A–E classification on every gap row, donor pairs declared NOT_PRESERVED, builder reproduces the outputs byte for byte.
