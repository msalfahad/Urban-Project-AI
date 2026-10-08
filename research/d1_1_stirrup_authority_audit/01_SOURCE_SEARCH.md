# 01 SOURCE SEARCH: bend radius, hooks, closure, link fabrication

Every channel of the issued set was searched again for the facts a fabricated link length needs. No design code, external example, donor or other engine was opened.

## Findings

| Fact | Result |
|---|---|
| BEND_RADIUS | SOURCE_EXPECTED_NOT_LOCATED - the issued sections draw the corners bent (chorded arcs) but no radius, diameter or mandrel is printed; no radial dimension exists; P8-N03 forbids scaling |
| BEND_DIAMETER | SOURCE_EXPECTED_NOT_LOCATED - no text, note or dimension |
| CENTRELINE_BEND_GEOMETRY | SOURCE_EXPECTED_NOT_LOCATED - drawn, not dimensioned |
| HOOK_ANGLE | SOURCE_EXPECTED_NOT_LOCATED - hook ticks / corner hook drawn; no angle printed |
| HOOK_LENGTH_EXTENSION | SOURCE_EXPECTED_NOT_LOCATED - no text or dimension; project rule register HOOKS_AND_BENDS = NO_PROJECT_SOURCE |
| CLOSURE_LAP | SOURCE_EXPECTED_NOT_LOCATED - the only lap note in the set is p.15 'LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40xDIA' (slab temperature bars); note 9 70D / 40D is for starters |
| LINK_FABRICATION_NOTE | SOURCE_EXPECTED_NOT_LOCATED - no standard-link, bending-schedule or bending note |
| GENERAL_BENDING_NOTE | SOURCE_EXPECTED_NOT_LOCATED - p.8 notes 1-24 carry none |
| COVER_SEMANTICS | p.8 note 22 prints a MINIMUM cover (>= 2.5 / >= 7 cm): the cover-reduced link envelope is an UPPER envelope, not an exact or minimum size |

## A. DXF (ST7757.dxf, all layouts and block definitions)

- Texts scanned: 4055 (ATTDEF 92, ATTRIB 962, DIMENSION 754, MTEXT 393, TEXT 1854).
- Legacy-Arabic texts decoded: 63.
- Dimension types: {'0': 750, '1': 4} (0 linear, 1 aligned).
- Radius or diameter dimensions: **0**.
- Term hits (every hit is listed below; an absent term had none):
  - `STIRR`: 'STIRRUPS/m'
- Searched English terms: BEND, BENT, RADIUS, RAD., MANDREL, FORMER, HOOK, 135, LAP, SPLICE, OVERLAP, CLOSURE, ANCHOR, DEVELOP, EXTENSION, CRANK, SHAPE, CUT, LINK, TIE, STIRR, XD, XDIA, X DIA, R=.
- Searched Arabic terms: ثني, تثني, خطاف, كانة, كانات, رباط, وصلة, وصلات, تراكب, نصف قطر, تكسيح.
- Drawn reinforcement arcs in model space (S-REIN.D), by undimensioned drawn radius in drawing units:
  16.6: 192, 24.1: 166, 25.4: 8, 31.8: 40, 33.2: 7, 45.7: 64.
  These several drawn radii show bends are drawn but not defined. They are QA only: P8-N03 forbids scaling.

## B. Issued link sections (PDF vector strokes, S-REIN.D)

| Section | Segments | Straight sides | Short corner chords | Corners | Radius dimensioned |
|---|---|---|---|---|---|
| p13 GB_EXTERIOR (30 x FOLLOW ARCH) | 22 | 4 | 16 | ROUNDED (chorded arcs) | False |
| p13 GB_GT_5M (30x60) | 22 | 4 | 16 | ROUNDED (chorded arcs) | False |
| p13 GB_LT_2_5M (30x30) | 21 | 4 | 16 | ROUNDED (chorded arcs) | False |
| p13 GB_LT_5M (30x40) | 21 | 4 | 16 | ROUNDED (chorded arcs) | False |
| p15 TYP. SLAB ON BEAMS beam section | 20 | 4 | 16 | ROUNDED (chorded arcs) | False |

## C. General notes and project rules

- p.8 notes transcribed (S1): 24. Notes containing any bend / hook / lap / link term: P8-N09, P8-N19.
- Notes or typicals anywhere in the S1 rule register containing such a term:
  - P8-N09 (p.8, develop): Development length of STARTER bars >= 70 D in tension zones, >= 40 D in compression zones.
  - P8-N19 (p.8, tie): Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m.
  - P9-COL-TIES (p.9, tie): Column ties Ø8, 6 per metre (all column types).
  - P9-COL-L (p.9, tie): L is the long side of the column section (tie topology selector).
  - P9-COL-BAND-1 (p.9, tie): L ≤ 50 cm: one closed perimeter tie.
  - P9-COL-BAND-2 (p.9, lap, tie): 50 < L < 80 cm: two overlapping closed ties.
  - P9-COL-BAND-3 (p.9, lap, tie): 80 < L < 120 cm: two overlapping closed ties + one small central tie.
  - P11-12-CB-TYPICAL (p.11, stirrup): Continuous-beam figure: support top bars to 0.22 Ln (0.3 Ln2 at an end span), first stirrup 7.5 cm, bottom bar stop 0.15 L.
  - P13-GB-GT5 (p.13, link): Ground beam > 5 m.
  - P13-GB-LT5 (p.13, link): Ground beam < 5 m.
  - P13-GB-EXT (p.13, link): Ground beams under exterior walls (outer normal ground level to GF slab level).
  - P15-TEMP-NOTES (p.15, lap): Temperature bars lap 40D; top temp bars x2000 across beams parallel to main bars (1000 at spandrels); use the larger top bars where adjacent spans differ.
  - P15-SLAB-ON-BEAMS (p.15, anchor): Slab-on-beam typical: top anchor 0.25 L1 at a non-continuous support; 0.30 x max(L1, L2) at a continuous support; 50% of top bars extend into the adjacent slab; 50% of bottom bars stop 0.125 L short of a continuous support, the balance continues.
  - P15-TWISTED (p.15, tie): Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.
  - P15-PLANTED (p.15, anchor): Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.
- P8-N03: Use printed dimensions; do not scale the drawings.
- P8-N22: Cover >= 2.5 cm columns / slabs / beams; >= 7 cm in contact with soil. (rule register scope: minimum cover, minimum cover).
- Project rule register HOOKS_AND_BENDS: NO_PROJECT_SOURCE (never used for official kg).

## D. PDF detail and schedule sheets pp.9-16 (OCR search aid)

Method: pp.9-16 text layers (S-TEXT.D, S-TEXT.SCH, S-DIM.D, 0, S-TEXT) rendered from the vector strokes with the pure-python pypdf renderer at 3.0 px/pt, rotated 90, then tesseract 5 'eng' --psm 11; raw OCR lines kept. OCR is a search aid only: a hit is re-read on the render, a non-hit is backed by the DXF text sweep.

Terms found: 40X, ANCHOR, DIA, EXTEN, LAP, STIRR. Every hit was re-read:
- STIRR hits: schedule header 'STIRRUPS/m', column stirrup labels, 'Spiral Stirrups' (turned column), opening-in-beam '3 NO. Ø10 STIRR. AT 5cm c/c' - counts / spacings only, no bend or hook geometry
- p15 '40xDIA': note 1 of the slab temperature notes: 'LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40xDIA' - slab temperature bars only
- p15 'TOP ANCHOR BARS' / 'EXTEND 50% OF TOP REINF.': slab-on-beam typical (slab bars), not links
- p16 'be lap': OCR noise from the word 'LANDING' (stair detail render re-read visually)

No BEND, BENT, RADIUS, HOOK, SPLICE, MANDREL, 135 or OVERLAP text appears on pp.9-16.
