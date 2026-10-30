# T-367: B9-04 masonry joint mortar on the V3.0.26 block lines (MASONRY_JOINT_MORTAR_V1, R-T367-1)

Worker 2 (lane A), claim 2026-10-30 08:45 UTC, base working head 88ef8cb8 (T-279 MERGED, ARCH_TAKEOFF_V3.0.26 = candidate
of record). Research only: a new unwired module, an application script, its ledgers and tests; no engine, rule,
knowledge or registry file changed; no candidate or released line moves; nothing released (released default V2.9 +
route G). Drawings are cited by Drive folder and title only. ERS read: s.2.1, s.2.2, s.2.3, s.2.4, s.3 (installed vs
procurement; build before deduct), s.4, s.7.

## 1. Physical element (ERS s.2.1)

The installed laying mortar of a MORTARED (black cement block) wall: the bed joint under every course and the perpend
(head) joint after every unit, filled through the full wall thickness for solid units (owner Q-60 / Q-75 call the black
units solid). Unit m3, element = each wall (or established piece) of a V3.0.26 MAS.BLOCK part line. Three quantities
kept apart (ERS s.3): (1) installed wet joint volume (this task, a physical quantity of the built wall); (2) procurement
mortar (waste, dry factor: needs named sources, HELD); (3) cement / sand (needs a named MASONRY mix, HELD). White AAC
walls are laid with a thin-bed adhesive: another material, no joint volume, kept apart and HELD (owner 2026-10-29: the
10 mm joint is for mortared blocks, "not AAC thin-bed").

## 2. Evidence (hierarchy s.2.2)

1. Drawings: no Alsenan sheet prints a block product, joint or mortar mix (T-091 printed-notes census, re-cited by
   T-176; nothing re-read this run).
2. Specification: MPW 1990 section 04220 not readable through the connector (T-176 s.2: data item, unchanged).
3. Owner rules: Q-75 decision 2026-10-23 14:15 (40 x 20 module PROVISIONAL: 39 x 19 face + 1 cm joint from the owner's
   2025 sales-order record; mortar to be verified against the actual joint geometry before VERIFIED; waste never a
   hardcoded %); owner session 2026-10-29 (provisional 10 mm bed joint for mortared blocks, not AAC thin-bed); Q-60 A
   (white pallet data, adhesive coverage HELD); Q-53 C (cement / sand DERIVED from a mix, constants "not universal");
   Q-45 B (1:4 = the bed under / behind TILES: another physical layer).
4. OWNER_QUESTIONS_ANSWERED searched for a masonry mix: none. Q-45 B's "1:4 for walls" is the 2 cm wall mortar behind
   wet-wall tiles; Q-53 C's 1:3 is the stair marble bed; finish_materials_table.py's 1:4 is the finish bed. Each governs
   another layer and is NOT borrowed (refused in code).

## 3. Reconstruction (first principles; owner manual method and drawing-derived method)

Module (w + j) x (h + b) = (0.39 + 0.010) x (0.19 + 0.010) = 0.40 x 0.20. Per m2 of wall face:

- joints: bed = (1 / 0.20) courses x 1.00 m x 0.010 x t = 0.050 t; head = 12.5 units x 0.19 x 0.010 x t = 0.02375 t;
- identity: t x (1 - 0.39 x 0.19 / 0.08) = t x (1 - 0.92625) = 0.07375 t (the module asserts both agree);
- t 0.15 -> 0.0110625 m3 / m2 (bed 0.0075 + head 0.0035625); t 0.20 -> 0.01475 (bed 0.010 + head 0.00475);
- lay-out check (test): course by course, 4.00 x 2.00 x 0.20 = 0.118 m3 = 8 x 0.01475; a non-modular 3.13 x 2.77 x 0.15
  wall lies within one joint strip per edge of the identity. The same per-m2 figures as the merged T-176 module
  (BLOCK_PROCUREMENT_V1, independent code; asserted equal in the test).

Owner manual method: the owner gives no separate mortar method; his 2026-10-29 provisional 10 mm joint and the Q-75
module ARE the inputs above. Drawing-derived method: no sheet prints a joint, so there is no second figure; the only
open physical alternative is the supplier's unit height: a 200 mm-high unit (module 0.40 x 0.21, the owner's T-355
example) gives t x (1 - 0.078 / 0.084) = 0.0714 t, shown BESIDE in every row, never merged (supplier data item, Q-75).

## 4. Result: wall by wall on the V3.0.26 lines (MORTAR_BY_WALL_T367.csv, MORTAR_BY_LINE_T367.csv)

Part line ids are computed with engine.source.boq_line.line_id on the arch_v3026.part_line identity (project, MAS.BLOCK,
parent element + '#BLOCKWORK:<status> <type>', R-T279-1, T-279, m2); 19 part ids = the 19 parts of T-279 s.2.

| Floor / t | Parent line | V3.0.26 part line (area status) | Black walls | m2 | mortar m3 (0.40 x 0.20) | beside 0.40 x 0.21 |
|---|---|---|---|---|---|---|
| GF 0.15 | L-0d9b9e89bb6455da475d | L-87e0023741a8e2d98b21 (VER) | GF-W21, GF-W33 | 9.8950 | 0.109463 | 0.106018 |
| GF 0.15 | | L-adb393d6db51056d343b (DC) | GF-W19, GF-W22 | 21.5261 | 0.238132 | 0.230637 |
| GF 0.15 | | L-abf15bdf70ccf1e7b474 (OA) | GF-W28, GF-W29 | 24.2374 | 0.268126 | 0.259686 |
| GF 0.20 | L-4165954ce4871eda30cc | L-1c53fadb2f92d1f36d4e (VER) | GF-W01 | 62.1640 | 0.916919 | 0.888057 |
| 1F 0.15 | L-c22e309433e7b671cf2d | L-73acd5a9d7e7cf6515c1 (VER) | 1F-W20, W21, W22 | 52.3180 | 0.578768 | 0.560550 |
| 1F 0.15 | | L-4054259959463edd70fb (DC) | 1F-W18, 1F-W24 (part) | 25.2727 | 0.279579 | 0.270779 |
| 1F 0.15 | | L-a56a8add7812d1b52cb7 (OA) | 1F-W12, W13 (part), W17 (part), W19, W23 | 58.2529 | 0.644423 | 0.624138 |
| 1F 0.20 | L-5ffa7157a2fe483dd008 | L-10dd62f66ad05488e63b (VER) | 1F-W02, W03, W09 | 23.9000 | 0.352525 | 0.341429 |
| 2F 0.15 | L-246f3c09de4c6b90efe5 | L-e1e06ec149b44d4f6f8a (OA) | 2F-W08 | 9.6400 | 0.106643 | 0.103286 |
| 2F 0.20 | L-afe984a62285e133ec2f | L-76a4d8e50423fb02b914 (VER) | 2F-W01, 2F-W06 | 21.6600 | 0.319485 | 0.309429 |
| 2F 0.20 | | L-a6eedf5e4adec6d07618 (DC) | 2F-W05 (part) | 3.8000 | 0.056050 | 0.054286 |
| **Black, 24 walls / pieces** | | | | **312.6661** | **3.870113** | **3.748294** |

- Closure (acceptance b): black 0.15 201.1421 + black 0.20 111.5240 = 312.6661 m2 = the black share of 579.1011 m2 to
  0.0000 m2; + white established 266.4350 = 579.1011 (asserted in code). Bed 2.623806 + head 1.246308 = 3.870113 m3.
- By AREA status (kept beside): VERIFIED 169.937 m2 -> 2.277160 m3 (11 walls); DRAWING-CONFIRMED 50.5988 -> 0.573762 (5);
  ASSUMED - OWNER-APPROVED 92.1303 -> 1.019191 (8). MORTAR status of every row: **ASSUMED — OWNER-APPROVED** (weakest of
  the area status and the provisional Q-75 / 2026-10-29 module; never VERIFIED until the supplier's actual dimensions
  and joint are on record and the Checker re-derives it, owner 2026-10-23).
- HELD by name, blank, never 0: black walls 1F-W07, 1F-W11, 1F-W14 + 1F-W15, 1F-W16, 2F-W00, GF-W00, GF-W02, GF-W03,
  GF-W08, GF-W09, GF-W13, GF-W14, GF-W23 .. GF-W27, GF-W30 (held walls) and GF-W20, GF-W31, GF-W32, GF-W34 (drop walls,
  U - L x d never evaluated); the held pieces of 1F-W13, 1F-W17, 1F-W24, 2F-W05 (named on their parents); UNKNOWN type:
  GF-H01 (0.40 band), GF-H02.
- White (acceptance b): 18 established walls / pieces 266.4350 m2 (0.20: 240.5500, 0.15: 25.8850) on 8 part lines:
  adhesive HELD (no joint, no coverage, no product: Q-60, T-355 / T-362); 10 white held walls blank. A 10 mm joint on a
  white wall is refused in code.
- D-12 (ST p.8 note 20, walls drawn 0.20 / 0.15 beside 0.25 columns; T-176 flag by the same wall id, register r2,
  never chosen): GF-W01, GF-W28, 1F-W02, 1F-W18, 1F-W23 carry 1.614691 m3 on 124.3528 m2; if the designer confirms the
  column thickness for a row, that row's mortar scales by 0.25 / t (and its product is not a 15 / 20 black unit).
- Edge tolerance (T-176 s.3, named, not added): (L x b + H x j) x t per wall; not re-evaluated here because the fill
  ledger carries areas, not lengths and heights per piece.
- Course-geometry screen (consistency only, not proof; merged T-355 r2 MESH_LEVELS on the same register v4 pieces):
  bed length implied by the area (5 m of bed per m2) against 3 x the net run at every third course level: on the 20
  WHOLE black walls the ratio is 0.740 .. 0.998 (lower where the top level has no block above it, e.g. a 3.60 m wall
  has 5 levels for 6 course triples, or where openings stack), never above 1.000: no wall's area exceeds what its
  courses can hold. The 4 established-part walls read 0.363 .. 0.905 because T-355's levels include their HELD pieces.
- Change against T-176 (same rate, new area basis): 290.052 m2 / 3.6059 m3 (MASONRY_AREA_V1 r2, 23 walls) -> 312.6661 m2
  / 3.870113 m3 (register v4 in V3.0.26, 24 walls): +22.614 m2, +0.264213 m3, all from the area basis, 0 from the rate.

## 5. Cement and sand (acceptance c)

HELD by name: (1) no masonry laying-mortar mix printed or answered; (2) no approved mortar waste. The derivation is in
code (Q-53 C form: dry = wet x (1 + waste) x dry factor; cement = dry x c / (c + s) x density / bag; sand = dry x s /
(c + s)) and runs only with a mix whose source names masonry / block laying mortar plus a sourced waste and sourced
constants. Lead: a candidate for the ERS s.2.7 / s.6 package (a material genuinely unspecified): "block laying mortar
mix (c : s) and mortar waste for the 3.870113 m3 installed (ASSUMED — OWNER-APPROVED) on the V3.0.26 black walls". Not
asked by the worker.

## 6. Freelancer (acceptance d; Drive 'Alsenan chalet project', the blockwork workbook, cover sheet and quantity sheet)

His workbook has three m2 rows (exterior 559.8015, 15 cm 617.2480, 20 cm 83.6400; total 1,260.6895 m2) and NO mortar,
glue, cement, sand or bag row (all sheet texts searched); his unit-rate column is empty. Reconciliation in m3 (scope,
not a quantity): his 15 / 20 cm areas at the same joint geometry would carry 6.828306 + 1.233690 = 8.061996 m3 vs the
candidate's 3.870113 m3 established. The 4.191883 m3 is wholly area scope (700.888 vs 312.6661 m2 = 388.2219 m2 x the
same per-m2 rates): his storey-height basis, parapets and fence inside his 15 cm row, and the 22 black walls + 4 pieces
HELD blank here; 0 m3 from the mortar rate. **Verdict proposal: RULE_DIFFERENCE** (he measures blockwork per m2 with the
mortar inside the rate; no mortar line exists to compare); no numeric verdict on mortar; the m2 verdicts of T-279 s.4
stand (UNRESOLVED at line level).

## 7. Rule, test, lessons row

R-T367-1 (every villa; provenance T-367; research rule, not a rule-store version): installed joint mortar of mortared
block walls = net installed m2 x t x (1 - face / module), the bed and head split shown; per wall, bound to the MAS.BLOCK
part line that carries the wall; status = weakest(area status, the module's status); thin-bed (AAC) walls carry adhesive
HELD, never a mortar joint; cement / sand only from a mix whose source names masonry laying mortar, never a finish-bed
or stair-bed mix; waste and derivation constants only with a source; held / drop walls blank by name.

Tests: tests/t367_masonry_mortar (villa M367 by hand, not the development villa: normal 0.1475 + 0.0885 + 0.0708 =
0.3068 m3, per-m2 bed / head split, lay-out check, status weakest, module beside; adverse: finish 1:4 table / Q-45 / Q-53
/ porcelain mix borrowed refused, mix without a masonry source refused, AAC with 10 mm refused, held wall as 0 refused,
mm units refused, wall twice refused, closure with a held wall counted refused, unknown status refused, waste as a %
refused; development-villa pins: files reproduce, closure 312.6661 / 579.1011, agreement with merged T-176, every wall
once, 19 / 11 part groups).

Proposed lessons row (ERS s.7): | 2026-10-30 | Masonry laying mortar had a per-m2 rate since T-176 but no wall-by-wall
binding to the candidate's block lines, and three nearby 1:4 / 1:3 values (finish bed, wet-wall bed, stair bed) sat in
the rule store ready to be borrowed for its cement | a mix was recorded by its ratio, not by the physical layer it
governs; mortar was computed on an older area basis | a mortar is bound wall by wall to the line that carries the
wall, its status is the weakest of the area and the module; a mix applies only to the layer its source names (every
villa; T-367) | tests/t367_masonry_mortar (finish mix borrowed refused; AAC as 10 mm refused; held wall as 0 refused) |
PROPOSED |

## 8. For the Checker (re-measure)

- Per m2 by your own joint geometry: 0.0110625 / 0.01475 (and the 0.40 x 0.21 beside: 0.0714 t).
- Black share by your own sum of FILL_T333.csv MAS.BLOCK rows (block_type BLACK, carried, part_status on ESTABLISHED
  PART rows): 201.1421 / 111.5240 m2; then GF 0.20 VER BLACK GF-W01 62.164 x 0.01475 = 0.916919 m3 (the largest row,
  23.7 % of the total) and 1F 0.15 OA BLACK 58.2529 x 0.0110625 = 0.644423 m3.
- One part line id by your own line_id call (e.g. GF-W01 -> L-1c53fadb2f92d1f36d4e) against the V3.0.26 run output.
- The freelancer workbook: no mortar / glue / cement row (cover sheet rows 13-19, quantity sheet).
