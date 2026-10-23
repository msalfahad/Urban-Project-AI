# T-227 Blockwork resolution 3/4: annex datum, lift walls and openings, the 0.40 strip, dome partitions, window heads

Worker 2 (lane A), 2026-10-23, run session_01Co2Tn7JVW17h4gsuRMDJKS; r2 (narrow rework, Checker 20:14) 20:43-, s.10. Development villa, not an accuracy claim. ERS read;
s.2 steps 1-4 (element first, evidence hierarchy, first principles, reconciliation in units), s.3 (a level mark's
meaning before its arithmetic; build before deduct; an owner fallback kept in its own scope), s.4 (rules + tests), s.7
(lessons row below). Files: research/agents_t227/* and tests/t227_resolution/* only. No engine module, method, rule /
knowledge version, registry, frozen file or released quantity changed; register v1 (T-225) untouched: the changed rows
are in `register_delta.csv` (T-228 builds register v2 from the deltas). Drawings are cited by Drive title / sheet only.

## 1. Result in engineering terms (black + white blockwork, m2 net; statuses of programme s.2)

| Item | Before (register v1) | After (this delta) | Status |
|---|---|---|---|
| Net blockwork with a SOURCE-SUPPORTED figure (all floors) | 252.815 m2 | **380.498 m2 (+127.683, +50.5 %)** (r1: 379.614) | SOURCE-SUPPORTED PENDING INDEPENDENT CHECK; VERIFIED 0 |
| GF white 0.20 | 4.459 | 19.863 (+15.404: GF-W16) | as above |
| 1F white 0.20 | 15.833 | 128.112 (+112.279: 1F-W00 12.863 (r1 11.979), 1F-W06 54.487, 1F-W10 44.929) | as above |
| Opening deductions newly established on held-gross walls | - | GF-W04 +2.730, GF-W10 +1.440, GF-W18 +8.580, 2F-W02 +3.780 m2 | DRAWING-CONFIRMED deductions; nets stay HELD on their gross |
| Annex walls (13 rows, gross figure 167.530 m2, not a quantity) | HELD (Q-54 B) | **HELD, evidence test done: +4.30 is NOT the structural slab** | HELD, missing item named (D-39) |
| Lift walls GF-W08 / W09 / W13 / W14 | HELD (tie beam) | HELD: tie beam required at GF (4.50 > 4.30), section and the '3.00 m' datum printed nowhere | HELD (D-43) |
| Lift openings L-GF-01 / L-1F-01 / L-2F-01 | HELD | HELD: head drawn / printed nowhere; owner door fallback not extended | HELD |
| GF-H01 (0.40 band, 0.60 m) / GF-H02 (0.20 x 0.90) | HELD | HELD: H01 lies under the 0.40 B20 band, no block family, material and base not printed; H02 not re-read | HELD |
| 1F pieces under the two dome openings (10.29 m) | HELD | HELD: nothing drawn over the chords inside the opening; no section cuts them | HELD |

Why the nets rose: the register v1 was built on the T-175 hosts before T-201 / T-207 were merged, so it still held 21
window heads that those merged ledgers had established from the drawn DWF elevations / sections and the current issue
(Checker 07:00: 26 / 29 heights DRAWING-CONFIRMED, 5 VERIFIED; T-207: W11 / W12 1.95 x 2.20). Applying them by Q-73
(each opening by its own width x height) closes four nets whose only hold was the opening and adds established
deductions on four more. Nothing else moved; no default, no freelancer value.

Engine vs freelancer (comparison only, programme s.5; T-225 three-way table): 1F external white 0.20, engine net
established 15.833 -> 128.112 m2 (r2) against his 165.621 m2 (his figure includes a 41.250 m2 projection with no wall run and
one height per floor; two 1F external walls, 1F-W04 and 1F-W05, still HELD in the engine, 1F-W05 closed by T-226 if merged), so the residual is not like for like. Per opening,
his deductions use a flat 2.00 m window height where the drawing gives 1.50 (W24 / W25 on 1F-W06 / 1F-W10: (1.55 + 1.00)
x 0.50 = 1.275 m2 less deduction in the engine; ENGINE_RIGHT, T-201).

## 2. (a) Annex datum: the owner's Q-54 B test (release only if the documents clearly make +4.30 the structural slab)

Physical element: the annex roof slab (GF annex rooms at +0.30) over walls GF-W00, W02, W04, W06, W17, W18, W23, W24,
W25, W26, W27, W35, W36. The block height (Q-60 A) runs from the floor slab top to the underside of the member above, so
both slab tops must be structural datums.

| Source | What it shows | Verdict |
|---|---|---|
| SECTION B-B (Alsenan_Architectural_P7757_Pages_11-12.pdf p.1, read at 500 dpi this run) | the +4.30 marker apex sits on the TOP line of a thin unhatched layer over the hatched roof band (T-214 vector reading of the same band: 0.050 / 0.200) | NOT THE SLAB (finished-roof line) |
| ST7757 dxf.dxf, every text (nested) | no structural level of any slab, no '+4.30', no roof build-up; note 18 gives the slab thickness 0.16 only | SILENT |
| ST7757.pdf (16 pages, T-206; p.8 re-read) | no S.S.L / T.O.S of the annex roof (the p.16 S.S.L values are an N.T.S. template) | SILENT |
| Roof detail | none in either set (Pages_11-12 p.2 is the fence; P7757.dxf has no roof / insulation text; the ST 'INSULATION MEMBRANE' text is a foundation detail) | SILENT |
| sanitary-7757.pdf (T-214) | SLOPE 1 % on the +4.30 roof: a constant drawn 0.05 cannot be its build-up | NOT THE SLAB |
| Elevations (T-063 / T-200) | +4.30 roof, parapet +4.80 ('480'), same convention as the finished terrace levels | FINISHED LEVEL |
| Annex heads (T-201) | W04 / W08 heads +2.80: they fix the openings, not the slab | SILENT |
| Annex floor (T-214) | drawn dry layer 0.05 under +0.30: floor slab top +0.25 | FLOOR ESTABLISHED |

Result (UP-MAS-DATUM-001 R3 / R4): the documents positively show +4.30 as a finished roof line above a build-up and
print no structural level, so 4.30 - 0.30 = 4.00 is not a slab-to-slab height. All 13 annex rows stay **HELD**; the
missing item is the annex roof structural slab top (or the roof build-up at the walls), designer item D-39. Each wall
height is then (+4.30 - b_roof) - 0.25 - member depth; the register's carried figures equal the case b_roof = 0.05.
Sensitivity (information only): 0.478 m2 of gross per cm of b_roof over the 47.83 m of annex run. No owner question:
ERS s.2.7 is not met (an unprinted design value, a designer item; the owner's rule Q-54 B already decides what to do).

## 3. (b) Lift walls and openings

- Tie beam (ST7757.pdf p.8 note 19: beams tie the lift columns at 3.00 m where the storey is higher than 4.30 m, round the
  lift): GF storey 4.50 > 4.30, so it is required at GF only (1F / 2F 4.20). Its section is printed on no sheet (p.8 note
  only; p.14 lift detail, every plan and schedule: T-204 + this run's full ST text search), and '3.00 m' is not tied to a
  datum (top, axis or soffit; above FFL or slab). The four GF lift runs stay HELD; smallest held quantity = the strip on
  the 5.50 m of clear run between column faces (T-204) x the tie-beam depth (UP-MAS-TIEBEAM-001; designer D-43).
- Lift landing openings L-GF-01 / L-1F-01 / L-2F-01 (1.00 m drawn): no head on any sheet (section A-A draws the stairs and
  no lift landing; B-B's 1F doors are two leafed 0.90 doors, T-201; no elevation sees the shaft). The owner's Q-55
  fallback (internal door 2.20 m, ASSUMED) is scoped to internal doors; a lift entrance is a supplier / designer item
  (like the pit depth on ST p.14), so the fallback is not extended (UP-OPEN-LIFT-001, ERS s.3). Nets of GF-W08 (11.615 ..
  15.365), 1F-W07 (5.891 .. 9.341) and 2F-W00 (3.040 .. 6.840) stay bounds, not quantities. What is built above a
  leafless shaft opening is the same open item (the head).

## 4. (c) GF-H01 and GF-H02

GF-H01: the architectural plan draws a 0.40 band (both sides exterior, 1.40 m with a 0.80 column inside, 0.60 m outside
it) beside the entrance; mapped into the ST frame (T-108 GF translation) it lies exactly under the 0.40-wide B20 band of
the GROUND FLOOR ROOF SLAB plan. 0.40 is no block family (supplier sheet 0.10 .. 0.30, Q-60), no sheet prints its
material, and its base (court +0.15 or entrance landing +1.00) is not fixed: section A-A cuts 0.95 m west of the column
and looks west, away from it. HELD on material and base (UP-MAS-BAND-001; never booked as block or concrete). GF-H02 (a
0.20 x 0.90 outline on the furniture / stair layer at the external stair landing, hand census T-143) was not re-read on
the plan this run (no V2 run carries it); it stays HELD with its item named.

## 5. (d) 1F partitions under the two dome openings

The FIRST FLOOR ROOF SLAB plan draws both dome openings (circles r 2.211 / 2.411 m, radial 'SEE DETAIL'); the 1F plan
draws partitions crossing inside the circles (e.g. the bath / living partition crosses the eastern opening on a chord of
about 2.9 m, matching the 2.98 m piece). The ring B4 is on the circle edge only (Q-44 A); nothing is drawn over the chord
inside it; section B-B draws the domes beyond the cut (the 1F roof band is continuous in that view) and no section cuts
these partitions. The six pieces (1F-W11 4.01, 1F-W13 2.98 + 1.40, 1F-W17 0.44, 1F-W18 0.44, 1F-W24 1.02 = 10.29 m,
T-226 PIECE_RESOLUTION) stay HELD: no top (UP-MAS-VOID-001), never the storey height. This holds in both dome scenarios
(S0 domes, S1 open skylight).

## 6. (e) Window heads in the register

| Wall | Openings closed (area m2) | Deductions before -> after | Net |
|---|---|---|---|
| GF-W16 | W09 2.250, W10 1.500 | 0.000 -> 3.750 | **15.404** (gross 19.154) |
| 1F-W00 | r2: W16 4.363 and W15 4.805 -> 4.363 (arched outlines, s.10; r1 took W16 4.805 from T-201) | 5.885 -> 9.806 (r1 10.690) | **12.863** (r1 11.979; gross 22.669) |
| 1F-W06 | W19 0.480, W20 0.480, W24 2.325 | 0.000 -> 3.285 | **54.487** (gross 57.772) |
| 1F-W10 | W21 / W22 / W23 0.480, W25 1.500 | 0.000 -> 2.940 | **44.929** (gross 47.869) |
| GF-W04 | W04 0.480, W08 2.250 | 1.980 -> 4.710 | HELD (annex gross; 14.302 on the figure) |
| GF-W10 | W05 / W06 / W07 0.480 | 1.980 -> 3.420 | HELD (gross); with T-226's 50.845 (READY, not merged) it would be 47.425 |
| GF-W18 | W11 / W12 4.290 | 0.000 -> 8.580 | HELD (annex gross; 11.245 on the figure) |
| 2F-W02 | W27 1.500, W28 0.480, W29 1.800 | 0.000 -> 3.780 | HELD (gross: unlabelled spans, T-226) |

Still HELD openings (not heads this package can read): A-GF-01, A-1F-01 (arches), D-GF-07 (render vs plan, D-53),
D-GF-14, P-GF-01, P-1F-01 (T-222), the three lift openings; W02 has no block run in this register.

## 7. Rules (proposed, every villa; `datum_rules.py`) and tests

UP-MAS-DATUM-001 (a level mark is a slab datum only when printed or drawn for its own zone type; never a roof with
falls), UP-MAS-HEADS-002 (heads from merged DRAWING-CONFIRMED / VERIFIED ledgers only; width x height checked), UP-MAS-
TIEBEAM-001, UP-OPEN-LIFT-001, UP-MAS-VOID-001, UP-MAS-BAND-001. tests/t227_resolution: 23 tests on villa T227-K (not
Alsenan): printed S.S.L, printed build-up, drawn floor layer; adverse: a roof mark taken as the slab without a slab
level refused, a constant layer on a roof with falls refused, a layer carried to another zone refused, negative
build-up, frame size offered as the opening area, deductions beyond the gross, held head / held gross never forming a
net, opening order permuted (mirror); lift fallback scope; development-villa delta reconciliation (net = gross -
deductions, held never 0, annex / lift rows stay HELD) and `alsenan_t227.py --check`.

Lessons register row (proposed):

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | 126.799 m2 of block net stayed HELD in register v1 on 21 window heads that two merged ledgers (T-201, T-207) had already established | The register was built on the opening ledger of the day before (T-175 hosts) and no step re-read the newer merged head ledger; a resolved input did not propagate | A register / ledger built from merged inputs re-reads every newer merged ledger of the same element (here: opening heads) before it is handed in, and lists the ledger versions it used (every villa, every register) | tests/t227_resolution (heads applied only from established ledgers; net reconciles) | proposed |

## 8. For the Checker (re-measure from the drawings, every wall whose class rises: GF-W16, 1F-W00, 1F-W06, 1F-W10)

1. Length and height of each of the four runs: as in register v1 (T-108 r2 pieces; the delta does not change them).
2. Openings: W09 / W10 on SECTION A-A (sheet10, pantry wall beyond the cut); W16 against W15's printed 300 + 10 on the NW
   frame of P7757.dxf; W19 / W20 / W24 on the NE elevation (p7757_arch_sheet09.pdf); W21 / W22 / W23 / W25 on the SW
   elevation (Pages_07-08 p.7). Deduct width x height (Q-73).
3. Annex: B-B on Pages_11-12 p.1 (the +4.30 marker on the top of the thin layer over the hatched roof band); confirm
   that no ST sheet prints an annex roof level.

## 9. Not done / uncertain

- GF-H02 not re-read on the plan (no V2 run); the arches A-GF-01 / A-1F-01 and the lift openings stay HELD.
- White block units (T-176 products) on the four new nets not recomputed (white units HELD in v1; T-228).
- The joint GF-W10 net depends on T-226 merging first.

## 10. r2 (Checker 20:14 narrow rework): W15 / W16 are arched openings, deducted by their true outline

Element first (ERS s.2.1): W15 and W16 are two windows in the 1F external white wall 1F-W00 (NW face). Each wall opening
is a jamb rectangle with a round-headed arch; outside it, on the wall face, a 0.10 surround band runs down both jambs and
round the arch. The window frame sits inside the opening. r1 took W16 = 1.55 x 3.10 = 4.805 from T-201 (and register v1
already carried W15 at 4.805 from T-175): both read the printed '300 + 10' to the crown of the band and applied it as a
rectangle.

Own re-measure this run (not the Checker's number as the expected value): Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55), NW elevation frame, layer 1. W16: jambs 2566 / 256A, the arch chain
walked end to end from jamb top to jamb top (49 line segments, crown pair 2785 / 2786, no branch once restricted to the
jambs); W15: jambs 2889 / 288A, 46 segments, the same outline translated 2.046 m. Both: width 1.5523, springing 2.1609
above the jamb bottoms (+5.50 floor), crown 3.000 (+8.50 = printed '300'); polygon of the drawn chain (never its chord)
4.3629 m2 = jamb rectangle 3.3544 + arch segment 1.0086. Band chain (12 segments) 1.7523 wide, crown 3.101 (= '+ 10'),
5.092 m2: a wall-face element, not the opening. Checker 4.362 vs own 4.3629: agrees (rounding of the parts).

| Wall / opening | r1 | r2 | Change | Status |
|---|---|---|---|---|
| W15 masonry deduction (merged T-175, summed in v1) | 4.805 | 4.363 | -0.442 m2 (-9.2 %) | DRAWING-CONFIRMED (own polygon), Checker 4.362 |
| W16 masonry deduction (r1 from T-201) | 4.805 | 4.363 | -0.442 m2 (-9.2 %) | DRAWING-CONFIRMED (own polygon), Checker 4.362 |
| W18 (unchanged) | 0.50 x 2.16 = 1.080 | 1.080 | 0 | DRAWING-CONFIRMED (T-150 printed) |
| 1F-W00 deductions | 10.690 | 9.806 | -0.884 m2 | |
| 1F-W00 net = 22.669 - 9.806 | 11.979 | **12.863 m2** (2.573 m3 at 0.20) | +0.884 m2 (+7.4 %) | SOURCE-SUPPORTED PENDING INDEPENDENT CHECK |
| W15 / W16 window line (Q-32 A, NOT this package's line) | - | 1.55 x 3.00 = 4.650 each (printed width; drawn 1.5523 x 3.000 = 4.657) | | FREELANCER_RIGHT on window area (Checker 20:14); lane I / T-238 |

GF-W16 15.404, 1F-W06 54.487, 1F-W10 44.929 m2: resubmitted unchanged (Checker 20:14: deductions AGREE).
Who is right on 1F-W00 masonry: neither r1 (4.805, band crown) nor a window-rule rectangle (4.650): the masonry around
the arch spandrels and behind the band is built, so it stays in the wall (Q-73 final). Freelancer comparison: his 1.55 x
3.00 deducts 0.287 m2 more masonry per window than the outline (RULE_DIFFERENCE between the window rule and the masonry
rule; on the window line he is right).

Rule (proposed, `datum_rules.py` UP-OPEN-ARCH-001, every villa): an opening's height is read on the opening line; a
surround band, moulding or stepped reveal is a wall-face element; masonry / plaster / paint deduct jamb rectangle + the
arch segment as drawn (never the chord, never the enclosing rectangle); the window line keeps Q-32 A. Functions:
`arched_opening` (from a drawn profile), `measured_arched_opening` (from measured values; the repository keeps no
drawing coordinate), `check_masonry_deduction` (refuses BAND_CROWN_AS_HEAD, RECTANGLE_FOR_MASONRY, NOT_THE_OUTLINE,
OPENING_HELD). `alsenan_t227.py` replaces the merged T-175 block deduction of any arched opening in a run's v1 sum and
the T-201 head of W16 by the outline; register v1, T-150 / T-175 / T-201 files untouched (their correction for windows
and plaster / paint is T-238's delta).

Tests (non-Alsenan fixture T227-K, r2): semicircular 1.20 x 2.00 + r 0.60 with a 0.10 band: masonry 2.9655 m2 by hand
(2.400 + pi 0.36 / 2), window 3.120; adverse: band crown 3.240 refused, width x crown 3.120 for masonry refused, jamb
rectangle only refused, two-point chord profile refused, profile on the band line refused, a segment larger than width
x rise refused, missing springing HELD (never 0); mirror and mm units invariant; plain 0.60 x 0.80 window = its own
outline; Alsenan delta W15 / W16 4.363, 1F-W00 12.863.

Lessons row (ERS s.7, proposed): | 2026-10-23 | W15 / W16 4.805 vs 4.363 m2 (T-227 r1, Checker 20:14) | the printed chain
'300 + 10' was read to the crown of the 0.10 surround band and applied as a rectangle; r1 also took the merged T-201
head without re-reading the outline | read the opening line first; a band / moulding is a wall-face element; masonry
deducts the true arched outline, the window line keeps Q-32 A (any villa) | tests/t227_resolution r2 adverse cases;
T-238 census of every other arched / banded opening | rework |

Not in r2 (by the Checker's narrow scope): other arched or banded openings (T-238), the window-line and plaster / paint
deltas for W15 / W16 (T-238), the GF-W10 ruling and the D-43 / annex rows (Checker).
