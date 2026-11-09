# T-584 Steps: external door steps, the E1 entrance step lm and stair-flight steps as count x length (lane A, research)

Worker 2, 2026-11-07, branch `agents/task-T-584`, candidate of record ARCH_TAKEOFF_V3.0.58 (= V3.0.57 for every code
read here). No quantity, line, method, rule or registry file changed. Development villa, not an accuracy claim; the
method R-T584-1 is for every villa. Signs: **ours - his**.

Build: `t584_extract.py --dxf <P7757.dxf> --write` (own read of the architectural DXF by handle, Drive 'Alsenan chalet
project' P7757_DXF_COMPRESSED.zip decoded into `.work/private` only) -> `T584_DRAWN.json` (handles, lengths, printed
level figures, distances; no coordinate); `t584_alsenan.py [--check]` -> `out/T584_STEPS.json` (pinned: T584_DRAWN,
line index V3.0.57, T-325 ledger, T-412 flight table, FREELANCER_RAW_ROWS through the merged T-577 reader).

## 1. Physical elements (ERS s.2.1)

- STEP AT AN OPENING: a change of finished level at a door / gate, built as a front (nosing) edge + a riser. This villa
  draws every step as a pair: front edge solid (layer 5) and a companion 0.050 UPHILL (layer 2) - the same convention as
  every flight (T-412). A step exists only where that edge is drawn AND the printed levels differ.
- Where the edge lies ON the outer wall face with nothing drawn beyond it, the step is the external threshold stone itself
  (its outer nosing + a riser down to the outside): ONE element with the threshold strip. A front edge drawn beyond the
  face would be an outside stair (EXT_STEP, B7, marble by OWNER_RULE_OUTDOOR_FLOORS): none is drawn on this villa.
- FLIGHT STEP (UP-STAIR-008): commercial step lm = drawn treads x drawn width (tread + riser + nosing together); the
  arrival riser's edge is a landing / floor nosing (B7-05), not a step (R-T412-1).

## 2. External doors and the gate (own read by insert handle; levels = nearest printed figure, no wall crossed)

| Opening | Block | Face edge (front / companion) | Printed levels (high / low) | Element | lm | riser | m2 | Status |
|---|---|---|---|---|---|---|---|---|
| D-GF-01 dewaneya -> court | D120 15E | 172 / 173, 0.900 | +0.30 (401) / +0.15 (394) | THRESHOLD_STEP | 0.900 | 0.15 | 0.135 | DRAWING-CONFIRMED |
| D-GF-03 -> court | d220 1B5 | 1C6 / 1C7, 0.800 | +0.30 (403) / +0.15 (409) | THRESHOLD_STEP | 0.800 | 0.15 | 0.120 | DRAWING-CONFIRMED |
| D-GF-05 kitchen -> side passage | D120 192 | 19C / 19D, 0.900 | +0.30 (405) / +0.15 (407) | THRESHOLD_STEP | 0.900 | 0.15 | 0.135 | DRAWING-CONFIRMED |
| D-GF-09 stair hall -> side walk | D120 3FF | 3FD / 3FE, 0.900 | +0.30 (4AC) / not printed | THRESHOLD_STEP | 0.900 | HELD 0 .. 0.30 | HELD 0 .. 0.270 | riser HELD |
| D-GF-06 pantry -> E1 landing | D120 33E | none | +1.00 (411) / landing +1.00 (T-260 ruling) | NO_STEP | - | - | - | NOT_APPLICABLE |
| D-GF-07 main door -> E1 landing | D200 281 | none | +1.00 (40F) / +1.00 (411) | NO_STEP | - | - | - | NOT_APPLICABLE |
| D-2F-01 lobby -> roof | D115 12BA | none | +9.70 (134E) / +9.70 (1352) | NO_STEP | - | - | - | NOT_APPLICABLE |
| D-GF-15 gate in the fence | D120 2D8 | fence line 8E through / 8F, 0.900 | +0.15 (40B) / +-0.00 (datum LEL A89) | THRESHOLD_STEP | 0.900 | 0.15 | 0.135 | DRAWING-CONFIRMED |

Checks: in every pair the companion lies on the higher printed side (uphill), asserted in code; the one parallel line
beyond a face (3CB at D-GF-05, 1.20 out) is the inner line of the window in the passage's opposite wall (glazing 3CC ..
3CF behind it, wall ends 3D1 / 3D5), not a step. The drawn nosing runs between the frame members (0.900 / 0.800); the
stone under the frame is the T-325 strip width (1.000 / 0.900 / 1.000 / 0.900), which stays the strip line's measure.
D-GF-05 is booked by T-325 as a wet marble threshold; it is an outside door (T-268) with a 0.15 step: cross-trade note.
D-GF-15: the drawn clear 0.900 (8F) and block 1.000 are new evidence for its HELD unbounded strip line (T-327 s.4).

## 3. Tables (causes close exactly; % withheld wherever HELD / SCOPE / UNIT / UNRESOLVED / omission)

Stair steps (his H16 / H23 / H30: count x width booked in his area column):

| Stair | lm ours / his | nr ours / his | Causes (lm) |
|---|---|---|---|
| ST-01 main + D1 | 51.750 / 75.60 | 45 / 63 | width 45 x (1.150 - 1.20) -2.25 ENGINE_RIGHT; MS1-T winder turn HELD 5 pieces -6.00 (ours blank, beside >= 4.14365, C-ST-3); 6 arrival edges -7.20 RULE_DIFFERENCE; 7 pieces -8.40 UNRESOLVED (T-412 / T-578) |
| ST-02 round | 16.100 / 33.60 | 14 / 28 | width -0.70 ENGINE_RIGHT; RS-C HELD 12 pieces -14.40 (beside 13.7964 .. 13.85, Q-50 A cond); 2 arrival edges -2.40 RULE_DIFFERENCE |
| ST-03 E1 | 0 / 14.00 | 0 / 5 | **ENGINE_OMISSION -11.20 CONFIRMED** (4 fronts 36E 36C 36A 30B x 2.800, dimension A06 2800, re-read by handle); platform edge 30A -2.80 RULE_DIFFERENCE |
| m2 | 0 / 123.20 | - | UNIT: his lengths in an area column; tread / riser m2 are B7-02 / B7-03 |

Every one of the 14 FIN.STAIR.STEP_LM lines is used (7 owned, 2 HELD) or named (5 second readings, never valued). Owned
lines = drawn treads x 1.150 asserted to the line value; candidate + held treads = T-412 census treads per stair.

Door steps (his H36..H41: six pieces 1.30 / 2.50 / 1.00 / 1.00 / 0.90 / 1.00 = 7.70, no door id):

| Group | lm ours / his | m2 ours / his | nr ours / his | Verdict proposal |
|---|---|---|---|---|
| House doors | 3.500 / 7.70 | 0.390 (+ D-GF-09 HELD 0 .. 0.270) / 7.70 (UNIT) | 4 / 6 | UNRESOLVED -4.20 lm / -2 nr: 4 drawn steps, none at D-GF-06 / -07 / D-2F-01 (same level, no edge); his rows carry no id, so matching by figure is refused. Reading H1 (one per external door) would put 3 of his pieces where nothing is drawn |
| Gate D-GF-15 | 0.900 / - | 0.135 / - | 1 / - | UNRESOLVED (SCOPE): whether his rows hold the fence gate is not established |

F-T577-2 resolved as an element: the external door step is NOT a separate piece outside the door on this villa; it is
the threshold stone's outer nosing + riser (ruling proposal FR-T584-3). Our strips 6.80 lm (T-577) and his door steps
7.70 lm remain different measures of different scopes.

## 4. Fix-row proposals (manifest style; nothing wired, all HELD until lane I wires them)

- FR-T584-1: B7-06 FIN.STAIR.STEP_LM line for E1: 11.200 lm / 4 nr, DRAWING-CONFIRMED, marble (owner outdoor rule),
  bound to the E1 tread L-314c3ac6d45431b687c5 / riser L-0afa7bd369ec489ebfc2; 30A stays the landing edge.
- FR-T584-2: nosing lm + riser m2 beside the strip on the owning threshold line, D-GF-01 / -03 / -05 / -09 / -15 (table
  s.2); no new step line; material by the strip's specification (HELD).
- FR-T584-3 (ELEMENT_REGISTER ruling, Lead): R-T584-1 (b) one element / two elements / NOT_APPLICABLE as in s.1.

## 5. Rule, tests, lessons row (proposed)

R-T584-1 (t584_rules.py). Tests `tests/t584_steps` (35): fixture Villa K584 (entrance 3 x 2.40 = 7.20 lm, flight 14 x
1.10 = 15.40 lm, mm = m, threshold step 0.90 x 0.15 = 0.135 m2, step beyond the face, same level = NOT_APPLICABLE,
unprinted level HELD with bound, piece-per-riser split, rotation 0/37/90/180/211 x mirror); adverse: step lm booked as
m2 refused, a step owned by threshold and outdoor floor refused, default step without an edge refused, edge between equal
levels refused, edge on face and beyond as one piece refused, unprinted level without bound refused, cm / fractional
treads / zero width refused, unnamed residual / open gap refused, HELD without bound and VERIFIED refused, omission
withholds %; Alsenan pins (byte-identical rebuild, edited input stops the build, door set, hand checks, closures, no
coordinates). L2 with t577 / t412: 93 pass.

Lessons row: | 2026-11-07 | his 'door steps' read as a separate piece outside each external door | the reference row
carries no door id and the drawn step convention (edge pair on the wall face) was not read | R-T584-1: a step exists only
where its edge is drawn and the printed levels differ; an edge on the face is the threshold stone's nosing (one element);
same level both sides = no step | tests/t584_steps | PROPOSED |

Missing / uncertain: the side-walk level at D-GF-09 (not printed); the nosing / threshold stone specification (not
printed, T-412 RFI 1); his door-step rows' doors (no id); the ST-01 winder subdivision (C-ST-3) and RS-C (RFI-S27).
