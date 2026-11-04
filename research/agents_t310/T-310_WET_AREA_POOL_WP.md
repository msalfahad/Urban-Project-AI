# T-310: wet-area waterproofing fixes and pool layer lines in the candidate (ARCH_TAKEOFF_V3.0.49)

Worker 2 (lane A, stream F), claim 2026-11-04 00:41 UTC, run session_01E6cPner8LiP93QwzhcyAtE. Gate B integration
package on the candidate of record V3.0.48 (merge 5de697ff, V3_0_48_BOQ_LINES.json 33a81c53). Nothing released; V2.9 +
route G stays the default. Drawings named by Drive folder and title only ("Alsenan chalet project": P7757.dxf from
P7757_DXF_COMPRESSED.zip and "ST7757 dxf.dxf", own decode this run).

## 1. Physical elements (ERS s.2.1) and what moves

| Element | Before (V3.0.48) | After (V3.0.49) | Status | Source |
|---|---|---|---|---|
| 1F east bath (1F-12) wall upturn, L-60f10010 | 1.480 m2 (window W18 deducted) | **1.580 m2** = (8.700 - 0.800) x 0.20, run of waterproofing policy V3 | DRAWING-CONFIRMED (Checker own re-measure, T-303) | T-303 |
| its doorway segment 0.80 x 0.20 | not stated | HELD beside (0.160 if billed): doorway detail not printed, UP-WP-003 1.1.0 | HELD | policy V3 rows |
| 3 termination lines on W18 (L-0a7238ed / L-1ef59757 / L-8fb80f62) | BOUNDED | NOT_APPLICABLE_WITH_EVIDENCE (sill 0.84 above the 0.20 upturn: no membrane edge) | evidence | T-303 |
| pantry (GF-07) floor membrane, L-f32abcdb | 13.500 m2 | **13.455 m2** = box 13.500 - column 2FAE 0.900 x 0.050 | DRAWING-CONFIRMED | T-286 + own re-read |
| 11 transition m2 lines | one per room side | keyed by physical door id (record only, figure unchanged) | unchanged | T-303 / T-249 |
| 2 duplicate transition lines (doors D-GF-02, D-GF-10 booked from both sides) | BOUNDED | NOT_APPLICABLE, naming the carrying line | evidence | T-303 |
| doors D-GF-11, D-GF-12, D-1F-06 (candidate OP-017 / OP-018 / OP-010) | no transition line | one HELD BLANK line each (BLOCKED_RFI, never 0) | HELD | T-303 |
| pool membrane (WP.POOL.MEMBRANE) | no line (MISSING) | **29.582355 m2** on base + outer faces; upstand 0 .. 1.349668 HELD beside; function HELD (S8.2) | DRAWING-CONFIRMED | T-309 |
| pool protection screed (WP.POOL.PROTECTION_SCREED) | no line (MISSING) | **1.524503 m3**; upstand 0 .. 0.068072 HELD beside | DRAWING-CONFIRMED | T-309 |

Every other V3.0.48 line is byte-identical (asserted by integrate()); totals move only in the waterproofing codes
(asserted by write()).

## 2. Pantry column ruling (O-T303-01, own re-read, ERS s.2 steps 1-4)

Physical question: is there floor under the 0.045 m2 the T-286 closure removes? Read on P7757.dxf by handle: the printed
box is faces AE (west), B3 (east edge), A6 (south), 158 (north), DIMENSIONs 5D5 3000.0 and 5E1 4500.0 -> 13.500 m2. The
closed S-COL.BON outline 2FAE is 1.100 x 0.250; relative to the box's north-west corner it runs x -0.200 .. +0.900 and
y -0.050 .. +0.200: it sits in the corner of the two 200 mm walls (9F / AE west, 158 / 15A north) and stands 0.050
proud of the north wall face over 0.900 m. Overlap with the box: 0.900 x 0.050 = 0.045000 m2. (The Checker's T-303
window found 'no S-COL.BON entity inside the box' because the outline's body lies outside it; only its 50 mm edge
intrudes.) A column is not floor: the membrane is laid on the slab face and turns up the column face. The other 17 wet
floor lines follow their drawn outline round column corners (O-T303-01's own example: the dewaneya wash, 0.0175 m2), so
the pantry follows the same rule: 13.455 m2. Residual named: the architectural wall line 158 does not draw the 50 mm
step; a column set flush by the designer gives 13.500 (+0.045, +0.33 %). Owner method (Q-37 A box) and drawing method
(box less column) agree up to that named reading; not an owner question (ERS 2.7: no method choice open).

## 3. Policy V3 (F-C-T458-2) and the upturn rule

engine/source/waterproofing_policy_v3.py: V2 rows unchanged (UP-WP-002 2.0.0 0.20 m; door crossings never deduct the
run; each doorway segment its own row, HELD while the project's doorway detail is unknown), V3 subtotals: an item whose
rows are all HELD prints HELD (measured_m2 None), never 0.0 (the Checker's T-458 finding); an item with measured and
held rows prints PARTIAL. V2 is kept unchanged as history (its test still pins the old 0.0). The 1F east bath value is
computed by the policy from the re-measured boundary and door width and asserted equal to the inventory's 1.58; a window
whose sill is at or below the upturn is refused as 'not deducted' (it would cut the run).

## 4. Engine vs freelancer

No freelancer row per wet room (T-074 compared the boundary only: 144.61 vs 144.73 lm, +0.1 %); upturn +0.100 m2 and
pantry -0.045 m2 move the candidate's wet-area membrane by +0.055 m2 net. Pool: the freelancer carries no pool membrane
or screed row (T-309 search of his 885 rows): RULE / SCOPE difference, the whole 29.582 m2 + 1.525 m3 is scope he does
not carry (his silence is not absence, lessons row 2026-10-24). Who is right: east bath upturn ENGINE_WRONG (fixed),
transitions ENGINE_WRONG rule application (fixed, figures still held), pantry ENGINE_WRONG -0.045 (fixed, flush-column
reading named), pool MISSING category (added).

## 5. Rule, tests, files

R-T310-1 (every villa): see the module docstring of engine/source/arch_v3049.py. Tests tests/t310_wet_area_wp: villa
W310 by hand (normal: upturn 1.840 with a window above, utility box less column 4.960, one transition per door with a
duplicate and a missing door, pool membrane 12.000 + screed 0.600 with held upstands; adverse: window at the upturn,
stale before, value off the policy / closure, held door with a value, door keyed twice, duplicate without a keyed
carrier, NA with a value, pool layer on a water face, reversed bound, 0, mm, VERIFIED as an input, wrong code, stale
line, applied twice, held line valued 0 in the check, record on another code; mirror / rotation); policy V3 normal +
adverse (all-held prints HELD); hub wiring; family master 1.46.0.

Waiting (named, not in this package): the pantry's own door (threshold / transition / number, insert not bound), the
pantry open-side termination and floor drain count, the two closure-derived thresholds (T-303 finding 2), every
transition figure (detail not printed), the pool upstand (C9) and membrane function (S8.2).

Lessons-register row (proposed, ERS s.7): 2026-11-04 | a structural column's 50 mm edge inside a printed wet box was
missed by an entity-in-window search (the outline's body lay outside the box) | a presence check that looks for
entities INSIDE a region misses an outline that only overlaps it | test a region against every outline by polygon
intersection area, never by insertion point or centroid (every villa: columns, shafts, ducts in wet rooms and floor
zones) | tests/t310_wet_area_wp (floor less column) | PROPOSED.

## 6. Run on the drawings (this session)

research/agents_t310/v3049_run.py on the Drive copies (own decode; own T-167 run): V3_0_48_BOQ_LINES.json = candidate
of record 33a81c53 (asserted), 4876 lines -> V3_0_49_BOQ_LINES.json f3fe14da, 4881 lines: 18 changed + 5 added, 4858
byte-identical. Bindings asserted on the candidate: the two duplicates carry closures D2:495 / D2:825; the three
missing doors' doorway lines (GF OP-017, GF OP-018, 1F OP-010; opening ids are per floor) have no transition line.
Totals moved (waterproofing codes only): FIN.WP.WALL_UPTURN 25.114585 -> 25.214585 m2 (+0.100, +0.40 %);
FIN.WP.FLOOR 85.62071 -> 85.57571 m2 (-0.045, -0.05 %); FIN.WP.DOORWAY_TRANSITION 13 bounded (high 2.138816) -> 11
bounded (high 1.819408) + 3 HELD BLANK; FIN.WP.TERMINATION 7 bounded (high 3.660363) -> 4 (high 3.160363);
WP.POOL.MEMBRANE + 29.582355 m2; WP.POOL.PROTECTION_SCREED + 1.524503 m3. Per-line rows: summary_t310.json.

## 7. r2 (Verifier rejection 2026-11-04 ~02:25 UTC: Gate B (b), 4 new failures)

Cause: ARCH_TAKEOFF_V3.0.49 (declared TOOLING) imported waterproofing_policy_v3 -> v2, both declared UNWIRED_PRODUCER:
the T-212 property P2 (no candidate reaches an unwired producer) failed in t212 (2) and t379 (1); the committed T-459
binding (t459) did not list arch_v3049.

Fix (no quantity change):
- arch_v3049 is a GUARD_HOST: `guard_recheck()` runs the merged V3.0.6 guard through `arch_v307.guard_changes` over the
  V3.0.48 lines with this version's changes + its 5 added lines (each ADD names its guard_element, part WHOLE). A hold
  on a changed or added line refuses the run (arch_v307), and so does a hold on any other line (nothing outside the
  waterproofing codes moves). No guard block -> NO_PROJECT_INPUT in the log. load_inputs validates the optional block.
- Guard class record (own commit, guard tests untouched): waterproofing_policy_v2.py:36 and _v3.py:20
  UNWIRED_PRODUCER -> GUARDED_VIA_V3.0.6 (their lines now reach the candidate and the V3.0.6 guard re-runs over them).
  Rebar firewall (T-477): v2 stays OTHER_REBAR_AWARE; v3 carries no rebar word (t477 undeclared check passes).
- t310_inputs.build carries the V3.0.7 guard inputs unchanged (t193, new_records [] as t146 / t211 / t231).
- T-459 binding rebuilt by `t459_census.py candidate --write` (arch_v3049: no route G token, touching []); master
  1.46.0 rebuilt by its builder (line references only); rules/RULES_MANIFEST.json rebuilt by m9_rules_manifest.py
  (only the 1.46.0 sha).

Drive run (this session, own decode of P7757_DXF_COMPRESSED.zip + ST7757 dxf, own T-167 run, chained to the end):
V3_0_48 33a81c53 (4876 lines) -> V3_0_49 f3fe14da (4881), identical to r1; guard state RUN over 4881 lines, evidence
research/agents_t193/dev_villa_guard_evidence_v2.json (a94e199b), held_live_new [], silent_omissions [], no hold
on any line -> the run passes; findings stay recorded-only / listed-not-live as in V3.0.7.
Tests: tests/t310_wet_area_wp/test_guard_r2.py (normal: no block, block with no finding = same changes, ADD
guard_element; adverse: drawn part carried by no line refuses, hold outside the codes refuses, malformed block refused,
candidate importing a still-unwired producer is a P2 problem).

## 8. Round 3 (worker 2, 2026-11-04 04:41 UTC): rebase only, re-versioned ARCH_TAKEOFF_V3.0.52

T-497 merged V3.0.50 / master 1.47.0 (5f8814e8, extends V3.0.48) during r2; T-483 r2 holds V3.0.51 / 1.48.0 in
parallel. By the merge-order rule this package rebases on the merged 416392e8 as the next free numbers: module
engine/source/arch_v3052.py (was arch_v3049.py; METHOD ARCH_TAKEOFF_V3.0.52, EXTENDS ARCH_TAKEOFF_V3.0.50, schema
URBAN_V3052_INPUTS_V1, files V3_0_52_*), its earthworks invariant now arch_v3050.check_zone_owner (the V3.0.48 check on
the swapped-back view), WAITING from arch_v3050. Engineering content unchanged (rules, records, values).
- Hub tools/urban_boq_m9.py as T-497 / T-483 r2: a V3.0.52 run is rewritten to a V3.0.50 run on the one V3.0.50 line
  (line-stable), "--v3052-inputs and --method go together", stage after the V3.0.50 stage on l3050; the r2 rewrite of
  the 45 method lists is gone (shared files taken from the working branch).
- Master rules/coverage/BOQ_FAMILY_MASTER_1.49.0.json = 1.47.0 + pending V3.0.52 (builder build_master_1_49_0.py,
  --check True, problems []); 1.46.0 dropped (never merged). RULES_MANIFEST and the T-459 binding rebuilt by their tools.
- research/agents_t310/v3052_run.py: as before plus --v3050-inputs (research/agents_t497/t497_inputs.py), asserts
  V3_0_48 33a81c53 and the candidate of record V3_0_50 d40c4ec5 as the base.
- Drive run r3 (own decode, own T-167 run, chained to the end): V3_0_48 33a81c53 -> V3_0_50 d40c4ec5 (4876, the
  candidate of record, asserted) -> V3_0_52 dbb9aab0 (4881): 18 changed + 5 added, 4858 identical; the 23 ledger rows,
  the totals moved by code and the wet_area_wp identity are identical to r2 (asserted by the summary builder), guard
  RUN, no hold. The first r3 run refused: integrate() passed the V3.0.50 lines as `before` to check_zone_owner, which
  then fed the V3.0.50 trench range to the V3.0.48 check; fixed (no `before`: the V3.0.48 form is rebuilt from the
  record) with tests/t310_wet_area_wp/test_rebase_v3050.py (normal + adverse; the normal case fails on the old call).
- Full suite on f8e9e6fc ran to the end: 2 failed = t310 summary pin (summary regenerated after this run) + t485
  'T-443','T-350b','T-497' (identical on the working branch 416392e8: baseline, T-483 r2's gate fix); t310 folder,
  t212, t379, t459, t497 green on the final commit.
