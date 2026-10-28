# T-311: PARAPETS AND PLINTH as physical elements, every component tied to ONE owner trade and a candidate line (development villa; every villa by R-T311-1 .. 4)

Worker 1 (lane S), claim 2026-10-28 19:24 UTC (re-claim of the 2026-10-26 claim that left no branch), run unknown.
Research only: no engine module, rule or knowledge file, candidate line, released line or V2.9 cell changed; released
default stays V2.9 + route G; nothing released. ERS read and applied: s.2.1 (the physical element first, split into
components), s.2.2 (the printed alternatives and the owner method side by side), s.2.4 (closure in units, residuals
named), s.2.7 (no owner question: the open item is a designer detail already under owner Q-65 C), s.3 (one element,
several geometries; build before deduct; a notation's meaning is not extended), s.4 (rules + tests), s.7 (lesson row).

## 1. Run and identity

Drive 'Alsenan chalet project' (read-only; private copies only in .work/private): ST7757.pdf (p.13, p.14 at 400 dpi),
'ST7757 dxf.dxf' (`9f9d1179`), p7757_arch_sheet10.pdf (section A-A) and Alsenan_Architectural_P7757_Pages_11-12.pdf
p.11 (section B-B) at 300 dpi, P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) for the own candidate run (Python 3.11,
`research/agents_t167/v304_run.py` then `research/agents_t255/v3019_run.py`): **V3_0_19_BOQ_LINES json `b35475bf` / csv
`ef63b73b` = the candidate of record byte for byte** (T-255), 3,705 lines; extract `CANDIDATE_V3019_T311.json` (445
lines of the concrete, blockwork, WP roof, facade / finish and plaster families, and every line naming a parapet,
plinth, upstand or coping). Two concrete lines name an 'upstand': the water-tank columns C2 / C3 held on D-44 (B15
upstand / downstand), blank, not parapet carriers; the two STR.REBAR 'upstand' lines are the B20 / B23 stair upstands
(D-26). No concrete, blockwork or formwork line names a parapet. Builder
`t311_alsenan.py --write / --check`; rules `parapet_plinth.py`; tests `tests/t311_parapet_plinth` (22).

## 2. What the drawings say each parapet IS (the question no register row answered)

| Source (read this run) | What it draws | Keyed to an Alsenan run? |
|---|---|---|
| ST p.14 P1 'TYPICAL DETAIL OF PARAPET SECTION.' | edge beam 'AS PER SCH.' **to the slab top**; an RC upstand '30' above the slab top with its own cage ('MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING'); 'Brick Wall'; an RC cap with a moulded projection, heights 'AS PER ARC.' (cap 5 d12/m, 5 d10/m) | no |
| ST p.14 P2 'DETAIL OF PARAPET SECTION.' | RC parapet 130 high, 30 x 10 cap, stepped 10 + 10 onto a 60 x 40 beam (6 d12/m, 6 d10/m, 5 d10/m) | no (130 = the printed 1F height NE / SW: a coincidence of numbers, not a callout) |
| ST p.14 P3 'DETAIL OF PARAPET SECTION.' | tapered RC parapet 105 high, 15 + 15 at the base, 15 at the top (6 d12/m, 5 d10/m) | no |
| ST slab plans (DXF, three places) | 'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING' ('casting': the parapet is cast work) | - |
| P7757 sections A-A and B-B | every parapet (annex +4.30, GF +5.50, 1F +9.70, 2F +13.90) is cut in the **same hatch as the slab and the edge beams**, continuous with them; the block walls below are cut **unhatched**; plain top, the drawn wall thickness | the sections are the architectural detail the plans refer to, but they show no brick zone and no cap |

So the parapets are cast concrete on the architect's sections, while the structural 'typical' is brick on an RC
upstand. Two authoritative documents differ and none keys a type to a run: the **material split is HELD** (owner Q-65 C
already says: request material and construction details from the designer; provisional alternatives may be shown;
classification HELD). No owner question (ERS 2.7: a designer detail, already answered as HOLD).

What every printed alternative shares, and so what is NOT open: **at least 0.30 m of RC above the structural slab
top** (P1's upstand) and **no parapet concrete inside the beam lines** (P1 dimensions the scheduled depth to the slab
top; the engine's beam lines take the schedule depth: R-T311-2). P2 / P3 profiles (0.30 cap, 0.30 tapered base)
contradict the drawn 0.20 thickness of every run, so only their 'all RC' fact enters the range.

The solid's height above the structural slab top = printed height above the finished roof + b_edge, the build-up depth
at the edge, which is HELD (D-39, T-214 / T-221: roof structural tops held). Every quantity below is the printed part;
b_edge adds a named HELD increment, never a default.

## 3. Run-by-run ledger (PARAPET_RUN_LEDGER_T311.csv; 24 runs = T-172's per-side table)

| Chain (roof / top) | Centreline m | Solid m3 (above finish) | Concrete m3 (P1 upstand .. all RC) | Blockwork m2 (all RC .. P1) | Formwork m2 | Outer face m2 | Inner face m2 | Top m2 |
|---|---|---|---|---|---|---|---|---|
| Annex +4.30 / +4.80 | 28.885 | 2.889 | 1.733 .. 2.889 | 0 .. 5.777 | 17.331 .. 28.885 | 14.671 (IN_LINE GF) | 14.214 | 5.777 |
| GF house +5.50 / +6.00 | 28.370 | 2.837 | 1.702 .. 2.837 | 0 .. 5.674 | 17.022 .. 28.370 | 14.385 NO_LINE | 13.985 | 5.674 |
| 1F +9.70 / +11.00 (printed NE / SW) | 49.676 | 10.600 .. 11.648 | 2.981 .. 11.648 | 0 .. 43.335 | 29.806 .. 116.477 | 53.914 .. 59.292 NO_LINE | 52.082 .. 57.185 | 9.935 |
| 2F +13.90 / +14.40 | 29.050 | 2.708 | 1.625 .. 2.708 | 0 .. 5.810 | 17.430 .. 29.050 | 14.900 (IN_LINE 2F) | 14.150 | 5.415 |
| **Total** | **135.981** | **19.033 .. 20.081** | **8.040 .. 20.081** | **0 .. 60.596** | **81.589 .. 202.782** | 97.870 .. 103.248 | **94.431 .. 99.534** | **26.801** |

HELD increments per metre of b_edge: concrete / solid +26.801 m3, blockwork +135.981 m2. 1F heights HELD on NE-1 / SW-1
(1.0996 .. 1.2996) and SW-2 (0.385 .. 1.60), as T-172.

## 4. Plinth, segment by segment (PLINTH_SEGMENT_LEDGER_T311.csv; 29 = T-305's plinth bands)

Physical element: the exterior face from the outer finished ground (natural +-0.00 on the street / sea edges, the
+0.15 court paving top elsewhere, R-GB-DATUM-1) to the F.F.L. Substrate from the floor datum chain: the main-house
exterior ground beam (soffit +-0.00 by D-35, top +0.95 = 'Ground Floor slab level', p.13 / T-214) is exposed over its
whole outer face; above it the GF wall starts at the structural slab top, so the 0.05 m course +0.95 -> +1.00 is wall.
Annex: beam top +0.25 (T-214), F.F.L. +0.30; its depth is a CONFLICT (T-253) but the exposed face is concrete either way.

| Zone | Length m | Face m2 | Concrete substrate m2 | Wall course m2 | Status |
|---|---|---|---|---|---|
| house | 71.645 | 63.927 .. 64.988 | 60.345 .. 61.406 | 3.582 | pool-court bottom HELD (T-305) |
| annex | 29.542 | 7.056 | 5.579 | 1.477 | beam depth CONFLICT (concrete in its line), face DRAWING-CONFIRMED |
| passage P-1 | 4.700 | 0.705 | HELD | HELD | no beam top read for the passage face |
| **Total** | **105.887** | **71.689 .. 72.750** (= T-305 66.736 + 4.952 .. 6.013, residual 0.000) | 65.924 .. 66.985 | 5.059 | |

## 5. Every component once: trade and candidate line (COMPONENT_OWNER_T311.csv; 46 rows, DOUBLE 0)

| Component | Trade | Candidate line | State |
|---|---|---|---|
| parapet RC part (all chains) 8.040 .. 20.081 m3 + HELD | CONCRETE | none (no STR.CONC line names a parapet or upstand; beam lines stop at the slab top) | **NO_LINE: MISSING** |
| parapet masonry part 0 .. 60.596 m2 + HELD | BLOCKWORK | none (the run's wall network holds no parapet: every wall bounds a room) | NO_LINE (HELD material) |
| parapet formwork 81.589 .. 202.782 m2 | FORMWORK | none (no formwork family; T-199 queued) | NO_LINE |
| parapet reinforcement | REBAR | none; HELD (type unkeyed; no rebar code change before an approved stage) | NO_LINE |
| outer face, annex 14.671 / 2F 14.900 m2 | PLASTER_EXT | L-b05f70c92405dbcfbe62 (GF) / L-d52c4f763b19aedf8b8b (2F), both BLOCKED_RFI, no quantity | IN_LINE |
| outer face, GF 14.385 / 1F 53.914 .. 59.292 m2 | PLASTER_EXT | none | NO_LINE (T-305) |
| inner faces 94.431 .. 99.534 m2 | PLASTER_PARAPET_INNER | none | NO_LINE |
| tops 26.801 m2 | COPING_TOP | none (cap profile HELD) | NO_LINE |
| membrane upturn on the inner face, annex 28.428 / GF 27.970 / 1F 48.784 / 2F 28.300 m.l x 0.20 | WATERPROOFING | L-d4c73babd2a275c28929 (AT220, annex roof) / L-994b88140f2ea50f1b31 (AT216, GF terrace) / L-5ce5ba49792e8f9d1f6f (AT379, 1F roof) / L-aac1f35e08f85b643692 (ROOF-TOP, BLOCKED_RFI: 2F run HELD) | IN_LINE (each line's m.l contains the runs: CLOSURE) |
| top arrises 271.962 m.l | CORNERS | none (own m.l line, T-172 / T-305) | NO_LINE |
| plinth plaster face 71.689 .. 72.750 m2 | PLASTER_EXT | none (geometry carrier L-c0e9a4c62171de1f369b BLOCKED only) | NO_LINE |
| plinth concrete substrate 65.924 .. 66.985 m2 (face, no m3) | CONCRETE | STR.CONC.GROUND_BEAM lines (the beam's m3; the plinth adds no m3) | OTHER_LINE |
| plinth wall course 5.059 m2 | BLOCKWORK | L-4165954ce4871eda30cc (GF t=0.20 MAS.BLOCK; height from the slab top) | OTHER_LINE (never again) |
| annex-roof band 4.080 m2 | PLASTER_EXT | none | NO_LINE (T-305) |
| its foot upturn 3.400 m.l | WATERPROOFING | L-d4c73babd2a275c28929 | IN_LINE |

Roof identification for the upturn lines: AT216 32.721 m2 = the GF house terrace strip (T-221 TERRACE-550 32.387),
AT220 55.559 m2 = the annex roof (T-221 ROOF-430 52.848), AT379 = the 1F terraces; Checker please confirm by outline.

## 6. Closure (CLOSURE_T311.csv)

Parapet outer faces GF + 1F 68.298 .. 73.676 against T-305's NO_LINE bands 68.298 .. 73.676 (residual +0.0006: T-305's
4-decimal rows); annex 14.671 and 2F 14.900 against T-305's IN_LINE bands (+0.00005: T-172 4-decimal run lengths, 0);
plinth 71.689 .. 72.750 (0.000); substrate split closes (0.000); inner faces, tops and arrises against T-305 ITEMS
(<= 0.0007, 3-decimal items). Max residual 0.0007, every one named.

## 7. Against the freelancer (comparison only)

| His row | His m2 | Drawing | Cause |
|---|---|---|---|
| BLK 172 'الدروه' 66.00 x 1.00 | 66.00 | annex + GF centreline 57.255 m, 0.50 above the finished roof; block 0 .. 11.451 m2 | his length +8.745 m; height 1.00 vs 0.50 + b_edge; all block vs >= 0.30 RC in every alternative |
| BLK 177 'الدروه' 42.85 x 1.80 | 77.13 | 1F centreline 49.676 m, 1.30 printed (0.448 .. 1.30); block 0 .. 43.335 m2 | length -6.826 m; height 1.80 vs 1.30 + b_edge |
| BLK 178 29.80 x 1.00 | 29.80 | 2F centreline 29.050 (outer 29.800), 0.50; block 0 .. 5.810 m2 | his outer run; height 1.00 vs 0.50 + b_edge |
| his RC workbook | no parapet row | parapet concrete 8.040 .. 20.081 m3 + HELD | omitted in his RC; MISSING in the candidate too |

Total: his parapet blockwork 172.93 m2 vs the drawing 0 .. 60.596 m2 (+ 135.981 m2 per m of b_edge). Verdict proposals:
material UNRESOLVED (Q-65 C, designer); heights RULE_DIFFERENCE pending b_edge (no printed source for his 1.00 / 1.80);
parapet concrete: a MISSING category on both sides (every printed alternative carries >= 0.30 m RC; ENGINE_RIGHT is not
claimable while the candidate has no line).

## 8. Rules, tests, register rows, lesson

- R-T311-1 .. 4 in `parapet_plinth.py` (docstring). Fixture `tests/t311_parapet_plinth/test_t311_rules.py` (villa N: an
  RC parapet 1.760 m3, a block parapet on a 0.30 upstand with a printed cap 0.480 m3 + 3.600 m2, an unkeyed run 0.300 ..
  0.500 m3 / 0 .. 1.000 m2, plinth 6.000 + 0.500 m2 and a court segment 1.800 + 0.200 m2); adverse: a component in two
  trades refused, a defaulted height refused (a HELD bound accepted), a missing thickness refused, a HELD component as
  0 refused, the upstand carried again as blockwork refused, the upstand inside a beam line refused, an unprinted keyed
  type refused, a ground-beam soffit above the ground refused; mirror, reversal, rotation and millimetres do not move
  the result. `test_t311_alsenan.py`: byte rebuild, every run / segment once, closures named, one owner, held never 0,
  concrete lower bound = the upstand, house beam top +0.95.
- Register rows for the Lead (proposal): (a) 'Parapet runs, all roofs: RC part above the slab top = CONCRETE (new
  parapet line family; never BEAM: the schedule depth ends at the slab top), masonry part = BLOCKWORK, faces = FACADE
  (outer) / PARAPET_INNER (inner), top = COPING, upturn = the roof's FIN.WP.ROOF_UPTURN line; material split HELD
  (Q-65 C, designer)'; (b) 'Plinth: plaster face FACADE plinth (no finish line today); substrate = the ground-beam
  outer face (its m3 stays CONC.GROUND) + the GF wall course (MAS.BLOCK GF t=0.20); no plinth m3'.
- ERS s.7 lessons row (proposal): 2026-10-28 | A parapet was carried as 'block on the slab edge' (T-107, the freelancer
  172.93 m2) and as nothing in concrete, while the structural sheet's three details and the architectural sections all
  put at least 0.30 m of RC above the slab top and the sections draw it all RC | the element was classed by one detail
  ('Brick Wall') without asking what each printed alternative shares and without reading the section hatch | for an
  element whose detail is not keyed, book the part every printed alternative shares as fixed and the rest as a bounded
  HELD range; read the hatch convention of the section from its own slab / wall cuts; concrete above the slab top is
  never inside a beam line (every villa) | tests/t311_parapet_plinth | proposed.

## 9. Missing / HELD (never 0)

Material split per run (designer: which detail on which run; cap profile 'as per arc.'); b_edge per roof (D-39); 1F
NE-1 / SW-1 / SW-2 heights; reinforcement (type unkeyed, no rebar change before an approved stage); passage plinth
substrate; pool-court plinth bottom; the ground-beam / wall outer-face alignment (0.30 beam vs 0.20 wall: a possible
0.10 m ledge at +0.95, not printed); stop-ends at free parapet ends; the 2F roof upturn line has no outline (BLOCKED_RFI).
Lane I consumer: COMPONENT_OWNER_T311.csv (component, trade, line or NO_LINE, quantity range, status) with the two
ledgers as its rows; T-314 integrates the faces, a new concrete line family carries the parapet RC part.
