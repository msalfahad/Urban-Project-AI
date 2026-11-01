# T-417 ST-01 straight flights and half landings: element defined by handle, the -2.016 m3 flight-length residual and the +0.1624 m3 landing-area residual traced (research only)

Worker 1 (lane S), 2026-11-01 09:21 .. UTC, branch `agents/task-T-417`. Development villa (Alsenan is one sample; the
method `t417_rules.py` is for every villa). No engine module, candidate line, released cell, rule or knowledge version
is changed; nothing is released. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied; Q-19, Q-46 A, Q-47 A, Q-61 (2), Q-62 A,
R-CONC-OWN-1, R-STAIR-LANE-1; method of T-415 (element by handle, residual split traced / HELD / unexplained).

## 0. Sources (own reads this run; private copies in `.work/private` only)

- Structural: 'ST7757 dxf.dxf' (sha256 9f9d1179, Drive 'Alsenan chalet project'), ST p.4 (GF roof slab plan: MS1) and
  ST p.5 (1F roof slab plan: MS2), read BY HANDLE by `t417_alsenan.py` (asserts type and layer of every handle).
- Second drawing (cross-read): the architectural DXF P7757.dxf (P7757_DXF_COMPRESSED.zip, ab54dd55): level texts
  '+5.50' (5 x) and '+9.70' (3 x) on layer LEVEL, so MS1 rises +1.00 -> +5.50 = 4.50 and MS2 +5.50 -> +9.70 = 4.20;
  no 5300 / 5316 dimension in either DXF (own scan of every DIMENSION; the 1400 dimensions of ST are all on other
  sheets, none on the p.4 / p.5 stair).
- Freelancer: his two ST-01 rows of the concrete + rebar workbook (stairs sheet), read only for his own printed figures:
  flights W 1.2 x L 5.3 x T 0.28 = 1.7808 m3 x 4; landings W 1.2 x L 1.4 x T 0.20 = 0.336 m3 x 3 (asserted against the
  workbook by `--freelancer`). Row text stays private.
- Engine side: merged T-258 r2 ledger (research/agents_t258/LEDGER_T258.csv), reproduced by hand to 2e-6 m3.

```
python3 -I research/agents_t417/t417_alsenan.py --dxf <private>/ST7757_dxf.dxf --freelancer <private>/concrete_rebar.xlsx --write
python3 -I research/agents_t417/t417_alsenan.py --check      # REPRODUCED, no private input
```

## 1. Physical element (ERS s.2.1) and the two methods side by side

ST-01 is the dog-leg main stair in the shaft between the wall faces 284 / 296 (p.4) and 5E3 / 5D4 (p.5): per storey a
lower flight, a half landing across both lanes, an upper flight, 0.10 well (S-OPENING 256 / 25A, 62D / 62E). This task
covers the three VALUED flights MS1-U (+3.50 -> +5.50), MS2-L (+5.50 -> +7.516), MS2-U (+7.684 -> +9.70) and the
half-landing plates; MS1-L / MS1-T / MS1-T-SLAB (C-ST-4, C-ST-3) and MS2-TR stay HELD, untouched.

| Solid | Owner manual method (Q-19, Q-47 A, Q-62 A) | Drawing-derived method (this run) | Status |
|---|---|---|---|
| steps | n x 1/2 r g w | 12 riser lines at 0.300 by handle per flight, lane 1.200 opening edge to wall face; r MS1 4.50 / 27 (Q-46 A section count), MS2 4.20 / 25 (section A-A) | DRAWING-CONFIRMED plan; riser ASSUMED — OWNER-APPROVED (MS1 Q-46 A) |
| waist | T 16 on the INCLINED soffit: run x sec(a) x t x w | same: MS1-U 3.300 x 1.143959 = 3.775064 m; MS2 3.300 x 1.146124 = 3.782209 m | as the riser |
| heads / foot | beam billed through owns it (R-CONC-OWN-1) | MS1-U head in B20, MS2-L foot in B20, MS2-U head in B23 | OWNED_ELSEWHERE (T-189 / T-192) |
| landings | printed plate T 16, plate to its edge | MS1-LD 25B -> 279 x 2F3 -> 296 = 1.20 x 1.20; MS2-LD-E 62F -> 5C0 x 5E2 -> 5D4 = 1.20 x 1.20; MS2-LD-W 632 -> 5C0 x 5E3 -> 5E2 = 1.15 x 1.30 | DRAWING-CONFIRMED |
| edge beam | 'B3 (With Stair)' in the beam line (Q-61 (2) HOLD) | band 279 -> 274 (p.4) and 5C0 -> 5BE (p.5) = 0.200 wide, texts 6B7 / 6B6, 6B9 / 6B8 | OWNED_ELSEWHERE |
| side columns | the column owns its intersection | S-COL.BON on the SAME plan as the lane (T-412 lesson) | see s.3 |

## 2. Component table (acceptance a; ST p.4 / p.5 by handle)

| Flight | Riser lines (foot -> head) | Run m | Rise m | Steps m3 | Waist m3 (inclined m) | Owned elsewhere m3 | Net m3 = ledger | Plate-eq. m3/m2 |
|---|---|---|---|---|---|---|---|---|
| MS1-U | 25B .. 459 (12 drawn) | 3.300 | 2.000 | 0.360000 | 0.724812 (3.775064) | 0.087261 (head B20 0.057261 + Q-62 wedge 0.030000) | 0.997551 = 0.997552 | 0.273942 |
| MS2-L | 646 .. 632 (12 drawn) | 3.300 | 2.016 | 0.362880 | 0.726184 (3.782209) | 0.055619 (foot B20 0.025448 + wedge 0.030171) | 1.033445 = 1.033444 | 0.275016 |
| MS2-U | 62F .. 644 (11 drawn + arrival = p.4 459, asserted one going beyond 644) | 3.300 | 2.016 | 0.362880 | 0.726184 (3.782209) | 0.087691 (head B23 0.057451 + wedge 0.030240) | 1.001373 = 1.001373 | 0.275016 |

| Landing plate | Edges (handles) | m2 | m3 (T 16) | His unit bound (T-398) |
|---|---|---|---|---|
| MS1-LD | 25B -> 279, 2F3 -> 296 | 1.440 | 0.230400 | 1 (his 1.2 x 1.4) |
| MS2-LD-E | 62F -> 5C0, 5E2 -> 5D4 | 1.440 | 0.230400 | 1 (his 1.2 x 1.4) |
| MS2-LD-W | 632 -> 5C0, 5E3 -> 5E2 | 1.495 | 0.239200 | none (his third unit is bound to the held turns, T-398) |

## 3. Ownership: 0 double (acceptance c)

| Neighbour | Contact | Owner | Double? |
|---|---|---|---|
| B20 (GF, band 2C6 / 458, 0.40) | MS1-U head 0.20 inside; MS2-L foot | beam line billed full depth (0.990 / band) | no: deducted from the flights (OWNERSHIP) |
| B23 (1F, 5E1 / 5E4, 0.45) | MS2-U head | beam line (1.11375) | no: deducted |
| B3 'With Stair' 279 -> 274 / 5C0 -> 5BE (0.20) | the landings' north edge | beam line, Q-61 (2) HOLD | no: plates stop at 279 / 5C0 |
| arrival landings ARR-1F / ARR-2F | beyond 459 / 644 | slab panels GF-077 / 1F-062 | no (R-STAIR-LAND-1) |
| column 691 (1F C3, p.5) | 0.050 proud into the MS2-L lane over s 0.95 .. 1.45 m | column; schedule 0.20 x 0.50 vs drawn 0.25 (CONFLICT T-248 / D-16) | HELD range 0 .. 0.006684 m3 kept inside MS2-L until the conflict closes (own integral: 0.05 x (0.5 x 0.16 x 1.146124 + 0.168 x 0.3 x 0.83333) = 0.006684, = the T-258 figure) |
| column 36B (GF, p.4) | 0.050 proud into the MS1-L lane, same s | column | plan 0.025 m2 HELD with MS1-L (no value: MS1-L riser layout in CONFLICT C-ST-4) |
| columns 341 (p.4) / 682 (p.5) | east side of MS1-U / MS2-U | column | FLUSH with wall faces 296 / 5D4: 0 |

## 4. The two residuals split (acceptance b; signs engine - freelancer)

Flights (3 of his 4 units against MS1-U / MS2-L / MS2-U): engine 3.032369 vs his 3 x 1.7808 = 5.3424, contribution
-2.310031 m3 (= T-398) = WIDTH 0 + THICKNESS_BASIS -0.063460 + OWNERSHIP -0.230571 + LENGTH -2.016000.

The LENGTH term: his 5.300 m is the DEVELOPED STEPPED PROFILE of MS1-U, run 3.300 + rise 12 x 4.50 / 27 = 2.000
(treads + riser faces), reproduced to 0 mm with no free parameter. On MS2 the same profile is 3.300 + 2.016 = 5.316;
his row is ONE unit x 4, so the MS1-U length was carried to the MS2 flights.

| Term | m3 | Physical cause | Verdict proposal |
|---|---|---|---|
| RISE_IN_LENGTH MS1-U | -0.672000 | 2.000 m of riser height laid as plan length under a 'slab + steps' thickness (0.28 against the drawn plate-equivalent 0.2739 per PLAN m2): concrete the drawn solid does not contain | ENGINE_RIGHT |
| RISE_IN_LENGTH MS2-L, MS2-U | -0.677376 x 2 | same, rise 2.016 | ENGINE_RIGHT |
| ONE_LENGTH MS2-L, MS2-U | +0.005376 x 2 | his one length 5.300 (MS1-U) against their own profile 5.316 | ENGINE_RIGHT (each flight its own profile) |
| **sum** | **-2.016000** | closes to 1e-6; unexplained **0** | |

Candidates tested and rejected (nearest first, |5.300 - x|): shaft wall 296 / 5D4 length 5.200 (0.100), run + arrival
landing 5.250 (0.050, already rejected by T-398: puts slab panels into the stair), shaft 44448 -> 49848 5.400 (0.100),
B20 outer face -> B3 outer face 4.900, run + landing + B3 4.700, inclined run 3.775 / 3.782. Only run + rise is exact.
Under the structural-plan count 28 (C-ST-4) the MS1-U profile would be 3.300 + 1.929 = 5.229: his 5.3 follows the
section count 27, the same reading as Q-46 A (his source, not design evidence).

Landings (2 of his 3 units, bound as in T-398): contribution +0.028000 = THICKNESS_BASIS -0.134400 (printed T 16 vs
his 0.20, printed nowhere; T-398) + AREA +0.162400, which now splits:

| Term | m3 | Cause | Verdict proposal |
|---|---|---|---|
| OWNERSHIP MS1-LD | -0.038400 | his depth 1.400 = plate 25B -> 279 1.200 + B3 band 279 -> 274 0.200 (beam line) | ENGINE_RIGHT |
| OWNERSHIP MS2-LD-E | -0.038400 | his depth 1.400 = plate 62F -> 5C0 1.200 + B3 band 5C0 -> 5BE 0.200 | ENGINE_RIGHT |
| COUNT MS2-LD-W | +0.239200 | the drawn west half-landing plate 1.15 x 1.30 T 16 has no unit of his in this binding: his 3 one-lane landings (3 x 1.2 x 1.2 + B3) against 4 drawn lane plates (MS1-LD, MS1-T-SLAB held, MS2-LD-W, MS2-LD-E) | ENGINE_RIGHT (the plate is drawn; WHICH of his units is missing is not provable, so the term follows the T-398 binding) |
| **sum** | **+0.162400** | closes; unexplained **0** | |

So the T-406 r3 SD-STAIR 'unexplained' list loses 'ST-01 flight length -2.016' and 'landing area +0.1624'
(-1.8536 m3 net of sign, never offset: the negative term leaves as -2.016 traced, the positive as +0.1624 traced).

## 5. Hand fixture (acceptance d) and tests

`tests/t417_st01_flight/test_t417_rules.py` (Villa D417, NOT Alsenan): flights of 10 risers x 0.17 / 0.16, going 0.28,
lane 1.10, T 0.15, run 2.52: steps 0.261800, waist 0.486437 (sec 1.169881), profile 4.22; row 1.10 x 4.22 x 0.25:
RISE -0.4675 (own), on the 0.16 flight RISE -0.44 + ONE_LENGTH -0.0275; column 0.05 proud over s 0.50 .. 1.00 =
0.006603 (independent midpoint sum). Adverse: waist on the plan or developed length refused; 'slab + steps' on the
developed profile refused; untraced length stays whole (4.30); sibling from another row refused; borrowed riser,
mm as m, float count, missing riser refused; unprinted waist HELD (None, never 0); band owned by the stair refused;
landing depth matching nothing stays AREA untraced; projection beyond the run / across the lane refused; closure gap
refused; sibling order independent. `test_t417_alsenan_pins.py`: --check REPRODUCED, 12 risers x 3.30 x 1.20, terms
close to T-398's -2.310031, length -2.016 all traced, MS1-U profile 5.300, landing +0.1624 closes, column 691 HELD
0 .. 0.006684, no coordinates in the summary.

## 6. V3.0.36 binding and proposals (acceptance e; no candidate line moves)

s.6a Line binding. The V3.0.36 chain (v304_run -> v3036_run) was started on the private copies this run but had only
reached V3.0.1 after 45 min and was stopped before the run lock ran out: **V3.0.36 (`d462203f`) NOT reproduced this
run.** The binding below is the V3.0.29 binding of record (research/agents_t387/BINDING_T387.csv, = the V3.0.21 file by
the T-398 assertion); the T-416 / T-415 verdicts record no structural stair line moved since V3.0.29. Lane I confirms
the six ids and values on `d462203f` before restating the roll-up.

| Line id | Element | State | m3 | Pieces (T-258 r2) | This task |
|---|---|---|---|---|---|
| L-e37d81a8be8e0aa0010c | ST-01 MS1-LD + MS1-U | VALUED | 1.227952 | MS1-LD 0.230400 + MS1-U 0.997552 | reproduced; RISE -0.672, B3 OWNERSHIP -0.0384 |
| L-67e4b0485135f84acc46 | ST-01 MS2-L | VALUED | 1.033445 | MS2-L | reproduced; RISE -0.677376, ONE_LENGTH +0.005376; column 691 HELD 0 .. 0.006684 inside |
| L-bb0e57b1948175a3d5b8 | ST-01 MS2-U | VALUED | 1.001373 | MS2-U | reproduced; RISE -0.677376, ONE_LENGTH +0.005376 |
| L-2416e65f053a14199cfc | ST-01 MS2-LD | VALUED | 0.469600 | MS2-LD-W 0.239200 + MS2-LD-E 0.230400 | reproduced; COUNT +0.2392, B3 OWNERSHIP -0.0384 |
| L-7863355dfcb68a681d2d | ST-01 MS1-L / MS1-T / MS1-T-SLAB | HELD (blank) | - | C-ST-4 / C-ST-3 | untouched (column 36B plan 0.025 m2 named) |
| L-659243ed9fc2831c3ae8 | ST-01 MS2-TR | HELD (blank) | - | C-ST-3 | untouched |
- Lane I (Worker 3, after the Checker): no ST-01 value changes. The T-406 roll-up restates SD-STAIR: 'ST-01 flight
  length -2.016' -> TRACED (RISE_IN_LENGTH -2.026752 + ONE_LENGTH +0.010752, ENGINE_RIGHT) and 'landing area +0.1624'
  -> TRACED (OWNERSHIP B3 -0.076800 + COUNT +0.239200, ENGINE_RIGHT); SD-STAIR unexplained -5.827775 -> -3.974175
  (ST-02 only, T-415 split it further).
- Column 691: the HELD deduction 0 .. 0.006684 stays inside L-67e4b0485135f84acc46 (MS2-L) until the C3 section
  conflict closes; then it is deducted from MS2-L once (never in both).
- No owner question (ERS 2.7 not met: the drawings resolve both terms).

## 7. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | The freelancer's ST-01 flight length 5.30 m (2.00 m beyond the drawn 3.30 m run) stood UNEXPLAINED -2.016 m3 for a day; it is the developed stepped profile (run 3.30 + rise 2.00) under a 'slab + steps' thickness; his landing depth 1.40 = plate 1.20 + the B3 edge beam 0.20 (T-417) | length candidates were searched among plan lengths only; a row length was not tested against the flight's own run + rise, nor a landing depth against plate + edge band | a plate row's length is tested against the drawn run, the inclined length AND the developed profile run + n r of the same flight; a 'slab + steps' thickness is a per-plan-m2 figure and is applied to the plan run only (the profile is a finish / form length); a landing depth is tested against plate + edge band (the band is the beam's); a row of 'count x unit' may carry one flight's length to its siblings (ONE_LENGTH), never a length of another row; every villa, straight flights and landings | tests/t417_st01_flight (developed profile refused as concrete length, sibling from another row refused, untraced stays whole, band owned by the stair refused) | PROPOSED |

## 8. Not done / uncertain

- His basis is INFERRED (exact numeric reproduction with two drawn / section figures); only he can confirm it. The
  verdict does not rest on it: the drawn solid (steps + waist on the inclined soffit) is ENGINE_RIGHT either way, and
  the inference only moves the term from 'unexplained' to 'traced'.
- MS1 riser 4.50 / 27 is Q-46 A (C-ST-4 open: structural plan 28): every MS1-U figure inherits ASSUMED — OWNER-APPROVED.
- His fourth flight unit (MS1-L) and third landing unit (turns) stay HELD (C-ST-3 / C-ST-4), not re-derived here.
- His entrance row (1.8 x 2.8 x 0.28) does NOT follow run + rise (E1: run 1.20 + rise 0.85 = 2.05): the convention is
  not shown to be universal in his sheet; it is shown for ST-01 only. ST-02's 16.4 m is not run + rise either
  (developed plan 8.636 .. 9.385 m + 4.50 = 13.1 .. 13.9 m): T-415's UNRESOLVED stands.
