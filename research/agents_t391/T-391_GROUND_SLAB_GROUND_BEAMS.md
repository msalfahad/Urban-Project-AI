# T-391 Ground slab and ground beams: the two largest UNRESOLVED concrete components of T-385, re-measured and split

Worker 3 (lane S row taken under the lane I throughput rule), 2026-10-31 11:06 .. UTC, run session_01E6cPnetFqFn8Rd9wsqj7Mq,
branch `agents/task-T-391`. Research only: no engine, candidate, released line, rule or method version changed, nothing
released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Sources and runs

Own Drive copies (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf' (`9f9d1179`),
P7757_DXF_COMPRESSED.zip -> P7757.dxf (`ab54dd55`), the concrete + rebar workbook (quantities only). Candidate lines: the
25 STR.CONC.GROUND_SLAB and 58 GROUND_BEAM lines (boundary beam excluded, it is GB-BOUNDARY) as committed by T-347
(`research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json`), contractual view with `verdicts/V3.0.29/DOWNGRADES.json`: the
T-385 component totals are reproduced exactly (GS-SLAB 17.240684 m3 valued + 1 held line 3.929788; GB-MAIN 27.625386 m3
on 38 valued lines, 20 held), so the ids and figures are those of V3.0.29 = V3.0.30 for these families. Engine cell
outlines: the route-G overlay and SLAB_FACES.csv of an own `research/agents_t167/v304_run.py` run on the same copies
(same 25 cell ids and net areas as the committed lines). A full V3.0.30 chain run was started but had not finished when
this package was written: V3.0.30 itself was not reproduced in this run.

```
python3 -I research/agents_t391/t391_extract.py "<private>/ST7757 dxf.dxf" --svg <run>/v29/structural/overlays_m4/Slab_thickness_basis_SH08.svg \
    --faces <run>/v29/structural/SLAB_FACES.csv --out research/agents_t391/OWN_GROUND_T391.json
python3 -I research/agents_t391/t391_alsenan.py --freelancer "<private>/<concrete workbook>.xlsx" --out <checkout>/.work/private/t391/out --write
```

Files: `t391_rules.py` (R-T391-1 .. 5, pure), `t391_extract.py`, `t391_alsenan.py`, `OWN_GROUND_T391.json` (180 own
faces: kind, area, DXF edge handles, no coordinates; the engine-cell binding; the drawn length envelope),
`summary_t391.json` (engine side + cause terms in m3; the freelancer's row values stay in `.work/private/t391/out`).
Tests `tests/t391_ground_recon` (18).

## 1. Physical elements (ERS s.2.1)

- **Ground slab**: slab on grade, 'T=10cm' printed on the GROUND BEAMS PLAN (T-206 DRAWING-CONFIRMED), cast between the
  ground-beam faces. Convention C1 (T-234 / T-241 / T-242): the ground beam is billed full depth from the slab top and
  owns its strip; the slab is the panel between faces, never over a strip (R-T391-1 / -2).
- **Ground beam**: b x D x L face to face (Q-61 C member by member). D by position (T-242 / T-253 / T-289, Checker
  verified): interior p.13 length classes 0.30 / 0.40 / 0.60, exterior main house D printed by two levels (top +0.95 to
  N.G. +-0.00 = 0.95), annex exterior CONFLICT (D-35), court no section, D-34 title precedence open.

## 2. Own hand table (OWN_GROUND_T391.json; acceptance a)

Own polygonisation of the GROUND BEAMS PLAN frame: layer-1 band edges (85 lines, 4 arcs 139 / 13A / 157 / 158),
S-COL.BON edges and outlines, S-BW rings 7BE / 7C2 (lift shaft) and 7C5 / 7C6: **180 faces, 289.1136 m2** inside the
network = **27 slab panels 217.2315 m2** (OWN-090, a 0.1556 m2 triangle bounded by three beams, counted a panel as T-242
GS-29 and the engine do) + beam strips 57.9719 + column pieces 5.8652 + lift shaft and ring 8.0450 m2 (strips together
71.8821 m2). Each engine cell is bound to the own faces it covers by more than half; no own face in two cells.

| Engine cell (line) | Engine net m2 | Own faces (m2) | Engine - own m2 | Cause |
|---|---|---|---|---|
| 19 cells, e.g. cd1f57cc (L-a36f703f) 24.505, e4c2bd9d 22.9654, 77b8830f / b8f67954 14.8931, ... | 150.9935 | one own panel each, equal | 0.0000 | AGREE (19 faces to 0.0001 m2) |
| 49a7dae5 (L-69527cb9) | 3.5977 | OWN-018 3.8344 | -0.2367 | engine deducts a 'member overlap' of 0.2367 m2 inside a panel the own read bounds by layer-1 faces only; T-242 GS-17 also 3.598: the member is not on layer 1 (not located here) |
| 3f7728a8 (L-8b681fda), c1b4b440 (L-f192ff5f) | 2.6156, 2.2447 | OWN-022 2.7212, OWN-025 2.2534 | -0.1056, -0.0087 | the two panels against the lift ring 7C2 and the oblique beam 17E+17F (the lift C2 oblique gap, T-230): three reads give three areas (T-242 2.745 / 2.285): UNRESOLVED, 0.011 m3 |
| d74f3fe2 (L-1031c9be) + 0caa2bd2 (L-5e881fd3) | 10.9051 + 2.0502 | OWN-006 13.4514 (one panel bounded by arc 158 and straight bands) | -0.4961 | the engine splits the court-side panel in two at a line not drawn on layer 1 and stops it short of arc 158 (its own ring closure, T-254); UNRESOLVED, 0.050 m3 |
| c1089bdb (L-41cfb82e) HELD 'SLAB_CELL_FREE_COLUMNS' | 39.2979 (gross 41.0762 - overlap 1.7783) | slab panels OWN-007 11.9237 + OWN-009 11.52 (stair hall) + OWN-010 10.9742 + OWN-047 1.1875 = **35.6054**; not slab: lift shaft OWN-020 3.24, beam strips 2.7383, column pieces 0.25 = 6.2283 | held | see F1 |
| 4df8fcd9 STAIR_ZONE, **no GS line** | 8.3723 | OWN-011 8.3723 | (not a line) | see F2 |

Ground beams: 58 lines bound once (summary groups): valued 38 = interior class D 0.30 (1 run, 0.10 m), D 0.40 (17 runs,
57.3969 m), D 0.60 (4 runs, 26.44 m), exterior main house D 0.95 (16 runs incl. the ring 157 / 158, 56.5168 m); held 20 =
D-34 downgraded 9 (16.5989 m), D-35 annex CONFLICT 8 (31.5364 m), court 3 (5.70 m). Engine face-to-face length
194.289 m against the own strip length 193.7583 m (beam strips at 0.30, curved strips included): -0.531 m (0.27 %), the
T-230 end adjustments the strip area does not carry. Own drawn envelope of a lump length: 193.7583 (face to face) ..
231.9083 m (run through every adjoining column / ring).

## 3. Cause split (acceptance b; signs engine - freelancer, m3; R-T391-3 / -4)

**GS-SLAB residual -12.309316 m3** = (the freelancer's one plate x 0.10 against the 24 valued engine faces):

| Cause | m3 | Verdict proposal |
|---|---|---|
| his plate covers the beam / column / lift strips the beams already own (71.8821 m2 x 0.10; his area exceeds the whole drawn network, so it covers them) | **-7.188210** | ENGINE_RIGHT (C1: the same concrete twice on his side) |
| own slab panels inside the engine's HELD cell (35.6054 m2 x 0.10) | **-3.560540** | HELD (named item, never agreement; F1) |
| the stair-zone panel the engine routes out of the slab family (8.3723 m2 x 0.10) | **-0.837230** | UNRESOLVED (F2) |
| his area beyond the whole drawn network (bare number, no drawn element) | **-0.638640** | UNEXPLAINED (his side) |
| engine vs own on the valued faces (-0.8470 m2: -0.2367 member overlap, -0.4961 court-side panel, -0.1143 lift-side panels) | **-0.084700** | UNRESOLVED (three small reads above) |
| remainder | 0.000004 | closes (<= 0.001) |

Traced (named) -7.188210; HELD -3.560540; unexplained -1.560570 (UNRESOLVED -0.921930 + his excess -0.638640).

**GB-MAIN residual -10.354614 m3** (his one section 0.30 x 0.60 over his two lump lengths against the 38 valued runs):

| Cause | m3 | Verdict proposal |
|---|---|---|
| held runs: his section over the 53.8353 m the engine holds (D-34 9, D-35 annex 8, court 3) | **-9.690354** | HELD (named, never 0, never agreement) |
| section, exterior main house: printed D 0.95 (two levels) vs his 0.60 on 56.5168 m | **+5.796522** | ENGINE_RIGHT (DEPTH; T-289 Checker-verified basis) |
| section, interior class 0.40 vs his 0.60 on 57.3969 m (17 runs) | **-3.443815** | ENGINE_RIGHT (p.13 'less than 5 m' class; T-242 FREELANCER_WRONG section) |
| section, interior class 0.30 vs 0.60 on 0.10 m | -0.009000 | ENGINE_RIGHT |
| section, interior 0.60 runs | 0.000000 | AGREE |
| plan / end adjustments of valued runs (net plan vs 0.30 x L) | +0.000013 | AGREE |
| length basis: his lump length over the engine's 194.289 m (his lies inside the drawn envelope 193.758 .. 231.908 m, so it runs partly through supports; which supports cannot be split from two lumps) | **-3.007980** | UNEXPLAINED (untraced remainder, bounded; not closed as a rule difference by its sign) |
| remainder | 0.000000 | closes |

Traced (named) +2.343720; HELD -9.690354; unexplained -3.007980.

Both components together (-22.663930 m3): traced -4.844490, HELD -13.250894, unexplained -4.568550 (was UNRESOLVED
-22.663930 as a whole in T-385 r2).

## 4. Findings and proposals (acceptance c; no line edited)

- **F1 (held bound basis, R-T391-5)**: the held cell's bound 3.929788 m3 is its net area 39.2979 m2 x 0.10, but 6.2283 m2
  of the cell's gross are the 1.80 x 1.80 lift shaft (S-BW 7BE / 7C2, a pit, T-063) and beam / column strips round the
  shaft, which are not slab (the engine deducts only 1.7783 m2 of member overlap). Proposed held bound **0 .. 3.560540
  m3** (the four own slab panels 35.6054 m2 x 0.10), high -0.369248 m3: a lane I held-range fix (the line stays HELD;
  why it is held, the shaft-corner columns read as free columns, is T-042's ENGINE_MISSED_PRINTED_VALUE and is not
  settled here). Not a downgrade record: the line already carries no value.
- **F2 (stair zone on grade)**: OWN-011 8.3723 m2 carries a drawn flight on the ground-beam sheet itself (layer 2: nine
  1.15 m tread lines 160 .. 168 and arcs 169 / 16A); the engine excludes the panel from the slab family (STAIR_ZONE, no
  GS line), T-242 counted it as slab (GS-11). Whether the 0.10 slab runs under the first flight or the flight bears on
  its own base is printed on no sheet read; no owner rule covers it (OWNER_RULE_STAIRS 2026-10-21 / 10-24 searched).
  The stair hall OWN-009 11.52 m2 carries the same kind of tread lines (10D .. 113, 1C4 .. 1C7) and sits in the held
  cell. UNRESOLVED, 0.837230 m3 named; a designer item for the stair ownership work (not an owner question: ERS s.2.7
  not met, the drawings and the designer come first).
- **F3 (small reads)**: -0.0847 m3 in three panels (member overlap in 49a7dae5, the court-side split at arc 158, the
  lift-side oblique panels). Under 0.1 % of the slab family each; named, not traced to one entity.
- **No ENGINE_WRONG quantity** on a valued GS or GB line: every valued ground-slab face equals an own drawn panel to
  0.0001 m2 or differs by a named small read; every valued ground-beam figure is net plan x its printed depth.
- Freelancer: slab FREELANCER double count of the strips (-7.188) + an excess of no drawn element (-0.639); beams one
  section on every run (interior < 5 m too deep, exterior main house too shallow) + lump lengths running partly
  through supports.

## 5. Methods side by side

| Method | Ground slab | Ground beams |
|---|---|---|
| Owner manual method | Q-61 C member by member; no answered rule on a slab under a flight on grade | Q-61 C; D-34 / D-35 designer items |
| Drawing-derived (this task) | 27 panels 217.2315 m2 x 0.10 = 21.72315 m3 if every panel is slab; 35.6054 m2 held with the cell, 8.3723 m2 UNRESOLVED (F2) | valued runs = net plan x printed D; 53.8353 m held |
| Candidate V3.0.29 / V3.0.30 | 24 faces 172.4068 m2 = 17.240684 m3 + held 3.929788 (bound over-stated 0.369248, F1) | 27.625386 m3 on 38 runs + 20 held |
| Freelancer (quantities, private) | one plate over the whole network and more | one section x two lumps |

## 6. Rules, lessons row (proposed)

R-T391-1 .. 5 (`t391_rules.py`). Lessons row (ERS s.7): | 2026-10-31 | GS-SLAB -12.309 and GB-MAIN -10.355 m3 stood
UNRESOLVED as two totals (T-385) | a slab plate and two beam lumps were compared total vs total, with held cells, strips
under the plate and a stair-zone panel inside the same number | a slab residual is split on ONE own partition of the
ground plan (panel / strip / column / shaft, each piece once), each term an own area x the printed thickness; a beam
residual by run into plan, section, held and length terms; a lump length is an untraced remainder with its drawn
envelope, never closed by its sign; a held cell's bound covers its slab panels only (every villa; provenance T-391) |
tests/t391_ground_recon (strip under the plate named; slab over a beam DOUBLE refused; depth from the slab top twice
refused; held as 0 refused; mm areas refused; plate below the network cannot name strips) | PROPOSED |

## 7. Checker re-measure list

- Own partition: the GROUND BEAMS PLAN frame noded on layer 1 + S-COL.BON + S-BW -> 180 faces, 289.1136 m2; panel
  OWN-001 24.505 m2 = 4.225 x 5.80 (edges 114 / 7E0 / 7CF / 7E8 ...), OWN-011 8.3723 with tread lines 160 .. 168.
- The held cell: OWN-007 + OWN-009 + OWN-010 + OWN-047 = 35.6054 m2; lift shaft 7BE 1.80 x 1.80 = 3.24 m2.
- One D 0.40 run (e.g. BAND0018, 4.30 m clear, 1.29 m2 x 0.40 = 0.516) and one exterior run (BAND0001.1 2.40 m x 0.30
  x 0.95 = 0.684).

## 8. Not done / uncertain

- V3.0.30 chain not reproduced in this run (the 83 lines are bound through the committed V3.0.24 file and the exact
  T-385 totals); the engine cell outlines come from the route-G overlay scaled onto the DXF (rectangular reference face
  6.000 m2), good to the cell, not to the millimetre.
- The 0.2367 m2 'member overlap' in 49a7dae5 not located; the 0caa2bd2 / d74f3fe2 split line not identified.
- The freelancer's two lumps cannot be split run by run: the length term stays untraced.
