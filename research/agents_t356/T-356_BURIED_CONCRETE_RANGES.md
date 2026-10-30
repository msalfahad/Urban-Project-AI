# T-356 Three buried-concrete range findings of T-347: strap blinding, boundary lower band, interior ground-beam depth class (lane S)

Worker 1, 2026-10-30 01:21 .. UTC, run session_01E6cPnbg5mYjoMs4iL8kNku, branch `agents/task-T-356`. Research ledger:
no candidate, released or engine line changed, no method or rule version, nothing released. Development villa, not an
accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. T-347 MERGED 509f90c2 before the claim: its verdict closed
none of the three findings, so all three are answered here.

## 0. Sources and runs

Own reads, Drive "Alsenan chalet project" (decoded into `.work/private` only): 'ST7757 dxf.dxf' (`9f9d1179`, the
manifest copy) and 'ST7757.pdf' (`74da1523`; p.10 schedule of simple beams, p.13 typical footing / ground-beam details,
p.14 typical boundary wall plan + section A-A at 110 and 400 dpi). Candidate of record: V3.0.24 lines as committed by
T-347 (`CANDIDATE_V3024_BURIED_LINES.json`, lines json `19394733`). Merged ledgers read only: T-347 binding, T-242 run
ledger, T-233, T-230, T-100, T-253, T-037.

```
python3 -I research/agents_t356/t356_extract.py "<.work/private>/ST7757 dxf.dxf"    # -> ALSENAN_T356_INPUT.json (values only)
python3 -I research/agents_t356/t356_alsenan.py --write                             # -> FINDINGS / FILL / DOWNGRADE_PROPOSALS / summary
```

Files: `t356_rules.py` (R-T356-1 .. 6, pure), `t356_extract.py`, `t356_alsenan.py`, `ALSENAN_T356_INPUT.json`,
`FINDINGS_T356.csv` (15 lines), **`FILL_T350_T356.csv`** (11 HELD rows for T-350), `DOWNGRADE_PROPOSALS_T356.json`
(2 proposals for the Checker), `summary_t356.json`. Tests: `tests/t356_buried_ranges/` (29: rules on the hand villa T356-X, strip geometry normal / rotated /
mirrored / skewed / past the plot, committed-output checks).

## 1. F-T347-2 Strap blinding (L-35382b18, STR.CONC.BLINDING, BOUNDED_EXPOSURE 0.377803 .. 0.771877 m3)

**Physical element**: a 10 cm plain-concrete layer under the three straps SB1 / SB2 / SB3 between the faces of the
footings each joins, if one is cast. **What is printed**: p.10 gives the strap sizes only (SB1 70 x 50, SB2 100 x 50,
SB3 50 x 40); p.13 draws blinding under footings ('10 | L x W | 10') and under ground beams ('10 | 30 | 10'), and no
strap section exists (D-15). The strap soffit level is not printed either (T-230: flush with the footing soffits at
5 / 5 known ends with D = H, but SB3 / F3 is 0.40 vs 0.30).

**Own measure** (DXF strap edges 1689 / 1B1C, 1B08 / 1B09, 1B26 / 1B27; footing outlines 1B24, 1B1B, 1B07, 1B19,
1B2A, 166B): the strip grown 0.10 on its two sides only, clipped at the footing outlines, inside the plot (no part
beyond 1658):

| Strap | joins | clear concrete m2 | own strip m2 | in the footing blinding band m2 | merged strip m2 |
|---|---|---|---|---|---|
| SB1 | F8 1B24, F10+F 1B1B | 3.185000 | 4.095000 | 0.180000 | 3.915000 |
| SB2 | F11 1B07, F6 1B19 | 2.264406 | 2.722948 | 0.242040 | 2.480908 |
| SB3 | F15 1B2A, F3 166B | 1.632420 | 2.284012 | 0.149771 | 2.134241 |
| **total** | | 7.081826 | **9.101960** | 0.571811 | **8.530149** |

The strip between two parallel footing faces is a parallelogram, so its area is exactly (B + 0.20) x axis clear length;
the PRINTED breadth governs over the drawn one (p.10: SB1 0.70, SB2 1.00, SB3 0.50; drawn SB2 is 0.987 .. 0.988 wide,
SB3 0.500 .. 0.502). Axis clear lengths (own): SB1 4.5500, SB2 2.2927, SB3 3.2580 m. Own strip at printed breadth
**9.126840 m2**; the drawn polygon 9.101960 m2 is kept as the check (-0.024880 m2 = the drawn SB2 / SB3 widths).

Readings: **none** (what is drawn: no blinding under a strap) 0; **merged** (every strap soffit flush with the footing
soffits, the footing blinding band owns its 0.10 in front of each face) 0.855277 m3; **own layer** (strap soffit at
another level) **0.912684 m3**. Every admissible reading lies in **0 .. 0.912684 m3** (R-T356-2). T-233 / T-100 gave
0 .. 0.913 by the same formula on T-065's rounded lengths (2.294 / 3.259): +0.000316 m3, rounding only.

**The line, decomposed** (own reproduction, `candidate_basis_reproduction_m2`): own strip 0.912684 - drawn vs printed
breadth 0.002488 - merge into the footing band 0.057181 + strip inside the F10+F outline the route-G frame does not see (1B1B is an open polyline, T-233
finding 3) 0.121505 - **plan deduction of the ground-beam blinding strips 0.214938** + residual 0.012295 = 0.771877.
The ground-beam deduction is physically inadmissible: T-230 (merged) puts every strap top at or below -0.33 and every
ground-beam soffit at or above -0.35 in the annex and +0.35 in the main house (gap >= 0.28 m): two layers at different
levels share no volume. The low end 0.377803 is the REACH merge window of an outline-less footing (superseded by
the 1B1B outline) and it excludes the drawn reading 'none'. Residual 0.012295 m3: the engine's ground-beam strip
outlines (route G bands) vs the T-230 pairing used here; not traced further because the deduction itself is refused.

**Proposal: CORRECT RANGE** (= LEDGER_RIGHT, T-233 confirmed to 0.0003 m3): HELD 0 .. 0.912684 m3, open item D-15 (blinding under straps
and strap soffit level). The line is already a held state, so this is a lane I held-range fix in T-350, not a
downgrade record. Nothing is chosen because it is larger.

## 2. F-T347-3 Boundary lower band (L-6290a9f3, STR.CONC.BOUNDARY_WALL, SOURCE_DERIVED 7.2204 m3)

**Physical element**: the LOWER boundary-wall ground beam (p.14 section A-A: 20 wide, depth NOT written, bars 2 d14 +
3 d16 T&B, d8/20, on the 130 x 80 x 30 pad under each boundary column, on 10 cm blinding), drawn on the foundation
plan as the 0.20 band S-BOUN 1658 / 1659 closed round the plot. Different member from the UPPER G.B at N.G. (T-253,
44.07 m x 0.20 x 0.40 = 3.5256 m3, brick between them).

**Own measure**: band area 18.388 m2, centreline **91.94 m**; it runs through 9 footing outlines for **21.45 m**
(1B1B 4.45, 1B07 3.50, 1B1A 3.80, 1B2A 1.80, 1B24 3.60, 1668 0.90, 1669 1.50, 166A 0.90, FN 1100 1.00: the owner's
'10 footings' = 9 outlines, F10 + F tagged on one); free 70.49 m. Both owner figures re-measured exactly.

**Printed sections**: p.10 row 'B.W 20 x 60' (4 d16 bottom, 2 d14 top, 7 d8/m), p.14 plan 'GROUND BEAM (20x40)'.
The A-A lower G.B bars are NOT those of the B.W row (2 d14 + 3 d16 T&B, d8/20), and its depth is not written: so
which section governs the band is open (Q-28 / RFI-S03). Crossing levels with the 9 footings are not printed (Q-28:
deduct only where they share elevation). Range of the band solid (R-T356-3): **5.6392 .. 11.0328 m3** (70.49 x 0.20 x
0.40 .. 91.94 x 0.20 x 0.60); the owner's provisional A is 8.4588.

**New named item (pad split, R-T356-4)**: A-A draws the lower G.B down to the pad soffit and the 80 of the pad
includes the 20 of the beam, so at each pad 0.20 x 1.30 x 0.30 = **0.078 m3** belongs to the band OR to the pad,
once. The pad (and column) count is not printed ('SEE ARCH PLAN', M4 / RFI-S04) and no rule names the owner: the
LINE's low end is NOT ESTABLISHED (5.6392 - 0.078 n); the physical total (band + pads) does not move.

**The line**: 60.17 m x 0.20 x 0.60. 60.17 m is the band with one plot side lost (T-037: 30.97 + 14.60 + 14.60, the
31.17 m neighbour side not in the group): neither 70.49 nor 91.94. At B.W 20 x 60 it is -1.2384 m3 against the
owner's provisional A and -3.8124 against B; its section is one of two printed readings. It lies inside the range
only by chance. **Proposal: CORRECT RANGE by a downgrade-only record** (UNSUPPORTED BASIS on the length; DGP-T356-BAND):
line HELD blank, audit range 5.6392 .. 11.0328 m3 for the band solid, line low end NOT ESTABLISHED (pad split).

## 3. F-T347-4 Interior ground-beam depth class (D-34) - the whole population, not only the 6 flagged lines

**Printed** (p.13, read at 110 dpi): 'Ground Beams. More than 5m length without concentrated load' 30 x 60; 'Less than
5m length without concentrated load' 30 x 40; 'Less than 2.5m length' 30 x 30. No precedence is printed. Below 2.5 m
both lower titles hold literally; exactly 5.00 m is covered by neither 'more' nor 'less' (R-T356-5). Note: the 2.5 m
title alone has no 'without concentrated load' qualifier, so 'the most specific title governs' is not even implied by
the wording: D-34 stays a designer item (S8), not something this task can settle.

**Root cause of the single values**: the candidate's range rule varies only the LENGTH BASIS (clear vs c/c: 'the class
at the other length basis gives the range'); a run whose two bases fall in the same band gets one depth, although two
TITLES hold. Own check of all 13 T-242 D-34 runs (titles recomputed on both bases, net plan x depth; equal to the T-242
ledger to 1e-4 on every run):

| Lines | Verdict | Line m3 | Own range m3 |
|---|---|---|---|
| 6 D-34 only, single 0.30 (13C+7D9, 141+7DA, 16F+7FF, 17B+7E5, 180+181, 182+183: the T-347 six) | CORRECT_RANGE | 0.716600 | 0.716600 .. 0.955467 |
| 3 D-34 + D-33, single value (177+7CD#2 0.30, 180D+180E 0.30, 184+7CF#3 0.60 at exactly 5.00 m) | CORRECT_RANGE | 1.227300 | 0.927300 .. 1.336400 |
| **9 single-value lines** (DGP-T356-GB-D34) | | **1.943901** | **1.643901 .. 2.291867** (high - line +0.347967) |
| 114+115+7DF, 142+7D8 | LINE_RIGHT | already the D-34 range | |
| 15C+7CC, 17E+17F | OTHER BASIS | the line omits the T-230 neck end adjustment of the run (-0.0300 / -0.0003 .. +0.0104 m2): 15C low 0.216 vs 0.207, 17E+17F high 0.291231 vs 0.295391 | held-range fix for lane I, not a D-34 matter |

For the three D-33 runs the range is the printed-title range only; a beam lands on each and no loaded section is
printed (D-33): named beside the range, no figure. **Proposal: CORRECT RANGE by a downgrade-only record**
(DGP-T356-GB-D34, 9 lines, UNSUPPORTED BASIS: one title shown as the value of an open precedence). Displacement: on
the main house the part below EG is 0 under either depth (T-347 ZERO_BY_BOUND); the two annex runs' below-EG share
moves with D inside the T-347 held range: no earthworks figure changes.

## 4. FILL for T-350 (`FILL_T350_T356.csv`, 11 rows, every one HELD with value blank)

| Line | lo m3 | hi m3 | Held by |
|---|---|---|---|
| strap blinding L-35382b18 | 0.000000 (READING_NONE, D-15: a bound from a drawn reading, not a default) | 0.912684 | D-15 |
| boundary lower band L-6290a9f3 | blank (NOT ESTABLISHED: pad split) | 11.032800 | Q-28, M4 |
| 9 interior ground beams | narrowest printed title | widest printed title | D-34 (+ D-33 on 3) |

Checked on the committed CSV by `test_fill_held_blank_never_zero` (the T-332 lesson).

## 5. Methods side by side

| Method | Strap blinding | Lower band | Interior GB < 2.5 m |
|---|---|---|---|
| Owner manual method | none answered (D-15 is a designer item) | Q-28 A PROVISIONAL 8.4588, not released; deduct a crossing only where elevations overlap | none (D-34 designer) |
| Drawing-derived (this task) | 0 .. 0.912684 HELD | 5.6392 .. 11.0328 band solid; line low NOT ESTABLISHED | net plan x [0.30, 0.40] HELD |
| Candidate V3.0.24 | 0.377803 .. 0.771877 (GB deduction, REACH window) | 7.2204 SOURCE_DERIVED (one side lost) | 0.30 single PROVISIONAL |
| Freelancer | in his whole-plot plate (T-233: RULE_DIFFERENCE) | footing sheet 71.7 m x 0.20 x 0.60 = 8.604 (T-233) | 0.30 x 0.60 on every beam (T-242: FREELANCER_WRONG section) |

Who is right: strap blinding LEDGER_RIGHT (candidate WRONG basis on both ends); band ENGINE_WRONG basis (length),
section UNRESOLVED (Q-28); freelancer's band 8.604 = 71.7 m (a bare number, between free and drawn) x B.W: inside the
range, UNRESOLVED; ground beams RULE_DIFFERENCE inside a held range (D-34), candidate shows one reading as a value.

## 6. Rules, lessons row (proposed), checker list

R-T356-1 .. 6 (`t356_rules.py` docstring). Lessons row (ERS s.7): | 2026-10-30 | Three buried-concrete lines carried a
single reading or a mis-based range of an open designer item: strap blinding deducted ground-beam strips 0.28 m above
it and excluded 'no blinding' (0.3778 .. 0.7719 vs 0 .. 0.9127 m3); the boundary band showed 60.17 m (a side lost) x
one section as a value (7.2204 vs 5.6392 .. 11.0328); 9 ground beams showed one length-class title where two hold
(1.9439 vs 1.6439 .. 2.2919) | ranges were built only along the dimension a module knew how to vary (length basis,
merge window), not along every open reading of the element | a held range spans EVERY admissible reading of every
open item the element depends on (title, section, length, presence), each named; a plan overlap is deducted only
between solids that share a level (every villa; provenance T-356) | tests/t356_buried_ranges (GB above never
deducted; lost-side length inside the range still CORRECT_RANGE; most-specific title pick refused; held as 0 refused;
mm input refused) | PROPOSED |

Checker re-measure (one finding by hand, acceptance e): the band: 1658 = 31.37 x 15.00, 1659 = 30.97 x 14.60,
centreline 2 x (31.17 + 14.80) = 91.94 m; the 9 crossings above (each outline's extent along the 0.10 line);
p.14 A-A lower G.B depth not written, pad 80 including the 20. Or SB1: edges 1689 / 1B1C at x 148 712 / 149 412 (0.70),
clear between the F8 face (1B24, y 42 298) and the F10+F face (1B1B, y 37 748) = 4.55 m: own strip 0.90 x 4.55 = 4.095
m2, footing blinding band 2 x 0.10 x 0.90 = 0.180 m2.

## 7. Not done / uncertain

- The candidate's 0.012295 m3 residual on the strap line (route-G band outlines) not traced; the deduction it sits in
  is refused anyway.
- No line wired (lane I T-350); the downgrade records are proposals, the Checker issues them.
- p.13 read at 110 dpi only (titles legible; no dimension read from it).
