# T-071: exterior spaces drawn on their own layer (roofs, balconies, pool, void, garden)

Worker 3, 2026-10-19. Development villa (Alsenan), not an accuracy claim. Areas, lengths, counts and entity handles only.
Method piece `engine/source/exterior_spaces.py` (EXTERIOR_SPACES_V1), NOT wired: no released method, face, room or quantity
changes. Rules: UP-WP-ROOF-001, UP-WP-003, UP-QTY-STATUS-001; owner answers Q-24 (roof like a bathroom, inside the
parapet, 0.20 m upturn, dome upturn), Q-25 (every drafting gap closed by the membrane, listed), Q-29 (dome positions are
open skylights).

## 1. What the piece does (general, no names coded)

For every exterior label the T-061 guard holds (ROOF, BALCONY / TERRACE, POOL, VOID, GARDEN; English and Arabic via
ROOM_VOCAB_V2) and for every layer the run typed OTHER: the layer's lines + the room builder's own boundary items + the
closures of free parapet ends (each straight own-layer end that touches nothing is extended along its own direction to
the first line it meets, search reach = the engine's existing THIN_LIMIT_M 0.45 m) are noded on a 0.1 mm grid and
polygonized; the face round the label gives A (net of closed shapes inside), its perimeter split (own layer / building /
closure), every closure with what it meets, the closed shapes inside, and B (A widened by the measured parallel band of
the own-layer edges; review only, the owner chose A).

| Code | Status | Quantity |
|---|---|---|
| ROOF | RELEASED_METHOD_PIECE (Q-24) | membrane = A net; upturn = whole A boundary (parapet + walls + closures) + ring of each closed shape that is an opening, x 0.20 m; gap cover listed (gap, 0.10 m lap, 0.20 m upturn, Q-25) |
| BALCONY | PROVISIONAL (UP-WP-ROOF-001, as `owner_finish_scope.exterior_wp_lines`) | membrane = A; upturn HELD EXTERIOR_WP_UPTURN_BY_SPECIFICATION |
| POOL | HELD POOL_NO_MEMBRANE_RULE | geometry attached |
| GARDEN | HELD EXTERIOR_SCOPE_UNRESOLVED (OQ-04) | geometry attached |
| VOID | UNSUPPORTED VOID_OPEN_TO_BELOW | geometry attached |

Never released, never 0: no units (UNITS_MISSING); no layer closes a face within the reach (NO_CLOSING_LAYER); two OTHER
layers close different faces (AMBIGUOUS_BOUNDARY_LAYER); a recognised opening of the run (door / window / passage opening,
door swing, gate) on a gap (GAP_HAS_OPENING, Q-25); a closed shape inside a roof that no label (DOME, SKYLIGHT, قبة ...) or
project fact identifies (its area HELD INNER_SHAPE_UNIDENTIFIED, shown beside the released rest, no upturn round it); a
frame whose WALL-typed layer encloses exterior labels while an OTHER layer separates more rooms (layer_role_check RISK,
T-062 lesson: every record of the frame HELD LAYER_ROLE_RISK). Two labels in one face are reported once each, the face is
counted once (`counted_with`).

## 2. Alsenan (P7757 DXF, sha256 ab54dd55...31cc4; ARCH_TAKEOFF_V2.9, working branch 97c4bfc, Python 3.11)

Project facts (`research/agents_t071/alsenan_facts.json`, handles only): the two circles on the 1F roof shown on the
second-floor plan (R221 printed beside each) are open skylights, owner Q-29 with Q-24. Run:
`python research/agents_t071/run_alsenan.py <P7757.dxf> research/agents_t071/alsenan_exterior_spaces.json --facts ...`.

| Roof (label, level) | A net m2 | Upturn lm (parapet / building / closure / skylight rings) | Closure | T-062 hand |
|---|---|---|---|---|
| 1F west (+4.30) | 55.559 | 35.727 (31.402 own edges; 4.125 building; 0.200) | 0.200 m to wall + column, no opening on it | 55.560, 35.727 |
| 1F south-east strip (+5.50) | 32.721 | 52.940 (33.922; 18.613; 0.405) | 0.405 m to wall + column, no opening | 32.721, 52.940 |
| 2F level roof (+9.70; 2 labels, 1 face) | 115.832 (146.532 - 2 x 15.350 skylights) | 92.922 (48.265; 16.800; 0.075; 2 x 13.891) | 0.075 m to wall, no opening | 146.532 - 30.716 = 115.816 |
| **Total** | **204.112** | **181.589 lm = 36.318 m2 at 0.20 m** | 3 gaps, 0.680 m | 204.097 m2, 181.59 lm |

The own / building split differs from T-062 by 0.474 m on the west roof (a piece where the parapet line runs on a wall
line counts as building here); the totals are identical. The door-layer line in each gap (T-062) is not a recognised
opening of the run, so each gap is closed (Q-25). Second check: T-062's topology trace (another algorithm) and its hand
calculation from corner dimensions give the same A and perimeters; the printed radius R221 = the drawn 2.211 m circles.
Without the facts file the two circles are HELD (30.70 m2 shown) and the 2F upturn is 65.14 m.

Other labels: pool (2 labels, one face): layer 5 closes 8.576 m2 (B 10.932), layer 2 closes 1.11 / 1.07 m2 round the
labels: HELD (no membrane rule; also ambiguous). Court / yard (4 labels, one face): 167.067 m2 net, 177.299 filled, one
0.232 m closure: HELD (OQ-04). 1F void: layer 5 oval 3.820 m2, layer 2 2.613 m2: UNSUPPORTED. Layer roles: wall layer `1`
encloses no exterior label: OK on all three frames.

## 3. Engine vs freelancer (one line "roofs and annexes")

| Item | Engine (this piece, not wired) | Freelancer | Difference | Was |
|---|---|---|---|---|
| Roof membrane m2 | 204.112 (3 roofs measured, A basis) | 285.00 | -80.888 m2 (-28.38 %) | no roof line (labels held, no area) |
| Roof upturn lm | 181.589 (incl. 27.782 round the 2 skylights) | 194.00 | -12.411 lm (-6.40 %) | none |

Not measured (stays out, never 0): the 2F block's own top roof (+13.90, parapet 0.50 printed on the elevations) is on no
plan frame of the DXF or of the PDF sheets read (T-062, T-063); the 2F floor plate is 55.08 m2 (engine plate, not a roof
outline), so it is the most likely part of the freelancer's 285 m2 but not proved; the 6.130 m2 behind the 0.20 m parapet
round the 1F void (+5.50, no ROOF label); the third dome stands on that top roof.
Verdict proposals: membrane and upturn UNRESOLVED as totals (the freelancer's single line cannot be split per roof and
includes a roof with no plan); on the three plan roofs ENGINE_RIGHT by hand: 11.8 x 1.3 + 10.4 x 3.2 + (4.0 x 1.8 -
(1.1^2 - pi 1.1^2 / 4)) = 55.560; 18.97 x 1.30 + 1.30 x 6.20 = 32.721; 18.87 x 5.0 + 4.2 x 2.1 + 6.57 x 6.6 - 2 pi
2.211^2 = 115.816 m2 (engine 115.832, chord error +0.016).
Proposed for the lead (not asked by the worker): which drawing gives the 2F top roof outline (a roof plan, or the 2F plan
outer walls with the 0.50 m parapet printed on the elevations).

## 4. Tests (`tests/t071_exterior_spaces`, 20 pass)

Synthetic villa (not Alsenan) by hand: roof 41.200 m2 filled, dome r 0.80 (2.011), A net 39.189, perimeter 27.00 + 11.20 +
0.20 = 38.40 m, dome ring 5.027 m, B 46.239; balcony 3.00 x 1.50; D pool 3.571; void 1.500; a TERRACE with no line round
it. Variants m, mm, rotated 37 deg, mirrored, rotated + mirrored in m. Cases: labelled dome (opening), unlabelled circle
(held part), project fact OPENING / MEMBRANE_UNDER, gate on a gap (not closed), reach too short (held), units missing,
two layers closing different faces, two labels one face, layer-role RISK (unit and through the real run with no layer map),
report rows carry no geometry. The T-062 synthetic check moved here (`test_t062_synthetic_plan.py`) and also runs the
real V2.9 run -> guard -> EXTERIOR_SPACES_V1 on the same plan in all five variants.
