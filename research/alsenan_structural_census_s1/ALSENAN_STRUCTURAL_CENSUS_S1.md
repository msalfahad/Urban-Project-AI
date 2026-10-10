# ALSENAN STRUCTURAL CENSUS — ROUND S1 (source rules + occurrence census)

**No rebar tonnage and no kg is calculated in this round.** The plan decides occurrence; the schedule only defines.
No human, freelancer or benchmark total was read; the census was frozen before any comparison (`INDEX.json:
frozen_before_benchmark = true`, `built_twice_identical = true`).

Sources: `ST7757.dxf` (sha256 `9f9d1179…`, all plan sheets in one model space) and `ST7757.pdf` (sha256 `74da1523…`;
p.8 raster notes, pp.9–12 schedules, pp.13–16 vector details). A second DXF export (`ST77573.dxf`) gives identical counts
for every outline and tag population.

Code: `engine/source/structural_census.py` (generic, stdlib), `research/external_engine_lab/alsenan_structural_s1.py`
(ST7757 adapter), `research/alsenan_structural_census_s1/rules_s1.py` (rule transcription) and
`build_census_s1.py` (runner: `python research/alsenan_structural_census_s1/build_census_s1.py --twice`).

---

## 1. Rules (61 rules: BLOCKED_METHOD 5, CANDIDATE 16, EXACT_RULE 37, SOURCE_CONFLICT 3)

Slab thickness precedence: **LOCAL PANEL NOTE > FLOOR-SPECIFIC NOTE > PROJECT DEFAULT (160 mm)**. No slab is hard-coded.

| Rule | Page | Status | Normalised rule |
|---|---|---|---|
| P8-N01 | 8 | EXACT_RULE | administrative |
| P8-N02 | 8 | EXACT_RULE | discrepancy -> engineer (supports SOURCE_CONFLICT handling, never auto-resolve) |
| P8-N03 | 8 | EXACT_RULE | printed dimension > scaled dimension (scaled values stay PROVISIONAL) |
| P8-N04 | 8 | EXACT_RULE | openings: cross-check architectural vs structural |
| P8-N05 | 8 | EXACT_RULE | material |
| P8-N06 | 8 | EXACT_RULE | fc_RC >= 300 kg/cm2; fc_plain >= 150 kg/cm2 |
| P8-N07 | 8 | EXACT_RULE | QA |
| P8-N08 | 8 | EXACT_RULE | fy >= 4200 kg/cm2 |
| P8-N09 | 8 | EXACT_RULE | starter (dowel) development length: tension 70D, compression 40D |
| P8-N10 | 8 | EXACT_RULE | foundation bearing check |
| P8-N11 | 8 | BLOCKED_METHOD | beam width +5 cm where pipes pass (occurrences not marked on plans) |
| P8-N12 | 8 | EXACT_RULE | founding level to be confirmed |
| P8-N13 | 8 | EXACT_RULE | material |
| P8-N14 | 8 | EXACT_RULE | temporary works |
| P8-N15 | 8 | EXACT_RULE | temporary works |
| P8-N16 | 8 | EXACT_RULE | material |
| P8-N17 | 8 | SOURCE_CONFLICT | formwork >= 14 days |
| P8-N18 | 8 | EXACT_RULE | NORMAL_SUSPENDED_SLAB_THICKNESS = 160 mm; precedence LOCAL PANEL NOTE > FLOOR NOTE > PROJECT DEFAULT |
| P8-N19 | 8 | EXACT_RULE | LIFT_TIE_BEAM required where storey height > 4.30 m; at +3.00 m |
| P8-N20 | 8 | EXACT_RULE | architectural coordination |
| P8-N21 | 8 | BLOCKED_METHOD | deep-beam side bars (D > 60 cm): 2/3/4 Ø12 by width - width -> count mapping NOT printed; schedule REMARKS override |
| P8-N22 | 8 | EXACT_RULE | cover: members 25 mm; soil-contact 70 mm |
| P8-N23 | 8 | EXACT_RULE | formwork camber |
| P8-N24 | 8 | EXACT_RULE | coordination |
| P1-NOTE-A | 1 | EXACT_RULE | same as P8-N18 (second printed source) |
| P1-NOTE-B | 1 | CANDIDATE | neighbour-side external ground beams: upper + lower beam over a black-brick wall |
| P1-NOTE-C | 1 | SOURCE_CONFLICT | formwork >= 21 days |
| P4-6-NOTE-1 | 4 | EXACT_RULE | parapet geometry from the architectural drawings |
| P4-6-NOTE-2 | 4 | CANDIDATE | SLAB_TOP_OVER_BEAM = 5Ø10/m, extending L/3 (span) each side? / total? - 'بطول ثلث البحر' = length one third of the span; both directions |
| P9-SOIL | 9 | EXACT_RULE | founding depth >= 1.5 m; q_allow 2.20 kg/cm2 |
| P9-COL-TIES | 9 | EXACT_RULE | COLUMN_TIE = Ø8 @ 6/m - per-metre count applies to a tie SET (all closed ties of the topology band) or to single ties: NOT stated |
| P9-COL-L | 9 | EXACT_RULE | L = long section dimension |
| P9-COL-BAND-1 | 9 | EXACT_RULE | TIE_L_LE_50: 1 closed tie |
| P9-COL-BAND-2 | 9 | EXACT_RULE | TIE_50_LT_L_LT_80: 2 overlapping closed ties |
| P9-COL-BAND-3 | 9 | EXACT_RULE | TIE_80_LT_L_LT_120: 3 closed ties |
| P9-COL-TMIN | 9 | EXACT_RULE | T_min(H): <=4.3 -> 20; 4.3..4.7 -> 25; 4.7..5.0 -> 30 (cm) |
| P10-SBT-REMARKS | 10 | CANDIDATE | SIDE_BARS per beam row (overrides P8-N21 for that row); box-symbol meaning not printed |
| P11-12-CB-TYPICAL | 11 | CANDIDATE | CB support-top extension 0.22Ln / 0.3Ln2; stirrup start 75 mm; bottom stop 0.15L |
| P13-FOOTING-TYP | 13 | CANDIDATE | FOOTING components: bottom long, bottom short, BOXED cage (semantics of '3+4' NOT printed), starter foot >= 30 cm, starter 40D |
| P13-FOOTING-DEEP | 13 | BLOCKED_METHOD | LOWER_GROUND_BEAM required if (upper GB level - footing level) > 2.5 m |
| P13-GB-GT5 | 13 | EXACT_RULE | GB_GT_5M: 30x60, top 3Ø16, bottom 2 rows 3Ø16, links Ø8@150 |
| P13-GB-LT5 | 13 | EXACT_RULE | GB_LT_5M: 30x40, top 3Ø14, bottom 2 rows 3Ø14, links Ø8@150 |
| P13-GB-LT2_5 | 13 | CANDIDATE | GB_LT_2_5M: 30x30, 3Ø14 top + 2 x 3Ø14 |
| P13-GB-EXT | 13 | EXACT_RULE | GB_EXTERIOR: 30 x (FOLLOW ARCH), top 3Ø16, bottom 6Ø16, side 2Ø12@300, links Ø8@150 |
| P13-LINTEL | 13 | EXACT_RULE | LINTEL(type by opening width) - occurrences come from the architectural openings, not the structural plans |
| P14-LIFT | 14 | BLOCKED_METHOD | LIFT_PIT: walls 200 mm, 6Ø12/m + 6Ø16/m; depth BLOCKED (manufacturer) |
| P14-BOUNDARY | 14 | SOURCE_CONFLICT | BOUNDARY_WALL typical (conflicts with schedule row B.W 20x60 4Ø16/2Ø14) |
| P14-PARAPETS | 14 | CANDIDATE | PARAPET typical sections (applicability by architecture) |
| P15-TEMP-TABLE | 15 | EXACT_RULE | TEMP(t): exact rows only; 160 / 180 mm are NOT rows -> RULE_NOT_EXACT_MATCH (no interpolation) |
| P15-TEMP-NOTES | 15 | CANDIDATE | TEMP lap 40D; 2000 mm top strip over beams parallel to main bars (1000 spandrel); max(top) at shared supports |
| P15-SLAB-ON-BEAMS | 15 | EXACT_RULE | TOP_NONCONT=0.25L1; TOP_CONT=0.30max(L1,L2); BOT 50% stop 0.125L at continuous supports |
| P15-TWISTED | 15 | CANDIDATE | TURN_COLUMN extras: 4Ø16 + spiral 6Ø8/m over 2 x 1 m |
| P15-CASEMENT | 15 | CANDIDATE | special beam-column casement detail (occurrence not marked on plans) |
| P15-PLANTED | 15 | CANDIDATE | PLANTED_COLUMN support detail |
| P16-STAIR | 16 | BLOCKED_METHOD | STAIR typical (applicability to each plan stair NOT established) |
| P16-BEAM-OPENING | 16 | CANDIDATE | BEAM_OPENING extras (no opening marked on the plans) |
| P16-RIBS | 16 | CANDIDATE | RIBS (no ribbed slab on the plans: legend only) |
| P7-POOL | 7 | CANDIDATE | POOL detail; dimensions 'AS PER ARCH' |
| P7-DOME | 7 | CANDIDATE | DOME: shell 100 mm, Ø12@150 two layers; ring beam 3Ø16/3Ø18, 2Ø14@200 sides, 8Ø8/m |
| P3-GROUND-SLAB | 3 | CANDIDATE | GROUND_SLAB: t 100 mm, 5Ø10/m each way (extent of application not drawn) |
| P3-LEGEND | 3 | EXACT_RULE | symbol vocabulary for the census |

Source conflicts kept open (never auto-resolved): formwork 14 days (p.8 n.17) vs 21 days (p.1 note); boundary-wall
typical detail vs schedule row B.W.

### Stirrup rule — "DETAILS OF COLUMN REINFORCEMENT" (p.9), read from the DXF geometry

* General note (DXF handle 1BAA): **"ST. OF COLUMN – 6Ø8/m"**. L = length of column (long side of the section).
* Band sketches (each one checked against the closed tie polylines inside the drawn concrete outline):

| Band | Printed condition | Closed ties per level | Bars in sketch | Tie span / L (offset) |
|---|---|---|---|---|
| TIE_L_LE_50 | L ≤ 50 cm | 1 perimeter tie | 4 | 0.91 |
| TIE_50_LT_L_LT_80 | 50 < L < 80 cm | 2 overlapping ties | 8 (4 per long face) | 0.607 (0.03) + 0.607 (0.363) |
| TIE_80_LT_L_LT_120 | 80 < L < 120 cm | 2 overlapping + 1 small central | 12 (6 per long face) | 0.761 + 0.757 + 0.222 |

* Gaps: **L = 80 cm is in no band** (C7 is 30×80 / 25×80 / 20×80 → BOUNDARY_GAP, not snapped); L ≥ 120 out of range.
* Tmin table: H ≤ 4.3 m → 20 cm; 4.3–4.7 m → 25 cm; 4.7–5.0 m → 30 cm (H = height of floor).
* Population: BOUNDARY_GAP 3, TIE_50_LT_L_LT_80 13, TIE_80_LT_L_LT_120 16, TIE_L_LE_50 63.
* **Open (BLOCKED_METHOD):** whether 6/m counts tie *sets* or single ties — see questions at the end.

## 2. Levels and heights

| Level | Value | Status |
|---|---|---|
| Founding level | not printed (excavation ≥ 1.5 m below plot, p.9) | BLOCKED |
| Plot / ground beams | ±0.00 (+0.15 / +0.30 court & landings) | PRINTED |
| GF FFL | +1.00 | PRINTED |
| 1F FFL | +5.50 | PRINTED_ARCH (P7757 section A-A) |
| 2F FFL / 1F roof | +9.70 | PRINTED |
| Roof | +13.90 | PRINTED_ARCH |

Storey floor-to-floor: **GF 4.50 m, 1F 4.20 m, 2F 4.20 m**; foundation storey BLOCKED. Column clear height, main-bar length
and tie-zone length are kept as separate fields and are left BLOCKED / not in this round. Lift tie beam (p.8 n.19,
storey > 4.30 m) is **required at GF only**.

## 3. Columns — exact count by type and floor

39 physical positions (36 from the foundation + 2 planted on the GF roof + 1 planted on the 1F roof), **95 storey
occurrences**. Plan outlines: FP 36, CAP 35, GBP 36, GFRS 34, FFRS 21, SFRS 9 — every outline is in exactly one chain
(hard invariant PASS).

| Type | FOUNDATION | GF | 1F | 2F | Total |
|---|---|---|---|---|---|
| C | 5 | 5 | 0 | 0 | 10 |
| CN | 6 | 0 | 0 | 0 | 6 |
| P.C | 0 | 0 | 2 | 1 | 3 |
| C1 | 1 | 1 | 1 | 1 | 4 |
| C2 | 4 | 4 | 4 | 4 | 16 |
| C3 | 6 | 6 | 2 | 1 | 15 |
| C4 | 2 | 2 | 2 | 0 | 6 |
| C5 | 3 | 3 | 3 | 1 | 10 |
| C6 | 1 | 1 | 1 | 0 | 3 |
| C7 | 1 | 1 | 1 | 0 | 3 |
| C8 | 2 | 2 | 2 | 0 | 6 |
| C9 | 2 | 2 | 2 | 1 | 7 |
| C10 | 1 | 1 | 0 | 0 | 2 |
| C11 | 2 | 2 | 0 | 0 | 4 |
| **Total** | **36** | **30** | **20** | **9** | **95** |

Definitions: 12 schedule types (CGT rows) + CN (loose text row, foundation only: 30×30, 4Ø14) + 3 P.C from plan labels
(20×70 10Ø16; 20×50 8Ø16 ×2). C, C10, C11 have FOU and GR bands only (they stop at GF — consistent with the plans).
C4 / C6 / C7 / C8 have a 2ND band but no 2F occurrence on the plan (schedule row ≠ occurrence).

## 4. Column chains

* starts_at: FOUNDATION 36, 1F 2 (P.C on GF roof), 2F 1 (P.C on 1F roof).
* terminates_at: FOUNDATION 6 (the CN neck columns), GF 12, 1F 12, 2F 9.
* Events: GAP_IN_CHAIN 1 (CN at 29108/18112 missing on the axis plan), MISSING_ON_AXIS_PLAN 1, NO_SUPPORT_BELOW 3 (the
  P.C), TURN_ORIENTATION_CHANGE 2 (T.C at C8 31508/15062 and C9 27308/16612). D.C (dead column) bound to the chain at
  X06-Y04.
* Type conflicts (status SOURCE_CONFLICT, never resolved by the engine):
  * X12-Y02 (24308, 8912): axis plan + foundation plan say **C8**, ground-beam plan says **C7**; axis-plan size label 30X80
    and the drawn outline match **C7**.
  * X04-Y01 (7988, 7462): axis + foundation plans say **C3**, ground-beam plan says **C**.
* Drawn outline vs schedule section mismatches: 1F 11, 2F 3, FOUNDATION 6, GF 8 (e.g. lift columns drawn 20×50 / 25×100 on CAP vs 30 cm in
  the foundation band).
* GF columns below Tmin: 10 occurrences (C ×5, C2 ×4, C1 ×1) are 20 cm thick at GF where H = 4.50 m needs 25 cm.

## 5. Footings by type

26 outlines on the foundation plan (0 tag-only): CONFLICT(F/F10) ×1, F ×4, F11 ×1, F12 ×1, F13 ×1, F14 ×1, F15 ×1, F2 ×2, F3 ×2, F4 ×2, F5 ×2, F6 ×1, F8 ×1, F9 ×1, FF ×1, FN ×4.
F7 is in the schedule with **no plan occurrence**. FN (100×100) carries the CN neck columns.
Single-layer footings (FT) = ABSOLUTE_COUNT bottom bars; two-layer footings (FTB: F8, F12, F13, F14, FF) = BARS_PER_METRE
TOP + BOTTOM. BOXED values '3+4' / '3+5' / '3+6' / '3+8' → **BOXED_REQUIRED = true, BOXED_SEMANTICS = BLOCKED**.

## 6. Column–footing mismatches

* **F / F10 conflict**: one open outline at (30008, 7312), 325×140 drawn, carries tag F and tag F10 and holds C + C10 →
  type None, SOURCE_CONFLICT_COMPETING_TAGS (F10 in the schedule is 280×140).
* FN at CN (29108, 18112) overlaps F9 by 0.14 m² (FOOTING_OUTLINES_OVERLAP).
* No column without a footing; no footing without a column. Combined footings: CONFLICT_F_F10 → C+C10; F12 → C3+C7; F13 → C11+C5; F14 → C3+C8; F4 → C4+CN; F8 → C3+C8+CN; FF → C1+C2+C9.

## 7. Simple beams by type and floor (tagged spans)

| Type | GF roof | 1F roof | 2F roof | Total |
|---|---|---|---|---|
| B1 | 12 | 3 | 4 | 19 |
| B2 | 3 | 3 | 4 | 10 |
| B3 | 4 | 1 | 4 | 9 |
| B4 | 6 | 5 | 0 | 11 |
| B5 | 1 | 2 | 0 | 3 |
| B6 | 0 | 5 | 0 | 5 |
| B7 | 7 | 2 | 1 | 10 |
| B8 | 1 | 0 | 1 | 2 |
| B9 | 1 | 0 | 0 | 1 |
| B11 | 1 | 1 | 0 | 2 |
| B13 | 1 | 0 | 0 | 1 |
| B14 | 1 | 0 | 0 | 1 |
| B15 | 0 | 0 | 1 | 1 |
| B16 | 1 | 0 | 0 | 1 |
| B17 | 1 | 0 | 0 | 1 |
| B18 | 0 | 1 | 0 | 1 |
| B19 | 0 | 1 | 0 | 1 |
| B20 | 1 | 0 | 0 | 1 |
| B21 | 1 | 0 | 0 | 1 |
| B22 | 1 | 0 | 0 | 1 |
| B23 | 0 | 1 | 0 | 1 |
| B24 | 1 | 0 | 0 | 1 |
| B25 | 0 | 1 | 0 | 1 |
| B26 | 1 | 0 | 0 | 1 |
| B27 | 1 | 0 | 0 | 1 |
| B28 | 1 | 0 | 0 | 1 |
| B29 | 1 | 0 | 0 | 1 |
| CA | 1 | 0 | 0 | 1 |
| **Total** | **49** | **26** | **15** | **90** |

Ambiguous tags (tag between two parallel beams, kept COUNTED_BLOCKED): GF roof B1, B8; 1F roof B6 ×4.
Drawn width ≠ schedule B (SOURCE_CONFLICT): B21 (GF_ROOF, drawn 400 vs 45 cm); B29 (GF_ROOF, drawn 200 vs 25 cm); CB2 (GF_ROOF, drawn 250 vs 20 cm); CB2 (GF_ROOF, drawn 250 vs 20 cm); CB10 (1F_ROOF, drawn 200 vs 25 cm); CB10 (1F_ROOF, drawn 200 vs 25 cm); B6 (1F_ROOF, drawn 200 vs 25 cm).
Schedule rows with no plan occurrence: B10, B12, B.W.

## 8. Continuous beams by type and floor

| Type | GF roof | 1F roof | Spans (tags) |
|---|---|---|---|
| CB1 | 1 | 0 | 2 — MATCH_CONFIRMED |
| CB2 | 1 | 0 | 2 — MATCH_CONFIRMED |
| CB3 | 1 | 0 | 3 — MATCH_CONFIRMED |
| CB4 | 1 | 0 | 2 — SPAN_LENGTH_CONFLICT |
| CB5 | 2 | 0 | 2 — SPAN_COUNT_CONFLICT |
| CB6 | 1 | 0 | 2 — MATCH_CONFIRMED |
| CB7 | 1 | 0 | 2 — MATCH_CONFIRMED |
| CB8 | 1 | 0 | 2 — SPAN_COUNT_CONFLICT |
| CB9 | 0 | 1 | 3 — MATCH_CONFIRMED |
| CB10 | 0 | 1 | 2 — MATCH_CONFIRMED |
| CB11 | 0 | 1 | 3 — MATCH_CONFIRMED |
| CB12 | 0 | 1 | 2 — MATCH_CONFIRMED |
| CB13 | 0 | 1 | 2 — MATCH_CONFIRMED |
| **Groups** | 9 | 5 | 14 groups, 13 types |

Never forced: CB4 SPAN_LENGTH_CONFLICT (2.724 m from a free end vs 3.30 m), CB5 two single-span groups on different lines
(SPAN_COUNT_CONFLICT), CB8 SPAN_COUNT_CONFLICT (matches only if the adjacent untagged 3.825 m span is added — recorded as
an extension check, not applied).

## 9. Strap / ground / exterior / lintel / other beams

* Straps (FP): SB1 700 mm × 7.35 m (70×50 ✓), SB3 502 mm × 4.70 m (50×40 ✓), **SB2 987 mm × 5.11 m — schedule key
  duplicated (100×50 vs 80×50), SOURCE_CONFLICT** (drawn width favours 100).
* Ground beams (GBP): **62 spans**, all 300 mm wide: EXTERIOR_GB GB_GT_5M 4; EXTERIOR_GB GB_LT_2_5M 4; EXTERIOR_GB GB_LT_5M 12; GB GB_GT_5M 4; GB GB_LT_2_5M 11; GB GB_LT_5M 25; GB curved 2. 9 spans change category between c/c and clear length
  (AMBIGUOUS_LENGTH_BASIS); 2 curved spans (pool curve) BLOCKED_CURVED_SPAN; 5 spans outside the GF footprint.
* Exterior GB: 20 candidates by geometry (600 mm probe beyond the face outside the GF roof footprint).
* Lintels: population BLOCKED — occurrences come from the architectural openings (P13-LINTEL).
* Lift tie beam: required at GF by p.8 n.19, **not drawn** → BLOCKED.
* Stair beams: "B3 (With Stair)" ×3 (GF roof ×2, 1F roof ×1); one shares its span with CB3 (SOURCE_CONFLICT).
* Cantilever CA ×1 (GF roof). Untagged members: GF roof 5, 1F roof 13 (+6 dome ring arcs), 2F roof 1.

## 10–12. Slab panels per floor, thickness of each panel, annotations per panel

| Slab | Slab panels | Stair | Stair in void | Dome zones | Open to below | Outside / court |
|---|---|---|---|---|---|---|
| 1F_ROOF_SLAB | 14 | 1 | 0 | 8 | 1 | 1 |
| 2F_ROOF_SLAB | 7 | 0 | 0 | 0 | 0 | 2 |
| GF_ROOF_SLAB | 28 | 2 | 1 | 0 | 2 | 1 |
| GROUND_SLAB_SOG | 21 | 1 | 0 | 0 | 0 | 1 |

Thickness: GF roof 26 panels at default 160 + 4 faces with local **T 16**; 1F roof 13 default 160 + 2 local T 16;
**2F roof 2 panels with local T 18** (water tank: 2F-01, 2F-02) + 5 default 160; dome zones 100 (P7-DOME, CANDIDATE);
ground slab cells 100 mm from the GBP note "5Ø10/m E.W. T=10cm" (floor-specific, extent CANDIDATE).
Temperature table: 160 / 180 mm are **not rows** of the p.15 table → RULE_NOT_EXACT_MATCH on all 49 panels (no
interpolation).

| Panel | Class | Lx × Ly (m) | Area m² | t (mm) | Authority | Bar texts |
|---|---|---|---|---|---|---|
| SP-GF_ROOF_SLAB-02 | SLAB_PANEL | 0.62 × 1.7 | 1.053 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10 Y |
| SP-GF_ROOF_SLAB-03 | STAIR_FLIGHT_ZONE | 2.5 × 4.3 | 10.415 | 160 | LOCAL_PANEL_NOTE | 8Ø16/m X; 8Ø16/m Y; 8Ø16/m Y |
| SP-GF_ROOF_SLAB-04 | SLAB_PANEL | 1.47 × 1.75 | 2.572 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-GF_ROOF_SLAB-05 | SLAB_PANEL | 1.75 × 1.9 | 3.325 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-06 | SLAB_PANEL | 1.65 × 1.75 | 2.888 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-07 | SLAB_PANEL | 1.8 × 2.95 | 5.31 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-GF_ROOF_SLAB-08 | SLAB_PANEL | 3.5 × 3.52 | 12.32 | 160 | PROJECT_DEFAULT | 6Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-10 | SLAB_PANEL | 2.604 × 3.75 | 8.304 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 6Ø10/m Y |
| SP-GF_ROOF_SLAB-11 | SLAB_PANEL | 1.47 × 2.945 | 4.079 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-GF_ROOF_SLAB-12 | SLAB_PANEL | 1.98 × 2.2 | 4.118 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-14 | SLAB_PANEL | 1.58 × 1.98 | 2.817 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-GF_ROOF_SLAB-15 | SLAB_PANEL | 1.13 × 1.15 | 1.299 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10 X |
| SP-GF_ROOF_SLAB-16 | SLAB_PANEL | 1.75 × 3.3 | 5.375 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-17 | SLAB_PANEL | 3.3 × 4.171 | 11.7 | 160 | LOCAL_PANEL_NOTE | 6Ø10/m X; 7Ø12/m Y |
| SP-GF_ROOF_SLAB-18 | SLAB_PANEL | 2.37 × 2.548 | 5.544 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-GF_ROOF_SLAB-19 | SLAB_PANEL | 1.6 × 4.0 | 6.139 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 6Ø10/m Y |
| SP-GF_ROOF_SLAB-20 | SLAB_PANEL | 3.7 × 4.2 | 15.54 | 160 | PROJECT_DEFAULT | 6Ø10/m X; 7Ø10/m Y |
| SP-GF_ROOF_SLAB-21 | STAIR_IN_VOID_ZONE | 3.95 × 5.82 | 20.146 | — | BLOCKED | 8Ø16/m DIAGONAL_134 |
| SP-GF_ROOF_SLAB-22 | SLAB_PANEL | 3.411 × 5.15 | 15.108 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y; 6Ø14/m X |
| SP-GF_ROOF_SLAB-23 | SLAB_PANEL | 1.145 × 7.5 | 7.851 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 6Ø10/m X |
| SP-GF_ROOF_SLAB-24 | SLAB_PANEL | 1.41 × 2.951 | 2.08 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-GF_ROOF_SLAB-25 | SLAB_PANEL | 3.3 × 4.95 | 16.254 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y |
| SP-GF_ROOF_SLAB-26 | SLAB_PANEL | 4.0 × 4.5 | 18.0 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y |
| SP-GF_ROOF_SLAB-27 | SLAB_PANEL | 3.0 × 4.5 | 13.485 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y |
| SP-GF_ROOF_SLAB-28 | STAIR_FLIGHT_ZONE | 3.25 × 3.95 | 6.979 | 160 | LOCAL_PANEL_NOTE | 8Ø16/m X; 8Ø16/m Y |
| SP-GF_ROOF_SLAB-29 | SLAB_PANEL | 3.0 × 3.543 | 7.301 | 160 | LOCAL_PANEL_NOTE | 6Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-30 | SLAB_PANEL | 1.3 × 4.576 | 5.08 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-31 | SLAB_PANEL | 1.2 × 2.891 | 2.937 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-32 | SLAB_PANEL | 1.2 × 6.47 | 7.764 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-33 | SLAB_PANEL | 1.2 × 3.589 | 4.288 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-GF_ROOF_SLAB-34 | SLAB_PANEL | 3.0 × 4.5 | 13.455 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y |
| SP-1F_ROOF_SLAB-01 | STAIR_FLIGHT_ZONE | 2.5 × 4.3 | 10.415 | 160 | LOCAL_PANEL_NOTE | 8Ø16/m X; 8Ø16/m Y; 8Ø16/m Y |
| SP-1F_ROOF_SLAB-02 | SLAB_PANEL | 1.8 × 3.0 | 5.4 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-1F_ROOF_SLAB-03 | SLAB_PANEL | 2.22 × 4.415 | 9.503 | 160 | PROJECT_DEFAULT | 6Ø10/m X; 5Ø10/m Y |
| SP-1F_ROOF_SLAB-04 | SLAB_PANEL | 3.0 × 4.797 | 13.804 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y |
| SP-1F_ROOF_SLAB-05 | SLAB_PANEL | 4.1 × 4.325 | 17.705 | 160 | PROJECT_DEFAULT | 7Ø10/m X; 6Ø10/m Y |
| SP-1F_ROOF_SLAB-07 | SLAB_PANEL | 1.01 × 4.372 | 4.414 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-1F_ROOF_SLAB-08 | SLAB_PANEL | 0.785 × 4.1 | 3.22 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10 Y |
| SP-1F_ROOF_SLAB-09 | SLAB_PANEL | 1.598 × 1.825 | 2.762 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-1F_ROOF_SLAB-11 | SLAB_PANEL | 1.7 × 4.3 | 6.455 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 6Ø10/m Y |
| SP-1F_ROOF_SLAB-12 | SLAB_PANEL | 1.607 × 2.95 | 4.215 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-1F_ROOF_SLAB-21 | SLAB_PANEL | 4.3 × 4.85 | 20.855 | 160 | LOCAL_PANEL_NOTE | 8Ø10/m X; 7Ø10/m Y; 3Ø14 DIAGONAL_135; 3Ø14 DIAGONAL_45; 3Ø14 DIAGONAL_45; 3Ø14 DIAGONAL_135 |
| SP-1F_ROOF_SLAB-22 | SLAB_PANEL | 2.274 × 4.85 | 11.028 | 160 | PROJECT_DEFAULT | 6Ø10/m X; 5Ø10/m Y |
| SP-1F_ROOF_SLAB-23 | SLAB_PANEL | 2.274 × 4.85 | 11.028 | 160 | PROJECT_DEFAULT | 6Ø10/m X; 5Ø10/m Y |
| SP-1F_ROOF_SLAB-24 | SLAB_PANEL | 1.042 × 4.372 | 4.557 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-1F_ROOF_SLAB-25 | SLAB_PANEL | 1.142 × 4.1 | 4.684 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-2F_ROOF_SLAB-01 | SLAB_PANEL | 2.5 × 3.3 | 8.235 | 180 | LOCAL_PANEL_NOTE | 7Ø14/m X T&B; 6Ø14/m Y T&B |
| SP-2F_ROOF_SLAB-02 | SLAB_PANEL | 1.8 × 3.0 | 5.4 | 180 | LOCAL_PANEL_NOTE | 6Ø12/m Y T&B; 6Ø12/m X T&B |
| SP-2F_ROOF_SLAB-03 | SLAB_PANEL | 1.8 × 1.8 | 3.24 | 160 | PROJECT_DEFAULT | 5Ø10/m Y; 5Ø10/m X |
| SP-2F_ROOF_SLAB-04 | SLAB_PANEL | 3.0 × 5.0 | 15.0 | 160 | PROJECT_DEFAULT | 5Ø18/Top Y; 7Ø10/m X; 6Ø10/m Y |
| SP-2F_ROOF_SLAB-06 | SLAB_PANEL | 2.5 × 2.9 | 7.25 | 160 | PROJECT_DEFAULT | 6Ø10/m X; 5Ø10/m Y |
| SP-2F_ROOF_SLAB-07 | SLAB_PANEL | 1.2 × 1.8 | 2.16 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |
| SP-2F_ROOF_SLAB-08 | SLAB_PANEL | 1.2 × 3.0 | 3.6 | 160 | PROJECT_DEFAULT | 5Ø10/m X; 5Ø10/m Y |

Other slab bar texts: section-detail texts 6, plan-note 5Ø10/m ×3 (one per roof), P.C bar texts 3, support top bars 2
(3Ø16/Top GF roof on BL004, 4Ø16/Top 2F roof). T&B preserved: 4 texts (2F-01 7Ø14/m + 6Ø14/m, 2F-02 6Ø12/m ×2).
Corner bars 3Ø14 ×4 on 1F-21. Every SLAB-owned text is bound to a panel (0 unbound).

## 13. Special populations

| Kind | Count | Terminal states |
|---|---|---|
| TURN_COLUMN | 2 | COUNTED_DEFINITION_PARTIAL 2 |
| DEAD_COLUMN | 1 | COUNTED_DEFINITION_PARTIAL 1 |
| PLANTED_COLUMN | 3 | COUNTED_DEFINITION_PARTIAL 3 |
| STAIR_FLIGHT | 5 | COUNTED_BLOCKED 5 |
| STAIR_BEAM | 3 | COUNTED_AND_DEFINED 3 |
| LIFT_PIT | 1 | COUNTED_BLOCKED 1 |
| LIFT_TIE_BEAM | 1 | COUNTED_BLOCKED 1 |
| LINTEL_POPULATION | 1 | COUNTED_BLOCKED 1 |
| BOUNDARY_WALL | 1 | COUNTED_BLOCKED 1 |
| PARAPET | 3 | COUNTED_BLOCKED 3 |
| WATER_TANK_SLAB | 1 | COUNTED_AND_DEFINED 1 |
| DOME | 2 | COUNTED_DEFINITION_PARTIAL 2 |
| SWIMMING_POOL | 1 | COUNTED_DEFINITION_PARTIAL 1 |
| GROUND_SLAB | 1 | COUNTED_DEFINITION_PARTIAL 1 |
| SLAB_CORNER_BARS | 1 | COUNTED_AND_DEFINED 1 |
| BEAM_OPENING | 1 | NOT_IN_SCOPE 1 |
| CASEMENT_DETAIL | 1 | NOT_IN_SCOPE 1 |
| RIBBED_SLAB | 1 | NOT_IN_SCOPE 1 |
| SECTION_DETAIL_CALLOUT | 4 | NOT_IN_SCOPE 4 |

## 14. Pool

Occurrence: GBP label "swimming pool" + 2 curved ground beams; geometry "AS PER ARCH" (BLOCKED). p.7 detail (N.I.S = not to
scale): walls 20 cm, deep base 40 cm. Components and bar texts (component mapping read from the p.7 render, CANDIDATE):

| Component | Bars |
|---|---|
| CORNER_DETAIL_SLOPE | base top bar: 7Ø14/m; base bottom bar: 7Ø14/m |
| CORNER_DETAIL_DEEP | wall vertical l bar: 7Ø14/m; base l bar: 7Ø14/m |
| DEEP_END_BASE | corner bars: 3Ø16; bottom bars: 7Ø14/m; top bars: 7Ø14/m; bottom bars (second label): 7Ø14/m |
| DEEP_WALL | horizontal outer face: Ø12/20cm; vertical outer face: 7Ø14/m; top coping bars: 3Ø16; horizontal inner face: Ø12/20cm; vertical inner face: 7Ø12/m |
| SLOPED_BASE | bottom bars: 6Ø14/m; top bars: 6Ø12/m |
| CORNER_DETAIL_SLOPE_SHALLOW | bottom bar: 6Ø12/m; top bar: 6Ø12/m |
| CORNER_DETAIL_SHALLOW | base bar: 6Ø12/m; wall vertical l bar: 6Ø12/m |
| SHALLOW_BASE | bottom bars: 6Ø12/m; bottom bars (second label): 6Ø12/m; top bars: 6Ø12/m |
| SHALLOW_WALL | horizontal inner face: Ø10/20cm; horizontal outer face: Ø10/20cm; vertical bars: 6Ø12/m |
| SHALLOW_END_BASE | corner bars: 4Ø16 |

Pump room: not drawn. Non-structural build-up (5 cm screed, 5 cm insulation, 10 cm plain concrete) recorded, not counted.

## 15. Objects accounted (conservation)

**950 source objects, 950 register rows, 0 silent disappearances, 0 double counts.**
By state: COUNTED_AND_DEFINED 683, COUNTED_BLOCKED 49, COUNTED_DEFINITION_PARTIAL 184, NOT_IN_SCOPE 34.

## 16. Blocked / unresolved

* Conservation ledger: COUNTED_BLOCKED 49, COUNTED_DEFINITION_PARTIAL 184 (of 950).
* Rules: BLOCKED_METHOD 5, SOURCE_CONFLICT 3, CANDIDATE 16.
* Beams COUNTED_BLOCKED: 27 (ambiguous tags 6, untagged 19, lift tie 1, lintel population 1).
* Columns: 5 occurrences SOURCE_CONFLICT (two tag-conflict chains); 3 BOUNDARY_GAP tie bands (C7).
* Footings: 1 SOURCE_CONFLICT (F/F10); BOXED semantics BLOCKED on 11 single-layer types.
* Slabs: stair zones 4 + stair-in-void 1 + GBP stair 1 BLOCKED (P16-STAIR); temperature steel RULE_NOT_EXACT_MATCH on all 49 suspended panels.
* Levels: founding level, column clear height, main-bar length, tie-zone length BLOCKED / not in this round.

## 17. Top review questions

1. **COLUMN_TIES — 6Ø8/m semantics**: 6Ø8/m: is the count per metre a count of tie SETS (all closed ties of the band at one level) or of single closed ties?
2. **COLUMN_TIES — L = 80 cm boundary**: L = 80 cm (C7 30x80) sits on the printed limit of both bands (50<L<80, 80<L<120): band 2 (2 ties) or band 3 (3 ties)?
3. **COLUMNS — GF columns below Tmin**: GF storey is 4.50 m -> Tmin 25 cm (p.9); these columns are 20 cm in the schedule. Accept the schedule (engineer's design) or flag to the engineer?
4. **COLUMNS — tag conflict COLPOS-X04-Y01-7988-7462**: Which tag is right for this column position?
5. **COLUMNS — tag conflict COLPOS-X12-Y02-24308-8912**: Which tag is right for this column position?
6. **COLUMNS — drawn section vs schedule**: Plan outline size differs from the schedule band for these occurrences (e.g. lift columns 20X50 / 25X100 on the axis plan vs 30 cm in the schedule). Schedule governs?
7. **FOOTINGS — FTG-CONFLICT_F_F10-30008-7312**: One outline carries tags F and F10 (and holds C + C10). Which footing is it, or is it two footings drawn as one outline?
8. **FOOTINGS — BOXED '3+4'**: What does the BOXED value '3+4' (single-layer footings) mean - box/cage bars (3 one way + 4 the other) or starters?
9. **STRAPS — SB2**: SB2 appears twice in the schedule (100x50 and 80x50). Drawn width on FP is ~987 mm (favours 100). Which row governs?
10. **CONTINUOUS_BEAMS — CBO-GFRS-CB4-BL016**: Schedule spans vs plan spans disagree - which plan members form this CB?
11. **CONTINUOUS_BEAMS — CBO-GFRS-CB5-BL008**: Schedule spans vs plan spans disagree - which plan members form this CB?
12. **CONTINUOUS_BEAMS — CBO-GFRS-CB5-BL017**: Schedule spans vs plan spans disagree - which plan members form this CB?
13. **CONTINUOUS_BEAMS — CBO-GFRS-CB8-BL024**: Schedule spans vs plan spans disagree - which plan members form this CB?
14. **BEAMS — ambiguous beam tags**: These tags sit between two parallel beams at similar distance. Which beam does each tag name?
15. **BEAMS — B3 (With Stair) vs CB3**: One span carries both 'B3 (With Stair)' and 'CB3'. Is B3 a separate stair beam beside CB3, or the same member?

## 18. Tests

`tests/alsenan_structural_census/test_census_s1.py` — 27 tests covering every §24 item (same coordinate across floors,
type change, disappearing column, schedule row creates no occurrence, duplicate tag, footing–column mismatch, same beam
type with different lengths, beam schedule creates no occurrence, CB mismatch stays blocked, 160 overridden by a local
note, annotation binds to a panel, T&B preserved, special population cannot disappear) + tie-band boundary, register
hashes, conservation, rebuild = frozen registers, no-kg check, benchmark firewall, Round 3/4 rebar registers untouched.
Full-suite result: see `TEST_RUN.md`.

## What worked / what is not working / recommendation

**Worked**
* One model space, seven sheet frames → every plan sheet in a common local frame; vertical chains follow each column
  position plan by plan with a hard invariant (every outline in exactly one chain).
* The stirrup detail is real geometry in the DXF: tie counts and tie spans per band are read, not guessed.
* Legacy Arabic plan notes decoded deterministically; slab thickness marks bind to faces; every slab bar text has an owner.
* A test caught a real defect during the build (two off-grid CN columns shared one id); fixed and now guarded.

**Not working / still open**
* Tie semantics (6/m per set or per tie), the L = 80 boundary and the tie zone length are owner/engineer questions.
* Beam membership is only as good as the tag position: 6 tags remain ambiguous, 19 members carry no tag, 4 CB groups
  disagree with the schedule.
* Founding level and floor build-ups are not printed → no column lengths can be stated yet.
* Pool, stairs, lift pit, parapets and boundary wall have definitions but no closed geometry in the structural set.

**Recommend next (S2, after Mohammad / ChatGPT verify this census)**
1. Answer the review queue (ties first), then freeze the answers as owner facts.
2. Member geometry round: beam depths at each column face → column clear heights; founding level → foundation-storey
   length; GB category basis.
3. Only then the rebar round, consuming these registers unchanged (definitions × occurrences × rules).
