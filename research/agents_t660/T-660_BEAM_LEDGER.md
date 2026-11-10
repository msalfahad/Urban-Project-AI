# T-660 B10-07 beam concrete: the 27 HELD beam lines restated member by member from the drawings

Worker 1 (lane S), 2026-11-09, branch `agents/task-T-660`. Research only: no engine module, candidate line, rule file or
method version changed; nothing released; wiring is T-661. ERS s.2-5, owner Q-61 answer C (member by member), Q-44 A,
R-T402-1 .. 6 (T-402 r2, merged), R-T642. Development villa, not an accuracy claim.

## Sources and run

- Lines: the 27 STR.CONC.BEAM HELD lines of the 10 Nov trial BOQ r4 (`research/agents_t654/out/TRIAL_BOQ_R4_T654.json`,
  per_line): 22 bounded **8.332829 .. 13.684510 m3**, 5 blank (26 candidate V3.0.58 lines + the T-642 companion of the
  released GF BAND0030.2 strip).
- Own re-read this run (Drive 'Alsenan chalet project', 'ST7757 dxf.dxf' and 'ST7757.pdf', read-only, private copy
  only): plan edge lines of every conflict / piece, the four section cuts and their DIMENSION entities (DIMLFAC 0.025),
  the simple-beam schedule block text (p.10), the CB3 supports, the roof-slab plan notes, the architectural sections.
  Every handle is cited in `t660_beams.py`; nothing from a drawing is tracked beyond derived member quantities.
- `python3 -I research/agents_t660/t660_beams.py --write` -> `out/T660_BEAM_LEDGER.json` (one row per line id: class,
  status, before r4, value or bound, plan area, basis, guard).

## Physical element (ERS s.2.1)

A beam piece = drawn plan between the faces of the members that own the crossings x its printed overall depth, slab net
of the beam plan (T-395 / R-T395-1). A strip outside a scheduled beam's outer face with no mark, no bar and no printed
depth is NOT a beam by being drawn on the beam layer (R-T660-3): its depth is a property of what it is (projection,
parapet base), which the structural set refers to the architect ('CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE
CASTING' on all three roof-slab plans).

## Result (m3; 27 lines, each once)

| Class | Lines | Before r4 | After | Status | Basis |
|---|---|---|---|---|---|
| Piece past column 335 (GF, B24 band east) | 1 | 0.375 .. 0.5625 | **0.549624** | VALUED_AS_DRAWN (proposal) | D-D crosses it: 55 + 20 = 0.75 closing the outline, round 20 x 20 (two extents); plan 274 / 277 = 0.500; column 335 face .. end line 2A8 = 1.500 (R-T660-1) |
| Width conflicts GF B29, CB2 x2, B21; 1F B6, CB10 x2 | 7 | 5.144829 .. 6.111010 | same | HELD bounded | widths re-measured = T-402 handles (0.200 / 0.250 / 0.400 / 0.200 / 0.300); no cut crosses any; net concrete shift schedule - drawn **+0.175 .. +0.355** with slab pairing (R-T660-5) |
| Two marks GF CB3 / 'B3 (With Stair)' | 1 | 0.212 .. 0.3975 | same | HELD bounded | never both (Q-61 C(2)); evidence below |
| Unlabelled pieces past a support (1F x1, 2F x4) | 5 | 0.626 .. 1.879 | 0.626256 .. 1.878768 | HELD bounded | breadth-0.20 schedule rows 0.40 .. 1.20 x face-to-face length (R-T660-2); length term +0.000256 / -0.000232 |
| GF BAND0030.2 companion (T-642) | 1 | 0 .. 0.025 | same | HELD bounded | B4 0.50 released, B7 0.75 alternative |
| Projection strips / boxes (GF 3, 1F 7, 2F 1) | 11 | 7 bounded 1.975 .. 4.7095 (beam-schedule envelope) + 4 blank | **no m3 bound**, plan **6.947 m2** | HELD_NO_DRAWN_DEPTH | R-T660-3; the r4 range kept beside, labelled 'not drawn' |
| East dome ring (1F) | 1 | blank | blank, plan 1.799 m2 | HELD_NO_DRAWN_DEPTH | no B4 mark on it, dome detail depth 'AS PER ARCH' (Q-61 C(3)) |

Totals: before 22 bounded 8.332829 .. 13.684510 + 5 blank -> after **1 valued 0.549624 + 14 bounded 5.983085 ..
8.412278 + 12 held with plan area 8.7464 m2 and no drawn depth**. Reconciliation (exact, in the JSON): 8.332829 =
5.983085 - 0.000256 + 0.375 + 1.975; 13.684510 = 8.412278 + 0.000232 + 0.5625 + 4.7095. Valued + bounded: **6.532709 ..
8.961902 m3** (was 8.332829 .. 13.684510): the high end falls 4.722608 = 4.7095 of beam-schedule envelope applied to
strips whose depth no sheet prints (T-402 P1, never actioned) + 0.012876 the D-D round + 0.000232 length; the low end
falls 1.800120 = -1.975 set aside + 0.174624 the valued piece above its old low + 0.000256 length.

## Findings this run

1. **Sections A-A / B-B (re-read)** cross the GF / 1F 0.20 strips but draw ONLY B20 (59A '40', 5A8 '75') / B23 (16EA
   '45', 16F8 '75') with their 20 x 20 upstand on the outer half (upstand lines 55F / 7BC 0.20 inside the outer face);
   the schedule rows B20 40x75 11T18 / 11T18 and B23 45x75 11T18 / 11T18 equal the sections. The outline ends at the
   beam's outer face and no slab is drawn either side: the strip is neither shown nor excluded (Q-61 C(5) stays open).
2. **Parapet footprint candidate (new, double-count guard)**: the outer 0.20 strips (rounded corners, on the street and
   neighbour perimeter) sit where the architectural sections draw the cast parapets in the slab hatch (T-311), and the
   roof plans refer parapets to the architect before casting. If the parapet family (T-311 / T-659, MISSING today) is
   measured along that perimeter from the slab top, a strip valued in the beam family as well would be counted twice.
   Each strip carries the guard 'valued in ONE family only'.
3. **CB3 / B3** (evidence, R-T660-4): the p.11 CB3 row is a continuous THREE-span beam with printed spans 3.4 / 3.3 /
   3.8; the drawn band has three spans, c/c 3.670 / 3.350 / 3.850 (carrier 60.593 / 61.093, columns 37F, 373, 385): span 2
   and 3 within 0.05, span 1 +0.27. 'B3 (With Stair)' is a plan annotation 0.15 m north of span 2 at the stair landing.
   Under B-S18 (schedule over plan annotation) the CB3 reading 0.3975 is the drawing-preferred one; Q-61 C(2) holds it
   until the Checker confirms the cross-reference (B-S18 owner condition 1). Not selected here.
4. **East dome ring**: the dome detail (ST p.7, N.I.S.) dimensions the ring depth with 182F whose text is overridden
   'AS PER ARCH'; the dimension's own measurement is 3750 x DIMLFAC 0.02 = 0.75, an indication on a not-to-scale detail,
   inadmissible as a quantity (R-T402-6 spirit: the sheet SHOWS 'AS PER ARCH'). The ring stays held with plan 1.799 m2;
   the architect's dome section is the missing fact.
5. **BM-GF-059 value** on exact edges 0.500 x 1.500: 0.549624 (= Verifier's T-402 re-measure; T-402's 0.549284 used
   0.4996 x 1.5003). The column 335 outline (0.50 x 0.25, x 71.4634 .. 71.9634) and the piece do not overlap.

## Owner manual method beside the drawing-derived method; freelancer (quantities only)

| Item | Owner / freelancer method | Drawing-derived | Verdict proposal |
|---|---|---|---|
| GF piece past column 335 | his 0.5 x 0.75 x 1.501 = 0.562875 (T-545) | 0.549624 (round printed, f2f 1.500) | ENGINE_RIGHT -0.013251 (round -0.012876, length -0.000375) |
| Width conflicts | the schedule width on every row (T-402) | pair of readings + slab pairing | UNRESOLVED (designer D-27 / D-02) |
| Unlabelled pieces | the neighbour's section continued | breadth-0.20 schedule envelope | RULE_DIFFERENCE (Q-61 C(4)) |
| Projections / ring | no row | held, plan area | UNRESOLVED, not comparable |

## For the Checker (re-measure 5)

1. BM-GF-059: D-D chain 1785 / 1777, round 1777 / 17A3, edges 274 / 277, column 335, end 2A8 -> 0.549624.
2. GF B29 width 463 / 2CE = 0.200 and 1F CB10 5E7 / 5E8 = 0.300 (+ outer strip line 5E5).
3. GF B21 433 / 434 = 0.400 square to the inclined axis (-80.949 deg).
4. CB3 supports and c/c spans (finding 3).
5. A-A / B-B outlines end at the beam's outer face (finding 1).

## Rules, tests, lessons row (proposed)

`t660_rules.py` R-T660-1 .. 6. `tests/t660_beam_ledger`: hand villa V660 (piece 0.30 x 0.60, round 15 x 15, 2.40 m ->
0.420412; envelope of the drawn width only 0.200 .. 0.360; projection held with area; two marks never summed; span
cross-check evidence only; net shift with slab pairing; piece / column owned once under mirror and rotation) with
adverse cases (no crossing section, open chain, empty chain, unequal round, mm, missing width, width with no row,
projection with a mark / bars / depth, zero reading, duplicate id, HELD as 0, low > high); development villa from
committed files (27 r4 ids once, exact reconciliation, BM-GF-059 by hand, no freelancer text).

Lessons row (ERS s.7): | 2026-11-09 | 7 edge strips carried a beam-schedule depth range (1.975 .. 4.710 m3) in the trial
BOQ | a band on the beam layer was taken for a beam | a strip outside a scheduled beam's face with no mark, bars or
printed depth is held with its plan area and no m3 bound, listed beside the parapet family with a one-family guard
(every villa; provenance T-660, R-T660-3) | tests/t660_beam_ledger | PROPOSED |
