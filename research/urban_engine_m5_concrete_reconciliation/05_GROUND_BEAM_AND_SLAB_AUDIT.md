# 05 Ground beams + ground slab (investigation A)

## The ground zone, allocation-free

The freelancer's ground zone is 87.087 m3: its 'ground beams + ground slab' category, plus the perimeter beam and straps it files under foundations, plus the boundary-wall beam. Urban measures 51.237 m3 (ground slab + ground beams + straps), with conditional cells 3.74 - 4.90 m3 and a conditional boundary-wall beam 3.53 - 5.29 m3.

The brief's '75.09 vs 51.24' compares the freelancer's category with M4's ground beams + slab. That category already holds the boundary-wall beam; the perimeter beam and straps sit in its foundations category.

## Ground slab: where the freelancer's 295.5 m2 goes

|  | m2 | m3 |
|---|---|---|
| freelancer plate (one typed area, no outline) | 295.50 | 29.55 |
| drawn ground-floor plate (union of all SH08 faces: cells, beam strips, columns) | 285.88 | - |
|   cells Urban measures (20 cells, 0.10) | 167.55 | 16.75 |
|   cells Urban holds (lift / lobby cell, light-well stair cell) | 53.29 | - |
|   ground beams and columns inside the plate (already full depth) | 65.04 | - |
| freelancer area beyond the drawn plate (cannot be located) | 9.62 | - |
| christiannp (A7: GF gross outline) | 324.04 | 32.40 |

Two parts of the 295.5 m2 can be located, and one cannot:

- **65.04 m2 of the plate is ground beams and columns.** The freelancer prices them again at full depth, so 6.50 m3 is double counted (BEAM_SLAB_OVERLAP).
- **53.29 m2 is the two cells Urban holds.**
- **9.62 m2 lies beyond the drawn plate and cannot be located.** A single typed area cannot be placed. The 1.2 m passage between the two blocks (S-BOUN strip, +0.15) is a candidate.

### The held cells

The M4 face of the lift / lobby cell is split by the S8.1A recovered regions. Those polygons are in the same sheet frame plus the SH08 origin, and they were intersected exactly:

| Region inside the M4 cell | m2 |
|---|---|
| CELL_BETWEEN_MEMBERS (SPC-GROUND_SLAB) | 29.060 |
| STAIR_FLIGHT_ZONE (S8 STAIR (new element candidate: not in the PRE-S8 census)) | 11.520 |
| PIT_OPENING (SPC-LIFT_PIT) | 3.240 |
| BEAM (S5 GROUND_BEAM line BL033 (2 S1 occurrences)) | 1.506 |
| WALL (PS8-LIFT-WALLS) | 1.100 |
| BEAM (S5 GROUND_BEAM line BL010 (2 S1 occurrences)) | 0.968 |
| BEAM (S5 GROUND_BEAM line BL029 (1 S1 occurrences)) | 0.870 |
| BEAM (S5 GROUND_BEAM line BL030 (1 S1 occurrences)) | 0.810 |

How the cell is treated:

- **M4 already deducted the four ground-beam bands that cross it.** The lift void and the 200 mm pit walls are still inside the face: the S-BW pit outlines are not face edges.
- **M4's exposure of the face (4.49 m3) therefore overstates the slab** by the void and the walls.
- **M5 carries the slab candidates as CONDITIONAL ground slab:** 29.06 m2 x 0.10 (low). The high end adds the lobby / stair region.
- **The TT1 note's scope is not established (S8.1A).** That is RFI-M5-02.

## Ground beams

| Class | W | H base | H low | H high | Level inside | Spans | Length m | Base m3 | Blocker |
|---|---|---|---|---|---|---|---|---|---|
| EXTERIOR_WALL | 0.30 | 0.30 | 0.30 | 0.30 | +0.00 | 2 | 2.20 | 0.20 | GB_TITLES_AND_LENGTH_BASIS |
| EXTERIOR_WALL | 0.30 | 0.30 | 0.30 | 0.30 | +0.30 | 2 | 2.00 | 0.18 | GB_EXTERIOR_LEVEL_CONFLICT |
| EXTERIOR_WALL | 0.30 | 0.40 | 0.30 | 0.40 | +0.30 | 2 | 4.70 | 0.56 | GB_EXTERIOR_LEVEL_CONFLICT |
| EXTERIOR_WALL | 0.30 | 0.40 | 0.40 | 0.40 | +0.15 | 2 | 6.22 | 0.75 | GB_EXTERIOR_LEVEL_CONFLICT |
| EXTERIOR_WALL | 0.30 | 0.40 | 0.40 | 0.40 | +0.30 | 4 | 12.52 | 1.47 | GB_EXTERIOR_LEVEL_CONFLICT |
| EXTERIOR_WALL | 0.30 | 0.60 | 0.60 | 0.60 | +0.30 | 3 | 22.33 | 4.02 | GB_EXTERIOR_LEVEL_CONFLICT |
| EXTERIOR_WALL | 0.30 | 0.90 | 0.30 | 1.00 | - | 1 | 1.30 | 0.35 | GB_EXTERIOR_DEPTH |
| EXTERIOR_WALL | 0.30 | 0.90 | 0.30 | 1.00 | +1.00 | 2 | 0.99 | 0.27 | GB_EXTERIOR_DEPTH |
| EXTERIOR_WALL | 0.30 | 0.90 | 0.40 | 1.00 | +1.00 | 2 | 8.10 | 2.19 | GB_EXTERIOR_DEPTH |
| EXTERIOR_WALL | 0.30 | 0.90 | 0.60 | 1.00 | +1.00 | 3 | 19.00 | 5.13 | GB_EXTERIOR_DEPTH |
| INTERIOR | 0.30 | 0.30 | 0.30 | 0.30 | - | 10 | 13.60 | 1.22 | GB_TITLES_AND_LENGTH_BASIS |
| INTERIOR | 0.30 | 0.40 | 0.30 | 0.40 | - | 4 | 9.60 | 1.15 | GB_TITLES_AND_LENGTH_BASIS |
| INTERIOR | 0.30 | 0.40 | 0.40 | 0.40 | - | 14 | 52.20 | 6.26 | GB_TITLES_AND_LENGTH_BASIS |
| INTERIOR | 0.30 | 0.60 | 0.60 | 0.60 | - | 6 | 37.73 | 6.79 | GB_TITLES_AND_LENGTH_BASIS |
| PERIMETER_NO_WALL | 0.30 | 0.30 | 0.30 | 0.30 | - | 1 | 1.81 | 0.16 | GB_TITLES_AND_LENGTH_BASIS |
| STRAP SB1 | 0.70 | 0.50 | 0.50 | 0.50 | - | 1 | 5.70 | 2.00 | NOT_REVIEWED |
| STRAP SB2 | 1.00 | 0.50 | 0.40 | 0.50 | - | 1 | 2.26 | 1.13 | SCHEDULE_DUPLICATE_MARK |
| STRAP SB3 | 0.50 | 0.40 | 0.40 | 0.40 | - | 1 | 3.27 | 0.65 | NOT_REVIEWED |

### The freelancer's rows

| Row | What | B | C | D | m3 |
|---|---|---|---|---|---|
| FL-WS01-R032 | perimeter tie beam | 0.20 | 0.60 | 71.70 | 8.60 |
| FL-WS02-R013 | ground beams, longitudinal | 0.30 | 100 | 0.60 | 18.00 |
| FL-WS02-R014 | ground beams, transverse | 0.30 | 111 | 0.60 | 19.98 |
| FL-WS02-R015 | boundary-wall (fence) ground beam | 0.30 | 42 | 0.60 | 7.56 |

B, C and D are as typed in the workbook: width, length, depth on the ground-beam rows; width, depth, length on the perimeter row.

**Same network, different depth and length.** Three independent extractions agree on the drawn network:

- Urban's spans: 194.29 m net of columns;
- christiannp: 42 strips, 200.036 m gross;
- U-C4N: about 200 m (36.005 / 0.18).

The freelancer's 211 m is that network measured through the columns and junctions, with about 12 m more.

**Depth:**

- **Interior.** The freelancer's 0.60 everywhere replaces the printed p.13 classes: 30 x 30 under 2.5 m, 30 x 40 under 5 m, 30 x 60 over 5 m (-5.09 m3). Which length selects the class (centre to centre or clear) is RFI-A05; Urban takes the base reading and shows the range.
- **Exterior.** The detail is 30 x 'FOLLOW ARCH.' Urban brackets it at 0.9 - 1.0 m where the plan prints +1.00 inside, and keeps the class section where the inside level is +0.30 / +0.15 (annex, court) (+0.82 m3).

**The perimeter tie beam (71.7 m x 20 x 60, 8.604 m3) is not a drawn element:**

- every ground beam on SH08 is a 300 mm band;
- the 20 x 60 section is the schedule row B.W (boundary-wall beam), which binds to no plan occurrence;
- p.1 note B describes an upper and a lower beam over a black-brick wall on the neighbour side (CANDIDATE).

Urban holds note B as UNRESOLVED (0 - 3.17 m3 over 26.40 m of neighbour-side exterior beam), RFI-M5-08.

### The boundary wall

Layer S-BOUN on SH08 draws the wall strips, 200 mm thick:

- the main run along the neighbour, street and sea sides: 41.72 m;
- two short pieces: 1.20 m, 1.15 m.

The freelancer's 42 m follows the main run. p.14 prints a typical: R.C columns 20x30 4Ø14; GB 20x40; pads 130x80x30. It conflicts with the B.W row (20 x 60), and the spacing of pads and columns is not printed. The beam is a CONDITIONAL 3.53 - 5.29 m3; pads and columns are UNRESOLVED. Whether the boundary wall is in the contract at all is the client's call (RFI-M5-09).

## Map

`visual/01_GROUND_ZONE_FOOTPRINT.svg` (annotated), `visual/09d_UNRESOLVED_SH08.svg`.

