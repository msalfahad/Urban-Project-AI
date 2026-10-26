# T-305: EXTERIOR PLASTER / SIGMA FACE-TO-LINE LEDGER, every drawn exterior face against the candidate's line ids (development villa; every villa by R-T305-1 .. 3)

Worker 2 (lane A), claim 2026-10-26 02:41 UTC, run unknown. Integration dependency of a MISSING / unintegrated category
(the facade): a lane I package can now carry it face by face. Research only: no engine module, rule or knowledge file,
candidate line, released line or V2.9 cell changed; released default stays V2.9 + route G; nothing released. ERS read
and applied: s.2.1 (physical element first), s.2.2 (owner manual method and drawing-derived method side by side), s.2.4
(reconcile in m2 to named causes, never a plug), s.3 (one element, one owner per face; build before deduct; a notation's
meaning before its arithmetic), s.4 (rule + tests, normal and adverse), s.7 (lesson row, section 8). Builds on merged
T-159 (faces), T-162 r2 / T-172 (parapets, corners), T-175 (physical scope), T-237 (sizes), T-249 (opening census),
T-302 (W17 hole); none of their quantities is re-derived, only bound to lines.

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py, then research/agents_t266/v3018_run.py:
**V3_0_18_BOQ_LINES json `ec741004` / csv `af577422` = the candidate of record** (3,705 lines). Extract
`t305_alsenan.py --extract <run>/t266/v3018` -> CANDIDATE_V3018_FACADE_LINES.json (the 13 ARCH.FACADE_RUN /
ARCH.FACADE / FIN.EXT.FINISH lines: id, floor, element, state, quantity, run, RFI head; a census by item code of every
line naming facade / exterior / parapet / soffit / boundary). T-159 outlines re-extracted (`t159_extract.py`, run
98.886694 / 63.168865 / 29.800000 m, passage RESOLVED 105.886694) and its face table rebuilt **byte-identical** to the
merged FACADE_SIDES_T159.csv. `--geometry` read two glazing bindings by handle (FACE_GEOMETRY_T305.json, lengths only).
Ledger `--write`; `--check` rebuilds byte for byte; tests `tests/t305_facade_ledger` (19).

## 2. The physical element and the candidate's lines

Exterior plaster with its Sigma coat (owner notes Sigma 2026-10-21: Sigma is not a separate area) covers the OUTER face
of the built envelope, band by band between printed levels (owner Q-07 B), less each opening by the area of its HOLE in
that face (owner Q-73 A confirmed: full openings, only where masonry physically exists; T-302: the developed hole, never
the aluminium window measure). The candidate carries, per floor (GF / 1F / 2F):

| Line | Item | State | Quantity | Reaches (its own formula, UP-FACADE-001) |
|---|---|---|---|---|
| L-a1d2bc132f449743b329 / L-c22a64296e7db7575c68 / L-75f85984c61774c0a8fc | ARCH.FACADE_RUN | PROVISIONAL | 105.886694 / 63.168865 / 29.800 lm | the outline (V3.0 passage walls in on GF) |
| L-cc7dc0a51f3319a99482 / L-43527ae4e8ec75c56636 / L-348c4d8d32f3f6d35fe5 | ARCH.FACADE | BLOCKED_RFI | none ("FACADE_HEIGHT_NOT_IN_THE_DRAWING") | run x (next F.F.L. - F.F.L.); top floor to the lowest parapet top |
| **L-b05f70c92405dbcfbe62 / L-8bb83e16cc7b104ab88b / L-d52c4f763b19aedf8b8b** | **FIN.EXT.FINISH** | BLOCKED_RFI | none ("EXTERIOR_FINISH_NOT_SPECIFIED") | = ARCH.FACADE of its floor x the stated finish |
| L-c0e9a4c62171de1f369b | ARCH.FACADE plinth (GF) | BLOCKED_RFI | none | run x (F.F.L. - ground); no finish line reads it |
| 3 x 'facade outline 2' (L-66bc23b0..., L-472196bf..., L-0b729a17...) | ARCH.FACADE_RUN | BLOCKED_RFI | none | the 10.84 m second outline (RFI, defect L-N10-01): no face of T-159 |

So the candidate **does carry an exterior finish line on each floor, but none has a quantity**; no candidate line
reaches parapet outer faces, the plinth plaster, a face standing on a lower roof, parapet inner faces / tops or corners
(defect L-N10-02 measured here). The plaster / Sigma faces are booked to FIN.EXT.FINISH (the trade line); ARCH.FACADE
is recorded beside each as the geometry carrier it reads, never as a second owner. Other candidate lines touching the
envelope do not own faces: ARCH.WINDOW_REVEAL (27, BLOCKED_RFI) is the opening reveal strip in the wall thickness;
DOOR.EXTERNAL.ALUMINIUM (8) and ARCH.WINDOW are the opening items; STR.CONC.BOUNDARY_WALL (1) is the boundary
foundation only; FIN.CEILING lines hold the soffits (Q-68 C; not wall faces, outside this universe).

## 3. Every drawn exterior face once (FACE_LINE_LEDGER_T305.csv; 98 bands, residual 0.000000 m2 against T-159)

R-T305-1: a band belongs to its floor's finish line only where the line's formula reaches it (inside F.F.L. -> next
F.F.L.; top floor to its parapet top); the GF house roof-edge bands +1.00 -> +6.00 are cut at +5.50 (printed at both
ends); everything else is NO_LINE with its m2 and status.

| State | Line / cause | Measured m2 | HELD m2 (range) | Owner manual (Q-07 B bands) |
|---|---|---|---|---|
| IN_LINE | GF L-b05f70c92405dbcfbe62 (27 faces, 29 bands) | 479.920 | - | 479.920 |
| IN_LINE | 1F L-8bb83e16cc7b104ab88b (12 faces) | 265.309 | - | 265.309 |
| IN_LINE | 2F L-d52c4f763b19aedf8b8b (4 faces, +9.70 -> +14.40) | 140.060 | - | 140.060 |
| NO_LINE | parapet outer faces above the next F.F.L. (GF house +5.50 -> +6.00 on 28.770 m = 14.385; 1F above +9.70 = 52.043) | 66.428 | 1.870 .. 7.248 (1F SW-2 curve, recess returns) | 66.428 |
| NO_LINE | plinth (ground -> F.F.L.): geometry line L-c0e9a4c6... only, no finish line | 66.736 | 4.952 .. 6.013 (pool-court plinth) | outside the bands (UP-FACADE-001 RFI) |
| NO_LINE | 1F SE-1 face on the annex roof (+4.30 -> +5.50, 3.40 m) | 4.080 | - | 4.080 |
| NO_LINE | 1F slab edges over open air | no area (13.079 m; depth not printed, Q-68 C) | HELD, no number | - |
| NOT A FACE | GF SW-4 / NE-5 (passage mouth, boundary-wall end; Q-67 A cond.) | - | - | - |
| **Total** | | **1,022.534** (= T-159, residual 0.000000) | **6.822 .. 13.261** | **955.797** (= T-159) |

The owner manual figure (Q-07 B, bands from the floor, plinth an RFI) and the drawing-derived geometric figure (ground
to top) stand side by side on every row. OTHER_TRADE and NOT_APPLICABLE hold no T-159 face: the boundary fence and the
domes are not house faces (section 5).

**What the candidate's formula would give** (run x one printed storey height, the line's own formula; an illustration,
NOT a candidate quantity): 1F 63.168865 x 4.20 = 265.309 = the IN_LINE faces (difference 0.000067, T-159 4-decimal
areas); 2F 29.80 x 4.70 = 140.060 (0.000); **GF 105.886694 x 4.50 = 476.490 against 479.920: +3.430 m2 =
4.90 m x 0.70 m** (the passage face P-1 4.70 m and the covered annex strip of SW-3 0.20 m stand on the annex F.F.L.
+0.30, not the house +1.00), plus the 14.385 m2 GF house parapet band the formula never reaches. The annex edge faces
(+0.30 -> +4.80 = 4.50) agree with run x 4.50 only because the annex parapet top happens to be 4.50 above its own floor:
a villa whose annex roof sits lower would be over-measured by a single-height formula.

## 4. Every facade opening once, by its hole on its face (OPENING_HOLES_T305.csv)

R-T305-2: one deduction per opening on the one face band that holds it (every head is below its band top), by the hole
in that face; the aluminium window measure is kept beside it, never used.

| Group | Openings | Deduction m2 | Status |
|---|---|---|---|
| windows with printed / drawing-confirmed sizes (T-237 merged) | 22 | 35.585 | DRAWING-CONFIRMED |
| arched holes by their outline (T-238): W15, W16, W26 | 3 | 10.601 (window measure 11.650, Q-32 A) | DRAWING-CONFIRMED |
| W17 exterior developed hole (T-302) | 1 | 8.1434 (window measure 9.870, Q-76 A) | DRAWING-CONFIRMED |
| W03 curved pool glazing: the GF NW-4 face is the glazed line (T-175 GLAZED, Q-69 B) +1.00 -> +5.30, developed on the face 6.657684 x 4.30, plus its frame ends on NW-3 0.143487 and NW-5 0.103487 (glazing end lines 26D / 275) | 1 (3 rows) | 28.628 + 0.617 + 0.445 = 29.690 (window measure 28.251, Q-38 A) | DRAWING-CONFIRMED |
| W18 (1F, no engine opening, T-249): symbol 0.500 m in the 0.467302 m recess face NW-4; 0.032698 m of frame behind the return | 1 | 0.467302 x 2.16 = 1.009 (window measure 1.080) | DRAWING-CONFIRMED |
| doors with no printed height (Q-55 C 2.20 m): D-GF-01/03/05/06/09, D-2F-01 | 6 | 12.760 | ASSUMED — OWNER-APPROVED |
| W02 saloon glazing 6.33 m (height not printed; render shows two windows, designer D-53) | 1 | 0 .. 28.485 (cap = width x band 4.50) | HELD |
| D-GF-07 main door 2.00 x 2.50 printed (render single leaf vs plan double, T-161 F07c, designer D-53) | 1 | 0 .. 5.000 | HELD |
| GF OP-001 0.200 m on NE-6 (T-109 WALL_END_GAP: a drafting gap, wall face) | - | 0 (not an opening) | - |
| **36 census openings** (= T-162's 36 facade openings) | | **85.029 fixed + 12.760 assumed + 0 .. 33.485 held** | |

W05, W11, W12: their area is width x the ESTABLISHED height (0.60 x 0.80, 1.95 x 2.20); only the sill datum is HELD,
which moves the hole inside the band, not its area: taken as DRAWING-CONFIRMED area (Checker please confirm the
reading).

**Per line (LINE_SUMMARY_T305.csv; the lane I consumer shape):**

| Finish line | Gross m2 | Openings fixed / assumed / held cap | Net m2 | Status |
|---|---|---|---|---|
| GF L-b05f70c92405dbcfbe62 | 479.920 | 48.590 / 10.560 / 33.485 | **387.285 .. 420.770** | HELD (W02, D-GF-07); doors ASSUMED |
| 1F L-8bb83e16cc7b104ab88b | 265.309 | 30.784 / 0 / 0 | **234.526** | DRAWING-CONFIRMED |
| 2F L-d52c4f763b19aedf8b8b | 140.060 | 5.655 / 2.200 / 0 | **132.205** | ASSUMED part (D-2F-01) |
| **in-line total** | **885.290** | **85.029 / 12.760 / 33.485** | **754.016 .. 787.501** | |

No opening falls on a NO_LINE band: the NO_LINE wall faces (parapet outer faces 66.428, plinth 66.736, the annex-roof
band 4.080 = 137.244 m2 + 6.822 .. 13.261 HELD) are net = gross.

## 5. Items beside the faces (ITEMS_T305.csv; R-T305-3)

| Item | Quantity | Status | Ledger state |
|---|---|---|---|
| parapet inner faces (annex 14.214, GF 13.985, 1F 52.082 .. 57.185, 2F 14.150) | 94.431 .. 99.534 m2 | DRAWING-CONFIRMED geometry (1F HELD); plaster scope UNKNOWN; upper bound from the slab top | NO_LINE |
| parapet tops (5.777 + 5.674 + 9.935 + 5.415) | 26.801 m2 | DRAWING-CONFIRMED; cap profile P1 / P2 / P3 not keyed | NO_LINE |
| corners / arrises (T-162 r2) | 576.872 m.l DRAWING-CONFIRMED + 32.200 m.l ASSUMED (doors) + HELD (slab edges, frames 98.0 .. 195.2, drip, boundary wall) | as listed | NO_LINE (own m.l line; never m2) |
| facade frames (SE stair tower, NW pool court) | HELD (profile not detailed) | HELD | NO_LINE |
| SE projecting band 0.20 m (Checker T-159 observation: a line 0.200 m outside the 1F SE-1 and GF SE faces) | UNKNOWN, not 0 | UNKNOWN | NO_LINE |
| drip edge band | nothing drawn; owner not answered | UNKNOWN | NO_LINE |
| boundary / street fence faces | HELD (Q-65 C) | HELD | OTHER_TRADE (site boundary element) |
| domes inside and outside | excluded (owner item 3: no domes) | - | NOT_APPLICABLE |

## 6. Against the freelancer (exterior plaster / Sigma, m2)

The candidate has **no exterior plaster quantity** (3 FIN.EXT.FINISH lines BLOCKED_RFI): against his 1,469.97 m2 net it
is HELD, not 0. What this ledger makes ready for lane I, like for like (T-162 r2 reconciliation, unchanged):

| Basis | Drawing (this ledger) | Freelancer | Difference |
|---|---|---|---|
| wall faces gross (his wall rows, "without domes etc.") | 1,022.534 (+6.822 .. 13.261 HELD) | 968.237 | +54.297 (+5.6 %): RULE_DIFFERENCE totals (T-159 / T-162) |
| openings | 97.789 fixed + 0 .. 33.485 held, in FULL (Q-73 A) | 65.745 at HALF = 32.873 | RULE_DIFFERENCE (half deduction is his practice, not an owner rule, owner item 1) |
| wall faces net (all bands) | 891.260 .. 924.745 (+ held bands) | 935.364 (968.237 - 32.873) | -44.104 .. -10.619 (-4.7 .. -1.1 %) |
| his other rows | parapet inner + top 121.232 .. 126.335; domes excluded; boundary fence HELD; drip UNKNOWN; frames HELD; pool soffit 12.834 accepted (owner item 4, ceiling side) | 146.659 + 181.806 + 107.240 + 50.876 + 28.868 + 19.154 | per T-162 r2 |

Verdict proposals (for the Checker): the face-to-line ownership is ENGINE_RIGHT-ready only once a lane I package writes
the quantities (the candidate lines carry none, so there is no engine figure to judge: UNRESOLVED = HELD, not 0); the
formula reconciliation is a named lane I RISK, not a verdict on the current candidate: wiring run x H instead of the face
rows would be wrong on GF by -3.430 m2 (two-F.F.L. floor) and would leave the 14.385 m2 GF parapet band out; parapet outer faces, plinth plaster, the annex-roof band, parapet inner faces / tops and corners are a
**MISSING category** (no candidate line, priority 2).

## 7. Rules and tests (normal and adverse, non-Alsenan hand fixture)

`facade_line_ledger.py`: R-T305-1 (`owner_of`, `band_kind`, `split_at`), R-T305-2 (`deduction`, `hole_on_face`),
R-T305-3 (`to_wall_line`, `item_owner`, `add_to_area`), `Book` (one owner per key). Fixture (tests/t305_facade_ledger/
test_t305_rules.py, hand calculation in its docstring): two-storey house, GF 10.00 m face (6.00 flush under the set-back
1F, 4.00 roof edge with a 0.50 parapet), 1F 6.00 m, top floor to its parapet: GF plinth 5.000 NO_LINE, storey 33.000
IN_LINE, parapet 2.000 NO_LINE, 1F 25.200 IN_LINE; W1 1.800 + D1 1.980 (assumed) -> GF net 29.220. Adverse: a face
booked to two lines refused; a window measure used as the wall deduction refused; a hole larger than its band refused;
a parapet top or a corner m.l booked as wall m2 refused; a missing face reported as 0 refused (a HELD face with a
bound is accepted); a band straddling the next F.F.L. refused until split; a face on a lower roof and a slab edge give
NO_LINE; zero or two storey lines give NO_LINE, never a guess; mirror / reversed order / millimetre levels do not move
the result. Alsenan rebuild: test_t305_alsenan.py (byte-identical outputs, candidate identity, residual 0, 36 openings
once, line nets).

## 8. What is learned / what is missing / lessons-register row (ERS s.7)

- Learned: the candidate's single-height formula (run x H) is exact on a floor whose faces share one F.F.L. (1F, 2F
  here, 0.000 m2) and wrong on a floor with two F.F.L.s (GF annex +0.30 / house +1.00: +3.430 m2) and blind above the
  next F.F.L. (parapet outer faces 66.428 m2) and below the floor (plinth 66.736 m2, the annex-roof band 4.080 m2): the
  facade must be carried face by face, not as run x height.
- Learned: a glazed wall line (W03) is a hole the length of its face plus its frame ends, not the printed window width;
  a window symbol wider than its recess face (W18) deducts only the face it sits in.
- Missing (HELD / UNKNOWN, never 0): W02 and D-GF-07 holes (designer D-53 / D-45); the pool-court plinth (rim vs deck);
  the 1F SW-2 parapet curve; 13.079 m of slab edge (depth); the exterior finish system itself (the lines' own RFI: no
  specification printed; the area does not depend on it); parapet profile (P1 / P2 / P3); the SE 0.20 m band; drip.
- Lessons-register row proposal: "L-T305 | facade / exterior plaster | a facade carried as run x one storey height is
  exact only where every face of a floor shares one F.F.L. and ends at the next F.F.L.; two floor levels, set-back
  parapets, faces on lower roofs and plinths need face-by-face bands | R-T305-1 | tests/t305_facade_ledger".
- Consumer for lane I (T-199 / the V3.0 facade package): LINE_SUMMARY_T305.csv (per finish line gross / deductions /
  net range / status) with FACE_LINE_LEDGER_T305.csv and OPENING_HOLES_T305.csv as its rows; ITEMS_T305.csv for the
  NO_LINE categories a new line family must carry.

Files: `facade_line_ledger.py`, `t305_alsenan.py`, `CANDIDATE_V3018_FACADE_LINES.json`, `FACE_GEOMETRY_T305.json`,
`FACE_LINE_LEDGER_T305.csv`, `OPENING_HOLES_T305.csv`, `ITEMS_T305.csv`, `LINE_SUMMARY_T305.csv`, `summary.json`;
tests `tests/t305_facade_ledger/`.
