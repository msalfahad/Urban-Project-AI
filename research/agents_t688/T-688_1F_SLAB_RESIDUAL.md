# T-688: 1F slab residual (-0.556333 m3) and F-V-P18-2 (development villa; rules for every villa)

Worker 1, 2026-11-11. Candidate of record ARCH_TAKEOFF_V3.0.66 (line index T-677). Research only: no line, quantity,
frozen method, rule or knowledge version file changed. Numbers in `out/T688_STATEMENT.md` (generated).

## 1. Physical element (ERS s.2.2)

The 1F slab (sheet "FIRST FLOOR ROOF SLAB", tag 1F) is the cast-in-situ slab between member faces, at its own
thickness, net of: the two dome openings (inner circles 14.980 and 15.326 m2, radial opening symbols; ring beams B4 are
members), the 1.80 x 1.80 void (X symbol, 3.240 m2), the stair zone "(With Stair)" (10.725 m2, flights are the stair
family), and the member strips (beams 0.30 .. 0.55 m, columns). A printed level / thickness mark ("T 16" in the
largest panel) or the project default 0.16 sets the thickness; both sides use 0.16 on this storey, so the residual is
area, not thickness. The "P.C 20x50" (8 T16) inside one panel is a planted column standing ON the slab: no deduction.
The dome-corner cells (between each ring and its square bay, 4 per dome) carry no opening symbol: they are slab.

## 2. Own re-measure (R-T688-1, own noding)

`t688_measure.py` on Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (private copy): layers '1', S-COL.BON,
S-BOUN inside frame FR04; arcs at 0.2 mm sagitta; open ends extended 30 mm; polygonized (151 faces). Engine cells
located BY POSITION (M5 1F map placed by scale + offset fitted on 12 unique cells), never by area.

- 22 / 22 released panels located, one own face each, no face shared.
- Own 123.478724 m2 vs engine 123.477081 m2: +0.001643 m2 = +0.000263 m3, all on the 8 dome-corner cells
  (+0.0002 m2 each, arc chords). 14 straight-edged panels agree to <= 0.000002 m2. Engine geometry: AGREE.
- The 4 EXCLUDED 1F lines are faces outside the slab (edge strips / projections), not in either total.

## 3. The reference (his slab sheet, read as reference arithmetic only)

His 1F row is ONE typed constant: 120 m2 x 0.16 = 19.2 m3 (no area derivation; a 0.081 m3 deduction row multiplied
by a count of 0). GF is also typed (207) and agrees with the engine within its own rounding (207 - 33.069522 / 0.16 =
+0.315 m2 <= 0.5): same measuring convention (panel net between member faces). So 1F is scope, not convention.

## 4. Reconciliation of -0.556333 m3 (R-T688-2)

| cause | m3 | status |
|---|---|---|
| our error (engine vs own drawing re-measure) | 0.000000 (noise +0.000263, arc chords) | ENGINE_RIGHT on geometry |
| reference rounding of the typed 120 (+-0.5 m2) | -0.080 .. +0.080 | REFERENCE INPUT |
| reference scope: 2.977 .. 3.977 m2 of drawn panels not in his 120 | -0.636333 .. -0.476333 | UNRESOLVED (ambiguous) |
| sum | -0.556333 exactly (scope = difference - rounding) | |

62 subsets of the 22 drawn panels fit the scope band, so no panel can be named as "his omission" from his data; the
subset closest to his figure is never picked (ERS). Two physical candidates both fit: the 8 dome-corner cells
(3.846112 m2 = 0.615378 m3; a takeoff that deducts each dome bay as a square drops them) and the panel between B23
and the B6 over the west dome (3.220462 m2 = 0.515274 m3). Neither is evidence; it stays UNRESOLVED with the residual
named. WHO IS RIGHT: ENGINE_RIGHT on every drawn panel (own re-measure); the reference composition is UNRESOLVED
(his figure has no derivation). No owner question: ERS s.2.7 not met (no quantity is held by it; the drawing settles
the engine quantity).

Observation outside this storey (for the Lead): 2F (+0.043100 m3) splits by thickness as 0.16: engine 31.25 vs his
31.84 m2 (+0.59) and 0.18: 13.635 vs 13.35 m2 (-0.285); both beyond his 0.01 m2 resolution, i.e. a thickness-zone
split difference, not rounding. Not investigated here.

## 5. F-V-P18-2 (R-T688-3)

Own noding of the ground plan (frame FR08, ext 1 mm): the face of L-a7ab57d8 is unique: 0.95 x 1.20 = 1.140000 m2,
its own level mark +0.30 inside, bounded on all four sides by 0.30 m member strips (4 neighbours, widths 0.30). A
level is printed on a floor, and 0.95 m is no drawn member section: it is GROUND SLAB (B10-05). The engine line
already owns it correctly (STR.CONC.GROUND_SLAB RELEASED 0.114 = 1.14 x 0.10: AGREE); only the detector's region label
BEAM_STRIP (BAND0042 pairing its two 1.20 m edges 0.95 apart) is wrong. GB L-e16c9807 (BAND0042) is HELD and its
ledger runs are the curved exterior annex member ARC:139+13A 1.8063 m x 0.30 (T-426 / T-242), none inside this face:
no double release now. Register proposal: GF / SLAB / this face -> owner trade CONCRETE, B10-05 L-a7ab57d8; kind GB only
for the four 0.30 strips; when BAND0042 is bounded its runs stay outside the face (R-T688-3 (b)); the +0.30 / +0.15
step sits on a 0.30 strip and is a GB-part item. Verdict ENGINE_RIGHT (quantity), detector label wrong.

## 6. Rules, tests, lessons

`t688_rules.py`: R-T688-1 (own panel noding: opening symbol must span the face), R-T688-2 (typed reference constant:
resolution band, scope band, subset count, convention check on another storey), R-T688-3 (region label vs physical
element). `tests/t688_slab_residual` (19): villa V688 by hand (panel crossed by a void 36.19 - 1.00 = 35.19; mirror,
rotation, metres; unnoded void end leaks and is never deducted without gap closing; a level mark keeps a narrow face
slab), typed constants (ambiguous / unique / none / rounding-only / reference larger; our error named first; refusal
when a panel is not located; convention check), R-T688-3 normal + adverse, development villa statement reproduces and
its numbers (difference = rounding + scope bands exactly).

Lessons register rows (ERS s.7, PROPOSED):
| 2026-11-11 | a reference area typed as a round number can only be compared at its printed resolution | reference
reconciliation | split the difference into a rounding band and a scope band; count the drawn-panel subsets that fit; never
name the closest one | R-T688-2, T-688 |
| 2026-11-11 | an opening symbol in the corner of a larger face means the void outline did not close | own noding |
close unnoded ends first; an opening symbol must span its face | R-T688-1 (b), T-688 |
