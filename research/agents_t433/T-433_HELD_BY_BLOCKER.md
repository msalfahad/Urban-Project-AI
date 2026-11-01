# T-433 HELD concrete by blocker (research only; engine READ ONLY)

The HELD part of the merged r4 concrete roll-up (T-428 MERGED ea8f5ae5, Checker-restated basis traced -1.300165 /
**HELD -116.428339** / unexplained -5.171754 m3, engine - freelancer, candidate V3.0.37 = V3.0.38 for valued concrete)
split by the item that holds it. No line, value, state or released cell changes; no held line is valued. HELD means
engine 0 (blank or range) against the other side's figure: every item below is a withheld engine quantity, never 0,
never agreement. Engine-side and residual figures in m3 only; no freelancer row text.

## Inputs (all asserted in `t433_alsenan.py`)

- Part figures read from merged summaries: T-428 families (HELD per family, total), T-406 retraced HELD parts (BW-BAND,
  GB-BOUNDARY, GS-SLAB cell, CL-GF members, CL-LIFT, SD-DOME-3, SD-ST01 / ST03 parts, PL-PUMP), T-428 restated parts
  (ST-02 RS-C -1.244067, GB annex length fields +0.275940), T-397 rows (the 15 V3.0.33 column CONFLICT moves, per line),
  T-395 marks (held beam runs per mark), T-391 (53.8353 m held ground-beam runs at his one section 0.30 x 0.60).
- Ground-beam held runs split by line: 8 D-35 lines 31.5364 m, 3 court lines 5.7000 m, 9 D-34 lines (downgrade
  DG-a31a0d7e9dd564ad) 16.5989 m = 53.8353 m (= T-391 held_length_m, asserted), each x 0.18 m2.
- CL-NECK -8.805 / CL-2F -3.381 (the unchanged T-385 r2 column-family HELD -12.186 by component): rebuilt this run from
  the Drive workbook (Urban BOQ private data / Alsenan chalet project / the concrete + rebar workbook) with
  `t385_extract.py` + `t385_alsenan.py` into `.work/private` on the committed V3.0.29 lines (521 + 4 parapet): residual
  -114.464428, HELD -77.593, unexplained -37.123829, the Checker's T-385 r2 headline exactly; the column family closes
  to the merged -24.3375 (asserted).
- Family closure: the 34 parts re-add per family to the T-428 r4 HELD column in all 10 families and to -116.428339 in
  total (R-T433-1, asserted to 2e-6).

## Result: 25 blocker items (ranked by m3)

| Item | m3 | Blocker (designer list / owner Q) | Lines | Route | RFI |
|---|---|---|---|---|---|
| I-01 | -47.055000 | JOINT: footing blinding DG-3521554d (FF raft projection not printed, D-14 plot-line footings), F10 + F (Q-31 C), ground-beam blinding (D-34 / D-35 section choice), strap blinding (D-15) | 4 | DESIGNER | S06, S07, S08, S02, S09, S11 |
| I-02 | -8.805000 | Q-21 C founding / neck start level (36 necks) | 36 | DESIGNER | S01 |
| I-03 | -8.458800 | lower boundary band depth, DG-6dd9f1caba1ca77d (Q-28) | 1 | DESIGNER | S03 |
| I-04 | -6.670500 | 13 column outlines vs schedule bands (D-66): GF 3 lines -1.4625, 1F 10 lines -5.2080 (V3.0.33 CONFLICT moves) | 13 | DESIGNER | S20 |
| I-05 | -5.400612 | D-35 exterior / annex ground-beam depth 'FOLLOW ARCH.' (31.5364 m x 0.18 = -5.676552, + length fields through necks +0.275940) | 8 | DESIGNER | S09 |
| I-06 | -4.470543 | D-27 schedule vs drawn width: GF B21 -2.524568, B29 -1.263975, CB2 -0.682000 | 4 | DESIGNER | S13 |
| I-07 | -3.560540 | ground-slab cell L-41cfb82e: engine reads the lift-shaft corner columns as free columns (T-042 ENGINE_MISSED_PRINTED_VALUE) | 1 | **ENGINE** | none needed |
| I-08 | -3.525600 | M4 boundary-wall columns 'SEE ARCH PLAN', none drawn | 1 | DESIGNER | S04 |
| I-09 | -3.480000 | pool pump / plant room drawn on no sheet | 0 (named item) | DESIGNER | B-A14 (T-398 draft; **not in the 2026-10-31 register**) |
| I-10 | -3.381000 | JOINT: D-39 roof datum (9 lines), D-44 B15 (2), section conflict (2), planted PC-2F section text vs outline (1) | 9 | DESIGNER | S23, S22, **missing** (PC-2F section) |
| I-11 | -2.987802 | D-34 length basis / title precedence of the p.13 sections (16.5989 m x 0.18) | 9 | DESIGNER | S11 |
| I-12 | -2.260000 | D-21 tower dome over the 2F maid room (Q-27 A) | 1 | DESIGNER | S28 |
| I-13 | -2.062500 | JOINT: annex roof datum (Q-54 B / D-17), D-39, section conflict (4 of 5) | 5 | DESIGNER | S23, S20 |
| I-14 | -1.960000 | Q-31 C: F10 + F one outline, two tags | 1 | DESIGNER | S02 |
| I-17 | -1.780800 | JOINT: C-ST-4 MS1-L riser count, MS1-T winders not drawn (S-9) | 1 | DESIGNER | A04, S24 |
| I-16 | -1.768500 | D-16 column C8 30X80 vs 30 x 90 (GF -1.0125, 1F -0.756) | 2 | DESIGNER | S19 |
| I-15 | -1.764375 | D-04 unlabelled spans: GF B24 -0.562875, 1F B2 -0.064, 2F B15 -0.744, B1 -0.224, B8 -0.1695 | 6 | DESIGNER | S15 |
| I-18 | -1.650000 | JOINT: lift pit depth (lift supplier) + GF floor build-up (D-22 / D-40) | 1 | SUPPLIER | L-1 (T-401), B-A01 (by title) |
| I-19 | -1.411200 | E1 waist thickness not printed | 1 | DESIGNER | S26 |
| I-20 | -1.244067 | ST-02 RS-C soffit / waist (Q-50) | 1 | DESIGNER | S27 |
| I-21 | -1.026000 | court ground-beam section (GS-16 architect item), 5.70 m x 0.18 | 3 | DESIGNER | **missing** |
| I-22 | -0.744000 | D-02 CB10 width | 2 | DESIGNER | S12 |
| I-23 | -0.397500 | D-03 CB3 / 'B3 (with stair)' | 1 | DESIGNER | S14 |
| I-24 | -0.336000 | JOINT: MS1-T turn slab, MS2-TR turn riser (landing levels not printed) | 1 | DESIGNER | S24, S25 |
| I-25 | -0.228000 | pool steps not drawn | 1 | DESIGNER | A02 |
| **Total** | **-116.428339** | | 113 | | |

By route: DESIGNER -111.217799, SUPPLIER -1.650000, ENGINE -3.560540, DRAWING 0.000000. Every part in exactly one
item, every line in at most one item (`check_items`, asserted). JOINT items are never split by a share: the other side
carries them as one lump, so they unlock only when every listed fact is answered.

## Investigation tasks (drawing / engine settleable), ranked

1. **I-07 -3.560540 m3 (ENGINE)**: the own read exists (T-391 MERGED: panels OWN-007 / 009 / 010 / 047 = 35.6054 m2 x
   printed T 0.10 on the slab-on-grade plan; T-397 bound 0 .. 3.56054). The line is held only because the engine reads
   the four lift-shaft corner columns as free columns. Proposal: a lane S / lane I task to bind the cell to its own
   pieces (shaft 3.24 m2 and strips 2.9883 m2 out), Checker re-measure of the 4 panels; the comparison term then
   becomes traced (ENGINE_RIGHT or a slab-under-member difference), not an RFI.

No other item passes the ERS s.2.7 test the other way: for each, the merged investigations named in `summary_t433.json`
searched the sheets listed there and no sheet prints the missing fact (or two issued sheets print conflicting facts).
Beside I-01 (not a split): the Checker-VERIFIED footing layer 12.734438 m3 (T-322) is valued in no candidate line;
valuing it is a lane I action, but it does not separate the other side's one lump.

## RFI list by m3 (designer / supplier items)

Sole-blocker items (one RFI unlocks the whole item): S01 -8.805, S03 -8.4588, S20 -6.6705, S09 -5.400612, S13
-4.470543, S04 -3.5256, B-A14 -3.48, S11 -2.987802, S28 -2.26, S02 -1.96, S19 -1.7685, S15 -1.764375, S26 -1.4112,
S27 -1.244067, court (missing) -1.026, S12 -0.744, S14 -0.3975, A02 -0.228. Joint items (all listed RFIs needed):
blinding -47.055 (S06 + S07 + S08 + S02 + S09 + S11; a scope RULE_DIFFERENCE remains after all answers: his one layer
over a rectangle is printed nowhere), CL-2F -3.381, CL-GF members -2.0625, MS1-L -1.7808, lift pit -1.65, turns -0.336.
Ranked per RFI with joint items counted in full under each (ranking aid only, never re-added): S09 -52.456, S11
-50.043, S02 -49.015, S06 / S07 / S08 -47.055, S01 -8.805, S20 -8.733, S03 -8.459, S23 -5.444, S13 -4.471, ...
(`rfi_ranked` in the summary).

## Held with no comparison term (beside, not in the -116.428 m3; 27 lines)

Engine held lines the other side has no row for (or no separable row): 4 parapet RC (T-319), 5 columns TYPE_NOT_IN_SCHEDULE
(D-65), D-26 projection strips (GF / 1F / 2F, RFI-S18), D-05 edge strips (5 lines, RFI-S16), 1F B6 D-27 run with no row,
1F east dome ring (D-28, RFI-S17), 3 unbound / unlabelled beam bands, SB1 / SB3 parts inside footings (Q-31 C, RFI-S05),
stair-hall D1 waist (RFI-S26), the V3.0.35 boundary pad line (pad count not printed, 0.312 m3 per pad beside). The
T-428 engine-side register E-1 .. E-4 (GB-MAIN unloaded / loaded halves, D-34 0.40-end runs, 177+7CD#1) is printed
beside too; none enters the split.

## Own drawing reads this run

- `ST7757 dxf.dxf` (Drive, sha 9f9d1179) text search (TEXT / MTEXT / ATTRIB in model space and every block): pump,
  plant, machine, filter, ladder, step, court: one hit, 'COURT' (handle 154); no plant room, pump, ladder or step text
  (I-09, I-25 confirmed absent in English text; the Arabic notes use a legacy font encoding, so an Arabic text search is
  not conclusive). No ground-beam section title is drawn in the DXF beyond 'GROUND BEAMS PLAN'.
- `ST7757.pdf` p.13 (DETAILS) read as an image: four ground-beam sections, titled 'More than 5m length without
  concentrated load', 'Less than 5m length without concentrated load', 'Less than 2.5m length' and 'for exterior walls'
  ('FOLLOW ARCH.', outer normal ground level); none names the court (I-21 stays a designer item: whether the court runs
  are 'exterior walls' depends on a court ground level no structural sheet prints); blinding '10cm Plain con.' drawn
  under footings and ground beams only, none under straps (I-01, D-15).

## Findings (for the Lead; no figure moves)

- **F-T433-1**: the T-406 / T-428 cause text for CL-LIFT -1.650 cites D-43, which is the GF lift tie-beam SIZE. T-401
  (merged) names the two facts that hold the pit-wall height: the pit depth (lift supplier, RFI L-1) and the GF floor
  build-up (not printed). I-18 carries the T-401 blockers.
- **F-T433-2**: the V3.0.33 CONFLICT basis of 13 of the 15 column lines cites "D-63" (lift columns on the lift raft);
  the population is the designer list's D-66 (13 columns whose outline and schedule band differ: GF 3 + 1F 10,
  matches exactly) = RFI-S20. Label only; ranges unchanged.
- **F-T433-3 (RFI gaps)**: no RFI in the 2026-10-31 register covers the court ground-beam section (I-21, -1.026 m3),
  the pool plant room (RFI-B-A14 drafted in T-398 but not in the register, I-09, -3.48) or the planted column PC-2F
  section conflict (part of I-10).
- **F-T433-4**: 40.4 % of the HELD figure (-47.055 of -116.428) is one blinding lump that answers cannot fully close:
  after RFI-S06 / S07 / S08 / S02 / S09 / S11 the engine side is valued, but the difference to a single plain layer over
  a rectangle stays a scope RULE_DIFFERENCE (T-385 proposal). The next largest single RFIs by m3 are S01 (necks), S03
  (boundary band), S20 (column bands), S09 (D-35 depth).

## Method (t433_rules.py, R-T433-1 .. 7; every villa)

Split exact to 2e-6; each part in exactly one item; a jointly held lump is one JOINT item naming every fact, never split
by a share; each line in at most one item; held lines with no comparison term listed beside with their blocker; held
never 0 or positive; each item names drawings searched and a route (DRAWING with the drawing named / ENGINE / DESIGNER
or SUPPLIER with an RFI id or RFI_MISSING); no item values a held line; investigation and RFI lists ranked by m3.

Tests `tests/t433_held_blockers` (24): Villa R433 hand fixture (not Alsenan) normal, order invariance, ranking; adverse:
part in two items, part left out, line in two items, beside line also in an item, beside without blocker, items not
re-adding to the roll-up, item figure not its parts (neck fields dropped), held 0 / positive, unknown part, no drawing
searched, DRAWING route without the drawing, designer route without RFI, joint blockers without the JOINT flag, a value
chosen for a held line, unknown route; Alsenan pins (total, 25 items / 34 parts, D-35 / D-34 / court by length, column
moves, D-27, routes, beside disjoint, summary reproduces, a moved component split breaks the family closure).

## Proposed lessons-register row (ERS section 7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | The roll-up carried -116.428 m3 HELD as one column; which answer unlocks how much was not visible, two cause texts cited the wrong designer item (D-43 for the lift pit, D-63 for 13 column bands) and three blockers had no RFI (T-433) | HELD was recorded per component with free-text causes, never bound to the designer list or the RFI register | a roll-up's HELD figure is split by blocker item with every part in exactly one item, jointly held lumps as one JOINT item (never shared out), each item routed DRAWING / ENGINE / DESIGNER / SUPPLIER with the drawings searched and an RFI id or RFI_MISSING; held lines without a comparison term are listed beside (every villa, every reconciliation; provenance T-433) | tests/t433_held_blockers (part in two items / none refused; joint split refused; designer item without RFI refused; DRAWING route without the drawing refused) | PROPOSED |
