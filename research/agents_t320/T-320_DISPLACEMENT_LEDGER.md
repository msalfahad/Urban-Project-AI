# T-320 Backfill (B1-03) and disposal (B1-04): the buried-structure DISPLACEMENT ledger

Worker 1 (lane S), 2026-10-28, run session_01E6cPnbaB4TFV1B12DcgfKx. Development villa, not an accuracy claim. ERS
s.2-4 and s.7 applied. Research only: no engine module, method version, route G, rule / knowledge file or released
quantity changed. New: `displacement_ledger_v1.py` (DISPLACEMENT_LEDGER_V1, unwired, stdlib), `t320_alsenan_check.py`
(reads ONLY merged research ledgers, no drawing re-read) -> `LEDGER_T320.csv` (one row per component), `summary.json`;
tests `tests/t320_displacement_ledger/` (17 pass: non-Alsenan hand fixture villa T320-M + development-villa closure).

## 1. The physical element (ERS s.2.1)

BACKFILL is the soil returned into the excavation around the buried structure, from the formation up to the
**existing ground EG = natural ground +-0.00** (T-170 / T-253, Checker Gate A on the five D-35 readings: the courts'
+0.15 is paving laid ON natural ground, so the finished ground outside is a finish on EG, not a higher backfill top).
Backfill = excavated - displacement, where displacement is everything inside the excavation that is not returned soil:
blinding, underlay, footings, straps, the part of a neck / beam / wall BELOW EG, pit and pool shells and the VOIDS they
enclose (the pool water space is not backfilled). Two things are NOT this element:

- any part of a component ABOVE EG (refused by the module, reported as `above_EG_excluded_m3`);
- **zone Z2**, the fill placed above EG under the GF ground slab (EG +-0.00 -> slab underside +0.85 on dry floors,
  T-214): it is not "returned" into an excavation, it is bounded by the ground-beam faces, and its displacement is the
  ground beams, the necks above EG and the under-beam blinding. Named for lane I, not formed here (its gross needs the
  enclosed plan and the wet-floor b, T-221 / T-214).

The drawing prints the material: "Well graded clean compacted fill from excavation material" (p.13 x2, p.14; T-170):
the backfill and the Z2 fill both come from the excavated soil, so disposal = excavated x bulking - (backfill + Z2
fill re-used). Bulking: no answered rule (OWNER_QUESTIONS_ANSWERED / DECISION_REGISTER searched; Q-21 C lists
excavation, disposal, replacement fill, compaction and backfill as separate measures and gives no factor) -> HELD; the
module refuses a factor without an answered rule.

## 2. Level basis (what is a value, what is a bound)

| Datum | Value | Status |
|---|---|---|
| EG | +-0.00 | DRAWING-CONFIRMED (T-170 / T-253) |
| Formation (footing pits) | AT_MOST -1.50 (p.9 note 1, 'not less than 1.5 m'); F = -1.50 - d, d >= 0 HELD (Q-21 C / OQ-13) | HELD (bound) |
| Pit chain above F | blinding 0.10 / underlay 0.07 / footing H (T-206 VERIFIED, p.9) | DRAWING-CONFIRMED (relative) |
| Footing top | <= -1.33 + H: <= -0.63 for every type (F12 H 0.70) | so every pit's blinding, underlay and footing lie WHOLLY below EG for any d: their volumes do not depend on the formation |
| Pool formation | -1.50 = rim +0.30 - 1.20 - 0.40 - 0.05 - 0.05 - 0.10 (T-183 r2) | DRAWING-CONFIRMED |
| Main exterior GB bottom | on the outer normal ground +-0.00 (FOLLOW ARCH., D = 0.95) | DRAWING-CONFIRMED (T-253 Gate A) |
| Main interior GB | top +0.95 (dry), D <= 0.60 -> blinding bottom >= +0.25 | ZERO_BY_BOUND (condition: under a wet floor b <= 0.30) |
| Annex GB | top +0.25; interior D 0.30 .. 0.60 -> soffits to -0.35 (T-230) | below EG: HELD on D-34 / D-33; exterior CONFLICT (D-35 annex) |
| Lift pit floor (FF top) | 'as per lift manufacturer' (p.14, T-204) | HELD |

## 3. The ledger, Z1 (development villa; LEDGER_T320.csv per component, summary.json per pit / trench)

| Component (count) | m3 below EG | Status | Source |
|---|---|---|---|
| Pit blinding, 24 pits, net of F9 / FN and F8 / FN | 12.9234 = 12.7344 inside the plot + 0.1890 beyond the plot line | DRAWING-CONFIRMED / D-14 part HELD | T-170, T-233 |
| Pit underlay, 24 pits, net of F9 / FN | 7.6895 | DRAWING-CONFIRMED | T-170, T-219 (109.85 m2) |
| Footings, 24 pits, net of F9 / FN (0.14 x 0.30) | 52.9190 | DRAWING-CONFIRMED | T-170, T-233 |
| Necks below EG, 29 with a printed section on a known footing | **>= 4.3278** at d = 0, **+ 4.86 m3 per m** of d | HELD (AT_LEAST bound) | T-205 (A x (1.33 - H + d)) |
| Necks: C8 10E0 section conflict | 0.1992 .. 0.2241 at d = 0 | CONFLICT | T-205 |
| Necks: C10 + C on F10 / F; C1, C2 x2, C9 on the lift FF | range / no value | HELD | Q-31 C; pit depth |
| Straps SB1 / SB2 / SB3 outside the footings | 3.3905 | DRAWING-CONFIRMED (volume) | T-174 / T-230; below EG because each end is cast against a footing face whose top is <= -0.83 (strap top < -0.33) |
| Straps: SB3 in F3, SB1 in F10 + F, strap blinding | 0.0295 .. 0.2683; 0 .. 0.385; 0 .. 0.913 | HELD | T-233 (D-15, Q-31 C) |
| Main exterior ground beams (17 runs) | 0.0000 (bottom on N.G.; 15.960 above EG excluded) | DRAWING-CONFIRMED | T-253 |
| their blinding (p.13 10 / 30 / 10), -0.10 .. 0.00 | 2.7996 (55.99 m x 0.50 x 0.10) | DRAWING-CONFIRMED | T-253 / T-233 finding 2 |
| Main interior ground beams + blinding, 13 runs (5 CALCULATED, 6 D-34, 2 end-conflict) | 0.0000 | ZERO_BY_BOUND | T-242 |
| Main interior D-33 runs (13, incl. 4 also D-34) | no value (zero while D <= 0.85) | HELD | D-33 |
| Annex interior runs (6) | 2 D-34: range (beam (D - 0.25) b L + blinding, wholly below EG); 4 D-33: no value | HELD | T-242 |
| Annex exterior runs (9) | reading L: beam 0 + blinding only; reading S: no value | CONFLICT (D-35 annex) | T-253 s.3 |
| Court runs (3) | no section | HELD | T-253 s.4 |
| Lower ground-beam row (p.13 two-beam detail) | exists only if 2.28 + d > 2.50 (d > 0.22 m); drawn on no plan | HELD (conditional) | T-205 / T-042 B3 |
| Upper boundary G.B at N.G., 44.07 m x 0.20 x 0.40 | 3.5256 | DRAWING-CONFIRMED (the hidden 20 x 30 columns change the line split, not the solid) | T-253 |
| Lower boundary band, brick below N.G., pads | 5.639 .. 11.033; no value | HELD (Q-28) | T-233 / p.14 |
| Pool envelope (offset 0.10: screed + membrane), -1.50 .. EG | 18.3251 = 17.7766 inside the plot + 0.5486 beyond (back face on the boundary-wall line) | DRAWING-CONFIRMED / beyond part HELD | T-183 r2 |
| Pool blinding beyond the membrane line | not printed | HELD | T-183 B (>= 1.222) |
| FF lift footing, its blinding, underlay, pit shell + void | 0 .. 11.385; 0 .. 2.256; no value; no value (4.89 m3 per m of pit below EG) | HELD | T-233, T-204 |
| F10 + F (1B1B) footing / blinding / underlay | 2.176 .. 2.275 / 0.5025 .. 0.590 / 0.3185 .. 0.3248 (wholly below EG in every reading) | HELD (Q-31 C) | T-233 |
| **Z1 established** | **105.1630** (+ 4.86 m3 / m of d; AT_LEAST because of the necks) | | |
| Open shared volumes (never netted silently) | F8 / pool 0 .. 1.1211 (CONFLICT); band ends / pool layers 0.008 x 2; lower band / pool back wall (Q-28) | CONFLICT / HELD | below |

Pool envelope decomposition (summary.json `pool_decomposition`, closes to 1e-6): base 4.3742 + walls below EG 2.1211
(+ 0.7070 above EG excluded: 2.8281 = T-183 walls) + water space 7.2920 (VOID) + floor build-up 0.4289 + screed
0.5784 + 0.8226 + membrane 0.6108 + 0.8754 + blinding at the membrane line 1.2217 = 18.3251 = 12.216759 m2 x 1.50.

## 4. Closure (acceptance 1)

| Against | Merged figure | This ledger | Residual |
|---|---|---|---|
| T-170 F-T170-01 net, blinding / underlay / footings (24 pits) | 12.9234 / 7.6895 / 52.919 | 12.923438 / 7.689500 / 52.919000 | 0.000 (netted 0.0336 + 0.0098 + 0.0420 = the F9 / FN and F8 / FN overlaps, found by the module from the outline positions) |
| T-233 CONC.FOOTING measured | 64.304 | 52.919 + FF 11.385 | 0.000 |
| T-233 CONC.BLINDING measured | 14.990438 | 12.923438 - D-14 0.189 + FF 2.256 | 0.000 |
| T-219 underlay area | 109.85 m2 | 7.6895 / 0.07 | 0.000 |
| T-205 necks | 36 drawn | 29 bounded + 1 CONFLICT + 6 HELD | none dropped |
| T-183 r2 pool RC | 7.202 | base 4.374 + walls 2.121 below EG + 0.707 above | 0.000 |
| T-189 F8 / pool plan overlap | 1.2964 m2 | 1.296442 m2 (shapely, 256 segments) | 0.000 |
| T-253 boundary G.B / main exterior runs | 3.5256 / 17 runs | 3.5256 / 17 runs (L sum 55.99 m) | 0.000 |

No component was added that no merged line owns: the only non-concrete items are the pool's p.7 layers (T-183 lines I),
the GB blinding (T-233 ground-beam blinding, reading R), and the pool water space (a VOID, no line, not soil).

## 5. Methods side by side

| Method | Displacement / backfill | Status |
|---|---|---|
| Owner manual method | Q-21 C: measure excavation, disposal, replacement fill, compaction, blinding, footings, necks and backfill SEPARATELY; do not compute the necks on an unresolved datum; no bulking or working-space rule | applied: necks appear only as an AT_LEAST bound of displacement (never a neck quantity) |
| Released V2.9 / candidate | no backfill / disposal line (B1-03 / B1-04 NOT_IMPLEMENTED, BOQ_FAMILY_MASTER 1.14.0) | NOT_IMPLEMENTED |
| Freelancer | no excavation, backfill or disposal row (T-170 searched) | omitted on his side too |
| Drawing-derived (this task) | Z1 displacement 105.163 m3 established (+ 4.86 / m of d) + named holds; backfill = E - D only when E has a value | E HELD: backfill and disposal HELD BLANK, never 0 |

Verdict proposals: backfill / disposal UNRESOLVED (the excavated side is held on the formation, the working space and
pit-vs-bulk, OQ-13); the displacement side DRAWING-CONFIRMED where listed. Not FREELANCER_RIGHT (no line).

## 6. Findings

1. **F-T320-01 Displacement is independent of the excavation method; excavation is not.** Every pit's blinding,
   underlay and footing lie wholly below EG for any formation (footing top <= -0.63), so 73.53 m3 do not move with d,
   and a pit-vs-bulk choice (OQ-13) changes only the excavated side. Only the necks (4.86 m3 per m of d) and the F8 /
   pool collision depend on d. So lane I can form backfill = E(d, ws, method) - (105.163 + 4.86 d + held items) the
   moment the designer prints the formation.
2. **F-T320-02 F8 collides with the pool at the printed limit (CONFLICT, designer item T-183 interface 1).** F8's
   chain at -1.50 .. -0.83 and the pool base -1.30 .. -0.90 share 1.616 m2 of the pool envelope (1.296 m2 inside the
   outer wall, 2.000 m2 of F8 blinding): 1.121 m3 at d = 0, 0 for d >= 0.67. Counted once only when F8's founding level
   is printed; never netted silently.
3. **F-T320-03 Merged ledgers disagree on the FF blinding**: T-233 2.256 m3 (outline + 0.10, AGREE) vs T-170 HELD
   (p.14 projection not dimensioned). Both kept; the Checker rules which reading p.14 supports.
4. **F-T320-04 The main-house ground beams displace almost nothing below EG**: exterior beams stand ON natural ground
   (only their 0.10 blinding, 2.800 m3, is below EG); interior ones and their blinding are wholly above EG on the dry
   top +0.95. Their 15.96 + interior m3 sit in the Z2 fill, a separate element. The annex is the opposite: top +0.25,
   soffits to -0.35, so its runs DO displace backfill (held on D-34 / D-33 / D-35 annex).
5. **F-T320-05 Pool layers on the plot line**: the back face is on the boundary-wall line, so 0.549 m3 of the p.7
   screed / membrane / blinding lies beyond the plot line or in the boundary foundation (HELD, like D-14 0.189).
6. **Boundary band ends**: the upper G.B ends (7FE#3, 7FC#1) meet the pool wall face where p.7 runs 0.10 of layers:
   0.008 m3 each in both unless one stops at the other (HELD, not printed).

## 7. Rule and lessons row (proposed)

R-BACKFILL-DISP-1 (proposed; any villa; provenance T-320, Q-21 C, T-170 R-EXC-LEDGER-1): backfill = excavated -
displacement, where displacement is every solid AND every enclosed void inside the excavation below the existing
ground, each once (3-D intersections netted from positions; a collision of two drawn structures is a CONFLICT, never
netted silently); the part of any element above EG is not displacement (it belongs to the placed fill above EG, a
separate element); a component whose volume is merged but whose level is not printed counts only with a stated reason
it lies wholly below EG; a level known only as a limit gives an AT_LEAST bound with its coefficient per metre; disposal
needs an answered bulking rule (none: HELD). Adoption = a new rule version (lane I / Lead).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-28 | Backfill / disposal (B1-03 / B1-04) missing from both BOQs; the merged 'buried' figures were GROSS (F-T170-01), the pool's water space and its p.7 layers, the F8 / pool collision and the above-EG part of beams were in no displacement account (T-320) | Displacement was never defined as a physical account of its own: buried concrete was taken line by line, so shared volumes, enclosed voids and the EG cut were nobody's | R-BACKFILL-DISP-1 (any villa): every solid and enclosed void below EG once, netted by position, collisions CONFLICT, above-EG refused, limit -> AT_LEAST + coefficient, no default bulking | tests/t320_displacement_ledger (normal: villa T320-M two overlapping pits, neck through EG, beam partly above grade, tank shell + void; adverse: gross sum refused, above-EG counting refused, HELD level as 0 refused, missing EG refused, volume without a below-EG basis refused, default bulking refused, mm units, mirror; development villa closure 0.000 on T-170 / T-233 / T-183) | proposed |

## 8. For the Checker (re-measure)

1. Pick F12 (1ABF): blinding 4.60 x 3.40 x 0.10 = 1.564, underlay 14.08 x 0.07 = 0.9856, footing 9.856, neck C3
   (10CD) 0.15 x (1.33 - 0.70) = 0.0945, neck C7 (10C9) 0.24 x 0.63 = 0.1512: pit 12.6513 m3 (summary.json groups).
2. Pool: A10 = 10.935564 + 12.497787 x 0.10 + pi 0.01 = 12.216759 m2 x 1.50 = 18.3251; F8 in the envelope (T-189
   frame: F8 x -2.2502 .. 1.7498, y -4.85 .. -1.25) 1.6160 m2 footprint / 2.0000 m2 neat.
3. Main exterior blinding: 17 T-253 runs, sum L 55.99 m x 0.50 x 0.10 = 2.7996.

## 9. Not done / uncertain

- Zone Z2 (fill above EG under the GF slab) not formed: needs the enclosed plan, the wet-floor b and the D-33 / D-34
  sections; its components are named above.
- The GB blinding beside the neck faces (the 0.10 projections past a beam end at a neck) is not netted per neck:
  face-to-face run lengths are used (T-242 basis); small, named.
- Drainage (manholes, pipes, sanitary-7757.pdf) is outside this structural ledger, not read this run; no buried tank,
  septic tank or sub-base is in any merged ledger (none established, not assumed absent).
- No candidate line, no wiring (lane I).
