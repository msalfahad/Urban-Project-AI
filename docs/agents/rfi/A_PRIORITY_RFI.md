# A. Priority RFIs, Alsenan chalet (DRAFT, NOT TO BE SENT; owner 2026-10-29 22:05)

Prepared by the Lead 2026-10-30 00:15-00:25 UTC (run started 00:13) from CLARIFICATIONS_CONSULTANT_2026-10-24.md,
revalidated against the merged, Checker-verified evidence up to engine head b12e10de (T-352) and the board at d04da3be.
Companion files: D_REMOVED_REVISED.md (what was removed or changed, with evidence), C_UNLOCK_MATRIX.md (internal: which
questions together close each whole BOQ line), B_REMAINING_RFI.md (next Lead run: the remaining questions).

CORRECTIONS APPLIED (Lead 2026-10-30 04:20 UTC): every CORRECTED and PARTIAL citation verdict of the Checker (01:30
run and the 03:56 addendum, at the end of this file) is now written into the question text: S01 (ST p.9 note 1), S04,
S12, S13, S14, S15, S16, S18 (note sheet still to confirm), S19 / S21 (ST p.1), S20, S22 (ST p.6), S23 (sheets 10 / 11 /
04), A01, A03, A04, A05, A06, A07 and A08 (the space is now identified by position and size, and its use is asked; the
internal name 'dressing room' is removed). No question was added, removed or reworded beyond its citation, except A08.

STATUS: NOT SENT. The owner reviews; nothing goes to any designer until he says so. CHECKER (light run): re-check the
sheet / detail / handle citation of every question below against the drawing; a citation marked "(sheet no. to confirm)"
is one the merged evidence names by drawing content but not by sheet number: confirm or correct it from the print.

HOW TO READ A QUESTION. Each question stands alone and can be answered alone. "Options the drawings allow" lists only
what the issued prints themselves permit; it is never a proposed design, and the designer may answer differently. Until
an answer arrives, every affected quantity stays HELD or CONFLICT, visible, never 0. No owner decision is reopened.

Drawing set as issued: architectural P7757 sheets 01 .. 12 (P7757.dxf), structural ST7757.pdf p.1 .. 16
('ST7757 dxf.dxf'), 3 sanitary sheets. Page numbers are those prints. ST handles are DXF entity handles in 'ST7757 dxf.dxf'.

Count: 36 questions (structural 28, architect 8; A09 is a pointer, not a question) in 9 line groups (P-1 .. P-9); all 9 groups are now complete
(G1 and G4 were settled from the drawings; G2 and G3 are drafted below from the T-287 sheet search).

---

## Structural designer

### RFI-S01 Founding level of the footings and start level of the column necks
- Discipline: structural.
- Drawing: ST p.9 general note 1 (notes box under the bearing-capacity table: "excavation not less than 1.50 m below the
  existing plot level"; the existing plot level is printed +-0.00 only at the plot corners, outside the boundary); ST p.13 blinding /
  underlay detail; ST p.2 foundation plan; ST p.9 column schedule (necks).
- Missing information: the note fixes a minimum excavation depth only. No sheet prints the underside level of the
  footings or the level at which the column necks start.
- Requested: the founding (footing underside) level, or confirmation that the 1.50 m is the footing underside; the neck
  start level.
- Affected BOQ lines: CONC.COLUMN (28 necks, HELD, lower bound 9.2568 m3); CONC.BLINDING (ground-beam blinding level);
  excavation / backfill / disposal (no line yet; pits at least 188.017 m3 as a lower bound only); column starter bars.
- Options the drawings allow: footing underside at the 1.50 m excavation level plus the printed build-up; or the 1.50 m is
  the footing underside.

### RFI-S02 South-east footing carrying two tags (F10 and F)
- Discipline: structural.
- Drawing: ST p.2 foundation plan (one outline about 3.25 x 1.40 m tagged F10 and F); ST p.9 footing schedule (F10
  280 x 140 x 50; F 90 x 80 x 30).
- Conflict: one drawn outline carries two schedule tags whose sizes do not match it; no combined-footing note.
- Requested: two separate pads as scheduled, or one combined footing to the drawn outline (and its depth).
- Affected BOQ lines: CONC.FOOTING 2.176 .. 2.275 m3 HELD; CONC.BLINDING 0.552 .. 0.590 m3 HELD; strap SB1 inside it
  0 .. 0.385 m3 HELD.

### RFI-S03 Plot-perimeter foundation band: section and level
- Discipline: structural.
- Drawing: ST p.2 foundation plan (hatched 0.20 band, 91.94 m, of which 21.45 m passes through 10 footings); ST p.10
  beam schedule row B.W 20 x 60; ST p.14 TYPICAL BOUNDARY WALL (G.B 20 x 40); ST p.1 note 2.
- Missing / conflicting: two printed sections could apply (B.W 20 x 60 or G.B 20 x 40); the band's level where it
  crosses the footings is not shown (stopped at the footing or continuous at another level).
- Requested: the band's section, and its level and continuity at each footing it crosses.
- Affected BOQ lines: CONC.GROUND / CONC.FOOTING band 8.459 m3 (owner's provisional reading, not released) vs 11.033 m3;
  boundary lower band 5.639 .. 11.033 m3 range; CONC.BLINDING under the band.

### RFI-S04 Boundary-wall columns and pads: positions
- Discipline: structural (with the architect for the boundary-wall layout).
- Drawing: ST p.14 TYPICAL BOUNDARY WALL (pads 130 x 80 x 30, spacing "SEE ARCH PLAN"); architectural P7757 sheet 03,
  GROUND FLOOR PLAN 1:100 (boundary wall drawn 0.20; no column positions marked).
- Missing information: the detail refers to the architectural plan for the spacing, and the architectural plan marks no
  boundary-wall column or pad.
- Requested: the positions (or the spacing and the start / end points) of the boundary-wall columns and their pads.
- Affected BOQ lines: CONC.FOOTING / CONC.GROUND boundary pads and columns UNMEASURED; CONC.BLINDING under the pads
  UNMEASURED (an export row, never omitted).

### RFI-S05 Strap SB3 at footing F3: soffit level
- Discipline: structural.
- Drawing: ST p.2 foundation plan (SB3 running into F3); ST p.10 strap row SB3.
- Missing information: the soffit level of SB3 where it meets F3 is not printed, so the strap's volume inside the footing
  is not fixed.
- Requested: the SB3 soffit level relative to the F3 top / underside.
- Affected BOQ line: CONC.FOOTING, SB3 inside F3 0.0295 .. 0.2683 m3 HELD.

### RFI-S06 Blinding at the 8 footings on the plot line
- Discipline: structural.
- Drawing: ST p.13 (blinding printed 10 cm past each footing face); ST p.2 (8 footings drawn on the plot line).
- Missing information: whether the blinding projects beyond the plot line at these 8 footings or stops at it.
- Requested: stop at the plot line, or project as p.13.
- Affected BOQ line: CONC.BLINDING 0 .. 0.189 m3 HELD.

### RFI-S07 Blinding under the foundation straps
- Discipline: structural.
- Drawing: ST p.13 (blinding drawn under footings and under the four ground-beam sections; none drawn under straps).
- Missing information: whether the straps sit on blinding.
- Requested: blinding under the straps, yes or no (and its width if yes).
- Affected BOQ line: CONC.BLINDING 0 .. 0.913 m3 HELD.

### RFI-S08 Blinding projection under the lift raft (FF)
- Discipline: structural.
- Drawing: ST p.14 DETAIL OF LIFT WITH ISOLATED FOOTING (prints "10cm Plain con.", no projection dimension).
- Missing information: how far the blinding projects beyond the raft faces.
- Requested: the projection dimension.
- Affected BOQ line: CONC.BLINDING, FF blinding HELD, at least 2.070 m3.

### RFI-S09 Depth of the exterior ground beams (main house and annex)
- Discipline: structural (with the architect for the floor build-up).
- Drawing: ST p.13 ground-beam sections ("FOLLOW ARCH." from GF slab level to outer ground).
- Missing information: the exterior beam depth refers to the architectural drawings, which print no floor build-up and
  no outer ground level at the beams.
- Requested: the depth of the exterior ground beams (main house and annex), or the levels that fix it.
- Affected BOQ line: CONC.GROUND, 24 exterior beams HELD (11.930 m3 is on an unsupported basis and is not used); exterior
  side bars and links unquantified.

### RFI-S10 Ground beams carrying a concentrated load
- Discipline: structural.
- Drawing: ST p.13 (sections printed only for beams "without concentrated load"); ST p.2 (15 spans with another beam or
  the stair start bearing on them).
- Missing information: the section and reinforcement of the loaded spans.
- Requested: which spans are treated as loaded, and their section and bars.
- Affected BOQ lines: CONC.GROUND section of 15 spans; ground-beam reinforcement of 15 spans HELD.

### RFI-S11 Ground-beam section titles: length basis and the < 2.5 m link
- Discipline: structural.
- Drawing: ST p.13 section titles "more than 5m", "less than 5m", "less than 2.5m"; the < 2.5 m section's link drawn
  without size or spacing.
- Missing information: whether the lengths are clear spans or centreline spans; which title governs below 2.5 m (two
  apply); the size and spacing of the < 2.5 m link; one span measures exactly 5.00 m face to face.
- Requested: the length basis, the governing title below 2.5 m, the < 2.5 m link, and the section of the 5.00 m span.
- Affected BOQ lines: CONC.GROUND (5.00 m span HELD); ground-beam links of the < 2.5 m spans unquantified.

### RFI-S12 Beam CB10: width
- Discipline: structural.
- Drawing: ST p.5, 1F roof slab plan (CB10 drawn 0.30 wide; the CB10 label sits beside the 0.20 outer strip); ST p.11 / p.12
  continuous-beam schedule (CB10 0.25 x 0.50).
- Conflict: schedule width 0.25 vs drawn width 0.30, and the label placement leaves it unclear which band is CB10.
- Requested: which band is CB10, and its width.
- Affected BOQ line: CONC.BEAM, CB10 CONFLICT 0.744 / 0.893 m3 (part of the 7-run CONFLICT below).

### RFI-S13 Beams whose drawn width differs from the schedule (GF B29, GF CB2 two spans, GF B21, 1F B6 one span)
- Discipline: structural.
- Drawing: ST p.4 GF roof slab plan (B29, CB2, B21) and ST p.5 1F roof slab plan (B6) (two edge lines per beam) vs ST
  p.10 / p.11 schedules: GF B29 schedule 25 / drawn
  0.20 (6.74 m); GF CB2 two spans 20 / 0.25; GF B21 45 / 0.40 (inclined); 1F B6 vertical span at x 26.37, 25 / 0.20.
- Conflict: schedule width vs drawn width; no section cuts these beams.
- Requested: the built width of each listed span.
- Affected BOQ line: CONC.BEAM, 7 runs CONFLICT (with RFI-S12): drawn 5.4421 vs scheduled 5.7665 m3; beam soffit 8.7140
  vs 9.0072 m2.

### RFI-S14 GF beam line labelled both CB3 and "B3 (with stair)"
- Discipline: structural.
- Drawing: ST p.4 GF roof slab plan (labels CB3, B3 and "(With Stair)" on one beam line, the south line); ST p.16 TYPICAL DETAIL OF STAIR BEAM.
- Conflict: two type labels on one line.
- Requested: one beam of which type, or two members (and their positions).
- Affected BOQ line: CONC.BEAM HELD (never counted twice).

### RFI-S15 Six unlabelled beam spans
- Discipline: structural.
- Drawing: ST p.4 GF roof slab plan and ST p.5 1F roof slab plan (six drawn spans without a label; DXF handles listed
  with each span).
- Missing information: type and section.
- Requested: the type or section of each span.
- Affected BOQ line: CONC.BEAM HELD (location, length and candidate volume listed).

### RFI-S16 Edge strips and boxes without a section (west outer strip, SE box, CB12 outer strip, strips north of B23 / B20)
- Discipline: structural.
- Drawing: ST p.4 GF roof slab plan and ST p.5 1F roof slab plan (drawn bands; sections incomplete).
- Missing information: whether these bands are concrete beams, and their section.
- Requested: beam or not; the section if a beam.
- Affected BOQ line: CONC.BEAM HELD.

### RFI-S17 East dome-opening ring on the 1F roof slab
- Discipline: structural.
- Drawing: ST 1F roof slab plan (west ring prints two B4 texts; east ring, centre about x 30.83 / y 41.65, R 2.211 /
  2.411 m, prints no mark, only SEE DETAIL); ST p.7 DETAIL OF DOME (ring 20 wide, depth AS PER ARCH).
- Missing information: the section of the east ring.
- Requested: the east ring's beam type / section (the same as the west B4, or another).
- Affected BOQ line: CONC.BEAM HELD (0.900 m3 if B4).

### RFI-S18 Roof-edge projection bands
- Discipline: structural (with the architect).
- Drawing: ST p.4 GF roof slab plan and ST p.5 1F roof slab plan (rounded bands round the roof edges: 0.20 strips north of B20 / B23; 1F outer
  west strip 7.50 m; 1F strip 0.30 x 4.51 and SE box 0.30 x 0.90 outside CB12; GF outer west strip 0.20 x 4.10 m; 1F
  0.10 strip outside CB12 over 5.69 m; 1F rounded box about 0.40 x 1.00 m); a structural note (Arabic: the contractor
  matches parapet and projection details to the architectural drawings; sheet still to confirm: it is not ST p.1 note 1); sections A-A / B-B draw the beam outline only.
- Missing information: depth, section and material of each projection; cast with the slab or not.
- Requested: a section for each projection (or one typical section and where it applies).
- Affected BOQ lines: CONC.BEAM HELD (plan areas listed, no volume); facade finishes on the projection faces.

### RFI-S19 Column C8: section
- Discipline: structural.
- Drawing: ST p.1 columns and axes plan (C8 printed 30X80 at two positions, dimensioned 70 + 10); ST storey plans (five
  0.80 outlines); ST p.9 column schedule (30 x 90).
- Conflict: plan 30 x 80 vs schedule 30 x 90.
- Requested: the built section of C8 (neck, GF, 1F).
- Affected BOQ line: CONC.COLUMN CONFLICT (neck 0.240 .. 0.270 m2 section; GF 0.900 .. 1.0125 m3; 1F 0.180 .. 0.200 m2
  section).

### RFI-S20 Thirteen columns whose plan outline differs from the schedule
- Discipline: structural.
- Drawing: ST p.4 (GF RS 347, 359, 344) and ST p.5 (1F RS 691, 676, 697, 673, 694, 685, 688, 68E, 679, 667 (DXF
  handles), all S-COL.BON outlines; ST p.9 column schedule bands.
- Conflict: each outline is drawn at one size (e.g. 0.20 x 0.40, 0.25 x 0.50, 0.25 x 1.00) and the schedule band gives
  another; no third print settles it.
- Requested: the built section of each of the 13 columns.
- Affected BOQ line: CONC.COLUMN CONFLICT; with RFI-S19 and GF RS 380 / 1F RS 69A: 15 columns 8.034 .. 10.119 m3.

### RFI-S21 Lift columns and necks on the lift raft (C1, C2, C2, C9)
- Discipline: structural.
- Drawing: ST p.1 columns and axes plan (20X50 three times, 25X100); ST p.2 foundation plan (lift raft); ST p.9 column schedule FOUNDATION row (30 x 50, 30 x 100).
- Conflict: two printed sections.
- Requested: the governing section for these necks and the columns above.
- Affected BOQ line: CONC.COLUMN CONFLICT 0.55 vs 0.75 m3 per metre of height (neck depth also needs the lift-pit depth,
  asked of the lift supplier).

### RFI-S22 Beam B15 (20 x 120) at the water tank: upstand or downstand
- Discipline: structural.
- Drawing: ST p.6 2F roof slab plan (B15 label) and ST p.10 schedule (agree on 20 x 120; no section shows which side of the slab it sits).
- Missing information: upstand or downstand.
- Requested: upstand or downstand.
- Affected BOQ line: CONC.COLUMN, 2F tank-column heights 3.00 .. 3.80 m HELD (+0.160 m3 at the joint).

### RFI-S23 Structural slab-top level of each roof (annex +4.30, GF terraces +5.50, 1F roofs +9.70, main roof +13.90)
- Discipline: structural (with the architect).
- Drawing: architectural P7757 sheet 11, section B-B (+4.30 on one undivided band about 0.23 m on the annex roof);
  sheet 10, section A-A (+13.90 on the main-roof band, +9.70 on the 1F roof, +5.50 below); sheet 04, 1F plan (ROOF +4.30
  annex, +5.50 at the terraces, printed at finished levels); sanitary sheets (1 % falls).
- Missing information: whether each printed level is the structural slab top or the finished roof; whether a roof slab
  steps down from the adjacent floor slab.
- Requested: the structural slab-top level of each roof.
- Affected BOQ lines: CONC.COLUMN (2F columns and annex columns HELD; 3.528 m3 and 3.7125 m3 are on unsupported bases
  and not used); every wall height under a roof (17 rooms PROVISIONAL-DATUM); annex blockwork HELD.

### RFI-S24 Main stair ST-01, winder turn MS1-T (GF, top of the west flight)
- Discipline: structural (with the architect).
- Drawing: ST p.4 (wedge lines 2F6 / 2F4 / 2F5, closing line 2F3, "T 16" tag 580); architectural section A-A (5 risers
  in the turn); architectural GF plan (3 wedges + closing line); ST p.16 typical stair section (no winder shown).
- Conflict / missing: 5 risers on the section vs 3 winders + a closing riser on the plans; riser heights and the soffit
  form under the winders not shown.
- Requested: the riser count and heights in the turn, and the soffit (flat plate at which level, or following the
  winders).
- Affected BOQ line: CONC.STAIR_DOME, MS1-T treads 0.12 .. 0.13 + turn slab 0.2304 .. 0.2496 m3 HELD; stair soffit finish
  under the winders HELD.

### RFI-S25 Main stair, 1F turn riser MS2-TR between the half landings
- Discipline: structural.
- Drawing: ST p.5 (step line 5E2 / S-OPENING 633 between the two half-landing plates).
- Missing information: the level of each half-landing plate and of the turn riser.
- Requested: the two landing levels (or the riser height at the turn).
- Affected BOQ line: CONC.STAIR_DOME, MS2-TR no value (HELD).

### RFI-S26 Entrance flight E1 and stair-hall flight D1: waist slab or steps on fill
- Discipline: structural.
- Drawing: ST p.3 (D1 riser lines 1C4 .. 1C7; E1 riser lines 18A .. 179; no thickness printed); GF slab-on-grade
  "T=10cm"; ST p.16 typical stair section ("THICK." without a value).
- Missing information: how D1 (+0.30 to +1.00) and E1 (+0.15 to +1.00) are built.
- Requested: steps cast on fill over the slab-on-grade, or a self-supporting waist slab (and its thickness).
- Affected BOQ line: CONC.STAIR_DOME, D1 and E1 waists no value (HELD).

### RFI-S27 Round stair ST-02, curved part RS-C: soffit and thickness
- Discipline: structural.
- Drawing: ST p.4 (12 wedge lines 2DF .. 2EA, arcs 2DD / 2DE; "T 16" 5B6 printed on the straight part only); ST p.16.
- Missing information: the soffit form (helicoid slab or other) and thickness of the curved part.
- Requested: the section of the curved part.
- Affected BOQ lines: CONC.STAIR_DOME round stair curved part HELD (2.089 m3 unresolved); stair soffit finish HELD.

### RFI-S28 Tower dome over the 2F maid room
- Discipline: structural (with the architect).
- Drawing: architectural 2F plan (hidden circle, r 2.205, over the maid room); SE elevation (dome cap); ST p.6 (+13.90
  slab drawn as a flat panel B2, bars 7 d10 / 6 d10, no opening, ring or circle); ST p.7 DETAIL OF DOME (one generic
  detail, ring 20 "AS PER ARCH", rise 1.90).
- Conflict: the architecture draws a dome; the structural roof slab is flat with no opening or ring.
- Requested: is there a reinforced-concrete dome over a new opening in the +13.90 slab (opening, trimmer beams or ring,
  shell section), or an architectural cap on the flat slab? If a shell, does the p.7 detail apply (its rise 1.90 vs the
  elevation 2.15)?
- Affected BOQ lines: CONC.STAIR_DOME tower dome HELD (no value); slab opening / ring UNKNOWN; dome finishes HELD.

## Architect

### RFI-A01 Window W02 (6.33 m, GF)
- Discipline: architect.
- Drawing: architectural P7757 sheet 03, GF plan (W02 drawn as one 6.33 m window, '633' on the sea-view side); the client renders show two
  windows with a pier.
- Conflict: one window on the plan, two windows with a pier on the renders (renders are design intent only).
- Requested: the built arrangement (one window, or two with a pier and the pier width).
- Affected BOQ lines: windows (aluminium) W02 1 .. 2 pcs, its m2 HELD (rest of the line 76.256 m2 + W17 9.870 m2
  measured); plaster / paint and exterior plaster nets at W02 HELD.

### RFI-A02 Pool access (steps, bench or ladder)
- Discipline: architect (structural if cast in concrete).
- Drawing: architectural GF plan; ST p.7 pool detail; sections: no step, bench or ladder drawn.
- Missing information: how the pool is entered.
- Requested: confirm there is no built-in access, or provide its drawing (steps / bench in concrete, or a ladder).
- Affected BOQ line: CONC.POOL (base and walls measured; access element HELD).

### RFI-A03 Round reception stair ST-02: section, riser count and landing levels
- Discipline: architect.
- Drawing: architectural P7757 sheet 03 (GF plan) and sheet 04 (1F plan) (round stair drawn); sections A-A (sheet 10)
  and B-B (sheet 11) show no curved flight.
- Missing information: riser count, landing levels, curved geometry.
- Requested: a section (or riser count and landing levels).
- Affected BOQ line: CONC.STAIR_DOME, round stair HELD (curved part 2.089 m3 unresolved; straight flights 0.469 m3 to be
  confirmed).

### RFI-A04 Main stair MS1-L: riser count and landing edge
- Discipline: architect (with the structural designer).
- Drawing: ST p.4 stair linework for MS1-L vs architectural P7757 sheet 03 (GF plan) and sheet 10 (section A-A).
- Conflict: the two disciplines' linework differ on the riser count and the landing edge.
- Requested: the built riser count and landing edge.
- Affected BOQ line: CONC.STAIR_DOME, MS1-L HELD (staircase system PARTIALLY VERIFIED); ST-03 0.948 m3 is on an
  unsupported basis and not used.

### RFI-A05 Terrace dome drums on the +9.70 roof: material and wall thickness
- Discipline: architect (structural if concrete).
- Drawing: architectural P7757 sheet 11, section B-B ("130" above the +9.70 roof beside each drum); ST p.5 ring arcs
  5FE / 5FF, circle 649; sheet 04, 1F plan ("VOID").
- Missing information: material and wall thickness of the two drums (to the springing +11.00).
- Requested: material (concrete or blockwork) and thickness.
- Affected BOQ lines: CONC.STAIR_DOME drums no value (outer face 18.061 m2 each, geometry only); blockwork HELD.

### RFI-A06 GF garden band (13.986 m2)
- Discipline: architect.
- Drawing: architectural P7757 sheet 03, GF plan (band labelled GARDEN, 150 wide, west of the reception, drawn enclosed
  and roofed).
- Missing information: open to the sky or roofed; enclosed or open to outside air; planter (soil) or paved / tiled floor.
- Requested: the band's built form and floor.
- Affected BOQ line: floor area (internal) 1.364 m2 HELD; floor finish HELD.

### RFI-A07 Space under the round stair ST-02 (GF, F1 / F2)
- Discipline: architect.
- Drawing: architectural P7757 sheet 03, GF plan (space under ST-02; ST-02 underside not drawn).
- Missing information: whether the space under the stair is a finished floor, closed off, or solid.
- Requested: finished floor / closed / solid.
- Affected BOQ line: floor area (internal) 6.124 m2 HELD.

### RFI-A08 1F unlabelled space beside the master bedroom: use and floor finish
- Discipline: architect.
- Drawing: architectural P7757 sheet 04, 1F plan: the unlabelled 1.65 x 1.80 m space (2.970 m2) between the bath
  (2.00 x 1.80) and the master bed room (4.20 x 4.00) on the upper-neighbour side, a diagonal line drawn across it; no
  room name is printed and no finishes schedule is issued (D-10).
- Missing information: the use of the space and its floor finish.
- Requested: the use of the space and its floor finish material.
- Affected BOQ line: floor finish of this space HELD (area 2.970 m2 measured).

### RFI-A09 Document set covering the finishes (if one exists)
- Not asked here: the general request for a finishes schedule / specification is in B (A12 / D-10). RFI-A08 is the one
  item of it that closes a whole line.

---

## Rows queued for B_REMAINING_RFI.md (next Lead run; drafted only as a list here)

Reinforcement (no RFI alone closes the line: lap lengths T-273 internal): S9 bar ends of ground beams / straps / footings
/ SB2 row; S10 slab top-bar extent and bar-less panels; S11 pool bar population (D-57); S12 planted columns; S19 side bars
"2ø12/30cm" (width class or spacing; total or per face); S20 nested links; S21 beam bar ends / link hooks / note 9 scope
(owner 2026-10-29: only drawn bar parts are counted; this asks the designer what is drawn nowhere); S22 stair-beam crank,
planted-column extra bars. Blockwork: S14 lift-wall tie beam section (pit depth -> lift supplier); S16 black block
"above"; S17 walls containing columns; A4 W03 / W17 heads vs beams; A5 annex datum part (with RFI-S23); A7 partitions
under the dome openings; A10 D-GF-06 / P-1F-01 heads; NEW: SHARMAT wall-to-column restraint (owner 2026-10-29: Urban
counts ties as an optional estimating item; ask only whether the structure requires a wall-to-column restraint and, if
so, its specification; never presented as our design). Finishes / ceilings: A1 ceiling levels, A2 door / window schedule,
A5 roof build-up, A7 dome openings, A8 soffits, A12 schedules not issued (incl. tile sizes D-10), A13 external sills and
coping material. Other: S13 sunken-panel drop, A3 main door and SX-01, A9 D-55 level changes and the side passage, A11
sea-side element. Document control (not a design question): S18 issue date and revision per structural sheet.
Lift supplier (to CLARIFICATIONS_SUPPLIER, not the structural designer): lift-pit depth (S14 / D-43); landing door
heads L-GF-01 / L-1F-01 / L-2F-01.

---

## Checker citation verdicts (Verifier 2026-10-30 ~01:30 UTC; owner 2026-10-29 22:05 (3) light run)

Sources read this run (Drive, Alsenan chalet project, read-only, decoded into .work/private): 'ST7757.pdf' (16 pages
rendered; the print has no text layer, pages read as images), 'ST7757 dxf.dxf' (handles and texts by position),
'p7757_arch_sheet03.pdf'. ST page map, from the printed sheet titles and the DXF frame positions: p.1 columns and axes
plan (x about 157 .. 190 k); p.2 foundations (119 .. 151 k); p.3 ground beams / tie beams (81 .. 113 k); p.4 GF roof slab
(43 .. 75 k); p.5 1F roof slab (5 .. 37 k); p.6 2F roof slab (-33 .. -1 k); p.7 pool and dome details; p.8
recommendations; p.9 schedules of columns and footings + general notes box; p.10 schedule of simple beams (incl. B.W, SB1
.. SB3); p.11 / p.12 continuous-beam schedules; p.13 footing / ground-beam / lintel details; p.14 lift, boundary wall,
parapets; p.15 column details; p.16 stair details. Architectural P7757 sheet 03 = GROUND FLOOR PLAN 1:100. No quantity,
status or V2.9 cell changed by these verdicts.

- RFI-S01: CORRECTED: the 1.50 m note is ST p.9 general note 1 (notes box under the bearing-capacity table: excavation
  level not less than 1.5 m below the existing plot level), NOT p.1 (p.1 notes: slab 16 cm, neighbour-side tie beams,
  striking 21 days). p.13 footing detail (10 cm plain concrete, membrane, 5 cm screed, 10 cm projection), p.2 and p.9
  column schedule: OK.
- RFI-S02: CITATION OK: p.2 open outline 1B1B 3.25 x 1.40 with tag F10 (text at 147842, 36930) and F; p.9 F10 280 x 140
  x 50, F 90 x 80 x 30.
- RFI-S03: CITATION OK: p.10 B.W 20 x 60; p.14 TYPICAL BOUNDARY WALL G.B 20 x 40 and 'AS PER EXCAVATION DEPTH BELOW N.G.
  LEVEL'; p.1 note 2 (neighbour-side tie beams above and below the black block from foundation level). 91.94 / 21.45 m
  not re-measured.
- RFI-S04: CORRECTED: '(sheet no. to confirm)' -> architectural P7757 sheet 03 (GROUND FLOOR PLAN 1:100); p.14 pads
  (130x80x30) and 'SEE ARCH PLAN': OK; sheet 03 marks no boundary-wall column at the printed scale.
- RFI-S05: CITATION OK: p.10 SB3 50 x 40; p.2 (SB3 into F3).
- RFI-S06: CITATION OK: p.13 projection 10; p.2: own check, 8 footings with a face on the plot line (south F11, F14,
  F15, F x 2 incl. the corner F; west F; east F8, FN).
- RFI-S07: CITATION OK: p.13 shows blinding under the footing and the ground-beam sections, no strap section.
- RFI-S08: CITATION OK: p.14 DETAIL OF LIFT WITH ISOLATED FOOTING prints '10cm Plain con.' with no projection dimension.
- RFI-S09: CITATION OK: p.13 'Ground Beams for exterior walls' with 'FOLLOW ARCH.' and 'Outer Normal ground level'.
- RFI-S10: CITATION OK: p.13 section titles read 'without concentrated load'; the 15 loaded spans were not recounted.
- RFI-S11: CITATION OK: p.13 titles 'More than 5m', 'Less than 5m', 'Less than 2.5m length'.
- RFI-S12: CORRECTED: name the sheet: the CB10 labels are in the ST p.5 frame (1F roof slab plan), not 'roof slab plan'
  unspecified; p.11 / p.12 schedule row not re-read.
- RFI-S13: CORRECTED (sheet names): GF B29 / CB2 / B21 on ST p.4, 1F B6 on ST p.5; p.10 widths B29 25, B21 45, B6 25
  confirmed; CB2 (p.11 / p.12) not re-read.
- RFI-S14: CORRECTED (sheet name): ST p.4 (labels CB3, B3 and '(With Stair)' on the south line, y about 37.45 .. 38.13 m);
  p.16 not re-read.
- RFI-S15: CORRECTED: '(sheet no. to confirm)' -> ST p.4 (GF roof slab) and ST p.5 (1F roof slab); the six handles were
  not re-checked this run.
- RFI-S16: CORRECTED (sheet names): ST p.4 / p.5.
- RFI-S17: CITATION OK: ST p.5: circle 649 r 2.211 and arcs 64A .. 64D r 2.411 at (30.828, 41.651), 'SEE DETAIL' texts,
  west ring B4 texts; p.7 DETAIL OF DOME.
- RFI-S18: CORRECTED (sheet names): ST p.4 / p.5; the Arabic 'slab note 1' on parapets / projections was NOT found on
  p.1 (whose note 1 is the 16 cm slab): its sheet stays to confirm.
- RFI-S19: CORRECTED: '30X80' is printed on ST p.1 (columns and axes plan, two C8 positions), not on the storey slab
  plans; p.9 C8 30 x 90 (FOUNDATION) confirmed.
- RFI-S20: CITATION OK, sheet names to add: GF RS 347 / 359 / 344 / 380 in the ST p.4 frame, 1F RS 691 .. 667 / 69A in
  the ST p.5 frame (all S-COL.BON outlines).
- RFI-S21: CORRECTED: '20X50' (three) and '25X100' are printed on ST p.1 (columns and axes plan), not p.2; p.9
  FOUNDATION C1 / C2 30 x 50, C9 30 x 100 confirmed.
- RFI-S22: CORRECTED (sheet name): the B15 label is on ST p.6 (2F roof slab plan); p.10 B15 20 x 120 confirmed.
- RFI-S23: NOT CHECKED this run (architectural sections and roof plans: sheet numbers not cited, not opened).
- RFI-S24: CITATION OK: ST p.4: LINEs 2F6 / 2F4 / 2F5 / 2F3 and INSERT 580 in the p.4 frame; architectural sheets not
  opened.
- RFI-S25: CITATION OK: ST p.5: LINE 5E2 and S-OPENING LINE 633.
- RFI-S26: CITATION OK: ST p.3: LINEs 1C4 .. 1C7 (D1) and 18A .. 179 (E1) in the p.3 frame.
- RFI-S27: CITATION OK: ST p.4: LINEs 2DF .. 2EA, S-OPENING arcs 2DD / 2DE, INSERT 5B6.
- RFI-S28: CITATION OK for ST p.6 / p.7 sheet identity; the p.6 panel B2 bar text not re-read; architectural sheets not
  opened.
- RFI-A01: CORRECTED: '(sheet no. to confirm)' -> P7757 sheet 03 (GF plan; '633' on the sea-view side).
- RFI-A02: CITATION OK: sheet 03 pool (no step drawn at 1:100) and ST p.7 pool detail.
- RFI-A03: PARTIAL: GF = sheet 03 (round stair drawn); the 1F plan and sections A-A / B-B sheet numbers not checked.
- RFI-A04: PARTIAL: ST linework = p.4; architectural sheet numbers not cited, not checked.
- RFI-A05: CITATION OK for ST p.5 (arcs 5FE / 5FF = west ring, circle 649 = east ring); section B-B sheet not checked.
- RFI-A06: CORRECTED: '(sheet no. to confirm)' -> P7757 sheet 03 (band 'GARDEN', 150 wide, west of the reception).
- RFI-A07: CITATION OK: sheet 03 (space under the round stair).
- RFI-A08: NOT CHECKED this run (1F plan not opened).
Totals: 36 questions (A09 is a pointer, not counted): CITATION OK 19, CORRECTED 13, PARTIAL 2, NOT CHECKED 2 (S23, A08); 0 WRONG
beyond the corrections. The Lead applies the corrections in the question text (S01, S19, S21 change a page number).

### Addendum: the 2 NOT CHECKED + 3 PARTIAL items (Verifier 2026-10-30 ~03:56 UTC, run session_01E6cPnbD7nsBT15vQKR9kA7)

Sources read this run (Drive, Alsenan chalet project, read-only, decoded into .work/private; raster prints read as
images): 'p7757_arch_sheet04.pdf' (= 1st FLOOR PLAN 1:100), 'p7757_arch_sheet10.pdf' (= SECTION A-A 1:100),
'Alsenan_Architectural_P7757_Pages_11-12.pdf' p.1 (= sheet 11, SECTION B-B 1:100). No quantity, status or V2.9 cell changed.

- RFI-S23: CITATION OK, sheet numbers to add: section B-B = sheet 11 (annex +4.30 on the annex roof; drums '130' above
  +9.70); section A-A = sheet 10 (+13.90 on the main-roof band, +9.70 on the 1F roof, +5.50 below); 1F plan sheet 04 prints
  ROOF +4.30 (annex) and +5.50 at the terraces. The 'about 0.23 m undivided band' at +4.30 was not measured this run.
- RFI-A08: CORRECTED: the 1F plan is sheet 04, and it prints NO room name at this space: the room is the unlabelled
  1.65 x 1.80 m space (= 2.970 m2, matching the engine's typed 'dressing' ARCH.SPACE) between the bath 2.00 x 1.80 and the
  master bed room 4.20 x 4.00 on the upper-neighbour side, with a diagonal line drawn across it. 'Dressing room' is our
  label, not the architect's: the question must identify the space by position and dimensions and ask its USE and floor
  finish (the internal name is not a drawing fact).
- RFI-A03: CITATION OK: GF sheet 03 and 1F sheet 04 both draw the round stair; sections A-A (sheet 10) and B-B (sheet 11)
  show no curved flight, as the question says.
- RFI-A04: CORRECTED (sheet numbers): architectural GF plan sheet 03, section A-A sheet 10 (the main stair flights are cut
  there); ST linework p.4 as before. The riser count conflict itself was not recounted this run.
- RFI-A05: (was OK for ST p.5, B-B now checked) CITATION OK: section B-B = sheet 11, '130' printed above the +9.70 roof beside each drum; 1F plan sheet 04
  prints 'VOID' (the sea-side round void).
Updated totals: CITATION OK 21, CORRECTED 15, PARTIAL 0, NOT CHECKED 0 (36 questions + A09 pointer); 0 WRONG. Lead: apply
A08 (identify the space by position, ask use + finish) and the sheet numbers above in the question text.
