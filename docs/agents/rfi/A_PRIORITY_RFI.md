# A. Priority RFIs, Alsenan chalet (DRAFT, NOT TO BE SENT; owner 2026-10-29 22:05)

Prepared by the Lead 2026-10-30 00:15-00:25 UTC (run started 00:13) from CLARIFICATIONS_CONSULTANT_2026-10-24.md,
revalidated against the merged, Checker-verified evidence up to engine head b12e10de (T-352) and the board at d04da3be.
Companion files: D_REMOVED_REVISED.md (what was removed or changed, with evidence), C_UNLOCK_MATRIX.md (internal: which
questions together close each whole BOQ line), B_REMAINING_RFI.md (next Lead run: the remaining questions).

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
- Drawing: ST p.1 general note 1 ("excavation not less than 1.50 m below the existing plot level"); ST p.13 blinding /
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
- Drawing: ST p.14 TYPICAL BOUNDARY WALL (pads 130 x 80 x 30, spacing "SEE ARCH PLAN"); architectural GF plan (boundary
  wall drawn 0.20; no column positions marked) (sheet no. to confirm).
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
- Drawing: ST roof slab plan (CB10 drawn 0.30 wide; the CB10 label sits beside the 0.20 outer strip); ST p.11 / p.12
  continuous-beam schedule (CB10 0.25 x 0.50).
- Conflict: schedule width 0.25 vs drawn width 0.30, and the label placement leaves it unclear which band is CB10.
- Requested: which band is CB10, and its width.
- Affected BOQ line: CONC.BEAM, CB10 CONFLICT 0.744 / 0.893 m3 (part of the 7-run CONFLICT below).

### RFI-S13 Beams whose drawn width differs from the schedule (GF B29, GF CB2 two spans, GF B21, 1F B6 one span)
- Discipline: structural.
- Drawing: ST GF and 1F roof slab plans (two edge lines per beam) vs ST p.10 / p.11 schedules: GF B29 schedule 25 / drawn
  0.20 (6.74 m); GF CB2 two spans 20 / 0.25; GF B21 45 / 0.40 (inclined); 1F B6 vertical span at x 26.37, 25 / 0.20.
- Conflict: schedule width vs drawn width; no section cuts these beams.
- Requested: the built width of each listed span.
- Affected BOQ line: CONC.BEAM, 7 runs CONFLICT (with RFI-S12): drawn 5.4421 vs scheduled 5.7665 m3; beam soffit 8.7140
  vs 9.0072 m2.

### RFI-S14 GF beam line labelled both CB3 and "B3 (with stair)"
- Discipline: structural.
- Drawing: ST GF roof slab plan (two labels on one beam line); ST p.16 TYPICAL DETAIL OF STAIR BEAM.
- Conflict: two type labels on one line.
- Requested: one beam of which type, or two members (and their positions).
- Affected BOQ line: CONC.BEAM HELD (never counted twice).

### RFI-S15 Six unlabelled beam spans
- Discipline: structural.
- Drawing: ST GF / 1F roof slab plans (six drawn spans without a label) (handles in the T-110 ledger; sheet no. to confirm).
- Missing information: type and section.
- Requested: the type or section of each span.
- Affected BOQ line: CONC.BEAM HELD (location, length and candidate volume listed).

### RFI-S16 Edge strips and boxes without a section (west outer strip, SE box, CB12 outer strip, strips north of B23 / B20)
- Discipline: structural.
- Drawing: ST GF / 1F roof slab plans (drawn bands; sections incomplete).
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
- Drawing: ST GF and 1F roof slab plans (rounded bands round the roof edges: 0.20 strips north of B20 / B23; 1F outer
  west strip 7.50 m; 1F strip 0.30 x 4.51 and SE box 0.30 x 0.90 outside CB12; GF outer west strip 0.20 x 4.10 m; 1F
  0.10 strip outside CB12 over 5.69 m; 1F rounded box about 0.40 x 1.00 m); slab note 1 (Arabic: the contractor matches
  parapet and projection details to the architectural drawings); sections A-A / B-B draw the beam outline only.
- Missing information: depth, section and material of each projection; cast with the slab or not.
- Requested: a section for each projection (or one typical section and where it applies).
- Affected BOQ lines: CONC.BEAM HELD (plan areas listed, no volume); facade finishes on the projection faces.

### RFI-S19 Column C8: section
- Discipline: structural.
- Drawing: ST storey plans (C8 printed 30X80, dimensioned 70 + 10; five 0.80 outlines); ST p.9 column schedule (30 x 90).
- Conflict: plan 30 x 80 vs schedule 30 x 90.
- Requested: the built section of C8 (neck, GF, 1F).
- Affected BOQ line: CONC.COLUMN CONFLICT (neck 0.240 .. 0.270 m2 section; GF 0.900 .. 1.0125 m3; 1F 0.180 .. 0.200 m2
  section).

### RFI-S20 Thirteen columns whose plan outline differs from the schedule
- Discipline: structural.
- Drawing: ST storey plans, outlines GF RS 347, 359, 344; 1F RS 691, 676, 697, 673, 694, 685, 688, 68E, 679, 667 (DXF
  handles); ST p.9 column schedule bands.
- Conflict: each outline is drawn at one size (e.g. 0.20 x 0.40, 0.25 x 0.50, 0.25 x 1.00) and the schedule band gives
  another; no third print settles it.
- Requested: the built section of each of the 13 columns.
- Affected BOQ line: CONC.COLUMN CONFLICT; with RFI-S19 and GF RS 380 / 1F RS 69A: 15 columns 8.034 .. 10.119 m3.

### RFI-S21 Lift columns and necks on the lift raft (C1, C2, C2, C9)
- Discipline: structural.
- Drawing: ST p.2 foundation plan (20X50 three times, 25X100); ST p.9 column schedule FOUNDATION row (30 x 50, 30 x 100).
- Conflict: two printed sections.
- Requested: the governing section for these necks and the columns above.
- Affected BOQ line: CONC.COLUMN CONFLICT 0.55 vs 0.75 m3 per metre of height (neck depth also needs the lift-pit depth,
  asked of the lift supplier).

### RFI-S22 Beam B15 (20 x 120) at the water tank: upstand or downstand
- Discipline: structural.
- Drawing: ST slab plan and ST p.10 schedule (agree on 20 x 120; no section shows which side of the slab it sits).
- Missing information: upstand or downstand.
- Requested: upstand or downstand.
- Affected BOQ line: CONC.COLUMN, 2F tank-column heights 3.00 .. 3.80 m HELD (+0.160 m3 at the joint).

### RFI-S23 Structural slab-top level of each roof (annex +4.30, GF terraces +5.50, 1F roofs +9.70, main roof +13.90)
- Discipline: structural (with the architect).
- Drawing: architectural section B-B (+4.30 on one undivided band about 0.23 m); section A-A (+13.90 on the roof band);
  architectural plans (roof terraces printed at finished levels); sanitary sheets (1 % falls).
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
- Drawing: architectural GF plan (W02 drawn as one 6.33 m window) (sheet no. to confirm); the client renders show two
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
- Drawing: architectural GF / 1F plans (round stair drawn); sections A-A / B-B do not cut it.
- Missing information: riser count, landing levels, curved geometry.
- Requested: a section (or riser count and landing levels).
- Affected BOQ line: CONC.STAIR_DOME, round stair HELD (curved part 2.089 m3 unresolved; straight flights 0.469 m3 to be
  confirmed).

### RFI-A04 Main stair MS1-L: riser count and landing edge
- Discipline: architect (with the structural designer).
- Drawing: ST stair linework for MS1-L vs architectural plan and section A-A.
- Conflict: the two disciplines' linework differ on the riser count and the landing edge.
- Requested: the built riser count and landing edge.
- Affected BOQ line: CONC.STAIR_DOME, MS1-L HELD (staircase system PARTIALLY VERIFIED); ST-03 0.948 m3 is on an
  unsupported basis and not used.

### RFI-A05 Terrace dome drums on the +9.70 roof: material and wall thickness
- Discipline: architect (structural if concrete).
- Drawing: architectural section B-B (drum "130"); ST p.5 ring arcs 5FE / 5FF, circle 649; architectural 1F plan
  ("VOID").
- Missing information: material and wall thickness of the two drums (to the springing +11.00).
- Requested: material (concrete or blockwork) and thickness.
- Affected BOQ lines: CONC.STAIR_DOME drums no value (outer face 18.061 m2 each, geometry only); blockwork HELD.

### RFI-A06 GF garden band (13.986 m2)
- Discipline: architect.
- Drawing: architectural GF plan (band labelled garden, drawn enclosed and roofed) (sheet no. to confirm).
- Missing information: open to the sky or roofed; enclosed or open to outside air; planter (soil) or paved / tiled floor.
- Requested: the band's built form and floor.
- Affected BOQ line: floor area (internal) 1.364 m2 HELD; floor finish HELD.

### RFI-A07 Space under the round stair ST-02 (GF, F1 / F2)
- Discipline: architect.
- Drawing: architectural GF plan (space under ST-02; ST-02 underside not drawn).
- Missing information: whether the space under the stair is a finished floor, closed off, or solid.
- Requested: finished floor / closed / solid.
- Affected BOQ line: floor area (internal) 6.124 m2 HELD.

### RFI-A08 1F dressing room: floor finish
- Discipline: architect.
- Drawing: architectural 1F plan; no finishes schedule is issued (D-10).
- Missing information: the floor finish of the dressing room.
- Requested: the finish material.
- Affected BOQ line: floor finish of the dressing room HELD (area measured).

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
