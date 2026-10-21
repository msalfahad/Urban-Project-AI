# T-136 Footing steel by bar population (lane S, gate 3; a checked piece for the V3.0 candidate, not wired)

Worker 1, 2026-10-21. New piece `engine/source/footing_rebar_population_v1.py` (FOOTING_REBAR_POPULATION_V1), tests
`tests/t136_footing_rebar_population/` (12, synthetic villa, hand values), runner `run_t136_alsenan.py`, results
`T136_OCCURRENCES.csv` (one row per footing on the plan) and `T136_COMPONENTS.csv` (one row per footing and bar
direction). Nothing released changes: the piece is opt-in and read by no method.

## What the piece does

1. Reads the footing schedule rows as printed (mark, two plan sides, depth, short / long bars, bottom and top layer):
   count notation `n T d` (also Ø, %%c, the split cells `8 | 12`), per-metre `n T d /m` (`9 | 14/m`), spacing
   `T d @ s` (unit printed in the cell or in the schedule header; neither -> UNREADABLE, held). Empty, merged or
   unreadable cell -> HELD, never 0.
2. Binds each row by mark to the footings route G releases (route G's own FOOTINGS concrete items, passed as data). A
   footing with two marks, a size / type conflict (Q-31 C), an unconfirmed occurrence or a clipped outline -> HELD; a
   mark with no row -> HELD; a row with no footing on the plan -> listed, no steel created.
3. Per footing and direction: bar length = side - 2 x printed cover; count = printed count (RELEASED) or, for per-metre
   / spacing notation, HELD with three readings, because URBAN-REBAR-NET-AND-PROCUREMENT@v1
   (rules/methods/URBAN_METHOD_REGISTER_V3.json:111) gives no count formula: A = ceil(inside-cover side / spacing),
   B = A + 1 (both edge bars), C = rate x full side (fractional). kg = count x length x d^2/162 (rebar_unit_mass).
   Procurement = net while a bar is within the 12.0 m stock length (rule parameter); longer -> procurement HELD (lap
   not printed). Bar ends only from a cited detail; a layer with no cited end stays HELD (straight core shown).
   A printed BOXED cell (single-layer rows) is listed HELD unquantified with its printed text.

## Alsenan inputs (all read from the drawings; nothing typed from the freelancer)

| Input | Value | Where printed |
|---|---|---|
| Schedule rows | 17 rows (12 single-layer FT, 5 two-layer FTB), read from the INSERT attributes of the structural DXF (sha 9f9d1179) | structural PDF p.9 "Schedule of Footings"; cells checked against the PDF by eye, all 17 agree |
| Size unit | cm | p.9 header "FOOTING SIZE (cm)" |
| Cover | 70 mm, worded as a MINIMUM | p.8 general note 22: not less than 2.5 cm in columns, slabs and beams and 7 cm in concrete against soil |
| Bottom bar ends | straight | p.13 "TYP. DETAIL OF ISOLATED FOOTING": long and short bottom bars drawn straight; only the "Boxed bars" are bent |
| Top bar ends (two-layer) | none drawn | no two-layer footing section in the set -> HELD |
| Footings on the plan | 26 route G items (run B, as T-126) | foundation plan (p.2) |

## Result: engine vs route G vs freelancer (kg of footing steel, net)

| Line | kg | Status |
|---|---|---|
| Released, printed counts (19 single-layer footings x 2 directions) | **874.86** | RELEASED at the printed minimum cover |
| Two-layer footings F8, F12, F13, F14, FF (per-metre notation) | **2,742.51 .. 2,836.40** (reading C 2,797.81) | HELD, owner Q-71 (count) + top-bar ends |
| of which bottom layer | 1,606.07 .. 1,655.56 (C 1,635.65) | HELD, Q-71 only |
| of which top layer | 1,136.44 .. 1,180.84 (C 1,162.16) | HELD, Q-71 and top-bar ends not drawn |
| FN at the F9 corner (outline clipped) | 12.23 at full schedule size | HELD, not counted |
| F / F10 footing (two marks, Q-31 C) | not measured | HELD |
| BOXED bars, 20 single-layer footings ("3+4" .. "3+8", FN empty) | not measured | HELD unquantified |
| **Engine total shown** | **874.86 released + 2,742.51 .. 2,836.40 held** = 3,617.37 .. 3,711.26 | |
| Route G today (PROVISIONAL lines) | 3,735.91 | 50 mm STANDARD_PRACTICE cover, fractional per-metre counts |
| Frozen S4 (verified + lower bound) | 887.09 + 2,742.51 (BEST 2,836.40) | |
| Freelancer, footings line | 5,800 (5.8 t typed for 77.63 m3 "footings total") | kg/m3-type allowance; covers footings + straps + perimeter ground beam |

Per mark (route G -> engine): F 39.82 -> 37.69; F2 78.58 -> 76.73; F3 39.82 -> 38.68; F4 124.27 -> 121.78;
F5 160.00 -> 157.01; F6 93.69 -> 92.05; F9 183.90 -> 181.38; F11 111.79 -> 109.57; F15 24.09 -> 23.27;
FN x4 51.20 -> 36.69 + 12.23 held; F8 508.87 -> held 494.50 .. 512.21; F12 721.20 -> held 696.05 .. 716.47;
F13 421.59 -> held 408.89 .. 426.80; F14 442.27 -> held 422.83 .. 439.33; FF 734.82 -> held 720.24 .. 741.58.

## Why the numbers differ (verdict proposals for the verifier)

1. **Route G vs engine on printed counts: 907.16 -> 874.86 kg released, -32.30 kg (-3.6 %) on the 10 single-layer
   marks = -20.07 kg cover + -12.23 kg FN held (item 3).** Route G takes the footing cover from its convention file (REBAR_COVER_FOOTING_M base 0.05 m,
   "STANDARD_PRACTICE, typical general notes"); the project prints 7 cm against soil (p.8 note 22).
   **ENGINE_RIGHT** (hand: F = 8 x (0.80 - 0.14) + 7 x (0.90 - 0.14) = 5.28 + 5.32 = 10.60 m x 12^2/162 = 9.42 kg per
   footing; route G 8 x 0.70 + 7 x 0.80 = 11.20 m = 9.96 kg). The note says "not less than": 70 mm gives the longest
   bar the note allows, so the engine figure is the maximum straight run, never short.
2. **Two-layer footings: route G 2,828.75 kg vs engine held 2,742.51 .. 2,836.40.** Route G counts 9 / m x full side
   (fractional, e.g. 34.74 + 1.26 = 36.0 bars) at 50 mm cover. Which count is right needs owner Q-71: **UNRESOLVED**.
   Hand check, F8 bottom short bars "9 ø 14/m", footing 400 x 360: bar 3.60 - 0.14 = 3.46 m, spread over
   4.00 - 0.14 = 3.86 m: 9 x 3.86 = 34.74 -> A 35 bars 146.52 kg, B 36 bars 150.70 kg, C 36.0 bars 150.70 kg.
3. **FN at the F9 corner: route G and S4 give it full steel; the engine holds 12.23 kg.** The drawn FN outline
   (100 x 100) overlaps the F9 outline by 0.40 x 0.35 m (route G clips FN's concrete to 0.258 m3). Where FN's bars
   stop inside F9 is not drawn. **UNRESOLVED** (designer RFI; 12.23 kg, 0.3 % of the footing steel).
4. **Freelancer 5.8 t vs engine 3.62 .. 3.71 t**: not like for like. His line is one typed tonnage for "footings
   total" 77.63 m3, which also holds the strap beams and the perimeter ground beam, with no diameter or footing split
   (S4 post-freeze record). **RULE_DIFFERENCE / scope**; no % is claimed. The footing part of his line cannot be
   separated without his working.
5. **Engine = frozen S4 exactly** on every other component (released 874.86 + 12.23 = S4 verified 887.09; readings A
   and B = S4 LOWER_BOUND 2,742.51 and BEST 2,836.40), now read from the drawing and bound to route G's footings
   instead of the frozen census. Independent agreement of two routes.

## Owner manual method and drawing-derived method side by side

| | Manual QS take-off (hand, by footing) | This piece |
|---|---|---|
| Count | schedule count; for "/m": hand practice is spacing count + 1 (reading B) | printed count; "/m" held as A / B / C until Q-71 |
| Length | side - 2 x cover, cover from the general notes | same, 70 mm from note 22 |
| Mass | d^2 / 162 | same (project method) |
| Boxed bars | taken from the typical detail by eye | held: "3+4" is printed with no diameter and the detail gives no count |
| Result | not measured by the owner for this project | 874.86 kg released + 2,742.51 .. 2,836.40 kg held |

## Held items (never 0)

- Count rule for per-metre / spacing notation: owner Q-71 (2,742.51 .. 2,836.40 kg, 5 footings).
- Top-bar end legs of the two-layer footings (F8, F12, F13, F14, FF): no detail drawn; designer RFI (1,136.44 ..
  1,180.84 kg straight core held, end legs unquantified).
- BOXED bars of the 20 single-layer footings: printed "3+4" / "3+5" / "3+8", meaning not established (S4 Q-R3-6).
- F / F10 footing: two marks on one outline, schedule 2.80 x 1.40 vs drawn 3.25 x 1.40 (Q-31 C).
- FN overlapping F9: bar ends inside F9 not drawn.
- F7 has a schedule row and no footing on the plan; F10 appears only through the conflict: listed, no steel.
- The lift-footing extra "2 ø 16" label on FF (S4-Q1) is not a schedule cell: not read by this piece, still held in S4.

## Validation

- `pytest tests/t136_footing_rebar_population` 12 passed (synthetic villa: count / spacing / per-metre notations,
  mm / cm / m units, mirrored and rotated rows, merged cell, missing unit, missing cover, two marks, clipped outline,
  mark without row, row without footing, bar over 12 m, BOXED printed and empty).
- L2 (impact) + firewall: tests/alsenan, slab_rebar_s7, superstructure_beam_rebar_s6, footing_rebar_s4,
  ground_system_rebar_s5, slab_rebar_pre_s7, structural_comparison_engine, pre_s4_footing_readiness,
  d1_2_footing_cover_audit: the same 6 pre-existing failures before and after (byte-identical rebuild / frozen-register
  tests), 0 new. Freeze: 0 differing. Codemap: rebuilt, stale none.
