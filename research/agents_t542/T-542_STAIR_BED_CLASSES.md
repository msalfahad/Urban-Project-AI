# T-542 B7 stair bed beyond the treads: risers and landings classed to their governing bed rule

Worker 2 (lane A), 2026-11-06, branch agents/task-T-542, base engine ac3c77b2 (candidate of record ARCH_TAKEOFF_V3.0.58;
its stair and floor-bed lines are those of V3.0.57, T-507 index). Research only, UNWIRED: `research/agents_t542/*`,
`tests/t542_stair_bed_classes/*`. No engine, rule, registry or candidate file changed; no released quantity moves.
ERS s.2.1 (physical element first), s.2.4 (reconcile in units), s.4 (rule + test), s.7 (lesson). No drawing, workbook,
image or client name is copied: every figure is a dimension, a count or a line id already in merged research.

## 1. Physical element

Under each marble piece of a stair lies one cement-sand layer: under a TREAD a bed over the concrete going; behind a
RISER plate a vertical backing against the concrete riser face (not a bed under load); under a LANDING a bed whose rule
depends on what the landing is (T-493 R-T493-1): STAIR_LANDING (between storeys, only stair, UP-STAIR-005),
STAIR_ARRIVAL (at a storey floor, stair marble only by a named owner answer), FLOOR_OR_LANDING (own zone at a floor, no
material source, R-T490-1) and FLOOR (inside a room floor line, OWNER_RULE_STAIRS A6). One surface carries one bed:
a surface already bedded by the floor-bed family (FIN.FLOOR.BED.*) is never also a stair bed.

## 2. Governing bed rule per component (R-T542-1)

| Component | Bed rule | Source | Status |
|---|---|---|---|
| Tread | 0.03 m, 1:3 (V1 OWNER_VALUES STAIR_FLIGHT) + UP-STAIR-017@1.0.0 rate | Q-45 B (stairs 3 cm 1:3), Q-53 C | OWNER PROVISIONAL + CALCULATED PROVISIONAL |
| Riser | same bed, only with a named riser-bed source | Q-45 item 1 asked "marble stairs (treads, risers) __ cm", answered B | ASSUMED - OWNER-APPROVED; without the source HELD (RISER_BED_SOURCE_NOT_GIVEN) |
| STAIR_LANDING | 0.03 m, 1:3 (V1 STAIR_LANDING) | Q-53 scope "every stair (marble treads, risers, landings)" and its worked figure with the two landings at 0.03 1:3, answered C; V1 = the owner's finishing table | ASSUMED - OWNER-APPROVED; without the source HELD, the floor 1:4 bed never borrowed |
| STAIR_ARRIVAL | as STAIR_LANDING, only with its marble answer | Q-66 B (1F), Q-70 A (2F, condition met T-129), OWNER_RULE_OUTDOOR_FLOORS (E1) | as above; without the answer HELD |
| FLOOR_OR_LANDING / FLOOR | the floor host's bed (floor-bed family) | R-T490-1, A6 | beside, never in a stair sum |

The landing question is settled by the owner's record, not by a choice: Q-45 B names no landing bed, but Q-53 was asked
on a scope that put the landings in the 1:3 stair bed and was answered C on that scope, and the owner's finishing table
(V1) carries STAIR_LANDING at 0.03 / 1:3. Physically this holds for a landing between flights (the same stair slab,
the same stone, the same build-up as the treads it joins).

## 3. Result on the drawing-derived stair marble (T-534 C; out/STAIR_BED_COMPONENTS_T542.csv)

Installed mortar = area x 0.03; cement 9.576 bags / m3 and sand 0.9975 m3 / m3 (UP-STAIR-017, theoretical, V7
recomputed); procurement = installed + the Q-45 5 % loss as its own account (V6 / V7).

| Class | Area m2 | Installed mortar m3 | Cement bags | Sand m3 | Procurement m3 (+5 %) | Cement bags proc. | Sand m3 proc. |
|---|---|---|---|---|---|---|---|
| Treads (7 straight flights + E1) | AT_LEAST 23.3700 | 0.701100 | 6.713734 | 0.699345 | 0.736154 | 7.049411 | 0.734311 |
| Risers (8 flights) | AT_LEAST 12.2986 | 0.368958 | 3.533142 | 0.368036 | 0.387408 | 3.709820 | 0.386439 |
| Landings + arrivals (6) | 20.6900 | 0.620700 | 5.943823 | 0.619149 | 0.651736 | 6.241024 | 0.650106 |
| **Whole stair bed** | **AT_LEAST 56.3586** + 6 HELD | **1.690758** | **16.190699** | **1.686530** | **1.775298** | **17.000255** | **1.770856** |
| of which already on the V7 wire (11 released lines) | 35.4325 (lines 35.4313 + polygon 0.0012) | 1.062975 | 10.179049 | 1.060316 | 1.116123 | 10.687994 | 1.113330 |
| **beyond the treads' wire** (7 risers + 4 landings) | **20.9261** | **0.627783** | **6.011650** | **0.626214** | 0.659175 | 6.312261 | 0.657526 |

Beyond the wire: risers MS1-L 1.5717, MS1-U 1.886, MS2-L 1.9044, MS2-U 1.9044, D1 0.667, RS-S 1.6535, RS-A 0.7516
(= 10.3386, candidate lines HELD, counts settled by T-412); landings MS1-LD 1.4375, MS2-LD 2.9325, 2F arrival 4.865,
RS-LD 1.3525 (= 10.5875, no released line, T-502). Hand check: 20.92611 x 0.03 = 0.627783 m3; x 9.576 = 6.0117 bags;
x 0.9975 = 0.6262 m3. The V7 bed of the whole stair is +59.1 % over the treads-only wire (35.4313 -> 56.3586).

HELD by name (never 0): MS1-T winder treads and risers (S-9; reading 1.495 beside), RS-C curved treads 4.0944 and risers
1.8039 (Q-50 A cond), MS2-U 11th going 0.345 (not drawn), MS2-TR closing riser 0.1587 (position). Floor-bed family,
beside: GF hall 4.805 (L-3e451bfc) and GF lobby 1.3225 (L-faa974d2). Adverse view (no riser / landing source): AT_LEAST
23.37 m2 + 20 HELD.

## 4. Double count against the floor-bed family (R-T542-2), checked by element id

- 44 floor-bed elements (FIN.FLOOR.BED.* RELEASED, 23 dry + 21 wet, element id less ':bed') vs every stair element: 0 shared.
- GF hall and lobby (FLOOR_OR_LANDING) carry floor-bed lines: they go to that family once, never to the stair bed.
- 1F arrival: split out of the 1F living porcelain (T-240: 38.633536 - 4.9225 = 33.711036, then - 0.300 T-421); its
  host bed line is 33.411036 = the porcelain line, so the arrival is bedded once.
- RS-LD: the 1F porcelain deduction R04 1.352454 (T-493 F-2, grid 0.00005 vs 1.3525). MS1-LD / MS2-LD: over the stair
  void deducted by the 1F porcelain (T-493). 2F arrival: 0.000 overlap with the 2F lobby porcelain. E1 landing: carried
  only by L-3dd82a57 (T-490). A landing inside a host with no or a partial deduction is refused (test).

## 5. Finding F-T542-1 (for lane I; no line changed here)

The GF hall and lobby beds (6.1275 m2) are released at the dry floor rule (0.03 - 0.04 m, 1:4: 0.1838 - 0.2451 m3,
cement 1.4706 - 1.9608 bags, sand 0.2022 - 0.2696 m3) while their finish material is HELD (floor or landing, RFI-B-A12).
If the designer makes them marble landings the bed becomes 0.03 m 1:3: 0.1838 m3, cement 1.7603 bags (inside the 1:4
range) but sand 0.1834 m3, 0.0188 m3 BELOW the 1:4 low. The material-dependent mix should travel with the material
hold (range covering both mixes, or HELD on the mix) when the floor-bed materials are wired; not an owner question.

## 6. Engine vs freelancer

The freelancer has no cement / sand rows for the stairs (T-511 s.5); his stair marble is pieces x 1.20 (T-425:
RULE_DIFFERENCE / ENGINE_RIGHT). No new freelancer figure. Verdict proposal for the bed scope: ENGINE_RIGHT on the
classification (owner records Q-45 B / Q-53 C / V1), no freelancer pair.

## 7. Uncertain / missing

The riser backing at the full 3 cm is the owner's stated stair bed, not a measured detail (labelled ASSUMED -
OWNER-APPROVED, PROVISIONAL). The 20 mm landing marble (UP-STAIR-007) may take a thicker bed to stay flush with a 30 mm
tread or the adjacent floor; no detail, bed kept at 0.03 (named, not changed). Corner volumes where a tread bed meets
a riser backing are not modelled separately (area x thickness convention of V1). The winders, the curved part, the
MS2-U last going and the MS2-TR position stay with the designer RFIs.

## 8. Rule, tests, lesson

R-T542-1 .. 3 in `stair_bed_classes.py` (docstring, every villa, no villa constant). `tests/t542_stair_bed_classes`
15 tests: P542 fixture by hand (flight 10 x 0.165 / 9 treads x 0.30 x 1.10 + half landing 1.10 x 1.20 + arrival 1.10
x 1.50 = 7.425 m2 -> 0.22275 m3, 2.133054 bags, 0.222193 m3 sand, procurement 0.2338875 m3), the adverse lobby already
in the floor-bed family not counted twice, a stair landing on a floor-bedded element refused, host deduction missing /
partial refused, riser / landing / arrival without a source HELD (no 1:4 borrowed), held part, refusals, mm / mirror /
rotation, no villa constant, and the training-villa pins (`python3 -I research/agents_t542/t542_alsenan.py --check`).

Lessons-register row proposed (ERS s.7):

| 2026-11-06 | the stair bed was wired on treads only (35.43 m2) while the stair marble is 56.36 m2 | risers and landings had no bed class: the riser backing and the landing bed were read as "not stated" although Q-45 item 1 names risers and Q-53's answered scope names landings; floor-level landings could also sit in the floor-bed family | class every stair surface to its bed rule from the owner record (tread / riser with source / stair landing with source / arrival with its answer / floor-or-landing to the floor host), and join by element id so one surface carries one bed | tests/t542_stair_bed_classes | T-542 |
