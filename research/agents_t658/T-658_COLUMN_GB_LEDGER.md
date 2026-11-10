# T-658: B10-06 column, B10-04 ground beam / strap, B10-02 footing HELD lines (research, unwired)

Candidate ARCH_TAKEOFF_V3.0.61 / trial BOQ r4 (T-654). 61 HELD m3 lines, each once in `out/T658_LEDGER.json`
(`python -I research/agents_t658/t658_alsenan.py`). Rules R-T658-1 .. 8 in `t658_rules.py`. Nothing wired, nothing
released; inputs are sha-pinned committed files, the printed facts listed in `READS`, and (r2) the drawn plan areas in
`out/T658_BAND_AREAS.json`, measured by `t658_measure_bands.py <decoded ST dxf>` on 'ST7757 dxf.dxf' sha 9f9d1179
(the Checker's file; areas, widths and edge lengths only, no coordinate tracked).

| item | before (trial r4) | after r2 (T-658 ledger) |
|---|---|---|
| STR.CONC.GROUND_BEAM (29) | 14 bounded 2.808073 .. 6.621731; 15 blank | 9 bounded 1.173410 .. 5.096771; 16 LOWER_ONLY floor 5.069839 (8 annex D-35 2.227973 + 8 D-33 2.841866); 4 blank |
| STR.CONC.COLUMN (29) | 15 bounded 8.034 .. 10.119; 14 blank | 15 bounded 8.034 .. 10.119 (unchanged); 6 UPPER_ONLY ceiling 2.80125; 8 blank |
| STR.CONC.STRAP (2) | 0.0295 .. 0.6533 | unchanged (Q-74 checked: both are in-footing pieces) |
| STR.CONC.FOOTING (1) | 1.96 .. 2.275 | unchanged (R-T595-2) |

## r2 corrections (Checker r1 REJECTED, gates e + h)

(1) Oblique bands (R-T658-7). r1 multiplied the census span (the short edge) of an oblique band. Every run of the 61 was
checked on the drawing: 4 are not rectangles; all others are orthogonal (7 controls measured: area = span x 0.30 exactly)
or annex arcs carried on the centreline (exact for an annulus).

| run | drawn outline | area m2 | r1 m3 | r2 m3 |
|---|---|---|---|---|
| BAND0038 180+181 (45 deg) | face 176 -> face 180D; edge 181 drawn open 0.078 m short of 180D: two readings | 0.310134 (as drawn) / 0.326694 (to face) | 0.071008 .. 0.094676 | 0.093040 .. 0.130678 |
| BAND0039 182+183 (45 deg) | face corner 7C8 / 7C3 (corner piece 0.021280 m2 owned once) -> face 17E | 0.653733 | 0.186592 .. 0.248788 | 0.196120 .. 0.261493 |
| BAND0037.1 17E+17F (45 deg, D-33) | face 7E6 -> column 1EF netted | 0.807695 | 0.218423 .. 0.291231 | LOWER_ONLY 0.242309 |
| BAND0008.2 177+7CD #2 (D-33) | column 245 -> outer face R 2.55 of the curved band | 0.492189 | 0.1383 point | LOWER_ONLY 0.147657 |

Against the Checker's own r1 outlines (BAND0038 0.309944, BAND0039 0.631972 m2): both new highs bound them (0.130678 >=
0.123978; 0.261493 >= 0.252789). Residuals named: BAND0039 +0.021280 m2 = the corner triangle enclosed by faces 7C8 / 7C3
(no line closes it; the adjacent bands stop at those faces, so it is owned here once) + 0.000481 not explained;
BAND0038 as-drawn 0.310134 vs 0.309944 (0.000190 m2, 0.06 %, outline closure at the open end).

(2) D-33 ruling (R-T658-8): every run carrying a landing beam is LOWER_ONLY, low = drawn area x the least title that holds
(adjacent pair on a limit), least over the span readings, high not established: BAND0010.3 0.9 point -> 0.600 (5.00 m
ON_LIMIT, 30x40); BAND0008.1 blank -> 0.5964 (4.97 m reading, 30x40); BAND0008.2 0.147657; BAND0040 0.189; the two T-430
landing runs 7DC+7DD #1 and 7E7+7E8 #2 blank -> 0.4230 each (3.525 m, 30x40); and, by the same census tee, BAND0037.1
(182+183 lands on face 17E, drawn) and BAND0019 (141+7DA lands on face 142, drawn). The Checker's list named six; the
last two carry the same D-33 condition in the T-426 census and on the drawing (flagged for the Checker).

(3) Columns: marks re-read from the drawings this run. Arch sheet 10 SECTION A-A prints +/-0.00, +1.00, +5.50, +9.70,
+13.90 (storeys 450 / 420 / 420, parapet 50); arch sheet 9 NORTH EAST ELEVATION prints the annex +0.30 floor and +4.30
roof (storey 400). +13.90 and +4.30 AGREE. The bases +9.65 / +0.25 are NOT printed text on either set (ST dxf LEVEL layer
prints +0.15 / +0.30 / +1.00 and +9.70): they are the APPROVED structural datums of the facts register (DESIGNER),
= printed finished level - 0.05 and consistent with the printed storeys. Ceilings kept, provenance stated (F-T658-6).

Accepted in r1, kept: F-T658-1 short orthogonal spans 30x30 .. 30x40; F-T658-4 annex floors 2.227973.
Still blank: 3 court beams (no printed section), 1 neck-cut 0.10 m sliver (D-35, ownership open).

Lesson proposal (ERS s.7): a held line carried as a point while a second printed title also holds is a picked end
(R-T658-1); an oblique band measured on one edge understates its plan area: a held GB bound = drawn outline area x
depth (R-T658-7); a loaded run's unloaded titles are a floor, never a high (R-T658-8). Every villa.
