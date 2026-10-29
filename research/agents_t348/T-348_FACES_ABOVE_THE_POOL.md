# T-348: the faces above the pool and round the 1F void AT225 (freelancer rows 70 / 71 / 74, 109.890 m2)

Worker 2 (lane A), claim 2026-10-29 20:47 UTC. Investigation only: research files and tests; no engine module, rule,
knowledge file, candidate line, released line or T-337 row changed; nothing released. ERS applied: s.2.1 (each element
defined first), s.2.2 (drawing first; his figures traced, never taken), s.2.4 (reconciled in m2 to named causes,
residual 0), s.2.7 (no owner question: the drawings settle the geometry; two values stay HELD with their bound), s.4
(rules + tests), s.7 (lesson). No coordinate, client name, image or workbook text is committed.

## 1. Question and evidence

F-T346-1: after T-346 put 1F NW-5 into his row 69, his rows 70 (1 x 5.70 x 4.95), 71 (1 x 5.50 x 4.95) and 74
(2 x 5.50 x 4.95), "faces above the swimming pool", matched only NW-1 .. NW-4 and two returns (32.167 m2). What are they?

Read this run (Drive "Alsenan chalet project"): P7757.dxf (from P7757_DXF_COMPRESSED.zip) 1F plan, 2F plan (= 1F roof)
and NW elevation frame; p7757_arch_sheet04.pdf (1F plan); Alsenan_Architectural_P7757_Pages_07-08 p.2 (sheet 08, NW
elevation); T-110 beam register (B7); T-127 / T-342 (AT225); T-292 / T-302 (1F-11, W17).

What is physically built over the pool (sea end of the 1F, the "pool block", 4.8077 m of sea frontage):

- The 1F master bedroom 1F-11 has a **curved glazed wall NW-2** (r 1.935, arc 3.5283 on a 3.0594 chord, W17 across
  almost all of it) that bulges INTO the room. In front of it, between the arc and the sea line, is a **recess** (sagitta
  0.750 m) roofed by the 1F roof +9.70 (2F plan: the roof hatch runs to the parapet).
- The GF roof +5.50 in front has the **void AT225** (inside the B7 ring): its landward edge is 0.20 m in front of the
  curved wall, its sea side reaches 1.30 m past the sea line; open to the pool court below and the sky above.
- Across the sea line stands a **screen**: two piers (NW-1 1.1703, NW-3 0.578; fronts 0.298 m seaward, 1F plan CAB / CA7,
  2F plan 1315 / 1319) and, over the 3.0594 m between them, an **arched opening** (legs from +5.50 at the pier ends,
  head crown +8.4996 / +8.5501) with a spandrel to +9.70 and the parapet to **+11.00** (printed chain 3050.5 + 454.3 +
  1995.3 from +5.50). In plan the screen front is the overhead line CB3 (3059.4) / 2F plan 1319; screen depth 0.2983
  (CAA / CB2, printed 298.3 in the elevation chain). The bold outer arch of sheet 08 is the frame moulding (his row 75
  "frame" 0.45 x 8.75, T-162 frame, not this task).
- Sheet 08's pool-axis chain: pool 115 / 70 / **4300 to the court soffit +5.30** / **200** to +5.50 / 3050.5 / 454.3 /
  1995.3 to +11.00 / 3200 / 200 to +14.40. His 5.70 = 5.50 + 0.20; his 5.50 = +5.50 -> +11.00.

## 2. Each face: element, plan edge, levels, m2, status, owner line (FACES_T348.csv)

| Face (key) | Plan edge / evidence | Bottom -> top | m2 | Status | Binding |
|---|---|---|---|---|---|
| pier fronts NW-1 / NW-3, storey + parapet | T-305 lengths = projected pier widths | +5.50 -> +9.70 -> +10.999 | 4.9152 + 1.5206 + 2.4276 + 0.7511 = 9.6145 | DC | T-337 keys (unchanged) |
| recessed curved wall NW-2, storey | BCD / BCE / BD0 r 1.935, arc 3.5283 | +5.50 -> +9.70 | 14.8188 gross (W17 hole stays T-302 / T-337's) | DC | T-337 1F storey L-8bb83e16cc7b104ab88b (unchanged) |
| **screen front, parapet band** | 2F plan 1319, chord 3.0594 | +9.70 -> +11.00 | **3.977220** | DC | **re-measure of T-337 NW-2 PARAPET (HELD 4.223 .. 4.585 on the arc)**: above +9.70 the arc carries no face, the parapet runs straight at the screen front |
| **screen front, storey band (NEW)** | CB3 3059.4 | +5.50 -> +9.70 | gross 12.849480 - hole 8.134744 .. 8.525649 = **4.323831 .. 4.714736** | HELD | T-314 FILL NEW |
| **screen back, storey band (NEW)** | sea line, faces the recess (outside air, Q-67 A) | +5.50 -> +9.70 (owner Q-07 B band; drawing-derived: to the roof soffit, slab depth not printed) | **4.323831 .. 4.714736** | HELD | T-314 FILL NEW |
| screen opening intrados (NEW, a reveal) | 0.2983 x legs + head 7.735736 .. 7.893877 | - | 2.307570 .. 2.354743 | HELD | reveals FILL (T-326 / T-327) |
| recess soffit (NEW candidate) | segment r 1.935 / chord 3.0594 = 1.600884 | under +9.70 | 0 .. 1.600884 (PL-05 2.417 may hold it: faces not listed) | HELD | soffit family (Q-68 C), not facade |
| void ring inner face, landward arc | BCF r 1.735, 2.6750 m | 0.20 (sheet 08 '200') .. 0.75 (B7 20x75) below +5.50 | 0.535000 .. 2.006250 | HELD | **re-measure of T-337 NW-2 SLAB_EDGE_BELOW** (blank, 3.5283 m): the face is the ring's, 0.20 in front of the wall |
| void ring inner face, sea side + tips (NEW) | C7A 2.9218 + 2F1B 0.6185 + 2F1C 0.9233 = 4.4636 m | as above | 0.892720 .. 3.347700 | HELD | T-314 FILL NEW |
| NW-1 / NW-3 "slab edge below" | piers stand on the GF roof band, which runs on 1.50 m seaward | - | - | NOT_A_FACE | remove from T-337 SLAB-EDGE 1F |
| GF pool-court front slab edge (in his row-70 band) | +5.30 -> +5.50 printed; 4.8077 of the 5.40 m court front | 0.20 | 0.961540 | HELD (trade: court sea wall on the plot line, Q-65 C) | T-314 FILL NEW |

Why the two HELD values: (1) the screen opening is drawn as two lines 0.05 m apart; the inner one meets the pier ends
(plan CB2 / CAA), the outer one carries the printed crown 3050.5: which one is the hole edge is not printed; (2) the
void ring's depth is 0.20 on the architectural elevation and 0.75 in the B7 schedule (Q-61 (3): rings held unless
identified). Neither is a finish question for the owner; both are bounded, never 0.

Interior cross-check (acceptance b): the only interior face behind these is the room side of the curved wall (r 2.135,
BD2) in 1F-11 plaster / paint L-31db3c83552682d92ca3 / L-349db74a70e1eecda2d2 (present on V3.0.24, T-338 file); no
face here is that face: **overlap 0.000 m2**. The screen back faces the recess, which is open to air on its sea side
(no door, no glazing: exterior under Q-67 A).

## 3. Reconciliation statement (acceptance d; RECON_T348.csv)

**109.890 = row 70 28.215 + row 71 27.225 + row 74 54.450, residual 0.000000.**

- Row 70 (4.95 x 5.70, one plane +5.30 -> +11.00 of the sea elevation): drawn 27.402740 = pier fronts 9.614500 + screen
  parapet band 3.977220 + screen storey band gross 12.849480 + court front slab edge 0.961540; terms +0.811110 (his
  width 4.95 vs 4.8077 x 5.70) + 0.001150 (CAD parapet tops +10.999). **MAPPED.**
- Row 71 (4.95 x 5.50, "continued"): the recess faces behind the screen, drawn 27.668280 = screen back gross 12.849480
  + curved wall NW-2 14.818800; terms +6.435000 (his band above +9.70: the recess is roofed there) - 6.878280 (two faces
  stacked in depth, chord 3.0594 + arc 3.5283, vs his one width 4.95). **MAPPED (RULE_DIFFERENCE: one plane).**
- Row 74 (2 x 4.95 x 5.50 = 54.450): **NO DRAWN EXTERIOR FACE.** Besides its front and its recess the pool block has two
  sides: NE is the 1F NE face NE-2 (19.27 m straight), already in his row 64 (one plane 10.00 x 19.20); SW is the
  partition with the bath / 1F-11 (1F plan), an interior wall. His row reads the block as a free-standing box.
  Verdict proposal ENGINE_RIGHT (no face); his intent (box of four faces) is a reading, the physical result is firm.

Effect in units: his rows 70 / 71 / 74 (109.890) against the drawn faces they describe 55.071 m2 gross (27.403 +
27.668), of which NEW faces 25.699 gross (screen front + back storey bands) / 8.648 .. 9.429 net and 0.962 HELD (court
front), and T-337 re-measures -0.246 .. -0.608 m2 (NW-2 parapet 3.977 vs 4.223 .. 4.585). Like for like, his NW walls
lose 54.450 m2 that no face carries: T-346's like-for-like 926.365 -> **871.915** against the drawing 897.720 .. 938.606
(+ the new screen faces 8.648 .. 9.429 net) = his -34.453 .. -76.120 m2 (-3.8 .. -8.0 %) (rule difference on openings
unchanged, Q-73 A full holes vs his half).

Faces T-346 had placed in these rows that are NOT in them: 1F NW-4 (the W18 strip between the pool block and the
saloon block, elevation 0.50 m left of the block: 1.9627 + 0.5135) and the 0.08 m returns NE-1 / SW-1 (0.672 +
held parapets 0.176 .. 0.208): they are in no freelancer row (T-162 list of drawn faces in no row grows by 3.148 m2 +
held).

## 4. What T-314 and the other consumers get (FILL_T314_T348.csv)

NEW: screen front storey and screen back storey (HELD 4.323831 .. 4.714736 each), void ring sea side (HELD
0.892720 .. 3.347700), court front slab edge (HELD 0.961540, trade). RE-MEASURE: NW-2 parapet band DC 3.977220
(PARAPET-OUTER 1F line 53.550644 .. 59.290836 -> 53.304756 .. 58.682756); NW-2 slab edge = ring landward arc 2.675 m
HELD 0.535 .. 2.006. REMOVE: NW-1 / NW-3 slab edges (NOT_A_FACE). Reveals FILL: the screen intrados 2.307570 ..
2.354743 HELD. Soffit family: recess soffit 0 .. 1.600884 HELD (check against PL-05 first). Element register (Lead):
"1F pool-block screen (piers + arched opening + spandrel + parapet), sea line, 3.0594 m opening, +5.50 -> +11.00,
exterior both faces; owner trade exterior plaster / Sigma".

## 5. Rules (research, `t348_void_faces.py`; for a future rule version)

R-T348-1 a face is classified by what it faces (outside air / room / roof), not by its storey; a face above the roof it
stands on is a parapet face. R-T348-2 faces stacked in depth (screen front, screen back, intrados, recessed wall,
recess soffit) are separate faces, each once in its own plane; a projected width is never a face length; the screen
hole is deducted from both screen faces. R-T348-3 a face already carried by a ledger key is bound, never re-emitted; a
ledger row with no physical face (a slab edge where the lower roof runs on) is NOT_A_FACE. R-T348-4 HELD with its bound,
blank, never 0; a freelancer row is never a quantity.

## 6. Tests

`tests/t348_void_faces/test_t348_rules.py` (villa C, hand calculation in its docstring: a light-well screen 2.40 m with a
1.60 x 2.00 opening, roofed recess behind an r 2.00 arc; his three planes 27.000 = 8.640 + 0.360 + 14.922012 + 1.500 -
7.422012 + 9.000, residual 0; mirror / rotation / millimetres). Adverse: a void face counted inside and outside, a
freelancer row as a quantity, a face above a roof counted as facade, a face emitted twice / NEW while in the ledger /
one key bound twice, HELD with a point value or 0, a hole larger than its face, parts not adding up or None.
`test_t348_alsenan.py`: byte rebuild, statement residual 0, bound keys carry the T-337 values, NEW keys absent from
T-337, FILL HELD blank, screen values, interior overlap 0.

## 7. Lessons-register row (ERS s.7, proposed)

2026-10-29 | three freelancer rows (109.890 m2) "faces above the pool" looked like faces round the 1F void the ledger
lacked; the drawn element is a screen with an arched opening standing in front of a recessed curved glazed wall, and
the ledger had put the screen's parapet on the arc and a slab edge under piers that stand on a roof | the facade ledger
was built from the 1F plan outline (one face per outline side) and the elevation's one plane was matched to it; the
depth structure of the elevation (screen / recess / wall) was never read from the plans of both levels | before a
facade face is bound, read what stands in front of and behind each outline side on the plans of the floor and the roof
above; a screen and the wall it shades are separate faces (front, back, intrados, wall, soffit), and an elevation
plane is reconciled to them in depth (every villa) | tests/t348_void_faces | proposed.

Files: `t348_void_faces.py`, `t348_alsenan.py` (--write / --check), `FACES_T348.csv`, `FILL_T314_T348.csv`,
`RECON_T348.csv`, `summary.json`; tests `tests/t348_void_faces/`.
