# T-556 B5 dry wall plaster height: PLASTER_HEIGHT_METHOD_V1 (research, unwired; wiring is T-558)

Worker 2 (lane A), 2026-11-06, claim 08:40 UTC. Files: `t556_plaster_height.py` (R-T556-1, any villa),
`t556_inputs.py` (line ids, sources; no coordinate, no client name), `t556_alsenan.py` -> `out/T556_PLASTER_HEIGHT.json`
(`--check` rebuilds byte-identical; inputs sha256-pinned), `tests/t556_plaster_height/` (19 tests). No engine module,
method, rule / knowledge version, registry or candidate file changed; no quantity moves in the candidate.

## 1. Physical element and height (ERS s.2 step 1, s.3)

Dry plastered wall face from the FFL to the soffit of the structural slab / roof over it, above any false ceiling
(owner 2026-11-02, Q-72; Q-14: "plaster height = 4.50 - the first floor's build-up - the slab thickness"), net of every
hole (Q-73) and of crossing-beam end sections (beam sides / soffit are CEILING, Q-57). H = storey interval - build-up of
the floor above - slab above:

| Zone | Interval (source) | Build-up above | Slab | H plaster | Status |
|---|---|---|---|---|---|
| GF main, under the 1F slab | 4.50 (A-A +1.00 / +5.50) | 0.05 drawn (T-214, Verifier re-measured) | 0.16 | **4.29** | DRAWING-CONFIRMED |
| 1F, under the 2F slab | 4.20 (+5.50 / +9.70) | 0.05 (T-214) | 0.16 | **3.99** | DRAWING-CONFIRMED |
| any face under a ROOF (annex +4.30, terrace +5.50, roofs +9.70 / +13.90) | as the zone | roof build-up NOT printed (D-39 / DCR-6) | 0.16 | annex 3.79, GF 4.29, 1F / 2F 3.99 at the DRAWN-SECTION SCENARIO (the 0.05 layer the sections draw on the roof bands) | HELD, ESTIMATED scenario, sensitivity -face_roof x 0.01 m2 per cm |

Paint stays at the finished ceiling (G1 3.65 / 3.35 / 3.15); the plaster line is no longer equal to the paint line.

## 2. Per-line table (m2): old (paint height) -> new

| Room line | Old (candidate) | T-552 restated | **New** | roof lm | Cause of the change |
|---|---|---|---|---|---|
| GF-01 dewaneya L-b1529955 | HELD blank | 57.625 .. 75.088 | **61.464 .. 65.254** | 20.127 | H 3.79 scen.; W11 / W12 h 2.20 in full; arch 0 .. 3.79; CB6 2 ends 0.236 |
| GF-04 driver L-1ddc23d5 | HELD blank | 41.115 .. 44.255 | **43.155** | 12.50 | 12.50 x 3.79 - 4.22 |
| GF-15 master bed L-0d93f220 | 56.0131 REL | 68.720 .. 70.874 | **66.529** | 3.231 | 21.537 x 4.29 - (1.76 + 2.20 + W03 5.106 x 4.29) |
| GF-08 open room L-8cecb1d0 | 152.05 .. 178.81 | 183.431 .. 215.505 | **178.221 .. 211.805** | 32.445 | W03 to 4.29; W02 0 .. 27.156 and lift door HELD; B26 / B27 0 .. 2 ends |
| 1F-01 west master L-af9621f4 | 51.415 REL | 61.858 .. 63.628 | **62.573 .. 62.607** | 17.70 | 17.70 x 3.99 - 7.88 - B6 2 ends (0.20 .. 0.25 x 0.34) |
| 1F-04 500 x 365 L-971f0bda | 52.005 REL | 62.271 .. 64.011 | **63.141** | 17.40 | 17.40 x 3.99 - 6.285 |
| 1F-10 380 x 430 L-2ba8077b | 48.94 .. 52.29 | 58.498 .. 63.468 | **58.026 .. 62.050** | 9.558 | arch 0 .. 3.99; B19 0.472 + B6 0.136 .. 0.170 |
| 1F-11 east L-31db3c83 | 61.463 .. 61.718 | 74.531 .. 77.001 | **74.777 .. 80.198** | 22.149 | W17 hole 4.4361 .. 9.858 (T-292, crown 3.00 Q-76 A) |
| 1F-13 living zone L-9b4a7bab | 111.018 .. 114.368 | 134.293 .. 141.588 | **135.626 .. 139.616** | 22.487 | lift door 0 .. 3.99; edge beams not crossing |
| 2F-03 maid L-4ce74fc3 | 57.775 REL | 68.926 .. 70.816 | **69.775** | 18.90 | 18.90 x 3.99 - 5.54 - B2 2 ends 0.096 |
| 2F-01 lobby L-ae0cdd79 | 22.650 .. 26.000 | 27.966 .. 32.216 | **27.360 .. 31.766** | 9.009 | lift door 0 .. 3.99; B15 0 .. 2 ends |
| **11 lines** | 613.33 .. 650.39 (9 valued) | 839.23 .. 918.45 | **840.65 .. 895.90** | | |
| 4 released lines | 217.2081 | 261.775 .. 269.329 | **262.018 .. 262.052** (+44.81 .. +44.84, +20.6 %) | | |

Reproduction: on the 4 released lines face x G1 - the T-292 opening ledger = the candidate value exactly (< 0.0001), so
the inputs are the candidate's. Every line stays HELD: each has some face under a roof (T-128 trace share; GF-15 15 %).

## 3. Corrections to the merged T-552 restatement (Checker please re-measure)

1. **W03 head 4.30 is above the paint height 3.65** (T-144 printed sill / head; T-292): T-552 added face x (H - G1)
   only, keeping W03 capped at 3.65. GF-15 is over-stated by 5.106 x 0.64 = **3.268 m2** at H 4.29 (T-552 / Checker
   68.720 .. 70.874 -> 66.529); GF-08 by 1.625 x 0.64 = 1.040. W03's head is at the soffit within 10 mm (4.30 vs 4.29).
2. **Under a roof the term is the ROOF build-up, not the floor's**: T-552's 0 .. 0.10 bound came from the Q-43 floor
   allowance and has no source for a roof; replaced by the drawn-section scenario + sensitivity (no lower bound printed).
3. At the soffit height a hole of known height is deducted in full whatever its sill (W11 / W12 h 2.20, T-207).
4. Beam ends quantified: closed rooms 2 ends derived (CB6, B6, B19, B2), open rooms 0 .. 2 (B26 / B27, B15).

## 4. Freelancer and verdicts

Gross to gross on the same 11 rooms: engine 1,006.05 m2 at the plaster height vs his 924.205 (+81.85, +8.9 %): his flat
3.60 / 3.40 / 3.50 stop below the soffit (4.29 / 3.99 / 3.79). Verdicts: old candidate height ENGINE_WRONG (T-552);
new method ENGINE_RIGHT on height under Q-72 (his height RULE_DIFFERENCE vs the owner rule); lengths ENGINE_RIGHT
(T-128 r3); roof faces UNRESOLVED (D-39 / DCR-6, designer item, not an owner question: ERS 2.7 not met).

## 5. Rule, lesson, what is missing

R-T556-1 (module docstring). Lesson row proposed (ERS s.7): "11 dry plaster lines equal to their paint lines after the
owner set plaster to the slab underside | plaster and paint shared one height in the code path; the T-552 restatement
then shifted the face only and missed an opening whose head is above the paint line | a layer's height is its own rule;
two layers equal by construction is a defect signal; openings are re-cut at the new height | tests/t556_plaster_height |
OPEN until T-558 wires it". Missing: roof slab tops / roof build-up (D-39 / DCR-6), W02 / lift door / arch heights,
the floor-vs-roof split of each face is the T-128 trace share (not re-measured), beam-end counts in open rooms, B6
span width conflict; no independent drawing re-measure this run (merged ledgers).
