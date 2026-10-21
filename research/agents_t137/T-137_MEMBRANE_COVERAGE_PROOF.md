# T-137: membrane coverage proof (MEMBRANE_COVERAGE_PROOF_V1), checker piece, not wired

Worker 3, 2026-10-21. Gate 1 / 2 (waterproofing: no wet area or roof left with bare membrane). From scout answer R-07.
No method, rule, knowledge or frozen file changed; no quantity moves.

## 1. What the engine gives against the freelancer (unchanged by this piece)

| Trade, unit | Engine | Freelancer | Difference | State |
|---|---|---|---|---|
| Wet-area floor membrane, m2 | 72.12 | 72.01 | +0.11 m2 (+0.16 %) | released (V2.11 onward), unchanged |
| Roof membrane (three plan roofs), m2 | 204.11 | 285.00 | -80.89 m2 (-28.4 %) | 2F top roof HELD (Q-34), unchanged |
| Membrane rolls to buy, wet areas (18 incl. pantry), nr | 21 (V2.13) | no roll line | not comparable | released, now PROVEN by this check |
| Membrane rolls to buy, roofs, nr | 17 + 6 + 8 = 31 (V2.13) | no roll line | not comparable | 2F roof released on Q-58 A proof (V2.13), HELD 17 / 18 in V5 |

The new piece proves the layouts behind those counts; it does not count rolls.

## 2. What the proof does (general, every villa)

The surface the membrane must cover is rebuilt here from the outline alone, edge by edge (floor, one 0.20 m flap per
outer edge, a mitred corner piece at every convex corner, openings cut out with one 0.20 m flap inside each opening
edge: UP-WP-003, Q-29, Q-35 C), never from MEMBRANE_FOLD_V3.required. Then
`R = difference(set_precision(surface, 1 mm), set_precision(union of the laid sheets, 1 mm), grid_size = 1 mm)`
(R-07). Every piece of R must be numerical (at most 1 cm2, the engine's own limit MEMBRANE_FOLD_V2.COVER_TOL_M2) or lie
inside a declared patch whose m2 equals the unsnapped residue it holds; otherwise UNDECLARED_RESIDUE. A declared patch
over no residue is PATCH_WITHOUT_RESIDUE. Each sheet is checked against its strip record (length, width <= roll,
spliced pieces <= roll with the end lap), the side lap between bands (>= 0.10 m), every end-lap seam over the surface
(a seam under a third sheet is closed), the band count (>= ceil((D - lap) / (W - lap)), D = floor across + 2h) and the
engine's layout frame (every corner maps back onto the outline as given, within 1 mm).

Places where one flat sheet would have to serve two faces are listed, never assumed covered:
ADJACENT (an internal corner: the two flaps share 0.20 x 0.20 at a right angle, MEMBRANE_FOLD_V2's "corner pieces by
detail") and OPPOSED (two faces of a wall, pier or slot thinner than 0.40 m, or a flap over floor beyond a wall thinner
than 0.20 m). No Urban rule covers how the OPPOSED case is cut; it does not occur on the development villa.

## 3. Synthetic proof (not the development villa), tests/t137_membrane_coverage (74 tests)

Hand cases: rectangle 3.00 x 4.00 surface 14.96 m2 and 4 bands; L shape internal corner 0.04 m2; 0.10 m wall stub
1.50 m long OPPOSED 0.45 m2 + ADJACENT 0.04 m2; 5.00 x 4.00 with a 0.60 m opening surface 23.72 m2, corners 0.16 m2;
R-07's step miss reproduced on MEMBRANE_FOLD_V2's strips (step parallel to the strips, residue 4.00 x 0.20 = 0.80 m2,
undeclared) and closed by V3; T-096 fixture N residue 0.40 m2 on V2's strips; band bound at D = 1.00 / 1.90 / 1.91 /
3.40 m (1 / 2 / 3 / 4 bands); 45-degree splay with all corner patches matched; outline narrower than one strip.
Mutations that must fail: a sheet removed, a strip 0.05 m shorter than recorded, bands 0.05 m apart (side lap), a strip
cut in two with no end lap, a patch with no residue, a patch with the wrong m2, a surface that disagrees with V3, a
frame shifted 0.01 m. Units (mm and m), mirror, quarter turn and a 30-degree turn give the same proof. Generator:
24 + 24 random outlines (unions of rectangles on a 0.05 m grid, plus a chamfered corner, a column opening, a random
turn), every V4 wall-frame layout proved. Outside the suite, 700 more random outlines (one the fold itself refuses as not simple, held): 0 failures in any layout.

## 4. Development villa (Drive architectural DXF, sha256 ab54dd55...31cc4 = manifest), every area V2.13 folds

688 layouts proved (the four V3 layouts read by V2.12 / V2.13 and every V4 / V5 wall-frame layout): 0 failed,
104 PROVEN, 584 PROVEN_EXCEPT_DETAIL (internal corners only). The independently built surface equals the V5 ledger's
installed m2 in every area (e.g. 2F roof 134.325 m2, largest wet area 16.66 m2).

| Floor | Area id | Floor m2 | Layouts | V2.13 chosen: rolls, proof | Patches m2 = residue m2 | V5 chosen: rolls A/B/C, proof | Internal-corner m2 | Thin-wall m2 |
|---|---|---|---|---|---|---|---|---|
| GF | GF-RA3AD49 | 9.63 | 8 | 2, except detail | 0 = 0 | 2/2/2, except detail | 0.0700 | 0 |
| GF | GF-RDBD4F9 | 4.7307 | 12 | 1, except detail | 0.0240 = 0.0240 | 1/1/1, except detail | 0.0166 | 0 |
| GF | GF-RD6F891 | 3.7177 | 12 | 1, proven | 0.0034 = 0.0034 | 1/1/1, proven | 0 | 0 |
| GF | GF-RB62B55 | 3.375 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| GF | GF-R8496F0 | 3.1325 | 8 | 1, except detail | 0 = 0 | 1/1/1, except detail | 0.0100 | 0 |
| GF | GF-RF38DAF | 2.6752 | 12 | 1, proven | 0.0537 = 0.0537 | 1/1/1, proven | 0 | 0 |
| GF | GF-RB28769 | 2.3676 | 12 | 1, except detail | 0.0537 = 0.0537 | 1/1/1, except detail | 0.0100 | 0 |
| GF | GF-RDF7D28 | 2.3625 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| GF | GF-RFAD3C4 | 1.95 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| GF | GF-RD36087 | 1.485 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| 1F | 1F-R26FA0D | 10.151 | 8 | 2, except detail | 0 = 0 | 2/2/2, except detail | 0.0900 | 0 |
| 1F | 1F-R8BDA49 | 5.0225 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| 1F | 1F-R48AA46 | 5.0225 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| 1F | 1F-R48CDA5 | 4.725 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| 1F | 1F-RED23B8 | 3.5775 | 8 | 1, except detail | 0 = 0 | 1/1/1, except detail | 0.0100 | 0 |
| 1F | 1F-R52AC05 | 2.646 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| 2F | 2F-RE83BED | 5.55 | 8 | 1, proven | 0 = 0 | 1/1/1, proven | 0 | 0 |
| GF | GF-RC99C2A (pantry, printed 4.50 x 3.00) | 13.5 | 8 | 2, proven | 0 = 0 | 2/2/2, proven | 0 | 0 |
| 2F | SH03:2F:AT379 (roof, 2 dome openings) | 115.8321 | 436 | 17 (Q-58 A proof), except detail | 0.0633 = 0.0633 | 17/18/18 HELD Q-58, except detail | 0.3314 | 0 |
| 1F | SH04:1F:AT216 (roof) | 32.721 | 8 | 6, except detail | 0 = 0 | 6/6/6, except detail | 0.0400 | 0 |
| 1F | SH04:1F:AT220 (roof) | 55.5592 | 84 | 8, except detail | 0.0111 = 0.0111 | 8/8/8, except detail | 0.0800 | 0 |

Totals: wet areas 21 rolls (V2.13 and V5 A), internal-corner places 0.2066 m2 in the chosen wet layouts; roofs 31 rolls
(V2.13), internal-corner places 0.4514 m2. Roll counts unchanged; no defect in any count.

## 5. What we learned

- The 2F roof's R-07 step and the dome-opening upturns are fully closed by V3's upturn-only strips and the declared
  patches: no bare membrane in any layout (the owner's Q-58 A condition "prove corners and terminations" now has a
  geometric proof for coverage; the cutting of the corner pieces is still by detail).
- R-07's band bound ceil(D / 0.90) overstates by one when D - 0.10 is a multiple of 0.90 (D = 1.00 m takes one strip);
  the exact bound is ceil((D - lap) / (W - lap)).
- A flat union surface hides double need: at an internal corner the two upturns share 0.04 m2 of flat sheet that has
  to rise on two faces. V2 already counts those corners; a wall stub or slot thinner than 0.40 m would hide up to
  2 x h x its length per face pair. Not on this villa; any villa with a shower stub can hit it (reported, never assumed).
- Engine finding (not a count change): one 2F dome opening touches the roof outline (0.000 m; the other is 1 mm away).
  The outline is valid as drawn, but MEMBRANE_FOLD_V4 turns it into 109 wall frames (each dome chord is a frame) and in
  43 frames (172 layouts) the turned outline self-intersects by rotation noise; V4 folds it as it is. The proof repairs
  it only when the area is kept and warns OUTLINE_INVALID_AFTER_TURN. The chosen layouts are in the drawing's own frame
  and are not affected.
- An END_LAP seam inside the next band's side lap is closed by the third sheet (found on a chamfered synthetic room:
  V3's upturn-only piece meets its main strip with 0.029 m of end lap there, under band 2's sheet).

## 6. Missing

Wiring as a guard into the V3.0 candidate (lane I); a cut plan for the internal-corner and thin-wall pieces (by detail,
no Urban rule); the 2F top roof (Q-34 parked).

Run: `python3 -I research/agents_t137/alsenan_t137_run.py <P7757.dxf> --out <scratch>/t137.json --zone-length 4.50
--zone-width 3.00` (about 4 minutes; the 2F roof's 436 layouts take most of it).
