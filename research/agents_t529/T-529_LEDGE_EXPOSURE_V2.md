# T-529 B8-06 pool-court ledge membrane: exposure rule V2 from the drawn geometry (research, unwired)

Worker 2 (lane A), 2026-11-05, claim 14:4x UTC. Files: `t529_exposure_v2.py` (WP_APPLICABILITY_RULES_V2 exposure
step, R-WP-APPL-EXPOSED-2a..e, any villa), `t529_inputs.py` (handles and printed values only, no coordinate),
`t529_alsenan.py` (run on the private drawing), `tests/t529_ledge_exposure/` (14 tests). No engine module, method,
rule / knowledge version, registry, master or candidate file changed (V1 `engine/source/wp_applicability_rules_v1.py`
untouched and reused); candidate V3.0.58 and released V2.9 + route G do not move. Drawing by Drive title and handle
only: "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55..., re-checked this run).

## 1. Physical element and the question (ERS s.2.1)

The ledge is a 0.20 m strip of the +5.50 exterior slab (between the 1F curved bay face, r 1.935, and the void edge
BCF, r 1.735, west of the 1F wall line), over the GF pool court. Water reaches an exterior slab top by rain through
open sky AND by driven rain / run-off through any side open to the outside air; it is dry only under a cover with
every side closed up to that cover. The ledge's void side (BCF / 2F1C, single layer-5 lines, nothing standing on them)
and its continuation into the open-sky court (no step, joint or upstand drawn at the wall line) are open sides.

## 2. Rule V2 (proposed NEW version; supersedes only R-WP-APPL-EXPOSED-1 of V1; scope every villa)

- 2a open-sky part (surface less the plan union of drawn covers) -> EXPOSED.
- 2b covered part with any open side (slab / void edge, railing, parapet, or its interface with the open-sky part
  where no enclosing screen is drawn) -> EXPOSED: the balcony condition. UP-WP-ROOF-001 (OWNER_APPROVED, knowledge
  1.5.0: purpose 'exterior horizontal surfaces exposed to water', scope 'balconies, terraces and roofs drawn as
  spaces', area 'the drawn exterior space area') waterproofs a balcony over its whole drawn area with no deduction for
  the floor above it; a membrane also runs to a physical termination (upturn, edge, threshold, joint), never to the
  plan shadow of a slab 4 m overhead.
- 2c covered and closed round (walls; glazing with a drawn head closing to the cover; a screen on the cover line)
  -> NOT_APPLICABLE.
- 2d HELD with its bound (never 0): sides closed but cover outline not established; glazing without a drawn head or a
  side of unknown kind and no open side; a glazed cover whose outline is not drawn.
- 2e a printed membrane extent (detail / section) governs.
No angle is used anywhere (the T-522 theta_c table becomes information only). The covered / open split is always
reported with each boundary's source.

Difference from the row's acceptance text, stated for the Checker: the row proposed 'covered in plan -> no membrane'
(fixture 3.00 x 0.40, 1.80 covered -> 0.48 m2). Under the owner rule a covered part that is open at a side is a
balcony-type surface and is waterproofed, so the plain fixture gives **1.20 m2** (0.48 open-sky + 0.72 covered, open at
the void edge). The 0.48 m2 result is reproduced exactly where it is physically right: the covered part closed by a
glazed screen with a drawn head on the cover line (2c), or a printed detail stopping the membrane there (2e). A plan
projection rule would also waterproof no stacked balcony at all, contradicting UP-WP-ROOF-001.

## 3. Development villa (from P7757.dxf at run time)

| item | value | source |
|---|---|---|
| ledge area | 0.639573 m2 (own circle construction 0.639575; hand: r 1.935 segment at a = 1.1850 m 1.600907 - r 1.735 segment 0.963461 = 0.637446, + 0.002127 where the void follows 2F1C instead of the r 1.735 circle) | 1F plan BCD / BCE / BD0, BCF / 2F1C, wall line B62 / B61 |
| cover in plan | 100 % covered: open-sky part 0.000000 m2, covered 0.639573 m2 | 2F plan: ROOF +9.70 hatch 2F21 to its east edge 12A7 (the parapet inner face over the 1F wall), then the layer-5 element 12A7 / 1311 / 1319 / 130C / 1313 to 0.35 m past the 1F wall line (printed '35', DIMENSION 19A6, measured 0.348259) |
| cover edge distance | 0.295604 .. 1.045604 m behind the projection edge 1319 (T-522 took the 1F wall line: 0 .. 0.75) | information only |
| sides of the covered part | void edge 2.817214 lm (open), zone split on the wall line 0.562439 lm (open, slab continues), bay face 3.528277 lm (BCD 0.250804 wall, BCE glazing, BD0 wall); total 6.907930 = perimeter, residual 0 | 1F plan |
| decision | EXPOSED by 2b (open sides 3.379653 lm) | V2 |

The BCE / BD0 split differs from T-522 by 0.000836 lm (one discretisation segment straddling the junction is owned
by BCE here); it is information only: the V1 rows below take the T-522 split (BCD 0.250804, BD0 0.300810).

## 4. Effect if wired (stream F, no wiring here)

| V3.0.58 line | before | after (this piece) |
|---|---|---|
| L-2361d6ec ledge membrane, FIN.WP.ROOF m2 | HELD 0 .. 0.639573 | **0.639573 m2 MEASURED** (rule basis 2b + R-WP-APPL-EXPOSED / ONCE) |
| L-d7d1bf8c ledge upturn, FIN.WP.ROOF_UPTURN lm | HELD 0 .. 3.528277 (T-522: upturn 0 .. 0.551615 + transition 2.976663) | upturn **0.551614 lm MEASURED** (= 0.110323 m2 at 0.20; BCD 0.250804 + BD0 0.300810; V1 R-WP-APPL-UPTURN-1 now applies) + WINDOW_TRANSITION 2.976663 lm stays HELD (UP-WP-DOOR-001, by detail) |
| ledge void edge | HELD 2.817214 lm | unchanged (termination by detail) |
| new | - | DRAINAGE_FALLS RFI on the ledge (V1 R-WP-APPL-DRAIN-1; never blocks) |

FIN.WP.ROOF valued **209.018867 -> 209.658440 m2 (+0.639573, +0.306 %)**; HELD lines on the code: the ledge line
closes (the 2F block roof Q-34 stays). FIN.WP.ROOF_UPTURN **186.782544 -> 187.334158 lm (+0.295 %)**, 187.834160 lm
with the T-522 window run. Freelancer roof waterproofing 285.00 m2 (cells not read, T-494): -26.7 % -> -26.4 %, no
verdict change on the line total.

## 5. Findings

- F-T529-1 (correction of T-494 / T-522 evidence text): the +9.70 cover does not end on the 1F wall line. The hatch
  ends 0.20 m west of it (parapet over the wall) and a layer-5 element projects 0.35 m east of it (printed '35'),
  over y 4.5 m of the court. Over the open-sky zone it covers **0.165317 m2** of the T-507 4.906867 m2. Under V1 that
  strip would be 'covered, open at a side' (HELD); under V2 it is 2b EXPOSED, so the wired 4.906867 m2 stands. The
  element's build-up (slab, cornice, fascia band 1314..1318) is not read; V2 does not need it.
- F-T529-2: a plan-projection exposure rule contradicts the owner balcony scope (a stacked balcony would get no
  membrane); exposure is decided by open sides, not by the shadow of the cover.
- WHO IS RIGHT: ledge membrane ENGINE_RIGHT once wired (own hand 0.637446 + 0.002127 = 0.639573 m2); the V1 HELD was
  a rule gap, not a measurement error.

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-05 | a 0.64 m2 exterior ledge stayed HELD for two rounds and was narrowed by a rain angle | V1 made 'covered, open at a side' undecidable, and the cover edge was taken at the wall line without reading the plan above | R-WP-APPL-EXPOSED-2a..e (every villa): open-sky part and any covered part open at a side are EXPOSED (balcony condition, UP-WP-ROOF-001); closed round -> N/A; HELD only for an unestablished cover or enclosure; a printed extent governs; never an angle; read the plan above for the real cover edge | tests/t529_ledge_exposure (Q529 by hand 1.20 / 0.48; adverse: cover missing, glazing without head, glazed cover undrawn, unknown side, mm, unsourced, unreconciled, mirror / rotation) | proposed |

Missing: the threshold detail at BCE and the void-edge termination (designer), ledge falls / outlet (RFI). Wiring:
a later V3.0.x under Gate B (stream F) with V2 promoted as a new engine rule file.
