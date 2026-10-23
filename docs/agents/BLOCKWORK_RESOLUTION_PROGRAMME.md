# Blockwork resolution programme (owner 2026-10-23, main chat 15:45 UTC)

Owner request (his words, abridged only by line breaks): "Please expand the current blockwork reconciliation task into a
complete evidence-based resolution exercise. Objective: Reconcile the freelancer, older automated takeoff and current
engine quantities, while actively resolving as many HELD, provisional and unconfirmed blockwork items as possible from
the available project drawings. [...] Do not use arbitrary default heights, invented opening sizes or unsupported
assumptions merely to reduce the HELD total. [...] Success means materially increasing independently verified net
blockwork coverage - not simply reclassifying held quantities or making the totals resemble the freelancer's BOQ."
Full text: OWNER_SESSION_CHANGES.md row 2026-10-23 15:45 and the main chat. Released stays V2.9 + route G; the pilot
schedule is not changed by this programme.

## 1. Packages (lane A, Worker 2; Checker Gate A on each; no duplicate of an existing row)

| Row | Package | Owner items | Order |
|---|---|---|---|
| T-225 | Sources and three-way reconciliation, wall register v1, before-coverage | 1, 2, 6, 7, 9 (before) | first |
| T-226 | Heights: walls with no member drawn above or a beam-depth / register conflict; the 19 column-containing walls (D-12); column footprints and T-junction / L-corner audit | 4, 5, 8 | after T-225 |
| T-227 | Annex datum (Q-54 B evidence test), lift walls (ST p.8 note 19 tie beam, lift details), lift openings, the 400 mm strip GF-H01 and GF-H02, 1F partitions under the dome openings, remaining window heads | 4, 5, 8 | after T-225 |
| T-222 (existing) | P-1F-01, P-GF-05, the 1F bay basis | 5 | after T-225 |
| T-017 (existing) | Independent masonry census (no shared code with the engine): the length check the Checker uses for VERIFIED | 7, 10 | any time |
| T-228 | Resolution ledger (register v2, new file) and after-coverage report; owner items only under ERS s.2.7 | 6, 7, 9, 10 | after T-222, T-226, T-227 |

## 2. Status classes (owner 2026-10-23) and their board meaning

| Owner class | Meaning | Board status it replaces |
|---|---|---|
| VERIFIED | the Checker re-measured this wall's length, height and deductions independently and they agree | VERIFIED |
| SOURCE-SUPPORTED PENDING INDEPENDENT CHECK | every input read from a cited project drawing, not yet re-measured by the Checker | DRAWING-CONFIRMED |
| PROJECT-SPECIFIC | an owner-approved project or Urban rule supplies an input (e.g. Q-55 C door height, Q-60 A height rule, Q-75 provisional block module) | ASSUMED — OWNER-APPROVED |
| OWNER DECISION REQUIRED | the drawings conflict or are silent and no answered rule covers it; asked only under ERS s.2.7 in its s.6 format | (owner question) |
| HELD | evidence missing; the exact missing item and the smallest affected quantity are named; never 0, never a default | HELD |

## 3. Baseline (engine MASONRY_AREA_V1 r2, T-108 r2, checker MERGED 01eeafd0; working head 41847bf)

Black blockwork: gross 554.49 m2 = 150 mm 342.91 (source-supported 215.72, HELD 127.19) + 200 mm 211.58 (source-supported
125.88, HELD 85.70); deductions 36.08 (29.92 / 6.16); net with a figure 290.05 (150: 103.33 source-supported + 79.00
project-specific; 200: 107.72 source-supported). No 100 mm wall in the census. Independently VERIFIED net: 0 m2 (no
blockwork wall has had a full Checker re-measure of length, height and deductions; GF-W01 gross was re-measured in
T-143, net not).

Why confirmed gross - deductions is not the net (main chat trace, 15:40; T-225 reproduces it independently):
- 150 mm, 3.464 m2 = +16.223 (1F-W14 + W15: gross source-supported, net HELD on P-1F-01) - 12.760 (deductions booked
  on six walls whose gross is HELD: GF-W24 1.760, GF-W27 1.760, 1F-W11 1.760, 1F-W13 3.960, 1F-W16 1.760, 1F-W17 1.760)
  + 0.001 rounding.
- 200 mm, 12.001 m2 = +9.341 (1F-W07, net HELD on L-1F-01) + 6.840 (2F-W00, net HELD on L-2F-01) - 2.200 (GF-W08) -
  1.980 (2F-W05), deductions on held-gross walls.

## 4. HELD worklist at the start (every wall whose gross or net is HELD; from T108_BY_WALL.csv)

| Wall | Floor | Type | t (m) | Gross m2 | Gross status | Net status | Held openings | Cause class | Hold reason (engine) |
|---|---|---|---|---|---|---|---|---|---|
| GF-W00 | GF | BLACK | 0.2 | 32.175 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W02 | GF | BLACK | 0.2 | 6.336 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W03 | GF | BLACK | 0.2 | 0.000 | HELD | HELD |  | beam depth / register conflict | beam CB3 and B3 (With Stair) depth not established (register HELD (T-110: two marks D-03, candidate CB3 0.75 / B3 0.40: 2.64 m -> h HELD (ca |
| GF-W04 | GF | WHITE | 0.2 | 19.012 | HELD | HELD | W04;W08 | held opening | held opening(s): W04;W08 |
| GF-W06 | GF | WHITE | 0.2 | 9.000 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W07 | GF | WHITE | 0.2 | 4.018 | HELD | HELD |  | no member drawn above | no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at) |
| GF-W08 | GF | BLACK | 0.2 | 17.565 | HELD | HELD | L-GF-01 | lift tie beam size (ST p.8 n.19) | ST p.8 note 19 lift tie beam (size not printed): its strip is not deducted; held opening(s): L-GF-01 |
| GF-W09 | GF | BLACK | 0.2 | 7.380 | HELD | HELD |  | lift tie beam size (ST p.8 n.19) | ST p.8 note 19 lift tie beam (size not printed): its strip is not deducted |
| GF-W10 | GF | WHITE | 0.2 | 23.543 | HELD | HELD | W05;W06;W07 | beam depth / register conflict | beam CB2 depth not established (register CONFLICT (T-110: member CONFLICT in the T-110 register (Q-61 C); candidate 4.0 m: 3.36 m -> h HELD  |
| GF-W13 | GF | BLACK | 0.2 | 2.870 | HELD | HELD |  | lift tie beam size (ST p.8 n.19) | ST p.8 note 19 lift tie beam (size not printed): its strip is not deducted |
| GF-W14 | GF | BLACK | 0.2 | 15.556 | HELD | HELD | P-GF-01 | lift tie beam size (ST p.8 n.19) | ST p.8 note 19 lift tie beam (size not printed): its strip is not deducted; held opening(s): P-GF-01 |
| GF-W15 | GF | WHITE | 0.2 | 28.632 | DRAWING-CONFIRMED | HELD | D-GF-07 | held opening | held opening(s): D-GF-07 |
| GF-W16 | GF | WHITE | 0.2 | 19.154 | DRAWING-CONFIRMED | HELD | W09;W10 | held opening | held opening(s): W09;W10 |
| GF-W17 | GF | WHITE | 0.2 | 13.320 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W18 | GF | WHITE | 0.2 | 19.825 | HELD | HELD | W11;W12 | held opening | held opening(s): W11;W12 |
| GF-W23 | GF | BLACK | 0.15 | 4.992 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W24 | GF | BLACK | 0.15 | 17.280 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W25 | GF | BLACK | 0.15 | 17.280 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W26 | GF | BLACK | 0.15 | 15.575 | HELD | HELD | A-GF-01 | held opening | held opening(s): A-GF-01 |
| GF-W27 | GF | BLACK | 0.15 | 5.760 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W30 | GF | BLACK | 0.15 | 0.000 | HELD | HELD | D-GF-14 | held opening | no member above bound to this run; held opening(s): D-GF-14 |
| 1F-W00 | 1F | WHITE | 0.2 | 22.669 | DRAWING-CONFIRMED | HELD | W16 | held opening | held opening(s): W16 |
| 1F-W04 | 1F | WHITE | 0.2 | 10.553 | HELD | HELD |  | beam depth / register conflict | beam (none) depth not established (register HELD (T-110: depth not printed; T-110 candidate depths 0.40 .. 1.20 (Q-61 C, designer): 0.80 m - |
| 1F-W05 | 1F | WHITE | 0.2 | 0.771 | HELD | HELD |  | beam depth / register conflict | beam CB10 depth not established (register CONFLICT (T-110: CONFLICT D-02 on width only, schedule depth 0.50 -> candidate 3.7 m: 2.30 m -> h  |
| 1F-W06 | 1F | WHITE | 0.2 | 57.772 | DRAWING-CONFIRMED | HELD | W19;W20;W24 | held opening | held opening(s): W19;W20;W24 |
| 1F-W07 | 1F | BLACK | 0.2 | 11.321 | DRAWING-CONFIRMED | HELD | L-1F-01 | held opening | held opening(s): L-1F-01 |
| 1F-W10 | 1F | WHITE | 0.2 | 47.869 | DRAWING-CONFIRMED | HELD | W21;W22;W23;W25 | held opening | held opening(s): W21;W22;W23;W25 |
| 1F-W11 | 1F | BLACK | 0.15 | 0.444 | HELD | HELD |  | beam depth / register conflict | beam CB10 depth not established (register CONFLICT (T-110: CONFLICT D-02 on width only, schedule depth 0.50 -> candidate 3.7 m: 0.12 m -> h  |
| 1F-W13 | 1F | BLACK | 0.15 | 14.916 | HELD | HELD |  | no member drawn above | no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at) |
| 1F-W14 + 1F-W15 | 1F | BLACK | 0.15 | 16.223 | DRAWING-CONFIRMED | HELD | P-1F-01 | held opening | held opening(s): P-1F-01 |
| 1F-W16 | 1F | BLACK | 0.15 | 20.846 | HELD | HELD | A-1F-01 | beam depth / register conflict | beam B6 depth not established (register CONFLICT (T-110: member CONFLICT in the T-110 register (Q-61 C); candidate 3.7 m: 0.26 m -> h HELD ( |
| 1F-W17 | 1F | BLACK | 0.15 | 6.516 | HELD | HELD |  | no member drawn above | no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at) |
| 1F-W18 | 1F | BLACK | 0.15 | 17.934 | HELD | HELD |  | no member drawn above | no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at) |
| 1F-W24 | 1F | BLACK | 0.15 | 5.651 | HELD | HELD |  | no member drawn above | no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at) |
| 2F-W00 | 2F | BLACK | 0.2 | 6.840 | DRAWING-CONFIRMED | HELD | L-2F-01 | held opening | held opening(s): L-2F-01 |
| 2F-W02 | 2F | WHITE | 0.2 | 21.818 | HELD | HELD | W27;W28;W29 | beam depth / register conflict | beam (none) depth not established (register HELD (T-110: depth not printed; T-110 candidate depths 0.40 .. 1.20 (Q-61 C, designer): 0.92 m - |
| 2F-W03 | 2F | WHITE | 0.15 | 27.993 | HELD | HELD |  | beam depth / register conflict | beam (none) depth not established (register HELD (T-110: depth not printed; T-110 candidate depths 0.40 .. 1.20 (Q-61 C, designer): 0.26 m - |
| 2F-W05 | 2F | BLACK | 0.2 | 3.817 | HELD | HELD |  | beam depth / register conflict | beam (none) depth not established (register HELD (T-110: depth not printed; T-110 candidate depths 0.40 .. 1.20 (Q-61 C, designer): 1.24 m - |
| 2F-W07 | 2F | WHITE | 0.2 | 8.222 | HELD | HELD |  | beam depth / register conflict | beam (none) depth not established (register HELD (T-110: depth not printed; T-110 candidate depths 0.40 .. 1.20 (Q-61 C, designer): 2.94 m - |
| GF-W35 | GF | WHITE | 0.2 | 6.975 | HELD | HELD |  | annex datum (Q-54 B) |  |
| GF-W36 | GF | WHITE | 0.2 | 0.000 | HELD | HELD |  | no member drawn above | no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at) |
| GF-W37 | GF | WHITE | 0.2 | 0.000 | HELD | HELD |  | no wall band or member bound (glazed line / held strip) | no member above bound to this run |
| GF-H01 | GF | - | 0.4 | 0.000 | HELD | HELD |  | no wall band or member bound (glazed line / held strip) | no member above bound to this run |
| GF-H02 | GF | - | 0.2 | 0.000 | HELD | HELD |  | no wall band or member bound (glazed line / held strip) | no member above bound to this run |

| Type | t | Cause | HELD gross m2 |
|---|---|---|---|
| - | 0.2 | no wall band or member bound (glazed line / held strip) | 0.00 |
| - | 0.4 | no wall band or member bound (glazed line / held strip) | 0.00 |
| BLACK | 0.15 | beam depth / register conflict | 21.29 |
| BLACK | 0.15 | held opening | 15.57 |
| BLACK | 0.15 | no member drawn above | 45.02 |
| BLACK | 0.15 | annex datum (Q-54 B) | 45.31 |
| BLACK | 0.2 | beam depth / register conflict | 3.82 |
| BLACK | 0.2 | held opening | 0.00 |
| BLACK | 0.2 | lift tie beam size (ST p.8 n.19) | 43.37 |
| BLACK | 0.2 | annex datum (Q-54 B) | 38.51 |
| WHITE | 0.15 | beam depth / register conflict | 27.99 |
| WHITE | 0.2 | beam depth / register conflict | 64.91 |
| WHITE | 0.2 | held opening | 38.84 |
| WHITE | 0.2 | no member drawn above | 4.02 |
| WHITE | 0.2 | annex datum (Q-54 B) | 29.30 |
| WHITE | 0.2 | no wall band or member bound (glazed line / held strip) | 0.00 |

walls per cause: {'annex datum (Q-54 B)': 9, 'beam depth / register conflict': 10, 'held opening': 12, 'no member drawn above': 6, 'lift tie beam size (ST p.8 n.19)': 4, 'no wall band or member bound (glazed line / held strip)': 3}

## 5. Rules for every package

- Project drawings first (architectural DXF / PDF plans, sections A-A and B-B, elevations, ST plans, schedules and
  notes); a generic convention only where an answered owner rule names it, labelled PROJECT-SPECIFIC with its source.
- Never a default height, an invented opening size, the freelancer's value or the larger / smaller end to close a HELD
  item. A conflict between two drawings stays a range for the designer (never picked); missing evidence stays HELD
  with the exact missing item (sheet, dimension, member) and the smallest quantity it holds.
- Every wall row carries: wall id, floor, black / white, thickness, length, height, gross, deductions, net, evidence
  (Drive title + sheet / DXF handle; never copied content, coordinates, images or client names), calculation, owner
  status class, unresolved reason.
- Each package hands in its changed rows and a before / after table by floor x thickness x type; the Checker re-measures
  EVERY wall whose class rises (not a sample) before it is VERIFIED; until then it is SOURCE-SUPPORTED. Regression at
  the impact level and freeze 0 on every package; tests with a non-Alsenan fixture and an adverse case.
- Freelancer and older automated quantities are comparison columns only, never an input or a target.
