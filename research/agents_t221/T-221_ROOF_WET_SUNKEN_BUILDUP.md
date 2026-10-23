# T-221 Structural top of the zones T-214 held: roofs / terraces (falls), wet rooms, sunken panels; D-44 search

Worker 1 (lane S), 2026-10-23, run unknown. Development villa, not an accuracy claim. ERS read; s.2 steps 1-4 and 7,
s.3 (finished vs structural datum; a notation's meaning before its arithmetic), s.4, s.7 applied. Files:
research/agents_t221/* and tests/t221_roof_falls/* only: no engine module, method, rule / knowledge version, registry,
candidate or released quantity changed. Drawings cited by Drive title / view only; outlines in local metres.

## 1. Result in engineering terms

**A roof's build-up is a field, not a layer.** Between the slab and the finished roof lies t0 (the screed at the outlet)
plus the rise z(p) of the falls surface, plus the membrane / protection layers. The issued set fixes the fall (printed
'SLOPE 1%', sanitary-7757 p.2 / p.3) and the outlets (corner RWPs) of three roofs, so z(p) is now computed from the
drawings; it does NOT print t0, the layers, or which point a printed finished roof level refers to. Every roof therefore
stays HELD, now with its falls rise in metres instead of an open question.

| Zone | Area inside parapets (plan) | Outlets | Falls rise max, EIKONAL .. AXIS | Mean rise | Screed above the t0 plane | Status |
|---|---|---|---|---|---|---|
| ROOF-970 (1F roof terraces, finished +9.70) | 147.691 m2 | 3 corners (SW, SE, NE) | **0.107 .. 0.144 m** | 0.055 .. 0.071 m | 8.168 .. 10.455 m3 | HELD (t0, layers, level reference) |
| TERRACE-550 (GF roof strips, +5.50) | 32.387 m2 | 1 (SE corner) | **0.190 .. 0.203 m** | 0.084 .. 0.090 m | 2.712 .. 2.900 m3 | HELD (same) |
| ROOF-430 (annex roof, +4.30) | 52.848 m2 | 1 (SW corner) | **0.112 .. 0.147 m** | 0.059 .. 0.073 m | 3.103 .. 3.882 m3 | HELD (same) |
| ROOF-1390 (main roof, +13.90) | not measured here | **none drawn on any sheet** | - | - | - | HELD: DRAINS_NOT_DRAWN |
| GF-WET, ANNEX-WET (W.C / bath / wash) | - | - | - | - | - | HELD: no wet build-up printed; **no section cuts a wet room on any floor** (s.4) |
| 1F-SUNKEN x5, 2F-SUNKEN x1 | - | - | - | - | - | HELD: drop printed nowhere (D-41); no section cuts a panel (T-213) |

The range is from ONE named cause, FALL_LAYOUT_NOT_DRAWN (no ridges / valleys / cross-falls are drawn): EIKONAL is the
lowest surface that keeps every fall at least 1 % (rise = 1 % x shortest path inside the roof to the nearest outlet);
AXIS is the layout the drawn edge arrows show (1 % across to the parapet line, then 1 % along it: 1 % x the L1 path).
Never averaged. Grid 0.05 m, outline sampled every 0.01 m; resolution 0.0007 m.

## 2. The physical element and each number's meaning (ERS s.2 step 1, s.3)

- **'SLOPE 1%'** is printed with arrows along the edges, ending at the RWP symbols: it is the fall of the finished
  surface toward each outlet (a gradient), not a thickness. Q-45's owner value (0.5 % per m) is the fallback for a roof
  with no printed slope (Lead 2026-10-20 reading); it scales the rise only (a test shows 0.5 % halves it). Where a fall
  is printed, the printed fall governs (MISSION precedence).
- **The printed finished roof level** (+9.70, +5.50, +4.30, +13.90) is one marker per roof. On a surface that rises up to
  0.20 m it can be the level at the outlet, at the high point or at the marker position: the set does not say. It is a
  FINISHED datum and never the structural top (FINISHED_AS_STRUCTURAL), never b = 0.
- **The drawn roof band.** SECTION A-A / B-B draw every roof band (+4.30, the +5.50 sea strip, +9.70, +13.90) with the
  same constant 0.05 / 0.20 lines as the dry floors (section_bands.py re-run: A-A +13.90 0.050 / 0.201, +9.70 0.050 /
  0.200; B-B +4.30 0.050 / 0.200, +9.70 0.050 / 0.200). A constant 0.05 cannot carry a 0.11 .. 0.20 m rise: it is a
  drafting convention on roofs and stays refused (CONSTANT_LAYER_VS_FALLS, T-214). ST p.5 / p.6 draw no slab step and no
  level at any roof edge.
- **The parapet detail** (ST7757.pdf p.14 'TYPICAL DETAIL OF PARAPET SECTION.'): RC upstand 0.30 above the slab, note
  'MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING'. A printed upper bound on the build-up at a parapet: b(edge) < 0.30.
  With the rise known, the allowance left for t0 + membrane + protection at the worst point is 0.156 .. 0.193 (ROOF-970),
  **0.097 .. 0.110 (TERRACE-550)**, 0.153 .. 0.189 (ROOF-430): NOT PROVEN (t0 and layers unprinted), not violated. On
  the +5.50 strip a normal t0 + membrane + protection uses most of that 0.10 m: the designer item says so.
- **Wet rooms**: Q-45 bed 0.04 .. 0.06 + tile, 1 % falls; Q-41 bed only, no separate screed; tile thickness and membrane
  not given; no level is printed inside any wet room on the sanitary sheets (p.1-3 read) or the architectural plans.
- **Sunken panels**: the drop is the difference the wet build-up needs; printed nowhere (D-41); nothing carried.

## 3. Reconciliation (ERS s.2 step 4)

Owner manual method beside: Q-41 (roof / balcony screed own line, thickness not given) and Q-45 (roof bed by the falls)
give no t0 and no layer thicknesses, so they agree with the drawings on the falls principle and leave the same gap. No
freelancer or engine line carries a roof screed or a roof structural top (coverage family 'Roofing build-up / insulation
/ screed to falls' NOT_IMPLEMENTED, BOQ_FAMILY_MASTER 1.3.0), so there is nothing to reconcile in quantity; the screed
volume above the t0 plane (14.0 .. 17.2 m3 over the three roofs) is a by-product for the future line, HELD with t0.
Worked hand check (TERRACE-550, one outlet at the end of an 18.972 x 1.302 leg): EIKONAL 0.01 x sqrt(18.972^2 + 1.302^2)
= 0.1902; AXIS 0.01 x (18.972 + 1.302) = 0.2027. ROOF-970's far point lies on the 2F block's south face, 9.43 m from the
SW and SE outlets: 0.01 x sqrt(9.432^2 + 5.0^2) = 0.1068 / 0.01 x 14.43 = 0.1443.

Physical consequence, named for the designer (not a choice made here): ROOF-970 sits beside the 2F rooms at the same
finished +9.70 and the sections draw one slab band under both. If the slab is continuous at +9.65 (the 2F dry top,
T-214) then the terrace finishes at +9.70 only at the outlets and rises to +9.81 .. +9.84 at the block face plus t0 (door
thresholds), or the slab steps down / is cast to falls. The same holds for TERRACE-550 against the 1F floor +5.50.

## 4. Section-cut search for wet rooms (closes T-214 s.8 item 1)

Cut lines read on the DWF plan views (dashed line between the markers): A-A x line through the stair on every floor;
B-B one y line across all floors. Clearance to the nearest wet-room wall: GF A-A 0.58 m (W.C west wall face), GF B-B 1.07 m (south
Wash / W.C), 1F A-A 1.92 m (master bath), 1F B-B 0.93 m (sea-side BATH), 2F A-A 0.235 m (stair / W.C wall), 2F B-B
terrace only. **No section cuts a wet room on any floor**, so no drawn wet build-up exists to read.

## 5. D-44 (consultant row 2): B15 20 x 120 at the water tank, upstand or downstand

Searched sheet by sheet (summary.json d44_record): ST p.6 plan (size only, same line style as every beam, 'WATER TANK
PLACE' panel T18), ST p.10 schedule (20 / 120, bars only), ST p.14 details (parapet / boundary / lift, no tank), ST p.15 /
p.16 (typical details), the NE / NW / SW elevations (one coping at +14.40 = 13.90 + 0.50 across the face on which B15
runs; only the dome above it; no tank drawn), SECTION A-A (cut about 1.9 m inside that face looking at it: uniform roof
band; a 2.18 m box beyond, top +14.40, 2.15 .. 4.33 m from the north face, outside the 0 .. 3.5 m tank panel: not B15),
SECTION B-B (block beyond, no tank), sanitary p.1-3 (no roof plan). **NOT DRAWN on any sheet**: row 2 is send-ready.
An upstand would top at about slab + 1.02 >= +14.62 (slab top above +13.60 by the parapet rule), 0.22 m or more above the
drawn coping, but the architect draws no tank either, so the elevations neither show nor exclude it. 2F C2 / C3 heights
stay the T-119 r2 range 3.00 .. 3.80 m; the tank joint 0.160 m3 stays HELD.

## 6. Downstream lines (data for lane I; no BOQ line moved)

| Item | Before | After |
|---|---|---|
| Roof / terrace structural tops (D-39) | HELD, 'build-up unknown' | HELD on t0, layers and the level reference; the falls rise is DRAWING-CONFIRMED as a range per roof (table s.1) |
| Roof waterproofing / screed plan areas | open | 147.691 / 32.387 / 52.848 m2 inside the parapet faces (plan, DRAWING-CONFIRMED, Checker to re-measure; a 1 % slope adds 0.005 % to the surface); main roof outline not measured here |
| Roof screed m3 (Q-41 line) | HELD (thickness) | area x t0 + 14.0 .. 17.2 m3 above the t0 plane; t0 HELD |
| Necks (T-205) | b settled by T-214, d HELD | unchanged: the GF ground-beam top (p.13 'Ground Floor slab level') is a dry-floor datum; no wet zone changes it |
| T-189 B20 / B23 | PROVEN drawing basis, NOT PROVEN owner basis | unchanged (1F dry zone, T-214) |
| P-GF-05 masonry | 2.640 m2 (T-222 MERGED 769cad40) | unchanged |
| Column tops 2F -> roof | HELD with the roof build-up | HELD (main roof has no outlet; ROOF-1390) |
| 2F C2 / C3 (D-44) | HELD 3.00 .. 3.80 | HELD; D-44 send-ready |

D-39 narrowed: the falls are no longer unknown; the item asks for (1) t0 at the outlets and the roof layers, (2) the
reference point of each printed finished roof level, (3) whether the roof slab is continuous with the floor slab or
steps / is cast to falls, (4) outlets and falls of the +13.90 roof. D-40: wet zones keep their item (no section cuts
one). D-41 unchanged.

## 7. Verdict proposals

- Roof falls rise (three roofs): no engine line, no freelancer line: DRAWING-CONFIRMED range, Checker to re-measure.
- Roof / terrace / wet / sunken structural tops: UNRESOLVED (designer items D-39 / D-40 / D-41), no owner question:
  ERS 2.7 not met (unprinted design values, not an owner decision).
- D-44: UNRESOLVED, not drawn on any sheet: consultant row 2 send-ready.

## 8. Rule and lessons row (proposed)

Rule (any villa, provenance T-221): a roof / terrace build-up is t0 + z(p) + layers. With the outlets drawn and the fall
printed (or the owner's fall where none is printed), z(p) is computed as the range [EIKONAL, AXIS] from the cause
FALL_LAYOUT_NOT_DRAWN; t0, the layers and the reference point of a single printed finished roof level are separate
items, HELD when unprinted; a roof without drawn outlets is HELD (DRAINS_NOT_DRAWN); a printed upstand rule bounds b at
the parapet (PROVEN / VIOLATED / NOT PROVEN); a section is searched for a wet room before a wet build-up is called
undrawn.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Roof and terrace build-up held for days as one unknown thickness (D-39), while the drainage sheets print the fall and the outlets that fix most of it (0.11 .. 0.20 m rise) | The build-up was treated as a layer (one number under a level mark) instead of a field set by outlets and fall; a constant drawn band and a single finished level were the only sources searched | A roof build-up is t0 + z(p) + layers: compute z from the drawn outlets and the printed fall as [EIKONAL, AXIS] (named cause: plane layout not drawn), hold t0 / layers / the level's reference point, never a constant layer and never b = 0 (every villa, every roof / terrace / balcony) | tests/t221_roof_falls (villa T221-R: two outlets, reflex L, strip, mirror / rotation / mm; adverse: no outlet, zero fall, outlet outside, constant layer, dry layer to wet, finished as structural, allowance as datum) | proposed |

## 9. For the Checker (re-measure from the drawings, not from this file)

1. sanitary-7757.pdf p.3 (2F drainage plan): three RWP outlets at the SW, SE and NE corners of the +9.70 roof; 'SLOPE 1%'
   arrows. p.2: one outlet each on the +4.30 annex roof (SW) and the +5.50 strips (SE).
2. Architectural .dwf, 1st.FLOOR PLAN: the +5.50 south leg between the 1F south face and the boundary inner face
   (1.302 m) from the annex junction to the sea-side edge (18.972 m); then by hand 0.01 x (18.972 + 1.302) = 0.203 m.
3. One roof band from the DWF: SECTION B-B +9.70 (terrace only on this cut): lines 0.050 / 0.200 below the level line
   (`python3 -I research/agents_t214/section_bands.py <private .dwf>`), i.e. the constant band refused on a roof.
4. ST7757.pdf p.14 typical parapet: upstand 30 and the note on roof finishing.
5. D-44: ST p.6 B15 and the NW elevation coping +14.40 (dimension chain 420 + 50 from +9.70).

## 10. Not done / uncertain

- The +13.90 roof outline and its waterproofing area were not measured (no outlet, no falls): HELD.
- The two domes stand inside ROOF-970's outline (2 x about 15.3 m2 footprint); their scenarios follow T-185; neither
  contains a far point, so the rise is unchanged; the screed volume includes their footprint (scope for lane I).
- Outlets are placed at the inner corners; the drawn RWP symbol sits within 0.1 m of them (rise effect <= 0.001 m).
