# T-352 Stair formwork (missing category B7-13): the formed faces of both staircases, per flight and landing (Alsenan; every villa)

Worker 1 (lane S), 2026-10-29, run session_01E6cPnadnaNnumvqCTqqgXY. Research piece, not wired: no engine, candidate,
released line, rule or knowledge file changed; integration is T-199 (lane I) after the Checker's verdict. Development
villa, not an accuracy claim. Drawings named by Drive folder and title, entities by DXF handle; relative lengths only.
ERS s.2.1-2.4, s.3, s.4, s.7 applied. Rules: OWNER_RULE_STAIRS_2026-10-21 (S-1 drawing governs), 2026-10-24 s.4-s.6
(S-5 .. S-9: no generated winders, actual polygons, HELD blank), Q-19, Q-46 A, Q-47 A, Q-50 A cond, Q-61 C, Q-62 A cond,
UP-QTY-STATUS-001, WORKFLOW_CONTROLS s.5.

## 0. Inputs (own reads this run)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179... (= manifest) | p.4 / p.5 stair lanes, walls, wells, member bands, free edges beside every flight and landing, by handle (`t352_extract.py`, lengths only); T-139 faces re-polygonised from the same file to identify the slab beyond edge 289 (GF-146) |

Merged evidence built on, cited, not re-derived: T-163 r3 (659f889f) and T-332 r2 (61d5597e) formwork face ledger
(every stair face listed by id in `EXISTING_STAIR_FACES_T332.csv`, read only), T-258 r2 stair concrete components
(Checker-verified values: the cross-check of every side profile), T-281 soffits, T-184 inventory, T-189 / T-192 heads
and feet, T-139 slab panels. Candidate stair lines: the 11 STR.CONC.STAIR ids of V3.0.21 (T-332 digest), outside every
replaced / added set of V3.0.22 (finishes), V3.0.23 (parapet) and V3.0.24 (text of rebar / finish lines): carried
byte-identical into V3.0.24 by those runs' identity assertions (Checker: confirm on json 19394733).

## 1. The physical element (ERS s.2.1) and the methods

The formwork of a cast-in-place stair is: the waist soffit and landing soffits (horizontal / sloped forms), the riser
boards, and the SIDE forms: the stringer profile of each flight (step triangles + waist band, in side elevation) and
the edge of each landing plate, wherever the side does not bear against something that already exists. T-163 r3 /
T-332 already carry soffits and riser forms (32.822036 m2 CALCULATED on the stair element) and held the sides as one
aggregate row without a value (R4-339). This piece measures the sides.

* Side profile area (first principles): along its width a straight flight is a prism, so one side face = stair-owned
  volume / width; computed here directly from the printed primitives (riser = rise / count, going 0.300, waist T 16) by
  exact integration of the profile between stations (`profile_strip`), and cross-checked against the T-258 verified
  volumes / width (agreement 1e-6 m2; MS2-L carries a named 0.000057 m2 residual, s.3).
* What is beside each side decides the status (never a default): VOID (well, light well, opening, free slab edge with
  nothing at that level) -> FORMED, valued; WALL (block shaft / lift walls, T-173 / D-43) and MEMBER (beam band, stair
  beam 'B3 (With Stair)', column) -> HELD 0 .. area: formed or cast against it depends on the construction sequence,
  which no sheet prints; JUNCTION (well ends, corner strips whose own concrete is HELD) -> HELD; UNKNOWN (support / waist
  not printed: D1, E1) -> HELD unbounded.
* Owner manual method: none on record for formwork (no answer names one; T-163 s.6). The element method E (struct_n10)
  does not measure stairs. The drawing-derived method below is the only method; nothing is chosen for size.

## 2. Ledger (STAIR_FORMWORK_T352_BY_FACE.csv, 27 new faces; m2 contact area; nothing released)

| Stair / piece | Side or edge | Beside it (handle) | Status | m2 |
|---|---|---|---|---|
| ST-01 MS1-L (GF, CONFLICT C-ST-4) | east, well | S-OPENING 256 / 25A (0.100) | CONFLICT | 0.709344 .. 0.869164 |
| | east, last 0.050 | well end at the turn (MS1-T strip) | HELD | 0 .. 0.009846 |
| | west | shaft wall 284 | HELD | 0 .. 0.879010 |
| ST-01 MS1-U (GF -> 1F) | west, well | 256 / 25A over s 0 .. 3.100 (to the B20 face) | **CALCULATED** DRAWING-CONFIRMED | **0.831293** |
| | east | lift-shaft wall 296 | HELD | 0 .. 0.831293 |
| ST-01 MS1-LD (+3.50) | north 1.20 / east 1.20 | 'B3 (With Stair)' 279 / wall 296 | HELD | 0 .. 0.192 each |
| ST-01 MS2-L (1F -> landing) | east, well | 62D / 62E over s 0.150 .. 3.250; s 0 .. 0.150 above the 1F floor | **CALCULATED** DRAWING-CONFIRMED | **0.851277** |
| | east, last 0.050 | well end 633 / 632 (MS2-TR) | HELD | 0 .. 0.009869 |
| | west | shaft wall 5E3, column 691 | HELD | 0 .. 0.861146 |
| ST-01 MS2-LD-W (+7.516) | west 1.15 / north 1.30 | wall 5E3 / band 5C0 | HELD | 0 .. 0.184 / 0 .. 0.208 |
| ST-01 MS2-LD-E (+7.684) | north 1.20 / east 1.20 | band 5C0 / wall 5D4 | HELD | 0 .. 0.192 each |
| ST-01 MS2-U (landing -> 2F) | west, well | 62E over s 0 .. 3.100 (to the B23 face) | **CALCULATED** DRAWING-CONFIRMED | **0.834477** |
| | east | lift-shaft wall 5D4 | HELD | 0 .. 0.834477 |
| ST-01b D1 | both sides | 1C3 / 143 pair; ground-beam face 15F | HELD (unbounded: waist / support not printed) | - |
| ST-03 E1 | both ends | ground-beam band 145 / 7CA; layer-5 186 / 187 | HELD (unbounded) | - |
| ST-02 RS-S | north, light well | 2D0 over s 0 .. 2.950 | **CALCULATED** ASSUMED — OWNER-APPROVED (Q-50 A cond riser) | **0.775865** |
| | north, last 0.050 | corner strip 2CF / 2C4 | HELD | 0 .. 0.009745 |
| | south | 'B3 (With Stair)' 283, column 380 | HELD | 0 .. 0.785610 |
| ST-02 RS-LD (+4.696) | east 1.15 (column 374 takes 0.050) | free edge 289, 0.64 m below the GF-146 slab soffit | **CALCULATED** DRAWING-CONFIRMED (length x T 16; independent of the riser) | **0.184000** |
| | south 1.15 | B3 band 0.600 + column 374 0.550 | HELD | 0 .. 0.184 |
| ST-02 RS-A | west, light well | 2CF (runs past 315) | **CALCULATED** ASSUMED — OWNER-APPROVED | **0.314244** |
| | east | free edge 289: stair-owned profile tops at +5.3393, slab GF-146 soffit +5.34 | **CALCULATED** ASSUMED — OWNER-APPROVED | **0.314244** |
| **New** | 7 valued faces | | | **4.105400 CALCULATED** + 16 bounded HELD 0.709344 .. 6.434161 + 4 unbounded HELD |

Stair formwork family after this piece: 32.822036 (T-332, soffits + risers, unchanged) + 4.105400 = **36.927436 m2
CALCULATED** (+12.5 %), every held face beside it by name. Freelancer: no formwork row in any workbook
(FREELANCER_NO_ROW). Engine (released V2.9 + route G and candidate V3.0.24): no formwork line (T-199 QUEUED): not
comparable, neither side has the line; this ledger is the first measurement of the stair sides.

## 3. Cross-check and reconciliation (units)

Side profile from primitives vs T-258 stair-owned m3 / 1.20 (m2): MS1-U 0.8312925 vs 0.8312933; MS2-U 0.8344775 vs
0.8344775; RS-S 0.7856102 vs 0.7856100; RS-A 0.3142441 vs 0.3142442; MS1-L A 0.7191902 vs 0.7191908, B 0.8790103 vs
0.8790108 (all within 1e-6: the ledger rounds to 6 decimals in m3). MS2-L: 0.851277 formed + 0.009869 junction strip =
0.861146 vs 0.861203: **named residual 0.000057 m2** = the 12th step triangle's sliver below the MS2-LD-W plate soffit
(T-258: 0.030240 - wedge 0.030171 = 0.000069 m3 stays with the steps) beside the plate's well part; below every
tolerance, not valued, listed. The MS2-L foot below the floor inside B20 re-derived 0.021207 m2 x 1.20 = 0.025448 m3 =
T-192 (verified).

## 4. Cross-check with the general ledger (acceptance b): every overlap, double count 0

| Id | Existing face | Finding | Effect |
|---|---|---|---|
| OV-1 | R4-321 MS1-U risers 12 x 1.20 x 0.166667 | the 12th riser line 459 is 0.200 inside the B20 band: that 0.200 m2 is the B20 stair-side face above the last tread | carried once in the riser row; deduct from the B20 faces (R4-261.GF-066, HELD) when they close |
| OV-2 | R4-327 MS2-U risers | the same at B23 (0.201600 m2; R4-285.1F-045 HELD) | as OV-1 |
| OV-3 | R4-337.LANE RS-A risers | the 5th riser at 315 is plate C-T1's edge (0.192857 m2); no slab-edge face valued at 315 | listed only |
| OV-4 | R4-261.GF-066 B20 face, HELD 0 .. 1.475 | MS1-U's head bears on it from +5.039 to the slab soffit +5.34: 1.20 x 0.300811 = 0.360973 m2 cast against the flight | its bound overstates the formed part by up to 0.360973 |
| OV-5 | R4-285.1F-045 B23 face, HELD 0 .. 1.474594 | MS2-U's head: +9.2366 to +9.54 (1F-062 T 16): 0.364056 m2 cast against the flight | as OV-4 |
| OV-6 | R4-263.GF-146 slab edge at 289 'next to STAIR', HELD 0 .. 0.375993 | the wedge GF-146 is ABOVE the round stair (RS-LD +4.696, RS-A profile <= +5.3393 < soffit +5.34): its edge is free | **F-T352-2**: a formed free edge 2.35 x 0.16 = 0.375993 m2, not a stair junction (T-199 / the slab line) |
| OV-7 | R4-339 stringer-profile aggregate (HELD, NAMED_NOT_TIED) | split here into one row per side / edge | SUPERSEDED: T-199 takes the T352 rows and drops R4-339, never both |
| OV-8 | R4-319 MS1-T turn faces (HELD) | drawn winder lines 2F6 1.2587 + 2F4 1.6263 + 2F5 1.2587 + 2F3 1.150 = 5.2937 m x 4.50 / 27 = 0.882283 m2 is information only: 4 riser lines in the turn vs 5 risers on A-A, and C-ST-4 moves the turn start | winders stay HELD (drawn, not settled: S-9) |
| OV-9 | R4-316 slab under the winders HELD 1.440 .. 1.562 | the bound is T-111's plan-projection range; the turn is now drawn 1.30 x 1.15 = 1.495 m2 (T-281) and a warped soffit is never smaller than its plan | **F-T352-1**: lo 1.440 understates (>= 1.495); hi not established |

No new face shares an area with an existing one (unique ids, no existing id re-added, `check_faces`); the
member faces 'next to STAIR' are member faces and stay with their lines.

## 5. Addendum FILL for T-199 (T199_FILL_T352_ADDENDUM.csv)

13 rows (line id, family FW.STAIR, status, faces, m2 / lo / hi, face ids) over 8 of the 11 candidate stair lines;
HELD and CONFLICT rows carry m2 BLANK, lo / hi only where every face of the row has the bound, never 0.000000 as an
upper bound (R-T332-8 semantics). Valued: L-e37d81a8be8e0aa0010c 0.831293, L-67e4b0485135f84acc46 0.851277,
L-bb0e57b1948175a3d5b8 0.834477, L-056402f98a6dbbcde0a0 1.588353 (RS-S 0.775865 + RS-LD 0.184 + RS-A 2 x 0.314244).

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 7 valued side / edge faces 4.105400 m2 | HAND (drawing) measurement; FREELANCER_NO_ROW, engine has no line |
| wall / member sides | HELD 0 .. area (construction sequence not printed): not an owner question (ERS 2.7 not met: a contractor's means and methods item; the consultant list may ask whether the stair is cast before the shaft blockwork) |
| R4-339 | superseded (OV-7) |
| R4-316 bound / GF-146 edge | findings F-T352-1 / F-T352-2 for T-199 |

## 7. Rule, tests, lessons

Rule proposed (R-STAIR-FW-SIDE-1, any villa; provenance T-352; a new rule version when adopted): a flight's side form is
its stringer profile (step triangles + waist band, the stair-owned part between the first riser line and the member face
or landing it enters) on each side, one row per side; a landing's edge form is edge length x plate thickness, one row
per edge; each is FORMED (valued) only where the drawing shows open space beside it at that level (well, light well,
opening, free slab edge above or below), and HELD 0 .. area where a wall, member or held junction is beside it; a
riser line inside a member band is the member's face (listed once); winders and curved sides only when drawn,
dimensioned and count-consistent (S-9).

Tests (tests/t352_stair_formwork, 19): villa K hand fixture (straight flight with a quarter landing and a second
flight: 0.518199 / 0.165 / 0.296114 m2, head strip 0.009626, strips sum to the whole, side = volume / width, units);
adverse: a generated winder (not drawn / count disagrees) refused, a side form on a wall- or member-bearing side valued
-> refused, a stair soffit counted with the slab soffit (same region) refused, a held face as 0 / 0 .. 0 / printed 0 in
the FILL refused, missing waist or riser never computed, a face twice or re-added from the general ledger refused, a
CONFLICT collapsed to one end refused, a strip outside the flight refused; development villa pinned (committed outputs =
fresh build, 7 valued faces 4.105400, profiles = verified concrete / width, MS2-L residual named, held never 0, R4-339
superseded, every face bound to an STR.CONC.STAIR line).

Lessons row (proposed, ERS s.7): 2026-10-29 | the stair formwork family carried soffits and risers but no side forms (one
unvalued aggregate row) | the side of a flight was treated as one unknown instead of being read side by side on the
drawing (a well or opening beside it is a known void; only wall / member contacts depend on the unprinted sequence) |
R-STAIR-FW-SIDE-1 above (any villa) | t352 test_villa_k_ledger_and_fill, test_adverse_side_form_on_a_wall_bearing_side_refused,
test_adverse_generated_winder_refused | PROPOSED.

## 8. Checker re-measure list ('ST7757 dxf.dxf', by handle)

1. `python3 -I research/agents_t352/t352_extract.py <ST dxf>`: lanes 1.200 / well 0.100 / 1.200 on p.4 and p.5; well
   256 length 3.100 from the B20 face; MS1-U 25B -> B20 face 3.100; MS2-L 646 -> well start 0.150, -> 633 3.250; MS2-U
   62F -> B23 face 3.100; RS-S 2BA -> 2CF 2.950; RS-A lane 2CF -> 289 1.200; column 374 0.050 along 289.
2. One flight by hand: MS1-U side = 11 x 1/2 x 0.166667 x 0.300 + 0.16 x hypot(3.30, 1.833333) - head in B20 0.047718
   = 0.275000 + 0.604011 - 0.047718 = 0.831293 m2 (= 0.997552 / 1.20).
3. Beyond 289: only the slab wedge GF-146 (T-139, T 16, bars hooked at 289), then B21: RS-A / RS-LD east sides open.
4. Re-run: `python3 -I research/agents_t352/t352_alsenan.py` (prints byte-identical).

## 9. Not done / uncertain

* Every wall / member side stays HELD (16 faces, up to 6.434161 m2): the stair-before-blockwork sequence is not printed.
* MS1-L stays CONFLICT with its concrete (C-ST-4); winders (R4-319), the curved flight RS-C (R4-333), MS2-TR, the D1 and
  E1 sides stay HELD: no drawn and settled geometry.
* Binding is to the V3.0.21 ids carried unchanged into V3.0.24 by the cited identity assertions (not re-run here).
