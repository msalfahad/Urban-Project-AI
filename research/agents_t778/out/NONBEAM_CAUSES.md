# T-778 NON-BEAM CONCRETE: candidate vs freelancer by element and named cause (Alsenan; method every villa)

Candidate research/agents_t770/out/LINE_INDEX_V3_0_81.json + T-761 / T-757 fix rows (the T-757 base of 405.60 + 1.20 SAFETY). Concrete **406.79 m3** vs his RC total **352.44 m3** (his summary sheet SUM(E17:E23); plain concrete 47.06 sits on its own row outside it): **+54.36 m3 (+15.4 %)**. Bridge residual **-0.000024 m3**.

Non-beam elements he also carries (paired families without blinding): engine 199.19 vs his 218.05 m3 = **-18.86 m3**. Most of the +40 m3 the Lead named is scope, not measurement: blinding, RC parapets and lintels are in the candidate's concrete and outside his RC total.

## Bridge (engine - his RC total, m3)

| part | m3 |
|---|---|
| T-777 beams (merged split, not re-split) | +13.2778 |
| suspended slabs (T-694 / T-688: +0.46 named, UNRESOLVED scope of 2.98 .. 3.98 m2 1F panels) | +0.4628 |
| STR.CONC.FOOTING | +0.9450 |
| STR.CONC.STRAP | +0.0275 |
| STR.CONC.NECK | +1.5363 |
| STR.CONC.COLUMN | +5.3779 |
| STR.CONC.GROUND_BEAM (building) | -4.6036 |
| STR.CONC.GROUND_BEAM (boundary at N.G.) | -4.0344 |
| STR.CONC.GROUND_SLAB | -7.9091 |
| STR.CONC.STAIR | -6.0266 |
| STR.CONC.DOME | +0.8421 |
| STR.CONC.POOL | -4.9177 |
| STR.CONC.LIFT | -0.1000 |
| boundary wall band + pads + pad blinding (T-776 lines, not re-split; his perimeter tie beam 8.604) | +4.0148 |
| blinding: in the candidate's concrete, outside his RC total (his plain concrete 47.055 on its own row) | +26.7931 |
| parapet RC: ST p.14 typical RC 0.30 upstand his sheet omits | +8.0510 |
| parapet RC above the upstand: A-A / B-B cut RC vs his parapets in blockwork (Q-65 C) | +16.3165 |
| lintels: in-situ concrete figure, his lintels not in his RC sheet | +3.1050 |
| STR.CONC.SAFETY line (ignored pieces + T-757 widths) | +1.1997 |
| residual | -0.000024 |

T-776 (merged after the T-757 base) moves the boundary lines by {'STR.CONC.BLINDING [m3]': 1.8547, 'STR.CONC.BOUNDARY_PAD [m3]': -0.78, 'STR.CONC.BOUNDARY_WALL [m3]': 0.637} m3: not re-split here.
Beams + columns joint: T-777 C2c2 -8.3228 and T-778 C-4 +5.7825 m3 are the same joint volume on opposite lines.

## By verdict (all families, m3)

| verdict | m3 |
|---|---|
| AGREE | +0.0000 |
| ENGINE_RIGHT | -17.9946 |
| RULE_DIFFERENCE | -15.2919 |
| UNRESOLVED | -5.8380 |

## Fix rows

None. Every DEFAULT / ESTIMATE / SAFETY figure inside these families was checked for a printed schedule or section that could replace it: none exists (neck base heights wait on the lift raft level D-43; 2F column heights on the roof section; held ground-beam depths on D-33 / D-34 / D-35; the stair turn pieces and waists on D-08 / D-56 / S-9; the tower dome on D-21; lift pit and tie beam on D-43; pool steps not drawn). No candidate line changes.

## Three lines for the Checker (hand)

1. GROUND SLAB (largest paired family difference, -7.91 m3): his 295.5 m2 x 0.10 = 29.55 vs the GB plan network 289.1136 m2 = 27 panels 217.2315 + strips 71.8821 (T-391): 29.55 - 7.1882 (strips) - 0.6386 (beyond the network) = 21.7232 vs candidate 21.6409 (-0.0823 small reads).
2. GF column C11 (Drive 'Alsenan chalet project' / ST7757 dxf, schedule CGT GR 25 x 110): 2 drawn x 0.275 x 4.50 = 2.475 vs his 1 x 0.25 x 1.10 x 3.75 = 1.03125: COUNT +1.03125 (second drawn C11), JOINT_HEAD 2 x 0.275 x 0.75 = +0.4125.
3. Ground beam BAND0011.3 (exterior main house): T-170 footprint 1.905 m2 (6.35 m x 0.30) x 0.95 (top +0.95 to N.G. +-0.00, two printed levels) = 1.8097 = candidate L-e9a885323ad6; his section on the same run 6.35 x 0.18 = 1.143 (-0.667).

## STR.CONC.FOOTING

Engine **66.5790** vs his **65.6340 m3** (footings sheet rows 13-28 (F .. F.N)): **+0.9450 m3 (+1.4 %)**; residual -0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| F-1 F3 count (2 drawn outlines vs his 1) | +0.6720 | ENGINE_RIGHT | T-233 (Checker-verified): F3 1.60 x 1.40 / 1.40 x 1.60 drawn twice on p.2, schedule 1.60 x 1.40 x 0.30 = 0.672 each |
| F-2 F10 + F one drawn outline 3.25 x 1.40 x 0.50 vs his F10 row only | +0.3150 | RULE_DIFFERENCE | owner Q-31 C 'the bigger area' = the drawn outline (DEFAULT, T-757); of +0.315: the F pad 0.216 he leaves out of his 4 F rows (ENGINE_RIGHT, 5 F tags drawn) and 0.099 outline vs schedule rows (Q-31 rule) |
| F-3 FN 180C clipped by F9 (0.86 m2 drawn) vs his 4 full FN | -0.0420 | ENGINE_RIGHT | T-233: the notch 0.40 x 0.35 is the F9 / FN intersection drawn once, F9 (0.55 deep) owns it (R-CONC-OWN-1); he counts it twice |

Lines (26): L-01830823b3fe396ad418, L-057ca0aa9960e83c2ce3, L-0682b72a63f720f54c8d, L-10f3cd1eb0f81a3892f2, L-1590b76b2fe8f131dc07, L-164ae9d338976be9e582, L-1b7eaa73e9a5e911054d, L-1f0b37d3309ac5bb4c07, L-222e42d97ea28ca69931, L-2bae08911f281f31553f, L-3403073af4f952e49df1, L-35da88665bf36b89a8fc, L-4d689805e55dca54f7cf, L-5146145453fda384253d, L-5d3e72daa69dc769ca5e, L-7d8bf3e464a8406bfcb4, L-88c5feea922f65eb0eaa, L-92617ae61830c3cdce52, L-a244493709ce2e0d23da, L-a753af083197621c2ea4, L-bae601274440c03cf9a2, L-bd8e800cb07a297b25d7, L-cc381dfe7b49cb758166, L-d2c75eb10451e4dd1db5, L-dec7d97d6a15bedee772, L-f6af8a29e2c1b5fdcfd0

## STR.CONC.STRAP

Engine **3.4200** vs his **3.3925 m3** (footings sheet rows 29-31 (STB1-3)): **+0.0275 m3 (+0.8 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| S-1 SB3 part inside the F3 outline above the F3 top + net plan vs his rounded axis lengths | +0.0275 | ENGINE_RIGHT | T-233 / T-230: SB1 1.5925 equal; SB2 net plan 1.1464 vs his 0.5 x 1.0 x 2.30 = 1.15; SB3 0.6516 + 0.0295 above the F3 top (one solid, D-15) vs his 0.65; below materiality (1 % = 0.034 m3) |

Lines (5): L-abd65e1b745315dd17c2, L-b3a779187950eef0fcb6, L-c823e0dbd81e30c66aa5, L-cb4d0756fba483b7787b, L-d43bea72f2c8e939b663

## STR.CONC.NECK

Engine **10.3413** vs his **8.8050 m3** (walls + columns sheet rows 16-28 (necks)): **+1.5363 m3 (+17.4 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| N-1 COUNT | +0.8850 | ENGINE_RIGHT | C11 two drawn positions (10BA / 10DD; GF columns 35C / 37D, T-576) vs his one row; one more C3 / C position (10AE CONFLICT C3 vs C: the position is drawn whatever its mark) |
| N-2 SECTION (C11 schedule FOU 30 x 110 vs his 40 x 110) | -0.3750 | ENGINE_RIGHT | ST p.9 schedule FOU row C11 30 x 110 (company default: the schedule governs a column); his 0.40 is the C11 storey width, not the neck row |
| N-3 HEIGHT drawing-read (founding at the printed minimum, footing H) | +0.2112 | ENGINE_RIGHT | neck = top +0.95 down to the footing top over a founding at the printed minimum 1.50 below EG (ST p.9 n.1) less the 0.17 stack and the scheduled footing H (0.30 .. 0.70): his flat 1.50 ignores the footing depth printed per type (T-657); a deeper formation (Q-21 C) raises both sides |
| N-4 HEIGHT default / low-bound lines | +0.8151 | UNRESOLVED | route G base heights (lift raft level D-43) and low bounds kept under the 0.05 m3 materiality (widths in SAFETY) |

| mark | n_e | n_h | engine | his | count | section | height | H_e |
|---|---|---|---|---|---|---|---|---|
| C1 | 1 | 1 | 0.2925 | 0.225 | 0.0 | 0.0 | 0.0675 | [1.95] |
| C2 | 4 | 4 | 1.164 | 0.9 | 0.0 | 0.0 | 0.264 | [1.93, 1.95] |
| C3 | 6 | 5 | 1.332 | 1.125 | 0.225 | 0.0 | -0.018 | [1.18, 1.28, 1.58, 1.78] |
| C4 | 2 | 2 | 0.564 | 0.45 | 0.0 | 0.0 | 0.114 | [1.88] |
| C5 | 3 | 3 | 0.8712 | 0.81 | 0.0 | 0.0 | 0.0612 | [1.08, 1.88] |
| C6 | 1 | 1 | 0.3738 | 0.315 | 0.0 | 0.0 | 0.0588 | [1.78] |
| C7 | 1 | 1 | 0.3792 | 0.36 | 0.0 | 0.0 | 0.0192 | [1.58] |
| C8 | 2 | 2 | 0.9078 | 0.81 | 0.0 | -0.045 | 0.1428 | [1.78] |
| C9 | 2 | 2 | 1.104 | 0.9 | 0.0 | 0.0 | 0.204 | [1.73, 1.95] |
| C10 | 1 | 1 | 0.3738 | 0.315 | 0.0 | 0.0 | 0.0588 | [1.78] |
| C11 | 2 | 1 | 1.1748 | 0.66 | 0.66 | -0.33 | 0.1848 | [1.78] |
| C | 5 | 5 | 1.14 | 1.125 | 0.0 | 0.0 | 0.015 | [1.28, 1.78, 1.98] |
| CN | 6 | 6 | 0.6642 | 0.81 | 0.0 | 0.0 | -0.1458 | [1.08, 1.18, 1.28] |

Lines (36): L-05a99150a85e9185ae48, L-12f3d8b9375cac407bca, L-132cf60588a44f6af9d6, L-15b8ad39d6b2250c9546, L-15d9da9b17fd373553f0, L-1a9e469651c32cce9b97, L-314946394d849141dda2, L-34346cb438bffee6acec, L-3f7b9501a902579e7406, L-46f2b70254f074885dfc, L-486cd9a0bf52e4b32abb, L-48f2e06e5c946eb1e5a7, L-4ec473f7c0c712919823, L-4ef35980fbb54366703d, L-516989b817e0ccc7cb80, L-53d0b6af1a801c3db58e, L-5aec8a0055215ee5a711, L-5efd9ac69d4cfd9b9a6e, L-6a2040e0fe0bf7391b9c, L-734ff1a78bbe6b7eb4c3, L-85df35f17a205f919aa6, L-8eb74a02fcf5ae4465f8, L-953e87a3e9d0425d404e, L-995eca94ba8dc09a028f, L-ae1bd9cb228d57594e46, L-b21cbf6560f613b39bf0, L-b4c234c8a3873239f67f, L-bbad8cdb4d26986776a6, L-bd741a3faf2318dd8409, L-c1e802184591eac927cf, L-c8c07db4ac0d54d89bbf, L-dd3c32e4340e7a823a6e, L-dd6d11415961b554e906, L-efe50185c0da4244e158, L-f54b7b2acf11ebd2a585, L-fc622ff340ac65a544e3

## STR.CONC.COLUMN

Engine **33.9244** vs his **28.5465 m3** (walls + columns sheet rows 36-47 (GF), 52-61 (1F), 66-71 (roof)): **+5.3779 m3 (+18.8 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| C-2 COUNT GF | -0.5625 | ENGINE_RIGHT | T-576 (merged): the GF roof plan draws 30 SOLID members, all on registered positions; his GF rows carry C1 x2 / C2 x6 / C9 x3 that his own neck rows (C1 x1, C2 x4, C9 x2) and the drawing do not, and miss one drawn C11 (35C / 37D) and the 10AE position |
| C-3 SECTION (drawn / CONFLICT reading vs his row) | -0.4695 | UNRESOLVED | C8 10E0 drawn 0.25 x 0.80 (fits C7, T-566 CONFLICT) vs his C8 / C7 rows; 1F / 2F CGT sections vs his 0.20 widths; designer mark answer replaces it |
| C-4 JOINT_HEAD his columns stop under the beams (A x 0.75) | +5.7825 | RULE_DIFFERENCE | joint ownership (R-CONC-OWN-1): the candidate's column runs slab top to slab top and owns the joint; his stops 0.75 below and his beams run through the support. The same volume sits in T-777 C2c2 -8.32 m3 with the opposite sign: compare beams + columns together |
| C-5 STOREY_BASE GF | -0.1231 | ENGINE_RIGHT | annex columns to the annex roof (+4.30 printed - 0.175 roof build-up DEFAULT - base +0.25 = 3.875 m) vs his 3.75 + 0.75 frame (-0.625 m each), and the 35F family from the +0.25 base (5.20 m, T-576 BASE) |
| C-2 COUNT 1F | +0.4140 | UNRESOLVED | mark assignment, not traced member by member: engine 20 x 1F members vs his 19; per mark C3 -1, C7 -1, C8 +1, C9 +1 (+ C6 +1 in C-1): the 10E0 member is the C8 / C7 CONFLICT (T-566; he lists C7 x2 / C8 x1, the engine C7 x1 / C8 x2), the rest moves between C3 / C6 / C9 positions; designer mark answer (D-66) settles it |
| C-5 STOREY_BASE 1F | +0.0000 | AGREE | 1F 4.20 both frames |
| C-1 COUNT engine-only mark | +0.5040 | UNRESOLVED | 1F C6 (schedule CGT 1ST 20 x 60, DEFAULT section): his 1F rows carry no C6; part of the 1F mark assignment in C-2 COUNT 1F |
| C-2 COUNT 2F | +0.0000 | ENGINE_RIGHT | 2F columns on the SFRS positions his roof rows omit (C9 second position, C2 / C3 / C5 tank columns; T-757 / T-761 schedule CGT 2ND rows) |
| C-5 STOREY_BASE 2F | -0.1675 | UNRESOLVED | 2F height 4.075 = +13.90 printed - 0.175 roof build-up company DEFAULT - 9.65 vs his frame 4.20 (-0.125 m each); the roof build-up is a DEFAULT, the designer's roof section replaces it |

| storey | mark | n_e | n_h | engine | his | count | section | joint | storey_base | A_e | H_e | A_h | H_h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | C | 5 | 5 | 2.0625 | 1.875 | 0.0 | 0.0 | 0.375 | -0.1875 | [0.1] | [3.875, 4.5] | 0.1 | 3.75 |
| GF | C1 | 1 | 2 | 0.45 | 0.75 | -0.375 | 0.0 | 0.075 | 0.0 | [0.1] | [4.5] | 0.1 | 3.75 |
| GF | C10 | 1 | 1 | 0.7875 | 0.6562 | 0.0 | 0.0 | 0.1312 | 0.0 | [0.175] | [4.5] | 0.175 | 3.75 |
| GF | C11 | 2 | 1 | 2.475 | 1.0312 | 1.0312 | 0.0 | 0.4125 | 0.0 | [0.275] | [4.5] | 0.275 | 3.75 |
| GF | C2 | 4 | 6 | 1.8 | 2.25 | -0.75 | 0.0 | 0.3 | 0.0 | [0.1] | [4.5] | 0.1 | 3.75 |
| GF | C3 | 6 | 5 | 3.1319 | 2.3438 | 0.4688 | -0.1687 | 0.5288 | -0.0406 | [0.08, 0.125] | [3.875, 4.5, 5.2] | 0.125 | 3.75 |
| GF | C4 | 2 | 2 | 1.125 | 0.9375 | 0.0 | 0.0 | 0.1875 | 0.0 | [0.125] | [4.5] | 0.125 | 3.75 |
| GF | C5 | 3 | 3 | 2.13 | 1.6875 | 0.0 | 0.0 | 0.3375 | 0.105 | [0.15] | [4.5, 5.2] | 0.15 | 3.75 |
| GF | C6 | 1 | 1 | 0.7875 | 0.6562 | 0.0 | 0.0 | 0.1312 | 0.0 | [0.175] | [4.5] | 0.175 | 3.75 |
| GF | C7 | 1 | 1 | 0.9 | 0.75 | 0.0 | 0.0 | 0.15 | 0.0 | [0.2] | [4.5] | 0.2 | 3.75 |
| GF | C8 | 2 | 2 | 1.9125 | 1.6875 | 0.0 | -0.0937 | 0.3188 | 0.0 | [0.2, 0.225] | [4.5] | 0.225 | 3.75 |
| GF | C9 | 2 | 3 | 2.25 | 2.8125 | -0.9375 | 0.0 | 0.375 | 0.0 | [0.25] | [4.5] | 0.25 | 3.75 |
| 1F | C1 | 1 | 1 | 0.42 | 0.345 | 0.0 | 0.0 | 0.075 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 1F | C2 | 4 | 4 | 1.68 | 1.38 | 0.0 | 0.0 | 0.3 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 1F | C3 | 2 | 3 | 0.84 | 1.035 | -0.345 | 0.0 | 0.15 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 1F | C4 | 2 | 2 | 0.84 | 0.69 | 0.0 | 0.0 | 0.15 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 1F | C5 | 3 | 3 | 1.26 | 1.035 | 0.0 | 0.0 | 0.225 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 1F | C6 | 1 | 0 | 0.504 | 0.0 |  |  |  |  |  |  |  |  |
| 1F | C7 | 1 | 2 | 0.672 | 1.104 | -0.552 | -0.0 | 0.12 | 0.0 | [0.16] | [4.2] | 0.16 | 3.45 |
| 1F | C8 | 2 | 1 | 1.596 | 0.621 | 0.621 | 0.069 | 0.285 | 0.0 | [0.18, 0.2] | [4.2] | 0.18 | 3.45 |
| 1F | C9 | 2 | 1 | 1.512 | 0.69 | 0.69 | -0.138 | 0.27 | 0.0 | [0.18] | [4.2] | 0.2 | 3.45 |
| 1F | PC1 | 1 | 1 | 0.42 | 0.345 | 0.0 | 0.0 | 0.075 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 1F | PC2 | 1 | 1 | 0.588 | 0.483 | 0.0 | 0.0 | 0.105 | 0.0 | [0.14] | [4.2] | 0.14 | 3.45 |
| 2F | C1 | 1 | 1 | 0.4075 | 0.345 | 0.0 | 0.0 | 0.075 | -0.0125 | [0.1] | [4.075] | 0.1 | 3.45 |
| 2F | C2 | 4 | 4 | 1.6425 | 1.38 | 0.0 | 0.0 | 0.3 | -0.0375 | [0.1] | [4.075, 4.2] | 0.1 | 3.45 |
| 2F | C3 | 1 | 1 | 0.42 | 0.345 | 0.0 | 0.0 | 0.075 | 0.0 | [0.1] | [4.2] | 0.1 | 3.45 |
| 2F | C5 | 1 | 1 | 0.4075 | 0.345 | 0.0 | 0.0 | 0.075 | -0.0125 | [0.1] | [4.075] | 0.1 | 3.45 |
| 2F | C9 | 1 | 1 | 0.5705 | 0.621 | 0.0 | -0.138 | 0.105 | -0.0175 | [0.14] | [4.075] | 0.18 | 3.45 |
| 2F | PC | 1 | 1 | 0.3325 | 0.345 | 0.0 | 0.0 | 0.075 | -0.0875 | [0.1] | [3.325] | 0.1 | 3.45 |

Lines (59): L-0b7c92233a525c8b42f2, L-0ede77cfd0badc4c7d62, L-173531a454ee3e9d3317, L-1dc713c83bf62e525ff2, L-1ec3dfd936e83b658b2c, L-26491bc55abff7518911, L-26f6b6f2365c72e42291, L-291ba2ddf4bbe4f14cf7, L-2ac3c9b3b4c2221a0299, L-31a0424bd0efcc93efba, L-322d1a1a7d9504e9cbc6, L-33a9b7728781fcba12e2, L-43dae3d6dfec957b26a8, L-4aed92c117a7ab1c90ee, L-4c4496579e5bfa20ae9f, L-53f223b06db14ac41d47, L-541c7e565bb93ecdb78b, L-689abc61dfc445f60224, L-694a75c84dd6e4bb4491, L-6f56016cd0282ebad28a, L-734dc85d1a4ffbde5655, L-755eb56b55e86301b488, L-7b41af5790ea7ad5156e, L-7d70692d03102a2dc306, L-831f6fe3de133294bb8f, L-84bf7fb482a98fdbe482, L-85809d3db52bb93dfe96, L-8a88f805c490b970d754, L-8b751f06280405a6b658, L-8de64040a1c3ae6cf137, L-8df3988123e987fa87f9, L-8f8ad257d9b2cb9e027f, L-90ed3048543112eb4be1, L-919a5749ef79759e01ca, L-96a9079f54bc9bae6482, L-99451ab1afb179bfb75c, L-9a33d59e28a53df74b18, L-9cb26d86575a92694880, L-9f5a647014bbf83359f9, L-a2c6fa502bd864cf5da2, L-a2cb6d533860e6f37b3e, L-a87ea657a42a311cb851, L-a8abdc061090a72e84a4, L-ae51e56262137366926b, L-bc01297b1c4a4c45a15f, L-bcefe951cf96fb351bf8, L-c0b3340a906c2c7650f8, L-c10e2945d582b5a03126, L-c41f79b9171044490619, L-c677b628a776d3b87b02, L-cc702b8541c15fdfd98c, L-d2e900a1b15cef2a913f, L-d79d17d14f39d5148cb8, L-d9530ea806606b886fc9, L-e112e2add2f8979a6c39, L-e6c1c9a7feec10f64975, L-f169ec8deb0f70fe2681, L-fa1c346855c5040632a5, L-fad18af6e7139a5e99d1

## STR.CONC.GROUND_BEAM (building)

Engine **33.3764** vs his **37.9800 m3** (ground-beam sheet rows 13-14 (longitudinal 100 m + transverse 111 m at 0.30 x 0.60)): **-4.6036 m3 (-12.1 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| G-1 SECTION DEFAULT interior p.13 class D 0.30 | -2.5553 | UNRESOLVED | held runs valued at the p.13 class by clear span (company default 'exterior GB = same mark'; designer D-33 / D-34 / D-35 replace it) or kept at the low bound under materiality |
| G-1 SECTION DEFAULT interior p.13 class D 0.40 | -1.0962 | UNRESOLVED | held runs valued at the p.13 class by clear span (company default 'exterior GB = same mark'; designer D-33 / D-34 / D-35 replace it) or kept at the low bound under materiality |
| G-1 SECTION DEFAULT interior p.13 class D 0.41 | -0.0440 | UNRESOLVED | held runs valued at the p.13 class by clear span (company default 'exterior GB = same mark'; designer D-33 / D-34 / D-35 replace it) or kept at the low bound under materiality |
| G-1 SECTION DEFAULT interior p.13 class D 0.60 | -0.0000 | AGREE | typical 30 x 60 by clear span (DEFAULT on held runs) = his section |
| G-1 SECTION MEASURED exterior main house D 0.95 (two printed levels; ring 157 / 158 with end pieces) | +5.7630 | ENGINE_RIGHT | T-289 / T-391 (Checker-verified basis): top +0.95 to N.G. +-0.00 printed by two levels on the exterior main-house beams; his 0.60 everywhere |
| G-1 SECTION MEASURED interior p.13 class D 0.40 | -3.2907 | ENGINE_RIGHT | ST p.13 typical sections by clear span (< 2.5 m 30 x 30, < 5 m 30 x 40, > 5 m 30 x 60; T-242 / T-391): his one 30 x 60 section on every run |
| G-1 SECTION MEASURED interior p.13 class D 0.60 | +0.0000 | AGREE | p.13 typical 30 x 60 both sides |
| G-2 LENGTH his lump 211 m vs the engine's bound runs face to face | -3.4841 | UNRESOLVED | his 100 + 111 m lies inside the drawn envelope (face to face 193.76 .. through every support 231.91 m, T-391): which supports he runs through cannot be split from two lumps |
| G-3 unbound piece (no footprint in the band ledger) | +0.1037 | UNRESOLVED | BAND0009 0.1037 m3: valued run with no T-170 footprint row; below materiality |

Engine bound run length 191.644 m (plan / 0.30) vs his 211 m.

Lines (58): L-00465df980165c529476, L-0bb78accf8c0a0fbdbaf, L-0c5ede7fd2c9e425aa8d, L-0e30aadba2eebc6c3ede, L-0e852cca42fb8b765c58, L-1146bdecd41491ce9382, L-131df76e442a8b7cc2e9, L-1487bdda099006e0c4ba, L-151a282bcf2d5324a618, L-21795b350fbd09150c43, L-26fcfbbb143269e7bb58, L-27d104ca6fc3556d16e6, L-3284f44000c02179ace7, L-361f5e913c566c4fe2b5, L-3e7ea87496653eb75704, L-402dbe61d1c924144a3c, L-4129e781d6133b963bf7, L-43d1d1031b3d3ddd1cc4, L-46f25f72b44e8bc3e2e0, L-4783c6e18002c3a8a37e, L-56ebab0b7b448d0abeb1, L-5af89b9f1e5b90daf8f5, L-62243c74c430d383be86, L-62f712462a36d4ad1b32, L-6bf14711798e5af93594, L-7076482d75ca42691468, L-760f6c369aa655adc84d, L-7afad512258c1bad8519, L-81444e222487437e257e, L-95a1f198cfe7f398d6ae, L-970bac563cbcd69e2a30, L-9e28c7012784a8dc33c8, L-9f49f5fafcb9322c90b5, L-a55bfa01b726ef11650c, L-a8c5c32c7a785c1e3f05, L-bde0257c24588948167f, L-bf5eb56348883cb2776d, L-c0b7102a36344a0349f5, L-c5902fd02c58b85a5df1, L-c9bb2eca50a2a2c8b569, L-cc6aaa99e1892f34b92f, L-cfb4555cb26b39934bff, L-d08e7a9d809a56733ff9, L-d53e5eb08e2c6c668254, L-d8b98b143e293d30833b, L-dac43ee18f55433b57e7, L-e16c98075f69532a3dc7, L-e2134034441cb7db7bd7, L-e24946df436cbc25fca6, L-e8536bc4f2699a24e2ab, L-e9a885323ad6ec3ea32b, L-efbed17455bb224e126e, L-f0e25ad2cf73bf2a35ea, L-f24cf117a9ce1e875785, L-fadb548a6843001d45b0, L-fb53ac7edf5914afd6f5, L-fe78ae283abfb6256358, L-ff727b2a52e39509a659

## STR.CONC.GROUND_BEAM (boundary at N.G.)

Engine **3.5256** vs his **7.5600 m3** (ground-beam sheet row 15 (fence ground beam)): **-4.0344 m3 (-53.4 %)**; residual -0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| B-1 SECTION ST p.14 'GROUND BEAM (20x40)' vs his 0.30 x 0.60 | -4.2000 | ENGINE_RIGHT | printed section on ST p.14 A-A (T-761 DRAWING-READ, Checker plan 8.814 m2) |
| B-2 LENGTH 5 drawn runs 44.07 m vs his 42 m | +0.1656 | ENGINE_RIGHT | drawn fence-side runs 44.07 m (T-254 / T-761); his 42 m a round figure |

Lines (1): L-fb7a6431fede62e93fd5

## STR.CONC.GROUND_SLAB

Engine **21.6409** vs his **29.5500 m3** (ground-beam sheet row 11 (ground slab 295.5 m2 x 0.10)): **-7.9091 m3 (-26.8 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| GS-1 his plate over the beam / column / lift strips the beams own | -7.1882 | ENGINE_RIGHT | T-391 (merged): 71.8821 m2 of strips under his one 295.5 m2 plate; the ground beams already carry that concrete full depth from the slab top (C1) |
| GS-2 his area beyond the whole drawn network | -0.6386 | ENGINE_RIGHT | his 295.5 m2 exceeds the own network 289.1136 m2 (panels + strips) of the GB plan: 6.39 m2 on no drawn element |
| GS-3 engine faces vs own panels (T-391 F3 small reads) | -0.0823 | UNRESOLVED | member overlap in 49a7dae5, court-side split at arc 158, lift-side oblique panels (T-391 F3); below 1 % |

Lines (26): L-01ab48550ede182f95f8, L-1031c9be9aaae364fef4, L-12a2c3c89221d4e4470b, L-16dd2274da8100309927, L-22f26ff4a88e16eccff1, L-318b26bd7fe7b9c0a026, L-3e491437888384514498, L-41cfb82ed733f4d6e3a5, L-5e79c7fa289cf65458d4, L-5e881fd31885949d4e66, L-69527cb9affdad474268, L-8134577db97df050ff28, L-87d6ed48126aa9857e17, L-8b681fdaa3b3910b2b7b, L-90b863dddb0d2d66006d, L-9ee6ac27fb8cd893eb93, L-a36f703f0b42eed2195c, L-a7ab57d873e26a587fd9, L-ac92bcb7d88ef65bc82f, L-b27103a640f67f285132, L-bb5f541401f358993181, L-e2c5b39a34b082f7048c, L-e99390a3f7025b2195a5, L-ecc50c39d9be087ead23, L-f192ff5f4962efa8d08f, L-f8a170a867d268254e07

## STR.CONC.STAIR

Engine **9.0262** vs his **15.0528 m3** (stair sheet rows 11, 12, 20, 21): **-6.0266 m3 (-40.0 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| ST-1 ST-01 his 4 x 5.30 m sloped length vs drawn 14.428 m | -2.2753 | ENGINE_RIGHT | T-258 (merged): his 5.30 m per flight includes the floor landing; drawn sloped flights 14.428 m |
| ST-2 ST-01 his 0.28 / 0.20 plates vs drawn equivalent 0.2331 / T 16 | -0.9873 | RULE_DIFFERENCE | his flat 'slab + steps' plate vs the drawn waist T 16 + step triangles (T-258) |
| ST-3 ST-01 landing area 5.04 vs drawn 4.375 m2 | -0.1330 | ENGINE_RIGHT | T-258: landings 3 x 1.2 x 1.4 vs drawn MS1-LD + MS2-LD W / E |
| ST-4 ST-01 flight heads / foot billed in the beams B20 / B23 | -0.1402 | RULE_DIFFERENCE | joint ownership: the flight ends inside B20 / B23 are beam concrete in the candidate |
| ST-5 ST-02 5.537 m of his 16.4 m run on no drawing | -1.8604 | ENGINE_RIGHT | T-258: outer string sloped 10.863 m drawn; 5.537 m of his run on no sheet |
| ST-6 ST-02 curved part: his flat 1.2 x 0.28 vs wedges + helicoid waist (ESTIMATE) | -1.0259 | UNRESOLVED | curved treads + helicoid waist 0.16 ESTIMATE (T-761); D-08 replaces it |
| ST-7 ST-03 his run 1.80 vs drawn 1.20 m | -0.4704 | ENGINE_RIGHT | T-258: drawn run 1.20 m (5 risers 0.170) |
| ST-8 ST-03 his 0.28 flat vs steps + 0.16 waist on the slope (ESTIMATE) | +0.1866 | UNRESOLVED | ST-03 prints no waist; 0.16 = the ST-01 printed plate (ESTIMATE, S-9 / D-56 replace it) |
| ST-9 ST-01b lobby flight not in his sheet | +0.2659 | ENGINE_RIGHT | 0.1003 drawn steps (T-258); the 0.1656 waist is an ESTIMATE (0 if on compacted fill) |
| ST-10 ST-01 turn pieces (winders, flat turn, turn riser) DEFAULT | +0.4134 | UNRESOLVED | winder wedges + flat turn 1.44 x 0.16 + turn riser (T-711 / T-761 DEFAULT); the T-258 table held them without value |

Engine by flight {'ST-01': 5.0088, 'ST-01b': 0.2659, 'ST-02': 2.6241, 'ST-03': 1.1274}; his by flight {'ST-01': 8.1312, 'ST-02': 5.5104, 'ST-03': 1.4112}.

Lines (11): L-056402f98a6dbbcde0a0, L-061e18cf35a4b6b33d68, L-2416e65f053a14199cfc, L-659243ed9fc2831c3ae8, L-67e4b0485135f84acc46, L-7863355dfcb68a681d2d, L-821032bc04a0b0d02133, L-85f64587588af8537b4b, L-b6b0354b7842f0ed6e41, L-bb0e57b1948175a3d5b8, L-e37d81a8be8e0aa0010c

## STR.CONC.DOME

Engine **7.6221** vs his **6.7800 m3** (stair sheet row 13 (3 domes)): **+0.8421 m3 (+12.4 %)**; residual -0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| D-1 his typed 22.6 m2 per dome vs the shell mid-surface 25.407 m2 | +0.8421 | ENGINE_RIGHT | T-185 (Checker re-derived): ST p.7 DETAIL OF DOME rise 1.90 / span 4.42 / 0.10 shell = 2.5407 m3; the tower dome DEFAULT at the same shell (D-21); his 22.6 m2 is not the shell area |

Lines (3): L-8ea34765d16b54898140, L-d5401fa8986900c66c37, L-fffa895ed96b9d6a682c

## STR.CONC.POOL

Engine **7.4303** vs his **12.3480 m3** (pool sheet rows 11-15): **-4.9177 m3 (-39.8 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| P-1 pump room walls + floor not drawn | -3.4800 | ENGINE_RIGHT | T-183 r2 / T-193 (merged): no pump room on any ST / arch sheet read; consultant P-2 |
| P-2 pool walls: base thickness carried into the wall, 0.20 above the rim, length | -1.4919 | ENGINE_RIGHT | T-183: walls = band 2.3567 m2 x 1.20 (rim to base top); his 12 x 1.80 x 0.20 carries the base thickness +0.96, 0.20 above the drawn rim +0.48, length +0.05 |
| P-3 pool floor: drawn D outline 10.9356 m2 vs his typed 10.8 m2 (both 0.40) | +0.0542 | ENGINE_RIGHT | drawn D outline 3.50 x 1.75 + pi 1.75^2 / 2 (T-385) |
| P-4 steps | +0.0000 | AGREE | the candidate's SAFETY block copies his size (never VERIFIED; steps not drawn) |

Lines (3): L-15a128c38982af899894, L-36efa902da4263479e0b, L-b62a7065645589011141

## STR.CONC.LIFT

Engine **2.3000** vs his **2.4000 m3** (walls + columns sheet row 11 (lift walls)): **-0.1000 m3 (-4.2 %)**; residual -0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| L-1 pit wall ring plan 1.10 m2 (drawn, T-401) vs his 8 m x 0.20 = 1.60 m2, both 1.50 high | -0.7500 | ENGINE_RIGHT | the 1.80 x 1.80 shaft ring 1.10 m2 drawn (T-401, Checker T-394): two sides are the GB / beam strips already owned; his 8 m centre-line ring counts them again. Height 1.50 SAFETY on both sides (D-43) |
| L-2 GF tie beam (ST p.8 n.19) not in his sheet | +0.6500 | UNRESOLVED | printed note, section not printed: DEFAULT nearest printed (shaft ring beams); D-43 |

Lines (2): L-5ae06fda7d729d54c033, L-684fcad323adc0c8a267

## STR.CONC.BLINDING

Engine **26.7931** vs his **47.0550 m3** (footings sheet row 11 (outside his RC total)): **-20.2619 m3 (-43.1 %)**; residual +0.000000 m3 (0.000 % of the element).

| cause | m3 | verdict | reason |
|---|---|---|---|
| BL-1 his plate 15.00 x 31.37 x 0.10 over the whole plot vs plain concrete under each member | -20.2619 | RULE_DIFFERENCE | owner table 13 Nov / T-233: he blinds the whole plot (no sheet draws a plate; P7 compacted soil under the slab); the candidate blinds under footings, ground beams, straps, pool, lift raft (boundary pads: T-776 line, in the boundary bridge part) (p.13 '10 | L x W | 10'). Outside his RC total 352.44 (his summary row 15, plain concrete) |

Lines (7): L-080c97f5f6a92452cd04, L-10032bf9a60368473a7b, L-16b95607fc88cda3844a, L-35382b18e2e362df3ae6, L-7a5214a334ea3559fa2d, L-893c3db13b14dc38625e, L-98eb2d58075c9eddf1b4
