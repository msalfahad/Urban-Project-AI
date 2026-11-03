# T-457: wet-wall fixing double count (owner directive 2026-11-02 C2, re-scoped)

Synthetic evidence only; no drawing, no client data. Scope: every villa.

## Physical element

A tiled wet-room wall face (bathroom, kitchen, pantry, laundry, ironing room) is built up, by the owner's confirmed
practice (UPC-WETWALL-001, 2026-11-02), in three operations on the same m2: (1) spatter dash (طرطشة, plasterer);
(2) levelling render (مساح ناعم, tiler); (3) tile adhesive + porcelain (لاصق + بورسلان, tiler). Adhesive is the only
fixing material. A second mortar fixing bed (tile set in a 1:4 bed AND stuck with adhesive) is a double count. The
render is a substrate layer, not a fixing bed.

## Step 1: reproduction (research/agents_t457/t457_reproduce.py, out/T457_REPRODUCTION.json)

Hand fixture (not any project): 2.40 x 1.80 m bathroom, 0.80 m door, tile to 2.70 m, 0.60 x 0.60 m window:
run 2 x (2.40 + 1.80) - 0.80 = 7.60 m; gross 20.52 m2; net 20.16 m2.

| | cement layers on the wet wall | fixing materials | floor-bed total (with a 20 m2 dry floor) |
|---|---|---|---|
| V1 / V2 | one: 'bed' 0.02 m 1:4 + 5 %: 0.42336 m3, 3.38688 bags, 0.465696 m3 sand (labelled owner Q-45, PROVISIONAL) | adhesive 4.032 bags + the 'bed' by its label | 1.05336 .. 1.26336 m3 (wet-wall layer inside) |
| V3 | spatter dash (area 20.16, mortar HELD), levelling render (area 20.16, mortar HELD or sourced) | adhesive 4.032 bags only | 0.63 .. 0.84 m3 (floor only) |

Finding:
- **No physical second fixing bed exists.** V1 / V2 charge ONE cement layer plus adhesive; the 0.02 m layer is the
  levelling render. The candidate's wet-room FIN.PLASTER backing (R-WET-BACKING-1 / R-T329-1..4) is that same coat,
  "never a second priced item".
- **Candidate path (ARCH_TAKEOFF_V3.0.44 + tools/urban_boq_m9.py, 187-module static closure): ABSENT.** No finish
  materials table is reachable; of the 69 item codes in the closure the only wall-face layers are FIN.WALL.TILE and
  FIN.PLASTER (one line per room and one backing per tile line, both refused otherwise in arch_v3022.py:292); bed codes
  are FIN.FLOOR.BED.DRY / .WET (floors only); no adhesive, render or spatter-dash code. No candidate or released m2,
  m3 or bag moves.
- **What IS wrong in V1 / V2 (the identity of the layer):** it is reported as a tile fixing bed beside the adhesive;
  its 0.02 m / 1:4 / 8 bags / 1.1 m3 are recorded by the company rulebook 1.0.0 as an ENGINE ASSUMPTION, not a company
  rule (UPC-CEMENT-LAYERS-METHOD-001); and it is summed into the floor-bed mortar / cement / sand / bags-to-buy (on the
  fixture +0.42336 m3 = +67 % of the low floor-bed mortar, +3.39 bags). The spatter dash is missing altogether.

## Step 2: FINISH_MATERIALS_TABLE_V3 (engine/source/finish_materials_table_v3.py, UNWIRED_PRODUCER)

One behaviour change, WET_WALL only: bed keys NOT_APPLICABLE (never 0, never HELD); `fixing_material = ADHESIVE`;
`operations` = SPATTER_DASH, LEVELLING_RENDER, ADHESIVE_AND_PORCELAIN on the same net m2. Render / spatter-dash mortar
via company_rulebook_v1.cement_layer: thickness only from a sourced level 1 / 2 / 4 override, else HELD with the method
named and the sensitivity (m3 per mm = area / 1000); cement / sand HELD (no sourced per-m3 figures; the 1:4 bed /
black-block figures are never borrowed). A thickness > 0.10 m (mm or typo) is HELD. A wet-wall element asking for a
fixing bed is refused (SECOND_FIXING_BED). Bed totals = floor beds only; render / spatter dash summed apart. Every
other kind is V2's row, byte-identical (tested). V1 and V2 unchanged.

Tests: tests/t457_wet_wall_fixing (normal: fixture 20.16 m2, 4.032 bags, render 15 mm -> 0.3024 m3; adverse: second
bed refused x4 keys, custom WET_WALL bed in values ignored, render in mm HELD, override without source / level 3
refused, held wall blank in every operation, marble adhesive HELD, dry tiled wall UNKNOWN_KIND HELD, every floor kind
incl. rotated / mirrored / mm polygons = V2, mixed totals, wet-walls-only totals None never 0; reachability guard).

## General rule (proposed lessons row, ERS s.7)

A layer is named by its physical function before it is priced: on a wet wall the cement coat behind adhesive is the
levelling render (substrate), and the adhesive is the only fixing material; a substrate layer is never summed with
the floor tile beds, and its thickness / mix come only from a sourced level, never from an earlier engine practice
value (provenance T-457, UPC-WETWALL-001, UPC-CEMENT-LAYERS-METHOD-001).

## Not done / open

- Wiring V3 into the candidate (lane I / T-453 .. T-455 material rows); until then nothing reads it.
- Adhesive coverage stays V2's 5 m2 per bag for every porcelain size; UPC-ADHESIVE-001 tile-size rates (3 m2 for
  120 x 60 / 160 x 80) are a separate wiring item.
- Forward risk for the spatter-dash integration (T-364) and any render line: the candidate's wet-room FIN.PLASTER
  backing already IS the levelling render (trade: owner says tiler, the line sits in the plaster family). A future
  LEVELLING_RENDER line on the same faces would be the real double count; spatter dash is a distinct operation.
- The run-time census on the drawings (full candidate reproduction) was not run: the absence is shown on the code
  path (static closure + item-code census + refusals), which is where a second bed would have to originate.
