# T-524: lintel concrete at FLAGGED_DEFICIT ends: who owns the volume, exactly once (R-T524-1, Gate A, research only)

Worker 3, 2026-11-05. Lane I, non-candidate. `t524_lintel_end_ownership.py` (project-agnostic assessment + training-villa
builder reading committed records only), `tests/t524_lintel_end_ownership/` (32 tests). No engine, tool, rule, knowledge,
hub, master or candidate file changed; released default (V2.9 + route G) and candidate V3.0.58 untouched; bars untouched
(T-515).

## 1. Physical element and question (ERS s.2.1)

The cast RC lintel: span over the opening, two END ZONES beyond the jambs, and the HOST each end zone meets. T-453 / the
candidate STR.CONC.LINTEL lines carry B x D x (w + 2 x 0.40) (printed 'MIN.40cm' both ends). T-516 measured the masonry a
beside every jamb: 10 lintels have an end with a < 0.40. Per deficit end the T-453 zone overruns the masonry by
r = 0.40 - a, and that volume is one of:

| Host | What r is | Owner, counted once |
|---|---|---|
| RC column | the part inside the column outline, min(r, column depth along the wall) | STR.CONC.COLUMN (section x storey height already holds it); never B9-02 |
| RC column, beyond its far face | a lintel does not pass through a column | NOT BUILT (no trade) |
| far face of a cross wall / free end | the next space | NOT BUILT (no trade); lintel extension <= a |
| shared pier p < 0.80 | the two T-453 zones overlap by 0.80 - p (pier twice + each zone over the neighbour span) | LINTEL ON LINTEL: the pair occupies the pier once |

The lintel at a column end stops at the column face (extension in [0, a]); its connection to the column is a designer
item (RFI, never blocks integration): lines stay HELD BY NAME with [lo, hi] beside, never 0.

## 2. Evidence (committed records, numbers only)

- a, stoppers, through walls: research/agents_t516/out (Checker AGREE 06:09; P7757.dxf sha ab54dd55).
- B, D, T-453 L / m3 / formwork, heads: research/agents_t453/out/LINTELS_T453.csv (L1 B x 20, schedule p.13).
- Columns: R9.1 column crosswalk (per-storey outline position, section by storey from the p.9 schedule) + S8.6 opening
  census (opening centre in the same structural frame, wall angle, thickness). The builder re-derives the column face gap
  in the structural frame and refuses unless exactly one column reproduces the T-516 a within 30 mm (frame registration;
  W18 jamb 32.7 mm inside C8 by the arch DXF register vs 32.8 mm here).
- W18: start jamb 32.7 mm inside column C8 (ELEMENT_REGISTER 'Opening OP-1F-026', VERIFIED two routes, T-274).

## 3. Per deficit end

| Lintel | end | a m | host (along-wall depth) | gap struct frame | r m | inside column m3 | not built m3 |
|---|---|---|---|---|---|---|---|
| D-1F-04 | START | 0.079 | planted PC X08-Y02 1F 70x20 (0.20) | 0.0797 | 0.321 | 0.006000 | 0.003630 |
| D-2F-03 | START | 0.249 | C2 X10-Y09 2F 20x50 (0.50) | 0.2492 | 0.151 | 0.004530 | 0 |
| D-GF-06 | END | 0.140 | C6 X08-Y04 GF 25x70 (0.25) | 0.166 | 0.260 | 0.010000 | 0.000400 |
| W18 | START | 0.000 (jamb -0.0327) | C8 X15-Y06 1F 20x90 (0.90) | -0.0328 | 0.400 + strip 0.0327 | 0.017308 | 0 |
| D-1F-03 | START | 0.238 | stub + cross wall WB-FL0074-FL0075 | - | 0.162 | - | 0.004860 |
| D-1F-07 | START | 0.259 | own 0.109 + cross wall 0.150 | - | 0.141 | - | 0.004230 |
| D-1F-10 | END | 0.259 | own 0.109 + cross wall 0.150 | - | 0.141 | - | 0.004230 |
| D-GF-10 | START | 0.253 | stub + cross wall WB-FL0076-FL0077 | - | 0.147 | - | 0.004410 |
| D-GF-11 / 12 | pier | 0.238 | each other (heads 2.20, L1 both) | - | overlap 0.562 | lintel on lintel 0.016860 | - |

D-GF-06: by the structural-frame gap (0.166) the whole 0.234 overrun is inside C6 (0.00936 m3, 0 beyond); by the arch
a (0.140, governing) 0.25 inside + 0.010 beyond. Range of the split 0.00936 .. 0.0100 m3; the lintel figure is the same.

Column lines (V3.0.56 line index; the column lines are untouched, they already hold these volumes):
PC X08-Y02 1F = HL:PLANTED_COLUMN:PC-1F-A (RELEASED 0.588 = 0.70 x 0.20 x 4.20, by section); C6 X08-Y04 GF =
P-C:COL:SH12:C6@250087,56100|GF (RELEASED 0.7875, the only C6|GF line); C8 X15-Y06 1F = P-C:COL:SH12:C8@262766,57890|1F
(RELEASED 0.756 = 0.20 x 0.90 x 4.20; the other C8|1F line is X12-Y02 with the drawn / schedule conflict, HELD
0.756 .. 0.84); C2 X10-Y09 2F = one of the four C2|2F lines, all HELD (sheet-frame id not pinned).

## 4. Corrected lintel concrete (m3; HELD BY NAME, range beside; MIN-BEARING basis = bounded ends at 0.40)

| Lintel | T-453 | lo | hi | removed |
|---|---|---|---|---|
| D-1F-03 | 0.054 | 0.042 | 0.04914 | 0.00486 |
| D-1F-04 | 0.048 | 0.036 | 0.03837 | 0.00963 |
| D-1F-07 | 0.048 | 0.036 | 0.04377 | 0.00423 |
| D-1F-10 | 0.048 | 0.036 | 0.04377 | 0.00423 |
| D-2F-03 | 0.048 | 0.036 | 0.04347 | 0.00453 |
| D-GF-06 | 0.072 | 0.056 | 0.0616 | 0.0104 |
| D-GF-10 | 0.048 | 0.036 | 0.04359 | 0.00441 |
| D-GF-11 + D-GF-12 (pair) | 0.096 | 0.060 | 0.07914 | 0.01686 |
| W18 | 0.052 | 0.034692 | 0.034692 | 0.017308 |
| **Set** | **0.514** | **0.372692** | **0.437542** | **0.076458** |

Conservation (asserted in the code and the tests): 0.076458 = inside columns 0.037838 + lintel on lintel 0.016860 + not
built 0.021760. hi stays a MIN-BEARING figure: the BOUNDED ends may bear more (T-516 pier upper bounds), so the whole
B9-02 line stays HELD / PARTIAL; the concrete total of the villa falls by 0.076458 m3 on these lines only where the
integration adopts hi (0.037838 m3 of it was a double count with columns, 0.016860 with the neighbour lintel).

Formwork (T-453 2 L D + w B): 7.730 -> hi 6.79638 m2 (lo follows lo lengths); end-stop faces at the 4 cross-wall ends
0 .. 0.12 m2 listed for T-474 part 2 (not added); no end form at a column face. Host masonry face deducted by T-453
((w + 0.80) D): over-deducted at least 0.4570 m2 (D r per column / cross-wall end + 0.2 x 0.562 on GF-W32) and the
cross walls lose at most a 0.03 m2 window each where a lintel passes through (4 ends, 0.12 m2): both for the T-498 resume
(material base only; MAS.BLOCK contract area untouched).

## 5. Verdicts, register wording, lessons

- Engine vs freelancer: the freelancer has no lintel concrete row: UNRESOLVED (no comparison). Engine (T-453 / candidate)
  ENGINE_WRONG on 10 lines: 0.076458 m3 not lintel concrete (0.054698 m3 double counted, 0.021760 m3 not buildable).
- Register wording proposed for the Lead: "RC LINTEL END at a column / cross wall / shared pier (T-524, R-T524-1): the
  lintel runs from its bearing to the column face; any lintel volume inside a column outline is column concrete
  (STR.CONC.COLUMN, counted once there, never B9-02); beyond a column's far face or a cross wall's far face nothing is
  built (no trade); two lintels over one pier occupy it once (pair capped at the union); the host masonry material
  deduction takes only the lintel face that lies in the host wall."
- Lessons row (proposed, ERS s.7): | 2026-11-05 | a lintel length w + 2 x MIN bearing was booked where the jamb meets a
  column, a cross wall or a shared pier | 0.0547 m3 counted twice (columns, neighbour lintel) and 0.0218 m3 that cannot
  exist | cut every end zone at the first host it meets; inside a column it is column concrete; a pier is occupied once;
  conserve removed = inside + on-lintel + not built | tests/t524_lintel_end_ownership | T-524 |

## 6. Open

- Lintel connection at the 4 column ends, the 4 cross-wall ends and the D-GF-11 / 12 pier: designer item (T-516 RFI).
- D-GF-12 END (oblique junction) stays HELD (T-453 b_min in hi, 0 in lo).
- C2 X10-Y09 2F sheet-frame line id not pinned (all C2|2F lines HELD); W18 END 0.478 vs Checker 0.578 (F-C-T519-1) does
  not touch a deficit end.
- Pair overlap assumes the two heads equal (T-150 2.20 both, ASSUMED heads): refused automatically if they differ.
