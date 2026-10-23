# T-206 Level chain, run 2 (residential review R5): structural PDF sections, sunken wet slabs, per-footing chains

Worker 1 (lane S), 2026-10-23. Development villa, not an accuracy claim. ERS s.2-4 and s.7 applied. No engine module
changed: the merged `engine/source/level_chain_v1.py` takes the new evidence as chains with their own links (no new link
type was needed, so no `level_chain_v2.py`). New: `t206_alsenan_check.py` (evidence set R2 = the T-200 input, untouched,
+ the items below), `ALSENAN_LEVEL_INPUT_R2.json`, `summary_r2.json`, tests `tests/t206_level_chain_r2/` (non-Alsenan
hand fixture villa T206-Q + development-villa checks). Values, Drive file titles, pages, layers and handles only.

## 1. What was read (sheets searched)

- Drive "Alsenan chalet project" / ST7757.pdf, all 16 pages (vector, text drawn as linework; rendered and read, and the
  vector line coordinates measured where a number decides): axis, foundation, ground-beam and three slab plans with
  their legend (p.1-6), pool / dome detail (p.7), notes (p.8), schedules (p.9-12), details (p.13-16).
- ST7757 dxf.dxf: every TEXT / MTEXT / ATTRIB / DIMENSION text (nested to depth 4, layout DETAILS too); every HATCH by
  layer / pattern / scale.
- sanitary-7757.pdf, sheets 1-3 (GF / 1F / 2F drainage plans).
- The architectural levels and sections were read by T-200 (P7757 DXF, sheets 9 / 10); not repeated.

## 2. Chain table (R2; every value with its status)

### 2.1 Per storey

| Chain | FFL (finished) | Structural slab top | Build-up FFL -> slab top | Slab | Soffit / beam bottom |
|---|---|---|---|---|---|
| GF floor (ground slab) | +1.00 DRAWING-CONFIRMED | HELD (not printed) | HELD | 0.10 DRAWING-CONFIRMED (T=10cm) | HELD |
| Annex floor | +0.30 DRAWING-CONFIRMED | HELD | HELD | 0.10 DRAWING-CONFIRMED | HELD |
| 1F floor | +5.50 DRAWING-CONFIRMED | HELD | HELD | 0.16 DRAWING-CONFIRMED | HELD (B20 0.75 layer) |
| 1F sunken wet panels x5 (DXF HATCH 275, 276, 280, 287, 298) | +5.50 (storey FFL; no own mark) | **HELD: sunken by a drop no sheet prints** | HELD | 0.16 ("unless stated otherwise"; nothing stated) | HELD |
| 2F floor / terrace | +9.70 DRAWING-CONFIRMED | HELD | HELD | 0.16 DRAWING-CONFIRMED | HELD (B23 0.75 layer) |
| 2F sunken wet panel x1 (HATCH 5BF) | +9.70 | **HELD (sunken, drop not printed)** | HELD | 0.16 | HELD |
| 2F roof | +13.90 DRAWING-CONFIRMED | HELD | HELD (roof build-up) | 0.16 | HELD |
| Annex roof | +4.30 DRAWING-CONFIRMED | HELD | HELD | 0.16 | HELD |

No sheet of either set prints a structural slab top, soffit or beam-bottom LEVEL (T-200 finding, now with the whole ST
PDF and the sanitary set searched as well). The only S.S.L / T.O.B values in the ST set are in "TYPICAL STEEL LAYOUT -
STAIR SECTION" (p.16, marked N.T.S.): +4.00 at the top beam, +3.95 S.S.L, landing S.S.L +2.00, +0.00 T.O.B, -0.05
S.S.L. They are a template (no floor of this villa is at +4.00 or +2.00; GF FFL +1.00, 1F +5.50) and carry no FFL, so
they are not entered as project datums. What they show as a designer convention is a relation between two STRUCTURAL
surfaces at the stair beams (slab 0.05 below the beam top), not the FFL -> structure build-up.

### 2.2 Per footing type (17 types, ST7757.pdf p.9 schedule; p.13 / p.14 details)

Printed below every isolated footing (p.13, BOTH typical details, same stack): 5 cm screed, a membrane dimensioned **"2"**
(cm), 10 cm plain-concrete blinding. Vector check (right detail): lines at 427.48 / 434.56 / 437.32 / 451.48 pt give
7.08 / 2.76 / 14.16 pt, i.e. 5.0 / 1.95 / 10.0 cm at the chain's own scale (7.08 pt = the printed 5); left detail
5.08 / 1.95 / 10.0 cm. **The "2" that T-042 and T-200 left unread is the membrane thickness, 2 cm: UNDERLAY = 0.07 m
DRAWING-CONFIRMED.** The lift footing FF has its own detail (p.14: "5cm Screed", "Water proofing membrane" with no
thickness, "10cm Plain con.", footing "AS PER SCHEDULE", pit depth "As Per Lift Manufactures recommendations"): its
underlay stays HELD (the p.13 "2" is not carried to another detail, ERS s.3).

| Type | H (m) | Underlay | Blinding | Above formation: blinding top / footing bottom / footing top (m) | Absolute levels |
|---|---|---|---|---|---|
| F, F3, FN | 0.30 | 0.07 | 0.10 | 0.10 / 0.17 / 0.47 | HELD |
| F2 | 0.35 | 0.07 | 0.10 | 0.10 / 0.17 / 0.52 | HELD |
| F4, F5, F15 | 0.40 | 0.07 | 0.10 | 0.10 / 0.17 / 0.57 | HELD |
| F6, F7, F8, F10, F11, F13, F14 | 0.50 | 0.07 | 0.10 | 0.10 / 0.17 / 0.67 | HELD |
| F9 | 0.55 | 0.07 | 0.10 | 0.10 / 0.17 / 0.72 | HELD |
| F12 | 0.70 | 0.07 | 0.10 | 0.10 / 0.17 / 0.87 | HELD |
| FF (lift) | 0.55 | HELD (no membrane thickness) | 0.10 | HELD | HELD (pit depth to the lift maker) |

Formation (= founding) level: HELD. Printed: p.9 boxed note 1 "excavation level not less than 1.5 m below the existing
plot level" (FORMATION AT_MOST -1.50: a limit, OPEN, never a value); note 2 design bearing 2.20 kg/cm2, which is the
1.5 m row of the depth / bearing table on the same sheet (so the DESIGN BASIS is a 1.5 m founding depth, still a minimum);
p.8 note 12 leaves the founding level to the contractor and the supervising engineer after the soil check; owner Q-21 C.
Groundwater: p.9 note 4, 4.5 m below ground (below any formation near the limit; p.8 note 14 is conditional on water).
`summary_r2.json` "footings" gives two labelled what-ifs per type, NOT values: formation at the limit -1.50 (footing
bottom -1.33, top -1.33 + H) and the released V2.9 neck convention (footing underside -1.50, h = 1.00 + 1.50 - H),
which implies a formation at -1.67, 0.17 m deeper than the printed minimum.

Ground beams (p.13): interior typical depths 0.60 (span over 5 m), 0.40 (under 5 m), 0.30 (under 2.5 m), each 0.30 wide
on 0.10 blinding projecting 0.10 each side; exterior-wall beam: top "Ground Floor slab level", underside "Outer Normal
ground level", depth "FOLLOW ARCH." (names, no value; whether the existing +-0.00 or the court +0.15 is meant is not
fixed: GB_BOTTOM HELD). Detail selection (p.13): the single-ground-beam detail applies while (ground-beam top - footing
bottom) is less than 2.5 m, the two-beam detail above it. Formation at the limit and ground-beam top at most +1.00:
at most 1.00 + 1.33 = 2.33 m, single-beam detail; it changes only for a formation below about -1.67 (main house).

## 3. The T-189 condition (B20 / B23 over the stair)

NOT PROVEN. The T-189 rev2 ledger is unchanged only if the build-up FFL -> structural slab top is at most 0.289 m
(and the beam top not more than 0.167 m above the FFL). No sheet prints that build-up (s.1): ST PDF 16 pages, the ST DXF
texts, the sanitary set, and the architectural set (T-200). SECTION A-A / B-B of B20 / B23 (p.4 / p.5) print the beam
(40 / 45 x 75 with a 20 x 20 upstand) and no level. B20 and B23 are not in a sunken panel. The owner's manual 0.10
(Q-43) would lie inside the margin, but it is a finish-height method, shown beside, never a structural datum. Status
of the B20 / B23 stair-head lines: as T-189 rev2, conditional; HELD-reason LEVEL_NOT_PRINTED stays (lane I wiring).

## 4. Sunken wet slabs (new element finding)

The slab legend (p.3-p.6) has a "Sunken slab." hatch (lines 7.1 pt apart; "Cantilever-portion." 2.8 pt, "Bearing wall."
3.2 pt). On the plans: 5 sunken panels on the GF roof slab (= 1F floor) and 1 on the 1F roof slab (= 2F floor); in the
DXF they are HATCH ANSI31 scale 2000 on layer S-HAT.BAT (handles 275, 276, 280, 287, 298; 5BF), the cantilever hatch
ANSI31 scale 800. Each lies under a room with a floor drain on sanitary-7757.pdf (hand registration on the 31.37 x 15.00
plot frame, within about 0.5 m): two north 1F wet rooms, the south-west 1F wet rooms, the east 1F wet room, the 2F
maid-room wet room. The 1F laundry has a floor drain but no sunken hatch. The sanitary sheets run the branches "B.T.T.S."
(below the slab) and "T/B" (to below), so the drop is for the wet-room build-up / falls, not for pipes inside the slab.
**No sheet prints the drop** (no text, level or dimension inside or beside any sunken hatch, no section through one).

Consequences (no quantity changed here; for lane A / lane I): every takeoff that treats these panels as the storey's
normal slab top / soffit is flagged WRONG_REFERENCE with the needed datum HELD (uses W-1F-WET-*, W-2F-WET-5BF): slab
soffit and the ceiling / wall heights of the GF and 1F rooms below them, the wet-room screed or fill, and the
waterproofing upturns. Whether the panel drops at full thickness (soffit lower) or the slab is thinned is not printed
either: both stay HELD; never the normal slab top, never 0.

## 5. Engine vs freelancer (what this changes)

No released or candidate quantity changes (a check + evidence run). Effects for the lines that wait on these datums:
- Necks: released V2.9 10.855 m3 PROVISIONAL vs freelancer 8.805 m3 (-2.050 m3, -18.9 % of released) UNRESOLVED
  (T-205). New: the footing end is now a printed relation (footing top = formation + 0.17 + H); the formation and the
  ground-beam top are still unprinted. Under the released convention the footing bottom is at -1.50, i.e. a formation
  of -1.67; if the formation sits at its printed limit (-1.50) every neck is 0.17 m shorter at the footing end than the
  released convention. Not measured in m3 here (needs the neck sections; T-205), and neither end is a value.
- Excavation / backfill (T-170): per footing type the depth below the formation is now printed (0.47 .. 0.87 m to the
  footing top); the formation itself is HELD (Q-21 C). Pool chain unchanged (formation -1.50, T-183 r2).
- Wet-room slabs / ceilings below: a new HELD scope item (6 panels), not in any current line.

Verdict proposals: footing underlay 0.07 = DRAWING-CONFIRMED (engine none, freelancer not compared); necks UNRESOLVED
(formation and ground-beam top unprinted; designer item, T-042 B4); sunken panels UNKNOWN drop (designer item); no
owner question (ERS 2.7 not met: these are unprinted design values, not an owner decision).

## 6. Rule and lessons row (proposed)

Rule (any villa, provenance T-206): a dimension printed without a unit takes the unit of its own dimension chain and is
confirmed against the drawn spacing at that chain's own scale (vector measurement) before it is called "unread"; and
every hatch / symbol in a sheet's LEGEND is inventoried on that sheet's plans before the sheet is called searched (a
legend item found on a plan is an element: "Sunken slab." -> a sunken-slab chain per panel, its drop HELD when unprinted).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | The '2' under every footing carried as 'unread' by two runs (T-042, T-200) while it is the 2 cm membrane on the same printed chain as 5 and 10; six sunken wet panels in the slab legend never entered any chain | A unitless dimension was read alone, not against its own chain and scale; legend hatches were not inventoried on the plans | An unitless dimension takes its chain's unit and is checked against the drawn spacing at the chain's scale; every legend item is searched on the plans before a sheet counts as searched; an unprinted drop stays HELD (any villa) | tests/t206_level_chain_r2 (normal: sunken panel with T.O.S., printed formation; adverse: hatch-only panel HELD, normal soffit used under a sunken panel, T.O.S vs build-up conflict, two T.O.S., formation above the limit, missing formation, cm as m) | proposed |

## 7. For the Checker (re-measure from the drawings)

1. ST7757.pdf p.13 right footing detail: the vertical chain at the right edge prints 5 / 2 / 10; measure the three gaps
   (about 7.08 / 2.76 / 14.16 pt) and the screed / membrane / blinding labels in that order.
2. ST7757.pdf p.4 legend "Sunken slab." vs the hatched panels between B1 / B4 / CB2 (north) and B4 / B28 (east): same
   hatch spacing (about 7.1 pt), not the cantilever hatch (2.8 pt) of the B24 corner; DXF HATCH 275 / 298 ANSI31 x2000.
3. ST7757.pdf p.9: footing H column (F12 70, F9 / FF 55) and the boxed notes 1, 2, 4 with the depth / bearing table.
4. ST7757.pdf p.16: the stair-section levels are marked N.T.S. and are template values (not entered).

## 8. Not done / uncertain

- Interior ground-beam lengths (which depth class each beam is) and the GF slab / ground-beam relation for interior
  beams are not entered (p.13 names it only for the exterior-wall beam); T-205 / T-170 take the per-neck and
  per-excavation chains from here.
- The architectural set was not re-read for a wet-room finished level below the storey FFL (T-200 found none).
- Wiring (HELD reason LEVEL_NOT_PRINTED on neck, excavation, stair-head and sunken-panel lines) is lane I work.
