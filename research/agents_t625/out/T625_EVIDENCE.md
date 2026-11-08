# T-625 floor tile carry-forward: round-stair footprint and open-plan boundaries (R-T625-1)

Research only; no line, class or quantity of the candidate moves. Sources: Drive 'Alsenan chalet project' P7757.dxf and 'ST7757 dxf.dxf' (second drawing, frame residual 0.0 mm), decoded into .work/private only.

## Row 0: GF round-stair footprint below the cut

Own band 6.137684 m2 = F1 4.044824 (annular sector r 1.580511 .. 2.730511 m, sweep 93.491946 deg, 12 treads at 7.791 deg) + F2 2.09286 (run 1.15 wide to the cut 13C, less column 2FD2). Row 6.124412: DIFFERS 0.013272 m2 = {'chord_loss': '0.012453', 'engine_quads_vs_chord_route': '0.000838', 'cad_arc_end_vs_A7': '-0.000019'}. Engine split reproduced: {'F1_chord_plus_strip': '4.095250', 'F2_from_22F_net': '2.03', 'engine_F1_F2': ['4.094412', '2.03']}.

| Beside piece (not in the band) | m2 |
|---|---|
| curtail of the first step (arc 258 to the inner tread arc 239; printed 963 ends on it) | 0.157787 |
| inner string band, curve (23F / 239), net of the curtail | 0.092854 |
| inner string band, run (22C / 22E to the cut) | 0.092454 |
| outer string band, curve (23D / 23E), inside the face (north of A8) | 0.208535 |

Proposals: row: RULE_DIFFERENCE kept (UP-CER-001: the footprint is out of the tile; UP-STAIR-005 treads marble); quantity: ENGINE_WRONG 0.013272 m2 (chord flattening of a drawn arc band): own 6.137684 governs; curtail: ENGINE_WRONG 0.157787 m2: the first step's curtail is drawn (L5 arc 258) and printed (963 ends on it, 0.0 mm): a tread, not porcelain; also absent from the F1 tread marble line (4.094413): marble trade to check; strings: UNRESOLVED 0 .. 0.393843 m2: 0.05 bands drawn beside the tread edges (L5) are stair structure or cladding; ST-02 structure undrawn (Q-50 / T-269 designer item); not floor finish by drawing, not added.
Effect if adopted: GF porcelain L-7625f35c -0.013272 (band) -0.157787 (curtail) m2; row 0 amount 6.124412 -> 6.295471 m2.

## Open-plan outlines

### 1F-LIV.floor_drawn: own 38.988 m2 (AGREES 0.0 vs T-621 38.988; route 2 38.988), level(s) +5.50

Perimeter 43.840000 m by class {'WALL': '24.270000', 'PRINTED_LINE': '14.77', 'DOOR_ON_FACE': '4.7', 'PRINTED_DIMENSION': '0.10'}; columns notched ['3008'], inside []; printed edge checks all agree: True.

| Edge | Open side | m | Bounded by | Status |
|---|---|---|---|---|
| AF9 | DOOR_ON_FACE | 0.9 | BEF | DRAWING_CONFIRMED |
| AF9 | DOOR_ON_FACE | 0.9 | C18 | DRAWING_CONFIRMED |
| AFE | DOOR_ON_FACE | 0.9 | C1A | DRAWING_CONFIRMED |
| AFE | PRINTED_LINE | 1.0 | B9B | DRAWING_CONFIRMED |
| ABE | PRINTED_LINE | 1.15 | ABE | DRAWING_CONFIRMED |
| A8F | PRINTED_LINE | 0.35 | A8F | DRAWING_CONFIRMED |
| AC0 | PRINTED_DIMENSION | 0.05 | 10DF | PRINTED_ONLY |
| AC0 | PRINTED_LINE | 0.1 | AC4 | DRAWING_CONFIRMED |
| AC0 | PRINTED_DIMENSION | 0.05 | 10DF | PRINTED_ONLY |
| AC0 | PRINTED_LINE | 1.15 | AC0 | DRAWING_CONFIRMED |
| C21 | DOOR_ON_FACE | 1.0 | C31 | DRAWING_CONFIRMED |
| AEB | DOOR_ON_FACE | 1.0 | C32 | DRAWING_CONFIRMED |
| B74 | PRINTED_LINE | 5.87 | B74 | DRAWING_CONFIRMED |
| B75 | PRINTED_LINE | 1.6 | B75 | DRAWING_CONFIRMED |
| D24 | PRINTED_LINE | 1.15 | D24 | DRAWING_CONFIRMED |
| AF5 | PRINTED_LINE | 2.4 | AF5 | DRAWING_CONFIRMED |

### 1F-LIV.floor_printed: own 38.5855 m2 (AGREES 0.0 vs T-621 38.5855; route 2 38.5855), level(s) +5.50

Perimeter 43.140000 m by class {'WALL': '23.920000', 'PRINTED_LINE': '13.27', 'DOOR_ON_FACE': '4.7', 'PRINTED_DIMENSION': '1.25'}; columns notched ['3008'], inside []; printed edge checks all agree: True.

| Edge | Open side | m | Bounded by | Status |
|---|---|---|---|---|
| AF9 | DOOR_ON_FACE | 0.9 | BEF | DRAWING_CONFIRMED |
| AF9 | DOOR_ON_FACE | 0.9 | C18 | DRAWING_CONFIRMED |
| AFE | DOOR_ON_FACE | 0.9 | C1A | DRAWING_CONFIRMED |
| AFE | PRINTED_LINE | 1.0 | B9B | DRAWING_CONFIRMED |
| AC0 | PRINTED_DIMENSION | 1.15 | 10DF | DRAWING_CONFIRMED |
| AC0 | PRINTED_DIMENSION | 0.05 | 10DF | PRINTED_ONLY |
| AC0 | PRINTED_LINE | 0.1 | AC4 | DRAWING_CONFIRMED |
| AC0 | PRINTED_DIMENSION | 0.05 | 10DF | PRINTED_ONLY |
| AC0 | PRINTED_LINE | 1.15 | AC0 | DRAWING_CONFIRMED |
| C21 | DOOR_ON_FACE | 1.0 | C31 | DRAWING_CONFIRMED |
| AEB | DOOR_ON_FACE | 1.0 | C32 | DRAWING_CONFIRMED |
| B74 | PRINTED_LINE | 5.87 | B74 | DRAWING_CONFIRMED |
| B75 | PRINTED_LINE | 1.6 | B75 | DRAWING_CONFIRMED |
| D24 | PRINTED_LINE | 1.15 | D24 | DRAWING_CONFIRMED |
| AF5 | PRINTED_LINE | 2.4 | AF5 | DRAWING_CONFIRMED |

### GF-OPEN.full: own 147.657691 m2 (AGREES -0.000026 vs T-621 147.657717; route 2 147.657717), level(s) +1.00

Perimeter 55.306200 m by class {'WALL': '48.050548', 'PRINTED_LINE': '2.255652', 'DOOR_ON_FACE': '5.0', 'PRINTED_DIMENSION': '0'}; columns notched ['2F8A', '2FAE', '2FB4', '2FC0', '2FC3', '2FCF', '2FD5'], inside ['2FC6', '2FD2']; printed edge checks all agree: True.

| Edge | Open side | m | Bounded by | Status |
|---|---|---|---|---|
| 2E4 | DOOR_ON_FACE | 1.0 | 2F2 | DRAWING_CONFIRMED |
| 2E4 | PRINTED_LINE | 1.255652 | 2DC | DRAWING_CONFIRMED |
| 20F | PRINTED_LINE | 1.0 | 22B | DRAWING_CONFIRMED |
| 20F | DOOR_ON_FACE | 1.0 | 2C7 | DRAWING_CONFIRMED |
| AB | DOOR_ON_FACE | 2.0 | 281 | DRAWING_CONFIRMED |
| 158 | DOOR_ON_FACE | 1.0 | 33E | DRAWING_CONFIRMED |

## 1F living readings

- East lane: printed 38.5855 vs last drawn nosing 38.988 (+0.4025): PRINTED edge (10DF end, ST7757 459 on it at 0.0 mm): the 0.4025 beyond it is the 12th tread 0.345 (stair, marble) + the landing nosing band 0.0575 (arrival marble piece, T-240), never porcelain.
- RS-A arrival band 0.0575 m2: ENGINE_WRONG -0.0575 m2 (engine short): the landing nosing band in front of the top riser D24 (L2, ST 315 on it) up to nosing D22 (L5) is floor of the +5.50 living (R-T269 riser convention, as the east lane's 0.0575); in neither the printed reading nor the engine porcelain 33.711036; condition: no ST-02 stair line carries it.
- Restated floor at +5.50: 38.6430 m2; engine - restated = -0.009464 = {'arrival_rule_piece': '0.0475', 'rs_a_band': '-0.0575', 'residual': '0.000536'}.
- Slab edge margin: UNRESOLVED 0 .. 0.376 m2, not added: the structural slab edge (ST 2D2 / 2CF) lies 0.05 beyond the architectural void lines B74 / B75; the architectural line bounds the finish; the printed 1265 (1.25 = 0.05 + 1.15 + 0.05) makes the 0.05 west of B75 the round-stair flight's string; a void-edge / balustrade detail closes it.
- Row 13 with the band: {'his_minus_engine': '0.326464', 'if_band_adopted': '0.268964', 'class': 'UNRESOLVED kept'}.

Rows measured: 41 / 41 (row 0 own area this run; T-621 40 / 41).
