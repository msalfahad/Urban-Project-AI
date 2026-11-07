# T-585: skirting follow-ups of T-574: yard faces one by one, stair flights along the pitch, pieces in nr

Worker 2, 2026-11-07, lane A, non-candidate (research only: no engine, rule / knowledge version, registry, frozen or
candidate file changed; nothing released; released default V2.9 + route G unchanged). Files: research/agents_t585/* and
tests/t585_skirting_followups/* only. Development villa; not an accuracy claim. ERS read: s.2.1, 2.2, 2.4, 2.7 (no owner
question: the open finishes are already with the owner as OD-1; nothing contradicts), s.3, s.4, s.7.

## 0. What was read (Drive "Alsenan chalet project", read-only; private copies in .work/private only)

| Source | Read for |
|---|---|
| P7757_DXF_COMPRESSED.zip (architectural DXF) | GF yard face (T-147 `rooms.py`, box = plot-wall inner faces, as T-153): 177.1109 m2, perimeter 98.629 lm; every boundary stretch sampled at 5 mm and hosted on its entity (layers 1 / S-COL.BON / W / 5, door blocks); lengths from the entity ends (handles in YARD_FACES_T585.json); 268 text strings; both elevations |
| p7757_arch_sheet03.pdf | GF plan, court read at 150 dpi (raster, no text layer): names, levels +0.15 / +0.30, dimensions, section marks only |
| merged ledgers | T-501 LINES (flight pieces), T-574 out JSON (table restated), T-404 (fence faces), T-153 / T-157 (court split, porch envelope 4.60 x 4.30), T-412 (E1 +0.15 -> +1.00) |
| his register (numbers only) | yard row: C13 81.32 lm, D13 151.80 m2, G13 '=C13' |

**No sheet prints a base.** DXF: 0 of 268 strings names a skirting, base, plinth or finish; the NW / SE elevations draw
the wall feet with ground / slab lines only; sheet 3 prints no finish note in the court; T-404: no hatch, base or note
on any fence face (p.12); T-091 / T-360 / RFI-B-A12 (no finishes schedule or specification).

## 1. Physical element and rule (R-T585-1, `t585_rules.py`, every villa)

A yard skirting exists only where an established outdoor finish meets a wall face AND a base is printed or drawn.
Hosts: FENCE, WALL, SILL_WINDOW (range [0, L]); DOOR / GATE / OPEN_EDGE / FLOOR_GLAZING (no wall foot, 0 by geometry);
UNDRAWN (bound). Classes: DRAWING-CONFIRMED (finish + base note), NOT_IN_DRAWING (finish, no base: 0 lm measured, the
wall-foot length named beside), UNRESOLVED (floor finish HELD: bound [0, L], never 0). No finish at all: refused. Stair
flight: pitch = hypot(plan going, rise) per WALL side, zigzag kept beside (ORR-007), winder bound by convexity.
Pieces: nr, lm only with a printed piece length.

## 2. Yard faces (YARD_FACES_T585.json, out/T585_SKIRTING_FOLLOWUPS.json; 46 faces)

| Zone (floor finish, basis) | Faces lm | wall foot (fence + wall) | under unprinted sills | no face (doors / gates / open / glazing) | Class |
|---|---|---|---|---|---|
| West court (interlock, owner rule) | 38.642 | fence 20.400 (street 5.600, north 14.800) + walls 10.542 (dewaneya 4.442, annex 3.000, house west 3.100) | 3.300 (3A5 0.60, 3B1 1.50, 351 1.20) | G-01 2.500, doors 1.900 | NOT_IN_DRAWING |
| North side walk (porcelain, owner rule) | 32.340 | fence 16.470 + house north wall 12.170 | 2.700 (3FD 0.90, 3 x 0.60) | G-02 1.000 | NOT_IN_DRAWING |
| Covered porch (HELD, OD-1) | 4.000 | 2.800 | - | passage mouth 1.200 | UNRESOLVED 0 .. 2.800 |
| Pool court deck (HELD, OD-1) | 15.8046 | 8.298 (sea wall B7 5.168, columns / walls 3.130) + undrawn 0.512 | - | curved floor glazing 6.9946 | UNRESOLVED 0 .. 8.810 |
| E1 flight + landing (stair-owned, s.3) | 7.700 | 4.700 | - | main door 2.000, pantry door 1.000 | stairs |

Closure: 90.7866 yard + 4.700 + 3.000 stair-owned + 0.1424 polygon residual (mitre / flattening of the rooms.py face at
the dewaneya arc joint, +0.145, less a 0.003 window overlap) = **98.629 lm** = the yard face perimeter.

Totals: **DRAWING-CONFIRMED 0 lm**; NOT_IN_DRAWING wall foot **59.582 lm** (+ up to 6.000 under sills); UNRESOLVED **0 ..
11.610 lm**; no face 13.5946 lm.

vs his 81.32 lm: gap -81.32 = **RULE_DIFFERENCE / FREELANCER_SCOPE** (one SCOPE cause, closes exactly). His figure is the
perimeter typed for his 151.80 m2 paving row (G13 '=C13'), a paving outline, not a wall-face measure. Ours on that basis:
98.629 lm for 177.111 m2 (incl. porch and pool court). His outline is undimensioned: no term-by-term match. Not an
ENGINE_OMISSION: no drawing or owner text puts a base on a court wall (T-574 said UNRESOLVED; this run classes it).

## 3. Stair flights (lm) along the pitch, and E1 landing

The 13 HELD-FORM pieces are restated from an open "HELD >= 17.009" to **two measured forms**: pitch **17.009049** |
zigzag **23.300481 lm** (ORR-007 picks one; never added, never averaged). Pitch re-derived for every piece with levels
(hypot(plan, rise) + returns = T-501 sloped, |diff| <= 2e-6). Held pieces now bounded: MS1-T winders [2.350, 2.620191]
(walls on both sides, rise 0.833 split unknown; was blank); window / opening sides MS1-L.W2 0 .. 1.233936, MS1-U.E2 0 ..
1.052389, MS2-L.W2 0 .. 1.230432; MS1-U.E3b 0 .. 0.350796; RS-S.S0 0 .. 0.232143; RS-C.OUT unbounded (outer band role
unknown). Flight lower bound **17.009 -> 19.359049 lm**.

E1 (ST-03): one wall side (pantry face; the north side is open): pitch hypot(1.20, 0.85) = 1.470544 = T-501 E1.S. The E1
landing (1.40 x 3.70) has drawn walls on three sides: house face 1.700 (main door 2.000 out), stub 1.400, pantry 0.400
(door 1.000 out) = **3.500 lm**, no candidate line: **ENGINE_OMISSION proposal** (PROVISIONAL; same treatment as MS1-LD /
MS2-LD level landing skirting).

## 4. T-574 table restated (lm; every change attributed)

| Group | his | T-574 ours | T-585 ours (range) | gap range | change |
|---|---|---|---|---|---|
| ST-03 E1 | 4.37 | 0 (flight HELD) | 4.970544 .. 5.55 | +0.600544 .. +1.18 | two forms; landing +3.500 (ENGINE_OMISSION proposal); residual UNRESOLVED (his row unsplit) |
| ST-01 main | 23.10 | 10.90 (+ HELD) | 25.488505 .. 41.799082 | +2.388505 .. +18.699082 | two forms 12.238505 / 16.793338; winders bounded; T-574 landing / RFI holds 0 .. 7.45 and step 0 .. 0.168 carried |
| ST-02 round | 2.40 | 1.25 (+ HELD) | 4.55 .. unbounded | +2.15 .. - | two forms 3.30 / 4.457143; RS-C open |
| OUTDOOR yard | 81.32 | 0 (UNRESOLVED) | 0 DC | -81.32 | RULE_DIFFERENCE / FREELANCER_SCOPE (s.2) |
| ROOM | 282.85 | 197.278592 | unchanged | -85.571408 | not in scope |
| PIECES | 96 nr | 0 | unchanged, nr | - | no printed piece length (conversion refused) |

No % (scope / HELD causes, R-T574-1 (e)).

## 5. Verdict proposals, lesson, missing

- RULE_DIFFERENCE / FREELANCER_SCOPE: yard 81.32 lm. ENGINE_OMISSION (proposed): E1 landing 3.500 lm. UNRESOLVED: E1
  residual, ST-01 / ST-02 rows unsplit. 0 ENGINE_WRONG.
- Lane I proposal (no line here): one B7 level line for the E1 landing walls (3.500 lm, ST-03 marble stair); the yard stays
  without a line (NOT_IN_DRAWING) with its 59.582 lm wall foot named for the owner package beside OD-1.
- Lesson (ERS s.7, PROPOSED): "2026-11-07 | a reference's yard skirting equal to its paving perimeter | a perimeter
  includes gates, doors, open edges and glazing and no sheet prints an outdoor base | class each yard face by host and
  floor finish; only a printed base makes a quantity; the wall foot is named, never valued (every villa; T-585) |
  tests/t585_skirting_followups (face without a finish refused, nr to lm refused) | PROPOSED".
- Missing: an independent re-measure; sill heights (6.000 lm range); porch / pool-deck finishes (OD-1); ORR-007 (form);
  S-9 winders; RS-C band; his yard outline.

## 6. For the Checker

1. `python -I research/agents_t585/t585_alsenan.py --check` (byte-identical; pins in the JSON).
2. West court fence: street 5.600 (8.30 outer less G-01 2.50, -0.20 corner) + north 14.800 (plot 31.37 less 16.17 strip
   less the 0.20 + 0.20 wall ends) ; side walk north fence 16.170 = 1.30 x 16.17 strip length (T-153).
3. E1 landing: 0.900 + 0.800 + 1.400 + 0.259 + 0.141 = 3.500; E1 side hypot(1.20, 0.85) = 1.470544.
4. Winders: lo 1.20 + 1.15 = 2.350; hi 1.20 + hypot(1.15, 0.833333) = 2.620191.
