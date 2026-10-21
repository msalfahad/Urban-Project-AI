# T-155 Footing bars printed "per metre": what the drawings say, and the count under each reading (lane S evidence for Q-71)

Worker 3, 2026-10-21. Research only, NO REPO CODE: nothing in `engine/` changes, no quantity is released, no option is
chosen. Generic tool `t155_footing_notation.py` (synthetic fixture in `--check`); the project's schedule cells, the
per-row counts and the CSV stay in the private folder (`.work/private`, never committed), as the repository is public.
Drawings are referred to by their Drive folder and title only: Drive "Alsenan chalet project", `ST7757.pdf` (structural
set, 16 pages) and `ST7757 dxf.dxf`.

Session note: the session setup printed `AGENT_ENV FAIL: origin is not msalfahad/Urban-Project-AI:
https://github.com/msalfahad/urban-project-ai`, so the wrapper self-check (venv, codemap check, t061, freeze) did not
run. This task changes no engine file; the only code is the stand-alone research tool, run with the system python.

## 1. Footing types and where they are drawn

| Item | Where printed |
|---|---|
| Footing schedule, 17 rows: 12 single-layer rows with a printed COUNT (`n ø d`), 5 two-layer rows (TOP / BOT) printed PER METRE (`n ø d/m`): F8, F12, F13, F14, FF | `ST7757.pdf` p.9 "Schedule of Footings"; the DXF holds the same cells as INSERT attributes of blocks `FT` (single-layer) and `FTB` (two-layer); all cells of the 5 rows agree DXF vs PDF by eye |
| Size unit cm, columns L / W / H, then SHORT BARS / LONG BARS | p.9 header "FOOTING SIZE (cm)" |
| Each of the 5 marks occurs once on the foundation plan; plan outline equals the schedule L x W for all 5 (layer S-FOOTINGS, closed 4-vertex outlines, axis-aligned, plan in mm) | p.2 foundation plan / DXF |
| Cover 7 cm "not less than", concrete against soil (2.5 cm in columns, slabs, beams) | p.8 general note 22 |
| Bottom bars straight, short bars drawn as the dots of a section along L, long bars as the line; a bar dot at both ends of the section | p.13 "TYP. DETAIL OF ISOLATED FOOTING" (two variants) |
| Both typical details also draw a bar labelled **"Boxed bars."**: it runs along the top of the footing just under the top face and turns down at BOTH edges, its legs running down the side faces to the level of the bottom mesh (closed cage outline); no dimension is printed for its run, its legs, its count or its diameter | p.13, both variants (the "WITH OUT BASEMENT, level difference more than 2.5 m" one on the left and the plain one on the right) |
| The schedule has a **BOXED** column between LONG BARS and REMARKS. Single-layer (count) rows print `3+n` there (`3+4`, `3+5`, `3+6`, `3+8`), with no diameter glyph and no unit; FN's cell is blank; in the 5 two-layer rows the BOXED column holds the layer labels `TOP` / `BOT`, not a count | p.9; DXF blocks `FT` (attribute BOXED, template default `3+-`) and `FTB` (attributes BOXED-T / BOXED-B = TOP / BOT), as already recorded in research/source_recovery_delta (E-DXF-01) |
| A closed-cage section symbol is drawn in the REMARKS column for **F12, F13, F14 and FF** (not for F8): a closed rectangle with 4 bar dots along its top and 4 along its bottom, i.e. top and bottom layers joined at both edges. It is a schematic (the same 4 + 4 dots in all four rows, whatever the printed rates), not a bar count. FF's remark adds "قاعدة مصعد" (lift footing) | p.9; DXF layer S-REIN.D, 4 closed 4-vertex LWPOLYLINEs + 8 hatched dots each, inside the REMARKS column (x between its two border lines), one per row F12 / F13 / F14 / FF; none in the F8 row |
| FF is the lift footing; it also has its own full section: top and bottom bars joined by vertical legs at both edges, edge bars at all four corners, "AS PER SCH." | p.14 "DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)" |
| Two-layer footings drawn closed: F12, F13, F14 (p.9 symbol) and FF (p.9 symbol + p.14 section). **F8** is the only two-layer row with no box symbol and no own section; whether the p.13 "Boxed bars" detail applies to its top layer is not printed | pages 1-16 checked (r2 correction: the first issue said "no two-layer section anywhere" for F8 / F12 / F13 / F14 and "FF the only two-layer footing drawn", which is wrong for F12 / F13 / F14) |

## 2. Callouts as printed

Every cell of the 5 rows is `n ø d/m` in both directions and both layers (20 cells): TOP rates 6, 7 or 10 per metre
with ø14; BOT rates 8 or 9 per metre with ø14 or ø16. The exact cell text per footing is in the private CSV and on
p.9; Q-71 quotes the F8 cells.

## 3. What the notation means, from the drawings

1. **Rate per metre, not a total count: DRAWING-CONFIRMED (by contrast, no printed legend).** The same set prints three
   different notations side by side: a count `n ø d` (the 12 single-layer footing rows, the column schedule), a
   spacing with a printed length unit `ø d/s cm` (ground-beam links `ø8/15cm` p.13, the dome `ø12MM/15cm`, the pool
   detail `ø12/20cm`, beam side bars `2ø12/30cm`), and `n ø d/m` (the 5 footings, most slab-plan callouts, column ties
   "ST. OF COLUMN- 6ø8/m" p.9, lintel stirrups `5 ø8/M` in the lintel schedule p.13, lift-pit walls `6ø12/m` p.14).
   Since the spacing notation always carries "cm", `/m` is a number of bars per metre run (rate r, spacing 1/r).
2. **A total count is contradicted by the schedule itself.** The 12 count-printed footings carry 5.0 .. 10.0 bars per
   metre of the side they are spread along (9 of the 12 rows 8.0 .. 10.0). Read as a total, "9 ø 14/m" on a 4.00 m side would be
   2.25 bars per metre, about four times sparser than the smaller count-printed footings beside it.
3. **How the rate becomes whole bars across a footing is NOT printed: UNKNOWN.** No legend, note or dimension string
   says whether the rate is laid inside the covers or over the full side, or whether an edge bar is added. The
   typical details draw a bar at both ends of the section, but undimensioned, and both whole-bar readings below put a
   bar at both edges, so the details do not decide. Both readings are kept with their evidence.
4. **A drawing fact that bears on it (no recommendation from totals):** with a bar at each edge, the spacing a count
   gives is (inside side) / (count - 1). Under R1 that spacing is WIDER than the printed 1/r in 20 of 20 cells
   (example F8 bottom short: 11.35 cm against 100/9 = 11.11 cm), i.e. fewer bars per metre than printed. Under R2 it
   is at or below 1/r in 20 of 20 cells. R3 is not a whole number of bars in 15 of 20 cells.
5. **Bar ends (r2, for Q-71's "top layer waits on a designer detail"): what is drawn and what is not.**
   - Drawn: the closed-cage symbol on p.9 for F12, F13, F14 and FF says their top and bottom layers are joined at both
     edges; the p.13 "Boxed bars" callout draws such a bar turned down at both edges to the bottom mesh; FF has the full
     p.14 section with legs. So for these four the top-bar ends are NOT "not drawn": they are drawn as turned-down legs.
   - Not printed: the leg length (no dimension on p.9, p.13 or p.14; geometrically the legs would follow the footing
     depth H less covers, but that is a reading, not a printed dimension), any lap, whether the legs belong to the top
     bars or to separate U bars, and whether the bottom bars turn up. Leg steel stays HELD.
   - F8: no symbol, no own section; its top-bar ends remain undrawn. HELD.
   - The `3+n` cells of the single-layer rows: no legend, note or section defines them (no diameter, no unit; the
     typical detail does not label a count). Neither "3 bars + n bars", nor a bar mark, nor a count per edge is
     printed, so the meaning of `3+n` is UNKNOWN and the boxed bars of those 12 footings are HELD (they are not part
     of this task's five rows; research/pre_s8_structural_completeness already lists BOXED as BLOCKED_SEMANTICS and warns of a possible double count
     with the column starters if it is ever released as starter bars).
   None of this changes the straight-core counts of section 4 or the mapping to A / B / C: it bears only on the
   bar-end steel that Q-71 already says is held whatever the owner answers.

## 4. Count per footing and direction (method; numbers in the private CSV)

Bar length = the other side - 2 x 0.07 m (note 22; no assumed cover). Short bars (length W - 0.14) are spread along
L, long bars (length L - 0.14) along W. kg/m = d^2/162. Readings: R1 = ceil(r x (side - 0.14)); R2 = R1 + 1; R3 = r x
side (fractional). Top-layer bar ends (r2 corrected, section 3.5): F12, F13, F14 and FF drawn closed, turned down at
both edges (p.9 symbol, p.13 "Boxed bars", p.14 for FF), leg / lap length not dimensioned: straight core counted, legs
HELD; F8 ends not drawn: straight core counted, ends HELD.

Totals, all five footings, one occurrence each (kg, net, straight bars):

| Reading | Bottom layer | Top layer (core) | Both | Status |
|---|---|---|---|---|
| R1 inside covers, rounded up | 1,606.07 | 1,136.44 | **2,742.51** | HELD (Q-71) |
| R2 R1 + 1 edge bar | 1,655.56 | 1,180.84 | **2,836.40** | HELD (Q-71) |
| R3 rate x full side, fractional | 1,635.65 | 1,162.16 | **2,797.81** | HELD (Q-71) |

Per footing (R1 .. R2, R3): F8 494.50 .. 512.21 (503.36); F12 696.05 .. 716.47 (713.19); F13 408.89 .. 426.80
(415.93); F14 422.83 .. 439.33 (437.12); FF 720.24 .. 741.58 (728.21).

## 5. Mapping to Q-71 (done last)

R1 reproduces option A (2,742.51 kg) exactly, R2 option B (2,836.40 kg) and R3 option C (2,797.81 kg), each to 0.01
kg and per footing, from an independent read of the schedule (DXF attributes + PDF) and the plan. No reading outside
A / B / C is supported by the drawings: a "total count" reading is contradicted (3.2), and nothing printed supports a
different cover or a different side. The drawing evidence settles WHAT `/m` means (a rate); it does not settle HOW
the rate is turned into a whole count, which stays the owner's rule (Q-71). Section 3.4 is the drawing fact to put
beside the options. Freelancer: one 5.8 t kg/m3 allowance for all footings, straps and the perimeter beam (T-136), so
no like-for-like comparison exists for these five rows.

## 6. Synthetic fixture (`--check`, not any real villa), hand calculations

kg/m: ø10 0.617284, ø12 0.888889, ø14 1.209877, ø16 1.580247; cover 0.07 m in every case.

| Case | Hand calculation | R1 / R2 / R3 kg |
|---|---|---|
| Square 2.00 x 2.00, `8 ø 12/m` both ways | inside 1.86; 8 x 1.86 = 14.88 -> 15 / 16 / 16.0 bars of 1.86 m per direction; spacing R1 1.86/14 = 13.29 cm > 12.5, R2 1.86/15 = 12.40 cm | 49.6000 / 52.9067 / 52.9067 |
| Rectangle 3.00 x 1.50, `ø 14 @ 15 cm` (also `ø 14/15cm`, rotated 1.50 x 3.00, in cm, in mm `@ 150 mm`) | short: 2.86/0.15 = 19.07 -> 20 / 21 / 20.0 bars of 1.36 m; long: 1.36/0.15 = 9.07 -> 10 / 11 / 10.0 bars of 2.86 m; 55.8 / 60.02 / 55.8 m | 67.5111 / 72.6168 / 67.5111 |
| Combined 5.00 x 2.00, TOP `6 ø 16/m`, BOT `10 ø 16/m` | TOP short 6 x 4.86 = 29.16 -> 30, long 6 x 1.86 = 11.16 -> 12; BOT short 48.6 -> 49, long 18.6 -> 19; R1 297.60 m, R2 311.04 m, R3 304.32 m | 470.2815 / 491.5200 / 480.9007 |
| Exact multiple 1.54 x 1.54, `5 ø 10/m` | 5 x 1.40 = 7.0 exactly -> 7 / 8 / 7.7 bars of 1.40 m | 12.0988 / 13.8272 / 13.3086 |
| Count `18 ø 12` / `17 ø 12` on 2.20 x 2.00 | never re-counted: 18 x 1.86 + 17 x 2.06 = 68.50 m | 60.8889 (all readings) |
| No cover; `ø 14/m` (no count); `ø 14 @ 15` (no unit); empty cell | HELD / UNKNOWN, footing total None (never 0) | None |

## 7. For the Checker (Gate A) and the Lead

Re-count two types from p.9 (suggest F12 bottom, ø16, the largest steel, and F13 top, the narrowest footing) and
re-read the notation evidence in section 3 (p.9 column-tie note, p.13 lintel schedule and ground-beam sections, p.14
lift detail). To re-run: write the input JSON described in the tool's docstring from p.9 into the private folder and
run `python3 -I research/agents_t155/t155_footing_notation.py --input <that file>`. Then the Lead updates Q-71 with
the verified evidence: `/m` = bars per metre (drawing-confirmed by contrast), whole-count rule not printed, the
three readings reproduce A / B / C, and the spacing fact of section 3.4.

Learned: the same `/m` question decides the column ties, lintel stirrups, slab bars and lift-pit walls of this set
(Q-71 "ALSO WAITS ON"). Bar ends (r2 corrected): F12, F13, F14 and FF are drawn closed on p.9 (box symbol in REMARKS)
and the p.13 typical details call out "Boxed bars" turned down at both edges; FF also has the p.14 section. No leg
length is dimensioned anywhere, so leg steel is HELD for all four; F8 has no symbol and no section (ends HELD). The
designer request is therefore for the leg / lap dimension of the boxed bars (all footings) and the meaning of the
`3+n` BOXED cells, not for a missing top-bar detail.

## 8. Rework r2 (worker 1, 2026-10-21, after the Checker's 20:50 rejection)

Changed only the drawing evidence on bar ends (sections 1, 3.5, 4, 7): added the p.9 BOXED column and the closed-cage
symbol of F12 / F13 / F14 / FF (read on the PDF at 300 dpi and confirmed in the DXF, sha prefix 9f9d1179: REMARKS
column, layer S-REIN.D, none in the F8 row) and the p.13 "Boxed bars" callout; corrected the three wrong statements.
Leg length and the meaning of `3+n` stay HELD / UNKNOWN (nothing printed). No count, length, kg, reading or mapping
changed; the tool is unchanged and its `--check` still passes.
