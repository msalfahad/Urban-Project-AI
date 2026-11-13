# T-761 FIX ROWS on ARCH_TAKEOFF_V3.0.78: blank STR.CONC lines to figures (lane S, DELIVERY MODE F-02)

Blank STR.CONC lines: 80 before -> 0 after (67 with a figure, 13 IGNORED_SMALL < 0.05 m3 covered by the SAFETY line). Added m3: 58.42 + SAFETY 1.00. Ranged lines kept with their designer item: 114.

| item | lines | m3 |
|---|---|---|
| STR.CONC.BEAM | 14 | 5.26 |
| STR.CONC.BLINDING | 2 | 1.96 |
| STR.CONC.BOUNDARY_PAD | 1 | 3.12 |
| STR.CONC.COLUMN | 2 | 0.84 |
| STR.CONC.DOME | 1 | 2.54 |
| STR.CONC.GROUND_BEAM | 19 | 11.96 |
| STR.CONC.LIFT | 2 | 2.30 |
| STR.CONC.LINTEL | 12 | 0.73 |
| STR.CONC.NECK | 4 | 1.46 |
| STR.CONC.PARAPET | 4 | 24.37 |
| STR.CONC.POOL | 1 | 0.23 |
| STR.CONC.STAIR | 5 | 3.66 |

By label: DEFAULT 45.56 m3, DRAWING-READ 4.44 m3, ESTIMATE 2.38 m3, SAFETY 6.04 m3

| line | item | before | after | label | basis |
|---|---|---|---|---|---|
| L-17c4238c0ef76656d06e | BEAM | HELD blank | 0.2610 | DEFAULT | 2F edge projection 0.1 x 4.35 m: plan 0.4350 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.2610 m3; slab-cast at 0.16 would give 0.0696; D-05 / D-26 replace it |
| L-331d4bbef719a7f0bbca | BEAM | HELD blank | 0.0630 | DEFAULT | GF edge projection 0.2 x 0.5251 m (edges 2C6 2C7): plan 0.1050 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.0630 m3; slab-cast at 0.16 would give 0.0168; D-05 / D-26 replace it |
| L-377cb988b2271c2e2e4d | BEAM | HELD blank | 0.3414 | DEFAULT | 1F edge projection 0.1 x 5.69 m: plan 0.5690 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.3414 m3; slab-cast at 0.16 would give 0.0910; D-05 / D-26 replace it |
| L-54e397fe7b1485b2e8fe | BEAM | HELD blank | 0.0629 | DEFAULT | 1F edge projection 0.2 x 0.5238 m (edges 5E1 5E6): plan 0.1048 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.0629 m3; slab-cast at 0.16 would give 0.0168; D-05 / D-26 replace it |
| L-56c49c3c2596a0869533 | BEAM | HELD blank | 0.0960 | DEFAULT | 1F-STRIP-AT-COL: plan 0.16 m2 (T-724 census) x 0.60 company default = 0.0960 m3 |
| L-56d278bedc8dda2837a9 | BEAM | HELD blank | 0.9265 | DEFAULT | 1F edge projection 0.2985 x 4.2845 m (edges 5DE 629): plan 1.5441 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.9265 m3; slab-cast at 0.16 would give 0.2471; D-05 / D-26 replace it |
| L-634cefe5e8a7fb458e16 | BEAM | HELD blank | 0.3599 | DEFAULT | GF edge projection 0.1999 x 3.0005 m (edges 2C6 2C7): plan 0.5998 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.3599 m3; slab-cast at 0.16 would give 0.0960; D-05 / D-26 replace it |
| L-67f3d325019e618328eb | BEAM | HELD blank | 0.3598 | DEFAULT | 1F edge projection 0.2 x 2.9987 m (edges 5E1 5E6): plan 0.5997 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.3598 m3; slab-cast at 0.16 would give 0.0960; D-05 / D-26 replace it |
| L-89d266a3e5280a10a3b9 | BEAM | HELD blank | IGNORED_SMALL 0.0176 | DEFAULT | 1F-NW-CORNER: plan 0.029309 m2 (T-724 census) x 0.60 company default = 0.0176 m3 |
| L-a9d5e7dc22013e24d691 | BEAM | HELD blank | 0.8999 | DEFAULT | 1F edge projection 0.2 x 7.4996 m (edges 5E7 5E5): plan 1.4999 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.8999 m3; slab-cast at 0.16 would give 0.2400; D-05 / D-26 replace it |
| L-ab37afa17f2ac5b0efd1 | BEAM | HELD blank | 0.8996 | DEFAULT | east dome-opening ring in bay: plan 1.7993 m2 (T-721) x 0.50 = depth of the twin west ring B4 (L-48b7d139 released 0.7552, same ST p.7 DETAIL OF DOME; adjacent-span default) = 0.8996 m3; 0.60 default would give 1.0796; D-28 replaces it |
| L-aba59a2157a48a69e2fb | BEAM | HELD blank | 0.4920 | DEFAULT | GF edge projection 0.2 x 4.1 m: plan 0.8200 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.4920 m3; slab-cast at 0.16 would give 0.1312; D-05 / D-26 replace it |
| L-bb49e831f053bd30a6ce | BEAM | HELD blank | 0.1619 | DEFAULT | 1F edge projection 0.3 x 0.8994 m (edges 5C1 619): plan 0.2698 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.1619 m3; slab-cast at 0.16 would give 0.0432; D-05 / D-26 replace it |
| L-e296002577c012f0afd4 | BEAM | HELD blank | IGNORED_SMALL 0.0176 | DEFAULT | GF-NW-CORNER: plan 0.029309 m2 (T-724 census) x 0.60 company default = 0.0176 m3 |
| L-f113ed57f7875fed9a67 | BEAM | HELD blank | 0.0960 | DEFAULT | GF-STRIP-AT-COL: plan 0.16 m2 (T-724 census) x 0.60 company default = 0.0960 m3 |
| L-fbb65dfd2a66a16714ac | BEAM | HELD blank | 0.2400 | DEFAULT | 1F edge projection 0.4 x 1.0 m: plan 0.4000 m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = 0.2400 m3; slab-cast at 0.16 would give 0.0640; D-05 / D-26 replace it |
| L-893c3db13b14dc38625e | BLINDING | HELD blank | 0.9155 | DRAWING-READ | pool blinding: outline 7C6 grown by the printed wrap 0.10, clipped at the plot line, 11.8511 - 2.6958 (pit blinding already in L-98eb2d58) = 9.1553 m2 x 0.10 = 0.9155 m3 (T-667) |
| L-d0313e5d204e2758996a | BLINDING | HELD blank | 1.0400 | SAFETY | blinding under the 10 boundary pads: 1.30 x 0.80 x 0.10 (projection not printed) = 1.040 m3; follows the pad count |
| L-cda8f41522dc6f42b3d6 | BOUNDARY_PAD | HELD blank | 3.1200 | SAFETY | boundary pads 1.30 x 0.80 x 0.30 (ST p.14) = 0.312 m3 each x 10 (one column at each end of the 5 drawn band runs: count 'SEE ARCH PLAN', none drawn) = 3.120 m3; designer item replaces the count |
| L-0ede77cfd0badc4c7d62 | COLUMN | HELD blank | 0.4200 | DEFAULT | C2@247685,64087 2F: schedule section 0.10 m2 x storey 4.20 = 0.4200 m3 (= released 1F lines of the same mark, route G register 0.42); B15 up / down-stand on the tank (D-44) not added |
| L-c10e2945d582b5a03126 | COLUMN | HELD blank | 0.4200 | DEFAULT | C3@247476,61310 2F: schedule section 0.10 m2 x storey 4.20 = 0.4200 m3 (= released 1F lines of the same mark, route G register 0.42); B15 up / down-stand on the tank (D-44) not added |
| L-d5401fa8986900c66c37 | DOME | HELD blank | 2.5407 | DEFAULT | DOME-3 tower dome: arch circle r 2.205 (dia 4.41) and SE elevation 441 / 215 = the shells A / B; the only ST p.7 DETAIL OF DOME (442 / 190 / 10) -> same shell 2.5407 m3 (L-8ea34765 / L-fffa895e released); D-21 replaces it |
| L-00465df980165c529476 | GROUND_BEAM | HELD blank | 0.2880 | DEFAULT | drawn plan 0.7200 m2 x 0.40 (ST p.13 typical 30x40 by clear span 3.10 (route G register); company default exterior / loaded GB = same mark) = 0.2880 m3; holds D-35 |
| L-0bb78accf8c0a0fbdbaf | GROUND_BEAM | HELD blank | 0.2423 | DEFAULT | drawn plan 0.8077 m2 x 0.30 (ST p.13 typical 30x30 by clear span 2.43 (T-712); company default exterior / loaded GB = same mark) = 0.2423 m3; holds D-33 |
| L-1487bdda099006e0c4ba | GROUND_BEAM | HELD blank | 0.2205 | DEFAULT | drawn plan 0.7350 m2 x 0.30 (ST p.13 typical 30x30 by clear span 2.45 (T-712); company default exterior / loaded GB = same mark) = 0.2205 m3; holds D-33 |
| L-21795b350fbd09150c43 | GROUND_BEAM | HELD blank | 0.4560 | DEFAULT | drawn plan 1.1400 m2 x 0.40 (ST p.13 typical 30x40 by clear span 3.80 (route G register); company default exterior / loaded GB = same mark) = 0.4560 m3; holds D-35 (court) |
| L-3284f44000c02179ace7 | GROUND_BEAM | HELD blank | 0.2070 | DEFAULT | drawn plan 0.6900 m2 x 0.30 (ST p.13 typical 30x30 by clear span 2.30 (route G register); company default exterior / loaded GB = same mark) = 0.2070 m3; holds D-35 |
| L-402dbe61d1c924144a3c | GROUND_BEAM | HELD blank | 1.7460 | DEFAULT | drawn plan 2.9100 m2 x 0.60 (ST p.13 typical 30x60 by clear span 10.13 (route G register); company default exterior / loaded GB = same mark) = 1.7460 m3; holds D-35 |
| L-4783c6e18002c3a8a37e | GROUND_BEAM | HELD blank | 1.0800 | DEFAULT | drawn plan 1.8000 m2 x 0.60 (ST p.13 typical 30x60 by clear span 6.40 (route G register); company default exterior / loaded GB = same mark) = 1.0800 m3; holds D-35 |
| L-5af89b9f1e5b90daf8f5 | GROUND_BEAM | HELD blank | 0.9000 | DEFAULT | drawn plan 1.5000 m2 x 0.60 (ST p.13 typical 30x60 by clear span 5.00 (T-712) ON_LIMIT, c/c 5.30 -> 30x60 (route G both readings); company default exterior / loaded GB = same mark) = 0.9000 m3; holds D-33 |
| L-62243c74c430d383be86 | GROUND_BEAM | HELD blank | 0.0540 | DEFAULT | drawn plan 0.1800 m2 x 0.30 (ST p.13 typical 30x30 by clear span 0.60 (route G register); company default exterior / loaded GB = same mark) = 0.0540 m3; holds D-35 (court) |
| L-6bf14711798e5af93594 | GROUND_BEAM | HELD blank | 0.1350 | DEFAULT | drawn plan 0.4500 m2 x 0.30 (ST p.13 typical 30x30 by clear span 1.50 (route G register); company default exterior / loaded GB = same mark) = 0.1350 m3; holds D-35 |
| L-95a1f198cfe7f398d6ae | GROUND_BEAM | HELD blank | 0.4230 | DEFAULT | drawn plan 1.0575 m2 x 0.40 (ST p.13 typical 30x40 by clear span 3.52 (T-712); company default exterior / loaded GB = same mark) = 0.4230 m3; holds D-33 |
| L-a55bfa01b726ef11650c | GROUND_BEAM | HELD blank | 0.1170 | DEFAULT | drawn plan 0.3900 m2 x 0.30 (ST p.13 typical 30x30 by clear span 1.30 (route G register); company default exterior / loaded GB = same mark) = 0.1170 m3; holds D-35 (court) |
| L-a8c5c32c7a785c1e3f05 | GROUND_BEAM | HELD blank | 0.1890 | DEFAULT | drawn plan 0.6300 m2 x 0.30 (ST p.13 typical 30x30 by clear span 2.10 (T-712); company default exterior / loaded GB = same mark) = 0.1890 m3; holds D-33 |
| L-b4a13a43967ee4765662 | GROUND_BEAM | HELD blank | IGNORED_SMALL 0.0450 | DEFAULT | drawn plan 0.1500 m2 x 0.30 (ST p.13 typical 30x30 by clear span 0.50 (route G register); company default exterior / loaded GB = same mark) = 0.0450 m3; holds D-35 |
| L-be6708e07b40efa02779 | GROUND_BEAM | HELD blank | IGNORED_SMALL 0.0090 | DEFAULT | drawn plan 0.0300 m2 x 0.30 (ST p.13 typical 30x30 by clear span 0.10 (route G register); company default exterior / loaded GB = same mark) = 0.0090 m3; holds D-35 |
| L-cfb4555cb26b39934bff | GROUND_BEAM | HELD blank | 0.4230 | DEFAULT | drawn plan 1.0575 m2 x 0.40 (ST p.13 typical 30x40 by clear span 3.52 (T-712); company default exterior / loaded GB = same mark) = 0.4230 m3; holds D-33 |
| L-d53e5eb08e2c6c668254 | GROUND_BEAM | HELD blank | 0.1477 | DEFAULT | drawn plan 0.4922 m2 x 0.30 (ST p.13 typical 30x30 by clear span 1.54 (T-712); company default exterior / loaded GB = same mark) = 0.1477 m3; holds D-33 |
| L-d8b98b143e293d30833b | GROUND_BEAM | HELD blank | 1.0440 | DEFAULT | drawn plan 1.7400 m2 x 0.60 (ST p.13 typical 30x60 by clear span 5.80 (route G register); company default exterior / loaded GB = same mark) = 1.0440 m3; holds D-35 |
| L-e16c98075f69532a3dc7 | GROUND_BEAM | HELD blank | 0.1626 | DEFAULT | drawn plan 0.5419 m2 x 0.30 (ST p.13 typical 30x30 by quarter ring centre-line 1.81; company default exterior / loaded GB = same mark) = 0.1626 m3; holds D-35 |
| L-e24946df436cbc25fca6 | GROUND_BEAM | HELD blank | 0.6024 | DEFAULT | drawn plan 1.5060 m2 x 0.40 (ST p.13 typical 30x40 by clear span 4.97 (T-712); company default exterior / loaded GB = same mark) = 0.6024 m3; holds D-33 |
| L-fb7a6431fede62e93fd5 | GROUND_BEAM | HELD blank | 3.5256 | DRAWING-READ | boundary band 5 runs 44.07 m: 8.8140 m2 (Checker own) x 0.40 (ST p.14 'GROUND BEAM (20x40)') = 3.5256 m3; minus 0.024 m3 per boundary column (count not printed, each below materiality: not deducted) |
| L-5ae06fda7d729d54c033 | LIFT | HELD blank | 0.6500 | DEFAULT | GF tie beam (ST p.8 n.19), runs 1.80 / 1.80 / 1.20 / 0.70 = 5.50 m: nearest printed section = the GF-roof shaft ring beams on the same runs (B14 0.20x0.75x1.80 0.270 + B1 0.20x0.40x0.70 0.056 + B7 0.20x0.75x1.20 0.180 + B1 0.20x0.40x1.80 0.144) = 0.650 m3; D-43 replaces it |
| L-684fcad323adc0c8a267 | LIFT | HELD blank | 1.6500 | SAFETY | pit walls 0.20 ring: plan 1.100 m2 (T-401, Checker T-394) x 1.50 m pit height = 1.650 m3; pit depth is a lift-supplier item (D-43 / RFI L-1) and no company default exists: 1.50 is the SAFETY height (upper end of usual home-lift pits), replaced by the supplier depth |
| L-072bc37c5486905a9d21 | LINTEL | HELD blank | 0.0520 | DEFAULT | D-GF-09: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; width = printed door type D120 1.00 (drawn gap 0.90 gives 0.048: same materiality class boundary, named); existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-0d5e2e3ac4167df90d6d | LINTEL | HELD blank | 0.0520 | DEFAULT | D-GF-08: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (the lift tie beam of ST p.8 n.19 (unsized)); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-1313767d897f06ef95b6 | LINTEL | HELD blank | IGNORED_SMALL 0.0360 | DEFAULT | W04: 0.20 x 0.20 (ST p.13 schedule) x (0.60 + 2 x 0.15 bearing default) = 0.0360 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (CB6 BM-GF-030 (20x75) over the drawn head +2.80); printed note 'MIN 40 cm' bearing would give 0.0560 |
| L-17953d7882899d43473f | LINTEL | HELD blank | IGNORED_SMALL 0.0330 | DEFAULT | D-GF-14: 0.15 x 0.20 (ST p.13 schedule) x (0.80 + 2 x 0.15 bearing default) = 0.0330 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0480 |
| L-1c0e7646345156fcd0cb | LINTEL | HELD blank | IGNORED_SMALL 0.0480 | DEFAULT | D-2F-02: 0.20 x 0.20 (ST p.13 schedule) x (0.90 + 2 x 0.15 bearing default) = 0.0480 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (BM-2F-017 (unsized)); printed note 'MIN 40 cm' bearing would give 0.0680 |
| L-274b112580029084b80e | LINTEL | HELD blank | IGNORED_SMALL 0.0330 | DEFAULT | D-GF-04: 0.15 x 0.20 (ST p.13 schedule) x (0.80 + 2 x 0.15 bearing default) = 0.0330 m3; printed note 'MIN 40 cm' bearing would give 0.0480 |
| L-2c1c49db7cd7b16c6206 | LINTEL | HELD blank | IGNORED_SMALL 0.0330 | DEFAULT | D-1F-01: 0.15 x 0.20 (ST p.13 schedule) x (0.80 + 2 x 0.15 bearing default) = 0.0330 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0480 |
| L-7f9eb7cced8df33202a5 | LINTEL | HELD blank | 0.0720 | DEFAULT | W08: 0.20 x 0.20 (ST p.13 schedule) x (1.50 + 2 x 0.15 bearing default) = 0.0720 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (CB6 BM-GF-030 (20x75) over the drawn head +2.80); printed note 'MIN 40 cm' bearing would give 0.0920 |
| L-8f69c40749d579c14bf1 | LINTEL | HELD blank | 0.0520 | DEFAULT | L-GF-01: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-961608860fcb38c106af | LINTEL | HELD blank | IGNORED_SMALL 0.0360 | DEFAULT | D-1F-09: 0.15 x 0.20 (ST p.13 schedule) x (0.90 + 2 x 0.15 bearing default) = 0.0360 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0510 |
| L-9ec762c0bd529b924f33 | LINTEL | HELD blank | IGNORED_SMALL 0.0330 | DEFAULT | D-1F-06: 0.15 x 0.20 (ST p.13 schedule) x (0.80 + 2 x 0.15 bearing default) = 0.0330 m3; printed note 'MIN 40 cm' bearing would give 0.0480 |
| L-a500f10eedbd63a147ab | LINTEL | HELD blank | 0.0520 | DEFAULT | L-1F-01: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-b699ce0da6b29b888435 | LINTEL | HELD blank | 0.0600 | DEFAULT | W26: 0.20 x 0.20 (ST p.13 schedule) x (1.20 + 2 x 0.15 bearing default) = 0.0600 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (the 2F stair-roof piece over W26 (soffit 3.00)); printed note 'MIN 40 cm' bearing would give 0.0800 |
| L-b729bd6381f216153df8 | LINTEL | HELD blank | IGNORED_SMALL 0.0390 | DEFAULT | A-GF-01: 0.15 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0390 m3; existence default = one lintel per opening (owner lintel rule); arched head: straight-lintel equivalent (curved crown not printed, T-238); printed note 'MIN 40 cm' bearing would give 0.0540 |
| L-bf88bf6f5efaa0ae5bdc | LINTEL | HELD blank | 0.0520 | DEFAULT | W25: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-c1e57b06555adcf8edf7 | LINTEL | HELD blank | 0.0900 | DEFAULT | W11: 0.20 x 0.20 (ST p.13 schedule) x (1.95 + 2 x 0.15 bearing default) = 0.0900 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (B9 (0.75) over GF-W18); printed note 'MIN 40 cm' bearing would give 0.1100 |
| L-d887eecf51c121831336 | LINTEL | HELD blank | IGNORED_SMALL 0.0480 | DEFAULT | P-GF-01: 0.20 x 0.20 (ST p.13 schedule) x (0.90 + 2 x 0.15 bearing default) = 0.0480 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0680 |
| L-df32d6f42a824be21d3f | LINTEL | HELD blank | 0.0520 | DEFAULT | D-GF-05: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-e39175199fc6edc4db86 | LINTEL | HELD blank | 0.0900 | DEFAULT | W12: 0.20 x 0.20 (ST p.13 schedule) x (1.95 + 2 x 0.15 bearing default) = 0.0900 m3; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (B9 (0.75) over GF-W18); printed note 'MIN 40 cm' bearing would give 0.1100 |
| L-f892163c0602656f7e57 | LINTEL | HELD blank | 0.0520 | DEFAULT | W27: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-fd8aaedc3457d6648f18 | LINTEL | HELD blank | 0.0520 | DEFAULT | L-2F-01: 0.20 x 0.20 (ST p.13 schedule) x (1.00 + 2 x 0.15 bearing default) = 0.0520 m3; existence default = one lintel per opening (owner lintel rule); printed note 'MIN 40 cm' bearing would give 0.0720 |
| L-12f3d8b9375cac407bca | NECK | HELD blank | 0.2925 | DEFAULT | C1@213452,60528: route G base 0.2925 m3 (schedule section x neck from the printed minimum founding to the GB; register high 0.3675); lift raft level (D-43) replaces it |
| L-8eb74a02fcf5ae4465f8 | NECK | HELD blank | 0.2925 | DEFAULT | C2@213395,59220: route G base 0.2925 m3 (schedule section x neck from the printed minimum founding to the GB; register high 0.3675); lift raft level (D-43) replaces it |
| L-953e87a3e9d0425d404e | NECK | HELD blank | 0.5850 | DEFAULT | C9@214557,59222: route G base 0.5850 m3 (schedule section x neck from the printed minimum founding to the GB; register high 0.7350); lift raft level (D-43) replaces it |
| L-dd6d11415961b554e906 | NECK | HELD blank | 0.2925 | DEFAULT | C2@214579,60524: route G base 0.2925 m3 (schedule section x neck from the printed minimum founding to the GB; register high 0.3675); lift raft level (D-43) replaces it |
| L-030538dda6a32c601c4c | PARAPET | HELD blank | 3.6551 | DEFAULT | 2F_ROOF: sum of runs top m2 (T-319 / T-324 drawn) x (height above finish + roof build-up default 0.175) = 3.6551 m3 [NE-1 1.1850 x (0.500 printed + 0.175); NW-1 1.3250 x (0.500 printed + 0.175); SE-1 1.3250 x (0.500 printed + 0.175); SW-1 1.5800 x (0.500 printed + 0.175)]; all-RC above the slab top (P7757 sections A-A / B-B cut every parapet in RC = this villa's drawing; ST p.14 P1 'typical' alternative = RC 0.30 upstand 1.6245 m3 + block above; Q-65 C designer answer replaces it) |
| L-1d419b64e8ca1af30fb4 | PARAPET | HELD blank | 4.0480 | DEFAULT | ANNEX_ROOF: sum of runs top m2 (T-319 / T-324 drawn) x (height above finish + roof build-up default 0.175) = 4.0480 m3 [NE-6 2.1200 x (0.500 printed + 0.175); NE-6x 0.2600 x (0.500 printed + 0.175); NW-1 0.1200 x (0.500 printed + 0.175); SE-1 1.3000 x (0.500 printed + 0.175); SW-1 0.6000 x (0.500 printed + 0.175); SW-2 0.3770 x (0.500 printed + 0.175); SW-3 1.2200 x (0.500 printed + 0.175)]; all-RC above the slab top (P7757 sections A-A / B-B cut every parapet in RC = this villa's drawing; ST p.14 P1 'typical' alternative = RC 0.30 upstand 1.7991 m3 + block above; Q-65 C designer answer replaces it) |
| L-9a2c81164ec6499cc28c | PARAPET | HELD blank | 12.8892 | DEFAULT | 1F_ROOF: sum of runs top m2 (T-319 / T-324 drawn) x (height above finish + roof build-up default 0.175) = 12.8892 m3 [NE-1 0.0080 x (1.200 default 1.20 + 0.175); NE-2 3.8140 x (1.300 printed + 0.175); NW-1 0.2046 x (1.299 printed + 0.175); NW-2 0.6334 x (1.300 printed + 0.175); NW-3 0.1061 x (1.299 printed + 0.175); NW-4 0.0935 x (1.099 printed + 0.175); NW-5 1.3250 x (0.448 printed + 0.175); SE-1 1.4600 x (1.041 printed + 0.175); SW-1 0.0080 x (1.200 default 1.20 + 0.175); SW-2 0.8450 x (1.200 default 1.20 + 0.175); SW-3 1.3340 x (1.300 printed + 0.175)]; all-RC above the slab top (P7757 sections A-A / B-B cut every parapet in RC = this villa's drawing; ST p.14 P1 'typical' alternative = RC 0.30 upstand 2.9495 m3 + block above; Q-65 C designer answer replaces it) |
| L-b5ffc172a354375ca107 | PARAPET | HELD blank | 3.7752 | DEFAULT | GF_TERRACE: sum of runs top m2 (T-319 / T-324 drawn) x (height above finish + roof build-up default 0.175) = 3.7752 m3 [NE-4 3.8540 x (0.500 printed + 0.175); NW-7 1.5400 x (0.500 printed + 0.175); SW-9 0.1990 x (0.500 printed + 0.175)]; all-RC above the slab top (P7757 sections A-A / B-B cut every parapet in RC = this villa's drawing; ST p.14 P1 'typical' alternative = RC 0.30 upstand 1.6779 m3 + block above; Q-65 C designer answer replaces it) |
| L-b62a7065645589011141 | POOL | HELD blank | 0.2280 | SAFETY | pool steps not drawn (T-667 R-T667-5; consultant P-2): SAFETY block 0.30 x 2.00 x 0.38 = 0.228 m3 (one bench step across the 3.50 back wall, the size the reference workbook carries; never VERIFIED) |
| L-061e18cf35a4b6b33d68 | STAIR | HELD blank | 1.1274 | ESTIMATE | ST-03 E1: steps 0.3550 (T-258 / T-711) + waist 1.724 slope x 2.80 x 0.16 (ST-01 printed plate) = 1.1274 m3; S-9 / D-56 replaces the waist |
| L-659243ed9fc2831c3ae8 | STAIR | HELD blank | 0.0630 | DEFAULT | ST-01 MS2 turn riser: height 0.168 + 0.16 = 0.328 x thickness 0.16 (plate) x width 1.20 (turn 1.44 m2) = 0.0630 m3 (T-711 per-unit) |
| L-7863355dfcb68a681d2d | STAIR | HELD blank | 1.2134 | DEFAULT | ST-01 GF->1F remainder: reading A (27 equal risers 0.1667, within the 0.15-0.175 default) 0.8630 + winder wedges 1/2 x 0.1667 x 1.44 + flat turn 1.44 x 0.16 = 1.2134 m3 (T-711); reading B 1.4009 |
| L-821032bc04a0b0d02133 | STAIR | HELD blank | 0.1656 | ESTIMATE | ST-01b lobby D1 waist under 4 steps: plan 1.035 m2 (T-711) x 0.16 plate = 0.1656 m3 (if on compacted fill: 0) |
| L-b6b0354b7842f0ed6e41 | STAIR | HELD blank | 1.0879 | ESTIMATE | ST-02 round stair 12 curved treads: wedges 2.05385 m3/m x riser 4.50/28 = 0.3301 (T-711) + helicoid waist 4.1077 m2 x 0.16 x slope 1.153 = 0.7578; CA (0 .. 0.09) in SAFETY; D-08 replaces it |

SAFETY line NEW:STR.CONC.SAFETY = 1.00 m3 (ignored known pieces 0.4282 m3 on 13 lines < 1 m3 -> 1 m3 (owner materiality rule); covers also unread scraps named in bases (ST-02 CA 0 .. 0.09). T-757 may merge its own IGNORED_SMALL set into this ONE line (never two safety lines))

## Ranged lines kept (not changed by this row; designer item named, T-755 sweep)

| line | item | low .. high | designer item |
|---|---|---|---|
| L-005334b6998987164a5d | LINTEL | 0.04 .. 0.055 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-05a99150a85e9185ae48 | NECK | 0.235 .. 0.315 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-080c97f5f6a92452cd04 | BLINDING | 0.435 .. 0.59 | Q-31: owner question Q-31 (one outline, two footing tags) |
| L-0c5ede7fd2c9e425aa8d | GROUND_BEAM | 0.1125 .. 0.15 | D-34: ground-beam title by span: no precedence printed |
| L-0e852cca42fb8b765c58 | GROUND_BEAM | 0.216 .. 0.288 | D-34: ground-beam title by span: no precedence printed |
| L-10032bf9a60368473a7b | BLINDING | 0.0 .. 0.189 | D-14: blinding projection past the plot line |
| L-132cf60588a44f6af9d6 | NECK | 0.5874 .. 0.66 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-15b8ad39d6b2250c9546 | NECK | 0.4272 .. 0.54 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-15d9da9b17fd373553f0 | NECK | 0.0972 .. 0.18 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-164ae9d338976be9e582 | FOOTING | 2.176 .. 2.275 | Q-31: owner question Q-31 (one outline, two footing tags) |
| L-16b95607fc88cda3844a | BLINDING | 2.256 .. 2.352 | RFI-S08+RFI-S23: lift raft blinding projection (old RFI codes) |
| L-1a07849115af938b4a72 | LINTEL | 0.056 .. 0.066716 | Q-55: owner rule Q-55 C fallback door head (existence / spare) |
| L-1a9e469651c32cce9b97 | NECK | 0.1152 .. 0.198 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-1dc713c83bf62e525ff2 | COLUMN | 0.756 .. 0.84 | D-16: column C8: schedule section vs drawn outline differ |
| L-1fd49f3e7c5a7dd19d4d | BEAM | 2.262872 .. 2.545691 | D-27: beam width: schedule vs drawn differ |
| L-26f6b6f2365c72e42291 | COLUMN | 0.3287 .. 0.425 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-291ba2ddf4bbe4f14cf7 | COLUMN | 0.42 .. 0.504 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-2c7b0b1e1a439d9ffd1e | BEAM | 0.347 .. 0.4338 | D-27: beam width: schedule vs drawn differ |
| L-2efe48097978cae5fc99 | LINTEL | 0.063 .. 0.12042 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-314946394d849141dda2 | NECK | 0.267 .. 0.33 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-33a9b7728781fcba12e2 | COLUMN | 0.3267 .. 0.425 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-34346cb438bffee6acec | NECK | 0.1152 .. 0.198 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-35382b18e2e362df3ae6 | BLINDING | 0.0 .. 0.912684 | STRAP_BLINDING_NOT_PRINTED: strap blinding not printed |
| L-39ca5340879eafc35355 | BEAM | 0.44255 .. 0.55323 | D-27: beam width: schedule vs drawn differ |
| L-3af715c6e83364208ad0 | LINTEL | 0.08 .. 0.108 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-3f7b9501a902579e7406 | NECK | 0.2895 .. 0.3225 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-40e8c2597de12644e8e2 | LINTEL | 0.094 .. 0.26828 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-43dae3d6dfec957b26a8 | COLUMN | 0.36 .. 0.45 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-43e804ba4a4c07529fd5 | BEAM | 0.4563 .. 0.5475 | D-02: beam width: schedule vs drawn differ (CB10 kind) |
| L-441ae5fe85351347aff0 | LINTEL | 0.04 .. 0.055 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-46f2b70254f074885dfc | NECK | 0.282 .. 0.315 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-47882fa3a0d9cdcc122e | LINTEL | 0.08 .. 0.108 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-486cd9a0bf52e4b32abb | NECK | 0.3384 .. 0.378 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-48f2e06e5c946eb1e5a7 | NECK | 0.267 .. 0.3 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-4a12b89454e48ac510dc | LINTEL | 0.054 .. 0.1185 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-4aed92c117a7ab1c90ee | COLUMN | 0.756 .. 0.84 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-4c4496579e5bfa20ae9f | COLUMN | 0.9 .. 1.0125 | D-16: column C8: schedule section vs drawn outline differ |
| L-4ec473f7c0c712919823 | NECK | 0.192 .. 0.33 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-4ef35980fbb54366703d | NECK | 0.1062 .. 0.189 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-50667f69855b6d588011 | BEAM | 0.2875 .. 0.345 | D-02: beam width: schedule vs drawn differ (CB10 kind) |
| L-516989b817e0ccc7cb80 | NECK | 0.267 .. 0.3 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-53d0b6af1a801c3db58e | NECK | 0.192 .. 0.33 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-53ef44d8c490d1341b93 | LINTEL | 0.078 .. 0.081732 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-53f223b06db14ac41d47 | COLUMN | 0.45738 .. 0.595 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-541c7e565bb93ecdb78b | COLUMN | 0.20136 .. 0.35 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-5aec8a0055215ee5a711 | NECK | 0.2895 .. 0.3225 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-5efd9ac69d4cfd9b9a6e | NECK | 0.3384 .. 0.378 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-6057028f3f666538a007 | LINTEL | 0.056 .. 0.069 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-60f09eece6568b15f6ce | BEAM | 0.335 .. 0.4188 | D-27: beam width: schedule vs drawn differ |
| L-6290a9f3d93f38cd46d6 | BOUNDARY_WALL | 5.6392 .. 11.0328 | Q-28: owner question Q-28 (boundary band section / founding level) |
| L-6692d02cd6cd25120300 | LINTEL | 0.056 .. 0.08048 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-694a75c84dd6e4bb4491 | COLUMN | 0.26352 .. 0.50625 | D-39+D-66: column section conflict + roof slab top not printed |
| L-6a2040e0fe0bf7391b9c | NECK | 0.1152 .. 0.198 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-71998da6340be871d0af | LINTEL | 0.036 .. 0.042708 | Q-55: owner rule Q-55 C fallback door head (existence / spare) |
| L-734ff1a78bbe6b7eb4c3 | NECK | 0.192 .. 0.33 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-755eb56b55e86301b488 | COLUMN | 0.756 .. 1.05 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-786344670c0002b31478 | LINTEL | 0.092 .. 0.118 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-7a5214a334ea3559fa2d | BLINDING | 4.949374 .. 9.422514 | FOOTING_DETAIL_CHOICE_OPEN: footing blinding: governing detail choice open |
| L-7c3edce23ec8faa3d674 | BEAM | 0.112 .. 0.336 | D-04: unlabelled beam piece: no mark, depth row not printed |
| L-7d90a0feed2537221f16 | LINTEL | 0.0 .. 0.003 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-81444e222487437e257e | GROUND_BEAM | 0.1305 .. 0.174 | D-34: ground-beam title by span: no precedence printed |
| L-831f6fe3de133294bb8f | COLUMN | 0.42 .. 0.63 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-85809d3db52bb93dfe96 | COLUMN | 0.672 .. 0.84 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-85df35f17a205f919aa6 | NECK | 0.192 .. 0.33 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-882717b0c35a87e363ef | LINTEL | 0.056 .. 0.06 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-88ccf8d4505411deb9e5 | BEAM | 0.212 .. 0.3975 | D-03: two marks on one beam |
| L-8d031491396379f0cbb1 | BEAM | 0.0904 .. 0.2712 | D-04: unlabelled beam piece: no mark, depth row not printed |
| L-8de64040a1c3ae6cf137 | COLUMN | 0.45 .. 0.5625 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-8f8ad257d9b2cb9e027f | COLUMN | 0.42 .. 0.525 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-919a5749ef79759e01ca | COLUMN | 0.3287 .. 0.425 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-970bac563cbcd69e2a30 | GROUND_BEAM | 0.098008 .. 0.130678 | D-34: ground-beam title by span: no precedence printed |
| L-995eca94ba8dc09a028f | NECK | 0.3792 .. 0.432 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-9cb26d86575a92694880 | COLUMN | 0.36 .. 0.45 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-9e4895663f76d7f03ac9 | BEAM | 1.013607 .. 1.266989 | D-27: beam width: schedule vs drawn differ |
| L-9f5a647014bbf83359f9 | COLUMN | 0.26352 .. 0.405 | D-39+D-66: column section conflict + roof slab top not printed |
| L-a7848a35fb4329e09d10 | LINTEL | 0.052 .. 0.058 | Q-55: owner rule Q-55 C fallback door head (existence / spare) |
| L-a7b8b292503ae1bf6c77 | LINTEL | 0.036 .. 0.0628 | Q-55: owner rule Q-55 C fallback door head (existence / spare) |
| L-a87ea657a42a311cb851 | COLUMN | 0.504 .. 0.735 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-abd65e1b745315dd17c2 | STRAP | 0.0 .. 0.385 | Q-31: owner question Q-31 (one outline, two footing tags) |
| L-aca2db3c2b29719328c7 | LINTEL | 0.064 .. 0.064 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-ae1bd9cb228d57594e46 | NECK | 0.237 .. 0.27 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-b21cbf6560f613b39bf0 | NECK | 0.519 .. 0.585 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-b4c234c8a3873239f67f | NECK | 0.5874 .. 0.66 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-bbad8cdb4d26986776a6 | NECK | 0.3738 .. 0.462 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-bc01297b1c4a4c45a15f | COLUMN | 0.3287 .. 0.51 | D-39+D-66: column section conflict + roof slab top not printed |
| L-bd741a3faf2318dd8409 | NECK | 0.2376 .. 0.33 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-bef35462630d4b76596f | BEAM | 0.0 .. 0.025 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-bf76c17309c92605e174 | LINTEL | 0.056 .. 0.134 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-c0b3340a906c2c7650f8 | COLUMN | 0.26352 .. 0.405 | D-39+D-66: column section conflict + roof slab top not printed |
| L-c0b7102a36344a0349f5 | GROUND_BEAM | 0.20925 .. 0.279 | D-34: ground-beam title by span: no precedence printed |
| L-c1e802184591eac927cf | NECK | 0.1944 .. 0.36 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-c677b628a776d3b87b02 | COLUMN | 0.42 .. 0.63 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-c823e0dbd81e30c66aa5 | STRAP | 0.0295 .. 0.2683 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-c8c07db4ac0d54d89bbf | NECK | 0.1152 .. 0.198 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-cc702b8541c15fdfd98c | COLUMN | 0.42 .. 0.525 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-d62d2fcf3d0023ad1ad1 | BEAM | 0.248 .. 0.744 | D-04: unlabelled beam piece: no mark, depth row not printed |
| L-d79d17d14f39d5148cb8 | COLUMN | 0.3287 .. 0.425 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-dc8cbfc119d006ff3927 | BEAM | 0.112 .. 0.336 | D-04: unlabelled beam piece: no mark, depth row not printed |
| L-dd3c32e4340e7a823a6e | NECK | 0.177 .. 0.315 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-dd5b41a7af885e96f797 | LINTEL | 0.04 .. 0.055 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-e112e2add2f8979a6c39 | COLUMN | 0.42 .. 0.525 | D-66: column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2) |
| L-e2134034441cb7db7bd7 | GROUND_BEAM | 0.108 .. 0.144 | D-34: ground-beam title by span: no precedence printed |
| L-e6c1c9a7feec10f64975 | COLUMN | 0.26352 .. 0.405 | D-39+D-66: column section conflict + roof slab top not printed |
| L-ed7aadd01d9daa9559a9 | LINTEL | 0.056 .. 0.134 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-efe50185c0da4244e158 | NECK | 0.3738 .. 0.42 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-f0e25ad2cf73bf2a35ea | GROUND_BEAM | 0.108 .. 0.144 | D-34: ground-beam title by span: no precedence printed |
| L-f24cf117a9ce1e875785 | GROUND_BEAM | 0.19612 .. 0.261493 | D-34: ground-beam title by span: no precedence printed |
| L-f269fabb74f505755492 | LINTEL | 0.04 .. 0.04 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-f54b7b2acf11ebd2a585 | NECK | 0.192 .. 0.33 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-f68444edf483bc1d87d4 | LINTEL | 0.04 .. 0.04 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
| L-f83c4a469845c7e14dfa | BEAM | 0.064 .. 0.192 | D-04: unlabelled beam piece: no mark, depth row not printed |
| L-fad18af6e7139a5e99d1 | COLUMN | 0.41175 .. 0.50625 | D-39: roof slab top not printed (finished marks only); parapet build-up / height |
| L-fc622ff340ac65a544e3 | NECK | 0.4806 .. 0.54 | NO_SINGLE_VALUE: neck: founding level not printed (minimum 1.50 m below EG only) |
| L-fd68db051119ea0266ee | LINTEL | 0.096 .. 0.108 | DESIGNER_TAG: named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding) |
