# T-355: masonry accessories (blocks section, OPTIONAL items): bed-joint mesh strip (m.l), sharmat column ties (pcs), plaster-stage joint mesh by face class (m.l) (development villa; every villa by R-T355-1 .. 5)

Worker 2 (lane A), claim 2026-10-30 00:45 UTC, base working head b12e10de. Research only: new unwired module, an
application script, tests and generated maps; no engine module, rule, knowledge or registry file changed; no block,
plaster or concrete quantity moves; released default stays V2.9 + route G; nothing here is released. No drawing was
opened this run: every input is a MERGED ledger of this repository (list in t355_alsenan.py). ERS read: s.2.1 (define
the element first), s.2.2 (owner method beside the drawing-derived method), s.2.4 (reconcile in units), s.3 (installed
vs procurement; build before deduct; a notation's meaning before its arithmetic), s.4 (rule + test), s.7 (row below).
Owner basis: Q-77 answer (2026-10-29 21:22) and the owner's four points of 2026-10-29 (T-355 row; OWNER_QUESTIONS.md).

## 1. Physical elements and scope

| Item | What is physically built | Unit | Where it applies (owner) |
|---|---|---|---|
| Bed-joint MESH STRIP | expanded-metal strip in the mortar bed joint over every 3rd block course, where block stands under and over the joint | m.l net installed (lap / waste = procurement, apart) | every block wall, blocks section, optional, priced by quality |
| SHARMAT | ribbed metal tie fixed to the column face, other end in the block bed joint | pcs | each wall-to-column junction, every 3rd course; estimating rule only, SPECIFICATION HELD (material, size, anchorage, embedment, fixing); never a structural design approval; restraint question -> structural consultant RFI |
| Plaster-stage JOINT MESH (B9-03) | strip over a block-to-concrete joint inside a finished face | m.l | by face class A plastered / painted, B tiled, C exterior Sigma, D no plaster = EXCLUDED; B and C kept apart |

Three distinct items: never added into the block m2 (R-T355-5, refused in code), never summed with each other.

## 2. Course module (owner point 1) - ASSUMED — OWNER-APPROVED, PROVISIONAL

- BLACK (conventional mortared, Q-60): provisional 10 mm bed joint (Q-77 point 1) on the actual block height where it
  is available: the owner's own 2025 sales-order record of the black solid blocks, **39 x 19 cm face + 1 cm joint =
  the 40 x 20 module** the Q-75 provisional rule (2026-10-23) already counts with (12.5 / m2). Module **0.190 + 0.010 =
  0.200 m**. The owner's example in point 1 (200 mm block -> 210 mm module) is computed beside it, never merged: it
  applies if the supplier's block is 200 mm high (a supplier data item, Q-75: not an owner decision).
- WHITE (AAC, thin-bed adhesive; ACICO pallet data Q-60, two face families 62.5 x 25 and 60 x 20): no adhesive
  specification -> owner point 1 excludes the 10 mm joint: **every white wall's levels HELD by name** (never 0).
- Course n sits on a starting bed of one joint; its top is at n x 0.200 above the wall base (structural floor); the
  level over course 3k is 0.60 k. A level exists where block stands above it (level + joint < block top); a partial top
  course counts and is reported (11 levels, 18.42 m.l net, sit under a 0.09 / 0.13 m cut top course).

## 3. Results (development villa)

**Mesh strip (BLACK walls, 34 measured of 45 black walls; module 0.200):**

| Floor | Levels | Net installed m.l | HELD m.l (segments) | Module 0.210 net m.l |
|---|---|---|---|---|
| GF | 80 | 208.6005 | 54.2941 | 182.4545 (72 levels) |
| 1F | 102 | 271.5420 | 100.1989 | 269.3324 (99 levels) |
| 2F | 30 | 47.8997 | 25.4000 | 49.5997 (30 levels) |
| **Villa** | **212** | **528.0422** | **179.8930** | **501.3866** |

HELD segments by cause (m.l, each only its own segment): block top over the piece not established 92.1498 (T-274
pieces under a dome ring / conflict beam CB10 / sunken panels D-41 / T-261 HELD pieces); opening sill or head not
established 41.12 (passage openings A-GF-01 / A-1F-01 and lift doors L-1F-01 / L-2F-01: width + 2 x 0.40 at each level); opening station not
tied to a piece of known top 39.6732 (doors on walls that also carry pieces of unknown top, e.g. D-GF-11 / D-GF-12 on
GF-W32, D-1F-08 / 09 on 1F-W13); lintel bearings 6.95 (the printed MIN.40cm each end: actual bearing length not
drawn). Lintel spans are cut as concrete (ST7757.pdf p.13 LINTEL SCHEDULE depth by width band: L1 / L2 0.20, L3 0.30,
L4 0.40, L5 0.55; arched heads W15 / W16 / W17 / W26: lintel not the schedule's -> span HELD above the head).
Openings: T-237 merged sizes (doors 2.20 ASSUMED — OWNER-APPROVED Q-55; windows PRINTED / DRAWING-CONFIRMED), above FFL +
0.10 (Q-43); a door's hole runs from the structural floor; W18 cut at its 0.4673 m in masonry (T-274 scan: jamb 0.0327
inside a column). Module 0.210 vs 0.200: -26.6556 m.l (-5.05 %), mostly GF (block tops 3.75 / 4.34: one level fewer).

**Sharmat:** 117 physical junctions (one per block-segment / column boundary; equals T-317's V joints counted on one
side of each wall, an independent path), of which **31 measured on black walls = 182 ties (module 0.210: 170)**: GF 11
junctions 67 ties, 1F 14 / 79, 2F 6 / 36. HELD 86: white walls 66 (course), lift tie beam 10, annex datum 3, block top
beside the column not established 7 (T-261 piece heights not tied to stations, held pieces). UPPER BOUND named: the
lintel census (research/alsenan_lintels_s8_6, 01_OPENING_CENSUS) lists 8 opening jambs AT a column (7 openings); where
such a jamb lies on a measured junction the ties over the opening height do not exist; its band ids predate register
v2 and do not bind to the current runs (crosswalk not established): not deducted, named.

**Plaster-stage joint mesh by face class** (T-317 merged joint population, INSIDE joints only, residual 0 against
T-317: owner band 281.55 = 2.70 H + 278.85 V; drawing band 528.2021 = 215.172 + 294.44 + 18.59; exterior 230.1438):

| Class | Sides | Owner band m.l | Drawing-derived band m.l |
|---|---|---|---|
| A plastered / painted | 43 | 109.85 | 216.6229 |
| B tiled (T-312 wet rooms) | 38 | 67.90 | 111.0228 |
| C exterior Sigma | 25 | 230.1439 | 230.1439 (one band) |
| MIXED (a side facing a dry and a tiled room, or the pantry backsplash GF-07): class split HELD | 17 | 87.05 | 174.4379 |
| UNKNOWN (an internal side with no room in T-250: shaft / void) | 9 | 16.75 | 26.1185 |
| D no plaster / render | 0 sides in the register | EXCLUDED | EXCLUDED |

Neither band is chosen (the owner did not choose B or C of Q-77; the earlier 281.6 / 528.2 totals are not selected:
they are now split by class, each class kept apart). HELD joints (block top / band not established) stay counted by
name in JOINT_MESH_CLASS_T355.csv.

**Not covered (UNKNOWN by name):** GF-W30, GF-W37, GF-H01, GF-H02, 1F-W25, 1F-W00/W01 BAY-ENDS, GF P-GF-05 ABOVE-LINTEL
(no census run); register group-HELD walls; the lintels' own block-to-concrete joints (no lintel register binding).

**Against the freelancer:** no mesh-strip, sharmat or joint-mesh line: his blockwork sheet (المبانى.xlsx, sheet
الكميات rows 14-227, T-225 census) holds wall runs, deductions, a projection, the fence and parapets only; his plaster /
Sigma workbook has no joint-mesh line (T-317). Verdict proposal: **RULE_DIFFERENCE** (owner-added optional items, Q-77),
not a freelancer omission; NOT COMPARED in %.

## 4. Rules, code, tests

- R-T355-1 .. 5 (module docstring, research/agents_t355/t355_masonry_accessories.py): integer course levels from a
  sourced course spec, no fractional course; net strip with openings / lintel spans cut and only the uncertain segment
  HELD; junctions once (key wall, column station, face), duplicate refused; joint mesh by face class with MIXED held;
  items never folded into the block m2.
- Application: t355_alsenan.py (`--write`, `--check` reproduces every output byte for byte).
- Tests (26): tests/t355_masonry_accessories/test_t355_masonry_accessories.py, NON-Alsenan hand fixture (6.00 m run, two
  0.30 columns, block top 3.00, door 0.90 x 2.20, lintel 0.25, bearing 0.40): levels 0.60 / 1.20 / 1.80 / 2.40, strip
  4.50 / 4.50 / 4.50 / 3.70 = 17.20 m.l + 0.80 held, 2 junctions x 4 = 8 ties; adverse: mirror and mm identical, mm read
  as m refused, wall below 3 courses = no level, wall through a column = 2 junctions, duplicate junction refused, unknown
  height HELD never 0, no course spec HELD, mesh into block m2 refused, sill below the level runs through, unknown
  opening extent holds only its segment, unknown lintel holds span + bearings, opening beside an unknown piece held not
  cut, cut wider than the block refused, partial top course reported, module 0.200 vs 0.210 level count, face classes,
  lintel bands. test_t355_alsenan_pins.py: outputs reproduce; 117 junctions = T-317 V joints; class totals close to
  T-317; white walls HELD never 0; headline figures.

## 5. For the Checker (re-measure)

1. Course: Q-77 point 1 wording (T-355 row OWNER ANSWERS) and Q-75 decision 2026-10-23 (OWNER_QUESTIONS.md); the 39 x 19
   + 1 cm module in the owner's takeoff notes (skill quantity-takeoff-rules, black solid blocks).
2. Two walls by hand: GF-W01 (T-274 run GF|WB-FL0001-FL0002#2: run 19.27 - columns 0.40 + 1.10 + 0.50 + 0.70 + 0.10 =
   16.47 m block; tops CB8 0.75 -> 3.75, B1 0.40 -> 4.10; 6 levels; 16.4674 x 6 = 98.8044 net, 0.0026 m sliver HELD) and
   GF-W28 (door D-GF-13 1.00, head 2.30 above the structural floor, L1 lintel 0.20: levels 0.6 / 1.2 / 1.8 cut 1.00,
   2.4 span cut + 0.80 bearings HELD, 4.2 only over the 4.34 pieces).
3. Junction census: SHARMAT_T355.csv vs T-274 COLUMN pieces; ties at top 3.75 = 6 (0.200) / 5 (0.210).
4. Face classes: T-250 side rooms x T-312 tiled rooms (GF-02 / 03 / 05 / 06 / 10 .. 14 / 16, 1F-02 / 03 / 07 / 08 / 09 /
   12, 2F-02); pantry GF-07 MIXED.

Proposed lessons row (ERS s.7): *Problem*: a per-course accessory was first framed as wall height / 3 courses x length
(fractional courses, strip through openings, junctions per side). *Root cause*: the element (a strip in one bed joint,
a tie at one block end) was not defined before the arithmetic. *Rule*: integer course levels from a sourced course
spec; per level the block physically present, openings and lintel spans cut, uncertain segments HELD; junctions once
per physical block end at a column; thin-bed blocks without a specification HELD (every villa). *Test*:
tests/t355_masonry_accessories. *Status*: PROPOSED.
