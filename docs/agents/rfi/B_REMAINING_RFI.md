# B. Remaining RFIs, Alsenan chalet (DRAFT, NOT TO BE SENT; owner 2026-10-29 22:05)

Prepared by the Lead 2026-10-30 04:15-04:25 UTC (run session_01E6cPnckUhqJQdZyhEFoLeU) from
CLARIFICATIONS_CONSULTANT_2026-10-24.md section 0.2 and the list at the end of A_PRIORITY_RFI.md, revalidated against
the merged, Checker-verified evidence up to engine head 90135e91 (T-357) and candidate of record ARCH_TAKEOFF_V3.0.25.
Companion files: A_PRIORITY_RFI.md (the 36 questions that close whole lines), C_UNLOCK_MATRIX.md (internal),
D_REMOVED_REVISED.md (removals and changes, with evidence).

STATUS: NOT SENT. The owner reviews; nothing goes to any designer until he says so. CHECKER (light run): re-check the
sheet / detail citation of every question below against the print, one verdict line per question at the end of this
file (CITATION OK / CORRECTED <to> / WRONG <why>), exactly as for A. No quantity, status or V2.9 cell changes.

WHY THESE ARE "REMAINING": none of them, answered alone, closes a whole BOQ line (reinforcement also waits on the
internal lap work, blockwork on internal held pieces). They are real, unresolved designer matters; they stay in the
package so one reply can settle them together with A.

HOW TO READ A QUESTION: as in A. "Options the drawings allow" are what the issued prints themselves permit, never our
design. Until an answer arrives every affected quantity stays HELD or CONFLICT, visible, never 0. No owner decision is
reopened: where an owner decision already governs our counting (Q-55 door height, Q-71 links, option B slab bar ends,
Q-77 mesh / sharmat), the question asks only for the designer's drawing information, never for our convention.

Quantity figures are the held ranges recorded when each item was raised (CLARIFICATIONS 2026-10-24 / 25) unless a newer
merged task is named; they are for the owner's review of impact and are NOT part of the text sent to a designer.

Count: 26 questions (structural 13 incl. the wall-to-column restraint, document control 1, architect 12) + 2 lift-supplier
items + 1 client item. Sheet numbers not yet confirmed by a merged task are written as drawing names only (the Checker
adds them in its citation run).

---

## Structural designer: reinforcement

### RFI-B-S09 Bar ends and links of ground beams, straps, footings and the SB2 row
- Drawing: ST p.8 recommendation note 9 (development 70 d tension / 40 d compression; the zone is not stated); ST p.9
  footing schedule; ST p.10 SB2 row (the DXF also carries an SB2 insert outside the sheet frames).
- Missing information: the end zone and end shape (hook / leg) of ground-beam and strap bars; the top-bar ends of
  F8 / F12 / F13 / F14 / FF; which SB2 row governs.
- Requested: the bar-end detail (or a stated length per end) for these members, and the governing SB2 row.
- Internal impact (not sent): ground-beam ends 383.00 .. 670.26 kg; straps 76.11 .. 133.20 kg; SB2 127.96 kg; footing top
  layers 2,742.51 .. 2,836.40 kg (footing steel HELD, owner 2026-10-25 13:16). Our counting of drawn bar parts follows
  the owner's option B (2026-10-29 21:22); this asks only what is drawn nowhere.

### RFI-B-S10 Slab top bars over supports, bar-less panels and the tank slab
- Drawing: ST p.4 / p.5 / p.6 slab plans, note 2 ("one third of the span", printed in the notes box of p.4, p.5 AND
  p.6); ST p.15 TYP. SLAB ON BEAMS DETAIL ('.30 L1 OR .30 L2 WHICHEVER LARGER' / '.25 L1'); the tank-slab reinforcement on
  ST p.6 (2F roof slab, 'WATER TANK PLACE': '7ø14/m (T&B)' and '6ø12/m (T&B)', slab T18). [Lead 2026-10-30 12:40:
  corrected per the Checker's citation verdict: there is no p.7 tank detail.]
- Conflict / missing: two printed rules for the top-bar extent; the GF-126 zone is not delimited; 13 panels print no
  bars; note 2 vs the tank slab's top-and-bottom mesh, both on ST p.6.
- Requested: which rule governs the top-bar extent; the bars of each unprinted panel (or confirmation that none are
  required); the tank-slab reinforcement.
- Internal impact: top over supports 752.73 .. 1,931.52 kg; GF-126 7.89 .. 19.55 kg; 13 panels HELD; tank 28.66 .. 70.61 kg.

### RFI-B-S11 Pool floor bar population
- Drawing: ST p.7 pool detail (two zones R1 / R2 with a slope and a step); the owner's flat-floor decision Q-26 A (1.15 m)
  governs the concrete.
- Missing information: which bar population belongs to the flat floor that is built.
- Requested: the floor and wall reinforcement of the pool as built flat at 1.15 m.
- Internal impact: pool steel R1 888.90 .. 927.54 / R2 615.34 .. 639.45 kg. (Pool access is asked in A, RFI-A02.)

### RFI-B-S12 Three planted columns: link applicability, bar ends, anchorage and laps
- Drawing: planted-column tags ST p.4 'P.C 20x70 / 10ø16' (on B27), 'P.C 20x50 / 8ø16' (on B26); ST p.5 'P.C 20x50 / 8ø16'
  (on B19); ST p.9 DETAILS OF COLUMN REINFORCEMENT '* ST. OF COLUMN- 6ø8/m' (DXF 1BAA); ST p.15 BEAM CARRYING PLANTED COL.
  DETAIL (column bars entering the beam, 100 cm shown; no link, anchorage or lap note).
- Missing information: whether the general column-link note on p.9 applies to the planted columns (not assumed); the bar
  ends, anchorage into the supporting beam and laps of the planted-column bars.
- Requested: confirmation that the p.9 link note applies to the three planted columns (or their links); their bar ends,
  anchorage and lap requirements.
- Internal impact: main bars printed; links HELD until the applicability is confirmed; bar lengths HELD. [main chat
  2026-10-31, owner instruction: narrowed to applicability, bar ends, anchorage and laps.]

### RFI-B-S19 Beam side bars "2ø12/30cm"
- Drawing: ST p.10 Schedule of Simple Beams remarks: 2ø12/30cm (B7 .. B15, B17, B18, B20 .. B25, B28, B29), 2ø14/20cm
  (B19), 2ø16/20cm (B16, B26, B27); ST p.11 / p.12 continuous beams "MIDDLE REINT. 2ø12/30cm" (CB1, CB3, CB6, CB7, CB8,
  CB11, CB12); ST p.8 note 21 (2 / 3 / 4 ø12 side bars in beams deeper than 60 cm according to the beam width, unless
  stated otherwise).
- Missing information: whether "/30cm" is a beam-width class or a vertical spacing, and whether the count is in total or
  per face; how note 21 and the remarks combine.
- Requested, in one reply: (a) width class or spacing; (b) total or per face.
- Internal impact: side bars HELD, at least 0.362 t on released members.

### RFI-B-S20 Nested links
- Drawing: ST p.10 link symbol with two nested links on B17, B19 .. B26 (B18 none); the SB1 and SB3 rows also print a
  two-link symbol and the SB2 row a three-link symbol, no size. [Lead 2026-10-30 12:40: addition per the Checker.]
- Missing information: the inner link's size, legs and position.
- Requested: the inner-link dimensions and leg arrangement per beam.
- Internal impact: links HELD 2.035 .. 2.199 t (the active count takes one perimeter link only).

### RFI-B-S21 Superstructure beam bar ends, anchorage and link closure
- Drawing: ST p.8 note 9 (written for starter bars); ST p.11 / p.12 typical details (0.22 Ln support bars; first link
  7.5 cm from the face); no hook or end detail for beam bars or links.
- Missing information: whether note 9 governs beam bar anchorage into supports and laps; the end shape of top / bottom
  bars at end supports; the link hook type and length.
- Requested: the anchorage / end detail of beam bars and the link closure detail.
- Internal impact: beam bar ends HELD 1.61 .. 2.82 t (40 d .. 70 d); link hooks unquantified. Only drawn bar parts are
  counted meanwhile (owner option B, 2026-10-29).

### RFI-B-S22 Stair beam crank and planted-column extra bars
- Drawing: ST p.16 TYPICAL DETAIL OF STAIR BEAM (cranked profile, 'AS PER SCH.', no crank dimension) for B3 "(With
  Stair)" on ST p.4 (twice) / p.5 (once); ST p.15 BEAM CARRYING PLANTED COL. DETAIL, label '4ø16', with a 'DEPTH'
  dimension drawn beyond the column face on each side, governing THREE beams: B26 and B27 (ST p.4) and B19 (ST p.5).
- Requested: the crank dimensions; confirmation that the 4ø16 length is the column width + 2 x the beam depth (as drawn)
  and the end anchorage of those bars. [Lead 2026-10-30 12:40: corrected per the Checker's verdict: third beam B19; the
  extent IS drawn symbolically; 'EXTRA' is printed only on the twisted-column details.]
- Internal impact: stair beams HELD_DEFINED 20.25 kg each (plan-length lower bound); planted-column extra unquantified.

## Structural designer: blockwork, slabs and restraint

### RFI-B-S13 Sunken slab panels: depth of the drop
- Drawing: ST p.4 (GF ROOF SLAB = 1F floor: 5 hatched 'Sunken slab' panels, 19.3964 m2) and ST p.5 (1F ROOF SLAB = 2F
  floor: 1 panel between the two B2 west of B3 (With Stair), 5.400 m2); ST p.6 draws none. [Lead 2026-10-30 12:40:
  sheets corrected per the Checker's verdict, 'p.5 / p.6' -> 'p.4 / p.5'.]
- Missing information: the drop is not printed.
- Requested: the drop of each panel, and whether the tops of the two shared beams drop with the panels.
- Internal impact: slab concrete UNAFFECTED (60.2804 m3 for any drop); HELD per metre of drop: beam tops 3.006 .. 3.036 m3,
  riser formwork 41.451 m2, fill / screed 24.79 m3, WP upturn 41.451 m2, 7.913 m of GF wall height.

### RFI-B-S14 GF lift-wall tie beam
- Drawing: ST p.8 recommendation note 19 (tie beam at 3.00 m); ST p.14 lift details.
- Missing information: the tie-beam section.
- Requested: the section (and bars) of the lift-wall tie beam.
- Internal impact: lift block walls 43.37 m2 gross HELD; tie-beam concrete HELD. (The pit depth is a lift-supplier item,
  below.)

### RFI-B-S16 Black block on the neighbour-side ground beams
- Drawing: ST p.1 notes box, note 2 (black block above and below the neighbour-side tie beams, built from foundation
  level).
- Missing information: how far "above" reaches.
- Requested: up to the GF slab only, or the whole GF wall / fence height.
- Internal impact: 26.37 m of GF wall + 31.17 m of north fence, block type PROVISIONAL.

### RFI-B-S17 Walls that contain a column
- Drawing: ST p.8 recommendation 20 (wall built at the column thickness) vs the architectural plans (GF sheet 03, 1F sheet 04, 2F plan)
  printing 0.15 / 0.20 walls.
- Requested: the wall thickness where a column sits inside the wall.
- Internal impact: block m3 on 19 rows 23.407 .. 31.737 m3.

### RFI-B-SH Wall-to-column restraint (block walls against columns)
- Drawing: no sheet of the structural set (ST p.1 .. p.16 notes and details searched by the merged masonry-accessory
  task) prints a wall-to-column tie, restraint or connection detail.
- Missing information: whether the structure requires a restraint between block walls and the columns they abut, and if
  so its specification (type, size, spacing).
- Requested: is a wall-to-column restraint required; if yes, its specification.
- Internal note (not sent): Urban counts sharmat ties as a separate optional estimating item (owner Q-77, 2026-10-29);
  182 ties at the 31 measured junctions, specification HELD. The question asks only for the structural requirement and
  never presents our item as a design.

## Structural designer: document control

### RFI-B-S18 Issue and revision of the structural set
- Drawing: title-block DATE box: ST p.1 .. p.7 May 06, 2025; p.9, p.10, p.13 .. p.16 May 06, 2026; p.11 / p.12 without a
  title block (schedule frames 'Ref. S-2' / 'S-3' only); p.8 (RECOMMENDATIONS) has a header block without a date field.
  Every page carries the plot stamp '... May 06, 2026 - 12:04pm', p.1 .. p.7 from 'ST7757.dwg' and p.8 .. p.16 from
  'T7757.dwg' (two source drawings). [Lead 2026-10-30 12:40: corrected per the Checker's verdict.]
- Missing information: which date is the issue; whether p.8 and the beam schedules p.11 / p.12 belong to the same issue;
  the revision of each sheet; which of the two source drawings is the issue of record.
- Requested: the issue date and revision per sheet, and which source drawing (ST7757 / T7757) is of record (a
  document-control confirmation, not a design question).
- Internal impact: no quantity held; it defines the revision set every BOQ line is bound to (stated UNCONFIRMED in the
  export until answered).

---

## Architect

### RFI-B-A01 Ceiling levels and ceiling types
- Drawing: no reflected ceiling plan or ceiling section is issued; P7757 sheets 10 / 11 (sections A-A / B-B) print levels
  only.
- Missing information: the ceiling level per room; ceiling types, coves and drops (drop heights over 47.00 m of
  openings); the board type in wet rooms.
- Requested: a reflected ceiling plan, or a ceiling level and type per room.
- Internal impact: plaster heights bounded 531.8 .. 597.6 m2 and paint 529.5 .. 595.0 m2 (PROVISIONAL / HELD); 14 wet-wall
  tile lines; wet-room ceiling board on 82.51 m2.

### RFI-B-A02 Door and window schedule
- Drawing: the architectural elevations (sheets 06 .. 09) print sill and head for 9 openings only (W01, W03, W13, W14,
  W15, W17, W18, W26, D01); sections A-A (sheet 10) and B-B (sheet 11) draw the openings only, with no sill, head or tag;
  one printed door size (main entrance 2.00 wide, double leaf, on sheet 03; its 2.50 height per the merged opening
  census, sheet to be re-confirmed). [Lead 2026-10-30 12:40: corrected per the Checker's verdict.]
- Missing information: sill, head and arch rise of 20 windows and 3 arches; door heights and types.
- Requested: a door and window schedule.
- Internal impact: plaster / paint nets 104.1 m2 of range; window m2 HELD; door heights ASSUMED — OWNER-APPROVED 2.20 m
  (Q-55) meanwhile.

### RFI-B-A03 Main entrance door and the pool-court opening SX-01
- Drawing: P7757 sheet 03 (main door 2.00 x 2.50 double leaf; SX-01 4.521 m with a straight head); the client renders
  show a single leaf and a round arch over a low wall. (W02 is asked in A, RFI-A01.)
- Requested: the built arrangement of the main door and of SX-01.
- Internal impact: main door HELD (5.000 m2 candidate); SX-01 HELD.

### RFI-B-A04 Window heads above the beam soffit: W03 and W17
- Drawing: architectural elevations (sheets 06 .. 09: W03 head +5.30, W17 crown +9.20; the exact sheet to be named
  before sending, Checker verdict PARTIAL) against beam B8 20 x 75 on ST p.4 (GF roof slab top +5.50, so a soffit at most
  +4.75) and CB12 25 x 75 on ST p.5.
- Conflict: the opening head is above the beam soffit drawn on the same line.
- Requested: a lower head, or the beam moved / upturned.
- Internal impact: W03 and W17 CONFLICT (window and the wall above).

### RFI-B-A05 Roof build-up
- Drawing: P7757 sheets 10 / 11 (roof levels), the sanitary sheets (1 % falls); no roof section or build-up detail. (The
  structural slab-top levels are asked in A, RFI-S23.)
- Missing information: the roof build-up (falls screed, insulation, waterproofing, protection) per roof.
- Requested: the build-up per roof.
- Internal impact: roof finishes and the annex walls (83.82 m2 black + 29.30 m2 white) HELD with S23.

### RFI-B-A07 Under the 1F roof dome openings: ceiling, glazing and partition tops
- Drawing: architectural plans / sections vs ST p.5 1F roof slab (dome rings). (The 2F maid-room dome is asked in A,
  RFI-S28.)
- Missing information: what closes each opening below (ceiling, glazing or open); the top of the 1F partitions under the
  openings (10.67 m of wall).
- Requested: the ceiling / glazing under each opening and the top level of those partitions.
- Internal impact: 10.67 m of block HELD with no candidate height; ceilings under the openings HELD.

### RFI-B-A08 Soffits over outside air and the projection bands
- Drawing: no plan, section, elevation or detail draws a soffit finish or insulation (porch 19.181, side passage 5.640,
  pool court 12.834, roof edges 6.791 m2); two wet floors over outside air. (The structural section of the projection
  bands is asked in A, RFI-S18.)
- Requested: the soffit finish and build-up per place; insulation / waterproofing under the two wet floors over air.
- Internal impact: soffit areas CALCULATED, finish HELD.

### RFI-B-A09 Side passage and six outdoor level changes
- Drawing: P7757 sheet 03 (side passage 5.64 m2 without door or glazing; six outdoor openings with a 0.15 m level change,
  7.30 m of width, no step, sloped sill or ramp drawn). (The garden band is asked in A, RFI-A06.)
- Requested: the passage's built form and floor; step, sloped sill or ramp at each level change.
- Internal impact: classification and finish HELD.

### RFI-B-A10 Door D-GF-06 head and opening P-1F-01 head level
- Drawing: P7757 sheet 03 (D-GF-06 drawn rectangular, height not printed; the renders show a round arch); sheet 04
  (P-1F-01: no head level on any sheet).
- Requested: the head form and levels of D-GF-06; the head level of P-1F-01.
- Internal impact: D-GF-06 arched increment HELD; 1F-W14 + W15 nets 10.971 .. 16.223 m2, masonry above 0 .. 4.992 m2.

### RFI-B-A11 Sea-side boundary element (7.00 m: 6.00 solid + 1.00 gate)
- Drawing: P7757 sheet 03 (drawn 0.20 wide); the fence drawing does not show it.
- Requested: its material, height, structure, foundation, finishes and gate.
- Internal impact: visible HELD line (owner Q-63 C).

### RFI-B-A12 Railings, balustrades, shutters, unexplained squares and sheets not issued
- Drawing: renders vs drawings (shutters only at W14); nine small squares on two elevations (SE / fence elevations); the
  issued set has no site plan, top-roof plan, finishes schedule, specification, wet-room / kitchen or stair details, MEP.
- Requested: issue those sheets or confirm they do not exist; the railing / balustrade / shutter drawings; what the nine
  squares are.
- Internal impact: railings / shutters no quantity (not drawn); squares UNKNOWN; finishes, tile sizes (D-10), kitchen tile
  zones and MEP out of scope until issued.

### RFI-B-A13 External sills and parapet coping
- Drawing: architectural plans / elevations / sections draw the sill and coping outlines only; no finishes schedule,
  specification or owner rule names the material.
- Requested: material and profile of the external window sills (23; 2.5614 m2 / 29.530 m.l), the external door sills (6;
  1.310 m2 / 6.800 m.l), the 2 floor-level sills over air (0.160 m2) and the parapet top / coping / drip.
- Internal impact: geometry measured; material items HELD by name, never a default stone.

---

## Not to the designers

### Lift supplier (to CLARIFICATIONS_SUPPLIER_2026-10-23.md, not the structural designer)
- L-1: lift-pit depth (ST p.14 "as per lift manufacturer"; D-43): fixes the FF raft level, the neck depth of C1 / C2 / C9
  and the pit walls.
- L-2: landing door clear heights / head levels at L-GF-01, L-1F-01, L-2F-01 (the 1F-W07 mesh-strip residual 0.5948 m.l
  waits on L-1F-01).

### Client (survey; NEW from the merged existing-ground task, 2026-10-30)
- C-1: is a topographic survey (spot levels inside the plot) available? The set prints the existing ground +-0.00 only
  at the plot corners, outside the boundary; interior undulation and any existing fill are UNKNOWN. Internal impact:
  footing-pit excavation is a lower bound only (+129.234 m3 per metre the founding level lies below the 1.50 m
  minimum); the pool envelope moves 11.851 m3 per metre of ground rise. Sent only with the owner's approval, as a client
  request, never as a designer question.

### Not asked (internal or already in A)
- Mesh strip course height: owner answer 2026-10-29 (provisional 10 mm bed joint for mortared blocks); white AAC courses
  are an internal investigation (Lead 2026-10-30), not an RFI.
- Ground water / dewatering (ST p.8 notes 14 / 15, p.9 note 4): an internal investigation first (Lead 2026-10-30); an RFI
  only if that investigation shows a conditional scope the drawings cannot settle.
- Every item marked "(asked in A)" above.

---

## Checker citation verdicts (Verifier 2026-10-30 ~05:00 UTC, run session_01E6cPnazw4bAh9U4qdKdMqL; light run, queue item 1)

Sources read this run (Drive "Alsenan chalet project", read-only, decoded into .work/private, sha recorded):
'ST7757.pdf' (16 pages, no text layer: rendered at 100 / 200 dpi, read by eye, plus OCR of every page's stamps and
titles; sha256 74da1523..), 'ST7757 dxf.dxf' (texts by handle / position; sha256 9f9d1179..), 'p7757_arch_sheet03.pdf'
(GROUND FLOOR PLAN 1:100), 'p7757_arch_sheet04.pdf' (1st.FLOOR PLAN 1:100), 'p7757_arch_sheet10.pdf' (SECTION A-A
1:100), 'Alsenan_Architectural_P7757_Pages_01-02.pdf' (p.1 / p.2 = GF, 1F and 2F FLOOR AREA PLANS 1:200 with the area
tables) and 'Alsenan_Architectural_P7757_Pages_11-12.pdf' (p.11 SECTION B-B 1:100, p.12 FENCE PLAN / FENCE ELEVATION /
SECTION). Not opened this run: Pages_05-06 (2F plan p.5, SE elevation p.6), Pages_07-08, sheet09, sanitary-7757.pdf.
ST page map as in A (p.1 columns / axes ... p.16 stair details). No quantity, status or V2.9 cell changed by these
verdicts.

- RFI-B-S09: CITATION OK: p.8 note 9 = development length 70 d tension / 40 d compression, written for 'اشاير' (starter
  bars), no zone; p.9 = 'Schedule of Footings' + 'Schedule of Columns'; p.10 SB2 row 100 x 50, 10ø16 bottom, 20ø18 top,
  10ø8/m (DXF attribs 2ABB .. 2AC3, y -5678); the second SB2 insert (DXF 1FBC .. 1FC4, y -9548: 80 x 50, 10ø18, 10ø18,
  10ø8) lies below the printed table and is not on the print. Wording OK.
- RFI-B-S10: CORRECTED: the tank-slab reinforcement is printed on ST p.6 (2F roof slab: 'WATER TANK PLACE', panels
  '7ø14/m (T&B)' and '6ø12/m (T&B)', slab T18), NOT on a p.7 tank detail (p.7 holds only DETAIL OF SWIMMING POOL and
  DETAIL OF DOME). Note 2 (top bars 5ø10/m over beams, one third of the span, both directions) is printed in the notes
  box of p.4, p.5 AND p.6, so the note-2 vs (T&B) conflict sits on p.6 itself. p.15 TYP. SLAB ON BEAMS DETAIL: '.30 L1 OR
  .30 L2 WHICHEVER LARGER' and '.25 L1': OK. The 13 bar-less panels and the GF-126 zone were not recounted.
- RFI-B-S11: CITATION OK: p.7 DETAIL OF SWIMMING POOL draws a deep zone, a slope and a shallow zone (7ø14/m, 6ø12/m,
  ø12/20cm, ø10/20cm). Note for the sent text: 'R1 / R2' are our zone names, not printed: describe them as the deep
  floor and the sloped / shallow floor.
- RFI-B-S12: WRONG (stale): the bar count IS printed. Planted-column tags on the slab plans: ST p.4 'P.C 20x70 / 10ø16'
  (on B27) and 'P.C 20x50 / 8ø16' (on B26); ST p.5 'P.C 20x50 / 8ø16' (on B19); same finding as merged T-220
  (DXF 543 / 547 / 77D; D-46 narrowed to links and bar lengths). p.15 has no 'planted-column detail' as such: it has TYP.
  DETAIL OF TWISTED COLUMN (x2), BEAM IN CASEMENT WITH COLUMN (x2) and BEAM CARRYING PLANTED COL. DETAIL (column bars
  cranked into the beam, a 100 cm dimension, no link spacing). Rewrite: ask only the links (size, spacing) and the bar
  ends / laps of the three planted columns; delete 'no schedule row, no bar count'. Lead: the internal impact line
  ('column steel unquantified') should cite T-220 (main bars printed, steel HELD on links and lengths).
- RFI-B-S19: CITATION OK: p.10 remarks verified row by row: 2ø12/30cm on B7 .. B15, B17, B18, B20 .. B25, B28, B29;
  2ø14/20cm on B19; 2ø16/20cm on B16, B26, B27 (exact). MIDDLE REINT. 2ø12/30cm: p.11 CB1, CB6, CB7, CB12; p.12 CB3, CB8,
  CB11 (exact; CB2, CB4, CB5, CB9, CB10, CB13 blank). p.8 note 21 = 2ø12 / 3ø12 / 4ø12 side bars in beams deeper than
  60 cm according to the beam width, unless stated otherwise: OK.
- RFI-B-S20: CITATION OK, one addition: the nested-link symbol on p.10 is on B17, B19, B20 .. B26 (B18 none: exact);
  the SB1 and SB3 rows also print a two-link symbol and the SB2 row a three-link symbol (no size): add 'SB1 / SB2 / SB3'
  to the question or route them under S09 (SB2 is already there).
- RFI-B-S21: CITATION OK: p.8 note 9 is the starter-bar ('اشاير') development note; p.11 / p.12 typical span details
  print 0.22 Ln / 0.3 Ln2 support bars, '7.5cm' first link and 0.15 L; no hook, bend or end detail for beam bars or links
  on p.8 .. p.16.
- RFI-B-S22: CORRECTED: (a) stair beam: OK (p.16 TYPICAL DETAIL OF STAIR BEAM, cranked, 'AS PER SCH.', no crank
  dimension; 'B3 (With Stair)' printed twice on p.4 and once on p.5). (b) planted-column beams: the detail governs
  THREE beams, B27 and B26 (ST p.4) AND B19 (ST p.5, P.C 20x50 8ø16), not only B26 / B27. On BEAM CARRYING PLANTED COL.
  DETAIL the label is '4ø16' (the word 'EXTRA' is printed only on the twisted-column details, '4ø16 EXTRA'), and the bar
  extent IS drawn symbolically: a 'DEPTH' dimension beyond the column face (each side, by symmetry). Rewrite: ask the
  designer to confirm the 4ø16 length = column width + 2 x beam depth (as drawn) and its end anchorage, not 'length not
  dimensioned'.
- RFI-B-S13: CORRECTED: the sunken panels of the 1F floor are on ST p.4 (GF ROOF SLAB: 5 hatched 'Sunken slab' panels:
  B1 panel and B4 panel at the north, the B4 / B28 panel at the east, and the panel south of the D.C split in two by
  B27), and the 2F floor panel on ST p.5 (1F ROOF SLAB: 1 panel between the two B2 west of B3 (With Stair)); ST p.6
  (2F roof) draws none. 'ST p.5 / p.6' -> 'ST p.4 / p.5'. No drop printed: OK. Panel areas not re-measured.
- RFI-B-S14: CITATION OK: p.8 note 19 = tie beams joining the lift columns at 3.00 m where the storey height exceeds
  4.30 m, around the lift shaft; p.14 DETAIL OF LIFT WITH ISOLATED FOOTING (without basement) draws no tie-beam section.
- RFI-B-S16: CITATION OK: p.1 notes box ('ملاحظات'), second item: neighbour-side external tie beams, black block above
  and below, built from foundation level; no upper limit printed.
- RFI-B-S17: CITATION OK, sheet number to add: p.8 note 20 (walls containing columns are built at the column
  thickness); GF = arch sheet 03, 1F = sheet 04 (titles confirmed); the 2F plan is Pages_05-06 p.5 (sheet 05; identity
  from merged T-220 / T-194, not opened this run). Wall thicknesses not re-measured.
- RFI-B-SH: CITATION OK for the pages read: no wall-to-column tie, restraint or connection detail on ST p.1, p.4 .. p.8,
  p.10 .. p.12, p.14 .. p.16 (viewed) or in the OCR of p.2 / p.3 / p.9 / p.13 (foundation, ground beams, schedules,
  footing / ground-beam / lintel details). Wording (structural requirement only) OK.
- RFI-B-S18: CORRECTED: title-block DATE box: p.1 .. p.7 'May 06, 2025'; p.9, p.10, p.13, p.14, p.15, p.16 'May 06,
  2026'; p.11 and p.12 have NO title block (schedule frames 'Ref. S-2' / 'S-3' only); p.8 (RECOMMENDATIONS) has a header
  block (design / drawn / checked by, client) WITHOUT a date field: add p.8 to the undated group. Every one of the 16
  pages also carries the same plot stamp '... ST7757.dwg / T7757.dwg ... May 06, 2026 - 12:04pm A008-PC' (p.1 .. p.7 from
  ST7757.dwg, p.8 .. p.16 from T7757.dwg: two source files), and p.1 .. p.7 a 'May 06, 2026' print stamp top left. Ask
  also which of the two source drawings (ST7757 / T7757) is the issue of record.
- RFI-B-A01: CITATION OK: sheet 10 (A-A) and sheet 11 (B-B) print levels and storey chains only (±0.00, +0.15, +0.30,
  +1.00, +4.30, +5.50, +9.70, +13.90; 100 / 450 / 420 / 50); no ceiling line, no RCP among the 12 sheets.
- RFI-B-A02: CORRECTED: sections A-A (sheet 10) and B-B (sheet 11) print NO sill or head dimension and no opening tag
  (openings drawn only); the 9 sills / heads were read from the elevations (sheets 06 .. 09, per merged T-082 / T-083 /
  T-201), which this run did not reopen: cite 'elevations sheets 06 .. 09' as the source and the sections only as
  drawn outlines. The main-entrance 2.00 width is on sheet 03 (double leaf, chain 80 / 200 / 90); its 2.50 height is not
  on the plan (T-175 records it PRINTED; sheet not re-read).
- RFI-B-A03: PARTIAL: sheet 03 = GROUND FLOOR PLAN confirmed; '452' printed on the sea-view chain under the pool with
  the '45' return (SX-01 width); main door double leaf 2.00 on sheet 03; the '2.50' height is not on sheet 03 (see A02).
  Renders not checked.
- RFI-B-A04: PARTIAL: structural side OK (B8 20 x 75 on ST p.4 at the east wing; CB12 25 x 75 on ST p.5; GF roof slab
  top +5.50 on sections, so a 0.75 m beam soffit <= +4.75); the architectural sheets printing W03 head +5.30 and W17
  crown +9.20 were not reopened: Lead, name them (elevations 06 .. 09) before sending.
- RFI-B-A05: CITATION OK for sheets 10 / 11 (roof levels +4.30, +9.70, +13.90; slabs drawn without any build-up layer);
  no roof section or build-up detail on the sheets read; sanitary sheet not reopened.
- RFI-B-A07: CITATION OK (ST p.5 dome rings 'SEE DETAIL', ST p.7 DETAIL OF DOME; sheet 11 B-B draws the two domes
  over the +9.70 roof); no ceiling or glazing under them is drawn.
- RFI-B-A08: CITATION OK for the sheets read (03, 04, 10, 11, 12: no soffit finish or insulation drawn).
- RFI-B-A09: CITATION OK for sheet identity (sheet 03; '+0.15' outdoor marks printed); the six level changes and 7.30 m
  were not recounted.
- RFI-B-A10: CITATION OK for sheet identity (sheet 03 GF, sheet 04 1F); the opening ids are ours (not printed):
  identify D-GF-06 and P-1F-01 by position and size in the sent text, as for A08 in A.
- RFI-B-A11: CITATION OK: 'the fence drawing' = sheet 12 (FENCE PLAN / FENCE ELEVATION / SECTION, street front only);
  it does not draw the sea-side element.
- RFI-B-A12: CITATION OK with one precision: the set does contain p.1 / p.2 FLOOR AREA PLANS 1:200 (plot outline,
  setbacks, area tables), which are not a site plan (no levels, paving, fence or services); the fence elevation on
  sheet 12 prints small squares (6 visible); the SE elevation squares not reopened.
- RFI-B-A13: CITATION OK (no finishes schedule or specification among the 12 sheets).
- L-1: CITATION OK: ST p.14 'As Per Lift Manufactures recommendations' on the pit depth dimension.
- L-2, C-1: no drawing citation to check (C-1 matches the merged T-357 verdict: +-0.00 only at the plot corners).

Totals: 26 questions: CITATION OK 18 (S09, S11, S14, S16, S17, SH, S19, S20 with an addition, S21, A01, A05, A07, A08,
A09, A10, A11, A12, A13), CORRECTED 5 (S10 tank sheet p.6, S13 sheets p.4 / p.5, S18 p.8 undated + plot stamps, S22 third
beam B19 + 'DEPTH' extent, A02 sections print no sill / head), WRONG 1 (S12: bar counts printed, stale since T-220),
PARTIAL 2 (A03, A04: elevation sheets not reopened); L-1 OK; 0 NOT CHECKED. Lead: apply the five corrections and the S12
rewrite before the owner's review; nothing sent.

LEAD 2026-10-30 12:40 UTC (run session_01E6cPnbt2rnWMmSnoPa5qft): APPLIED in the question texts above: S10 (tank sheet
p.6, note 2 on p.4 / p.5 / p.6), S12 (rewritten: links and bar ends only), S13 (p.4 / p.5), S18 (p.8 undated, plot stamps,
two source drawings), S22 (B19 third beam, 'DEPTH' extent, '4ø16'), A02 (elevations 06 .. 09 as the source, sections
draw outlines only), plus the S20 addition and the A04 sheet note. Still open before sending: A03 / A04 elevation
sheet numbers (PARTIAL: elevations not reopened); S11 sent text to describe 'R1 / R2' as the deep floor and the sloped
/ shallow floor. Nothing sent; the owner reviews.
