# T-767 fix rows: waterproofing lines without a figure on V3.0.78

Lines without a point figure (WP families; 3 roof lines left to T-764 and 1 to MAIN_FILL): 50 -> 0; rows 50.

- wet floor 85.58 = 72.12 (T-010 rooms, vs freelancer 72.01: +0.11 m2, +0.15 %) + pantry wet zone GF-RC99C2A 13.455 m2 (owner Q-30 kitchens / pantry like a bathroom; the freelancer has none): RULE_DIFFERENCE +13.57 m2 (+18.8 %), not a measurement error
- GF-RC99C2A (pantry) has 1 floor drain (T-743) and no FIN.WP.PENETRATION line: a MISSING line of 1 pcs MEASURED for the wiring package (T-750 adds it); not counted in the 55 pcs
- BOUNDARY_GB_AND_STRAPS: 138.38 of its 154.94 m2 is the boundary band, whose p.14 detail prints no coating: RULE_DIFFERENCE, kept as ESTIMATE with its components so the owner can strike it
- FIN.WP.PENETRATION supersedes the T-750 ranges 19 .. 31 pcs (floor outlets only) by the owner default of 2026-11-13: one per fixture (WC, basin, shower, floor drain)

Wet-room membrane floor (released, unchanged): 85.58 m2 vs freelancer 72.01 m2.

| item | lines | after |
|---|---|---|
| FIN.WP.DOORWAY_TRANSITION [m2] | 14 | 2.2994 |
| FIN.WP.PENETRATION [pcs] | 17 | 55.0 |
| FIN.WP.ROOF [m2] | 1 | 0.64 |
| FIN.WP.ROOF_UPTURN [lm] | 2 | 4.028 |
| FIN.WP.TERMINATION [lm] | 4 | 3.1604 |
| FIN.WP.WALL_UPTURN [m2] | 1 | 1.9 |
| WP.FOUNDATION.BURIED_LIQUID [m2] | 4 | 462.72 |
| WP.FOUNDATION.FOOTING_MEMBRANE [m2] | 1 | 4.55 |
| WP.FOUNDATION.FOOTING_SCREED [m2] | 1 | 4.55 |
| WP.FOUNDATION.FOOTING_SCREED [m3] | 1 | 0.2275 |
| WP.FOUNDATION.FOOTING_SIDES [m2] | 1 | 86.88 |
| WP.FOUNDATION.LIFT_PIT_BOARD [m2] | 1 | 8.84 |
| WP.FOUNDATION.LIFT_PIT_MEMBRANE [m2] | 1 | 8.84 |
| WP.FOUNDATION.PROCUREMENT [item] | 1 | 1.0 |

| line | item | unit | element | before | after | label | basis |
|---|---|---|---|---|---|---|---|
| L-689197a4778b786de143 | FIN.WP.DOORWAY_TRANSITION | m2 | 1F-R26FA0D:doorway transition OP-008 | HELD 0.0 .. 0.18 | 0.18 | ESTIMATE | door width 0.90 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.18 m2; low 0 dropped |
| L-bec3b3df8ec830a46447 | FIN.WP.DOORWAY_TRANSITION | m2 | 1F-R26FA0D:doorway transition OP-010 | BLANK | 0.16 | DRAWING-READ | door width 0.80 (T-074 hand table of every wet door, Q-35 addendum; same width as the released FIN.WP.DOORWAY 0.12 m2 = 0.80 x wall 0.15) x 0.20 upturn = 0.16 m2 |
| L-aed6f48195f99648c3f3 | FIN.WP.DOORWAY_TRANSITION | m2 | 1F-R48AA46:doorway transition OP-004 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-dfc4e74604047cb21407 | FIN.WP.DOORWAY_TRANSITION | m2 | 1F-R48CDA5:doorway transition OP-018 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-07b084a5187a64634108 | FIN.WP.DOORWAY_TRANSITION | m2 | 1F-R8BDA49:doorway transition CLOSURE|D2:3118|D2:417@D2:3118:0 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-19f6405a5e60a99c29f7 | FIN.WP.DOORWAY_TRANSITION | m2 | 1F-RED23B8:doorway transition OP-019 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-b5a04e7c058346b6f734 | FIN.WP.DOORWAY_TRANSITION | m2 | 2F-RE83BED:doorway transition OP-006 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-b46013c737051e5441fe | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RA3AD49:doorway transition OP-025 | HELD 0.0 .. 0.2 | 0.2 | ESTIMATE | door width 1.00 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.2 m2; low 0 dropped |
| L-65194e5d4497f0882024 | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RB28769:doorway transition OP-018 | BLANK | 0.16 | DRAWING-READ | door width 0.80 (T-074 hand table of every wet door, Q-35 addendum; same width as the released FIN.WP.DOORWAY 0.12 m2 = 0.80 x wall 0.15) x 0.20 upturn = 0.16 m2 |
| L-1c36054a8cadc0726e65 | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RB62B55:doorway transition CLOSURE|D2:495|D2:417@D2:495:0 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-77a630d7e60ca6c404ba | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RD36087:doorway transition CLOSURE|D2:825|D2:417@D2:825:0 | HELD 0.0 .. 0.159408 | 0.1594 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.159408 m2; low 0 dropped |
| L-20400ca6dc38abb30c33 | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RD6F891:doorway transition CLOSURE|D2:820:0|D2:820:0 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-19908ce0b9a2bcadff80 | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RF38DAF:doorway transition OP-017 | BLANK | 0.16 | DRAWING-READ | door width 0.80 (T-074 hand table of every wet door, Q-35 addendum; same width as the released FIN.WP.DOORWAY 0.12 m2 = 0.80 x wall 0.15) x 0.20 upturn = 0.16 m2 |
| L-b4a23dc5fc953bc5a163 | FIN.WP.DOORWAY_TRANSITION | m2 | GF-RFAD3C4:doorway transition OP-026 | HELD 0.0 .. 0.16 | 0.16 | ESTIMATE | door width 0.80 x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition per door) = the engine high bound 0.16 m2; low 0 dropped |
| L-9971bd68a5150abebe0a | FIN.WP.PENETRATION | pcs | 1F-R26FA0D:wp_penetrations | BLANK | 2.0 | DEFAULT | 1F-R26FA0D: floor_drain 1 MEASURED (T-743 sanitary sheet) + 1 washing_machine_point point not drawn: owner default one WP penetration per fixture = 2 pcs |
| L-3e6dbcb5614746978a87 | FIN.WP.PENETRATION | pcs | 1F-R48AA46:wp_penetrations | BLANK | 4.0 | MEASURED | 1F-R48AA46: basin 1 + floor_drain 1 + shower_walkin 1 + wc 1 = 4 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-a5f885a2f86ee05d5b8b | FIN.WP.PENETRATION | pcs | 1F-R48CDA5:wp_penetrations | BLANK | 4.0 | MEASURED | 1F-R48CDA5: basin 1 + floor_drain 1 + shower_tray 1 + wc 1 = 4 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-fb8f6c4b9b3044505557 | FIN.WP.PENETRATION | pcs | 1F-R52AC05:wp_penetrations | BLANK | 3.0 | MEASURED | 1F-R52AC05: basin 1 + floor_drain 1 + wc 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-2253a7ed9e80ac00c728 | FIN.WP.PENETRATION | pcs | 1F-R8BDA49:wp_penetrations | BLANK | 5.0 | MEASURED | 1F-R8BDA49: basin 1 + floor_drain 2 + shower_walkin 1 + wc 1 = 5 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-2af93ddb70a431b92800 | FIN.WP.PENETRATION | pcs | 1F-RED23B8:wp_penetrations | BLANK | 4.0 | MEASURED | 1F-RED23B8: basin 1 + floor_drain 1 + shower_tray 1 + wc 1 = 4 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-faa7232880f13c1e4a99 | FIN.WP.PENETRATION | pcs | 2F-RE83BED:wp_penetrations | BLANK | 4.0 | MEASURED | 2F-RE83BED: basin 1 + floor_drain 1 + shower_walkin 1 + wc 1 = 4 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-6375385673176b8b2c9c | FIN.WP.PENETRATION | pcs | GF-R8496F0:wp_penetrations | BLANK | 3.0 | MEASURED | GF-R8496F0: basin 2 + floor_drain 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-229e7bf9e837e1d838bd | FIN.WP.PENETRATION | pcs | GF-RA3AD49:wp_penetrations | BLANK | 2.0 | DEFAULT | GF-RA3AD49: floor_drain 1 MEASURED (T-743 sanitary sheet) + 1 kitchen_sink point not drawn: owner default one WP penetration per fixture = 2 pcs |
| L-bcda623f9ad89eba41db | FIN.WP.PENETRATION | pcs | GF-RB28769:wp_penetrations | BLANK | 3.0 | MEASURED | GF-RB28769: basin 1 + floor_drain 1 + wc 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-f650522e7882dddccdfa | FIN.WP.PENETRATION | pcs | GF-RB62B55:wp_penetrations | BLANK | 3.0 | MEASURED | GF-RB62B55: basin 1 + floor_drain 1 + wc 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-a4bbc2efdb8425554344 | FIN.WP.PENETRATION | pcs | GF-RD36087:wp_penetrations | BLANK | 2.0 | MEASURED | GF-RD36087: basin 1 + floor_drain 1 = 2 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-20dfb3cd1232128b3cb6 | FIN.WP.PENETRATION | pcs | GF-RD6F891:wp_penetrations | BLANK | 4.0 | MEASURED | GF-RD6F891: basin 1 + floor_drain 1 + shower_tray 1 + wc 1 = 4 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-0db07ac89503dd3f5980 | FIN.WP.PENETRATION | pcs | GF-RDBD4F9:wp_penetrations | BLANK | 3.0 | MEASURED | GF-RDBD4F9: basin 2 + floor_drain 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-657bff4f4cc8e417bc6c | FIN.WP.PENETRATION | pcs | GF-RDF7D28:wp_penetrations | BLANK | 3.0 | MEASURED | GF-RDF7D28: basin 1 + floor_drain 1 + wc 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-5f41701522d675c37b10 | FIN.WP.PENETRATION | pcs | GF-RF38DAF:wp_penetrations | BLANK | 3.0 | MEASURED | GF-RF38DAF: basin 1 + floor_drain 1 + wc 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-345e907e572a363fb615 | FIN.WP.PENETRATION | pcs | GF-RFAD3C4:wp_penetrations | BLANK | 3.0 | MEASURED | GF-RFAD3C4: basin 1 + floor_drain 1 + wc 1 = 3 pcs (T-743 sanitary census, owner default one WP penetration per fixture) |
| L-2361d6ec13c952bd2ae3 | FIN.WP.ROOF | m2 | 1F-POOLCOURT-550-LEDGE:wp_membrane | HELD 0.0 .. 0.639573 | 0.64 | ESTIMATE | 1F pool-court +5.50 ledge drawn: the engine high bound 0.639573 m2 (drawn ledge / window-face run; low 0 = 'not membraned', dropped); below 1 % of the roof WP lines |
| L-d7d1bf8c5991ccf69ea2 | FIN.WP.ROOF_UPTURN | lm | 1F-POOLCOURT-550-LEDGE:wp_upturn | HELD 0.0 .. 3.528277 | 3.528 | ESTIMATE | 1F pool-court +5.50 ledge drawn: the engine high bound 3.52828 lm (drawn ledge / window-face run; low 0 = 'not membraned', dropped); below 1 % of the roof WP lines |
| L-1954878bb02c91139e1b | FIN.WP.ROOF_UPTURN | lm | 1F-POOLCOURT-550:wp_upturn window_face | HELD 0.0 .. 0.500002 | 0.5 | ESTIMATE | 1F pool-court +5.50 ledge drawn: the engine high bound 0.500002 lm (drawn ledge / window-face run; low 0 = 'not membraned', dropped); below 1 % of the roof WP lines |
| L-9592048116294937ab6f | FIN.WP.TERMINATION | lm | GF-R8496F0:termination passage OP-027 | HELD 0.0 .. 1.0 | 1.0 | ESTIMATE | membrane ends along the open edge / opening it names: run = the engine high bound 1 lm (the drawn width); low 0 = 'not terminated', dropped |
| L-f78da96a7d31f7b72068 | FIN.WP.TERMINATION | lm | GF-RB28769:termination other | HELD 0.0 .. 0.004711 | 0.0047 | ESTIMATE | membrane ends along the open edge / opening it names: run = the engine high bound 0.004711 lm (the drawn width); low 0 = 'not terminated', dropped; below 1 % of its family (materiality), logged |
| L-c57860d79f54a4c1c4b3 | FIN.WP.TERMINATION | lm | GF-RD36087:termination passage OP-020 | HELD 0.0 .. 0.9 | 0.9 | ESTIMATE | membrane ends along the open edge / opening it names: run = the engine high bound 0.9 lm (the drawn width); low 0 = 'not terminated', dropped |
| L-a4df8fc50fbab4bef48f | FIN.WP.TERMINATION | lm | GF-RDBD4F9:termination zone_line ZONE|D2:731:0|0 | HELD 0.0 .. 1.255652 | 1.2557 | ESTIMATE | membrane ends along the open edge / opening it names: run = the engine high bound 1.25565 lm (the drawn width); low 0 = 'not terminated', dropped |
| L-8090ff20f2b547d1bc96 | FIN.WP.WALL_UPTURN | m2 | GF-RC99C2A:wp_wall_upturn:wet_zone | BLANK | 1.9 | DEFAULT | pantry box 4.50 x 3.00: perimeter 15.00 - open side 4.50 - door 1.00 = 9.50 m wall run (T-750 hand table: 7.00 + window gaps 1.00 + 1.50) x 0.20 = 1.90 m2; the upturn runs under both windows because the default sill (0.90 dry / 1.60 wet) is above 0.20 |
| L-4f4e4c930e33ed6dafa3 | WP.FOUNDATION.BURIED_LIQUID | m2 | WPF:BOUNDARY_GB_AND_STRAPS | BLANK | 154.94 | ESTIMATE | straps 2 sides + top 16.56 (SB1 4.55 x (2x0.5+0.7) = 7.74; SB2 2.29 x (2x0.5+1.0) = 4.59; SB3 3.26 x (2x0.4+0.5) = 4.24) + boundary band 44.07 m (T-263) x 2 faces x buried 1.57 (formation 1.67 as T-764 - blinding 0.10) 138.38 = 154.94 m2; p.14 prints no coating on the boundary detail: RULE_DIFFERENCE, line may be struck by the owner |
| L-eba4599c26b0d24de873 | WP.FOUNDATION.BURIED_LIQUID | m2 | WPF:BURIED_GROUND_BEAM_FACES_HELD | BLANK | 96.92 | ESTIMATE | 118 held ground-beam faces (T-276): 74 at the candidate range midpoint, 44 traced length x (default beam depth 0.60 - slab 0.10) = 96.92 m2 |
| L-12aca7f853626262bd07 | WP.FOUNDATION.BURIED_LIQUID | m2 | WPF:FOOTING_TOPS_OUTSIDE_NECKS | BLANK | 108.92 | ESTIMATE | 25 footings: outline area - neck sections (T-263 per footing; 1B1B 4.55 - C10 0.21 - C 0.15; 1B1A midpoint) = 108.92 m2 |
| L-84a874dedb35cbe2bafb | WP.FOUNDATION.BURIED_LIQUID | m2 | WPF:NECK_FACES | BLANK | 101.94 | ESTIMATE | 32 necks: perimeter (T-263, sum 53.40 m) x neck height of the same mark = neck concrete range midpoint / schedule section (mean 1.85 m, 0 without a range at that mean) = 101.94 m2 |
| L-f7da4df288b4e006c0e7 | WP.FOUNDATION.FOOTING_MEMBRANE | m2 | WPF:FOOTING_UNDERLAY_MEMBRANE_1B1B | BLANK | 4.55 | ESTIMATE | footing 1B1B (F10 + F, Q-31 C): owner 'you can choose the bigger area' = drawn 3.25 x 1.40 = 4.55 m2, PROVISIONAL, flagged; schedule reading 2.80 x 1.40 + 0.90 x 0.80 = 4.64 beside |
| L-46cee803214ff2d964fa | WP.FOUNDATION.FOOTING_SCREED | m2 | WPF:FOOTING_PROTECTION_SCREED_1B1B | BLANK | 4.55 | ESTIMATE | same footing 1B1B: 4.55 m2 under the footing (Q-31 bigger area, PROVISIONAL) |
| L-79bc828150bbfe63ce8e | WP.FOUNDATION.FOOTING_SCREED | m3 | WPF:FOOTING_PROTECTION_SCREED_1B1B | BLANK | 0.2275 | ESTIMATE | 4.55 m2 x printed 5 cm screed (p.13) = 0.2275 m3 |
| L-13b1d3c202bc08fb65c2 | WP.FOUNDATION.FOOTING_SIDES | m2 | WPF:FOOTING_SIDE_FACES | BLANK | 86.88 | ESTIMATE | 25 footings (lift FF excluded: p.14 system): sum of 2 x (L + W) x schedule H, 1B1B drawn 3.25 x 1.40 x F10 H 0.50 = 86.88 m2 (governing p.13 detail not selected, Q-21 C) |
| L-f0aadf70513eb21d5671 | WP.FOUNDATION.LIFT_PIT_BOARD | m2 | WPF:LIFT_PIT_BOARD_WALLS | BLANK | 8.84 | DEFAULT | pit outer walls (ring 2.20 + 2 x default lift wall 0.20) x 4 = 10.40 m x buried height 0.85 (printed min founding 1.50 - blinding 0.10 - base 0.55, to N.G.) = 8.84 m2 (pit depth D-43 not printed) |
| L-302b401eff698289c54e | WP.FOUNDATION.LIFT_PIT_MEMBRANE | m2 | WPF:LIFT_PIT_MEMBRANE_WALLS | BLANK | 8.84 | DEFAULT | pit outer walls (ring 2.20 + 2 x default lift wall 0.20) x 4 = 10.40 m x buried height 0.85 (printed min founding 1.50 - blinding 0.10 - base 0.55, to N.G.) = 8.84 m2 (pit depth D-43 not printed) |
| L-d2488bbb7103c8cd2980 | WP.FOUNDATION.PROCUREMENT | item | WPF:FOUNDATION_WP_PROCUREMENT | BLANK | 1.0 | DEFAULT | 1 item: liquid coating supply for the buried faces of this set (product, coats, coverage not printed, UP-WP-MAT-001); priced on the m2 lines |
