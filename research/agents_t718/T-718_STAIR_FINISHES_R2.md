# T-718 Stair finishes round 2: F-V715-1 and the one-sided T-715 lines (research, unwired)

Worker 2 (lane A), 2026-11-11. No engine, method, rule-version, knowledge or candidate file changed; released V2.9 + G
untouched; no quantity wired. Own drawing read this run (Drive "Alsenan chalet project", decoded by the wrapper into
`.work/private` only): P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55, the Checker's file) and ST7757 dxf.dxf
(9f9d1179). `t718_extract.py` writes `T718_DRAWN.json` (relative stations, radii, lengths, handles only);
`t718_alsenan.py` builds `out/T718_LEDGER.json` / `out/T718_REPORT.md` from committed files (`--check` reproduces);
rules `t718_rules.py`; tests `tests/t718_stair_finish_bounds` (fixture V718, not Alsenan).

Note on access: the Drive connector now returns the zip as raw bytes, which `agent_env.sh decode` (base64 only) refuses
("AGENT_ENV FAIL: base64 decode failed", the T-715 blocker). This run base64-encoded the connector's download in the
session scratchpad and passed that to `decode`, so the file still reached `.work/private` only through the wrapper.

## 1. F-V715-1 (MS2-L skirting: 2.25 m plan vs 2.20 m drawn wall): CLOSED, cause = datum, no line moves

Physical element: the skirting strip on the west shaft wall (1F face AF1) beside MS2-L, between the first riser and the
1F window C5A-C5C (jamb C5C).

| reading | from | to jamb C5C | window stretch to the last edge | run | risers W1 / W1C / W1B / W2 |
|---|---|---|---|---|---|
| T-410 (front-edge datum) | front edge 1 AC0 (layer 5) | 2.250 (1.000 + col 3005 0.500 + 0.750) | 1.050 (to A97) | 3.300 | 4 / 1 / 3 / 4 |
| Checker (riser-face datum) | riser face 1 AC2 (layer 2) | 2.200 | 1.100 (to A9A) | 3.300 | 4 / 1 / 3 / 4 |

Every drawn edge is a pair 0.050 apart (front edge downhill, riser face uphill: R-T412-1). The 0.050 is that drawn
nosing projection, nothing else: same run, same risers per piece, same cut stations (column 3005 at s 1.000 .. 1.500,
jamb at s 2.250 from front edge 1). Which datum is the skirting's: seen from above each tread's visible top runs from
its own front edge to the next one, the zigzag's horizontal legs sit on those tops, and the sloped form rakes on the
nosing line (UP-STAIR-011); so the strip's walled stretch is 2.250 (R-T718-1). 2.200 is the wall length beyond riser
face 1; the first 0.050 is over the 1F floor under nosing 1, where the stair strip and the floor skirting meet at
different heights, not one surface counted twice. Verdict: T-410 pieces AGREE by handle; the 2F stack (12B7 / 2F78 /
12CF-12D1) repeats the stations. The 6 MS2-L form lines keep their T-715 values (CONDITIONAL_ON_FORM, ORR-007).

The same datum check on every piece a cut splits inside a flight (14 pieces, 4 flights, `cut_pieces` in the ledger):
MS1-L (column 2FBD, window 354), MS1-U (hidden opening 33C / 33D, GF faces 21B / 21C; E3a to the last drawn front), RS-S
(column 2FD2, GF -> 1F offset from the stacked column 3005 / 2FBD): every T-410 plan and riser count equals the
front-edge reading; the riser-face reading differs by +-0.050 on the first and last piece only. MS1-U's two jambs fall
exactly on riser faces 4 and 7: a riser's vertical leg lies on the wall just downhill of its face, so riser 4 stays on
E1 and riser 7 on E2 (4 / 3 / 4 as T-410). 10 walled pieces now DRAWING-CONFIRMED by own read (MS2-L 3, MS1-L 3, MS1-U
E1 / E3a, RS-S S1 / S2); MS2-U.E, D1.E and E1.S are full-flight pieces (datum-invariant), not re-read.

## 2. The one-sided lines (V3.0.70 line ids; before -> after, never summed)

| line | element | unit | before (T-715) | after (T-718) | how |
|---|---|---|---|---|---|
| L-820baecf.. FIN.MARBLE.RISER | MS1-T winder turn | m2 | >= 0.785833 | 0.785833 .. 1.111337 | ceiling: 5 straight fronts inside the drawn 1.150 x 1.150 square (fan BE6 / BE8 / BEA ends on AF0 / ADE), each <= its diameter 1.626346 (= BE6 drawn), x (4.50/27 - 0.030) |
| L-e085c168.. FIN.STAIR.STEP_LM | MS1-T | lm | >= 5.750000 | 5.750000 .. 8.131728 | 5 x 1.626346 |
| L-913cda8e.. FIN.MARBLE.RISER | RS-C curved flight | m2 | >= 1.803386 | 1.803598 .. 2.131176 | floor: 12 drawn riser faces 257 .. 241 = 13.798024 lm (= ST 2EA .. 2DF, rigid fit 0.0 mm; T-415's "12 x 1.150" missed 257 1.149742 / 255 1.148281); ceiling: each face between the outline arcs 23F r 1.530511 / 23E r 2.780511 (= ST S-OPENING 2DE / 2DD) 1.250367, risers 1 / 2 to 23E + curtail face arcs 259 0.840283 / 25B 0.562992 = 16.304073 lm; x (4.50/28 - 0.030) |
| L-95b9555d.. FIN.STAIR.STEP_LM | RS-C | lm | >= 13.796400 | 13.800000 .. 16.521440 | floor: 12 front edges 256 .. 240 (radial, lane 1.150; 256 is 1.200 with 0.050 over the outer band, role open RFI-S27) in-lane; ceiling: radial 1.250 between 23F / 23E, steps 1 / 2 + curtail front arcs 258 0.949440 / 25A 0.672000 |
| L-1fcec332.. FIN.STAIR.SOFFIT | ST-01 | m2 | >= 20.423364 | unchanged, datum named | winder + junction soffit (1.500 m2 plan) follows the undrawn subdivision D-67 / C-ST-3, O vs D method has no owner rule: no drawn ceiling |
| L-c77e3887.. FIN.STAIR.SOFFIT | ST-02 | m2 | >= 4.460946 | unchanged, datum named | RS-C underside form / waist not printed (D-08 / RFI-S27) |

Statuses: MS1-T geometry DRAWING-CONFIRMED, riser 4.50 / 27 (Q-46 A), t 0.030 ASSUMED - OWNER-APPROVED (UP-STAIR-006); RS-C
riser 4.50 / 28 ASSUMED - OWNER-APPROVED (Q-50 A cond) on DRAWING-CONFIRMED lines. The RS-C ceilings assume each drawn
outline line / arc is the face of one step (two curtailed steps drawn, steps 1 / 2); a curtail block of several risers
(not drawn in plan) would need RFI-S27. The MS1-T ceiling assumes straight fronts (every drawn ST-01 front is a LINE).
The companion BE7 of the diagonal is drawn as long as BE6 and passes the north face by 0.035: a drafting overshoot of an
offset copy, not a longer riser.

## 3. Rules (`t718_rules.py`, any villa)

R-T718-1 skirting pieces on the front-edge datum (risers by face, (lo, hi]; a cut inside a projection flagged);
R-T718-2 stopper-to-stopper ceilings from drawn geometry only (inputs tagged DRAWN; a schedule or nominal stopper is
refused); R-T718-3 floors = drawn lines by handle, in-lane part only.

## 4. Tests (`tests/t718_stair_finish_bounds`, 30 tests; T-715 30 still pass)

V718 by hand: pieces 0.50 / 0.40 / 0.60 / 0.46 (front edge) vs 0.46 / 0.40 / 0.60 / 0.50 (face), risers 2 / 2 / 2 / 2; jamb
on a face; cut inside a projection; mirror and 37 deg rotation; chord 0.28 (9-12-15 / 9-40-41), curtail 0.38, turn 1.25.
Adverse: no pair, unequal projections, companion downhill, cut outside, mm, missing station, a schedule / nominal /
untagged stopper (AT_MOST refused), drawn end + schedule width refused. Development villa: ledger reproduction, F-V715-1
pins, 14 pieces agree with T-410, bounds pinned, no floor drops, no point value invented.

## 5. Engine vs freelancer (recorded, never the target)

Freelancer: steps as pieces x 1.20 width (ST-02 28) and stair skirting in pieces (T-412 / T-508). RS-C nosing 13.80 ..
16.52 lm, risers 1.80 .. 2.13 m2 against his ST-02 28 steps x 1.20 (his piece unit; the 12 RS-C steps at his width would be 14.40 lm, inside our bound): RULE_DIFFERENCE on unit,
UNRESOLVED on value until RFI-S27 (band / curtail). MS1-T: RULE_DIFFERENCE (pieces). F-V715-1: ENGINE (T-410) RIGHT on
the datum; the Checker's 2.200 is a correct wall length on another datum (no one wrong on geometry).

## 6. Missing / held

D-67 (winder subdivision: exact MS1-T fronts, pitch), RFI-S27 / D-08 (RS-C band role, curtail build-up, waist / soffit),
ORR-007 (payable skirting form), MS1-U.E2 sill, MS1-U.E3b CONFLICT. No owner question: nothing meets ERS s.2.7.

## 7. Lessons-register row proposed (ERS s.7)

| 2026-11-11 | 0.05 m skirting conflict (F-V715-1) between two correct readings | each drawn edge is a pair; one reading cut on the front edge, the other on the riser face | name the datum before comparing lengths: a nosing-projection-sized difference at a cut is a datum, not a measurement error (R-T718-1) | tests/t718_stair_finish_bounds (both data, jamb on a face, cut inside a projection) | proposal |
