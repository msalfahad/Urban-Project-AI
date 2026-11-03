# T-481: FIN.SKIRTING remainder after V3.0.44 (development villa; method every villa)

Worker 2 (lane A), 2026-11-03. Research only: `research/agents_t481/*`, `tests/t481_skirting_remainder/*`; no engine,
rule, knowledge, method, registry or candidate file touched; no candidate or released quantity moves (integration rides
stream F behind T-443). ERS 2026-10-22 applied: s.2.1 element first, s.2.2 evidence, s.2.4 reconciliation in lm, s.4 rule
+ test, s.7 lesson. Rules: UP-SKIRT-001 1.4.0, R-T422-1 / T-296 threshold rule (skirting continues under a sill above
the floor), UP-CER-003 (doors deducted), R-T441-2 / R-T410-1 (stations, one face one owner), UP-QTY-STATUS-001, Q-72.
Drawings named by Drive folder and title only; no coordinate, image, note text or client data in any committed file.

## 0. What was read (this run, Drive folder "Alsenan chalet project", decoded into `.work/private` only)

| Source | Used for |
|---|---|
| P7757_DXF_COMPRESSED.zip -> P7757.dxf (current issue), by handle | NW elevation (W17 jambs, level-marker blocks, printed chain), 1F plan (dressing cell, ST-01 shaft faces, nosing / riser lines) |
| architectural DWF (vector), read with research/agents_t201/w2d_reader.py | SECTION B-B both ends (W11 street wall, W02 saloon), its level markers; FENCE ELEVATION / PLAN; GF plan B-B cut line and W11 / W12 / W02 glazing lines; 1F dressing (earlier-issue cross-check) |
| Alsenan_Architectural_P7757_Pages_11-12 p.11 (current issue scan) | SECTION B-B: W11 sill and W02 base checked against the current issue |
| merged T-201 / T-207 / T-238 / T-144 / T-296 / T-410 / T-422 / T-240 / T-250 ledgers | cited by row, not re-derived unless stated |

## 1. Window sills (acceptance 1): physical element and readings

Under a window the skirting exists only where wall stands below the opening (R-T481-1: masonry opening base above the
room FFL > 0.02 m; a frame / threshold rail is not wall).

| Window | Room / line | Evidence (own read) | Sill above FFL | Decision | Status |
|---|---|---|---|---|---|
| W11 | GF-01 dewaneya L-d3241491 | DWF SECTION B-B, street-wall cut 0.201 thick: frame base 999.1 mm and head 3200.5 mm above the printed ±0.00 apex; printed +0.30 floor marker 300.6 mm above it (same view) -> base +1.00, height 2.20 (= W11's 2.201 on the fence elevation). Current issue p.11: sill 0.72 above the +0.30 floor (scan profile over the printed 400, check +-0.03). Fence elevation (no level printed): base 0.849 above its ground line -> 0.55 (ground ±0.00) or 0.70 (ground +0.15) | **0.70** (views 0.55 .. 0.70, spread 0.15) | SKIRTED | DRAWING-CONFIRMED |
| W12 | same | identical outline to W11 on the fence elevation (top / bottom lines to 1 mm, T-207); B-B does not cut W12 | 0.70 | SKIRTED | DRAWING-CONFIRMED (bound to W11) |
| W02 | GF open plan L-71e2e002 (range L-e7dcdc69) | DWF SECTION B-B sea end: frame base on the +1.00 floor line (printed '100' from ±0.00, marker +1.00); current issue p.11: glazing starts on the floor line (T-201 overlay 0.025) | **0.00** | NOT_SKIRTED (floor glazing) | DRAWING-CONFIRMED; count / pier D-53 contingent |
| W17 | 1F-11 L-309f118f (range L-fbba0e0d) | P7757.dxf NW elevation: jamb lines start on the +5.50 marker block; printed chain from the +1.00 marker 4300 / 200 / 3050.5: 1.00 + 4.30 + 0.20 = +5.50; 1F plan prints only +5.50; frame rail 0.050 above (frame member; W15 / W16 0.106, T-238 floor glazing) | **0.00** | NOT_SKIRTED (floor glazing) | DRAWING-CONFIRMED |

Binding notes. (a) The GF plan B-B cut line passes 0.078 m outside W11's north jamb (inside the 0.81 pier), yet the section
draws an opening in the cut wall with W11's height: bound to W11 by height and wall, recorded. (b) The cut crosses W02's
four continuous glazing lines inside the 6.232 m span; I read it 1.215 m from the glazing end where T-201 recorded 0.205 m:
immaterial here (one uniform plan symbol, sill at the floor at the cut), named for the Checker. (c) W11's absolute sill
differs by 0.15 between views only if the fence ground line is ±0.00: it moves the masonry under the sill (T-207 HELD),
not the skirting decision (both > 0.02). (d) W02 renders show a pier (D-53): if the designer confirms one, its room face
takes skirting under R-T481-2; no width is drawn, so nothing is valued.

## 2. 1F dressing (acceptance 2): cell walk on P7757.dxf

Enclosed dry cell 1.650 x 1.800 (engine room 1F-RFFE7AF, T-240 area 2.970 VERIFIED). Layer 1 by handle:

| Side | Stretches | Opening (deducted by id) | Skirting lm |
|---|---|---|---|
| W 1.800 | B03 0.8908 + B04 0.1092 | door D315 (BEE) 0.800 | 1.000 |
| E 1.800 | B00 1.800 (wardrobe box B0A / BE3, layer 5, in front: not a deduction) | - | 1.800 |
| N 1.650 | B20 1.650 | - | 1.650 |
| S 1.650 | AD4 0.500 + AD5 0.150 | arch A-1F-01 (arch120 BEC) 1.000 | 0.650 |

**5.100 lm DRAWING-CONFIRMED** = gross 6.900 (the engine boundary 6.90) - 0.800 - 1.000. Earlier-issue DWF walk 5.1006
(AGREES, 0.0006). Joinery-backed 2.800 lm reported beside, not deducted (WALL_CONTACT_PATH_POLICY V1 / V2: furniture,
wardrobes and joinery are never site boundaries; no owner rule says otherwise). No jamb returns (UP-CER-003 practice).

## 3. Stair-shaft ownership (acceptance 3): R-T481-3 on the 1F ST-01 shaft faces

The room line L-ba3599ec (1F living + ST-1F) carries the shaft faces (10.232 lm, T-250 walk) inside its certain net and
W13 / W25 (2.200) in its range. On the 1F plan the whole shaft between the walls is flights and intermediate landings:
MS2-L rises north from its first nosing AC0, MS1-U arrives southward to its top nosing ABE, MS2-LD (+7.516) lies over the
north end. Face by face (SHAFT_FACES_T481.csv, face-local s from the north inner corner):

| Face | B7 owner (T-410 stretch) | Room (1F floor +5.50) |
|---|---|---|
| east B16 5.200 | 0 .. 1.200 MS2-LD.E (+7.516) and 0.850 .. 4.150 MS1-U.E1..E3: **4.150** | 4.150 .. 5.200: **1.050** (incl. 2FF3 flush) |
| west AF0 / W13 / AF1 4.625 | AF0 1.050 MS2-LD.W; W13 1.050 .. 2.250 in MS2-L.W2 (HELD there); AF1 2.250 .. 4.500 MS2-L.W1B / W1C / W1 2.250; 3005 returns 0.100: **3.400** | 4.500 .. 4.625: **0.125** |
| north ADE / W25 / ADD 2.500 | ADE 1.400 + ADD 0.100 MS2-LD.N (W25 in it, HELD there): **1.500** | 0 |

B7-owned 9.050 lm + room 1.175 lm = 10.225 vs the T-250 walk 10.232: residual 0.007 lm (walk sampling at the polygon
ends), named. Stations are T-410's (nosings), so no point has two owners (checked in code: a floor zone overlapping a
same-level flight is refused; stacked flights of other levels do not conflict).

## 4. Before / after (V3.0.44 -> proposal; LINES_T481.csv)

| Line | Before | After | Change |
|---|---|---|---|
| L-d3241491 GF-01 (W11 / W12) | 14.218037 + range 0 .. 3.909839 | **18.127876**, range NOT_APPLICABLE | +3.909839 certain (closes on gross 20.127876 - doors 2.000) |
| L-71e2e002 range L-e7dcdc69 (W02) | 0 .. 6.331578 | NOT_APPLICABLE (floor glazing) | -6.331578 held |
| L-309f118f 1F-11 range L-fbba0e0d (W17) | 0 .. 3.289498 | NOT_APPLICABLE (floor glazing); net 17.161172 unchanged | -3.289498 held |
| L-4a85470b 1F dressing | BLOCKED_RFI blank | **5.100** | +5.100 certain |
| L-ba3599ec range L-079bc766 (W13 / W25) | 0 .. 2.200 | NOT_APPLICABLE to room skirting (B7 MS2-L.W2 / MS2-LD.N) | -2.200 held |
| L-ba3599ec net (shaft faces) | 41.435360 | 32.385360 **after the integrator binds the 9.050 lm B7 faces to the engine edges** | -9.050 at binding |

FIN.SKIRTING: certain 189.818752 -> **198.828591 lm** (+9.009839, +4.75 %); held high 15.730915 -> **0** (every T-246
UNRESOLVED window resolved); blocked lines 3 -> 2. After the shaft binding: 189.778591 lm (the 9.050 lm then counted once,
in B7-07 / B7-08 lines, not in B3-06).

## 5. Engine vs freelancer; verdict proposals

Freelancer 282.85 lm = 12 dry-room gross perimeters, no door deduction (T-106). Candidate 189.82 -> 198.83 (-32.9 % ->
-29.7 %); after the shaft binding 189.78 (-32.9 %): RULE_DIFFERENCE (UP-CER-003 doors / passages deducted; his
perimeters also run along the stair shaft), never the target, no accuracy figure.
- W11 / W12: ENGINE_RIGHT now (sill 0.70 above the +0.30 floor; hand: 20.128 - 2 x 1.000 = 18.128).
- W02, W17: ENGINE_RIGHT now (floor glazing; hand W17: 1.00 + 4.30 + 0.20 = 5.50 = FFL).
- Dressing: ENGINE_OMISSION closed (hand 6.90 - 0.80 - 1.00 = 5.10; he has no dressing row).
- Shaft faces: RULE_DIFFERENCE vs his room perimeter (one face one owner: B7 along flights).

## 6. Code, tests, regression

- research/agents_t481/t481_skirting_rules.py: R-T481-1 (sill_above_ffl / window_base / decide / line_effect), R-T481-2
  (walk_cell), R-T481-3 (shaft_owners). t481_alsenan.py: readings + ledger, `--check` byte-identical.
- tests/t481_skirting_remainder: 23 tests. Hand villa K481 (not Alsenan): one high sill 9.90 -> 11.10, one floor glazing
  (range 4.20 -> 3.00 -> 1.00), one sill not printed HELD; cell 7.00 - 1.60 = 5.40 (mirrored); shaft 3.60 / 1.40.
  Adverse: split views HELD, no datum, missing FFL, millimetres, base below the floor, release not closing, edge beyond
  range, release without net, side not closing, joinery as boundary, opening twice, two owners same level, uncovered
  wall UNKNOWN, window not wall, stacked flights counted once.

## 7. Held / missing; lesson

Held: the shaft binding (needs the engine edges of L-ba3599ec by handle at integration); D-53 pier (W02); W25 / W13 in
B7 (T-410 stretches HELD on sill vs flight); the 0.007 lm walk residual. Checker: re-measure W11 (B-B) and W17 (NW
chain) yourself (acceptance asks 2 sills).

Proposed ERS s.7 row: | 2026-11-03 | a window "sill not established" for two weeks was established by a SECTION cut
(W11) and a printed chain (W17) nobody had bound to the skirting question; the hold carried an unrelated cause (W17's
archivolt height) | holds inherit the first cause written | before carrying a sill HELD, look for the opening in every
section and elevation chain and record the decision per view; a height hold is not a sill hold | tests/t481 decide() |
research |
