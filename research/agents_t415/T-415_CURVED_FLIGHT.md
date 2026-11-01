# T-415 ST-02 round stair: the curved flight RS-C defined, measured by handle and the -3.974 m3 residual split (research only)

Worker 1 (lane S), 2026-11-01 05:24 .. UTC, branch `agents/task-T-415`. Development villa (Alsenan is one sample; the
method `t415_rules.py` is for every villa). No engine module, candidate line, released cell, rule or knowledge version
is changed; nothing is released. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied; OWNER_RULE_STAIRS_2026-10-24 s.4 (S-9, (1),
(2), (4)), Q-50 A cond, Q-51 A cond, R-STAIR-LANE-1, R-CONC-OWN-1.

## 0. Sources (own reads this run, private copies in `.work/private` only)

- Structural: 'ST7757 dxf.dxf' (sha256 9f9d1179, Drive 'Alsenan chalet project'), ST p.4 GF roof slab plan, read BY
  HANDLE by `t415_alsenan.py` (asserts type and layer of every handle it uses).
- Second drawing (cross-check): the architectural DXF (P7757_DXF_COMPRESSED.zip), GF plan frame: the same 12 curved
  riser lines (layer 2, 177.8 .. 263.4 deg, 1.150 long, the same 0.050 radial offset), the same concentric arcs
  r 1.5305 / 1.5805 / 2.1555 (walking line) / 2.7305 / 2.7805 m, a 1200 dimension across the straight flight (wall
  face to void edge), '+1.00' at the foot. Plans agree on count, angles, lane and level.
- Freelancer: his ST-02 row in the concrete + rebar workbook (sheet of stairs), read only for his own printed figures
  W 1.2 x L 16.4 x T 0.28 = 5.5104 m3 and his description 'slab + steps' (his T is a combined slab-and-steps
  thickness; the same 0.28 is on his entrance and ST-01 rows). Row text stays private.
- Engine side: merged T-258 r2 ledger RS-S 0.942732 / RS-LD 0.216400 / RS-A 0.377093 = 1.536225 m3 valued (cited).

```
python3 -I research/agents_t415/t415_alsenan.py --dxf <private>/'ST7757 dxf.dxf' --write   # build
python3 -I research/agents_t415/t415_alsenan.py --check                                     # REPRODUCED, no private input
```

## 1. Physical element (ERS s.2.1) and the two methods side by side

ST-02 RS-C: the curved lower part of the round stair from the reception floor +1.00 to +2.929 (12 risers), a helical
reinforced slab ('8 d16/m' text 5BC printed inside its panel) between two opening edges: inner S-OPENING arc 2DE
r 1.530511 and outer S-OPENING arc 2DD r 2.780511 (lane 1.250, R-STAIR-LANE-1: structural lane = opening edge to
opening edge), void on both sides (VOID 2D3 in the well; X 54B / 54C in the outer corner). It ends at riser line 2BA,
the first of the 11 RS-S lines. Its concrete is three different solids (ERS s.3 'one element, several geometries'):

| Solid | Owner manual method (Q-51 A cond, Q-50 A cond) | Drawing-derived method (this run) | Status |
|---|---|---|---|
| steps | 0.5 x riser x each step's own DRAWN plan area | same formula; exact on a curved tread (on every walking path at radius r the step is a triangle R x g(r) / 2) | ASSUMED — OWNER-APPROVED (riser 4.50 / 28, plan count, no section) on DRAWING-CONFIRMED areas |
| waist | 'waist separately'; unknown waist -> HELD | t x K, K = integral of sec(alpha) dA with tan(alpha) = R / (r dtheta): the slope changes with the radius (1.26 at the inner edge, 1.09 at the outer), so never one secant, never a chord x width | HELD: no thickness printed for RS-C (the 'T 16' block 5B6 sits inside the RS-S panel only; ST p.16 typical stair section prints 'THICK.' with no value) |
| joints | 'remove intersections' | census below, each joint once | see s.3 |

## 2. Component table (acceptance a; m2 / m3, ST p.4 by handle)

Riser lines (walking order) 2EA, 2E9, 2E8, 2E7, 2E6, 2E5, 2E4, 2E3, 2E2, 2E1, 2E0, 2DF: radial base angle step
7.790996 deg at every radius (each line is offset 0.050 m from radial, the same offset for all, so the step is
constant). Tread k lies between riser k and k+1; tread 12 between 2DF and 2BA (the junction tread, curved then 0.0846 m
straight).

| Piece | Bounds (handles) | Plan m2 | K (m2) | m3 | Status |
|---|---|---|---|---|---|
| foot zone | lane start (arc ends 2DE / 2DD) -> 2EA | 0.059974 | - | 0 (floor +1.00, not a step) | GROUND SLAB / floor (OWN-011, T-391 F2) |
| treads 1 - 10 | 2EA .. 2E0 | 10 x 0.366379 | 10 x 0.418911 (closed form) | steps 10 x 0.029441 | as s.1 |
| tread 11 | 2E0 -> 2DF, outer strip clipped at the 'B3 (With Stair)' band face 283 | 0.363791 | 0.416076 (numeric) | steps 0.029233 | as s.1 |
| tread 12 (junction) | 2DF -> 2BA, inner arc to 2D0, B3 face 283 | 0.415515 | 0.459079 (numeric) | steps 0.033390 | as s.1 |
| **RS-C steps** | 12 treads | **4.443096** | - | **0.357035** | ASSUMED — OWNER-APPROVED (riser) |
| **RS-C waist** | 12 treads | - | **5.064265** | **HELD** (= 5.064265 x t m3, t not printed) | HELD (RFI-S27) |
| **RS-C total** | | | | **HELD, AT_LEAST 0.357035** (R-T415-5: a reinforced slab is printed, so waist > 0) | HELD |
| curtail | arcs 2EB (2EA -> 2E7) / 2EC (2E9 -> 2E7), layer 2, into the well to r 1.318 | 0.090129 beyond the lane (2EC 0.031306 inside it) | - | HELD, bound 0 .. 0.043455 (0.090129 x 3R, top of step 3 at most; concrete or finish not printed) | HELD (new; RFI-S27 addendum) |
| B3 clip | outer arc strip between r 2.7304 and 2.7805 beyond face 283 (treads 11 / 12 side) | 0.017565 | - | the beam band's (B3 'With Stair' line, Q-61 (2) HOLD) | OWNED_ELSEWHERE |
| waist foot | waist soffit below the floor at riser 1 | - | - | HELD with the waist (depends on t and the GF build-up) | HELD (F2 / RFI-B-S35) |
| CA pair | layer-5 pair 2DB / 2DC (r 2.1055 / 2.2055) under the walking line, continuing as 535 / 536 and 2CC / 2CD | - | - | no section; if a member, it owns its intersection with the waist | UNKNOWN (ST02-CA / ST02-2CC, unchanged) |

Numeric K self-check: the 1.5 mm grid reproduces the closed form of tread 3 to 5e-6 m2 (asserted < 2e-4).
Illustrative scenario only (NOT a quantity, never exported): if the RS-S 'T 16' governed RS-C, waist 0.810282 and total
1.167317 m3 (0.2627 m3 per plan m2 against his 0.28).

Retired reading: on the tread-line lane (1.150, the lines inset 0.050 from both opening edges) the treads are
4.107702 m2 and the steps 0.330083 m3 = the T-258 ledger information figures 'CAD tread areas 4.1077 m2, candidate
steps 0.330'. On the structural lane they are 4.443096 m2 / 0.357035 m3 (+0.335394 m2, +0.026952 m3): the RS-S / RS-A
lane of 1.200 already takes the 0.050 gap to the opening edge (T-258 r2, Verifier 13:10); the curved lane has that gap
on BOTH sides because both edges are S-OPENING.

## 3. Ownership: 0 double (acceptance c)

| Neighbour | Contact | Owner | Double? |
|---|---|---|---|
| RS-S | line 2BA: tread 12 ends there, RS-S's first triangle starts there (RS-S = 11 triangles 2BA .. 2C4, the 11th the wedge into RS-LD) | RS-C / RS-S | no (R-T415-2 asserted) |
| 'B3 (With Stair)' band 283 | outer strip 0.017565 m2 | beam band (held line) | no: clipped out of RS-C |
| ground slab OWN-011 (ST p.3) | foot zone 0.059974 m2 at +1.00; waist foot below the floor | slab (Q-62 A, T-391 F2 HELD) | no: no step lies below +1.00 |
| 1F slab GF-146 | none: RS-C top +2.929 < soffit +5.34 | - | no |
| B20 / B23 (T-189) | ST-01 members: no contact with ST-02 | - | not applicable |
| columns (S-COL.BON) | none within 1 mm of the RS-C lane (census) | - | no |
| ring / dome rings | none on ST p.4 at the stair (no layer-1 arc on the lane) | - | no |

## 4. The -3.974175 m3 residual split (acceptance b; signs engine - freelancer; `decompose_plate_row`, R-T415-6)

His area 1.2 x 16.4 = 19.680 m2 against the whole drawn ST-02 plan 10.835596 m2 (RS-C 4.443096 + RS-S 3.600 + RS-LD
1.3525 + RS-A 1.440): his row is 1.816 x the drawn plan.

| Term | m3 | Cause (physical) | Verdict proposal |
|---|---|---|---|
| RS-LD thickness basis | -0.162300 | his 'slab + steps' 0.28 laid over a FLAT landing; the landing is a plate 'T 16' (1.3525 x (0.16 - 0.28)) | ENGINE_RIGHT (T 16 printed, landing has no steps) |
| RS-S thickness basis | -0.065268 | drawn equivalent 0.942732 / 3.600 = 0.26187 m3 per m2 (T 16 waist x sec + R/2, net of the landing wedge) vs his 0.28 printed on no sheet | ENGINE_RIGHT (merged T-184 / T-258 hand figures) |
| RS-A thickness basis | -0.026107 | same, 0.377093 / 1.440 = 0.26187 | ENGINE_RIGHT |
| RS-C held binding | -1.244067 | his 0.28 x the drawn RS-C plan 4.443096; engine HELD, AT_LEAST 0.357035 (waist t unprinted, K 5.064265) | HELD (RFI-S27) |
| his area beyond the drawn plan | -2.476433 | 8.844404 m2 (7.370 m at his 1.2) that equals no drawn area: whole plan on his width 9.030 m, on two plans 18.059 m, plus the 9 lower treads again (ST p.3) 11.778 m: none reproduces 16.4 | UNRESOLVED (his length; only he can say what it measures) |
| **sum** | **-3.974175** | closes to 1e-6 | |

So the T-406 r3 'ST-02 -3.974175 unexplained' becomes: traced -0.253675 (ENGINE_RIGHT), HELD -1.244067, unexplained
-2.476433. Nothing is closed by 'closer to the freelancer'; his length stays untraced.

## 5. Hand fixture (acceptance d) and tests

`tests/t415_curved_flight/test_t415_rules.py` (Villa H, NOT Alsenan): a 90-degree flight r 1.0 / 2.2, 7 drawn riser
lines at 15 deg, riser 0.170: tread 0.502655 m2, steps 0.256354 m3, K per tread 0.544115 by an independent midpoint
integration, developed centreline 2.513274 m. Adverse: chord 2.262742 refused; one tread owned twice (also with the
ids reversed) refused; 'slab + steps' plate thickness plus separate triangles refused; undrawn winders / a curve
divided by count refused (owner S-9); waist with no thickness HELD (None, never 0); a thickness from another panel
refused; millimetres read as metres refused; missing riser refused; rotation and mirror give identical figures.
`test_t415_alsenan_pins.py`: --check REPRODUCED, 12 drawn risers, lane 1.250, constant step, hand tread 0.366379,
steps = R/2 x area, waist HELD with AT_LEAST bound, the split closes, the retired lane reproduces the T-258 4.1077 /
0.330.

## 6. Proposals (acceptance e; no candidate line moves)

- Lane I (Worker 3, after the Checker): no ST-02 value changes. The held line ST02-RS-C keeps a BLANK quantity and
  carries beside it: AT_LEAST 0.357035 m3 (steps on the structural lane), K 5.064265 m3 per m of waist thickness, the
  12 riser handles; its ledger note 'CAD tread areas 4.1077 m2, candidate steps 0.330' is restated on the structural
  lane (4.443096 / 0.357035, R-STAIR-LANE-1). New HELD named piece ST02-RS-C-CURTAIL (0.090129 m2, bound 0 ..
  0.043455 m3). The T-406 roll-up reads ST-02 as traced -0.253675 / HELD -1.244067 / unexplained -2.476433.
- RFI-S27 addendum (draft for the Lead, nothing sent): 'ST-02 curved flight: the curtail outline 2EB / 2EC at the
  foot reaches 0.212 m into the well beyond the opening edge: concrete step or finish only? and the waist thickness of
  the curved panel (only RS-S prints T 16).' ERS 2.7 not met for an owner question: designer information, already an
  RFI.

## 7. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | The ST-02 curved flight stood as one UNRESOLVED -3.974 m3 lump; its information area was on the tread lines (4.1077 m2) while the straight flights already used the structural lane (T-415) | a curved piece was compared to a plate row as a lump, and the lane rule applied to straight flights was not carried to the curve | a curved flight is steps 1/2 R x each drawn tread area on the structural lane (opening edge to opening edge) + waist t x K, K = integral of sec(alpha) dA with the slope of each radius (never one secant, never the chord); an unprinted waist is HELD with K beside it and AT_LEAST the steps where a reinforced slab is printed; a plate row is split by piece into thickness basis / held binding / area beyond the drawn plan; every villa, curved and helical stairs | tests/t415_curved_flight (chord refused, tread twice refused, undrawn winder refused, waist as 0 / borrowed refused, mm as m, rotation / mirror) | PROPOSED |

## 8. Not done / uncertain

- His 16.4 m: untraced (three drawn candidates tested, none within 0.10 m).
- The riser 4.50 / 28 is the owner's conditional plan count (no section): every step figure inherits ASSUMED —
  OWNER-APPROVED.
- The curtail's material and the waist foot depend on designer facts (RFI-S27 / RFI-B-S35); the CA pair's meaning is
  still UNKNOWN (a member under the walking line would own part of the waist).
- ST p.4 was read in the DXF and cross-read on the architectural DXF; the PDF sheet was not re-rendered this run.
