# T-277 Drawn-vs-scheduled beam width census (every villa; Alsenan check)

Worker 1 (lane S), 2026-10-24, run session_01SaQian7AivVta43UjyFL3T. Research piece, not wired: no engine, candidate,
released or ledger quantity changes (T-241 / T-252 CONC.BEAM ledger and T-264 formwork r4 read only). Development
villa, not an accuracy claim. Drawings named by Drive folder and title; entities by DXF handle; widths, lengths,
areas and volumes only (no coordinates in any committed file).

ERS applied: s.2.1 (physical element first), s.2.2 (two sources of one dimension side by side), s.3 (notation
before arithmetic; one element, several geometries per trade), s.4 (rule + regression test), s.7 (row proposed, s.8).

## 0. Inputs

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| 'ST7757 dxf.dxf' | 9f9d1179...38079 (= manifest) | the three roof-slab plans (GF / 1F / 2F, ST p.4 / p.5 / p.6): 119 beam labels (TEXT, layer S-TEXT), member edges (LINE / LWPOLYLINE / ARC on layers 1, 2, 5, S-BEAM, S-BOUN, blocks exploded), S-COL.BON column outlines; schedules: 35 SBT inserts (simple beams; attributes BEAM / W / H under the header 'B-(Bredth)' / 'D-(Depth)') and 13 C-BEAM2 / C-BEAM3 inserts (continuous beams; BEAM-NAME / W / H) |
| P7757_DXF_COMPRESSED.zip / P7757.dxf | ab54dd55... | block wall bands (T-125 `alsenan_v2_dump.py`, unchanged) laid on the slab plans by pure translation from the column outlines: GF 30 / 30 and 1F 20 / 20 columns matched, residual 0.000 m (T-108 / T-143 method, re-derived here) |
| merged ledgers | committed | T-252 CONC.BEAM ledger (run lengths between supporting faces, depths), T-110 member register (run ids, a station per run only), T-234 slab ledger (t 0.16 every GF / 1F panel beside these bands), T-228 blockwork register v2 (wall ids by V2 run) |

Files: `beam_width_census.py` (BEAM_WIDTH_CENSUS_V1, stdlib; rules R-BEAM-WIDTH-CENSUS-1, R-BEAM-WIDTH-CONSEQ-1),
`t277_extract.py` (private ST DXF -> `ALSENAN_T277_INPUT.json`: handles, widths, clear distances, schedule rows),
`t277_walls_extract.py` (private wall bands + ST geometry -> `ALSENAN_T277_WALLS.json`: lengths per wall),
`t277_alsenan_check.py` -> `CENSUS_LABELS_T277.csv` (119), `CENSUS_RUNS_T277.csv` (137), `CONFLICTS_T277.csv` (7),
`summary.json`; tests `tests/t277_beam_width_census` (27: villa W 19, Alsenan 8).

## 1. The physical element and the two sources (ERS s.2.1 - 2.2)

A beam's plan width b is one physical dimension that two documents of the same set state independently:

- **drawn**: the normal distance between the member's two drawn edge lines on its roof-slab plan (the difference of
  the radii of two concentric arcs for a ring); the edges must be parallel to EACH OTHER within 0.5 deg, else the
  band has no single drawn width (NON_PARALLEL);
- **scheduled**: the W column of the SBT / C-BEAM row of the label's mark. Notation first: the attribute is a number
  in cm (header 'B-(Bredth)'), converted once (x 0.01); a value that is only a width in another unit (W 20 read as
  20 m, 0.20 read as cm) is refused, never coerced.

Owner Q-61 C(1) governs a difference: CONFLICT, both readings, a designer item; never the schedule because it is
printed, never the larger, never the drawn by habit. **Owner manual method vs drawing-derived method**: no owner rule
fixes the governing width. The schedule method (B x D x L with the schedule B, the freelancer's and the released
route's basis) and the drawing-derived method (b between the drawn edges, the T-110 / T-241 / T-252 ledgers' basis)
are kept side by side below; this census decides neither.

## 2. Binding a label to its band (R-BEAM-WIDTH-CENSUS-1; geometry only, the schedule takes no part)

The label direction (within 2 deg) finds the edge lines crossing its normal at its station (the label centre, then
+/- 0.40 m along it). Two placements, read off the set as its drafting convention and tested:

| Placement | Rule | Alsenan evidence |
|---|---|---|
| INSIDE | the label is centred on the band (centre within 0.03 m of the band axis, text box inside both edges); a line of another layer class inside the span (hidden upstand line) does not split the member | 10 labels: offsets 0.001 .. 0.018 m (B17, B19, B20, B21, B22, B23, B24, B25, B26, B27) |
| BESIDE | otherwise the label names the nearest band from its text box edge; a gap that contains the label without it being centred is the panel strip between two members, never its band | 105 labels, clear 0.03 .. 0.33 m; the labels that sit in a gap without being centred are 0.066 .. 0.367 m off its axis (GF B1, B3, B7, CB3 x 3; 1F B6 x 3; 2F B1, B2) |
| BESIDE_STACKED | a label OUTSIDE the slab (no member edge of the band's own line class beyond it on the whole sheet) with a strip between it and an edge beam: both bands are readings | 3 labels: 1F CB10 x 2 (0.20 outer strip, 0.30 behind), 1F CB12 6DD (0.10 strip, 0.25 behind) |
| BESIDE_TIE | two bands within 0.05 m clear: both are readings | 1 label: GF CA 69E (two 0.30 bands; same width, so the width is settled though the binding is not) |

Classes over ALL readings of a label (`classify_readings`): AGREE only if every reading agrees (|drawn - W| <= 2 mm),
CONFLICT if none does, AMBIGUOUS if they split (the binding, not the width, is the open question), NO_SCHEDULE,
NO_BAND, NON_PARALLEL. A second, run-level pass measures the drawn width at three stations of every T-110 register
run (centre, +/- L/4), its direction from the nearest label of its own mark (the register supplies the station only;
for the two hand-typed centres of B26 / B27 the stations step from their labels).

## 3. Census result (all three slab plans)

| Sheet | Labels | AGREE | CONFLICT | AMBIGUOUS | NO SCHEDULE | NON_PARALLEL / NO_BAND |
|---|---|---|---|---|---|---|
| GF roof (ST p.4) | 66 | 62 | 4 (B29, CB2 x 2, B21) | 0 | 0 | 0 |
| 1F roof (ST p.5) | 38 | 34 | 3 (B6 6C5, CB10 x 2) | 1 (CB12 6DD) | 0 | 0 |
| 2F roof (ST p.6) | 15 | 15 | 0 | 0 | 0 | 0 |
| **all** | **119** | **111** | **7** | **1** | **0** | **0** |

Every one of the 119 labels has a schedule row (47 marks; schedule-internal duplicate: SB2 W 80 / W 100, a strap on
no slab plan, already D-38). Arcs: the GF void ring B7 labels 46E / 46F / 470 / 471 bind the arc pairs 2F0 / 2EE,
311 / 313, 312 / 310, 2EF / 2F0 at 0.200 (= T-252's two sources) and 47D binds 2A0 / 29F at 0.200; the 1F west ring
B4 labels 1828 / 1829 bind 5FE / 601 and 5FE / 600 at 0.200: AGREE.

Runs (137 register runs): **AGREE 105, CONFLICT 7, NO_SCHEDULE 18** (unlabelled spans, strips, upstands, boxes:
D-04 / D-05 / D-26, no own mark; their drawn widths are in the CSV), **NO_STATION 5** (the void-ring arc pieces:
covered by their labels above), **NO_BAND 2** (1F east box and east ring, HELD D-26 / Q-61 C(3)). The 7 CONFLICT
runs are exactly the 7 label conflicts, and they are **exactly D-02 (CB10 x 2) and D-27 (GF B29, CB2 x 2, B21; 1F
B6)**: this engine-independent census finds **no new width conflict** on any of the three sheets and confirms the
T-110 finding, run by run, to 0.1 mm.

## 4. Each CONFLICT and what it moves, per trade (R-BEAM-WIDTH-CONSEQ-1; both readings, nothing resolved)

L = run length between supporting faces (T-252 ledger), D = schedule / section depth (ledger; CB10 from the C-BEAM2
row 23F0 H 50, the ledger leaves it blank), t = 0.16 m (T-234 general note, every panel beside these bands).

| Run (ledger) | Edges | Drawn b | Sched. b | L m | D m | CONC.BEAM m3 drawn / sched. | Beam soffit m2 drawn / sched. | Beam sides m2 (both) | Slab soffit / slab m3, sched. minus drawn |
|---|---|---|---|---|---|---|---|---|---|
| GF B29 BM-GF-054#BAND0008 | 2CE / 463 | 0.200 | 0.25 | 6.7412 | 0.75 | 1.0112 / 1.2640 | 1.3482 / 1.6853 | 7.9546 | 0 .. -0.3371 / 0 .. -0.0539 |
| GF CB2 BM-GF-055#BAND0036.1 | 278 / 274 | 0.250 | 0.20 | 3.4700 | 0.50 | 0.4338 / 0.3470 | 0.8675 / 0.6940 | 2.3596 | 0 .. +0.1735 / 0 .. +0.0278 |
| GF CB2 BM-GF-055#BAND0036.2 | 278 / 274 | 0.250 | 0.20 | 3.3500 | 0.50 | 0.4188 / 0.3350 | 0.8375 / 0.6700 | 2.2780 | 0 .. +0.1675 / 0 .. +0.0268 |
| GF B21 BM-GF-056#BAND0042 (oblique 99.05 deg) | 434 / 433 | 0.400 | 0.45 | 7.4802 | 0.75 | 2.2441 / 2.5246 | 2.9921 / 3.3661 | 8.8266 | 0 .. -0.3740 / 0 .. -0.0598 |
| 1F B6 BM-1F-030#BAND0009 | 5CC / 5CD | 0.200 | 0.25 | 4.4153 | 0.50 | 0.4415 / 0.5519 | 0.8831 / 1.1038 | 3.0024 | 0 .. -0.2208 / 0 .. -0.0353 |
| 1F CB10 BM-1F-031#BAND0026.1 | 5E8 / 5E7 | 0.300 | 0.25 | 2.3010 | 0.50 | 0.3452 / 0.2876 | 0.6903 / 0.5753 | 1.5647 | 0 .. +0.1151 / 0 .. +0.0184 |
| 1F CB10 BM-1F-031#BAND0026.2 | 5E8 / 5E7 | 0.300 | 0.25 | 3.6510 | 0.50 | 0.5477 / 0.4564 | 1.0953 / 0.9128 | 2.4827 | 0 .. +0.1826 / 0 .. +0.0292 |
| **7 runs** | | | | | | **5.4421 / 5.7665** | **8.7140 / 9.0072** | 28.4686 | **0 .. -0.2932 / 0 .. -0.0469** |

- CONC.BEAM (b x D x L, the width effect alone): drawn 5.4421 vs schedule 5.7665 m3, -0.3244 m3 (-5.6 %) over the
  7 runs; D-27 alone 4.5493 / 5.0225 m3 and D-02 0.8928 / 0.7440 m3 = the T-110 / D-27 / D-02 figures. The T-252
  ledger ranges (B29 1.0136 .. 1.2670, B21 2.2629 .. 2.5457, B6 0.4426 .. 0.5532) carry the T-229 end strips as well;
  the width effect is the same.
- FORMWORK: only the beam soffit moves (b x L): -0.2932 m2 drawn vs schedule; the sides (D - t) x L per side do not
  depend on b. The slab soffit beside the band takes the complementary change 0 .. -0.2932 m2 (0 if the face that
  would move is a free edge: which face moves is itself the designer's answer), so the total soffit under these
  slabs does not change for an interior beam.
- CONC.SLAB: 0 .. -0.0469 m3 complementary (convention C1: the slab stops at the beam faces, T-234).
- BLOCKWORK (wall centrelines in the ST frame; the schedule width taken with EITHER drawn face kept):

| Band | Wall (register v2) | Kind | Under the band: drawn / sched. (m) | m2, sched. minus drawn | Register v2 today |
|---|---|---|---|---|---|
| GF CB2 span 1 / 2 | GF-W10 (0.20) | along, 3.470 / 3.350 m | inside both readings | **0** | CB2 pieces 3.46 / 3.36 at the printed depth (T-226 R4) |
| GF CB2 span 2 | GF-W19 (0.15) | crossing 90 deg | 0.050 / 0.050 or 0.000 | **0 .. +0.017** | slab 1.78 + B4 0.22: no CB2 piece (the Checker's 18:04 finding: 8.595 drawn .. 8.612 schedule) |
| GF CB2 span 2 | GF-W20 (0.15) | crossing 90 deg | 0.050 / 0.050 or 0.000 | **0 .. +0.017** | slab 1.02 at h 4.34: no CB2 piece (NEW, the same case as GF-W19) |
| 1F B6 BAND0009 | 1F-W16 (0.15) | crossing 90 deg | 0.200 / 0.250 | **-0.017** | B6 piece 0.26 m (a 0.03 m sampling tolerance each side, not a drawn length) |
| 1F CB10 span 1 | 1F-W11 (0.15) | crossing 90 deg | 0.100 / 0.100 or 0.050 | **0 .. +0.017** | CB10 piece 0.12 m |
| 1F CB10 span 1 / 2 | 1F-W05 (0.20) | along, 2.300 / 3.650 m | inside both readings | **0** | CB10 pieces at the printed depth |
| GF B29, GF B21 | none | | | 0 | |

Blockwork at stake over all conflicts: **-0.017 .. +0.034 m2** (net, schedule reading minus drawn). A wall running
along a conflict band lies inside both widths here, so its height is the printed depth's at either reading (T-226 R4
holds); only crossing walls change, by the strip delta_b x (D - t) = 0.05 x 0.34 = 0.017 m2 each.

## 5. Findings beyond the census numbers

1. **CB10's label does not identify CB10's band.** Labels 717 / 718 stand outside the 1F slab beside the 0.20 outer
   west strip (5E5 / 5E7, T-110 BAND0014, HELD D-05); the 0.30 inner strip (5E7 / 5E8) the ledgers bill as CB10 lies
   behind it. Both readings (0.20 and 0.30) differ from the schedule 0.25, so the line stays CONFLICT either way; but
   D-02's question is wider than "which width": which of the two drawn bands is CB10 (the other then being the
   strip of D-05).
2. **CB12 label 6DD is AMBIGUOUS** (0.10 east strip of D-26 between it and CB12 0.25); CB12's other label 6DE and
   both CB12 run centres read 0.250 = schedule: no quantity effect; noted under D-26.
3. **Blockwork register v2 misses two crossing strips** (GF-W19, GF-W20 under CB2 span 2) and carries two crossing
   pieces at sampled, not drawn, lengths (1F-W16 0.26 for a 0.20 / 0.25 band; 1F-W11 0.12 for 0.10). Lane A
   (T-274, height pieces closing the census length from the member drawn over them) should take these four walls;
   no register row is changed here.
4. Three runs (GF B29, B21; 1F B6) are drawn NARROWER than scheduled and four (GF CB2 x 2, 1F CB10 x 2) WIDER: no one-directional drafting habit explains them, so neither source can be preferred by pattern.

## 6. Designer list (proposed amendments, DESIGNER_CLARIFICATIONS format; the Lead files them; no new D number needed)

| D | Element | What the documents show | What is needed | Quantity kept as | Raised by / task |
|---|---|---|---|---|---|
| D-02 (amend) | 1F beam CB10, 2 spans (2.301 + 3.651 m) | C-BEAM2 23F0 W 25 / H 50; drawn: a 0.30 inner strip (5E7 / 5E8) and, between it and the labels 717 / 718 outside the slab, a 0.20 outer strip (5E5 / 5E7) | which drawn band is CB10 and its width (0.20 / 0.25 / 0.30); what the other strip is (D-05) | CONFLICT: CONC.BEAM 0.7440 (0.25) / 0.8928 (0.30) m3; beam soffit 1.4880 (0.25) / 1.7856 (0.30) m2 (slab soffit, schedule minus drawn, 0 .. +0.2976 m2 / 0 .. +0.0476 m3); blockwork 1F-W11 0 .. +0.017 m2 | T-110; T-277 |
| D-27 (amend) | GF B29 (2CE / 463), GF CB2 x 2 (278 / 274), GF B21 (434 / 433, oblique), 1F B6 (5CC / 5CD) | schedule W vs two parallel drawn edges (B29 25 / 0.20; CB2 20 / 0.25; B21 45 / 0.40; B6 25 / 0.20); no section cuts them | which width is the structure, span by span | CONFLICT: CONC.BEAM 4.5493 (drawn) / 5.0225 (schedule) m3; beam soffit 6.9284 (drawn) / 7.5192 (schedule) m2 (slab soffit, schedule minus drawn, 0 .. -0.5908 m2 / 0 .. -0.0945 m3); blockwork GF-W19, GF-W20 0 .. +0.017 m2 each, 1F-W16 -0.017 m2 | T-110; Checker 18:04; T-277 |
| D-26 (note) | 1F CB12 label 6DD | label outside the slab beside the 0.10 east strip, CB12 (0.25 = schedule) behind it | none for CB12's width; part of the D-26 strip question | no quantity effect | T-277 |

## 7. Verdict proposals (for the Checker)

- 111 labels / 105 runs AGREE: the T-110 / T-252 widths of those runs are confirmed by an engine-independent read
  (DRAWING-CONFIRMED at the width level; length and depth are not re-measured here).
- 7 CONFLICT runs: **UNRESOLVED (designer D-02 / D-27)** against the freelancer, who prices the D-27 spans at the
  schedule width (T-241) — a choice the drawings do not make; the released route also bills the schedule width
  (4.470 + 0.552 m3, T-241): neither is ENGINE_RIGHT nor FREELANCER_RIGHT until the designer answers.
- Blockwork GF-W19 / GF-W20 / 1F-W16 / 1F-W11: register v2 heights at the crossing strips do not follow the drawn
  members (finding 3): ENGINE (register) piece lengths to be corrected in lane A; quantities at stake 0.017 m2 each.

Checker re-measure suggestion (acceptance: three conflicts, two agreements): conflicts GF CB2 span 2 (278 / 274 =
0.250 vs C-BEAM2 28C7 W 20), GF B21 (434 / 433 = 0.400 normal to the edges, which run 99.05 deg; label 468 at
98.52 deg vs SBT 1F49 W 45), 1F CB10 (5E5 / 5E7 0.20 and 5E7 / 5E8 0.30 vs C-BEAM2 23F0 W 25); agreements GF B27
(S-BEAM 326 / 325 = 0.900 vs SBT 1F8B W 90, label 532 inside, centred) and 2F B7 (39A / 39B = 0.200 vs SBT 1EAF
W 20, label 7A1 beside).

## 8. Rules, test, lessons row (ERS s.4, s.7)

- R-BEAM-WIDTH-CENSUS-1 and R-BEAM-WIDTH-CONSEQ-1 (proposed, any villa; stated in `beam_width_census.py`).
  Provenance: drawing-reading conventions observed on this set (label inside = centred; label beside = nearest band,
  a projection strip outside the slab gives two readings), owner Q-61 C(1) for the CONFLICT, R-CONC-OWN-1 / C1 (T-234)
  for the slab complement, T-226 R4 for along-walls (depth only).
- Tests `tests/t277_beam_width_census/test_villa_w.py` (villa W: 0.25 drawn vs 20 scheduled = CONFLICT with its hand
  per-trade readings; adverse: edges 1 / 3 deg apart NON_PARALLEL, equidistant label AMBIGUOUS, a label in a panel
  strip refusing the strip, two marks on one band, any chosen width refused (larger / smaller / schedule / drawn),
  W in cm read as m and 0.20 read as cm refused, missing D / schedule / band never 0, duplicate schedule row, mirror /
  rotation / translation, stacked projection strip, interior line by layer class, arc band from radii) and
  `test_alsenan.py` (the census numbers above).
- Lessons-register row proposed (ERS s.7):

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-24 | Two block walls (GF-W19, GF-W20) cross the GF CB2 band over 0.050 m each and the register has no CB2 piece for either; the CB2 width conflict (D-27) therefore never reached blockwork, and CB10's label stands beside a strip, not beside the band billed as CB10 (T-277) | A width conflict was carried on the concrete line only; the trades that read the same band edges (formwork soffit, slab complement, wall heights under the band) were not given both readings; labels were bound to bands without a stated placement rule | A member-width CONFLICT is carried into EVERY trade that reads the band (beam m3, beam soffit, slab complement, walls crossing under it: strip delta_b x (D - t)); a label binds by a stated geometric rule (inside = centred; else nearest band; outside the slab past a strip = two readings), never by the schedule (any villa) | tests/t277_beam_width_census (normal: drawn 0.25 vs W 20 with its per-trade readings; adverse: larger width picked, cm as m, wrong-band label, non-parallel edges) | PROPOSED (T-277 READY) |

## 9. What is not done / uncertain

- Lengths and depths are the ledger's (not re-measured); only widths are this census's own.
- Which drawn face would move under the schedule width is unknown (designer): every face-dependent effect is a range.
- Walls: only centrelines are overlaid (thickness 0.15 / 0.20 inside both widths for the along-walls, checked by the
  centreline only); openings at a crossing strip are not checked (the four strips lie in no stretch the V2 run splits out as
  not-wall; door / window positions along those walls are not overlaid).
- The 2F sheet has no conflict; the GF annex roof (no slab plan of its own) is outside this census.
