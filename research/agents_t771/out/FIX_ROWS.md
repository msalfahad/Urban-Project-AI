# T-771 missing families: new lines and dispositions (fix-row set, unwired)

Candidate ARCH_TAKEOFF_V3.0.81; 39 families without a line; 23 new lines in 10 families; not covered: none.

| Family | Item | Unit | Figure | Label | Basis |
|---|---|---|---|---|---|
| B1-06 | SITE.EXCAVATION_SUPPORT (SITE:B1-06b) | item | 1.0 | DRAWING-READ | ST p.8 note 15 puts excavation protection / shoring on the contractor (extent by his specialist study); faces at the plot line >= 1.50 deep on all 4 sides (T-358 TRIGGERED); 1 lump-sum item, perimeter 2 x (15.00 + 31.37) = 92.74 lm beside |
| B4-05 | FIN.SPATTER_DASH (SPATTER:INTERIOR) | m2 | 1622.0 | ESTIMATE | = carrier FIN.PLASTER m2 total 1622.00 (V3.0.81 index with the merged T-760 / T-763 / T-769 figures; owner OD-V3B-4..7 coat under every finished face once, wet-room tile backing included; recompute from the carrier at wiring) |
| B4-05 | FIN.SPATTER_DASH (SPATTER:EXTERIOR) | m2 | 1054.0 | ESTIMATE | = carrier FIN.EXT.FINISH m2 total 1054.00 (V3.0.81 index with the merged T-760 / T-763 / T-769 figures; owner OD-V3B-4..7 coat under every finished face once; recompute from the carrier at wiring) |
| B4-05 | FIN.SPATTER_DASH (SPATTER:FENCE) | m2 | 179.84 | ESTIMATE | = carrier EXT.FENCE.PLASTER m2 total 179.84 (V3.0.81 index with the merged T-760 / T-763 / T-769 figures; owner OD-V3B-4..7 coat under every finished face once; recompute from the carrier at wiring) |
| B4-10 | FIN.WALL.TILE.EDGE (TILE_EDGE:CORNERS_AND_ENDS) | lm | 32.01 | ESTIMATE | T-368 determinate 31.65 lm at the 3.65 tile top x 3.00 / 3.65 (owner tile top 3.00, 13 Nov) = 26.01 + GF-14 wall end and flat stop 2 x 3.00 (no header on the slab plan) = 32.01; finish 45-degree OR steel profile (never both), designer list |
| B4-10 | FIN.WALL.TILE.EDGE (TILE_EDGE:DOOR_JAMBS) | lm | 0.0 .. 73.1 | ESTIMATE | door-jamb tile edges: T-368 range 0 .. 73.1 lm (0 when the door frame covers the edge); frame / architrave detail not printed |
| B5-02 | FIN.CEILING.GYPSUM (CEILING:GYPSUM_DECOR) | m2 | 411.34 | ESTIMATE | = FIN.CEILING m2 of the candidate 411.34 (4 lines still blank: T-768 fills them; recompute at wiring); owner Q-57 A mod + Q-48 A: gypsum decor ceiling in every room, moisture-resistant board type HELD (not specified); FIN.CEILING stays the physical area (B5-01): wire as the board item, not added to it |
| B5-03 | FIN.CEILING.CORNICE (CEILING:CORNICE) | lm | 302.88 | ESTIMATE | T-147 closed-room wall perimeter at the decor ceiling 302.88 lm; no cornice / cove detail printed (Q-57 A mod: cove only with geometry or a detail, not carried); open zones without a wall edge not counted |
| B7-05 | FIN.STAIR.NOSING (STAIR:NOSING) | lm | 97.09 | ESTIMATE | one nosing per step edge = T-766 FIN.STAIR.STEP_LM 89.69 (READY; recompute when merged) + landing / floor arrival edges 7.4 (T-412 DRAWING-CONFIRMED) = 97.09; nosing form not printed (designer list) |
| B7-11 | MET.RAILING.POST (RAILING:POSTS) | pcs | 10.0 | DRAWING-READ | posts drawn on the roof X railings: RL-02 (NW) 6, RL-01 (SE) 4 = 10 (T-361); glass panels drawn nowhere and not specified: no glass line |
| B9-03 | MAS.MESH_STRIP (MASONRY:MESH_STRIP) | lm | 856.14 .. 1147.96 | ESTIMATE OPTIONAL | strip on every 3rd course of every block wall (Q-77): T-355 black restated by T-362 + white family A (62.5 x 25 face, as T-765): certain 856.14 .. + held levels 291.82; 7 walls of unknown block type not in the range (T-362) |
| B9-03 | MAS.SHARMAT (MASONRY:SHARMAT) | pcs | 293.0 .. 601.42 | ESTIMATE OPTIONAL | one tie per 3rd course at every wall-to-column junction (Q-77): 293 pcs at 57 resolved junctions .. + 60 held junctions x 5.14 pcs average |
| B12-01 | MEP.SAN.WC (SANITARY:WC) | pcs | 12.0 | MEASURED | WC (GF 6, 1F 5, 2F 1): 12 pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743) |
| B12-01 | MEP.SAN.BASIN (SANITARY:BASIN) | pcs | 17.0 | MEASURED | wash basin (GF 11, 1F 5, 2F 1; 5 on both sheets): 17 pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743) |
| B12-01 | MEP.SAN.SHOWER_TRAY (SANITARY:SHOWER_TRAY) | pcs | 3.0 | MEASURED | shower tray (GF 1, 1F 2): 3 pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743) |
| B12-01 | MEP.SAN.SHOWER_WALKIN (SANITARY:SHOWER_WALKIN) | pcs | 3.0 | MEASURED | walk-in shower zone, screen + mixer (1F 2, 2F 1): 3 pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743) |
| B12-01 | MEP.SAN.FLOOR_DRAIN_4IN (SANITARY:FLOOR_DRAIN_4IN) | pcs | 14.0 | MEASURED | floor drain 4 in: 14 pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743) |
| B12-01 | MEP.SAN.FLOOR_DRAIN_3IN (SANITARY:FLOOR_DRAIN_3IN) | pcs | 5.0 | MEASURED | floor drain 3 in: 5 pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743) |
| B12-01 | MEP.SAN.KITCHEN_SINK (SANITARY:KITCHEN_SINK) | pcs | 1.0 | ESTIMATE | GF kitchen sink (kitchen FD4 drawn, sink symbol not): 1 per room by function (T-743 HELD the symbol); designer list |
| B12-01 | MEP.SAN.WASHING_MACHINE_POINT (SANITARY:WASHING_MACHINE_POINT) | pcs | 1.0 | ESTIMATE | 1F laundry washing-machine point (FD4 drawn): 1 per room by function (T-743 HELD the symbol); designer list |
| B13-06 | JOIN.WARDROBE (JOINERY:WARDROBE) | lm | 3.9 | DEFAULT | GF lobby box 0.50 x 2.10 (T-223) 2.100 + 1F dressing box 0.50 x 1.80 (T-223 / T-240) 1.800 = 3.900 lm; height 2.40 company default (owner 13 Nov); no interior drawing; boxes drawn on layer 5, no wall line (T-223 joinery rule) |
| B13-06 | JOIN.KITCHEN.BASE (JOINERY:BASE) | lm | 11.07 | DEFAULT | GF kitchen L counter north 2.650 + west 2.500 (T-351) 5.150 + GF pantry wall-backed legs 3.066 + 1.450 + 1.400 (T-351) 5.916 = 11.066 lm; height 0.85 company default (owner 13 Nov); no interior drawing; counter outlines drawn; pantry peninsula on the open edge not counted |
| B13-06 | JOIN.KITCHEN.WALL (JOINERY:WALL) | lm | 8.42 | ESTIMATE | GF kitchen west leg (north leg under W08) (T-351) 2.500 + GF pantry wall-backed legs (T-351) 5.916 = 8.416 lm; height 0.70 company default (owner 13 Nov); no interior drawing; wall units not drawn: on the wall-backed legs, none under a window |

| Family | Disposition | Evidence | Figure beside |
|---|---|---|---|
| B1-01 | COVERED_BY_ROW | T-769 new_lines (MERGED f8319feb), wired by a T-770 round |  |
| B1-05 | COVERED_BY_ROW | T-769 new_lines (MERGED f8319feb), wired by a T-770 round |  |
| B1-07 | COVERED_BY_ROW | T-769 new_lines (MERGED f8319feb), wired by a T-770 round |  |
| B1-06 | COVERED_BY_ROW | B1-06a dewatering NOT_APPLICABLE by T-769 (water -4.50 vs formation -1.67); B1-06b support = the new line above; B1-06c none printed (T-358) |  |
| B2-01 | REGISTER_NO_LINE | a room register, not a quantity: every line carries its room id (arch_measure.room_id); master 1.45.0 N/A |  |
| B2-03 | REGISTER_NO_LINE | Lead decision F-T730-5 (master 1.76.0): coverage denominator only, no candidate line | gross floor plate MEASURED T-720: GF 278.27, 1F 209.84, 2F 55.08 = 543.19 m2 |
| B2-04 | REGISTER_NO_LINE | a functional zone; its floor, wall tile and WP are on B3-02 / B4-01 / B8 lines (T-351) | open pantry 4.50 x 3.00 = 13.50 m2 (T-120) |
| B2-05 | REGISTER_NO_LINE | a void is a deduction, not a payable item: the GF light well is out of the GF ceiling (T-147), stair shafts on B7 lines | GF light well 23.24 m2 (ST p.4 face; 1F plan VOID 4.00 x 5.87 = 23.48) |
| B3-03 | NOT_APPLICABLE_WITH_EVIDENCE | no marble floor drawn or noted (T-091, 12 arch pages + DXF); GF entrance / hall floor is B3-01 (T-418); the freelancer 'entrance marble' rows are the E1 external stair (B7-02 / B7-04, T-471) |  |
| B3-07 | NOT_APPLICABLE_WITH_EVIDENCE | hidden skirting profile printed nowhere (T-409); doorway boundaries carry the marble threshold lines (B3-04); no profile / transition strip printed |  |
| B4-02 | COVERED_BY_LINE | kitchen / laundry / pantry faces are full-height wet-room tile on FIN.WALL.TILE (B4-01) by owner rule (UP-WET-001, Q-37 A / Q-40 A / Q-48 A); 0 own faces (T-351) |  |
| B4-04 | COVERED_BY_LINE | external render is FIN.EXT.FINISH (18 lines, T-760 figures), mapped to B4-07 in master 1.81.0: PROPOSAL for the next master: move FIN.EXT.FINISH to B4-04 (render), keep paint / edges in B4-07; no line moves |  |
| B4-11 | NOT_APPLICABLE_WITH_EVIDENCE | no material legend, 0 of 675 DXF texts name a cladding; render + paint on every face (T-360 MERGED 5bde82a7); porch arch surround on the designer list |  |
| B5-05 | NOT_APPLICABLE_WITH_EVIDENCE | no access panel drawn or noted; MEP drawings absent: revisit with B12 at the MEP stage |  |
| B6-08 | COVERED_BY_ROW | T-768 (worker 2, TODO) fills DOOR.LIFT_LANDING: 3 landings GF / 1F / 2F (T-619), 1.00 x 2.10 default; the lines are absent from V3.0.81, so T-768 adds them | 3 pcs |
| B7-10 | NOT_APPLICABLE_WITH_EVIDENCE | no wall handrail drawn (one FIN.HANDRAIL EXCLUDED_WITH_REASON line, T-199 / UP-STAIR-013) |  |
| B7-14 | PARKED | rebar parked by the owner 2026-11-11: approximate tons by ratio at the end |  |
| B11-02 | PARKED | rebar parked by the owner 2026-11-11: approximate tons by ratio at the end |  |
| B11-03 | PARKED | rebar parked by the owner 2026-11-11: approximate tons by ratio at the end |  |
| B11-04 | PARKED | rebar parked by the owner 2026-11-11: approximate tons by ratio at the end |  |
| B8-04 | COVERED_BY_LINE | showers sit inside the wet-room membrane FIN.WP.FLOOR + upturn (B8-01 / B8-03), no separate tanking (Q-40 A, T-369); 6 showers (T-743) |  |
| B8-07 | NOT_APPLICABLE_WITH_EVIDENCE | no balcony / terrace label, no slab projecting with a door onto it; the 2F roof terrace and the pool-court slab are on FIN.WP.ROOF (B8-06) (T-486 MERGED) |  |
| B9-05 | NOT_APPLICABLE_WITH_EVIDENCE | parapets carried all-RC on STR.CONC.PARAPET (T-761 MERGED: sections A-A / B-B cut every parapet in RC); ST p.14 typical block-on-upstand alternative noted in T-761's basis |  |
| B12-02 | HELD_MEP_STAGE | drainage / supply runs: the sanitary sheets are not to scale (plotted 1:108 vs printed 1:100, T-743); runs at the MEP stage (owner default 'drainage runs at MEP') |  |
| B12-03 | HELD_MEP_STAGE | no electrical drawing in the Drive set; MEP stage |  |
| B12-04 | HELD_MEP_STAGE | no HVAC drawing in the Drive set; MEP stage |  |
| B12-05 | HELD_MEP_STAGE | no low-voltage drawing in the Drive set; MEP stage |  |
| B13-03 | NOT_APPLICABLE_WITH_EVIDENCE | garden labels only, no landscape / irrigation plan (T-427); out of the owner scope freeze |  |
| B13-05 | NOT_APPLICABLE_WITH_EVIDENCE | no movement joint or sealant printed on ST p.1-16, ARCH p.1-12, SAN p.1-3 (T-365); owner Q-42 gives a width only; out of the owner scope freeze |  |
| B13-07 | NOT_APPLICABLE_WITH_EVIDENCE | no canopy or pergola on any sheet (T-199, T-471); railings, gates and shutters are on B7-09 / B13-08 / B13-04 / B6-05 |  |
