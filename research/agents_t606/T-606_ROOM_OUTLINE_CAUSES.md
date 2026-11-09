# T-606: room skirting UNRESOLVED 9.693234 lm split by room outline (R-T606-1)

Worker 2, 2026-11-07, lane A, non-candidate, backlog-permitted (research only: no engine, rule / knowledge version,
registry, frozen or candidate file changed; nothing released; released default V2.9 + route G unchanged). Files:
research/agents_t606/* and tests/t606_room_outline_causes/* only (plus the regenerated docs/CODEMAP.md). Training villa;
not an accuracy claim. ERS read: s.2.1 (element first), 2.3 (own drawing read), 2.4, 2.7 (no owner question: nothing
here is a genuine contradiction or a missing safety-critical design; every open item is his undimensioned row), s.3
(no number chosen by figure), s.4, s.7.

## 1. Physical element and method

Room skirting = the foot of a dry, untiled wall / column face where a finished floor meets it (UP-SKIRT-001 1.4.0),
net of doors, plus doorless jambs (R-T601-1). His room rows are GROSS perimeters (R-T574-1), so the 9.693234 lm is a
gross-vs-gross gap and is split here by OUTLINE. R-T606-1 (t606_rules.py): an outline is an ordered chain of drawn
edges by handle (LINE = its infinite line, ARC = its circle, vertex = intersection of neighbours), each edge a WALL or a
VIRTUAL edge (void, landing, zone, chord: no wall base), columns cut notches; a cause is the perimeter difference of two
re-measured readings (never typed); his row is ESTABLISHED only when one reading reproduces BOTH his perimeter (column
C) and his area (column D) strictly inside his 2-decimal rounding; one figure alone = CANDIDATE, never chosen.

Drawing: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf), decoded into the private folder only;
`t606_extract.py` writes handles, roles, lengths and areas only (T606_DRAWN.json, no coordinates).

## 2. Independent re-measures (8 outlines; T-574 had 1 of 11)

| Outline (handles) | drawn lm | engine gross (T-460) | area m2 |
|---|---|---|---|
| 2F maid 300 x 645 (1284 1292 1279 128B) | 18.90 | 18.90 | 19.35 |
| 1F 380 x 430 (AD8 AFF AD0 B08) | 16.20 | 16.20 | 16.34 |
| 1F 500 x 365 (AE7 AF8 AE9 C1E + column 2FFC notch 0.10) | 17.40 | 17.40 | 18.215 |
| GF driver 175 x 450 (113 131 11E 12F) | 12.50 | 12.50 | 7.875 |
| GF dewaneya (119 127 arc 10E R1.10 139 124) | 20.127876 | 20.127876 | 24.94032 |
| 1F living (AEC B68 AF9 B10 AFE B16 ADE C21 AEB AF7 + notches 3008 / 300E / 3005 0.30) | 52.44 | 52.44 | 75.983 (= T-113 engine face) |
| 1F curved room + lobby (B1D C0F C0A arc BD2 B6B ACE B0D C09 C15 C0B B0B) | 22.15067 | 22.15067 | 19.016592 |
| 2F corridor (1283 1294 128A 129A, landing edge 138B, 12B7) | 12.90 | 5.25 + 5.15 + 2.50 | 7.375 |

All eight agree to 0.000000 lm: the engine gross outlines are right as drawn.

## 3. The 9.693234 lm, by room (out/T606_OUTLINE_CAUSES.json; every room closes exactly)

The T-574 figure is a NET of offsetting terms: 1F living +8.66, GF open room -16.913904, 1F curved -0.73933, 2F
corridor -0.70.

| Room (his row P / A) | ours - his | causes (lm, verdict proposal) |
|---|---|---|
| 1F living (21: 43.78 / 38.96) | +8.66 | **+8.40 dog-leg well walls above the landing** (B16 4.15 + ADE 2.50 + C21 4.50 + column 3005 returns 0.10 in our gross; he closes on the landing edge ABE 1.15 + A8F 0.35 + AC0 1.35 = 2.85): ENGINE_RIGHT (our net already removes them: T-508 shaft 9.05 + W13 / W25); **+0.20 stair-opening zone** (our gross walks the walls AF7 / AEC with column notches 300E / 3008, his the opening edges B74 5.87 + B75 1.60 + D24 1.15 + AF5 2.40): see F-T606-1; **+0.06 UNRESOLVED** (his row vs the floor-only outline 43.84 / 38.988 m2: -0.06 lm, -0.028 m2, 0.14 %) |
| 1F curved room + lobby (22: 22.89 / 17.29) | -0.73933 | UNRESOLVED: no drawn reading (ours 22.15067 / 19.0166, chord 21.90 / 20.70, room alone 16.65067 / 15.0603, room alone chord 16.40 / 16.7438, each with or without the lobby / bath door reveals) reproduces either figure; his row is larger in lm and smaller in m2 than every reading (T-218 agrees) |
| 2F corridor (29: 13.60 / 7.70) | -0.70 | UNRESOLVED, two CANDIDATES on the perimeter only: maid door reveals 2 x 0.20 + roof door reveals 2 x 0.15 = 0.70 (area 7.705, on his rounding boundary: refused), lift + roof reveals 0.70 (area 7.725: refused); east-flight foot 0.30 beyond the printed landing gives 13.50 / 7.72 (neither) |
| GF open room (13 + 15: 72.92 / 147.96) | -16.913904 | UNRESOLVED, NOT re-measured this run: his two rows' AREA re-adds to the room's gross outline incl. pantry, garden band and stair zone (T-427, 0.30 m2); his perimeter is two sub-outlines whose shared edge he counts twice; the split needs the open-room face by handle (follow-up row proposed) |
| **Total** | **-9.693234** | **named +8.60 (ENGINE_RIGHT 8.40, F-T606-1 0.20); UNRESOLVED -18.293234 = -16.913904 - 0.73933 - 0.70 + 0.06** |

So the 'largest unnamed finishes residual' is not 9.69 lm: 8.60 lm of it were a positive offset (the 1F stair well and
opening, now named) and the true unnamed remainder is the GF open room -16.914 plus 1.38 lm on three rooms.

## 4. F-T606-1 (new finding, released net, ENGINE_WRONG proposal)

Line L-ba3599ec (1F living, FIN.SKIRTING released net 32.38536 lm in V3.0.58) walks 11.22 lm of wall face along the
printed stair opening 5.87 x 4.00 and the arriving stair box 1.15 x 2.40: AF7 4.00 (of 5.15) + AEC 7.02 (of 10.67) +
column notches 0.20. At +5.50 there is no room floor against them (void B7A, round-stair treads, stair box: T-113 O1 /
O2 / O3 / L1), and none of the line's deductions (doors 4.70, passage 1.00, glazing 3.10464, stair W13 / W25 2.20,
dog-leg shaft 9.05) lies on them. If the Checker confirms: candidate FIN.SKIRTING 209.428592 -> **198.208592 lm
(-11.22, -5.36 %)**; the stair-box part (AEC 1.15 + its notch share) belongs, if anywhere, to the ST-01 landing scope of
the stair class, never the room line. This is defect B12 (skirting along void edges) in its wall form. Corrected
quantity proposal: a deduction 'STAIR-OPENING-NO-FLOOR 11.22' on L-ba3599ec (lane I fix row), T-508's shaft rule
extended to every stair opening, not only the dog-leg well.

## 5. Rule, tests, lesson, missing

- R-T606-1 (t606_rules.py docstring, every villa; provenance T-606): handle-chain outlines, gross only, causes as
  reading differences re-adding exactly, his reading established only on BOTH figures strictly inside his rounding, one
  residual UNRESOLVED computed never typed; refusals: gross vs net, tiled face skirted, a cause or edge counted twice,
  typed residual, unknown verdict / role, parallel neighbours, missing handle.
- Tests tests/t606_room_outline_causes: villa K606 (not Alsenan; 4 rooms, doorless arch, wet room B, column notch, R1.00
  corner, stair opening) written by ezdxf and read back at 0 / 37 / 90 / 211 deg, mirrored, mm and m; adverse: gross vs
  net, tiled face, counted twice (id and edge), typed residual, boundary 7.705 refused, perimeter-only match refused,
  ambiguous readings; Alsenan rebuild byte-identical, split re-adds to -9.693234, no coordinates in the JSON.
- Lesson proposal (ERS s.7): "2026-11-07 | a room skirting residual of 9.69 lm was read as one unnamed amount | it was the
  net of +8.66 (1F stair well and opening) and -18.35 | split a gross-vs-gross gap by room and by reading before naming
  its size; a room line whose face includes a stair opening must deduct every wall face without floor at that level, not
  only the stair well | tests/t606_room_outline_causes | PROPOSED".
- Missing: the GF open room by handle (its face has pantry, band, stair-zone and wash-lobby mouth edges; his split line
  between his two rows is not drawn); the curved room has no reading; his rows carry no dimensions.

## 6. For the Checker

1. `python3 -I research/agents_t606/t606_alsenan.py --check` (byte-identical; pins in the JSON); with the private DXF:
   `.work/venv/bin/python -I research/agents_t606/t606_extract.py --dxf <P7757.dxf>` (re-read identical).
2. Largest cause (1F living, 8.40): B16 x = 4607 from 8356 to 12506 = 4.15, ADE y = 12506 2.50, C21 / AF1 / AF0 x = 2107
   from 8006 to 12506 = 4.50, column 3005 0.05 x 2 = 0.10; less ABE 1.15 + A8F 0.35 + AC0 1.35 = 2.85 -> 8.40.
3. F-T606-1: AF7 from y 906 to 4906 (printed 400) = 4.00; AEC from x 5907 to 12927 (587 + 115) = 7.02; 300E / 3008
   protrude 0.05 into the room.
