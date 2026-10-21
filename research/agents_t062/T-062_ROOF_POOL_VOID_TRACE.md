# T-062: why the roof, pool and void labels sit in no closed room (Alsenan, read-only)

Worker 2, 2026-10-19. Diagnostic only: no engine, rule or quantity change; no basis decided. Development villa, not
an accuracy claim. Counts, entity handles, areas and lengths only (no coordinates, no client data).

## Input and run

Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip" -> P7757.dxf, sha256 ab54dd55...31cc4 (= SOURCE_MANIFEST),
read outside the clone. Working branch 8774071 (first run on 6def656: identical JSON), Python 3.11, ARCH_TAKEOFF_V2.9. Tool: `research/agents_t062/roof_trace.py`
(general: no layer, room or project name in code). Census reproduced: 41 labels, 11 SILENT_OMISSION (all NO_ROOM), as T-004a.

## 1. The failing stage (same for all 7 labels)

| Label | Floor | Code (V1 vocabulary) | In a bounded face of the engine's own boundary set? |
|---|---|---|---|
| AT216, AT220 | 1F | ROOF | no |
| AT379, AT385 | 2F | ROOF | no (both labels lie in one face once traced) |
| AT19 (Arabic "swimming pool"), AT20 | GF | BATHROOM (V1; POOL in V2.10), POOL | no (both in one face once traced) |
| AT225 | 1F | VOID | no |

Stage: `engine/source/arch_rooms.py:1082-1096` (`spaces`) builds the room arrangement from the lines of the WALL,
COLUMN and WINDOW layers only (plus thresholds, wall caps, door closures). On this drawing the roof edges / parapets,
the pool outline and the void outline are all drawn on layer `5`, which `engine/source/arch_v27.py:198`
(`layer_roles`) types OTHER (layer `5` also carries stairs, furniture, the plot boundary: 1,287 segments on 1F). So
each label lies in the unbounded face of the wall network, `engine/source/topology.py:594` (`sites_of`) returns
bounded faces only, and `arch_rooms._faces_of` (`arch_rooms.py:408`) never sees the label. Not a closure defect of
the wall network: the bounding linework is simply not admitted. Tested directly: the run's own pass-1 items give no
bounded face for any of the 7 labels (`engine_boundary_face: null`).

Second-level cause (would remain if layer `5` were admitted): the parapet lines stop short of the wall they meet, on a
line of the door layer `D`; with layer `5` alone the roof faces leak (1F: 39.111 / 207.775 m2 faces, 2F: 370.384 m2
= the plot). Measured gaps (line extended along its own direction to the first wall line):

| Roof | Parapet lines (inner, outer) | Gap to the wall | What sits in the gap |
|---|---|---|---|
| 2F roof | D2:4793, D2:4805 | 0.075 m to wall D2:4744 | a 2.10 m line on layer `D` (D2:4834) drawn as the block's outer face |
| 1F west roof | D2:2869, D2:2870 | 0.200 m to wall D2:2874 / column | line D2:2876 on layer `D` |
| 1F south-east roof | D2:3035, D2:3036 | 0.405 m to wall D2:2912 / column | a ledge outline on layer `D` (D2:3230) |
| GF pool | closed by layer `5` alone (4 edges: 3 lines + 1 bulge arc) | none | - |
| 1F void | closed by layer `5` alone (4 bulge arcs, oval) | none | - |

General lesson (synthetic check): with no layer map, `layer_roles` picks ONE primary wall layer; on the synthetic plan
it chose the parapet layer as WALL and typed the real wall layer OTHER (roof labels then HELD as EXTERNAL). Roof and
parapet layers are a layer-role risk on any villa, not an Alsenan quirk.

## 2. Areas measured by hand from the drawing (both candidates; basis not decided)

A = inside the parapet inner face (the drawn edge round the label), up to the upper floor's wall faces.
B = to the parapet outer face: A widened by the parapet band on every parapet edge. Band width measured, not assumed:
the first parallel layer-`5` line outside the edge is at 0.200 m on most of the edge length (1F west 21.48 of 30.93 m,
1F south-east 21.36 of 28.67 m, 2F 29.54 of 48.27 m; the rest shows extra lines at 0.075-0.15 m and 0.30-0.55 m, read
as coping / cornice lines, not used). Every value below was recomputed by hand from the face's corner dimensions:

| Roof (label, printed level) | A m2 | A perimeter m (parapet / building / closure) | B m2 | B outer perimeter m | Hand check |
|---|---|---|---|---|---|
| 1F west (AT220, +4.30) | 55.560 | 35.727 (30.928 / 4.600 / 0.200) | 61.896 | 37.242 | A = 11.8 x 1.3 + 10.4 x 3.2 + (4.0 x 1.8 - (1.1^2 - pi 1.1^2 / 4)) = 55.560; B with the 0.20 band (arc r 1.30) = 61.897, perimeter 37.242 |
| 1F south-east L strip (AT216, +5.50) | 32.721 | 52.940 (28.665 / 23.870 / 0.405) | 38.655 | 54.540 | A = 18.97 x 1.30 + 1.30 x 6.20 = 32.721; B = 19.37 x 1.50 + 1.50 x 6.40 = 38.655 |
| 2F roof (AT379 + AT385, +9.70) | 115.814 net of the two dome footprints (146.532 with them) | 65.140 (48.265 / 16.800 / 0.075) + 27.78 round the domes | 125.656 net (156.36 with domes) | 67.140 | A = 18.87 x 5.0 + 4.2 x 2.1 + 6.57 x 6.6 = 146.532; domes 2 x pi x 2.211^2 = 30.718 (the polygon gives 30.704); B polygon 19.27 x 5.2 + 4.4 x 2.3 + 6.77 x 6.8 = 156.36 |
| total of the 4 ROOF labels | 204.095 (234.799 with dome footprints) | 153.807 (+27.78 dome rings) | 225.947 (256.651 with domes) | - | B total after removing the 0.20 x 1.30 = 0.26 m2 divider strip counted by both 1F roofs |

Held, not added: the area north of the 1F south-east roof, round the oval void (6.130 m2 net of the 3.825 m2 void), lies
behind another 0.20 m parapet pair (D2:3035 / D2:3036) and carries the printed level +5.50 (AT364) but no ROOF label: whether
it is roof is not printed on the plan. The two 1F roofs are separated by a 0.200 m double line (west roof +4.30, south
roof +5.50: two levels). Cross-check on a second plan: shifted onto the floor below (frames 45.000 m apart), 100 % of both
1F roofs lies on the GF floor plate and 145.079 of the 146.532 m2 2F roof (99.0 %) on the 1F plate; the GF plate minus the
1F plate is 100.890 m2 = 1F roofs 88.281 + area round the void 6.130 + void 3.825 + parapet bands (about 2.7).

Pool (GF, AT19 + AT20 in one face): A = water plan 8.579 m2 = pi x 1.55^2 / 2 + 1.55 x 3.10 (half circle + rectangle),
perimeter 11.069 m; pool wall drawn 0.200 m: to its outer face on the curved, north and south sides 10.236 m2
(pi x 1.75^2 / 2 + 1.55 x 3.50), 10.932 m2 if the 0.20 m band is also taken on the east side, where the pool edge is the
boundary-wall line. Void (1F, AT225): the oval drawn on layer `5` holds 3.825 m2 (perimeter 7.139 m); a void is excluded
by rule (open to below), so the right status is UNSUPPORTED like the other 1F void (AT215), not silent.

## 3. Engine vs freelancer (Alsenan, development reference)

| Item | Engine today | This trace (not wired) | Freelancer | Difference |
|---|---|---|---|---|
| Roof waterproofing m2 ("roofs and annexes", one line) | no roof line: the 4 ROOF labels are silent in V2.9 (held with no area by the unwired T-061 guard) | A 204.095 / A + domes 234.799 / B 225.947 / B + domes 256.651 | 285 | A -80.9 m2 (-28.4 %); A + domes -50.2 (-17.6 %); B -59.1 (-20.7 %); B + domes -28.3 (-9.9 %) |
| Roof upturn lm | none | A perimeter 153.807 (+27.78 round the domes = 181.59) | 194 | -40.2 lm (-20.7 %); with dome rings -12.4 lm (-6.4 %) |
| Pool floor concrete plan area m2 | not reported by the architectural route | 10.236 (3 sides) / 10.932 (4 sides) | 10.8 (x 0.40 m) | -0.564 (-5.2 %) / +0.132 (+1.2 %) |

Not measured: the roof of the 2F block itself (the "annex" in the freelancer's line title) is on no plan frame of this DXF;
its footprint on the 2F plan is 55.08 m2 (engine plate), so the freelancer's 285 m2 may include it, but that is not proved.
The 47 Arabic labels in an unmapped SHX font (T-004a) may include more roof labels: unread.

Verdict proposals for the verifier: roof waterproofing and upturn UNRESOLVED (basis A or B, dome footprints, the
annex roof and the area round the void are owner decisions; the engine gap itself is an ENGINE defect: labelled roofs
silent); pool plan area RULE_DIFFERENCE (water face vs outer wall face; depth and wall height not read here, see T-063);
void: ENGINE gap (silent instead of UNSUPPORTED).

## 4. Proposed fix task (for the lead)

T-061's `engine/source/room_label_guard.py` (on the working branch, not wired) already turns each of these labels into
HELD ROOM_LABEL_NO_FACE with no area, which is the right state until the owner answers. Next step after the answer: a new
method piece `engine/source/exterior_spaces.py` (not wired; arch_rooms.py, room_label_guard.py and frozen builders
untouched) that, for each held exterior label (ROOF, BALCONY, POOL, VOID, GARDEN), traces the OTHER layer that closes a
face round it (this script's steps 1-4) and attaches A, B, the perimeter split, the closures and the shapes inside to the
held record; released only on the answered basis; a void gets UNSUPPORTED (open to below); a label with no closing layer
stays HELD with no area (never 0, tested). Fixture: `research/agents_t062/synthetic_check.py` (moved to tests/ then).

## 5. Owner question proposed to the lead (one sentence each; not added to OWNER_QUESTIONS.md by the worker)

1. Roof waterproofing area: (A) inside the parapet's inner face, (B) to its outer face (A plus the 0.20 m parapet), or
   (C) another edge? Example to check by hand: the 1F west roof is 55.56 m2 (A) or 61.90 m2 (B). Blocks every roof line.
2. Domes standing on a roof: is the roof membrane measured under the dome footprints (2 x 15.36 m2 on the 1F roof) or
   not? Blocks 30.7 m2 of the 2F roof.
3. When a parapet line stops 0.075-0.405 m short of the wall it meets (a drafting gap), may the engine close it along
   the line's own direction, or must the roof stay held? Blocks all three roofs on this drawing.

## Synthetic hand check (not Alsenan)

`research/agents_t062/synthetic_check.py`: block 4.40 x 3.40 m on A-WALL, roof parapet on A-ROOF (0.25 m band) stopping
0.10 m short of the walls on a third layer, dome r = 0.80 m, D-shaped pool, rectangular void, and a BALCONY label with no
line round it. Hand: A 41.200 m2 filled, 39.189 net, perimeter 27.00 / 11.20 / 0.20, closures 2 x 0.100 m, band 0.25 m,
B 46.239 net, B perimeter 40.900 m; pool 3.571 m2; void 1.500 m2; BALCONY: no bounding layer, no area. Passes in mm,
metres, rotated 37 degrees, mirrored, rotated + mirrored in metres (B 46.243: circle polygon 0.004 m2 off).
