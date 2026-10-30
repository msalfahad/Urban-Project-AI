# B. Remaining RFIs, Alsenan chalet (DRAFT, NOT TO BE SENT; owner 2026-10-29 22:05)

Prepared by the Lead 2026-10-30 04:15-04:40 UTC (run session_01E6cPnckUhqJQdZyhEFoLeU) from
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
- Drawing: ST p.4 / p.5 / p.6 slab plans, note 2 ("one third of the span"); ST p.15 typical slab detail (0.30 max(L1, L2) /
  0.25 L1); ST p.7 tank detail (top and bottom mesh).
- Conflict / missing: two printed rules for the top-bar extent; the GF-126 zone is not delimited; 13 panels print no
  bars; note 2 vs the tank's top-and-bottom mesh.
- Requested: which rule governs the top-bar extent; the bars of each unprinted panel (or confirmation that none are
  required); the tank-slab reinforcement.
- Internal impact: top over supports 752.73 .. 1,931.52 kg; GF-126 7.89 .. 19.55 kg; 13 panels HELD; tank 28.66 .. 70.61 kg.

### RFI-B-S11 Pool floor bar population
- Drawing: ST p.7 pool detail (two zones R1 / R2 with a slope and a step); the owner's flat-floor decision Q-26 A (1.15 m)
  governs the concrete.
- Missing information: which bar population belongs to the flat floor that is built.
- Requested: the floor and wall reinforcement of the pool as built flat at 1.15 m.
- Internal impact: pool steel R1 888.90 .. 927.54 / R2 615.34 .. 639.45 kg. (Pool access is asked in A, RFI-A02.)

### RFI-B-S12 Three planted columns: bars and links
- Drawing: ST p.15 planted-column details (no schedule row, no bar count).
- Requested: the bar count, size and links of each planted column.
- Internal impact: column steel unquantified (the frozen route's 172.56 kg comes from a duplicated row and is not used).

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
- Drawing: ST p.10 link symbol with two nested links on B17, B19 .. B26.
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
- Drawing: ST p.16 TYPICAL DETAIL OF STAIR BEAM (cranked profile, no dimensions) for B3 "(With Stair)" on ST p.4 / p.5;
  ST p.15 BEAM CARRYING PLANTED COL. DETAIL (4 ø16 extra, length not dimensioned) for B26 / B27.
- Requested: the crank dimensions; the length of the extra bars.
- Internal impact: stair beams HELD_DEFINED 20.25 kg each (plan-length lower bound); planted-column extra unquantified.

## Structural designer: blockwork, slabs and restraint

### RFI-B-S13 Sunken slab panels: depth of the drop
- Drawing: ST p.5 / p.6 slab plans mark the sunken panels (1F floor 19.3964 m2 in 5 panels; 2F 5.400 m2).
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
- Drawing: ST p.1 .. p.7 dated May 06, 2025; p.9, p.10, p.13 .. p.16 dated May 06, 2026; p.11 / p.12 without a title
  block.
- Missing information: which date is the issue; whether the beam schedules p.11 / p.12 belong to the same issue; the
  revision of each sheet.
- Requested: the issue date and revision per sheet (a document-control confirmation, not a design question).
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
- Drawing: architectural elevations / sections (sections A-A sheet 10, B-B sheet 11) print sill and head for 9 openings only (W01, W03, W13, W14, W15,
  W17, W18, W26, D01); one printed door size (main entrance 2.00 x 2.50).
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
- Drawing: architectural elevations / sections (W03 head +5.30 under beam B8, whose soffit is at most +4.75 on ST p.4;
  W17 crown +9.20 against CB12 on ST p.5).
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
