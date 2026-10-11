# 07 Foundations, columns and beams (investigations C + D)

## Frame per floor (allocation-free)

| Floor | FL col | FL beams | FL slabs | FL frame | U col | U beams | U slabs | U frame | U cond. high | christiannp frame | FL - U |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | 17.44 | 42.88 | 33.12 | 93.44 | 20.25 | 39.14 | 33.45 | 92.84 | 3.52 | 109.55 | 0.60 |
| 1F | 7.73 | 17.03 | 19.20 | 43.95 | 10.67 | 21.10 | 20.00 | 51.77 | 5.39 | 56.14 | -7.82 |
| 2F | 3.38 | 6.06 | 7.50 | 16.93 | 5.80 | 4.30 | 7.51 | 17.61 | 0.67 | 16.15 | -0.67 |

**The near-equal beam totals hide compensating errors.** Per floor, the GF frames agree; the freelancer is short on 1F and close on 2F.

Columns differ by convention: the freelancer takes clear height under the beams and measures the beams through the joints. Urban takes floor to floor and measures the beams net of the columns. The joint is counted once either way, so only the frame per floor compares.

## Beams by floor and mark (largest differences)

| Floor | Mark | FL m3 | U base m3 | U cond. high | FL - U | Class |
|---|---|---|---|---|---|---|
| 1F | B25 | 0.00 | 2.84 | 0.00 | -2.84 | MISSING_IN_FREELANCER |
| GF | B27 | 0.00 | 2.50 | 0.84 | -2.50 | MISSING_IN_FREELANCER |
| 1F | B6 | 0.55 | 2.68 | 0.00 | -2.13 | GEOMETRY_DIFFERENCE |
| 1F | B19 | 0.00 | 1.60 | 0.00 | -1.60 | MISSING_IN_FREELANCER |
| GF | B26 | 4.42 | 3.10 | 0.68 | 1.32 | GEOMETRY_DIFFERENCE |
| 1F | B23 | 2.40 | 1.11 | 0.00 | 1.28 | GEOMETRY_DIFFERENCE |
| GF | B20 | 2.16 | 0.99 | 0.00 | 1.17 | GEOMETRY_DIFFERENCE |
| 2F | B15 | 1.63 | 0.65 | 0.00 | 0.98 | GEOMETRY_DIFFERENCE |
| GF | B7 | 1.57 | 0.68 | 0.00 | 0.89 | GEOMETRY_DIFFERENCE |
| 1F | CB10 | 0.88 | 0.00 | 0.00 | 0.88 | MISSING_IN_URBAN |
| 1F | B5 | 0.00 | 0.83 | 0.00 | -0.83 | MISSING_IN_FREELANCER |
| GF | B24 | 2.16 | 1.33 | 0.00 | 0.82 | GEOMETRY_DIFFERENCE |
| GF | CB3 | 1.53 | 0.93 | 0.00 | 0.60 | GEOMETRY_DIFFERENCE |
| GF | CB8 | 4.03 | 3.50 | 0.00 | 0.53 | GEOMETRY_DIFFERENCE |
| 1F | CB11 | 3.30 | 2.85 | 0.00 | 0.45 | GEOMETRY_DIFFERENCE |
| 1F | CB12 | 2.44 | 2.00 | 0.00 | 0.44 | GEOMETRY_DIFFERENCE |
| GF | CB5 | 0.57 | 0.18 | 0.00 | 0.38 | GEOMETRY_DIFFERENCE |
| 1F | B4 | 0.89 | 1.22 | 0.00 | -0.33 | GEOMETRY_DIFFERENCE |
| 2F | B8 | 0.81 | 0.52 | 0.00 | 0.29 | GEOMETRY_DIFFERENCE |
| 2F | B1 | 0.72 | 0.46 | 0.67 | 0.26 | GEOMETRY_DIFFERENCE |
| GF | B1 | 1.13 | 1.34 | 0.00 | -0.21 | GEOMETRY_DIFFERENCE |
| 2F | B2 | 1.02 | 0.82 | 0.00 | 0.20 | GEOMETRY_DIFFERENCE |
| GF | B2 | 0.85 | 0.66 | 0.00 | 0.19 | GEOMETRY_DIFFERENCE |
| 1F | CB9 | 1.22 | 1.04 | 0.00 | 0.18 | GEOMETRY_DIFFERENCE |
| GF | CA | 0.00 | 0.17 | 0.00 | -0.17 | MISSING_IN_FREELANCER |
| 1F | B2 | 0.84 | 0.67 | 0.19 | 0.17 | GEOMETRY_DIFFERENCE |
| GF | B28 | 0.00 | 0.15 | 0.00 | -0.15 | MISSING_IN_FREELANCER |
| 1F | B7 | 0.60 | 0.45 | 0.00 | 0.15 | GEOMETRY_DIFFERENCE |
| GF | CB1 | 3.41 | 3.28 | 0.00 | 0.13 | GEOMETRY_DIFFERENCE |
| 1F | CB13 | 1.05 | 0.92 | 0.00 | 0.13 | GEOMETRY_DIFFERENCE |

**What the mark crosswalk shows** (07A has every mark):

- **Many marks match to the litre** (GF B22, B29, B3, B5, B8, B11, B14, B16; 1F B18, B1, B11, B3; 2F B7). Same geometry, same depth reading.
- **Missing in the freelancer's BOQ, though drawn and bound:**
  - GF B27 (90 x 85, 3.27 m);
  - 1F B19, B25 and B5;
  - most of the 1F B6 length (21.4 m drawn against 4.37 m priced);
  - GF B28 and CA.
- **Missing in Urban's base:**
  - 1F CB10: two tags sit between a 200 band and a 300 band, so it is AMBIGUOUS and held in the 1F unlabelled-span exposure;
  - the unlabelled spans in general: CONDITIONAL, RFI-M5-04.
- **Length differences on continuous beams** (CB1 - CB8, CB9 - CB13): the freelancer measures centre to centre or the scheduled total; Urban measures the drawn spans net of the supports.
- **Depth reading (RFI-M5-01).** Urban's base takes H as the overall depth (slab inside); the high end, 80.79 m3, takes H below the slab. The freelancer uses the base reading.
- **The two dome-A ring arcs** that M4 bound to B4 are moved to the dome ring (D-02).

## Footings, straps and necks

| Family | Mark | FL m3 | U base m3 | U cond. high | FL - U | Class |
|---|---|---|---|---|---|---|
| FOOTINGS | F+F10 | 2.82 | 2.82 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F11 | 2.62 | 2.62 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F12 | 9.86 | 9.86 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F13 | 5.16 | 5.16 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F14 | 6.27 | 6.27 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F15 | 0.72 | 0.72 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F2 | 2.26 | 2.26 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F3 | 0.67 | 1.34 | 0.00 | -0.67 | GEOMETRY_DIFFERENCE |
| FOOTINGS | F4 | 3.52 | 3.52 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F5 | 4.03 | 4.03 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F6 | 2.86 | 2.86 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F8 | 7.20 | 7.20 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | F9 | 5.05 | 5.05 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | FF | 11.38 | 11.38 | 0.00 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| FOOTINGS | FN | 1.20 | 1.16 | 0.00 | 0.04 | GEOMETRY_DIFFERENCE |
| STRAPS | SB1 | 1.59 | 2.00 | 0.00 | -0.40 | GEOMETRY_DIFFERENCE |
| STRAPS | SB2 | 1.15 | 1.13 | 0.00 | 0.02 | MATCHED_WITHIN_TOLERANCE |
| STRAPS | SB3 | 0.65 | 0.65 | 0.00 | -0.00 | MATCHED_WITHIN_TOLERANCE |
| NECKS | C | 1.12 | 1.32 | 0.38 | -0.20 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C1 | 0.23 | 0.29 | 0.00 | -0.07 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C10 | 0.32 | 0.00 | 0.53 | 0.32 | MISSING_IN_URBAN_BASE (held as unresolved exposure) |
| NECKS | C11 | 0.66 | 1.32 | 0.00 | -0.66 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C2 | 0.90 | 1.23 | 0.00 | -0.33 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C3 | 1.12 | 1.84 | 0.00 | -0.72 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C4 | 0.45 | 0.63 | 0.00 | -0.18 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C5 | 0.81 | 1.12 | 0.00 | -0.31 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C6 | 0.32 | 0.42 | 0.00 | -0.10 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C7 | 0.36 | 0.43 | 0.00 | -0.07 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C8 | 0.81 | 1.08 | 0.00 | -0.27 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | C9 | 0.90 | 1.17 | 0.00 | -0.27 | HEIGHT_OR_LEVEL_DIFFERENCE |
| NECKS | CN | 0.81 | 0.00 | 1.12 | 0.81 | MISSING_IN_URBAN_BASE (held as unresolved exposure) |

**Footings agree mark for mark** (same schedule sizes), with two exceptions:

- SH10 draws two F3 outlines, and the freelancer prices one;
- one FN outline overlaps F9, and Urban deducts the overlap.

**The F/F10 conflict outline:** both sources price it as F10.

**Necks:** the freelancer's 1.50 m against Urban's footing top to +1.00. The founding level is printed only as a minimum (1.50 m below plot level), so it is RFI-M5-05.

**Straps:** Urban measures clear of the footings; the MCPs measure into them (11, X-01).

## Columns

| Floor | Mark | FL m3 | U base m3 | U cond. high | Class |
|---|---|---|---|---|---|
| 1F | C1 | 0.34 | 0.42 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C2 | 1.38 | 1.68 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C3 | 1.03 | 1.26 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C4 | 0.69 | 0.84 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C5 | 1.03 | 1.26 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C6 | 0.00 | 0.50 | 0.00 | MISSING_IN_FREELANCER |
| 1F | C7 | 1.10 | 0.67 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C8 | 0.62 | 1.51 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | C9 | 0.69 | 1.51 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 1F | P.C | 0.83 | 1.01 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 2F | C1 | 0.34 | 0.42 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 2F | C2 | 1.38 | 1.68 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 2F | C3 | 0.34 | 1.26 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 2F | C5 | 0.34 | 0.84 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 2F | C8 | 0.00 | 0.59 | 0.00 | MISSING_IN_FREELANCER |
| 2F | C9 | 0.62 | 0.59 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| 2F | P.C | 0.34 | 0.42 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C | 1.88 | 2.25 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C1 | 0.75 | 0.45 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C10 | 0.66 | 0.79 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C11 | 1.03 | 2.48 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C2 | 2.25 | 1.80 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C3 | 2.34 | 3.38 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C4 | 0.94 | 1.12 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C5 | 1.69 | 2.02 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C6 | 0.66 | 0.79 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C7 | 0.75 | 0.90 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C8 | 1.69 | 2.02 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| GF | C9 | 2.81 | 2.25 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| UNKNOWN | CN | 0.00 | 0.00 | 3.48 | UNRESOLVED_REQUIRES_ENGINEER (in neither base) |

**Planted columns (P.C, 1F and 2F):** the freelancer prices them (PC1, PC2, PC) and M4 missed them. The engine fix (V4) and M5 decision D-06 add them.

**CN columns:** their type is not in the schedule (RFI-M5-12).

**Lift-pit walls:** see 08.

