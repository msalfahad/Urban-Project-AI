# M5: quotation-critical concrete reconciliation (ST7757)

> **Status: NOT QUOTATION-READY as a fixed-price lump sum.** This is a planning reconciliation, not engineering approval. Nothing here is VERIFIED by a person, and the project gate stays INCOMPLETE. Concrete is priced at the brief's rate of 26.5 KWD/m3. Plain concrete (blinding) is kept apart from reinforced concrete (RC) everywhere.

**Phase: RECONCILIATION.** The Urban engine was run first, at its frozen M4 state (commit `35c0587`, V3 conventions); its register was hashed (`2e4a6ec6fa4e6e35c87efb7f`) before any external figure was read. The freelancer and MCP figures are read from their own records at build time. They explain differences only; no Urban quantity was chosen or tuned to meet them.

## The answer in one table

| Quantity | m3 | KWD |
|---|---|---|
| Freelancer RC (excl. its 47.055 m3 plain concrete) | 352.44 | 9,340 |
| Urban M4 headline (the brief's 312.05) = RC + plain | 312.05 | 8,269 |
|   of which Urban M4 RC | 289.89 | 7,682 |
|   of which plain concrete (blinding), not RC | 22.16 | 587 |
| **Urban M5 RC, drawing-supported measured base** | 316.06 | 8,376 |
|   measured range (every convention low .. high) | 307.57 - 344.60 | 8,150 - 9,132 |
|   conditional allowances (drawn, need an answer) | 14.55 - 35.38 | 386 - 938 |
|   unmeasurable items (not drawn; listed, never zero) | 13 items | - |
| Measured base + conditional high | 351.45 | 9,313 |
| Upper planning bound (measured high + conditional high) | 379.98 | 10,069 |

## A. Findings

### Why the difference is not 40.39 m3

- **The 40.39 m3 compares unlike things.** 352.436 - 312.046 = 40.39 m3. The Urban figure includes 22.155 m3 of blinding; the freelancer's does not (its 47.055 m3 of plain concrete is a separate row).
- **RC against RC, the M4 gap is 62.54 m3** (1,657 KWD).
- **M4's generic route does not measure four families** that the frozen S-stages measure: stairs, domes, the pool and the lift-pit walls (25.03 m3).
- **With them, after the M5 ownership decisions** (no double count, 11A), Urban's measured RC is 316.065 m3. The freelancer prices **36.37 m3 more (964 KWD)**.

### The difference, cause by cause

Each step is Urban minus freelancer; the steps close exactly (IV-08). The full table with evidence is 04.

| Step | Cause | m3 | KWD | Class |
|---|---|---|---|---|
| B01 | Boundary-wall ground beam (freelancer 42 m x 30 x 60) | -7.560 | -200 | SCOPE_DIFFERENCE |
| B02 | Perimeter tie beam (freelancer 71.7 m x 20 x 60) | -8.604 | -228 | SOURCE_CONFLICT (likely DOUBLE_COUNTED) |
| B03 | Pool pump room walls and floor | -3.480 | -92 | SCOPE_DIFFERENCE (not drawn) |
| B04 | Pool steps | -0.228 | -6 | SCOPE_DIFFERENCE (not drawn) |
| B05 | Ground slab over the ground-beam and column footprint (inside the drawn plate) | -6.504 | -172 | DOUBLE_COUNTED (BEAM_SLAB_OVERLAP) |
| B06 | Ground-slab cells Urban holds unresolved (lift / stair cell, stair-zone cell) | -5.329 | -141 | MISSING_IN_URBAN_BASE |
| B07 | Freelancer plate area beyond the drawn ground-floor footprint | -0.962 | -25 | GEOMETRY_DIFFERENCE (cannot be located) |
| B07a | Member overlap deducted inside measured cells, and rounding | +0.000 | 0 | GEOMETRY_DIFFERENCE (small) |
| B08 | Ground-beam length: freelancer total vs Urban net of columns | -3.008 | -80 | GEOMETRY_DIFFERENCE |
| B09 | Interior ground-beam depth: 0.60 everywhere vs the printed p.13 classes | -5.094 | -135 | THICKNESS_OR_DEPTH_DIFFERENCE |
| B10 | Exterior ground-beam depth: 0.60 vs the FOLLOW ARCH bracket | +0.824 | 22 | THICKNESS_OR_DEPTH_DIFFERENCE |
| B11 | Strap beams | +0.388 | 10 | GEOMETRY_DIFFERENCE |
| B12 | Footings | +0.630 | 17 | MISSING_IN_FREELANCER |
| B13 | Foundation necks | +2.050 | 54 | HEIGHT_OR_LEVEL_DIFFERENCE |
| B14 | Columns GF - 2F | +8.168 | 216 | HEIGHT_OR_LEVEL_DIFFERENCE |
| B15 | Suspended beams | -1.427 | -38 | GEOMETRY_DIFFERENCE + MISSING_IN_FREELANCER |
| B16 | Suspended slabs | +1.149 | 30 | GEOMETRY_DIFFERENCE |
| B17 | Lintels | +0.463 | 12 | MISSING_IN_FREELANCER |
| B18 | Stairs | -5.992 | -159 | ASSUMPTION_DIFFERENCE |
| B19 | Domes | -0.044 | -1 | GEOMETRY_DIFFERENCE + SCOPE_DIFFERENCE |
| B20 | Pool base and walls | -1.556 | -41 | HEIGHT_OR_LEVEL_DIFFERENCE |
| B21 | Lift pit walls | -0.255 | -7 | GEOMETRY_DIFFERENCE |

Start 352.436 m3 (freelancer RC) -> end 316.065 m3 (Urban measured base).

**How to read the bridge:**

- **Freelancer items with no drawing behind them, or counted twice: 26.38 m3.**
  - the boundary-wall beam (scope, B01);
  - the 20 x 60 'perimeter tie beam' (B02): no such beam is drawn, and the 211 m of ground beam already runs the exterior lines;
  - the pool pump room and steps (B03, B04): not drawn;
  - the ground slab poured over the ground-beam and column footprint (B05): those beams are already full depth.
- **Different conventions: ground-beam depths and lengths, 7.28 m3 net.** The freelancer uses 30 x 60 everywhere; the drawings print 30 x 30 / 30 x 40 / 30 x 60 by span (p.13).
- **Urban is higher on the frame** (columns +8.17, slabs +1.15). The beams net -1.43 m3 because of **compensating errors**:
  - the freelancer misses whole beams that are drawn (B27, B19, B25, B5, part of B6 / B4) and some column occurrences (1F C6, 2F C8);
  - it measures other beams centre to centre.
  - Per floor, allocation-free: GF agrees within 1 %, but the freelancer is 7.82 m3 short on 1F (07).
- **Stairs (-5.99) and the pool walls (-1.56) are assumption-driven.** The freelancer uses a 0.28 m slab equivalent on the stairs and 1.8 m pool walls. Urban integrates the drawn flights at the waist range (S8.7) and the drawn wall bands (S8.2A).

### Largest items

| Element | Freelancer m3 | Urban base m3 | Urban cond. high m3 | KWD (FL - U) | Class |
|---|---|---|---|---|---|
| M5-GROUND_SLAB-GROUND-SLAB_ON_GRADE | 29.55 | 16.75 | 4.90 | 339 | SCOPE_DIFFERENCE + BEAM_SLAB_OVERLAP + MISSING_IN_URBAN_BASE |
| M5-GB_PERIMETER-GROUND-PERIMETER | 8.60 | 0.00 | 3.17 | 228 | SOURCE_CONFLICT |
| M5-BOUNDARY_WALL-SITE-BEAM | 7.56 | 0.00 | 5.29 | 200 | SCOPE_DIFFERENCE |
| M5-GROUND_BEAMS-GROUND-NETWORK | 37.98 | 30.70 | 0.00 | 193 | THICKNESS_OR_DEPTH_DIFFERENCE + GEOMETRY_DIFFERENCE |
| M5-POOL_PUMP_ROOM-GROUND-PUMP_ROOM | 3.48 | 0.00 | 0.00 | 92 | SCOPE_DIFFERENCE |
| M5-STAIRS-ALL-ST-A | 8.13 | 5.17 | 0.00 | 78 | ASSUMPTION_DIFFERENCE |
| M5-BEAMS-1F-B25 | 0.00 | 2.84 | 0.00 | -75 | MISSING_IN_FREELANCER |
| M5-STAIRS-ALL-ST-C | 5.51 | 2.72 | 0.00 | 74 | ASSUMPTION_DIFFERENCE |
| M5-BEAMS-GF-B27 | 0.00 | 2.50 | 0.84 | -66 | MISSING_IN_FREELANCER |
| M5-BEAMS-1F-B6 | 0.55 | 2.68 | 0.00 | -56 | GEOMETRY_DIFFERENCE |
| M5-DOMES-ROOF-SHELLS | 6.78 | 5.08 | 0.00 | 45 | GEOMETRY_DIFFERENCE + SCOPE_DIFFERENCE |
| M5-DOMES-ROOF-RINGS | 0.00 | 1.65 | 0.00 | -44 | MISSING_IN_FREELANCER |

**Missing:**

- **In Urban's M4 base:**
  - three planted columns (fixed in V4, B);
  - the ground-slab cells under the lift lobby and the light-well stair (conditional);
  - 17 drawn beam spans no tag binds, incl. CB10 on 1F (conditional);
  - 46 lintels under beams (conditional).
- **In the freelancer's BOQ:**
  - the beams B27, B19, B25, B5 and B28 (and CA);
  - a second F3 footing;
  - the lobby steps ST-B;
  - the dome ring beams;
  - the lintels;
  - the cantilever portions.

**Double counted:**

- **In the freelancer's BOQ:**
  - the ground slab over 65.0 m2 of beams and columns (6.50 m3);
  - the perimeter beam (probable, 8.60 m3).
- **Avoided in M5:**
  - the water-tank roof slabs held by two registers;
  - the dome-A ring read by M4 as beams;
  - the dome-B opening read by M4 as a stair zone;
  - cantilever hatches read by M4 as unlabelled beams (11A).

### Top 5 risks

1. **RFI-M5-15**: Blinding scope: under footings and ground beams only (drawn), or a full-plot plate? (plain concrete, priced separately)
   - Swing 24.90 m3 (660 KWD); plain concrete.
2. **RFI-M5-01**: Beam schedule depth H: overall depth including the slab, or depth below the slab?
   - Swing 16.25 m3 (431 KWD); decides 110 measured beams.
3. **RFI-M5-07**: Dome ring depth ('AS PER ARCH'), the 1.30 m drum and the tower dome
   - Swing 7.57 m3 (201 KWD); 2 domes + tower.
4. **RFI-M5-16**: Confirm the 16 cm project slab default (two printed notes, machine-read only); range shown for +-1 cm
   - Swing 6.50 m3 (172 KWD); suspended slabs.
5. **RFI-M5-02**: Scope of the 'T=10cm, 5Ø10/m E.W.' ground-slab note: does the slab run in the lift / lobby cell (S8.1A candidates) and under the light-well stair cell?
   - Swing 4.90 m3 (130 KWD); two ground-slab cells.

## B. What changed

### Engine fix (Phase 8)

One confirmed defect is fixed: **planted columns labelled on a slab plan were not read.** The generic route read columns from the column plan only, so the three 'P.C 20x70' and 'P.C 20x50' labels on the GF and 1F slab sheets produced no column.

The fix is gated on the new conventions set `engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json`. That set is V3 plus `PLANTED_COLUMN_LABELS`. The CLI default stays V3, so the frozen M4 package still reproduces byte for byte.

| Engine run | RC m3 |
|---|---|
| before: V3 (frozen M4) | 289.891 |
| after: V4 (M5) | 291.319 |
| difference | 1.428 |

KWD impact: +37.8. The items are in 18; the bars stay MISSING_DATA (no ratio).

### M5 ownership decisions

They decide which register owns an element that two registers hold, and record what the frozen M4 run missed (11A). The M4 base changes only by D-02 (ring arcs reallocated to the domes) and D-06 (planted columns added):

| Id | Kind | Action | Base m3 | Exposure m3 dropped |
|---|---|---|---|---|
| D-01 | DOUBLE_COUNT_AVOIDED | EXCLUDE the S-stage rows; M4 SLABS owns them | 2.45 | 0.00 |
| D-02 | DOUBLE_COUNT_AVOIDED | REALLOCATE to DOMES: the S8.3 ring beam owns this concrete; M4 beam base and exposure removed | 0.28 | 0.67 |
| D-03 | FALSE_EXPOSURE_REMOVED | DROP the exposure: the face is the dome opening, not a stair zone | 0.00 | 2.74 |
| D-04 | OWNERSHIP_CHECKED | per band: M4 bound beam keeps it; an M4 unlabelled span is superseded by the cantilever portion; the cantilever value stays CONDITIONAL (thickness not printed) | 0.06 | 3.49 |
| D-05 | UNRESOLVED_DECOMPOSED | split the unresolved cell by the S8.1A regions: slab candidates are CONDITIONAL ground slab; the stair zone, lift walls and ground-beam pieces are not ground slab | 0.00 | 0.00 |
| D-06 | MISSING_DETECTION_ADDED | ADD as measured: printed section in the label x storey height | 1.43 | 0.00 |

### Classification of every candidate defect

| Id | Finding | Class | Action |
|---|---|---|---|
| E-01 | planted columns labelled on slab plans ('P.C 20x70') are not read | MISSING_DETECTION (confirmed: printed label, S8.5 population, freelancer rows) | FIXED in V4 (PLANTED_COLUMN_LABELS); +3 columns |
| E-02 | the dome-A ring arcs on the 1F sheet are bound to the straight-beam tag B4 | UNRESOLVED_INTERPRETATION (the ring depth is 'AS PER ARCH') | M5 decision D-02 (S8.3 owns the ring); no generic rule |
| E-03 | dome-B radial lines read as winder treads (stair zone) | INCORRECT_CLASSIFICATION, fail-safe (unresolved, not in the base) | M5 decision D-03; not fixed generically (a spiral stair fans the same way) |
| E-04 | the S-BW lift-pit outlines are not used as ground-slab face edges | MISSING_DETECTION (exposure only: the cell is unresolved) | M5 decision D-05; RFI-M5-02 decides the cell |
| E-05 | cantilever hatches read as unlabelled beams | UNRESOLVED_INTERPRETATION (exposure only) | M5 decision D-04 |
| E-06 | the M4 headline concrete total adds plain concrete to RC | REPORTING_ONLY (the summary keeps concrete_rc separately) | M5 reports RC and plain apart; the frozen M4 text is not edited |
| E-07 | two registers hold the water-tank roof slabs | REPORTING_ONLY | M5 decision D-01 |

### New unresolved or conditional items

- **Boundary wall:** a drawn run of 44.07 m on layer S-BOUN, valued 3.53 - 5.29 m3 for the beam only. Pads and columns: spacing not printed.
- **The p.1 note B neighbour-side beam:** 0 - 3.17 m3.
- **The lift / lobby ground-slab cell, split by S8.1A:** slab candidates 29.06 m2.

## C. What is still unanswered (minimum questions)

| # | RFI | To | Question | Low m3 | High m3 | Swing KWD | Note |
|---|---|---|---|---|---|---|---|
| 1 | RFI-M5-15 | Client / specification | Blinding scope: under footings and ground beams only (drawn), or a full-plot plate? (plain concrete, priced separately) | 22.16 | 47.05 | 660 | plain concrete |
| 2 | RFI-M5-01 | Structural engineer | Beam schedule depth H: overall depth including the slab, or depth below the slab? | 64.54 | 80.79 | 431 | - |
| 3 | RFI-M5-07 | Structural engineer + architect | Dome ring depth ('AS PER ARCH'), the 1.30 m drum and the tower dome | 6.74 | 14.30 | 201 | - |
| 4 | RFI-M5-16 | Person check | Confirm the 16 cm project slab default (two printed notes, machine-read only); range shown for +-1 cm | -3.25 | 3.25 | 172 | - |
| 5 | RFI-M5-02 | Structural engineer | Scope of the 'T=10cm, 5Ø10/m E.W.' ground-slab note: does the slab run in the lift / lobby cell (S8.1A candidates) and under the light-well stair cell? | 0.00 | 4.90 | 130 | - |
| 6 | RFI-M5-03 | Structural engineer + architect | Exterior ground beams 'FOLLOW ARCH.': the depth from GF +1.00 to the outer ground level, at the +0.30 / +0.15 annex and court edges; and the p.13 class basis (c/c or clear length) | 26.94 | 31.58 | 123 | - |
| 7 | RFI-M5-06 | Structural engineer + architect | Stair waist thickness and the GF -> 1F riser arrangement (27 / 28 risers, B20 clash) | 7.56 | 12.13 | 121 | - |
| 8 | RFI-M5-04 | Structural engineer | Section of the drawn beam spans no tag binds (incl. the two CB10 tags on the 1F slab sheet, ambiguous between a 200 and a 300 band) | 5.06 | 9.58 | 120 | - |
| 9 | RFI-M5-12 | Structural engineer | CN column / neck type (not in the schedule) and the neck sections without a bound footing | 1.54 | 5.51 | 105 | - |
| 10 | RFI-M5-11 | Architect | Door / window head heights against the beam soffits (lintel needed only if the head is below the soffit) | 0.00 | 3.42 | 91 | - |
| 11 | RFI-M5-05 | Structural engineer | Founding level (only 'excavation >= 1.50 m below plot level' is printed): necks, lift pit walls | 0.00 | 3.22 | 85 | - |
| 12 | RFI-M5-08 | Structural engineer | p.1 note B (neighbour-side external ground beams: upper + lower beam over a black-brick wall): is there a second beam on the neighbour side, and is it the B.W row? | 0.00 | 3.17 | 84 | - |
| 13 | RFI-M5-09 | Client + structural engineer | Is the boundary wall in the contract? Which section governs (p.14 typical GB 20 x 40 or schedule row B.W 20 x 60), and the pad / column spacing? | 3.53 | 5.29 | 47 | - |
| 14 | RFI-M5-10 | Architect + pool specialist | Pool floor profile (flat vs deep end / slope), steps, and where the pump / plant room is (not drawn) | 6.50 | 7.44 | 25 | - |
| 15 | RFI-M5-13 | Structural engineer | Thickness of the hatched cantilever portions | 0.68 | 0.68 | 0 | - |
| 16 | RFI-M5-14 | Structural engineer | Water-tank base and walls (only the roof slab is drawn) | 0.00 | 0.00 | 0 | not measurable: not drawn |
| 17 | RFI-M5-17 | Architect + structural engineer | Parapets: RC or masonry, and their geometry | 0.00 | 0.00 | 0 | not measurable: not drawn |

## D. Recommendation

**NOT QUOTATION-READY for a fixed price.** The blockers are:

1. **RFI-M5-01, the beam depth reading:** 16.25 m3.
2. **The ground-slab extent and the exterior ground-beam depth (RFI-M5-02, -03)**, plus the unlabelled spans (RFI-M5-04).
3. **Elements with no drawing:** the pump room, the water-tank base and walls, the parapets, the boundary-wall pads and columns, and the tower dome / drum.

**Closest defensible schedule:**

- **Quote the measured base, 316.06 m3 RC, as provisional quantities** (remeasurable), with the conditional allowances 14.55 - 35.38 m3 as separately listed items.
- **Add the blinding as its own line:** 22.16 m3 drawn, or the full-plot alternative.
- **List the unmeasurable items as exclusions or provisional sums.** Never price them at zero.
- **Use a variation mechanism** for the RFI outcomes. The 12 workbook gives every line at 26.5 KWD/m3.

Do not take the freelancer's total as a target. It contains items with no drawing behind them and a probable double count. It also misses drawn beams, some column occurrences, the dome rings and the lintels.

