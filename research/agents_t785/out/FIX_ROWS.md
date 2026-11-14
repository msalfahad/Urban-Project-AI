# T-785 wet-room waterproofing vs the freelancer (V3.0.82; fix rows, unwired)

His room list: 17 rows (GF 10 incl. kitchen, 1F 6 incl. laundry, roof floor 1); ours 18 = his 17 + pantry.

FLOOR m2: ours 85.57571 vs his 72.01 = +13.56571 (+18.84 %); residual 0.0. Like for like (17 rooms, pantry out): 72.12071 (+0.15 %).
UPTURN lm: our wall run 135.572925 vs his perimeter 144.61 = -9.037075 (-6.25 %); residual 0.0. On his gross-perimeter basis (17 rooms: run + doorway segments + open edges): 144.728925 (+0.08 %).

| cause | net |
|---|---|
| floor:ENGINE_RIGHT | +0.307294 |
| floor:RULE_DIFFERENCE | +13.235 |
| floor:TOLERANCE | +0.023416 |
| upturn:ENGINE_RIGHT | +0.5183 |
| upturn:RULE_DIFFERENCE | -9.556 |
| upturn:TOLERANCE | +0.000625 |

SUNKEN rooms (R-T785-2, 6): upturn 9.148 -> 13.722 m2, recess 12.983232 m2 new (6 panel parts capped at the beam bound). Wall upturn m2 27.114585 -> 31.688585.

- F-T785-1: the D-41 default recess 0.30 (main chat 13 Nov, used by T-765 drop walls) exceeds the T-710 beam bound d_max 0.24 on panels 275 / 276 / 280 / 287 / 5BF; R-T785-2 caps it there (298: 0.30 < 0.34). T-765 GF-W20 uses 0.30: 0.9308 x 0.06 = 0.056 m2 of blockwork, below materiality; one drop value per panel across trades is a T-770 wiring check
- F-T785-2: the pantry had 5 WP lines absent from the candidate (doorway, transition, transition nr, termination, penetration; T-710 c / T-767 note): added as new lines
- his 72.01 / 144.61 are also his wet-room gypsum ceiling and cornice figures (decor sheet H74 / H75): one room list feeds three trades

| room | title | his row | floor | his floor | run lm | doors lm | open lm | gross lm | his lm | sunken |
|---|---|---|---|---|---|---|---|---|---|---|
| GF-RDBD4F9 | GF lobby wash (2 basins) | 14 | 4.730695 | 4.73 | 6.6432 | 1.6 | 1.256 | 9.4992 | 9.5 | False |
| GF-RD36087 | GF basin space by the stair | 15 | 1.485 | 1.7 | 3.20296 | 0.8 | 0.9 | 4.90296 | 5.3 | False |
| GF-RD6F891 | GF master bath | 16 | 3.717683 | 3.7 | 6.824665 | 0.8 | 0.0 | 7.624665 | 7.6 | False |
| GF-RB28769 | GF core W.C. 245 x 167 (wedge) | 17 | 2.36761 | 2.3 | 6.0051 | 0.8 | 0.0 | 6.8051 | 6.7 | False |
| GF-RF38DAF | GF core W.C. 289 x 167 (wedge) | 18 | 2.675221 | 2.67 | 6.61404 | 0.8 | 0.0 | 7.41404 | 7.4 | False |
| GF-RDF7D28 | GF stair-core W.C. 175 x 135 | 19 | 2.3625 | 2.36 | 5.40296 | 0.8 | 0.0 | 6.20296 | 6.2 | False |
| GF-RA3AD49 | GF kitchen | 20 | 9.630001 | 9.55 | 13.5 | 1.0 | 0.0 | 14.5 | 14.35 | False |
| GF-RFAD3C4 | GF driver W.C. | 21 | 1.95 | 1.95 | 4.8 | 0.8 | 0.0 | 5.6 | 5.58 | False |
| GF-RB62B55 | GF W.C. by the reception room | 22 | 3.375 | 3.37 | 6.7 | 0.8 | 0.0 | 7.5 | 7.5 | False |
| GF-R8496F0 | GF wash by the reception room | 23 | 3.1325 | 3.15 | 5.4 | 0.8 | 1.0 | 7.2 | 7.2 | False |
| 1F-R48CDA5 | 1F east bath 210 x 225 | 27 | 4.725 | 4.72 | 7.9 | 0.8 | 0.0 | 8.7 | 8.7 | True |
| 1F-RED23B8 | 1F bath by the laundry | 28 | 3.5775 | 3.6 | 6.8 | 0.8 | 0.0 | 7.6 | 7.6 | True |
| 1F-R52AC05 | 1F W.C. by the laundry | 29 | 2.646 | 2.59 | 5.74 | 0.8 | 0.0 | 6.54 | 6.48 | True |
| 1F-R48AA46 | 1F west bath A 245 x 205 | 30 | 5.0225 | 5 | 8.2 | 0.8 | 0.0 | 9.0 | 9 | True |
| 1F-R8BDA49 | 1F west bath B 245 x 205 | 31 | 5.0225 | 5 | 8.2 | 0.8 | 0.0 | 9.0 | 8.9 | True |
| 1F-R26FA0D | 1F laundry | 32 | 10.151 | 10 | 15.24 | 1.7 | 0.0 | 16.94 | 16.85 | False |
| 2F-RE83BED | 2F roof-floor W.C. 300 x 185 | 36 | 5.55 | 5.62 | 8.9 | 0.8 | 0.0 | 9.7 | 9.75 | True |
| GF-RC99C2A | GF pantry (wet zone, Q-37 A) | None | 13.455 | None | 9.5 | 1.0 | 4.5 | 15.0 | None | False |

## Changed lines

| line | element | before | after | label | basis |
|---|---|---|---|---|---|
| L-ba15212ec9887e6d4f73 | 1F-R48AA46:wp_wall_upturn | 1.64 | 2.46 | DEFAULT | sunken wet room (T-213 / T-710 panel 280): company default 'recess + 0.30 up' (owner 2026-11-13): wall run 8.20 x 0.30 = 2.460 m2 (was x 0.20); recess on its own line (R-T785-2) |
| L-60f100105399a9bdfb08 | 1F-R48CDA5:wp_wall_upturn | 1.58 | 2.37 | DEFAULT | sunken wet room (T-213 / T-710 panel 298): company default 'recess + 0.30 up' (owner 2026-11-13): wall run 7.90 x 0.30 = 2.370 m2 (was x 0.20); recess on its own line (R-T785-2) |
| L-ace6533512ada47d1352 | 1F-R52AC05:wp_wall_upturn | 1.148 | 1.722 | DEFAULT | sunken wet room (T-213 / T-710 panel 276): company default 'recess + 0.30 up' (owner 2026-11-13): wall run 5.74 x 0.30 = 1.722 m2 (was x 0.20); recess on its own line (R-T785-2) |
| L-6e6daedebef2db6a83bd | 1F-R8BDA49:wp_wall_upturn | 1.64 | 2.46 | DEFAULT | sunken wet room (T-213 / T-710 panel 280+287): company default 'recess + 0.30 up' (owner 2026-11-13): wall run 8.20 x 0.30 = 2.460 m2 (was x 0.20); recess on its own line (R-T785-2) |
| L-a93486d24647a9e14445 | 1F-RED23B8:wp_wall_upturn | 1.36 | 2.04 | DEFAULT | sunken wet room (T-213 / T-710 panel 275): company default 'recess + 0.30 up' (owner 2026-11-13): wall run 6.80 x 0.30 = 2.040 m2 (was x 0.20); recess on its own line (R-T785-2) |
| L-b842beb71b67af783cd7 | 2F-RE83BED:wp_wall_upturn | 1.78 | 2.67 | DEFAULT | sunken wet room (T-213 / T-710 panel 5BF): company default 'recess + 0.30 up' (owner 2026-11-13): wall run 8.90 x 0.30 = 2.670 m2 (was x 0.20); recess on its own line (R-T785-2) |

## New lines

| item | unit | element | net | label | basis |
|---|---|---|---|---|---|
| FIN.WP.WALL_UPTURN_LM | lm | GF-RDBD4F9:wp_wall_upturn_lm | 6.6432 | MEASURED | run of the upturn strip of line L-519ae15dd6ff755f4aa5 = 1.32864 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RD36087:wp_wall_upturn_lm | 3.20296 | MEASURED | run of the upturn strip of line L-017f9184994017c8a62b = 0.640592 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RD6F891:wp_wall_upturn_lm | 6.824665 | MEASURED | run of the upturn strip of line L-8b981cb63e87f18b13d4 = 1.36493 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RB28769:wp_wall_upturn_lm | 6.0051 | MEASURED | run of the upturn strip of line L-60d7c01f386770e2bf9c = 1.20102 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RF38DAF:wp_wall_upturn_lm | 6.61404 | MEASURED | run of the upturn strip of line L-0226eb38b2c6469296df = 1.32281 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RDF7D28:wp_wall_upturn_lm | 5.40296 | MEASURED | run of the upturn strip of line L-8dd259ad89d2cd276ad2 = 1.08059 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RA3AD49:wp_wall_upturn_lm | 13.5 | MEASURED | run of the upturn strip of line L-f77fe27244893dc1cc9b = 2.7 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RFAD3C4:wp_wall_upturn_lm | 4.8 | MEASURED | run of the upturn strip of line L-31877d6c1cb33b74e5a7 = 0.96 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RB62B55:wp_wall_upturn_lm | 6.7 | MEASURED | run of the upturn strip of line L-6c277fc130b921a7f83e = 1.34 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-R8496F0:wp_wall_upturn_lm | 5.4 | MEASURED | run of the upturn strip of line L-5362cff3511074da962a = 1.08 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 1F-R48CDA5:wp_wall_upturn_lm | 7.9 | MEASURED | run of the upturn strip of line L-60f100105399a9bdfb08 = 1.58 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 1F-RED23B8:wp_wall_upturn_lm | 6.8 | MEASURED | run of the upturn strip of line L-a93486d24647a9e14445 = 1.36 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 1F-R52AC05:wp_wall_upturn_lm | 5.74 | MEASURED | run of the upturn strip of line L-ace6533512ada47d1352 = 1.148 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 1F-R48AA46:wp_wall_upturn_lm | 8.2 | MEASURED | run of the upturn strip of line L-ba15212ec9887e6d4f73 = 1.64 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 1F-R8BDA49:wp_wall_upturn_lm | 8.2 | MEASURED | run of the upturn strip of line L-6e6daedebef2db6a83bd = 1.64 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 1F-R26FA0D:wp_wall_upturn_lm | 15.24 | MEASURED | run of the upturn strip of line L-2d478a44f042f938e4e7 = 3.048 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | 2F-RE83BED:wp_wall_upturn_lm | 8.9 | MEASURED | run of the upturn strip of line L-b842beb71b67af783cd7 = 1.78 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines) |
| FIN.WP.WALL_UPTURN_LM | lm | GF-RC99C2A:wp_wall_upturn_lm | 9.5 | DEFAULT | run of the upturn strip of line L-8090ff20f2b547d1bc96 = 1.9 m2 / rule height 0.20 (R-T785-1; walls only, doorways and open edges are their own lines); pantry run = T-767 DEFAULT 15.00 - 4.50 - 1.00 |
| FIN.WP.SUNKEN_RECESS | m2 | 1F-R48AA46:wp_sunken_recess | 2.109216 | DEFAULT | membrane lining the recess (tray on the structural slab): panel 280 loop 8.7884 x d 0.24 (default 0.30 capped at the beam bound) = 2.1092 m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - slab 0.16, T-710) |
| FIN.WP.SUNKEN_RECESS | m2 | 1F-R48CDA5:wp_sunken_recess | 2.63856 | DEFAULT | membrane lining the recess (tray on the structural slab): panel 298 loop 8.7952 x d 0.30 (default 0.30) = 2.6386 m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - slab 0.16, T-710) |
| FIN.WP.SUNKEN_RECESS | m2 | 1F-R52AC05:wp_sunken_recess | 1.5456 | DEFAULT | membrane lining the recess (tray on the structural slab): panel 276 loop 6.4400 x d 0.24 (default 0.30 capped at the beam bound) = 1.5456 m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - slab 0.16, T-710) |
| FIN.WP.SUNKEN_RECESS | m2 | 1F-R8BDA49:wp_sunken_recess | 2.631 | DEFAULT | membrane lining the recess (tray on the structural slab): panel 280 loop 5.4235 x d 0.24 (default 0.30 capped at the beam bound); panel 287 loop 5.5390 x d 0.24 (default 0.30 capped at the beam bound) = 2.6310 m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - slab 0.16, T-710) |
| FIN.WP.SUNKEN_RECESS | m2 | 1F-RED23B8:wp_sunken_recess | 1.754904 | DEFAULT | membrane lining the recess (tray on the structural slab): panel 275 loop 7.3121 x d 0.24 (default 0.30 capped at the beam bound) = 1.7549 m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - slab 0.16, T-710) |
| FIN.WP.SUNKEN_RECESS | m2 | 2F-RE83BED:wp_sunken_recess | 2.303952 | DEFAULT | membrane lining the recess (tray on the structural slab): panel 5BF loop 9.5998 x d 0.24 (default 0.30 capped at the beam bound) = 2.3040 m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - slab 0.16, T-710) |
| FIN.WP.DOORWAY | m2 | GF-RC99C2A:doorway D120 | 0.2 | DRAWING-READ | floor piece through door D120: printed gap 1.00 x wall 0.20 (T-710 c) |
| FIN.WP.DOORWAY_TRANSITION_NR | pcs | GF-RC99C2A:doorway transition nr D120 | 1.0 | DRAWING-READ | one transition per physical door (Q-35 C): D120 |
| FIN.WP.DOORWAY_TRANSITION | m2 | GF-RC99C2A:doorway transition D120 | 0.2 | ESTIMATE | door width 1.00 x 0.20 upturn carried across the door (same basis as the 14 released transitions, T-767) |
| FIN.WP.TERMINATION | lm | GF-RC99C2A:termination open side | 4.5 | DRAWING-READ | membrane edge on the open dining side, printed DIM 5E1 4.50 (T-710 c; Q-37 A) |
| FIN.WP.PENETRATION | pcs | GF-RC99C2A:wp_penetrations | 1.0 | MEASURED | T-743 sanitary census {'FLOOR_DRAIN': 1} (one WP penetration per fixture, owner default) |

## Upturn components (lm, ours - his)

| room | component | lm | cause |
|---|---|---|---|
| GF pantry (wet zone, Q-37 A) | pantry upturn run (not in his list, owner Q-37 A) | +9.5 | RULE_DIFFERENCE |
| GF lobby wash (2 basins) | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF lobby wash (2 basins) | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF lobby wash (2 basins) | lobby to stair hall, no wall | -1.256 | RULE_DIFFERENCE |
| GF lobby wash (2 basins) | boundary: hand reading vs his perimeter | +0.0002 | TOLERANCE |
| GF lobby wash (2 basins) | engine run vs hand boundary less segments (closure / door block width) | -0.001 | TOLERANCE |
| GF basin space by the stair | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF basin space by the stair | basin space to passage, no wall | -0.9 | RULE_DIFFERENCE |
| GF basin space by the stair | boundary: hand reading vs his perimeter | -0.4 | RULE_DIFFERENCE |
| GF basin space by the stair | engine run vs hand boundary less segments (closure / door block width) | +0.00296 | TOLERANCE |
| GF master bath | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF master bath | boundary: hand reading vs his perimeter | +0.0245 | ENGINE_RIGHT |
| GF master bath | engine run vs hand boundary less segments (closure / door block width) | +0.000165 | TOLERANCE |
| GF core W.C. 245 x 167 (wedge) | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF core W.C. 245 x 167 (wedge) | boundary: hand reading vs his perimeter | +0.1098 | ENGINE_RIGHT |
| GF core W.C. 245 x 167 (wedge) | engine run vs hand boundary less segments (closure / door block width) | -0.0047 | TOLERANCE |
| GF core W.C. 289 x 167 (wedge) | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF core W.C. 289 x 167 (wedge) | boundary: hand reading vs his perimeter | +0.014 | ENGINE_RIGHT |
| GF core W.C. 289 x 167 (wedge) | engine run vs hand boundary less segments (closure / door block width) | +4e-05 | TOLERANCE |
| GF stair-core W.C. 175 x 135 | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF stair-core W.C. 175 x 135 | engine run vs hand boundary less segments (closure / door block width) | +0.00296 | TOLERANCE |
| GF kitchen | doorway segment 1.00 m | -1.0 | RULE_DIFFERENCE |
| GF kitchen | boundary: hand reading vs his perimeter | +0.15 | ENGINE_RIGHT |
| GF driver W.C. | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF driver W.C. | boundary: hand reading vs his perimeter | +0.02 | ENGINE_RIGHT |
| GF W.C. by the reception room | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF wash by the reception room | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| GF wash by the reception room | arch to the reception room, no leaf, no wall | -1.0 | RULE_DIFFERENCE |
| 1F east bath 210 x 225 | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 1F bath by the laundry | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 1F W.C. by the laundry | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 1F W.C. by the laundry | boundary: hand reading vs his perimeter | +0.06 | ENGINE_RIGHT |
| 1F west bath A 245 x 205 | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 1F west bath B 245 x 205 | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 1F west bath B 245 x 205 | boundary: hand reading vs his perimeter | +0.1 | ENGINE_RIGHT |
| 1F laundry | doorway segment 0.90 m | -0.9 | RULE_DIFFERENCE |
| 1F laundry | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 1F laundry | boundary: hand reading vs his perimeter | +0.09 | ENGINE_RIGHT |
| 2F roof-floor W.C. 300 x 185 | doorway segment 0.80 m | -0.8 | RULE_DIFFERENCE |
| 2F roof-floor W.C. 300 x 185 | boundary: hand reading vs his perimeter | -0.05 | ENGINE_RIGHT |

## Floor components (m2, ours - his)

| room | component | m2 | cause |
|---|---|---|---|
| GF lobby wash (2 basins) | 2-dp rounding | +0.000695 | TOLERANCE |
| GF basin space by the stair | passage reveal 0.20 x 1.10 taken into his room (1.55 x 1.10) | -0.22 | RULE_DIFFERENCE |
| GF basin space by the stair | his 1.705 truncated to 2 dp | +0.005 | TOLERANCE |
| GF master bath | diagonal-wall corner 0.983 x 0.982 / 2 out of 2.10 x 2.00 | +0.017683 | ENGINE_RIGHT |
| GF core W.C. 245 x 167 (wedge) | wedge room by shoelace on the drawn wall faces | +0.06761 | ENGINE_RIGHT |
| GF core W.C. 289 x 167 (wedge) | 2-dp truncation | +0.005221 | TOLERANCE |
| GF stair-core W.C. 175 x 135 | 2-dp truncation | +0.0025 | TOLERANCE |
| GF kitchen | printed 300 x 270 + 105 x 150 less two drawn piers 0.045 | +0.080001 | ENGINE_RIGHT |
| GF W.C. by the reception room | 2-dp truncation | +0.005 | TOLERANCE |
| GF wash by the reception room | column corner out of the printed 150 x 210 | -0.0175 | ENGINE_RIGHT |
| 1F east bath 210 x 225 | 2-dp truncation | +0.005 | TOLERANCE |
| 1F bath by the laundry | drawn jamb 0.45 x 0.05 out of 2.00 x 1.80 | -0.0225 | ENGINE_RIGHT |
| 1F W.C. by the laundry | printed 180 x 147 against his 1.80 x 1.44 | +0.056 | ENGINE_RIGHT |
| 1F west bath A 245 x 205 | printed 245 x 205 against his 5.00 | +0.0225 | ENGINE_RIGHT |
| 1F west bath B 245 x 205 | printed 245 x 205 against his 5.00 | +0.0225 | ENGINE_RIGHT |
| 1F laundry | printed 347 x 300 / 185 with the W.C. corner, against his typed 10.00 | +0.151 | ENGINE_RIGHT |
| 2F roof-floor W.C. 300 x 185 | printed 185 against his 1.875 | -0.07 | ENGINE_RIGHT |
| GF pantry (wet zone, Q-37 A) | pantry box 4.50 x 3.00 less the column edge 0.900 x 0.050 | +13.455 | RULE_DIFFERENCE |
