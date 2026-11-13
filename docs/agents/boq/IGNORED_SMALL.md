# IGNORED_SMALL: concrete pieces known to be below 0.05 m3 (owner materiality rule 2026-11-13 14:00)

Rule (DELIVERY_MODE s.3): a concrete piece KNOWN to be < 0.05 m3 is ignored and logged here by line id; the ONE safety
line STR.CONC.SAFETY = 1 m3 if the ignored sum is below 1 m3, else the sum. The rule file and its test belong to T-757;
rows that apply it append here. Sizes are the DEFAULT figures of the source fix-row set (never VERIFIED).

| line | item | element | size m3 | basis | source |
|---|---|---|---|---|---|
| L-89d266a3e5280a10a3b9 | STR.CONC.BEAM | 1F-NW-CORNER strip piece | 0.0176 | 0.029309 m2 x 0.60 default | T-761 |
| L-e296002577c012f0afd4 | STR.CONC.BEAM | GF-NW-CORNER strip piece | 0.0176 | 0.029309 m2 x 0.60 default | T-761 |
| L-b4a13a43967ee4765662 | STR.CONC.GROUND_BEAM | BAND0017.2 | 0.0450 | 0.15 m2 x 0.30 class depth | T-761 |
| L-be6708e07b40efa02779 | STR.CONC.GROUND_BEAM | BAND0013.1 | 0.0090 | 0.03 m2 x 0.30 class depth | T-761 |
| L-1313767d897f06ef95b6 | STR.CONC.LINTEL | W04 | 0.0360 | 0.20 x 0.20 x (0.60 + 0.30) | T-761 |
| L-17953d7882899d43473f | STR.CONC.LINTEL | D-GF-14 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-1c0e7646345156fcd0cb | STR.CONC.LINTEL | D-2F-02 | 0.0480 | 0.20 x 0.20 x (0.90 + 0.30) | T-761 |
| L-274b112580029084b80e | STR.CONC.LINTEL | D-GF-04 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-2c1c49db7cd7b16c6206 | STR.CONC.LINTEL | D-1F-01 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-961608860fcb38c106af | STR.CONC.LINTEL | D-1F-09 | 0.0360 | 0.15 x 0.20 x (0.90 + 0.30) | T-761 |
| L-9ec762c0bd529b924f33 | STR.CONC.LINTEL | D-1F-06 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-b729bd6381f216153df8 | STR.CONC.LINTEL | A-GF-01 | 0.0390 | 0.15 x 0.20 x (1.00 + 0.30) | T-761 |
| L-d887eecf51c121831336 | STR.CONC.LINTEL | P-GF-01 | 0.0480 | 0.20 x 0.20 x (0.90 + 0.30) | T-761 |

Sum T-761: 0.4282 m3 on 13 lines (< 1 m3) -> STR.CONC.SAFETY 1.00 m3 (SAFETY), proposed in
research/agents_t761/out/FIX_ROWS.json on agents/task-T-761. T-757 adds the bounded small ranges to this same table and
keeps ONE safety line.

T-757 additions (2026-11-13, ranged lines with width < 0.05 m3: the line takes its LOW bound; the logged size is the WIDTH
of the unresolved part; agents/task-T-757 research/agents_t757/out/FIX_ROWS.json):

| line | item | element | size m3 (width) | basis | source |
|---|---|---|---|---|---|
| L-bef35462630d4b76596f | STR.CONC.BEAM | U-C:BEAMS:GF:BAND0030.2~T642_DEPTH_B4_B7 | 0.0250 | low 0.0 .. high 0.025; cause DESIGNER_TAG | T-757 |
| L-81444e222487437e257e | STR.CONC.GROUND_BEAM | P-C:GROUND_BEAMS:GROUND:BAND0020 | 0.0435 | low 0.1305 .. high 0.174; cause D-34 | T-757 |
| L-e2134034441cb7db7bd7 | STR.CONC.GROUND_BEAM | P-C:GROUND_BEAMS:GROUND:BAND0021 | 0.0360 | low 0.108 .. high 0.144; cause D-34 | T-757 |
| L-f0e25ad2cf73bf2a35ea | STR.CONC.GROUND_BEAM | P-C:GROUND_BEAMS:GROUND:BAND0030 | 0.0360 | low 0.108 .. high 0.144; cause D-34 | T-757 |
| L-0c5ede7fd2c9e425aa8d | STR.CONC.GROUND_BEAM | P-C:GROUND_BEAMS:GROUND:BAND0034 | 0.0375 | low 0.1125 .. high 0.15; cause D-34 | T-757 |
| L-970bac563cbcd69e2a30 | STR.CONC.GROUND_BEAM | P-C:GROUND_BEAMS:GROUND:BAND0038 | 0.0327 | low 0.098008 .. high 0.130678; cause D-34 | T-757 |
| L-a7b8b292503ae1bf6c77 | STR.CONC.LINTEL | LINTEL:D-1F-05 | 0.0268 | low 0.036 .. high 0.0628; cause Q-55 | T-757 |
| L-1a07849115af938b4a72 | STR.CONC.LINTEL | LINTEL:D-GF-01 | 0.0107 | low 0.056 .. high 0.066716; cause Q-55 | T-757 |
| L-71998da6340be871d0af | STR.CONC.LINTEL | LINTEL:D-GF-02 | 0.0067 | low 0.036 .. high 0.042708; cause Q-55 | T-757 |
| L-a7848a35fb4329e09d10 | STR.CONC.LINTEL | LINTEL:D-GF-03 | 0.0060 | low 0.052 .. high 0.058; cause Q-55 | T-757 |
| L-fd68db051119ea0266ee | STR.CONC.LINTEL | LINTEL:D-GF-07 | 0.0120 | low 0.096 .. high 0.108; cause DESIGNER_TAG | T-757 |
| L-3af715c6e83364208ad0 | STR.CONC.LINTEL | LINTEL:W01 | 0.0280 | low 0.08 .. high 0.108; cause DESIGNER_TAG | T-757 |
| L-441ae5fe85351347aff0 | STR.CONC.LINTEL | LINTEL:W05 | 0.0150 | low 0.04 .. high 0.055; cause DESIGNER_TAG | T-757 |
| L-f269fabb74f505755492 | STR.CONC.LINTEL | LINTEL:W06 | 0.0000 | low 0.04 .. high 0.04; cause DESIGNER_TAG | T-757 |
| L-786344670c0002b31478 | STR.CONC.LINTEL | LINTEL:W09 | 0.0260 | low 0.092 .. high 0.118; cause DESIGNER_TAG | T-757 |
| L-882717b0c35a87e363ef | STR.CONC.LINTEL | LINTEL:W10 | 0.0040 | low 0.056 .. high 0.06; cause DESIGNER_TAG | T-757 |
| L-47882fa3a0d9cdcc122e | STR.CONC.LINTEL | LINTEL:W13 | 0.0280 | low 0.08 .. high 0.108; cause DESIGNER_TAG | T-757 |
| L-53ef44d8c490d1341b93 | STR.CONC.LINTEL | LINTEL:W16 | 0.0037 | low 0.078 .. high 0.081732; cause DESIGNER_TAG | T-757 |
| L-6057028f3f666538a007 | STR.CONC.LINTEL | LINTEL:W19 | 0.0130 | low 0.056 .. high 0.069; cause DESIGNER_TAG | T-757 |
| L-7d90a0feed2537221f16 | STR.CONC.LINTEL | LINTEL:W19+W20:PIER_REMAINDER | 0.0030 | low 0.0 .. high 0.003; cause DESIGNER_TAG | T-757 |
| L-6692d02cd6cd25120300 | STR.CONC.LINTEL | LINTEL:W20 | 0.0245 | low 0.056 .. high 0.08048; cause DESIGNER_TAG | T-757 |
| L-dd5b41a7af885e96f797 | STR.CONC.LINTEL | LINTEL:W21 | 0.0150 | low 0.04 .. high 0.055; cause DESIGNER_TAG | T-757 |
| L-f68444edf483bc1d87d4 | STR.CONC.LINTEL | LINTEL:W22 | 0.0000 | low 0.04 .. high 0.04; cause DESIGNER_TAG | T-757 |
| L-005334b6998987164a5d | STR.CONC.LINTEL | LINTEL:W28 | 0.0150 | low 0.04 .. high 0.055; cause DESIGNER_TAG | T-757 |
| L-aca2db3c2b29719328c7 | STR.CONC.LINTEL | LINTEL:W29 | 0.0000 | low 0.064 .. high 0.064; cause DESIGNER_TAG | T-757 |
| L-3f7b9501a902579e7406 | STR.CONC.NECK | P-C:NECK:COL:SH10:C2@209843,64560 | 0.0330 | low 0.2895 .. high 0.3225; cause NO_SINGLE_VALUE | T-757 |
| L-5aec8a0055215ee5a711 | STR.CONC.NECK | P-C:NECK:COL:SH10:C2@212578,64533 | 0.0330 | low 0.2895 .. high 0.3225; cause NO_SINGLE_VALUE | T-757 |
| L-ae1bd9cb228d57594e46 | STR.CONC.NECK | P-C:NECK:COL:SH10:C3@209914,60584 | 0.0330 | low 0.237 .. high 0.27; cause NO_SINGLE_VALUE | T-757 |
| L-516989b817e0ccc7cb80 | STR.CONC.NECK | P-C:NECK:COL:SH10:C3@217138,51213 | 0.0330 | low 0.267 .. high 0.3; cause NO_SINGLE_VALUE | T-757 |
| L-48f2e06e5c946eb1e5a7 | STR.CONC.NECK | P-C:NECK:COL:SH10:C3@226007,58025 | 0.0330 | low 0.267 .. high 0.3; cause NO_SINGLE_VALUE | T-757 |
| L-46f2b70254f074885dfc | STR.CONC.NECK | P-C:NECK:COL:SH10:C4@220308,64637 | 0.0330 | low 0.282 .. high 0.315; cause NO_SINGLE_VALUE | T-757 |
| L-5efd9ac69d4cfd9b9a6e | STR.CONC.NECK | P-C:NECK:COL:SH10:C5@216447,64629 | 0.0396 | low 0.3384 .. high 0.378; cause NO_SINGLE_VALUE | T-757 |
| L-486cd9a0bf52e4b32abb | STR.CONC.NECK | P-C:NECK:COL:SH10:C5@220440,52886 | 0.0396 | low 0.3384 .. high 0.378; cause NO_SINGLE_VALUE | T-757 |
| L-efe50185c0da4244e158 | STR.CONC.NECK | P-C:NECK:COL:SH10:C6@209970,56575 | 0.0462 | low 0.3738 .. high 0.42; cause NO_SINGLE_VALUE | T-757 |

Sum T-757: 0.7715 m3 on 34 lines. Register total 1.1997 m3 (T-761 0.4282 + T-757) >= 1 m3 ->
ONE line STR.CONC.SAFETY restated 1.00 -> 1.1997 m3 (SAFETY; max(1.00, sum); never a second safety line).
