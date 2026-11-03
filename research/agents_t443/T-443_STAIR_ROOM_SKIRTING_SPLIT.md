# T-443: stair-room skirting split, ARCH_TAKEOFF_V3.0.46 (development villa; method every villa)

Worker 1 (stream F, lane I), 2026-11-03. Gate B integration package on the candidate of record V3.0.45 (T-478,
merge 8ccf69b3, candidate 5972888b). ERS applied: s.2.1 element, s.2.2 evidence (owner manual method and drawing
method side by side), s.2.4 closure in units, s.4 rule + tests, s.7 lesson. No client data, drawing text or coordinate
in this file: handles, room-local lengths, line ids, states and quantities only.

## 1. Scope as built (and one correction to the row)

The row names five "BLOCKED parents": GF L-2175a965 / L-47fa825d and 2F L-10e79bd4 / L-dd6930fd / L-b8d4a7f0. Read in the
candidate (T-441 summary `parents`, own run): only **L-47fa825d (GF) and L-b8d4a7f0 (2F) are FIN.SKIRTING lm**.
L-2175a965 (GF, BLOCKED) and L-dd6930fd (2F, BLOCKED) are **FIN.CEILING m2** stairwell ceilings and L-10e79bd4 is a
**PROVISIONAL FIN.CEILING decor part 5.6258 m2**, not blocked. They are not skirting and T-441 measured no ceiling: they
stay byte-identical (asserted by the integration). Lead: the row's parent list mixes the T-441 `LINES` table (all
lines on the two stair rooms) with the skirting parents.

## 2. Physical element and methods (ERS s.2.1 / s.2.2)

A room skirting is a strip at the foot of a finished vertical face at the FLOOR level of a floored space. A walled stair
room is not one floored space: it holds floor parts (T-418: GF hall +1.00, GF back lobby +0.30, 2F lobby and 2F arrival
+9.70), flights (B7 stair skirting, T-410), and the open well (no floor, no skirting).

| | Owner manual method | Drawing-derived method (this package) |
|---|---|---|
| Rule | perimeter of each floored part at its level less each door / lift opening by id (UP-SKIRT-001, UP-CER-003) | the merged T-441 face table: each side cut into stretches by DXF handle, faces skirted, openings by id, lift opening whole |
| GF hall +1.00 | 6.550 face side - OP-010 1.000 - OP-020 0.900 = 4.650 lm | 4.650 lm (220 1.400, 21F 0.100, 21C 2.000, 21B 0.050, 298 1.100) |
| GF back lobby +0.30 | 2.300 - OP-013 0.900 = 1.400 lm | 1.400 lm (21B 1.150, 26F 0.1469, 2AB 0.1031) |
| 2F lobby +9.70 | 5.250 - OP-007 0.900 - OP-002 1.000 = 3.350 lm | 3.350 lm (1283 2.000, 1295 0.1016, 1294 0.2484, 1289 0.400, 128A 0.600) |
| 2F arrival +9.70 | 5.150 - OP-001 1.000 = 4.150 lm | 4.150 lm (1282 0.4158, 1283 1.0842, 2F72 / 129A 0.500, 129A 0.200, 12B7 1.950) |

Own re-measure this run (research/agents_t443/t443_handle_check.py on P7757.dxf sha256 ab54dd55, by handle): every
handle drawn length agrees with the stretches citing it (FULL: 1282, 1283 3.0842 = 2F lobby 2.000 + arrival 1.0842,
1289, 128A, 1294, 1295, 21C, 21F, 220, 26F; PART with the rest owned elsewhere: 21B 2.100 = hall 0.050 + D1 east 0.900
(T-410) + lobby 1.150; 298 2.750 = hall 1.100 + 1.650 T-410 MS1-L.W1; 2AB 1.4531 = lobby 0.1031 + 1.350 west of the
lobby (strip face 0.200 + MS1-T north 1.150); 12B7 / 129A / 2F72 the rest beside the slab opening). Residual 0.000 on
every handle.

## 3. What the package does (V3.0.46, engine/source/arch_v3046.py)

Own run this session (research/agents_t443/v3046_run.py on P7757.dxf ab54dd55 + "ST7757 dxf.dxf" 9f9d1179, Python
3.11 venv): V3_0_45_BOQ_LINES.json **5972888b** (= the candidate of record, asserted) -> V3_0_46_BOQ_LINES.json
**0d44e033**, 4861 -> 4868 lines, 2 changed + 7 added, 4859 outside rows byte-identical; totals moved only in
FIN.SKIRTING lm: certain 189.818752 -> **203.368752 lm (+13.550, +7.14 %)**, blocked lines 3 -> 5, held range
unchanged (0 .. 15.730915). Pins: research/agents_t443/summary_t443.json, tests/t443_stair_room_skirting/
test_alsenan_pins.py. Children ids: GF L-af8221bd .. (summary `parents`), 2F L-9ff582c9 / L-dff4f49f.

| Line | Before (V3.0.45) | After (V3.0.46) | Status |
|---|---|---|---|
| L-47fa825d GF stair-room skirting (parent) | BLOCKED_RFI, no figure | BLOCKED_RFI, no figure; remainder = GF-ST-CN strip north face 0.200 (unread, T-418); names its children | HELD (remainder named) |
| SKIRT-T443:GF-ST-HALL (new) | - | MEASURED 4.650 lm (gross 6.550, OP-010 1.000 + OP-020 0.900) | lm DRAWING-CONFIRMED; material HELD with floor L-f53d4986 |
| SKIRT-T443:GF-ST-LOBBY030 (new) | - | MEASURED 1.400 lm (gross 2.300, OP-013 0.900) | lm DRAWING-CONFIRMED; material HELD with floor L-b4441a1b |
| SKIRT-T443:GF-ST-HALL:DIVIDER-BAND (new) | - | BLOCKED_RFI blank; 2.200 (cut) / 3.400 (T-418 outline) lm beside | HELD (RFI a) |
| SKIRT-T443:GF-ST-HALL:OP-020-JAMBS (new) | - | BLOCKED_RFI blank; 0.400 lm beside | HELD (RFI b) |
| SKIRT-T443:GF-ST-LOBBY030:WEST-FACE (new) | - | BLOCKED_RFI blank; 1.150 lm beside if on the drawn line | HELD (RFI c) |
| L-b8d4a7f0 2F stair-room skirting (parent) | BLOCKED_RFI, no figure | NOT_APPLICABLE_WITH_EVIDENCE (no figure): carried by its two children; 9.400 lm beside the slab opening, no floor | NA with evidence |
| SKIRT-T443:2F-ST-LOBBY (new) | - | MEASURED 3.350 lm (gross 5.250, OP-007 0.900 + OP-002 1.000 LIFT, no jambs) | VERIFIED (Checker T-441 own re-measure); porcelain Q-70 A |
| SKIRT-T443:2F-ST-ARRIVAL (new) | - | MEASURED 4.150 lm (gross 5.150, OP-001 1.000) | lm DRAWING-CONFIRMED; material HELD beside the Q-70 A marble landing L-5d2be30d |

FIN.SKIRTING lm certain total: **+13.550 lm** (4.650 + 1.400 + 3.350 + 4.150), every figure before inside a BLOCKED
line with no figure. Nothing else moves (asserted: outside rows byte-identical, totals move only in FIN.SKIRTING).

Closure (R-T443-1 g; refused otherwise): GF run 11.100 = children 6.050 + flight faces owned by T-410 (west 2.800,
MS1-T north 1.150, D1 east 0.900) + remainder 0.200, residual 0.000. 2F run 16.900 = children 7.500 + no floor 1.500 +
3.400 + 4.500, residual 0.000. The held faces (band, jambs, lobby west) are not in the engine run (no wall drawn there):
they are listed as their own lines, never silently in or out.

OP-002 (2F lift landing ELV-01-2F): deducted WHOLE as `LIFT_OPENING`, `jamb_skirting: false`; a jamb return on a lift
opening is refused at load and a lift deduction re-marked as a passage is refused by `check_stair_rooms` (register LIFT
DOOR GAP IN SKIRTING; lessons row 2026-11-01). The ARCH.PASSAGE line L-c91732d6 that still counts OP-002 as a passage
piece is an openings item: untouched here, named for the openings owner.

## 4. Rule, tests, lesson

- R-T443-1 (every villa; module docstring): integrates R-T441-1 .. 4: cover each side once; faces need a handle;
  openings by id, lift whole without jambs, door jambs never; one base one owner against the merged stair side stretches
  (level-aware); no face in two children; held blank with cause; the engine run closes in lm or the split is refused.
- tests/t443_stair_room_skirting (K443 hand villa, not Alsenan): 24 + 4 registry tests. Normal: hall 6.90 - 1.80 = 5.10,
  lobby 5.40 - 1.10 (lift, whole) = 4.30, held children blank, parents HELD / NA, closure 8.30 / 9.30, outside lines
  byte-identical, mirror invariance, files. Adverse: **lift opening skirted as a passage** (load and post-integration),
  door jamb, face owned by a flight (one base one owner), a landing at another level is not an overlap, held with a value,
  held carried as 0, held stretch with no line, closure residual, mm unit slip, opening without id, gap, face without
  handle, one face in two parts, stale parent, floor line of another room, owner material without its Q-nn, applied twice.
- Lessons-register row proposed (ERS s.7): | 2026-11-03 | the integration row listed three ceiling lines as skirting
  parents | the T-441 LINES table (every line on the stair rooms) was read as the parent list | check each named parent's
  item code and unit in the candidate before splitting; a non-matching line stays byte-identical and is named | tests/
  t443_stair_room_skirting | T-443 |

## 5. Engine vs freelancer (quantities only; T-106 / T-441 traces)

| Space | Freelancer | Candidate V3.0.46 | Difference | Verdict proposal |
|---|---|---|---|---|
| 2F corridor (= 2F lobby + arrival) | 13.60 lm (gross perimeter) | 7.500 lm | -6.100 lm (-44.85 %) | RULE_DIFFERENCE 2.900 (OP-001 / OP-007 / OP-002 not deducted by him; UP-CER-003, lift B6-06) + RULE_DIFFERENCE 2.500 (no skirting on the slab-opening / flight-top edge, R-T410-1, B12) + UNRESOLVED 0.700 (his outline 13.60 vs drawn 12.90) |
| GF stair hall + back lobby | no row | 6.050 lm | +6.050 lm | ENGINE_RIGHT on the existence of the faces (drawn walls at floor level); material HELD |

The percentage is not an accuracy figure; two of three components are owner-rule differences.

## 6. Held / missing

- Designer items (RFIs a-c of T-441, drafts, nothing sent): divider band role / south end / finish; OP-020 reveal owner;
  space under the winders (lobby west face; strip GF-ST-CN, the parent's 0.200 remainder).
- Materials: GF hall, GF back lobby and 2F arrival skirting materials follow HELD floor / landing finishes.
- R-T481-3 (1F shaft, 9.050 lm from L-ba3599ec to B7; merged a8609a7a but not re-measured at its Gate A): a different
  room line, needs that line's engine edges by handle; WAITING `T443_1F_SHAFT`, not consumed here.
- Flight faces: B7-07 / B7-08 own them (form ORR-007), unchanged.
