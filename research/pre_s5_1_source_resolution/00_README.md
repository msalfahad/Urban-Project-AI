# PRE-S5.1: ground-system source resolution and provenance cleanup

| Item | Value |
|---|---|
| Baseline | `0a23c06` (pre-S5 accepted; S4 frozen; S5 not started) |
| Builder | `build_pre_s5_1.py [ST7757.dxf] [P7757.dxf]` (both sha256-checked; byte-identical on rebuild) |
| Engines | `engine/source/rebar_provenance.py` (generic identity), `engine/source/ground_system_provenance.py` (rebased), `engine/source/ground_system_resolution.py` (decisions) |
| Drawings | ST7757.dxf `9f9d1179a5d2...`, P7757.dxf `ab54dd554c31...` |

**No steel mass is calculated and S5 is not started.** This round resolves the sources behind the pre-S5 readiness
matrix: the exterior walls from the architecture, the FOLLOW ARCH. depth, the length basis, concentrated loads, the
nested length conditions, SB2 and the free ends. It also replaces two shortcuts: the footing-shaped beam provenance and
the min(clear, c/c) bar run.

## 1. Provenance (01)

- The generic contract `rebar_provenance` carries `ELEMENT_OCCURRENCE_ID`, `ELEMENT_MARK` and `ELEMENT_FAMILY`.
  The FOOTING family keeps `FOOTING_*` as aliases that must equal `ELEMENT_*`. Any other family is **rejected** if it
  carries a `FOOTING_*` key.
- `ground_system_provenance.validate_s5_part` no longer fills the footing slots with the beam id. It runs the generic
  validator and then the member fields.
- The generic validator gives the same verdict as the frozen `validate_s4_part` on all 84 S4 records and 10
  mutations of each (840 cases). The S4 freeze manifest is untouched.

## 2. Bar run (05)

- The pre-S5 `min(clear, c/c)` lower bound is removed from the code.
- Four lengths are now stored per span:
  - MEMBER_CENTERLINE_LENGTH: support reference to support reference;
  - MEMBER_CLEAR_CONCRETE_LENGTH: the frozen band piece;
  - SUPPORT_FACE_TO_FACE_RUN: the centreline against the actual support faces;
  - BAR_STRAIGHT_RUN_LOWER_BOUND: the shortest face-to-face run over the centreline and the two outer bar lines
    (half width − 70 mm soil cover), so an oblique support is not over-measured.
- A support beside the line (offset column, L-corner) is met at its face plane.

| LENGTH_STATE | Spans |
|---|---|
| BAR_RUN_GEOMETRY_UNRESOLVED | 1 |
| CONSISTENT | 51 |
| LENGTH_GEOMETRY_CONFLICT | 7 |

- **LENGTH_GEOMETRY_CONFLICT spans** (136-7D5-1, 177-7CD-2, 17E-17F-1, 180-181-1, 182-183-1, 7E0-FD-1, A-157-158-1) are never resolved by taking the smaller number. They are:
  - two spans whose support column does not cut the full beam width (the concrete piece is longer than the centreline);
  - five spans with oblique or arc-trimmed ends, where the frozen band (the overlap of the paired faces) stops short of
    the support face the bar lines reach.
- **BAR_RUN_GEOMETRY_UNRESOLVED:** 1811-1812-1. This span ends on the plot boundary with no support.

## 3. Architectural exterior-wall overlay (02)

**Registration:**
- P7757 GF to ST7757 GBP: 30/30 architectural column outlines land on equal GF-roof-slab outlines under one translation (second best 1).
- GFRS and GBP share their sheet frame. Translation arch → GBP = [241057.656, 841641.496] mm.

**Wall line along each span:**
- The span centreline is cut every 50 mm across the beam width + 50 mm.
- A parallel P7757 GF wall-line element crossing the cut covers that station. The elements are paired masonry
  (R5 60–450 mm pairing), single wall lines, glazing and curved wall or glazing.
- Door or gate geometry in an uncovered station counts as an opening in the line.

**Exterior class of every wall element:** both faces are probed 400 mm out and classified on the frozen S1 GBP slab
panels:
- ground slab = inside;
- S1 OUTSIDE_BUILDING_OR_COURT = outside;
- beyond the panelled plate = outside;
- the one unpanelled hole (53.83 m²) carries interior labels (DINING, W.C, +1.00), so it counts as inside.

| WALL_CLASS (relation) | Spans |
|---|---|
| AMBIGUOUS_WALL_RELATION | 6 |
| NO_WALL_ABOVE | 12 |
| UNDER_EXTERIOR_WALL | 23 |
| UNDER_INTERIOR_WALL | 18 |

## 4. Exterior authority (03)

The architecture decides. The structural ground-slab edge may only contradict it (SOURCE_CONFLICT). The V3 zone and
R4 footprint proxies are recorded and never voted.

| EXTERIOR_AUTHORITY | Spans |
|---|---|
| CANDIDATE_EXTERIOR | 2 |
| EXTERIOR_SOURCE_VERIFIED | 22 |
| INTERIOR_SOURCE_VERIFIED | 29 |
| SOURCE_CONFLICT | 1 |
| UNRESOLVED | 5 |

**The 19 spans on which the two proxies disagreed: 16 resolved by architecture**
(7 exterior, 9 interior), the rest:
- 10B-7D1-1: CANDIDATE_EXTERIOR
- 180D-180E-1: UNRESOLVED
- 1811-1812-1: UNRESOLVED

## 5. FOLLOW ARCH. depth (04)

**What the p.13 exterior section actually draws (crop P13_GB_EXTERIOR):**
- The depth dimension "FOLLOW ARCH." runs from the "Ground Floor slab level" arrow to the beam soffit.
- The dashed "Outer Normal ground level" line is drawn **at the beam soffit**.
- The R4 transcription's word "below" has no printed source. S1 reads it the same way: "outer normal ground level to
  GF slab level".

**Levels:**
- Outer natural ground is ±0.00 (sections A-A VE-AA-01 and B-B VE-BB-01; plan ±0.00 marks outside the plot).
- GF FFL is +1.00 in the main block (100 cm chain VE-AA-08). The annex block is +0.30. Court paving is +0.15.

**What is not printed:**
- the floor build-up between FFL and slab top (S1 level register);
- any depth.

**Result:** D = (FFL − build-up) − NGL is **bounded above only**.

| Outcome | Spans |
|---|---|
| BOUNDED | 26 |
| UNRESOLVED | 4 |

| D_MAX (m) | Spans |
|---|---|
| 0.3 | 8 |
| 1.0 | 18 |
| None | 4 |

The 8 annex spans at +0.30 give D ≤ 0.30 m. That is shallower than any cross-verified
typical section and cannot hold the drawn three bar levels with 70 mm cover. This is an engineering question (11).

## 6. Length basis of the p.13 titles (05)

**Sources searched:**
- **p.13 titles:** say "length" with no basis.
- **GBP plan dimensions:** 35 dimensions, all axis-to-axis grid chains plus edge offsets
  ({'AXIS-FACE': 4, 'AXIS-AXIS': 27, 'AXIS-OTHER': 4}). None measures a beam span.
- **CB typical figure:** uses both Ln and L.
- **Lintel schedule:** measures openings.

The basis is therefore **not stated**. The clear basis is tested on the support face-to-face run (concrete clear where
unresolved), alongside the centreline basis.

- SAME_RESULT on 48 spans.
- The basis changes the detail on 11 spans: 10B-7D1-1, 10B-7D1-2, 137-138-1, 142-7D8-1, 145-7CA-2, 15C-7CC-1, 15D-7C8-1, 17C-7E3-1, 1811-1812-1, 182-183-1, A-157-158-1.

A basis-dependent component releases only where it is identical in both bases' details.

## 7. Concentrated loads (06)

| LOAD_STATE | Spans |
|---|---|
| NO_CONCENTRATED_LOAD_EVIDENCE | 28 |
| UNKNOWN | 31 |

**Evidence kinds:** {'BEAM_END_REACTION': 41, 'UNIDENTIFIED_SYMBOL': 5, 'JUNCTION_AT_SUPPORT': 12, 'STAIR_BEARING_CANDIDATE': 5}.

**What was checked:**
- **Columns bearing on a span or planted on a ground beam: none.** All 36 GBP column chains start at FOUNDATION. The 3
  planted columns sit on the GF and 1F roof slabs.
- **Loads, symbols and notes on GBP:** no LOAD / kN / P= note.
- **Two '******' marks:** S-TEXT, no legend.

**Why UNKNOWN is not treated as no load:**
- Most UNKNOWN spans have another ground beam **ending** mid-span (BEAM_END_REACTION). The others are the
  reception stair zone or an unidentified mark.
- The interior p.13 sections are titled "without concentrated load", and no loaded section is drawn.
- So under UNKNOWN the loaded case is a separate candidate with no detail. An interior span that needs the
  ≥ 2.5 m sections is blocked until the engineer says whether a framing ground beam counts.
- The < 2.5 m and exterior sections carry no such clause, so those spans are unaffected.

## 8–9. Nested < 2.5 m / < 5 m and the 2.5 m stirrup (07)

- **Precedence:** 23 spans meet both "Less than 2.5m" and "Less than 5m" literally. No note or
  drawn grouping orders them, so RULE_PRECEDENCE_SOURCE = SPECIFICITY_CANDIDATE and both details are preserved.
- **Longitudinal bars:** identical (3Ø14 in all three positions), so they are candidate-invariant and release.
- **2.5 m stirrup:** the section draws a closed link with **no size or spacing**. No project note gives ground-beam
  links (P9 column ties and the CB figure are other members).
- **Stirrup state:** BLOCKED_COMPONENT on every span where the 2.5 m section is a candidate. Ø8/150 is never
  inherited.

## 10. SB2 (08)

Two SBT rows share the key SB2.

| Facet | State |
|---|---|
| Section | width SOURCE_CONFLICT (80 vs 100); depth 50 is candidate-invariant |
| TOP and BOTTOM bars | BLOCKED (10Ø18 / 10Ø18 vs 20Ø18 / 10Ø16) |
| Stirrups (10Ø8/m in both rows) | CANDIDATE_INVARIANT: Ø and rate READY, count LOWER_BOUND |
| Link path | BLOCKED (width and topology) |

The plan's drawn width of 987 mm is recorded but does not adjudicate.

## 11. SB1 / SB3 (03, 10)

- The straight run is at least the clear concrete length between the footing faces (SB1 4.550 m, SB3 2.838 m), as a
  LOWER_BOUND.
- The column c/c and footing c/c are recorded.
- DEVELOPMENT_INTO_FOOTING_1 / _2 stay BLOCKED_UNQUANTIFIED.

## 12. Free ends (09)

The 7 FREE_END nodes are all classified: {'FOOTING': 2, 'COLUMN': 4, 'BOUNDARY': 1}.
- **Footings:** two ends lie inside the FF footing outline.
- **Columns:** four ends touch column outlines, two of them outlines the rectangle detector did not return. Two are a
  50 mm and a 20 mm drawing gap.
- **Boundary:** the east end of 1811-1812 lies on the S-BOUN plot-boundary line.

## 13. Readiness (10) — movement from pre-S5

| Ground beams | pre-S5 | PRE-S5.1 |
|---|---|---|
| READY_LOWER_BOUND | 46 | **31** |
| BLOCKED_COMPONENT | 13 | **28** |

**Moved up to READY_LOWER_BOUND** (5): 10B-7D1-2, 137-138-1, 7D4-F8-2, 7E7-7E8-1, A-139-13A-1. The architecture verified
the exterior (or interior) wall, so the 3Ø14 / 3Ø16 candidates collapsed to one detail.

**Moved down** (20), by first blocking cause:
- BAR_RUN_LENGTH_GEOMETRY_CONFLICT: 4
- CANDIDATE_DETAILS_DISAGREE (exterior authority not verified / length basis): 4
- CONCENTRATED_LOAD_UNRESOLVED (Q-L1): 12

**All 28 blocked spans**, by first blocking cause:
- BAR_RUN_LENGTH_GEOMETRY_CONFLICT: 6
- CANDIDATE_DETAILS_DISAGREE (exterior authority not verified / length basis): 7
- CONCENTRATED_LOAD_UNRESOLVED (Q-L1): 15

**Straps:** SB1 and SB3 READY_LOWER_BOUND (unchanged). SB2 BLOCKED (bars), with its stirrup Ø, rate and count now
released as candidate-invariant.

## Files

| File | Content |
|---|---|
| 01_PROVENANCE_CONTRACT_UPDATE.md | generic identity contract, S4 compatibility, rejected footing identity |
| 02_GROUND_BEAM_ARCH_WALL_OVERLAY.csv | per span: wall handles, overlap, wall / exterior class, method, authority |
| 03_EXTERIOR_AUTHORITY_REGISTER.csv | per span: proxies, architecture, slab edge, authority, applicability before / after |
| 04_FOLLOW_ARCH_DEPTH_REGISTER.csv | exterior candidates: top / bottom levels, sources, derived bound, outcome |
| 05_LENGTH_BASIS_ANALYSIS.csv | per span: four lengths, length state, faces, detail by clear / centreline basis |
| 06_CONCENTRATED_LOAD_REGISTER.csv | per span: load state and evidence |
| 07_DETAIL_PRECEDENCE_ANALYSIS.md / 08_SB2_SOURCE_CONFLICT.md | nested conditions and 2.5 m stirrup; SB2 evidence |
| 09_GROUND_BEAM_FREE_END_REGISTER.csv | the 7 former free ends |
| 10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv | occurrence x component, MAY_RELEASE, pre-S5 status |
| 11_ENGINEERING_QUESTIONS_FINAL.md / 12_S5_GO_NO_GO.md | remaining questions; S5 scope decision |
| PRE_S5_1_SUMMARY.json, S5_1_PROVENANCE_TEMPLATES.json, INDEX.json | summary, generic templates, hashes |
