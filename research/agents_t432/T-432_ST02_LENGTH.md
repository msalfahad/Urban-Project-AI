# T-432 ST-02 freelancer length basis: is his 16.4 m one drawn construction? (research only)

Worker 3 (cross-lane, lane S row), 2026-11-01 15:01 .. UTC, branch `agents/task-T-432`. Development villa (Alsenan is
one sample; the method `t432_rules.py` is for every villa). No engine module, candidate line, released cell, rule or
knowledge version is changed; nothing is released; the RS-C waist stays HELD. ERS s.2.1 - 2.4, s.3, s.7;
OWNER_RULE_STAIRS_2026-10-24 (S-9: no undrawn winders); R-T415-1 / -6, R-T417-1, R-STAIR-LANE-1.

## 0. Sources

- Structural: 'ST7757 dxf.dxf' (sha256 9f9d1179, Drive 'Alsenan chalet project'), ST p.4 GF roof slab plan, own read
  this run BY HANDLE (`t432_alsenan.py` asserts type and layer): arcs 2DE / 2DD (S-OPENING), riser lines 2EA .. 2DF
  (RS-C), 2BA .. 2C4 (RS-S), 2C8 .. 315 (RS-A), edges 2D0 / 2CF (S-OPENING), 283 / 289 (layer 1). Private copy in
  `.work/private` only.
- Second drawing (own read this run): the architectural DXF P7757.dxf (P7757_DXF_COMPRESSED.zip), both ST-02 frames
  (concentric S-OPENING-radius arcs 2780.5 / 1530.5 on layer 5). See s.3a: the 1F frame ('+5.50') agrees with ST p.4
  piece by piece; the GF frame ('+1.00') prints a different straight part.
- Freelancer: his ST-02 row W 1.2 x L 16.4 x T 0.28 = 5.5104 m3, count 1, read this run for its numeric cells only
  (concrete + rebar workbook, stairs sheet; no row text, no header cells): L 16.4 is a TYPED constant (no formula),
  E = T x L x W, total = count x E. So 16.4 carries no construction of its own; its printed precision is one decimal.
- Engine side: drawn plan 10.835596 m2 and the term AREA_BEYOND_DRAWN -2.476433 m3 (T-415 MERGED 8c8372a4).

```
python3 -I research/agents_t432/t432_alsenan.py --dxf <private>/ST7757_dxf.dxf --write   # build
python3 -I research/agents_t432/t432_alsenan.py --check                                   # REPRODUCED, no private input
```

## 1. Physical element and the question (ERS s.2.1, s.2.4)

ST-02 is the round stair +1.00 -> +5.50, 28 drawn risers (riser 4.50 / 28 = 0.160714, Q-50 A cond, ASSUMED —
OWNER-APPROVED), in walking order:

| Piece | Kind | Risers (handles) | Plan from its first riser to the next piece's first riser |
|---|---|---|---|
| RS-C | curved, lane 1.250 (r 1.530511 .. 2.780511), constant step 7.790996 deg | 12 (2EA .. 2DF) | arc to 270 deg + 0.0846 straight to 2BA |
| RS-S | straight, lane 1.200 (2D0 -> 283) | 11 (2BA .. 2C4, at 0.300) | 3.000 |
| RS-LD | corner landing 1.150 x 1.200 (2C4 -> 289, 283 -> 2C8) | 0 | depends on the path (below) |
| RS-A | straight, lane 1.200 (2CF -> 289) | 5 (2C8 .. 315, at 0.300) | 1.200 |

Owner manual method / drawing-derived method side by side: the owner's method (Q-51 A cond, Q-47 A) measures steps by
drawn plan area and the waist on its own soffit; it never uses one row length. The question is therefore NOT how to
measure ST-02 (T-415 / T-258 did) but what HIS length measures: T-417 showed his ST-01 length 5.300 = run 3.300 + rise
2.000 exactly (developed stepped profile). Is 16.4 the same construction, or any other one stated construction?

## 2. Plan lengths per piece and path (m, own read by handle)

| Path (one rule on every piece, R-T432-1) | RS-C | RS-S | RS-LD | RS-A | Plan total |
|---|---|---|---|---|---|
| INNER (opening edge: arc r_in to 2D0, void edges) | 2.546239 | 3.000 | 0.000 (inner corner) | 1.200 | 6.746239 |
| CENTRE (each piece's lane centreline) | **3.571913** | 3.000 | 1.150 (0.55 + 0.60) | 1.200 | 8.921913 |
| RISERS (polyline through the drawn riser-line midpoints) | 3.570199 | 3.000 | 0.849264 (2C4 mid -> 2C8 mid) | 1.200 | 8.619463 |
| OUTER (arc r_out to 283, then 283 / 289) | 4.594408 | 3.000 | 2.350 (1.15 + 1.20) | 1.200 | 11.144408 |

RS-C CENTRE by hand (Checker re-measure): r_c = (1.530511 + 2.780511) / 2 = 2.155511; 2EA meets r_c at
175.9736 + asin(0.05 / 2.155511) = 177.3029 deg (the riser lines are offset 0.050 from radial); arc to 270 deg =
92.6971 deg = 1.617872 rad x 2.155511 = 3.48731 m; + 0.0846 straight to 2BA = 3.5719 m (module 3.571913, by line-circle
intersection). Its developed profile (T-417 basis) = 3.571913 + 12 x 0.160714 = **5.500484 m**. The centre chord 2EA ->
2BA (3.160467) is recorded and refused as a length (R-T432-3). Noted: the curved lane centre (r 2.155511) and the
straight lane centre (2.130442) differ by 0.025069 at 270 deg (lanes 1.250 vs 1.200); the jump is lateral, it adds no
length to the CENTRE path.

## 3. Constructions tested (acceptance: name, formula, m, misfit = construction - 16.400)

49 constructions, each a fixed rule with no free parameter (full table in `summary_t432.json`): 4 paths x 4 bases
(PLAN; PROFILE = plan + 28 risers once; INCLINED = each flight sqrt(plan^2 + rise^2), landing flat;
PROFILE_LANDING_IN_BOTH = the landing counted in both adjoining flights), ONE_LENGTH (one flight's profile x 3 flights,
without / with the landing: the T-417 sibling convention), COUNT (26 drawn treads x 0.300 with / without landing and
rise), and the T-415 double-drawing reading (profile + the 9 lower RS-C treads again, drawn also on ST p.3).

| Construction | Formula | m | Misfit m |
|---|---|---|---|
| ONE_LENGTH 3 x RS-C RISERS profile | 3 x (3.570199 + 1.928571) | 16.496311 | +0.096311 |
| ONE_LENGTH 3 x RS-C CENTRE profile | 3 x 5.500484 | 16.501453 | +0.101453 |
| ONE_LENGTH 3 x RS-S OUTER profile + landing | 3 x (3.000 + 1.767857) + 2.350 | 16.653571 | +0.253571 |
| CENTRE PROFILE + RS-C treads 1-9 again (ST p.3) | 13.421913 + 9 x 2.155511 x 0.135978 | 16.059842 | -0.340158 |
| OUTER PROFILE | 11.144408 + 4.500 | 15.644408 | -0.755592 |
| CENTRE PROFILE_LANDING_IN_BOTH | 8.921913 + 1.150 + 4.500 | 14.571913 | -1.828087 |
| COUNT 26 x 0.300 + outer landing + rise | 7.800 + 2.350 + 4.500 | 14.650 | -1.750 |
| **CENTRE PROFILE (the T-417 ST-01 basis)** | 8.921913 + 4.500 | **13.421913** | **-2.978087** |
| OUTER INCLINED | 4.982 + 3.482 + 2.350 + 1.444 | 12.259111 | -4.140889 |
| CENTRE PLAN | 8.921913 | 8.921913 | -7.478087 |

Result (R-T432-4): **no construction reproduces 16.4 exactly (tolerance 0.0005 m, his 5.3 was reproduced to 0 mm),
none even inside his printed one-decimal band (+-0.05 m): UNRESOLVED.** The nearest (+0.096 m) is a sibling-length
reading with no evidence beyond the figure, and is not chosen for being nearest (ERS s.2.4). The T-417 developed
profile, exact on ST-01, leaves 2.978 m of 16.4 on ST-02: the convention is not carried by his sheet to the round stair
(as T-417 already found for his entrance row E1). Consistent with T-417 s.8 (developed plan 8.636 .. 9.385 + 4.50).

### 3a. Second drawing (architectural DXF) and sensitivity

| Piece | ST p.4 (this task) | Arch 1F frame '+5.50' | Arch GF frame '+1.00' |
|---|---|---|---|
| RS-C | 12 risers, step 7.791 deg | same (T-415) | same (T-415) |
| RS-S | 11 risers at 0.300, run 3.000 | 11 at 0.300, run 3.000 | 11 risers, run 2.950: 0.300 x 9 + one 0.250 tread (between the 7th and 8th riser line from the foot, 1.800 .. 2.050 from the first) |
| RS-LD | 1.150 x 1.200 | last RS-S riser and first RS-A riser at the ST p.4 places (1.150 x 1.200) | 1.250 x 1.450 (RS-A first riser 0.250 further up) |
| RS-A | 5 risers, run 1.200 | first two riser lines at the ST p.4 places, 0.300 apart (the rest not re-listed) | 4 risers at 0.300, run 0.900 |
| risers | 28 | 28 on RS-C + RS-S + the first RS-A lines (not fully re-counted) | 27 |

The architectural GF frame is a different drawn layout of the straight part (27 risers, one 0.250 tread, a deeper
landing): a DRAWING CONFLICT for the Lead's register (ST-02 riser count / landing depth; the structural plan, the
architectural 1F frame and the owner's Q-50 A cond count all say 28). It does not change this task's answer: on the GF
frame (riser 4.50 / 27), the 46 constructions give the nearest 16.716 (+0.316 m), none within 0.05: UNRESOLVED either way.
It may matter to the RS-S / RS-LD / RS-A quantities (not in this task's scope: no line moved).

## 4. The -2.476433 m3 restated (acceptance)

| Term | m3 | Cause | Verdict proposal |
|---|---|---|---|
| AREA_BEYOND_DRAWN (his 1.2 x 16.4 = 19.680 m2 vs the drawn 10.835596 m2; 7.370337 m of his length on his width) | **-2.476433** | his length; no stated construction of the drawn stair reproduces it (49 tested) | **UNRESOLVED** (stays whole; never split by a nearest construction, never 0) |

Engine side unchanged: the drawn plan 10.835596 m2 is DRAWING-CONFIRMED on two drawings (T-415); the RS-C waist stays
HELD (5.064265 x t m3, t not printed, AT_LEAST 0.357035). Illustrative only, never a term: if the T-417 basis were his
on ST-02, RISE_IN_LENGTH would be -1.512000 m3 (4.50 x 1.2 x 0.28) and -0.964433 m3 would remain unexplained, so even
then the term would not close. The ST-02 split stays traced -0.253675 / HELD -1.244067 / unexplained -2.476433 m3.

## 5. Hand fixture and tests

`tests/t432_st02_length/test_t432_rules.py` (Villa K432, NOT Alsenan): curved flight (lane 1.0 / 2.0, 90 deg, 8
radial risers) + straight flight (6 risers, run 1.40) + 1.0 x 1.0 corner landing + short flight (3 risers, run 0.56),
riser 0.175: CENTRE / PROFILE 8.291194, OUTER / PROFILE 10.076593 by hand; normal: a row length 8.291194 TRACED to
exactly CENTRE / PROFILE; 9.0 UNRESOLVED and its term kept whole; 8.29 (1.2 mm off) not taken as the nearest.
Adverse: 'rise added twice on a landing' refused three ways (a landing carrying risers; a rise added on a landing; a
stair owning 23 risers for 17 drawn); mixed paths refused; chord as curved plan refused; riser in mm, missing path,
float count, flight without risers refused; two exact constructions AMBIGUOUS; a TRACED split that does not close
refused; walked-down / mirrored order gives identical lengths. `test_t432_alsenan_pins.py`: --check REPRODUCED, piece
risers 12 / 11 / 0 / 5, RS-C centre 3.571913 (and by hand), 49 constructions, none within 0.05, term -2.476433 whole,
no coordinates in the summary.

## 6. Proposals (no candidate line moves)

- Lane I: nothing to wire. The T-406 / T-428 roll-up keeps ST-02 unexplained -2.476433 m3, now with the cause
  'his length 16.4 is no drawn construction (T-432, 49 tested, nearest +0.096 m)'.
- No owner question (ERS 2.7 not met: the drawn quantity does not depend on his basis; only he can say what 16.4
  measures). If the owner ever asks the freelancer: 'ST-02 L 16.4: which path and which pieces?'.

## 7. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | After T-417 traced his ST-01 length as run + rise, the same basis could have been assumed for his ST-02 16.4 m | a convention exact on one row was a candidate for every row of the same sheet | a row length is TRACED only by exactly one stated construction (one path on every piece, every drawn riser once, a landing never with a rise) within the row's printed precision; a convention shown on one row is re-tested per row, never carried; none or two exact -> UNRESOLVED / AMBIGUOUS with the full construction table; every villa, multi-piece and curved stairs | tests/t432_st02_length (rise on a landing refused, mixed paths refused, nearest not chosen, ambiguous, term kept whole) | PROPOSED |

## 8. Not done / uncertain

- His 16.4 stays untraced; constructions outside the 49 (e.g. a length measured on another sheet or another stair) are
  not excluded, only not found.
- The riser 4.50 / 28 is the owner's conditional plan count: every PROFILE / INCLINED figure inherits ASSUMED —
  OWNER-APPROVED (a different count changes the rise only if the total level difference changes: it does not, 4.50).
- The architectural GF-frame difference (s.3a) is recorded, not resolved: which layout governs the straight part is a
  designer / Lead item (the structural plan governs concrete by Q-50 A cond), not an owner question under ERS 2.7.

self-gate: a c d f h PASS (research + tests only; no frozen file, rule or knowledge version; freeze 0; read by handle,
hand figures independent of the module; freelancer quantities only; nothing missing became 0).
