# T-263 Liquid waterproofing of buried concrete as a BOQ scope (Alsenan; rule for every villa)

Worker 2 (lane A), 2026-10-24, run unknown. Research ledger + unwired rules module (BURIED_WP_V1, stdlib), NOT wired
into any method version: released ARCH_TAKEOFF_V2.9 + route G and the V3.0.x candidate are unchanged; nothing released.
Drawings named by Drive folder and title; members by DXF handle / run id; values only (no coordinates, no client data).
ERS applied: s.2 steps 1-4 (physical element first, evidence hierarchy, first principles, reconciliation in units),
s.3 (installed vs procurement; build before deduct; a note of one detail not carried to another element), s.4 (rule +
test), s.7 (lesson row).

Files: `buried_wp_v1.py` (rules), `t263_alsenan_check.py` (runner, merged values-only inputs only),
`LEDGER_T263.csv` (one row per face), `summary.json`; tests `tests/t263_buried_wp` (villa Q by hand + adverse +
Alsenan pinned). Repeat: `python3 -I research/agents_t263/t263_alsenan_check.py [--write]`.

## 0. Gap re-checked on the current candidate (lesson 2026-10-24, T-255)

Working head 969e0ae5: the only WP item codes in engine/source are the wet-area / roof / balcony family
(FIN.WP.*); T-219 (MERGED de7c1c4c) proposed WP.FOOTING_MEMBRANE / SCREED.FOOTING_PROTECTION / WP.FOOTING_SIDES /
WP.LIFT_PIT_* (integration T-270 QUEUED). No code, line or freelancer row carries a liquid coat on a ground beam, a
neck or a footing top. The gap stands: drawn scope, no BOQ line in any state.

## 1. Sources read this run (private copies in .work/private only, never committed)

| Source (Drive "Alsenan chalet project") | Read for |
|---|---|
| ST7757.pdf (sha 74da1523, 2,219,156 bytes) p.13 at 110 / 300 dpi | both 'TYP. DETAIL OF ISOLATED FOOTING': where the 'Two layers liquid water proofing to be applied to all surface in contact with earth' leader points, what each member stands on; the four 'Ground Beams' sections (each on 10 cm plain concrete) |
| ST7757.pdf p.14 at 110 dpi | lift detail (sheet membrane + protection board, no liquid note); 'TYPICAL BOUNDARY WALL' plan + A-A (no coating drawn or noted); 'Slab on grade.' (no underlay drawn) |
| ST7757.pdf p.8 (recommendations, Arabic) and p.9 (foundation notes, schedules) at 80 dpi | no other waterproofing / bitumen note: note 13 (sulphate-resisting cement for concrete in contact with soil and ground water), note 22 (cover 7 cm against soil) are material / cover, not a coating |
| Merged ledgers (values only) | T-242 9455a63d (61 runs, face-to-face L, panels on each side), T-253 dff9cb79 (natural ground +-0.00, main exterior D 0.95, boundary band 44.07 m), T-233 2ecb5bf0 (26 outlines), T-205 5f40dfdb (36 necks), T-219 de7c1c4c (underlay / sides / lift: owned there) |
| tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json | his waterproofing rows: 'عازل حمام+مطابخ' (wet areas) and 'عازل سطح' (roofs) only |

## 2. The physical element (ERS s.2.1)

**What the drawing prints.** Both p.13 isolated-footing details carry the same note. Right detail (single ground
beam, level difference < 2.5 m): the leader ends on the footing TOP beside the neck; the ground beam above rests on
"COMPACTED SOIL" over "Well graded clean compacted fill from excavation material". Left detail (> 2.5 m, two ground
beams): the leader ends on the NECK face between the two beams; the sheet "Insulation membrane" wraps the footing
sides and runs under the lower beam. No layer line is drawn for the liquid coat: the scope is the note's text, "all
surface in contact with earth", applied to the members of that detail (footing, neck, ground beam).

**What the note means physically.** A liquid coat is applied to a concrete face after the formwork is struck and
before backfill. So a face is in scope when it is a formed face with earth (natural ground or the printed compacted
fill) against it in the finished work, and only over that height. Member by member:

| Member / face | Earth against it? | Evidence | Result |
|---|---|---|---|
| Footing top outside the neck(s) | yes (backfill) | p.13 right leader ends on it | outline - neck footprints; line follows the detail selection (left detail: a lower beam, not drawn on plan, covers part) |
| Footing sides | yes | p.13 both details | OWNED by T-219 WP.FOOTING_SIDES (liquid 80.04 vs sheet 93.03 m2, HELD): not counted here |
| Footing soffit | no (on screed / membrane / blinding) | p.13 chain 5 / 2 / 10 | OWNED by T-219 underlay: refused here |
| Neck sides | yes | p.13 left leader; right detail fill around it | perimeter x neck height; height HELD (Q-21 C, T-205) |
| Ground-beam side facing a slab panel | yes, up to the slab underside | p.13 right detail: fill under the 'T=10cm' slab on grade (T-206) | L x (D - 0.10) |
| Ground-beam outside face | only below natural ground | T-253 R-GB-DATUM-1: outer ground = natural +-0.00; the +0.15 courts are paving | L x max(0, 0.00 - soffit) |
| Ground-beam soffit | no | all four p.13 'Ground Beams' sections draw 10 cm plain concrete under the beam; a soffit cast on blinding cannot be coated | EXCLUDED (named, 55.002 m2 of soffit shown, never summed) |
| Ground-beam top | no (floor build-up) | - | excluded |
| Ground slab soffit | fill, but cast on it | 'Slab on grade.' (p.14) draws no underlay | EXCLUDED: not coatable; no damp-proof sheet printed (designer item) |
| Boundary-wall upper G.B 20 x 40 | yes, both faces 0.40 (top at N.G.) | p.14 A-A prints no coating, no note | HELD: note scope (the p.13 note is not carried to another detail's element, ERS s.3); gross 35.256 m2 |
| Boundary lower G.B + base | yes | depth 'as per excavation' | HELD: note scope + depth not printed |
| Straps SB1-SB3 | yes | not drawn in the p.13 detail; level not printed (T-230) | HELD |
| Lift-pit walls / lift columns / FF top | yes | p.14: sheet membrane + protection board, no liquid note | OWNED by T-219 WP.LIFT_PIT (each face once) |
| Procurement (coats, litres, kg) | - | product, coats, coverage not printed | HELD (UP-WP-MAT-001 BY_SPEC) |

OWNER MANUAL METHOD vs DRAWING-DERIVED METHOD (ERS s.2.2): the owner's membrane method (1 x 10 m roll, 0.10 lap, 0.20
upturn, Q-30 / Q-24 / Q-40) is written for wet areas and roofs; no owner rule covers buried concrete (family B8-08).
Only the drawing-derived method applies; the 0.20 upturn is not extended to buried faces (UP-WP-003 scope).

## 3. Ledger (LEDGER_T263.csv: 59 runs x 2 faces + soffits, 2 arcs, 26 footing tops, 36 necks, 6 named rows)

**Ground beams (buried side faces):**

| Component | Faces | Hand calculation | m2 | Status |
|---|---|---|---|---|
| Interior, single-title runs (T-242 VERIFIED component): 109+7CB#1, 17C+7E3#1, 7DC+7DD#2, 7E7+7E8#1, 7E9+7EA#1 | 10 | 2 x (0.40 - 0.10) x (4.400 + 3.228 + 3.525 + 3.525 + 4.225 = 18.903) | **11.3418** | DRAWING-CONFIRMED |
| Main exterior, face on a slab panel on fill: 107+7CE#1, 10A+7C9#1, 114+115+7DF#2, 145+7CA#1, 170+7C3#2/#3/#4, 7D0+FC#1/#4, 7E0+FD#1/#2 | 11 | (0.95 - 0.10) x (0.3639 + 4.30 + 1.00 + 1.90 + 3.37 + 3.35 + 3.25 + 2.975 + 1.20 + 3.35 + 3.25 = 28.3089) | **24.0626** | DRAWING-CONFIRMED |
| Main exterior, outside face (soffit +-0.00 = natural ground) | 14 | buried height 0: a plinth face above ground (0.95 m high) | not a quantity | EXCLUDED (above natural ground) |
| Main exterior faces on GS-08 (two slab levels), GS-12 / GS-16 (open or floored not printed): 109+7CB#2 (both), 109+7CB#3, 170+7C3#1, 7D0+FC#2/#3, 145+7CA#1 (outer) | 7 | - | HELD | PANEL_SPLIT_LEVEL / PANEL_HELD |
| Interior runs held on depth (D-33 / D-34 / T-217) or on GS-12 / GS-08 | 54 | candidates L x (title D - 0.10), shown, never summed | HELD | DEPTH_HELD / PANEL_HELD |
| Annex exterior (CONFLICT) 16, court runs 6 | 22 | - | HELD | DEPTH_HELD |
| Ring ARC:157+158, arc ARC:139+13A | 2 | ring building-side face 0.85 x 6.4681 (convex) or 0.85 x 5.7069 (concave) = 5.4979 / 4.8508 | HELD | ARC_SIDE_NOT_TRACED / annex CONFLICT |
| **Ground-beam faces measured** | **21** | | **35.4044** | DRAWING-CONFIRMED |

**Footing tops outside the necks** (each outline once; FF 1B2B owned by T-219's lift line):

| Reading | Outlines | Hand calculation | m2 | Status |
|---|---|---|---|---|
| SINGLE (one ground beam; the top fully backfilled) | 23 | 109.85 (T-219 membrane outlines) - 12.54 (F14 1B1A, below) - neck footprints 4.71 = | **92.60** | HELD: DETAIL_NOT_SELECTED |
| F14 1B1A, C3 + C8 (C8 section CONFLICT 0.24 / 0.27, T-217) | 1 | 12.54 - 0.15 - (0.24 .. 0.27) | 12.12 .. 12.15 | HELD |
| DOUBLE (two ground beams) | 24 | lower beam on the top is not drawn on plan | no value | HELD |
| 1B1B (F + F10, one outline, two tags) | 1 | - | no value | HELD (Q-31 C) |

Neck footprints deducted (T-205 sections, printed = drawn unless noted): C11 x 2 0.66, C2 x 2 0.30, C3 x 6 0.90, C4 x 2
0.30, C5 x 3 0.54, C6 0.21, C7 0.24, C8 10D0 0.27, C9 10DA 0.30, C x 4 0.60, CN x 6 0.54 (the three CN that T-205 left
unlinked go one to one onto the three FN outlines 10F0 / 10F8 / 1100; each FN carries one CN 0.30 x 0.30, so the
deduction does not depend on the pairing) = 5.10 .. 5.13 with C8 10E0. The SINGLE reading is the drawn system unless
the formation lies below about -1.67 (T-206); it is shown, never released while the formation is HELD (Q-21 C).

**Necks**: 32 necks HELD on the height (formation / ground-beam levels not printed, T-205 / Q-21 C): perimeter
**55.6 .. 55.8 m2 per metre of neck height** (C8 10E0 2.2 .. 2.4 m). 4 lift necks (C1 1099, C2 1096 / 1093, C9 1090 on FF)
EXCLUDED: inside the p.14 lift system (T-219).

## 4. Engine vs freelancer (units first)

| Item | Drawing (this task) | Released A (V2.9 + G) | Candidate V3.0.13 | Freelancer | Difference and cause |
|---|---|---|---|---|---|
| Ground-beam buried faces | 35.404 m2 DRAWING-CONFIRMED + 85 faces HELD (incl. 2 arcs) | no line | no line | no row | engine and freelancer silent on a drawn scope: -35.404 m2 each (missing category) |
| Footing tops outside necks | HELD: 104.72 .. 104.75 m2 (SINGLE) + 1B1B | no line | no line | no row | same, held by detail selection (formation) |
| Necks | HELD: 55.6 .. 55.8 m2 per m of height | no line | no line | no row | same, held by neck height |
| Boundary G.B faces | HELD (note scope): 35.256 m2 gross | no line | no line | no row | designer item |

His waterproofing is wet areas and roofs only (T-219 searched all 6 workbooks; re-checked this run: rows 'عازل حمام+مطابخ',
'عازل سطح' and their upturn rows). Verdict proposals: ground-beam faces **DRAWING scope missing in BOTH;
FREELANCER_WRONG on scope (omission)**, engine silent omission to be integrated (lane I); footing tops and necks
UNRESOLVED (formation, Q-21 C); boundary / straps UNRESOLVED (note scope, designer); procurement UNRESOLVED (product
not printed).

## 5. Findings beyond the line

- **Plinth faces (cross-trade, lane A facade / plaster):** the 14 main-house exterior ground-beam outside faces stand
  0.95 m above natural ground (soffit +-0.00, top +0.95, T-253): they are exposed plinth faces, not buried. Their
  finish (exterior plaster / Sigma down to the ground or to the court paving) belongs to the facade line; register
  L-N10-02 already names "the plinth below the lowest F.F.L.". Not measured here.
- **Faces against the court paving** (+0.00 .. +0.15, plain concrete on natural ground, T-253 reading 4-5): not earth;
  no coat.

Designer / consultant items proposed (no owner question: ERS 2.7 not met; the drawings leave these to the designer):
(1) liquid product, number of coats, coverage (procurement); (2) does the p.13 note apply to the boundary-wall beams and
the straps (their own details print nothing)?; (3) any damp-proof sheet under the slab on grade?; existing: formation
(Q-21 C) for the footing tops and necks, GS-12 / GS-16 (T-242 architect items), D-33 / D-34 / D-35 annex depths.

## 6. Rule, test, lessons row

Rule proposed (every villa; provenance T-263 from ST p.13 / p.14 of this set; a new rule version when adopted,
R-WP-BURIED-1): a coat printed for "surfaces in contact with earth" is measured face by face on the members of the detail
that prints it: a face is in scope only where a formed concrete face has earth (natural ground or printed fill) against
it in the finished work, over that height (beside a slab on fill: D - slab thickness; outside: natural ground - soffit,
0 at or above it); soffits cast on blinding / underlay and tops under the floor are named exclusions; faces another
line owns (footing underlay and sides, lift sheet system) are never counted twice; a member of another detail that
prints no coating is HELD on the note's scope, never assumed; a face whose depth, datum or panel is held is HELD with its
candidates; procurement only with a printed product and coverage.
Tests: tests/t263_buried_wp (villa Q by hand: interior 2.40, exterior with the soffit at ground 3.85 + excluded plinth
face, exterior with the soffit 0.20 below ground 4.50, footing tops 3.02 / 1.26, neck 1.98; adverse: coat above the
printed ground / slab underside refused, underlay or footing side counted as a coat refused, neck coat on a held height
never released and never 0, held depth / panel / datum stay HELD with candidates only, mm / cm as m refused, three faces
refused, slab thicker than the beam refused, neck footprints larger than the footing refused, neck section conflict
holds the top, two-tag outline HELD, face order invariant; Alsenan ledger pinned to the committed CSV / summary).

Lessons row proposed: 2026-10-24 | 'All surface in contact with earth' (ST p.13) was carried as 'waterproof ALL buried
concrete', which would have coated 14 main-house exterior ground-beam faces that stand 0.95 m above natural ground and
55 m2 of beam soffits cast on blinding | A note's scope was read as an element list, not as a physical condition per
face | A coating printed for faces in contact with earth is measured per face over the height that has earth against it
(slab underside / natural ground vs soffit), soffits cast on blinding excluded, faces owned by another layer never twice,
other details' members HELD on scope (any villa) | tests/t263_buried_wp (adverse: coat above the printed ground refused;
underlay face as coat refused) | PROPOSED.

## 7. Not done / uncertain

- Not integrated (lane I package: new item code e.g. WP.BURIED_LIQUID with per-face rows; family B8-08 state).
- The ring's building-side face is not traced (no level marks on either side): HELD with both readings.
- Face lengths are the run's face-to-face length on both faces; the corner / neck GAP pieces of T-242 (<= 0.03 m2 of plan
  each) are not converted into face lengths (column faces belong to the neck line, HELD).
- p.8 was read at 80 dpi; notes 13 and 22 are material / cover requirements, not a coating.
- Checker re-measure list: p.13 right detail leader end (footing top) and left detail leader end (neck face); the four
  p.13 'Ground Beams' sections on 10 cm plain concrete; p.14 A-A and lift detail (no liquid note); run 7E0+FD#1 (L 3.35
  face to face, GS-01 on side B, outside on side A: 0.85 x 3.35 = 2.8475 m2 + plinth face excluded); run 7E9+7EA#1
  (L 4.225, D 0.40: 2 x 0.30 x 4.225 = 2.535 m2); footing F12 1ABF 14.08 - C3 0.15 - C7 0.24 = 13.69 m2 (SINGLE).
