# T-317: spatter dash (B4-05, m2) and mesh at block-to-concrete joints (B9-03, m.l) as physical-element ledgers (development villa; every villa by R-T317-1 .. 5)

Worker 2 (lane A), claim 2026-10-28 21:45 UTC, base working head 8943b5ed. Research only: no engine module, rule,
knowledge or registry file changed; no candidate or released line moves; released default stays V2.9 + route G; nothing
here is released. Inputs are MERGED ledgers of this repository (register v4 T-288, T-274 run pieces, T-261 r3, T-305,
T-312, T-244 / T-292 line extracts). Drawings read this run only for a text census: Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`), decoded into the private folder; no
coordinate, image, client name or drawing content is committed. ERS read: s.2.1 (define the element first), s.2.2
(evidence hierarchy, owner method beside the drawing-derived method), s.2.4 (reconcile in units, residual named), s.3
(physical vs payable; build before deduct), s.4 (rule + test, normal and adverse), s.7 (lessons row below).

## 1. Engineering question and the answer

**What are spatter dash and joint mesh physically, where do they apply, and how much is there?**

- **Spatter dash (طرطشة)** is the cement-slurry bond coat thrown on a wall face before the coat that finishes it. Where
  it applies is a scope fact, and the owner has answered it for this villa: **OD-V3B-4 .. 7 (owner, 2026-10-04,
  research/external_engine_lab/alsenan_v3b_owner_decisions.json)**: dry internal walls SPATTER -> ROUGH -> SMOOTH ->
  PAINT ("separate items on the same geometric population"); tiled faces SPATTER -> TILE PREPARATION -> TILE (no plaster
  under tile); external Sigma SPATTER -> ROUGH -> SMOOTH -> SIGMA; stone SPATTER -> CLADDING. OD-V3-4 (method register
  URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1) makes it a separate line. So **B4-05 is the whole finished wall-face population
  once, whatever the substrate**, not a concrete-only subset. The row's framing ("every exposed concrete face that
  receives plaster") is the substrate split of that population; it is reported beside it (s.4), never as the item.
- **Joint mesh (شبك)** is a strip over a block-to-concrete joint inside a finished face (block end at a column, block
  top under a beam / slab soffit, block beside a deeper member's step). **Nothing answers its scope**: no owner rule
  (OWNER_QUESTIONS_ANSWERED, OWNER_RULE_* / OWNER_NOTES_*, rules/owner_library 1.4.0, URBAN_RULES 1.7.0, method
  register: no entry), no drawing note (text census of P7757 675 texts and ST7757 2,339 texts: no mesh / spatter /
  plaster / render note; the ST notes in a legacy Arabic font are concrete notes), no finishes specification issued
  (PROJECT_UNDERSTANDING_ASSESSMENT item 3), and no freelancer line. The joint population is measured in m.l; **the item
  stays HELD by name (blank, never 0)**. A mesh width is a product property and is never part of the quantity.

## 2. B4-05 spatter dash: one record per host finish line (SPATTER_T317.csv, 60 hosts; candidate line: NO LINE)

| Host family (source) | Determinate m2 | State | HELD range m2 | HELD blank hosts |
|---|---|---|---|---|
| Internal plaster, V3.0.20 FIN.PLASTER (T-244 MERGED 59dbfd0e on the T-292 extract; totals asserted) | 234.9481 (24 lines incl. door-through-wall reveals) | ASSUMED — OWNER-APPROVED (G1 heights Q-43 / Q-48 A) | 489.4811 .. 545.4607 (9 lines) | 4: annex GF-R7512EA / GF-R51E127 (G2), ST-2F shaft (T-173), pantry GF-RC06FED |
| Wall tile, T-312 ledger (MERGED 8943b5ed) | 307.9616 (11 rooms) | ASSUMED — OWNER-APPROVED | - | 6: annex GF-02 / 03 / 05 / 06, GF-10, GF-11 (no level) |
| Exterior Sigma, T-305 lines (MERGED 9d71ef09; openings at full, OD-V3B-3) | 1F 234.5255 DRAWING-CONFIRMED; 2F 132.2050 ASSUMED (doors 2.20) | | GF 387.2852 .. 420.7702 (openings without a hole) | - |
| Exterior faces with NO finish line (T-305) | lower-roof face 4.0800 DRAWING-CONFIRMED | | parapet outer faces 68.2978 .. 73.6758; plinth 71.6886 .. 72.7498 (finish not printed: spatter applies under Sigma or stone alike) | - |
| **Villa** | **913.7202** | | **1,016.7526 .. 1,112.6565** | **10** |

One face once (CARRIED_T317.csv, 18 rows): the 17 blank wet-room plaster lines host nothing (OD-V3B-4: no plaster under
tile; the face is the tile line's), and the pantry backsplash 32.3422 m2 (T-312 NO LINE) lies inside the pantry's own
plaster faces (blank line), so it is not a second host. Ceilings: every Alsenan room takes a 0.15 m decor (gypsum)
ceiling (Q-48 A), so the slab soffit above it is not finished; the exposed soffits (stair soffit over the flights
10.725 m2 T-283, pool ceiling 12.834 m2 in exterior Sigma per the owner note) are NOT in OD-V3B-4 .. 7 (walls only):
listed, HELD by name, not added.

**Against the freelancer** (workbook 'المساح الداخلى والسجما', invoice rows 18 / 19): spatter 433.83 m2 'wet rooms and
kitchens' (= his wall-tile total, sheet سيراميك H72) + 70.7125 m2 'under skirting' (282.85 m of skirting x 0.25 m:
typed, = 282.85 / 4) = 504.5425 m2, interior only; no dry-wall, exterior or joint-mesh spatter line (carried in his
plaster / Sigma rates). Reconciliation in units:
- Tiled faces like for like (the 11 rooms both price): engine 307.9616 vs his 295.44 m2, **+12.5216 m2 (+4.24 %)** =
  height +43.1933 (owner G1 3.65 / 3.35 vs his room heights) - doors 23.10 - windows 4.92 - length 2.652, residual
  0.0002 (T-312's merged reconciliation, the same faces). Proposal: RULE_DIFFERENCE (height basis), not an engine error.
- Under-skirting band 70.7125 m2: **RULE_DIFFERENCE, not additive.** Under OD-V3B-5 the dry spatter covers the whole
  plaster face from the finished floor, skirting zone included (the owner method deducts no skirting band), so his band
  is inside the engine's dry population; his 0.25 m band height is printed nowhere and is no owner rule: never used.
- Dry interior and exterior spatter: no freelancer line; RULE_DIFFERENCE (rate-included pricing vs OD-V3-4 separate
  item). A single villa total is NOT COMPARED (different scope: 913.72 determinate + held vs his 504.54 interior only).

## 3. B9-03 joint mesh: the joint population (JOINTS_T317.csv, 1,440 rows; scope HELD, no quantity)

Pieces: every census run of every register v4 wall, cut exactly at the column outlines, beam bands and slab faces
(T-274), block top = storey (GF 4.50 / 1F 4.20 / 2F 4.20) - member depth or slab thickness; T-261 r3 walls take their own
piece heights; sunken-panel pieces 4.34 - d (D-41) HELD; annex (Q-54 B) and lift-tie-beam (ST p.8 n.19) walls HELD.
Bands (R-T317-5): OWNER = finished floor (+0.10) to +0.10 + 3.65 (GF) / 3.35 (1F, 2F), i.e. 3.75 / 3.45 above the
structural floor; DRAWING-DERIVED = finished floor to the soffit over each piece; EXTERIOR = the whole storey (Sigma).
Metres per finished side (an internal wall has two):

| m.l | H: block top under member | V: block at column | STEP: member level changes | HELD (H m / V+STEP count) |
|---|---|---|---|---|
| Interior, OWNER band | INSIDE 2.70 (2F-W07 at 3.00); AT BAND EDGE 76.8638; ABOVE 206.8651 | 278.85 (GF 91.25 / 1F 140.70 / 2F 46.90) | 0 inside (all above the band) | 134.3311 m / 76 V |
| Interior, DRAWING-DERIVED | INSIDE 215.1720 (under beams); AT CEILING CORNER 71.2569 (under slab) | 294.44 | 18.59 | 134.3311 m / 76 V |
| Exterior side (Sigma) | 106.1138 | 121.80 | 2.23 | 50.8577 m / 44 V |

What the owner band shows: the owner's height rule (storey - 0.60 beam - 0.15 decor ceiling - 0.10 floor) puts the band
top at or below almost every block top: on 1F / 2F exactly at the soffit of a 0.75 m beam (4.20 - 0.75 = 3.45), on GF at
3.75 = the soffit of CB-series 0.75 beams. So under the owner method the horizontal joints sit at the plaster stop or
behind the decor ceiling (2.70 m inside on the whole villa); under the drawing-derived method 215.17 m are inside. The
vertical joints at columns are inside under both (clipped at the band top under the owner method).

Bounds named (never silently taken): V joints in a band that also carries an opening are UPPER bounds (an opening jamb
may meet the column and shorten the joint; band and run stations are not aligned in the committed T-274 tables):
interior GF 58.40 / 1F 80.40 / 2F 6.70, exterior GF 32.00 / 1F 41.90 m. H joints are counted over the whole run length: over an opening
the joint exists only where block stands between the lintel and the member (heads against piece tops not checked here:
named); the lintel's own joints are NOT MEASURED (no lintel register). Not covered by the register runs (UNKNOWN by name): GF-W30, GF-W37,
GF-H01, GF-H02, 1F-W25, 1F-W00/W01 BAY-ENDS, GF P-GF-05 ABOVE-LINTEL; concrete walls (lift / retaining / pool),
free-standing columns and column returns are not block-to-concrete joints of a register wall.

## 4. Concrete share of the finished faces (substrate split, FACES_T317.csv)

Established wall sides of the register runs, owner band (interior) and whole storey (exterior), face = block +
concrete asserted per side (residual 0): interior GF 220.7849 = concrete 23.3600 + block 197.4249 (10.6 %), 1F 427.3694
= 39.6975 + 387.6719 (9.3 %), 2F 79.7300 = 9.3800 + 70.3500 (11.8 %); exterior GF 96.3000 = 29.1524 + 67.1476 (30.3 %),
1F 134.4484 = 38.7532 + 95.6952 (28.8 %), 2F all held (T-261 walls). Sides HELD: interior 58, exterior 18. This split is
information for the plaster / Sigma lines (the concrete faces are the plaster's), not a second spatter quantity. It
covers in-plane faces of register block walls only; column returns, free columns, RC walls and beam soffits across
rooms are not in it (named, not measured here).

## 5. Rules, code, tests

- **R-T317-1 .. 5** (every villa; research/agents_t317/t317_spatter_mesh.py docstring): scope before numbers; spatter =
  the host finish population once; one concrete face per (column, wall plane, face); joints classified against the
  finished band (INSIDE / AT_BAND_EDGE / ABOVE / HELD), V joints clipped to the band and HELD at an opening jamb, STEP
  joints where the member level changes; owner and drawing-derived bands side by side. Provenance: OD-V3B-4 .. 7,
  OD-V3-4, Q-43 / Q-48 A, T-274 / T-288 / T-261 / T-305 / T-312 / T-244.
- Code: t317_spatter_mesh.py (generic), t317_alsenan.py (`--write`, `--check` reproduces every output byte for byte).
- Tests (29): tests/t317_spatter_mesh/test_t317_spatter_mesh.py, NON-Alsenan hand fixture (4 x 5 m room, four 0.30 x
  0.30 columns, 0.20 x 0.60 beams under a 0.15 slab, storey 3.50, one full-height tiled face): drawing-derived 58.500 m2 =
  concrete 14.820 + block 43.680, joints H 15.600 / V 22.400 m; owner band 47.700 = 6.360 + 41.340, H all above, V
  21.200; adverse: column face from two rooms refused, joint on an unplastered side refused, default mesh width refused,
  held carried as 0 refused, face in two hosts refused, HELD host with a figure refused, mm read as m refused, mirror and
  mm identical, opening at a column holds the joint, unknown block top held, band edge not inside, step joints.
  test_t317_alsenan_pins.py: every figure of s.2 - s.3 re-derived from the merged inputs.

## 6. For the Checker (re-measure)

1. OD-V3B-4 .. 7 wording and date in alsenan_v3b_owner_decisions.json; whether any later answer narrows spatter to
   concrete faces (none found: grep 'spatter|طرطش|mesh|شبك' over OWNER_QUESTIONS*, OWNER_RULE_*, OWNER_NOTES_*).
2. Host totals: FIN.PLASTER V3.0.20 234.9481 / 489.4810 .. 545.4606 (T-244 s.4), tile 307.9616 (T-312), exterior
   234.5255 / 132.2050 / 387.2852 .. 420.7702 (T-305); 17 wet plaster lines carried by tile.
3. Freelancer: invoice rows 18 / 19 (433.83, 70.7125), sheet البيان A45 282.85 (skirting run).
4. Two joint pins: 2F-W07 (T-261 piece 2.70 m at 3.00 inside the owner band), 1F band edge 3.45 = 4.20 - 0.75.

Proposed lessons row (ERS s.7): *Problem*: a finish preparation coat was framed as a concrete-face item. *Root cause*:
the substrate (concrete) was taken for the scope; the owner's method puts spatter on every finished face. *Rule*: scope
of a preparation item comes from the method record; the substrate split is information beside it; a joint item is
measured only where a finished coat covers both sides of the joint, against the same band the finish uses (every
villa). *Test*: tests/t317_spatter_mesh. *Status*: PROPOSED.
