# T-715 Stair finishes HELD on ARCH_TAKEOFF_V3.0.70 (research, unwired)

Worker 2 (lane A), 2026-11-11. No engine, method, rule-version, knowledge or candidate file changed; released V2.9 + G
untouched. Census of the 85 HELD stair-finish lines by line id: `out/T715_LEDGER.json` / `out/T715_CENSUS.md`, built by
`t715_alsenan.py` from committed, Checker-merged ledgers only (T-184, T-410, T-412, T-415, T-281, T-493, T-508, T-684,
T-690). No drawing was opened this run: the Drive connector returned the DXF zip as binary and
`agent_env.sh decode` refused it ("AGENT_ENV FAIL: base64 decode failed"; known, decode PR #6 open).

## 1. Result (85 lines, V3.0.70)

| Family | Lines | After (proposal) |
|---|---|---|
| FIN.MARBLE.RISER (B7-03) | 13 | 7 MEASURED 10.338610 m2 (MS1-L 1.571667, D1 0.667, MS1-U 1.886, MS2-L 1.9044, MS2-U 1.9044, RS-S 1.653536, RS-A 0.751607); 2 AT_LEAST (MS1-T >= 0.785833, RS-C >= 1.803386); 4 NOT_APPLICABLE (duplicate readings, carrier named) |
| FIN.STAIR.FLIGHT (B7-01 pitch) | 14 | 7 MEASURED 20.234818 lm; 2 BLANK (MS1-T walking line D-67; RS-C curved Q-50); 5 NOT_APPLICABLE |
| FIN.MARBLE.TREAD | 5 | MS1-T 1.3225 m2 MEASURED (tiling, R-T715-2); RS-C BLANK (marble edge / curtail, RFI-S27); 3 NOT_APPLICABLE |
| FIN.STAIR.STEP_LM | 5 | MS1-T >= 5.75 lm; RS-C >= 13.7964 lm; 3 NOT_APPLICABLE |
| FIN.MARBLE.LANDING | 2 | GF bound NOT_APPLICABLE (T-493: no landing in it); 2F bound WIRING_GAP (= T-493 lines 4.865 + 2.9325) |
| FIN.STAIR.SOFFIT | 2 | ST-01 >= 20.423364 m2; ST-02 >= 4.460946 m2 (min of methods O / D, T-281) |
| FIN.STAIR.SKIRTING.ZIGZAG / SLOPED | 44 | 27 CONDITIONAL_ON_FORM (13 pieces x 2 + MS2-TR zigzag 0.168); 8 AT_MOST (no wall established); 4 RANGE (winder corner); 4 NOT_APPLICABLE (T-690); 1 AT_LEAST (MS2-TR sloped >= 0.168) |

Riser and pitch use the section counts (A-A, Q-46 A): 4.50 / 27 and 4.20 / 25, D1 0.70 / 4; ST-02 4.50 / 28 is
ASSUMED - OWNER-APPROVED (Q-50 A cond). Visible riser = r - 0.030 (UP-STAIR-006, owner default). Marble width 1.150 (drawn
front edges, T-412). Skirting form pair: payable total 17.009046 .. 23.300477 lm (sloped .. zigzag, 13 confirmed pieces;
= T-508 17.009049 / 23.300481 within the 6-dp riser rounding of T-410). New line proposed (no candidate line): MS2-TR
closing riser marble 0.1587 m2.

## 2. Findings (ERS s.2)

1. **The winder turn's tread marble is not held by D-67.** The treads of a turn tile its region whatever the subdivision,
   so the turn marble = the region area 1.3225 m2 (T-493 itemised 1.150 x 1.150). D-67 holds only the per-winder split,
   the pitch line and the exact nosing / riser lengths; each nosing runs inner corner -> outer wall, so step lm >= 5 x
   1.150 and riser >= 5 x 1.150 x (r - t).
2. **Duplicate readings.** 1F flights 1 / 4 / 6 (ST-02 seen through the void), 2F flight 1 (MS2-L stacked) and GF-RC flight
   3 (RS-S remainder) carry riser / pitch / tread / step lines whose carrier reading stands in the candidate: NOT_APPLICABLE
   with the carrier named (R-T715-3); the 0 .. X bounds they carried were double counts, not uncertainty.
3. **Skirting form is a payable choice, not a geometry gap.** Both forms are physically measured on 13 walled pieces; the
   owner's ORR-007 answer selects a column with no re-measure. Winder corner walls: zigzag W + N = 3.183333 lm exact for
   any subdivision; sloped pair 2.493380 .. 2.620192 lm.

## 3. Rules proposed (`t715_rules.py`, any villa)

R-T715-1 riser / pitch / step of a straight flight from its section count; R-T715-2 turn region tiling and floors;
R-T715-3 one physical flight, one carrier reading; R-T715-4 skirting physical strip vs payable form (corner bounds).

## 4. Tests (`tests/t715_stair_finishes`)

Villa V715 hand-calculated (r 0.17, going 0.28, width 1.00, t 0.02): riser 1.5 m2, pitch 2.948101, step 9.0; turn floors;
skirting 0.95 / 0.725512; corner 2.68 / 2.112439 .. 2.209297; random tiling fans; sloped <= zigzag on 200 random
stretches; mirror of the corner; adverse: mm, missing count / rise / width (never 0), goings mismatch, visible riser <= 0,
plan-governed turn, no carrier / excluded carrier / self carrier, statement guards and directed rounding. Development villa:
85 by id, none 0, pins, T-508 agreement, ledger reproduction.

## 5. Engine vs freelancer (recorded, never the target)

Freelancer: steps as PIECES (ST-01 63, ST-02 28, ST-03 5, x 1.20 width) and 96 stair-skirting pieces (T-412 / T-508).
Ours: risers ST-01 56 + MS2-TR, ST-02 28, width 1.150. Riser / skirting: RULE_DIFFERENCE on unit (pieces vs m2 / lm);
width ENGINE_RIGHT (1.150 drawn front edge vs 1.20); ST-01 count +7 his UNRESOLVED (T-412). Duplicate readings:
ENGINE_WRONG (double count), corrected here.

## 6. Missing / held

ORR-007 (payable skirting form), D-67 (winder subdivision), D-08 / RFI-S27 (RS-C band, curtail, waist), the GF hidden
opening 33C / 33D sill (MS1-U.E2), MS1-U top CONFLICT (E3b). No owner question: nothing meets ERS s.2.7 (ORR-007 is
already with the owner).

## 7. Lessons-register row proposed (ERS s.7)

| 2026-11-11 | winder turn marble held with the subdivision (D-67) | an area that is the union of the pieces does not depend on how it is cut | tile first: a surface quantity of a region is its area; only per-piece counts / lengths wait on the subdivision (R-T715-2) | tests/t715_stair_finishes (random fans, plan-governed count refused) | proposal |
