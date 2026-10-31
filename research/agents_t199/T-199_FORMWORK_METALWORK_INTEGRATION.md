# T-199: formwork and railings / shutters in the candidate (ARCH_TAKEOFF_V3.0.30), integration package for Gate B

Worker 3 (lane I), 2026-10-31 UTC, run session_01E6cPneTpAJJ4RXpwYWC8M1. Development villa, not an accuracy claim.
Opt-in candidate only: the released default stays ARCH_TAKEOFF_V2.9 + route G; nothing is released. No client name,
coordinate or image is committed; drawings are cited by Drive title only.

integrates: T-163 (r3, MERGED 659f889f), T-164 (MERGED 390fabf4), T-308 (r5, MERGED efb38618), T-311 (MERGED bd7b8c23),
T-332 (r2, MERGED 61d5597e), T-352 (MERGED b12e10de). Consumed files (pinned by sha256 in
`research/agents_t199/t199_inputs.py`; an edited file stops the build; nothing is typed):

| File | Task, Checker verdict | Used for |
|---|---|---|
| research/agents_t332/T199_FILL_T332.csv | T-332 r2, Verifier 2026-10-29 22:02 UTC Gate A PASS (own re-aggregation of all 678 rows) | formwork r5 faces bound to the V3.0.21 concrete lines (r5 = T-163 r3 + T-264 r4 + T-293 + T-308: CB5 span 2 once, BAND0049 HELD) |
| research/agents_t332/FORMWORK_T332_BY_FACE.csv | the same | the faces tied to NO line (24 parapet runs = T-311, 2 lift-pit faces, 12 r5 pieces), 69 SPLIT_UNRESOLVED, named aggregates, INFO, S1 |
| research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json | the same | each bound concrete line as bound (id, item, element, state, quantity), re-checked on the candidate |
| research/agents_t352/T199_FILL_T352_ADDENDUM.csv + STAIR_FORMWORK_T352_BY_FACE.csv | T-352, Verifier 2026-10-30 00:09 UTC Gate A PASS (own re-measure of the 7 valued faces) | stair SIDE faces, 27 faces on 8 STR.CONC.STAIR lines |
| research/agents_t164/RAILINGS_T164.csv + SHUTTERS_T164.csv | T-164, Verifier 2026-10-22 20:21 UTC Gate A PASS (own re-measure RL-02 / RL-03, 0.0 %) | railing runs (lm), shutters (pcs) |
| research/agents_t199/DOWNGRADE_BOUND_V3029.json | ids copied by `t199_downgrades.py` from the board's verdicts/V3.0.29/DOWNGRADES.json (sha256 in the file) | the 9 unresolved Checker downgrade records: no valued formwork may sit on a concrete line they hold |

DOWNGRADE RECORDS (Lead acceptance): the 9 records of verdicts/V3.0.29/DOWNGRADES.json (incl. DGP-T373-LAP and
DGP-T378-STAIR) stay bound: this package adds lines only, every V3.0.29 line is byte-identical (asserted), so each record's
line_content_sha256 still matches its lines; no HELD BLANK line is re-valued. The three m3 records (footing blinding,
boundary lower band, 9 ground beams D-34) carry formwork rows that the ledger already holds (OQ-10 FORMED HELD ranges;
blinding has no form row): no valued formwork line sits on any of the 422 downgrade-bound lines (asserted in the inputs
and refused by the engine).

## 1. The physical question and the answer (ERS s.2.1, s.3)

**Formwork.** A formed face is a concrete surface cast against a form; it bounds ONE member and is reported beside the
candidate line that carries that member's concrete, never inside its m3. A face cast against ground, blinding, screed or
masonry has no form (no row). Below the existing ground OQ-10 is open (no answered owner rule measures formwork:
OWNER_QUESTIONS_ANSWERED searched for 'formwork' / 'shuttering'; only Q-74 A names it, for the straps' own geometry), so
the FORMED and EARTH_CAST readings travel together on ONE blank line, never summed, never chosen. The released run and
V3.0.29 had **no formwork line at all** (0 of 3,962 lines; T-332: 0 formwork lines in V3.0.21).

**Railings / shutters.** A railing run is its installed length: the 50 mm plan band's centreline (corners once), on a
flight the sloping path per tread (UP-STAIR-012), never the plan projection; height and material are specification, never
a length. A shutter is a pair of leaves counted on the elevations; no rule sets its area basis (louvre panel, leaf
outline or opening), so the area is HELD. V3.0.29 carried 14 BLOCKED per-flight FIN.RAILING lines of the plan reader
(STAIR_RISER_NOT_ESTABLISHED) and no roof / floor-edge guard, no shutter.

Rule **R-T199-1** (engine/source/arch_v3030.py, every villa): formwork is booked face by face, once, beside its member's
concrete line (one line per FILL row: concrete line x status x alternative x method); E (element method) is the
comparison method, carried beside G on the same line's record, never a second line; a valued line needs its concrete
line live and exactly as the ledger bound it (id, item, element, state, quantity: else the binding is stale and the build
stops); no valued formwork on a concrete line a Checker downgrade record holds; an S1 scenario face is never in the
candidate; OQ-10 alternatives never summed or chosen; HELD is BLANK, never 0. Railings: one run one line, a confirmed run
is the sum of its measured segments (a HELD segment inside it, or a plan length relabelled, is refused); held runs blank
with the measured part named; shutters by leaf count, area HELD. While a run line carries a figure, a per-flight
FIN.RAILING line with a figure is refused (the same guard twice).

## 2. BOQ lines (V3.0.29 -> V3.0.30): 661 lines ADDED, 3,962 byte-identical, 0 changed

| Family (item code, unit) | Lines | Valued (state) | Blank (HELD) | Valued total | Evidence (s.5) |
|---|---|---|---|---|---|
| STR.FORMWORK m2 (B10-13) | 612 | 254 (191 PROVISIONAL + 63 SOURCE_DERIVED: the concrete line's own state) | 358 = 194 HELD faces + 60 OQ-10 pairs + 104 untied faces | **1,028.905457** | CALCULATED (T-163 r3 -> T-332 r2 Gate A); NOT RELEASED |
| STR.FORMWORK.STAIR m2 (B7-13) | 31 | 10 (2 PROVISIONAL + 8 SOURCE_DERIVED) | 20 (7 T-332 + 9 T-352 incl. 1 CONFLICT + 4 untied) + 1 NOT_APPLICABLE | **36.927436** = 32.822036 soffits / risers + 4.105400 sides | CALCULATED; T352-21 / -26 / -27 ASSUMED — OWNER-APPROVED (riser 4.50 / 28, Q-50 A cond) beside it |
| MET.RAILING.GUARD lm (new) | 6 | 4: RL-01 6.262, RL-02 4.921, RL-03 7.967, RL-06 2.400 | RL-04 (6.127 measured), RL-10 | **21.550** | RL-02 + RL-03 12.888 VERIFIED (Checker T-164 e / f); RL-01, RL-06 DRAWING-CONFIRMED |
| FIN.RAILING lm (B7-09) | 5 new (+14 per-flight blank lines unchanged) | 2: RL-05 16.324, RL-08 1.042 | RL-07 (16.153 measured), RL-09 UNKNOWN, RL-11 | **17.366** | DRAWING-CONFIRMED |
| FIN.HANDRAIL lm | 1 | - | - | - | EXCLUDED_WITH_REASON (RL-12, UP-STAIR-013: none drawn) |
| ARCH.SHUTTER pcs / m2 (B6-05) | 3 + 3 | W14 2, W11 2, W12 2 = **6 pcs** | 3 area lines | 6 pcs | DRAWING-CONFIRMED (count); area and material HELD |

Formwork by member (valued, concrete line item): beam lines 412.991855 (soffits, sides, slab-edge bands and joints the
ledger books on the beam line), slab lines 375.049829, column lines 128.633361 (shafts + valued joint faces), ground-beam
faces above N.G. 47.947713, dome shell soffit forms 48.300 (2 x 24.150, the S0 approved design, beside the SOURCE_DERIVED
dome shell lines of T-185), pool 15.982699 (water face 13.283363 + outer face above EG 2.699336), stairs 32.822036 +
4.105400 sides = **1,065.832893 m2 valued**. Comparison method E on the same members 422.693420 m2 (beside, never added).

Held, by name (blank, never 0; bounds beside each line, never in a total): 194 + 7 HELD FILL rows (joint faces, sunken
panel edges D-41, stair wall / member sides, BAND0049 with no drawn face, faces held with their concrete line); the 60 OQ-10
lines (FORMED 183.696276 m2 in all, EARTH_CAST 0, never summed), incl. the strap sides on the T-174 axis lengths (SB1 4.550,
SB2 2.2927, SB3 2.6064 = 9.449 m2 FORMED, Q-74 A) and the F8 / pool conflict 0 .. 1.856909; 108 untied faces: 24 parapet RC
faces of T-311 (81.588690 .. 202.781594 m2; parapet RC volume is T-319's lines, these faces are bound to no line yet), the
lift-pit wall faces (5.500 m2 per m of pit height each, depth D-43), 69 SPLIT_UNRESOLVED pieces (T-293), 12 r5 pieces with
no member (unmarked layer-5 pairs, two dome drums G3-b, boundary pads), the neck aggregate R4-048 and the sunken-panel
aggregate R4-315. Stair sides: 16 bounded + 4 unbounded HELD, the MS1-L well side CONFLICT 0.709344 .. 0.869164 (C-ST-4).
R4-339 (aggregate stair sides) SUPERSEDED by T-352's 27 faces; R4-314 (pool-court void band) owned by the ring line, not
here; 7 S1 scenario faces and 7 INFO rows never lines; R4-340 WALLS / BASE and R4-342 REMOVED (replaced by their faces).

Identity: V3.0.29 3,962 lines -> V3.0.30 4,623 (661 ADDED); every V3.0.29 line byte-identical (outside_rows_sha256
bae739b9...); vs released V2.9 + route G: the 661 lines are NOT_IN_RELEASED (V2.9 has no formwork, guard or shutter line;
its 14 per-flight FIN.RAILING lines are blank there as here); every other line's comparison with V2.9 is the one V3.0.29
already reported (3,962 SAME vs V3.0.29). Totals moved (A304.code_totals): only STR.FORMWORK, STR.FORMWORK.STAIR,
MET.RAILING.GUARD, FIN.RAILING, ARCH.SHUTTER (asserted; the column the engine calls 'released' is the valued sum, NOT
RELEASED). Per-line before / after / faces / bounds / alternatives / E comparison / evidence: V3_0_30_INTEGRATION_LEDGER.csv;
line-by-line diff vs V3.0.29 and vs released V2.9: V3_0_30_DIFF.csv (run outputs, not committed).

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived (carried) |
|---|---|---|
| Formwork | none on record (no answered rule; OQ-10 open below EG; Q-74 A: the straps' own axis geometry) | method G: the drawn faces cast against a form on 'ST7757 dxf.dxf' by handle (T-163 r3 .. T-308 r5, T-332 r2, T-352); method E (struct_n10 element faces) beside as the comparison |
| Stair guard | UP-STAIR-012: installed sloping length; UP-STAIR-013: wall handrail only where shown | band centreline per tread (ST-02 r 1.5555, riser 0.160714) and pitch line from the merged T-184 counts (T-164) |
| Roof / floor-edge guard | drawn length | plan band centreline, corners once; NW elevation rail 4.921 = plan 4.921 (Checker) |
| Shutters | none (Q-33 covers windows, not shutters) | leaves counted on the SE elevation and the fence elevation |

Where both exist they agree (installed length; drawn faces). Where no owner method exists, nothing is chosen for size:
the E figure is never used and the OQ-10 readings stay side by side.

## 4. Evidence status, missing and held (WORKFLOW_CONTROLS s.5)

- CALCULATED (formwork: carried exactly as merged; the Gate A verdicts re-measured pieces, not every face): 1,065.832893 m2
  on 264 lines; of it ASSUMED — OWNER-APPROVED on three stair side faces (Q-50 A cond riser) named in the line records.
- VERIFIED: RL-02 4.921 + RL-03 7.967 = 12.888 lm (Checker's own re-measure). DRAWING-CONFIRMED: RL-01 6.262, RL-05
  16.324, RL-06 2.400, RL-08 1.042 = 26.028 lm; shutters 6 pcs (count).
- HELD / UNKNOWN (blank): 378 formwork lines + 1 NOT_APPLICABLE (R4-330 on the blank MS1 flights line); RL-04 GF sea strip
  (plan band vs NW elevation; in neither metalwork nor the parapet chain as a figure), RL-07 ST-01 inner balustrade (16.153
  measured, the MS1-T winder and MS1-LD turns not dimensioned), RL-09 ST-02 outer band (guard or string), RL-10 fence railing
  (length not printed), RL-11 ST-03 entrance guard (none drawn); shutter areas and materials.
- Not in this package: the 14 per-flight FIN.RAILING blank lines (V2.9 plan-reader method, riser not established) stay
  byte-identical; they describe the same stair guards as RL-05 / RL-07 / RL-08, so the engine refuses a figure on them while
  a run line is valued; retiring them needs the Lead to name the owner line in the element register (finding F-T199-1).
  T-361 (merged: posts / glass panels / open edges) adds no quantity and is not wired. Real export (boq_export_v1) not
  re-run on V3.0.30 (no Checker V2 verdict binds a V3.0.30 line yet). Parapet faces not bound to the T-319 parapet RC
  lines (a new binding is its own Gate A piece).

## 5. Downstream consistency (cross-trade, double count)

- Concrete: no concrete line changes (formwork is its own family). Binding: all 351 concrete lines the faces are bound to
  stand in V3.0.29 exactly as T-332 bound them on V3.0.21 (item, element, state, quantity re-checked line by line; 0 stale):
  V3.0.22 .. V3.0.29 moved no STR.CONC line under a face.
- Each face once: 1,102 face ids booked across the 643 formwork lines (checked on the finished lines); every face of the T-332
  ledger is booked, the E comparison or a named non-line (closure test, 0 left over); the 27 T-352 faces once.
- Downgrades: 9 records, 422 lines, all byte-identical; no valued formwork on any of them.
- Parapets: the 24 parapet RC faces are HELD with no line (T-311 runs); parapet RC concrete (T-319, V3.0.23) is not re-bound
  here (a new binding is a Gate A piece: proposed follow-up), so a parapet formwork figure exists nowhere.
- Railings vs parapets: RL-01 / RL-02 / RL-03 stand on the low parts of the wavy parapets (railing lm; the parapet block /
  RC is the parapet family's); RL-04 carries no figure in either.
- Shutters vs windows: shutters are not windows (Q-33); the window lines are untouched.

## 6. Against the freelancer (not proof)

Formwork: no formwork row in any of his six workbooks (T-163: 885 raw rows): **FREELANCER_NO_ROW** on 1,065.833 m2 valued +
the held / OQ-10 faces (a missing category on both sides until now; no %). Railings: his one row 'internal railing' 18.95 lm
(typed constant, FIN cover sheet) vs ours interior valued 19.766 lm (RL-05 16.324 + RL-06 2.400 + RL-08 1.042) + RL-07 16.153
measured HELD: **UNRESOLVED on his scope** (T-164 verdict: 18.95 fits one staircase system, not both); roof guards 19.150 lm
and shutters 6 pcs: no row (**HAND_FOUND**, an omission on his side and in V2.9).

## 7. Validation

- Own Drive copies this run ('Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`, 'ST7757 dxf.dxf'
  `9f9d1179`), decoded into the private folder only. Fresh T-167 base run (`research/agents_t167/v304_run.py`), then the full
  CLI run `research/agents_t199/v3030_run.py` (`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.30 --v3030-inputs`):
  **V3_0_21 json be22a4e4 (= T-332's binding base), V3_0_28 json 6f19b32b, V3_0_29 json 6b5dc44f / csv 09b3493b REPRODUCED
  (= the candidate of record, T-327 Gate B)**; **V3_0_30 json f90e8a66 / csv c8fd70f2**, ledger csv a017a941, diff csv
  2450f475, run json 592ac0fc. `v3030_direct.py` on the same V3_0_29 gives the same json byte for byte.
- Independent re-derivation straight from FORMWORK_T332_BY_FACE.csv and STAIR_FORMWORK_T352_BY_FACE.csv (face values, not
  through the FILL tables or t199_inputs): 264 (concrete line, method) keys, 0 mismatches, 1,065.832893 m2.
- tests/t199_formwork_metalwork: villa V199 by hand (beam G 3.300 with E 4.200 beside, column 3.600, slab 11.400, stair
  3.300 + side 0.850, footing OQ-10 1.920 / 0 blank, parapet face 1.2 .. 2.0 blank, railings 5.500 / 3.089 pitch line / held
  2.000, shutters 2 pcs + area HELD; totals 18.300 / 4.150 m2; V3.0.29 lines byte-identical; order invariant); adverse: held
  with a figure, E as a line, OQ-10 reading valued, alternative without FORMED, stale binding, valued face on a downgraded
  line, valued face on a blank concrete line, S1 face, a face twice, face count, negative / zero, stair side on a non-stair
  line, unmerged source, confirmed run with a held segment, a run not its segments, plan projection relabelled, held run
  with lm, verified held run, run twice, shutter area given, non-integer leaves, applied twice, concrete line missing, a
  REPLACE, double face / held figure on finished lines, per-flight railing figure beside the runs; Alsenan pins (T-332
  totals G 626.872989 + E=G 434.854504 = 1,061.727493, E 422.693420; T-352 27 faces / 7 valued 4.1054; every face once;
  R4-339 superseded; 7 S1 never; parapet 24 = T-311 totals; 60 OQ-10 FORMED 183.696276; no valued formwork on the
  downgrade-bound lines; railings 38.916 / verified 12.888; 6 pcs; an edited ledger stops the build); master 1.25.0 (builder,
  checks clean, dropping the entry is stale, a family naming the package refused).
- L4 full suite tests/ + agents/ to the end on 5a324c57 (task commits 874628a3 + 5a324c57): 398 FAILED / ERROR, test by
  test against research/agents_t202/known_failures.json (396 listed): GONE 1 (christiannp WORKTREE_GITDIR passes here),
  **NEW 3**:
  (1) tests/r8_1 test_project_names_appear_only_as_field_audit_evidence_never_in_logic: the drawing_method text of the
  FORMWORK_FILL piece named the structural DXF's Drive title (a project token) in engine/source: **fixed** (the module now
  says 'the structural DXF'); tests/r8_1 + t199 re-run: only the 3 known r8_1 failures remain. The lines are unchanged by the
  fix (V3_0_30 json f90e8a66 again via v3030_direct.py; ledger json 367409ee / run json 9c7af9a2 carry the new text).
  (2) + (3) tests/t130_family_master test_every_written_item_code_belongs_to_one_family and
  test_no_not_implemented_family_has_a_module_in_engine_source: **NOT fixed, named for the Checker / Lead (finding F-T199-3)**.
  Both compare the CODE on the head with the frozen registry snapshot 1.1.0 (never edited): the new item codes
  STR.FORMWORK, STR.FORMWORK.STAIR, ARCH.SHUTTER have no family there (B10-13 and B7-13 list no item code at all), and B6-05
  shutters / B7-10 handrail are NOT_IMPLEMENTED there while this package now writes them. A missing category cannot be
  integrated without a new item code, and the family states may move only with the Checker's verdict (1.25.0 declares the
  package PENDING, names no family), so the 1.1.0 snapshot assertions break by construction; no earlier package added an
  item code. Not weakened or edited here. Proposed resolution (the Checker's or Lead's call): at Gate B the Checker's
  registry version assigns the codes to B10-13 / B7-13 / B6-05 / B7-09 (MET.RAILING.GUARD) and moves their states, and
  the two snapshot checks are re-pointed at the governing (newest) registry with the same assertions; until then the two
  are listed as caused by this package, not as known failures.
- L2 after the fix: tests/t199_formwork_metalwork (51), t327 / t326 / t332 / t352 / t164 / t319 / t343 / t338 / t318 /
  t279 / m9_s6 / t061 pass; codemap rebuilt by the tool at the end, stale none; freeze 0.

## 8. For the Checker (Gate B always-checked lines)

- New calculation family (all lines new to the candidate): sample the FILL binding on the two lines at or above 2 % of the
  formwork total (dome shells L-017d95e5711dfc94964c and L-e42d4100a60b118404f1, 24.150 m2 each, faces R4-343 / R4-350 beside L-8ea34765d16b54898140 / L-fffa895ed96b9d6a682c
  S0 soffit forms, T-163 r3 s.dome) and the largest beam / slab lines in V3_0_30_INTEGRATION_LEDGER.csv; every railing run
  (RL-01 L-b54ee211b5af50087b29, RL-02 L-1ff5e79e1c11b3a04eed, RL-03 L-b75c30fcd5e3b5607433, RL-05 L-62577112dc4c8cdb8640,
  RL-06 L-c9cd76a27a48bd353eea, RL-08 L-7c65444302070a5f33e6) on P7757.dxf by the T-164 handles; the shutter counts (W14 SE
  elevation, W11 / W12 fence elevation, Pages_11-12 p.12).
- Unit / dimensional assumptions: m2 contact area (formwork), lm installed path (railings), pcs (leaves); no conversion.
- Structural-safety relevant: formwork of footings / ground beams below EG stays OQ-10 blank; stair formwork 36.927 m2 with
  three ASSUMED — OWNER-APPROVED faces named.
- Cross-trade: F-T199-1 (per-flight FIN.RAILING lines vs the runs), parapet faces vs T-319 lines (not bound), RL-04.
- Material classification: none changed (no existing line retyped).

## 9. Findings and lessons-register row (proposed, ERS s.7)

- **F-T199-1** The plan reader's 14 per-flight FIN.RAILING lines (blank) and the T-164 runs RL-05 / RL-07 / RL-08 are the
  same guards on two line sets; guarded (no figure on both), retirement needs the register owner (Lead).
- **F-T199-3** The t130 snapshot tests (registry 1.1.0 vs the code) cannot pass once a missing category gets its own
  item code: see section 7 for the proposed resolution (Checker / Lead).
- **F-T199-2** No concrete line moved under a formwork face between V3.0.21 and V3.0.29 (351 / 351 re-checked), so the
  T-332 binding was consumable as is; a later concrete change will now stop the V3.0.30 build instead of carrying a stale
  face.

| 2026-10-31 | the candidate had no formwork and no guard / shutter line for nine days after both ledgers were Checker-merged (missing category on both sides, freelancer included) | the derived trade (formwork) was built against ledger revisions (r3 .. r5) and re-bound by research tasks, but no package wired a line family for it, and the railing census had no line home except the per-flight blank lines | book a derived trade as its own line family beside the member line it derives from, consuming the Checker-merged binding table unchanged and re-checking every bound member line on the candidate (a moved member stops the build); a census with no line home gets its own item code, never a relabelled one (PROJECT-INDEPENDENT) | tests/t199_formwork_metalwork (normal: villa V199 formwork 18.300 / 4.150 m2, railings 5.500 / 3.089, 2 pcs; adverse: stale binding, E as a line, OQ-10 valued, held as 0, S1, face twice, plan length relabelled, per-flight figure beside the runs) | PROPOSED |

## 10. r2 (Checker REJECTED r1 2026-10-31 02:58, gate f + Gate B regression): registry and guards only

NEEDS (a) / (b) / (c) of the r1 verdict, nothing else. No engine, tool or input file changed since r1 (`git diff --stat
ef92923c HEAD`: registry 1.25.0 and its builder, RULES_MANIFEST sha by the tool, tests, maps by the tool); no run reads
1.25.0 (rule_store reads 1.0.0, coverage_census_v2 1.1.0), so the 3,962 V3.0.29 + 661 added lines are byte-identical to
r1 (V3_0_30 json f90e8a66 / csv c8fd70f2) by construction.

(a) BOQ_FAMILY_MASTER_1.25.0 (builder FAMILY_MOVES, PROPOSED, the Checker confirms with the merge):

| Family | Item code now owned | Capability 1.24.0 -> 1.25.0 | Evidence (file:line, resolves) |
|---|---|---|---|
| B10-13 Formwork (all elements) | STR.FORMWORK | IMPLEMENTED_NOT_INTEGRATED (unchanged) | arch_v3030.py:80 FW_CODE, :352 fw_line(); test_arch_v3030.py:147 / :160 |
| B7-13 Stair formwork | STR.FORMWORK.STAIR | NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED | arch_v3030.py:80 FW_STAIR_CODE, :335 _fw_code(); test :147 / :302 |
| B6-05 Shutters | ARCH.SHUTTER | NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED | arch_v3030.py:464 shutter_lines(); test :198 / :337 |
| B7-10 Wall-mounted handrail | FIN.HANDRAIL (already) | NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED | arch_v3030.py:95 RAIL_KIND, :431 rail_line(); test :405 (new, V199 4.089 lm) |

IMPLEMENTED_NOT_INTEGRATED is the registry's definition of this case (tested code, read only by an opt-in method;
released_method_reads stays "none"). Name terms dropped on the moved families. Candidate blocks, in_v3_0_candidate,
development-villa figures unchanged (a pending package raises no candidate state; FMC check clean). Counts: NOT_IMPLEMENTED
18 -> 15, IMPLEMENTED_NOT_INTEGRATED 13 -> 16; RAISED 33 -> 36. B7-13 is moved too because STR.FORMWORK.STAIR is the stair
formwork family's own code (module docstring line 8); leaving it NOT_IMPLEMENTED while it owns a written code fails the guard.

(b) Guards: tests/t199_formwork_metalwork/test_family_master_1_25_0.py runs both t130 live-code guards at FULL strength on
1.25.0 (same helper functions, no exemption) + 8 of the 1.1.0 file checks (test_v3_0_field not carried: it already fails
on 1.24.0 for B7-14), adverse: ARCH.SHUTTER unowned refused, B7-10 back to NOT_IMPLEMENTED refused, a 'shutter' name term
hits shutter_lines(). The two 1.1.0 live-code checks are pinned to the 1.1.0 era: they exempt only codes 1.1.0 never mapped
that the governing (newest) registry owns in an implemented family, and only 1.1.0 NOT_IMPLEMENTED families the governing
registry moved with resolving file:line evidence, and only while the governing registry passes both guards itself (else
AssertionError); new adverse test: an unowned code is never exempt, a governor moved back exempts nothing. Not deleted, the
1.1.0 file-only checks untouched.

(c) L4 and maps: see the READY handoff (full suite on the r2 head vs research/agents_t202/known_failures.json); freeze 0;
codemap built by the tool, stale none.

Finding F-T199-4 (Lead, register owner; not changed here): the guard's code scan covers only STR / FIN / ARCH / MAS / DOOR
prefixes, so MET.RAILING.GUARD (roof / floor-edge guards, written by arch_v3030.py:82) is owned by no family and unscanned;
no family of the 99 fits it exactly (B7-09 is the stair guardrail). A registry change that names its family and widens the
scan to MET. is proposed for the Lead.
