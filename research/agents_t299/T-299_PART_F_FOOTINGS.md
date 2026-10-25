# T-299 PART F: footing reinforcement populations F8, F12, F13, F14, FF (read only)

Worker 1 (lane S), 2026-10-25, under ENGINEERING_REASONING_STANDARD.md s.2 - s.4, owner 13:16 (F1 - F8), Checker emphasis
13:25 (C1 - C5) and the owner's Q-71 footing answer (12:36). READ ONLY: no engine file, candidate line, quantity, state or
V2.9 cell changes; footing steel stays HELD; the engine's footing kg is not modified. Builds on T-171 (merged 701d227):
its notation reading, its max-spacing count and its enclosing-bar scenario are reused, not repeated. Drawings cited by
Drive folder and title only (Drive "Alsenan chalet project", `ST7757.pdf` pp.8 / 9 / 13 / 14 re-read this run at
110 - 300 dpi); per-bar positions stay in the private folder.

Files: `t299_part_f.py` (model, pure, stdlib), `PART_F_SUMMARY_T299.json` (20 populations, statuses, readings),
`tests/t299_part_f` (16 tests, villa K299F hand fixture). F-T299-01 folded: `t299_alsenan.py` restates the T-138 strap /
ground-beam link holds by designer item (S21 / S20) instead of "Q-71" (reason text only; RECON summary byte-identical).

## 1. Note 22: exact scope (C1, F2)

ST p.8 note 22 (Arabic, three channels agree: D1.2 raster re-read, R4 OCR, S1 transcription; read again this run): "the
concrete cover shall NOT BE LESS THAN 2.5 cm in columns, slabs and beams and 7 cm in concrete in contact with soil".

| Point | Finding | Evidence |
|---|---|---|
| Wording | a MINIMUM, never an exact value or a maximum | "لا يقل ... عن" |
| Members | 2.5 cm names columns, slabs, beams only; footings are not in that list, so a footing's cover comes only from the soil clause | note 22 text |
| Footing SIDE faces | in contact with soil: both p.13 variants draw "well graded clean compacted fill" against them and the detail itself labels them "surface in contact with earth" (two layers liquid waterproofing); FF (p.14): fill + protection board + membrane against the sides | p.13, p.14 |
| Footing BOTTOM face | sits on 5 cm screed + membrane + 10 cm plain concrete (both p.13 variants, p.14): not soil. Whether the soil clause reaches it is NOT needed below (next row) | p.13, p.14 |
| What a cover changes (`cover_effect`) | SIDE cover -> every bar's straight run and, for a rate population, its count; BOTTOM / TOP cover -> bar level and leg lengths only (legs are HELD anyway) | geometry |

So every count and straight run in this part rests on the SIDE cover, which note 22 governs as "not less than 70 mm"
without any reading of the bottom face. Clear cover is kept apart from the bar centre: first centre = cover +
d_enclosing + d / 2 (F3; 76 mm for a ø12 edge bar with nothing between it and the face).

Consequence of MINIMUM (D1.2 already recorded it for S4, 0 kg): side - 2 x 70 is the LONGEST straight run the note
allows, and a count at 70 mm is the largest the note allows; a larger actual cover can only lower both, and no upper
cover is printed. Counts and runs below are therefore "at the minimum cover" (project basis), never as-built facts.

## 2. Every footing population with a reinforcement row, and what the cover changes (C2)

| Path (module / method) | Cover it uses | Count-printed footings (single layer) | Rate footings (F8, F12, F13, F14, FF) |
|---|---|---|---|
| route G `engine/source/generic_route._footing_bars` (URBAN_M8_GENERIC_CONVENTIONS_V6, released default V2.9 + route G, PROVISIONAL) | `REBAR_COVER_FOOTING_M` 0.050 / 0.050 / 0.075 | straight run only (base 50 mm is 20 mm per end BELOW the note-22 minimum: every base bar is 40 mm longer than the longest run allowed) | straight run only in route G, because it counts rate x full side (fractional, independent of cover): a fractional count, refused by F1 |
| `engine/source/footing_rebar_population_v1.run` (T-136, FOOTING_REBAR_POPULATION_V1; candidate since ARCH_TAKEOFF_V3.0.2) | 70 mm as the bar-end position | 874.86 kg DRAWING-CONFIRMED (s.3) | HELD A / B / C |
| frozen S4 / S4.1 (`research/alsenan_footing_rebar_s4*`) | 70 mm SOURCE_EXPLICIT, corrected by D1.2 to MINIMUM -> PROJECT_BASIS_NUMERIC (0 kg change) | 887.09 kg (= 874.86 + FN 12.23) | 2,742.51 (A) |
| T-171 research | 70 mm + enclosing 0 .. 16 mm | not re-counted | 2,769.06 .. 2,829.83 kg |
| this part | 70 mm MINIMUM, side faces | traced (s.3) | s.4 |

Route G footing items by element id (`ROUTE_G_ITEMS_T299.csv`, family FOOTINGS, 27 items on 25 footings; base kg):

| Mark | Notation | Footings | Element ids | Route G base kg | Cover changes |
|---|---|---|---|---|---|
| F | COUNT | 4 | `FTG:SH10:F@195510,50796:88b429`, `FTG:SH10:F@195510,56796:878832`, `FTG:SH10:F@197910,56946:0ce993`, `FTG:SH10:F@207260,50796:767bc7` | 39.822 | straight run only |
| F11 | COUNT | 1 | `FTG:SH10:F11@209785,50796:109682` | 111.793 | straight run only |
| F15 | COUNT | 1 | `FTG:SH10:F15@200710,50796:932498` | 24.089 | straight run only |
| F2 | COUNT | 2 | `FTG:SH10:F2@209810,63096:3919bf`, `FTG:SH10:F2@212510,63096:277c2f` | 78.578 | straight run only |
| F3 | COUNT | 2 | `FTG:SH10:F3@199160,54846:b6c1c9`, `FTG:SH10:F3@205460,51746:38c592` | 39.822 | straight run only |
| F4 | COUNT | 2 | `FTG:SH10:F4@219980,63146:142c12`, `FTG:SH10:F4@224030,63171:ab0b66` | 124.267 | straight run only |
| F5 | COUNT | 2 | `FTG:SH10:F5@215980,63096:f1403e`, `FTG:SH10:F5@220080,51396:04f491` | 160.000 | straight run only |
| F6 | COUNT | 1 | `FTG:SH10:F6@209560,54546:cf553f` | 93.689 | straight run only |
| F9 | COUNT | 1 | `FTG:SH10:F9@219230,58746:3192fb` | 183.901 | straight run only |
| FN | COUNT | 4 | `FTG:SH10:FN@217180,55770:8f5b19`, `FTG:SH10:FN@221705,55770:b61882`, `FTG:SH10:FN@222230,61096:0e0098`, `FTG:SH10:FN@225880,54296:cf72aa` | 51.200 | straight run only |
| F12 | RATE | 1 | `FTG:SH10:F12@207310,58046:67454a` | 721.195 | count (every physical reading) + straight run |
| F13 | RATE | 1 | `FTG:SH10:F13@204810,54196:6b1a4d` | 421.589 | count + straight run |
| F14 | RATE | 1 | `FTG:SH10:F14@216030,50796:73a8e9` | 442.270 | count + straight run |
| F8 | RATE | 1 | `FTG:SH10:F8@222880,56746:624706` | 508.874 | count + straight run |
| FF | RATE | 1 | `FTG:SH10:FF@212310,57596:8e679c` | 734.819 | count + straight run |

Route G sums 907.160 kg (count-printed) + 2,828.747 kg (rate) = 3,735.907 kg, a PROVISIONAL SUBTOTAL (r1 rule), never a
total. Its footing steel rests on a cover below the drawing's minimum on every row: a route-G finding for the Checker,
not a downgrade (route G is PROVISIONAL; nothing verified rests on it). The frozen route is not edited.

## 3. The 874.86 kg footing line (C3, C4)

Trace: `engine/source/footing_rebar_population_v1.run` (T-136, merged 6d532c5), integrated in the candidate from
ARCH_TAKEOFF_V3.0.2 (T-142) and carried since; status DRAWING-CONFIRMED in the candidate (not in released V2.9). It is
the 19 single-layer, count-printed footing occurrences (marks F x4, F2 x2, F3 x2, F4 x2, F5 x2, F6, F9, F11, F15,
FN x3; FN at the F9 corner held 12.23 kg), short bars along W counted along L. Reproduced here to 0.01 kg: sum of
n x (side - 2 x 0.070) x d^2/162 = 874.86 kg. It does NOT overlap the 20 rate populations of s.4 (other footings).

| Component | Basis in the line | Finding |
|---|---|---|
| Count | printed `n ø d` | DRAWING-CONFIRMED stands (printed; never re-counted) |
| Diameter | printed | stands |
| Straight run | side - 2 x 70 mm | rests on the minimum cover taken as the bar-end position: it is the LONGEST run note 22 allows, an upper value, not a confirmed length. And p.13 (both variants) draws the bottom bars ending between the vertical legs of the "Boxed bars" that every one of these rows prints (`3+n`, FN empty): a leg of unprinted diameter between bar end and face shortens each bar by 2 d_box where it lies at that end |
| Weight | count x run x d^2/162 | follows the run: an upper value at the minimum cover |

Sensitivity (scenario only, never a quantity): boxed leg 8 / 10 / 12 / 14 / 16 mm at both ends of every bar of a
footing with a printed BOXED value -> 867.75 / 865.97 / 864.19 / 862.41 / 860.63 kg (-7.11 .. -14.23 kg, -0.8 .. -1.6 %);
whether a leg lies at both ends in BOTH directions is not drawn (one elevation, S4 Q-R3-6); a larger actual cover lowers
it further, with no printed bound.

**DOWNGRADE RECORD PROPOSAL for the Checker (C4; through `docs/agents/verdicts/<candidate>/`, not written here):** the
candidate footing line 874.86 kg (FOOTING_REBAR_POPULATION_V1): count DRAWING-CONFIRMED (unchanged); straight run and
weight DRAWING-CONFIRMED -> PROVISIONAL (upper value at the note-22 minimum cover; boxed-leg diameter not printed);
quantity unchanged (no silent change); released V2.9 unchanged. Designer item: extend Q-R3-6 / the boxed-bar request
with "bar-end position of the bottom bars relative to the boxed-bar legs, and the boxed-bar diameter".

## 4. The 20 rate populations (F1, F5, owner Q-71 points 1 - 10)

Readings kept side by side (never merged, never a fractional count): MAX_SPACING = 1/n is the largest centre-to-centre
spacing with an edge bar at each side (T-171): N = ceil(L_eff / s) + 1, L_eff = side - 2 x 70 - 2 d_enc - d, with d_enc
over the T-171 scenario 0 .. 16 mm; DENSITY_IN_ZONE = n bars per metre of the zone inside the covers: ceil(n x (side -
2 x 70)) (Q-71 reading A). Refused for footings: N = n x L + 1 (Q-71 point 8), the beam 7.5 cm first link (point 7).
Short bars spread across L, long bars across W (S4 SOURCE_DERIVED_HIGH_CONFIDENCE). Margin = extra side cover (mm) at
which the max-spacing / density count first loses a bar.

| Population | ø | Count range (density .. max) | Count | Achieved spacing at e = 0 vs printed max (mm) | Margin (mm) | Developed length | Weight | Audit scenario kg | HELD reason |
|---|---|---|---|---|---|---|---|---|---|
| F8 BOT SHORT | 14 | 35 .. 36 | HELD | 109.89 / 111.11 | 35 / 42 | HELD | HELD | 145.161 .. 150.702 | notation (RFI); min cover; p.13 is a single-layer detail |
| F8 BOT LONG | 14 | 32 .. 33 | HELD | 107.69 / 111.11 | 1 / 8 | HELD | HELD | 148.205 .. 154.114 | notation; enclosing bar (knife edge 1 mm); min cover |
| F8 TOP SHORT | 14 | 24 .. 25 | HELD | 160.25 / 166.67 | 7 / 14 | HELD | HELD | 99.539 .. 104.654 | notation; enclosing bar; top ends not drawn |
| F8 TOP LONG | 14 | 21 .. 22 | HELD | 164.10 / 166.67 | 57 / 64 | HELD | HELD | 97.260 .. 102.743 | notation; top ends not drawn |
| F12 BOT SHORT | 16 | 39 .. 40 | HELD | 108.82 / 111.11 | 11 / 19 | HELD | HELD | 186.615 .. 193.422 | notation; enclosing bar (12 mm) |
| F12 BOT LONG | 16 | 28 .. 29 | HELD | 108.71 / 111.11 | 22 / 30 | HELD | HELD | 187.076 .. 195.224 | notation |
| F12 TOP SHORT | 14 | 43 .. 44 | HELD | 98.74 / 100.00 | 23 / 30 | HELD | HELD | 157.531 .. 162.898 | notation; top ends not drawn |
| F12 TOP LONG | 14 | 31 .. 32 | HELD | 98.26 / 100.00 | 23 / 30 | HELD | HELD | 158.576 .. 164.930 | notation; top ends not drawn |
| F13 BOT SHORT | 16 | 34 .. 35 | HELD | 121.88 / 125.00 | 10 / 18 | HELD | HELD | 119.707 .. 124.998 | notation; enclosing bar (10 mm) |
| F13 BOT LONG | 16 | 19 | INVARIANT AT MIN COVER | 124.67 / 125.00 | 60 / 5 | HELD | HELD | 123.942 .. 124.903 | count: every reading 19 at 70 mm (density drops at +5 mm cover); length: cage not drawn |
| F13 TOP SHORT | 14 | 30 .. 31 | HELD | 138.20 / 142.86 | 2 / 9 | HELD | HELD | 80.868 .. 84.764 | notation; enclosing bar (2 mm) |
| F13 TOP LONG | 14 | 16 .. 17 | HELD | 140.38 / 142.86 | 52 / 59 | HELD | HELD | 79.910 .. 85.562 | notation |
| F14 BOT SHORT | 14 | 33 .. 34 | HELD | 110.48 / 111.11 | 46 / 53 | HELD | HELD | 124.888 .. 129.989 | notation |
| F14 BOT LONG | 14 | 29 .. 30 | HELD | 108.48 / 111.11 | 18 / 25 | HELD | HELD | 127.294 .. 132.844 | notation |
| F14 TOP SHORT | 14 | 22 .. 23 | HELD | 165.73 / 166.67 | 73 / 80 | HELD | HELD | 83.259 .. 87.934 | notation |
| F14 TOP LONG | 14 | 19 .. 20 | HELD | 165.58 / 166.67 | 73 / 80 | HELD | HELD | 83.399 .. 88.563 | notation |
| FF BOT SHORT | 14 | 41 .. 42 | HELD | 108.44 / 111.11 | 1 / 8 | HELD | HELD | 214.690 .. 221.553 | notation; enclosing (1 mm knife edge); p.14 cage legs undimensioned |
| FF BOT LONG | 14 | 40 .. 41 | HELD | 108.65 / 111.11 | 7 / 14 | HELD | HELD | 214.293 .. 221.238 | notation; enclosing (7 mm); p.14 legs |
| FF TOP SHORT | 14 | 27 .. 28 | HELD | 164.67 / 166.67 | 57 / 64 | HELD | HELD | 141.381 .. 147.702 | notation; p.14 legs |
| FF TOP LONG | 14 | 27 .. 28 | HELD | 160.96 / 166.67 | 7 / 14 | HELD | HELD | 144.648 .. 151.089 | notation; enclosing (7 mm); p.14 legs |

Summary: diameters 20 / 20 PRINTED; integer counts 1 / 20 invariant at the minimum cover (F13 BOT LONG = 19, a Checker
VERIFIED candidate AT 70 mm only), 19 / 20 HELD as a one-bar range; developed lengths 0 / 20 (F4: p.13 is drawn for a
single-layer boxed footing, its use for the two-layer case is not stated; F12 / F13 / F14 print a cage symbol in REMARKS
with no section; FF p.14 is a closed cage with undimensioned legs; F8 has neither); weights 0 / 20 (F5: a count never
makes a weight). Audit scenario (F6, never a quantity, never summed with a measured value): 2.718241 .. 2.829826 t
(min count x shortest scenario run .. max count x longest run). Neither endpoint is verified; the engine's 2.829 t is
not validated by it; the T-171 2.769 - 2.830 t range is one slice of it (max-spacing reading only).

Hand checks (stop point F8 / F12 first; F13 / F14 / FF computed by the same tool, named for the Checker):
- F8 BOT SHORT `9 ø 14/m` across 4.00 m: L_eff = 4000 - 140 - 14 = 3846 mm; 3846 / 111.11 = 34.614 -> 35 + 1 = 36
  (d_enc 16: 3814 -> 34.326 -> 36); density 9 x 3.86 = 34.74 -> 35. Range 35 .. 36; run <= 3.60 - 0.14 = 3.46 m.
- F8 BOT LONG across 3.60 m: 3446 / 111.11 = 31.014 -> 33; d_enc 8: 3430 -> 30.87 -> 32 (the 1 mm knife edge); density
  9 x 3.46 = 31.14 -> 32.
- F12 BOT SHORT `9 ø 16/m` across 4.40 m: 4244 / 111.11 = 38.196 -> 40; d_enc 12: 4220 -> 37.98 -> 39; density
  9 x 4.26 = 38.34 -> 39.
- F12 BOT LONG across 3.20 m: 3044 -> 27.396 -> 29 (d_enc 16: 3012 -> 27.108 -> 29); density 9 x 3.06 = 27.54 -> 28.

## 5. F7: what "n ø d/m" means for the installed count

The drawing set prints counts (`n ø d`), spacings (`ø d/s cm`, p.13 ground-beam links) and rates (`n ø d/m`); it never
states whether a rate is a maximum spacing or an average density, nor where the edge bars stand (D1.2: no dimension
binds a footing bar line). The max-spacing reading rests on practice (T-171 E7, level 4, labelled), the edge bars on
the p.13 drawing. The two readings differ by exactly one bar in 19 / 20 populations, so the meaning changes the
installed count: the designer clarification is KEPT (RFI: "for footing mesh printed `n ø d/m`, is 1/n a maximum
centre-to-centre spacing with a bar at each edge, and what is the edge-bar position from the side face?"). This is a
DESIGNER item, not an owner question (standard s.2.7: the owner's 12:36 method already says to present the defensible
readings and hold).

## 6. Reconciliation (kg, all scenarios; nothing added to a measured total)

| From | To | Cause | kg |
|---|---|---|---|
| route G rate footings 2,828.747 | T-171 max-spacing at e = 0: 2,829.83 | route G: 50 mm cover (longer runs) + n x full side, fractional (fewer bars) | +1.08 net of two opposite causes |
| T-171 2,829.83 | this envelope high 2,829.826 | same model (rounding of the T-171 figure) | 0.00 |
| T-171 low 2,769.06 (e = 16) | this envelope low 2,718.241 | density reading (one bar fewer in 19 rows) combined with the 16 mm scenario run | -50.82 |
| Q-71 A 2,742.51 | Q-71 B 2,836.40 | T-171 s.4 (unchanged) | +93.89 |

Residual unexplained: none.

## 7. General rule proposed (R-FTG-MESH-COVER-1; scope footings, any villa; provenance Alsenan ST p.8 / 9 / 13 / 14,
owner Q-71 12:36; adoption = a NEW rule version, not made here)

"A printed cover note is read with its wording and its scope. Footing mesh counts and straight runs depend only on the
cover of the SIDE faces the bars are spread / run towards; a MINIMUM cover gives the largest count and the longest run
the note allows, which are project-basis values, never confirmed lengths. A rate `n ø d/m` gives at least two
defensible whole-bar counts (max spacing with edge bars; density in the zone) unless the drawing states which; the
population is HELD as that range until it does. A straight run stops at a drawn enclosing bar; with its diameter
unprinted the run is HELD. Count, diameter, developed length and weight carry separate statuses; a scenario range is
never VERIFIED and never summed with a measured value." Test: `tests/t299_part_f` (normal: KF1 counts 23 .. 24 /
19 .. 20, KF2 invariant 16 with positions 76 .. 1569 mm, units / rotation, printed-count trace 15.288889 / 14.933333 kg;
adverse: fractional count, N = n x L + 1, beam 7.5 cm offset, length from a minimum cover, automatic 2 d_enc, weight
claimed VERIFIED with a HELD count, HELD as 0, scenario summed, missing / unreadable cover or cell, larger cover never
raises a count).

Lessons-register row proposed (s.7): 2026-10-25 | a footing line (874.86 kg) carried DRAWING-CONFIRMED on runs taken
at a cover printed as a minimum, with a drawn boxed-bar leg between bar end and face | the status of the count (printed)
was given to the weight; the cover's wording was read as a value | count, run and weight carry separate statuses; a
minimum cover gives a longest run, never a confirmed length (footings, any villa; T-136, T-299 F) | tests/t299_part_f
(weight claim refused while the length is HELD; length from a minimum cover refused) | OPEN (Checker downgrade record).

## 8. HELD and named items

- 19 counts (notation RFI s.5; enclosing-bar diameter on 9 of them), 20 developed lengths (s.4), 20 weights.
- Designer: boxed / cage bar diameter and leg dimensions; bottom-bar end position vs the boxed legs (also for the 874.86
  kg line); top-layer bar ends of F8 / F12 / F13 / F14; FF cage legs; F8 (no cage symbol) vs F12 / F13 / F14 (symbol).
- Not in this part: cover of ground beams / straps / ground slab / starters (note 22 names beams at 2.5 cm and soil at
  7 cm; R4 lists them under the soil clause): named for the Lead, not investigated here.
- Integration priorities unchanged (T-298, T-254 ahead of any quantity change, F8).
