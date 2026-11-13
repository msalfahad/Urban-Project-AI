# T-719 void register: missing family B2-05 voids / double height / shafts (lane A, research, unwired)

Worker 2, 2026-11-11. Candidate of record ARCH_TAKEOFF_V3.0.71 (T-704 line index). A register and a deduction check
with own drawing reads, not a verification; nothing wired or released; V2.9 + route G unchanged; no engine, rule /
knowledge version, registry or candidate file touched. Files: `t719_extract.py` (own DXF read by handle + the released
engine's split of the same faces -> `T719_DRAWN.json`, lengths / areas / handles only), `t719_rules.py` (R-T719-1 .. -5,
every villa), `t719_alsenan.py` (builder, inputs sha256-pinned, `--check`), `out/T719_VOIDS.{json,md}`,
`tests/t719_void_register` (16 tests). Drawing read this run: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip
(P7757.dxf sha ab54dd55, decoded by the wrapper into `.work/private` only) and a V2.9 run on it kept there.

## Physical element (ERS 2.1)

A void is an opening through a floor slab: light well / double height, stair well, lift shaft, dome / skylight opening.
It belongs to the plan of the slab it pierces (upper storey: no floor finish inside it); the storey below is double
height there (no ceiling at its own level); the ceiling over the volume is carried once, at the top (R-T719-1 .. -3).

## Register (7 entries; numbers in out/T719_VOIDS.md)

| void | outline | floors | floor of the pierced storey | ceiling below / top |
|---|---|---|---|---|
| V-01 ST-02 light well | 7.02 x 4.00 - 1.15 x 1.60 = **26.240** (walls AF7 / AEC, slab edges AF5 / D24 / B75 / B74); X-rect 5.82 x 2.75 = 16.005 + corner landing +4.696 1.3225 + flights / pocket / 0.05 strips 8.9125 | pierces 1F, GF double height | 1F living: face in outline 26.1725 (0.0675 in the wall line); deducted 16.005 (VOID) + 6.771668 (ST-02 flights seen) + 3.453 (T-116 residue) = 26.229668: **-0.057168 DEDUCTED_TWICE** | GF: 14.9434 + 9.8536 + GF-159 1.3756 = 26.1726 vs 26.1725 ONCE (GF-159 bound by sum, position not read); top: decor group 51.0496 holds it **and** the blank V2.9 line 'ceiling over void' names 16.005 again: DOUBLE_COUNT_RISK |
| V-02 oval beside the 1F east bay | four layer-5 arcs BCF / 2F1C / C7A / 2F1B, **3.824** (1.85 x 2.70; T-071 3.820) | 1F slab projection, GF pool court | meets no internal face on 1F or GF: **EXTERIOR** | no internal ceiling; slab top / soffit / edge lines absent from the candidate (named) |
| V-03 lift shaft | 1.80 x 1.80 = **3.240** each, stacked GF / 1F / 2F | 1F, 2F slabs | own SHAFT space every plan: ONCE (excluded) | none; lining / top need a specification (named) |
| V-04 ST-01 dog-leg shaft | stair box 2.50 x 4.29 = **10.725** at 1F; well between flights 0.20 x 3.40 (1F A8D / A8E, 2F 1356 .. 1359, open balustrade gap, T-709) | 1F, 2F slabs | 1F: treads 8.337 + landing 4.865 + well 2.142 (T-116 / T-122, cited) | 1F stair zone 10.725 = box: ONCE; GF / 2F stairwell ceilings one HELD line each |
| V-05 west dome opening | circle 12EB r 2.2111 = **15.359** | 1F roof slab | roof (not a finished floor) | 1F-RB72F22 19.050 - 11.5808 = 7.4692, R8BDA49 5.0225 - 1.4227, R48AA46 5.0225 - 1.2410: all ONCE; top: one dome-soffit line (HELD) |
| V-06 east dome opening | circle 2F33 r 2.2111 = **15.359**; overlaps the light well 0.108 | 1F roof slab | roof | R3CFCFD -0.3418, R48CDA5 -0.4472 ONCE; living 14.0359 (own circle 14.066: +0.030 named residual, arc pieces vs circle) |
| V-07 third dome | circle 1300 r 2.205 drawn 'above' on 2F; no opening line, no structural drawing | top roof | NOT A DRAWN VOID (S0): **HELD** by scenario, outline None | S1 open skylight would cut 2F maid 11.066 / bath 1.624 / shaft 1.619 ceilings: never applied here |

## Findings (no quantity moved)

1. **V-01 1F living porcelain L-b06400d4 (33.411036): ENGINE_WRONG candidate, 0.057 m2 deducted twice.** On the 1F plan
   the radial flight F1 (box to 2.87) and the straight flight F4 (read from 2.82, line B43) overlap 1.15 x 0.05 =
   0.057438 m2; arch_floor.split_face sums the footprints (STAIR_BELOW_SEEN 6.771668), while the T-116 residue 3.453
   equals the geometric remainder (own 3.45327). Sum 26.229668 vs face 26.1725: -0.057168; after the overlap
   +0.00027 (inside tolerance). Corrected: 33.468204 (+0.17 %). On the GF plan F2 starts at 2.87: no overlap there.
2. **V-01 ceiling top: DOUBLE_COUNT_RISK.** L-35341ff2 '1F-R78C367:ceiling over void' (blank, HELD) names 16.005 m2 the
   decor group L-43bf1f86 (51.0496 = 75.983 - stair zone 10.725 - 0.1725 - east dome 14.0359) already carries. It must
   stay blank / EXCLUDED; valuing it adds 16.005 m2 twice.
3. Every other void is deducted once by a named line or is outside the internal faces (V-02 EXTERIOR).
4. T-709 band cross-check: the double-height walls of V-01 are west AF7 4.00 and south AEC 7.02, the same runs R-T709-1
   uses (E3E 4000 / D7B 7020); the other four edges are slab edges (railing / edge, no wall).

## Who is right / missing

- V-01 floor: ENGINE_WRONG (0.057 m2) with the hand reason above; freelancer not compared (no void row).
- Missing (named, not valued): ST-02 corner landing finish (1.3225 at +4.696: no FIN.MARBLE.LANDING line for ST-02),
  V-02 exterior slab top / soffit / edge, lift shaft lining and top, V-07 by scenario (S0 / S1, Q-29 / T-185).
- Uncertain: GF-159 lies in the well by sum only; the dome residual 0.030 m2 (arc pieces vs circle).

## Rule and lessons row (ERS s.7, proposed)

R-T719-1 .. -5 (t719_rules.py). Lessons row: "Light well 1F floor deducted 26.2297 inside a 26.1725 opening (T-719):
two flight footprints summed where they overlap on the upper plan -> deduct the union of the named pieces inside the
void outline, never the sum (any villa); test `test_adverse_deducted_twice_overlapping_footprints`."
