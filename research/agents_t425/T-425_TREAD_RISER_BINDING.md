# T-425 stair TREAD / RISER finish binding in the candidate V3.0.36 (development villa; method every villa)

Worker 2 (lane A), 2026-11-01. Research files `research/agents_t425/*` and `tests/t425_tread_binding/` only; no engine,
rule, knowledge, method, registry or candidate file touched; no candidate quantity changed (lane I proposal in section
6). ERS applied (s.2.1 physical element first, s.2.2 evidence, s.2.4 reconciliation in units, s.4 rule + test, s.7
lesson). Rules: OWNER_RULE_STAIRS_2026-10-24 s.1 (one verified stair geometry; a landing never both a tread and a
landing), s.4 S-9 (never generate winders; N-1 only where demonstrated; release per quantity; HELD blank), UP-STAIR-002
(drawing governs), UP-STAIR-005 (landing polygons), UP-STAIR-008 (commercial step lm), Q-46 A (section A-A counts for
ST-01), Q-50 A cond (round stair: curved part HELD), T-184 R-STAIR-CONT-1, WORKFLOW_CONTROLS s.5. No image, client
name, drawing text or workbook row text is copied here.

## 0. What was read

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural DXF, sha ab54dd55) and "ST7757 dxf.dxf" (sha 9f9d1179), decoded into `.work/private` only | own re-read BY HANDLE: MS1-L DC .. 485 (+ companions), the winder radials 4A2 / 49E / 4A0 on GF and BE6 / BE8 / BEA (+ BE7 / BE9 / BEB) on 1F, MS1-U A92 .. ABE, MS2-L AC0 .. A97, the 2F west lane 1387 .. 135F (+ 1389 .. 1362), MS2-U 135B .. 1386, D1 481 .. 490 |
| Candidate of record: `research/agents_t246/v3036_run.py` on the Drive copies (after `research/agents_t167/v304_run.py`), file V3_0_36_BOQ_LINES.json sha256 d462203f.. (4730 lines; the same run reproduces V3_0_35_BOQ_LINES.json byte-identical to T-412's b011bace..; every stair line id and value is unchanged from V3.0.35 to V3.0.36) | every stair line (FIN.MARBLE.TREAD / FIN.STAIR.STEP_LM / FIN.MARBLE.RISER / FIN.MARBLE.LANDING) with its calculation input `flight_id`; the engine's cross-plan repeat record (ARCH_PLAN `run/cross_plan_stairs`) and its flight footprints (ARCH_ROOMS) |
| research/agents_t412 (MERGED f9c80501): ALSENAN_EDGES_T412.json | the drawn front-edge table per flight (built on, not re-derived; re-checked by handle here) |
| research/agents_t184 (MERGED; levels, A-A riser counts, R-STAIR-CONT-1), agents_t410 (notches), agents_t415 (RS-C) | levels, counts, continuation rule |

## 1. Physical element and the question (ERS s.2.1)

A TREAD is the going surface behind one drawn front (nosing) edge; a landing / floor edge is the top nosing of a flight
and has no tread behind it (T-412 R-T412-1). B7-02 (tread marble, m2) and B7-06 (commercial step, lm, UP-STAIR-008)
are therefore owned by the FLIGHT, a physical run of steps between two levels. The engine reads stair flights per
storey plan; one physical flight is drawn on up to three plans: below the cut on its own storey plan, hidden above the
cut on the plan below (PARTIAL), and again on the plan above, seen down through the stair opening (SEEN_THROUGH). The
question is, per flight: how many readings are valued, how many treads each carries, and against what is drawn.

## 2. Binding: every candidate stair reading to a drawn flight (BINDING_T425.json)

The engine's own cross-plan record classifies each repeat as STACKED (a different flight in the same plan position on
the storey above: valued on both plans) or SEEN_THROUGH_VOID ("counted once, on the plan below"). Own reading of what is
physically built:

| Engine reading | Plan / lane | Engine class | Drawn flight (own reading) | Role | Evidence |
|---|---|---|---|---|---|
| GF F1 (L-151d / L-d4d7) | GF west lane | STACKED under 1F F2 | MS1-L +1.00 -> +2.667 | OWN | 8 hidden riser-face lines DE .. CD read, 7 treads; the solid fronts DC .. C9, C8 (to the cut) and the hidden C5 front 9 straight treads at 0.300 |
| GF F2 (L-a4ae / L-f20f) | GF east lane | STACKED under 1F F3 | D1 +0.30 -> +1.00 | OWN | 481 484 48F + floor edge 490 |
| 1F F2 (L-6580 / L-2365) | 1F west lane | (lower of 2F F1) | MS2-L +5.50 -> +7.516 | OWN | AC0 .. A97, 12 lines, A97 = landing edge |
| **2F F1 (L-79be / L-1e88)** | 2F west lane | **STACKED** over 1F F2 | **MS2-L again** | **SEEN_THROUGH** | 11 solid lines 1387 .. 135F with hidden companions +0.050 at run positions -0.30 .. 2.70, the SAME positions as 1F ABF .. A97 (asserted by handle); no flight leaves 2F (T-184 R-STAIR-CONT-1: the 2F plan draws no flight from +9.70; ST p.6 covers the shaft) |
| 1F F3 (L-e1eb / L-0aa4) | 1F east lane | (lower of 2F F2) | MS1-U +3.50 -> +5.50 | OWN | A92 .. ABE 11 fronts |
| 2F F2 (L-07f0 / L-60fc) | 2F east lane | STACKED over 1F F3 | MS2-U +7.684 -> +9.70 | OWN | 135B .. 1386 11 fronts; a genuinely different flight (MS2-U lies over MS1-U and hides it) |
| **1F F5 (L-b466 / L-e085)** | 1F, ST-01 shaft north end | none (a 1F flight) | **MS1-T winder turn (+2.667 -> +3.50), seen down through the opening** | SEEN_THROUGH | engine footprint box = run positions -46.003 .. -44.703 / 2.75 .. 3.935 in the 1F frame = the ST-01 west lane + well band at the turn; the 1F plan draws the winder radials there as BE6 / BE8 / BEA (solid) with companions BE7 / BE9 / BEB (layer 2), at the same positions as GF 4A2 / 49E / 4A0. **Corrects T-412's "UNBOUND"**: T-412 looked for it at RS-LD |
| GF RS-C F1 (L-fa53 / L-95b9) | GF | (lower of 1F F1) | RS-C curved | OWN | Q-50 A cond: curved part HELD |
| 1F F1 | 1F | SEEN_THROUGH_VOID | RS-C | SEEN_THROUGH | not valued (BOUNDED_EXPOSURE) |
| GF RS-S F2 + F3 (L-89c8 / L-0ec4) | GF, above the GF cut | SEEN_THROUGH_VOID (F2); none (F3) | RS-S +2.929 -> +4.696 | PARTIAL x 2 | hidden; 6 + 3 treads |
| 1F F4 | 1F | (upper of GF F2) | RS-S | OWN | 10 treads, NOT valued (BOUNDED_EXPOSURE) |
| GF RS-A F4 (L-1dac) | GF, above the GF cut | SEEN_THROUGH_VOID | RS-A +4.696 -> +5.50 | PARTIAL | 3 treads |
| 1F F6 | 1F | (upper of GF F4) | RS-A | OWN | 4 treads, NOT valued |

## 3. Result per flight: drawn vs candidate (FLIGHT_TABLE_T425.csv, LINE_TABLE_T425.csv)

Tread m2 on the engine's own basis (drawn going x drawn front-edge width; straight goings 0.300 front to front by
handle); step lm = treads x drawn width (B7-06 owner row basis, treads only).

| Flight | Drawn treads | Candidate valued readings (treads) | B7-02 m2 before -> after | B7-06 lm before -> after | Cause of the mismatch | Class |
|---|---|---|---|---|---|---|
| MS1-L | 9 straight (+ winder 485 in the HELD turn) | GF F1 (7) | 2.415 -> **3.105** (+0.690) | 8.050 -> **10.350** (+2.300) | the engine reads the riser-face companions DE .. CD (8 lines = 7 treads); the treads fronted by C8 (drawn solid only to the cut break) and C5 (hidden, above the cut) are not read | ENGINE_WRONG -2 treads |
| MS1-T (turn) | 4 wedges on the plans / 5 on A-A / 3 on ST p.4 | 1F F5 (4) | 1.495 -> **HELD** | 4.7815 -> **HELD** | a winder turn seen from 1F, valued as a 1F flight; owner S-9 + C-ST-3 count conflict | HELD (beside 1.495 / 4.7815) |
| MS1-U | 11 (ABE's going 0.300 drawn on ST p.4: 459 at s 3.30) | 1F F3 (10) | 3.450 -> **3.795** (+0.345) | 11.500 -> **12.650** (+1.150) | n lines -> n - 1 treads: the last drawn front ABE is a tread whose rear (the 1F floor edge) is not on the arch plan (A-A 12 risers) | ENGINE_WRONG -1 |
| MS2-L | 11 | 1F F2 (11) **and 2F F1 (10)** | 7.245 -> **3.795** (-3.450) | 24.150 -> **12.650** (-11.500) | the same flight valued on 1F and again on 2F: the engine classes the 2F reading STACKED (a new flight) because it has no level test; nothing leaves 2F | **DOUBLE COUNT confirmed** |
| MS2-U | 11 (1386's rear, the 2F floor edge, drawn on neither sheet) | 2F F2 (10) | 3.450 -> **3.450** + 1 tread HELD (beside 0.345) | 11.500 -> **12.650** (+1.150) | n - 1 as MS1-U; the 11th tread's front 1386 is drawn (pieces / step lm stand), its going is not | ENGINE_WRONG -1 (lm); m2 HELD for 1 tread |
| D1 | 3 | GF F2 (3) | 1.035 -> 1.035 | 3.450 -> 3.450 | | AGREE |
| RS-S | 10 | GF F2 (6) + GF F3 (3) | 3.105 -> **3.450** (+0.345) | 10.350 -> **11.500** (+1.150) | valued on the plan BELOW (hidden, above its cut) where 9 of 10 are read; the 1F reading (10, below the 1F cut) is the complete one and is not valued | ENGINE_WRONG -1 |
| RS-A | 4 | GF F4 (3) | 1.035 -> **1.380** (+0.345) | 3.450 -> **4.600** (+1.150) | as RS-S (1F reading 4 not valued) | ENGINE_WRONG -1 |
| RS-C | 12 radial | GF F1 (12) | 4.094 -> **HELD** | 13.796 -> **HELD** | valued PROVISIONAL where Q-50 A cond holds the curved part | HELD (beside 4.094 / 13.796) |
| E1 | 4 x 2.800 | separate line L-314c3ac6d45431b687c5 (no flight_id) | see section 3.2 | | | AGREE |

**Totals over the 14 flight readings (BINDING_T425.json; E1 separate):** B7-02 valued **27.324 -> 20.010 m2 (-7.314 m2, -26.8 %)** = double count -3.450 (MS2-L
on 2F) - HELD 5.589 (RS-C 4.094 + MS1-T 1.495) + treads not read +1.725 (MS1-L 0.690 + MS1-U 0.345 + RS-S 0.345 + RS-A
0.345); the RS-S partial reading F3 (1.035) folds into F2. MS2-U's 11th tread 0.345 m2 HELD beside. B7-06 valued
**91.028 -> 67.850 lm (-23.178 lm)** = double -11.500 - HELD 18.578 + treads not read +6.900 (2.300 + 1.150 x 4).
Hand check: 17.250 + 0.690 + 0.345 + 1.380 + 0.345 = 20.010; 57.500 + 2.300 + 1.150 + 1.150 + 4.600 + 1.150 = 67.850.

### 3.1 Risers (B7-03) and landings (B7-04)

Every FIN.MARBLE.RISER line is BLOCKED_RFI with no quantity (riser height basis open): no m2 at stake today, but one
riser line exists per engine reading, so the 2F F1 (L-7adf1ccd0c407b61221a, MS2-L again) and 1F F5
(L-820baecf7f726b4d8f1e, MS1-T) riser lines carry the same disposition as their tread lines (not valued beside 1F F2;
HELD), and the drawn riser counts per flight are T-412's (MS1-L 10, MS1-U 12, MS2-L 12, MS2-U 12, D1 4, RS-S 11, RS-A 5;
turn and RS-C HELD). The two FIN.MARBLE.LANDING lines (GF L-1983e89d8b619eade1db, 2F L-5d2be30dd8d2ffeacc42) are
BOUNDED_EXPOSURE upper bounds "enclosure - drawn treads": the 2F bound subtracts the MS2-L treads read through the well,
which is a void at 2F, not a landing; no valued m2 changes, the bound basis is noted for the B7-04 owner row.

### 3.2 E1

Candidate L-314c3ac6d45431b687c5 SOURCE_DERIVED 3.3594 m2 (T-157 CAD polygon of the merged ledger) vs printed 4 x 0.300
x 2.800 = 3.360 m2: AGREE (-0.0006 m2, -0.02 %, polygon vs printed figures); no change proposed.

## 4. Freelancer ST-01 63 vs 56 pieces, traced (quantities only)

His row: 63 pieces x 1.20 for the main stair incl. the lobby flight (T-412 s.5). Drawn: 56 risers = MS1-L 10 + turn 5 +
MS1-U 12 (GF -> 1F 27, riser 166.7 mm) + MS2-L 12 + MS2-TR 1 + MS2-U 12 (1F -> 2F 25, 168.0 mm) + D1 4 (175 mm).
Every drawn reading fails (risers 56, treads 45 + winders, 52 without D1, 57). Tested: pieces = ceil(storey rise /
uniform riser r), per storey, levels +0.30 / +1.00 / +5.50 / +9.70 (T-184): **r in 150.0 .. 155.0 mm gives 5 + 30 + 28 =
63** (and r = 150 mm also on the merged lobby -> 1F split, 35 + 28); 160 mm gives 61, 165 mm 59, 170 mm 57 (sweep in 0.5
mm steps, `freelancer_trace`). So his 63 is reproduced exactly by a storey-height / 150-155 mm riser estimate, not by the
drawn count. Proposal: **RULE_DIFFERENCE (estimate by assumed riser) / ENGINE_RIGHT on the drawn 56** (Q-46 A: the
section counts); not proven (his row has no breakdown); his ST-02 28 and ST-03 5 equal the drawn counts. Width: ENGINE
RIGHT 1.150 drawn vs his 1.20 (T-412).

## 5. Rule, test, lesson

- **R-T425-1** one flight occurrence, one valued tread line: every valued tread / step line binds to exactly one drawn
  flight or is HELD by name (UNBOUND); a flight carries at most one valued tread and one valued step line; a further
  SEEN_THROUGH reading is a DOUBLE_COUNT, a further PARTIAL reading is FOLDED into the carrier; never summed.
- **R-T425-2** the tread count is the number of drawn tread fronts (solid and hidden layers), never "lines - 1"; tread
  m2 = sum of drawn going x drawn width; a tread whose going is drawn on no sheet keeps its piece / step lm and its m2 is
  HELD by name (no uniform-going default).
- **R-T425-3** a reading of a flight the owner holds (winder turn S-9, curved part Q-50) is HELD, whatever its count.
- Engine causes named for lane I (no engine change here): (a) the cross-plan class STACKED vs SEEN_THROUGH is decided
  without levels: a repeat on the storey above is a new flight only when a flight is drawn LEAVING that storey (T-184
  R-STAIR-CONT-1); (b) "seen through: counted once, on the plan below" values the plan where the flight is ABOVE the cut
  (hidden, partial: RS-S 9 / 10, RS-A 3 / 4): the governing reading is the plan whose cut the flight lies below; (c) n
  lines -> n - 1 treads ignores that the last drawn line is a tread front when the floor edge is undrawn (MS1-U, MS2-U),
  and that a tread above the cut is drawn hidden (MS1-L).
- Tests `tests/t425_tread_binding`: Villa K425 hand fixture (U stair: a flight valued on GF short by 2 hidden treads, a
  flight seen through from 2F, a last tread with undrawn going, a held winder turn, an unbound ghost reading; adverse
  'flight valued twice' must be DOUBLE_COUNT and the C flight valued once; refused: mm as m, zero going, a front edge
  twice, a going without source, two OWN readings, unknown flight, unbound as OWN, valued without quantity, reading
  twice); order and mirror invariance; Alsenan pins on the committed binding (reproduces, hand totals, the double count
  line ids, the F5 rebinding, the freelancer trace).
- Lessons-register row proposed:

| 2026-11-01 | candidate stair treads 27.324 m2 vs 20.010 drawn: MS2-L valued on 1F and 2F (3.450), RS-C and the winder turn valued where held (5.589), 5 flights short by 1-2 treads (1.725) | cross-plan class without levels (STACKED vs seen through), 'counted once on the plan below' takes the hidden partial reading, n lines -> n - 1 treads | one physical flight, one valued tread line, on the plan whose cut it lies below; tread count from drawn fronts (both layers); held flights never valued (any villa) | tests/t425_tread_binding | T-425 |

## 6. Lane I proposal (no candidate change in this task)

Per line id in LINE_TABLE_T425.csv: CORRECT MS1-L / MS1-U / RS-S (carrier GF F2) / RS-A (GF F4) to the drawn values;
MS2-U step lm 12.650, tread m2 3.450 + 1 tread HELD (TREAD_GOING_NOT_DRAWN, beside 0.345); SUPERSEDE (not valued, never
deleted) 2F F1 tread / step / riser lines (DOUBLE_COUNT of 1F F2) and RS-S GF F3 (FOLDED into GF F2); HELD by name 1F
F5 (MS1-T, S-9) and GF RS-C (Q-50 A cond) with their beside figures. No owner question: every item is a drawing fact or
an answered rule (S-9, Q-46, Q-50); the turn and RS-C stay on the existing designer list (C-ST-3, RFI-S27).

## 7. Self-gate and what is missing

self-gate: a (research + tests only) c (non-Alsenan K425 fixture with adverse cases) d (reproducible: `python3 -I
research/agents_t425/t425_alsenan.py --dxf <P7757.dxf> --candidate <run>/v3036/V3_0_36_BOQ_LINES.json --write`;
`--check` without private input) f (nothing wired, no item code created) h (handles, run positions, lengths, counts and
engine ids only) PASS.
Missing: the winder turn and RS-C (designer); MS2-U's last going (designer: the 2F floor edge position); the notch
deductions at 5 edges (T-410, 0.1175 m2) are not in these figures (width 1.150 per tread kept on the engine basis).
