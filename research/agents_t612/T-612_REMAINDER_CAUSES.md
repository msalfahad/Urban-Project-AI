# T-612: room skirting UNRESOLVED remainder by outline (R-T612-1 on R-T606-1)

Worker 2, 2026-11-07, lane A, non-candidate, backlog-permitted (research only: no engine, rule / knowledge version,
registry, frozen or candidate file changed; nothing released; released default V2.9 + route G unchanged). Files:
research/agents_t612/* and tests/t612_open_room_outline/* only (plus the regenerated docs/CODEMAP.md). Training villa;
not an accuracy claim. ERS read: s.2.1 (element first), 2.3 (own drawing read), 2.4, 2.7 (no owner question: his rows
carry no dimensions; nothing is a contradiction in the drawings or a missing safety-critical design), s.3 (no number
chosen by figure), s.4, s.7.

## 1. Physical element and method

Room skirting = the foot of a dry, untiled wall / column face where a finished floor meets it (UP-SKIRT-001 1.4.0), net
of doors (Q-06 A), lift landing doors excluded, stair-opening walls without floor excluded (F-T606-1). His room rows are
GROSS perimeters with an area beside each (R-T574-1); the T-606 remainder is a gross-vs-gross gap. R-T612-1
(`t612_rules.py` docstring) extends R-T606-1 for an open room that several of his rows cover: (1) engine face and drawn
gross outline both re-measured by handle, their difference a named cause by edge; (2) a column crossing the outline is a
notch, a column / wall wholly inside is an INTERIOR SOLID reported as its own piece, never a hole folded into the
perimeter; (3) a split between his rows over one outline is counted in both; an UNDRAWN split is solved only as a
BOUND and stays UNRESOLVED; (4) a net residual is reported as its parts (one cause refused), an arc never as its chord;
(5) an arc edge that uses only part of its drawn entity sweeps inside the entity's drawn range (R-T606-1's mid-angle
rule fails there: the GF curved glazing is such an arc; regression test pins the old failure).

Drawing: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf), decoded into the private folder only;
`t612_extract.py` writes handles, roles, lengths and areas only (T612_DRAWN.json, no coordinates; a test asserts it).

## 2. GF open room re-measured by handle

| Reading | chain (handles) | lm | m2 |
|---|---|---|---|
| engine face GF-RC99C2A (line L-71e2e002) | B5 E0 97 27D(arc, bulge seg 1) 2E4 222 20F AB 158 AE A8 30F 104; notches 2F8A 2FB4 2FC0 2FC3 2FC6 2FD2 | **56.006096 = engine gross 56.006096 (0.000000)** | 126.927717 (V2.9 126.927696) |
| drawn gross outline (his area's outline) | B5 E0 97 27D 2E4 222 20F AB 158 AE 104; notches 2F8A 2FB4 2FC0 2FC3 2FCF 2FD5 | **55.906096** | **147.657717** (= T-427 147.658, second route) |

Face vs outline, by edge (re-adds exactly): face south side on the band / curb line A8 +13.82 and band end 30F +1.50
(both VIRTUAL: no skirting, already deducted in T-574), columns 2FD2 / 2FC6 notched +0.30; outline south facade 104
-13.82, west wall AE -1.50, facade columns 2FCF / 2FD5 -0.20: **+0.10 lm, ENGINE_RIGHT** (no skirting quantity moves;
the 3.90 lm facade of the dining piece x 3.00 .. 6.80 inside it is already the T-431 cause in T-574). Column 2FC3 sits
0.04995 proud of the facade as drawn: notch 0.099896 in both readings and in the engine.

## 3. The GF -16.913904 lm

= **+0.10 named** (section 2) **+ -17.013904 UNRESOLVED** (his 72.92 vs the drawn outline 55.906096, -23.33 %).

- Reading test (R-T606-1 step 4, both figures strictly inside his rounding): bases face / outline x up to 4 of 8 drawn
  pieces (reveals D200 2.00 x 0.20, D120 stair hall 1.00 x 0.20, D115 wash lobby 1.00 x 0.15, D120 west 1.00 x 0.20,
  lift landing 1.00 x 0.20, wash-lobby mouth 1.255652 x 0.15, the solids island 2FD2 + wall 336/337 + 2FC6 8.70 lm /
  0.88 m2 walked gross or net): **NOT_ESTABLISHED, 0 readings reproduce even his perimeter** (every piece walked:
  66.806096 < 72.92).
- His AREA is the drawn gross outline + 0.302283 m2 (0.20 %): he walked round nothing he took out of the floor (the
  island net would give 146.777717; the stair is inside his area, T-427), and no combination of reveal areas makes
  0.302283 (0.15 / 0.188348 / 0.20 / 0.40 pieces).
- So the only reading left that re-adds his perimeters is a **split between his two rows, counted in both**. Pure
  partition: split 8.506952 lm, his entrance row then has 6.253048 lm on the outline and 8.506952 shared (re-adds his
  58.16 exactly); with every drawn piece also walked the split is 3.056952 lm (bound 3.057 .. 8.507). The split line is
  **UNDRAWN**: his entrance row 14.76 / 10.46 as a rectangle would be 5.466542 x 1.913458, and none of 1,955,100 axis
  rectangles on the drawn lines' 57 x 50 positions reproduces it (0, 1 or 2 reveals). Widened 3 m round the outline
  (the entrance porch outside D200 with its steps, sheet 03: no 'entrance hall' label inside the room, DINING /
  RECEPTION / SALOON only): 21 of 16,769,025 rectangles hit both figures, and **0** of them has its four sides drawn
  over at least half their length: every hit is a figure coincidence between lines of other elements (ERS s.3 in
  numbers: a big enough search always finds a match by figure). CANDIDATE only (R-T612-1.3): if established, a split
  carries no wall base, so that part of his figure is no skirting (ENGINE_RIGHT on it).

## 4. 1F curved -0.73933 and 2F corridor -0.70 (T-606 readings re-checked)

- 1F curved room: the arc question answered by sign. Arc BD2 (r 2.135, 94.2 deg used) = 3.509762 lm on its arc; read as
  its chord the room gives dP -0.25067 lm and dA +1.683408 m2; his row is dP **+0.73933**, dA **-1.726592** against ours:
  opposite signs on both, so arc-vs-chord explains none of it. UNRESOLVED (T-606: 4 bases x 2 reveals, none).
- 2F corridor: two perimeter-only candidates (maid + roof reveals 0.70, area 7.705 on his rounding boundary; lift + roof
  0.70, area 7.725): refused. UNRESOLVED.

## 5. Totals and verdict proposals

| Residual | lm | named | UNRESOLVED | verdict proposal |
|---|---|---|---|---|
| GF open room | -16.913904 | +0.10 face vs outline (ENGINE_RIGHT) | -17.013904 | UNRESOLVED; CANDIDATE undrawn split 3.057 .. 8.507 lm counted twice |
| 1F curved | -0.73933 | 0 | -0.73933 | UNRESOLVED (not arc vs chord: sign test) |
| 2F corridor | -0.70 | 0 | -0.70 | UNRESOLVED |
| **Total** | **-18.353234** | **+0.10** | **-18.453234** | |

No ENGINE_WRONG found: the engine gross outline is right as drawn (third independent route after T-606's eight).
Fix row proposal FR-T612-1 (lane I, statement V-next, no quantity): restate the GF -16.913904 as +0.10 ENGINE_RIGHT +
-17.013904 UNRESOLVED with the split bound; his GF rows are a partition of one outline, so a per-room comparison must
compare his row SUM against one outline only with the split named.

## 6. Rule, tests, lesson, missing

- R-T612-1 (`t612_rules.py`, every villa, provenance T-612): see section 1.
- Tests `tests/t612_open_room_outline` (24 PASS): villa K612 (not Alsenan; 12.00 x 8.00 open room, curved glazing r 5.00
  used 90 of 196 deg, boundary column, interior column, zone line, two passages) written by ezdxf, read back at 0 / 37 /
  90 / 211 deg, mirrored, mm and m: hand P 42.053982 / A 106.574954; adverse: the R-T606-1 mid-angle sweep cannot close
  the partial-arc outline (pinned), interior column folded as a hole (+1.60 lm, refused), arc measured as chord refused,
  net residual as one cause refused, undrawn split never ESTABLISHED, gross vs net, missing handle, typed residual,
  impossible rectangle, sweep outside the drawn range; Alsenan rebuild byte-identical, re-adds -18.353234, no coordinate.
  T-606 tests still 12 PASS.
- Lesson proposal (ERS s.7): "2026-11-07 | his GF open-room rows (58.16 + 14.76 lm) were compared as one figure with one
  engine line and left -16.91 lm unnamed | two of his rows partition one outline, so their sum counts the undrawn split
  between them twice; the engine face also differs from the drawn outline by edge | compare a row SUM with the drawn
  gross outline, name face-vs-outline by edge, and carry the split as a bound (never a reading) | tests/t612_open_room_outline
  | PROPOSED".
- Missing: his split line between reception + dining and entrance (no dimension, not drawn); his 0.302283 m2 above the
  outline; the curved room and the 2F corridor rows carry no dimensions.

## 7. For the Checker

1. `python3 -I research/agents_t612/t612_alsenan.py --check` (byte-identical); with the private DXF:
   `.work/venv/bin/python -I research/agents_t612/t612_extract.py --dxf <P7757.dxf>` (re-read identical).
2. Re-measure from P7757 (room-local metres, origin = inner SW corner at the pantry, i.e. west wall AE x / facade 104 y):
   outline = east wall B5 x 18.97, E0 y 7.50 to 97 x 16.97, glazing 27D r 2.448 from y 8.192 to 2E4 y 8.95 (1.585596),
   2E4 to 222 x 7.70, down to 20F y 7.90, to AB x 3.00, down to 158 y 4.50, to AE x 0, down to 104 y 0, back to B5;
   notches 0.10 each at 2F8A, 2FB4, 2FC0, 2FCF, 2FD5, 0.099896 at 2FC3, 0 at 2FAE: 55.906096 lm / 147.657717 m2.
3. Face: same but A8 y 1.50 from x 0 to 30F x 13.82, 30F down to 104: 56.006096 lm (= engine).
