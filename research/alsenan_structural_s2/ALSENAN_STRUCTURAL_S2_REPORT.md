# URBAN PROJECTS — GENERIC STRUCTURAL ENGINE — S2

## Engineering flags, source authority and review workflow

Alsenan / ST7757 is the first validation project only. All production logic is generic and lives in `engine/source/`. Alsenan facts live only in the adapter and its outputs.

What this round did not do:
- calculate any rebar kg;
- change the S1 census (it is read by sha256);
- touch the Round 3/4 rebar registers;
- integrate pricing.

---

## GENERIC CODE ADDED (project-independent)

| Module | What it does |
|---|---|
| `engine/source/structural_authority.py` | **SOURCE_AUTHORITY_MODEL**: six fact classes and 11 authority levels. The ordering is set per fact type (`MEMBER_TYPE`, `MEMBER_SECTION`, `REINFORCEMENT`, `SLAB_THICKNESS`, `DETAILING_METHOD`, `OCCURRENCE`) and can be replaced per project. Levels are grouped into tiers, and a disagreement inside one tier is `SOURCE_CONFLICT`, never a pick. Overrides by a higher tier are recorded. No candidates means `BLOCKED`; no fallback value is invented. |
| `engine/source/engineering_flags.py` | **ENGINEERING_FLAG_SCHEMA**: all requested fields, the 6 statuses with legal transitions, an append-only history, the 10 issue types and severities. Flags carry a stable content `flag_key` plus a display `flag_id` (STR-COL-001…). Release works per component: an open flag affects only the components that depend on the facts it touches. The summary produces the front-summary lines. |
| `engine/source/project_claims.py` | **PROJECT_CLAIM_SCHEMA**: a claim is bound to project + drawing revision + member scope. `ASSERTION` fills a gap; `ADJUDICATION` answers named flags, and the conflicting sources stay on record. Claims support supersession. Mismatched project, revision or scope is refused. |
| `engine/source/rule_promotion.py` | **RULE_PROMOTION_SCHEMA**: PROJECT_ONLY → GENERIC_CANDIDATE → GENERIC_APPROVED, or REJECTED. Promotion needs an explicit `propose()` with a project-free statement; project terms are rejected. Approval needs a written review by someone other than the proposer. Only approved rules can be consumed. |
| `engine/source/question_helper.py` | **QUESTION_HELPER_SCHEMA**: a consultant block and a help-mode block for Mohammad, built only from the flag's source context. Includes a plain-language glossary and AutoCAD steps (FIND text with DXF codes shown as displayed, select by handle, LAYISO, ZOOM). |
| `engine/source/flag_detectors.py` | 22 generic detectors, each a *condition* over a project-independent review-view shape (see below). |

The 22 detectors (no Alsenan IDs are written anywhere):
- Equal-authority type disagreement.
- Section override or conflict.
- Value on an uncovered band limit.
- Table row missing (no interpolation).
- Below a rule minimum.
- Duplicate schedule key.
- Two marks on one drawn member.
- Schedule field with unstated meaning.
- Continuous-beam span mismatch.
- Ambiguous mark binding.
- Untyped members.
- Member type existing at one level only.
- Member missing on one plan.
- Required by rule but not drawn.
- Population depending on a non-exact rule.
- Per-metre transverse count on a multi-tie band, and transverse zone not established.
- Schedule bar count different from the detail sketch.
- Class depending on the length basis.
- Overlapping outlines.
- Rule-versus-rule conflict.
- Missing geometry.
- Schedule row with no plan occurrence.

**Generic tests:** `tests/structural_review_engine/test_review_engine.py` has 15 synthetic tests and uses no project coordinates, marks or totals. It covers:
- the brief's 10 cases: plan vs local type; single-floor member; uncovered boundary; local overrides default; equal authorities conflict; claim resolves a conflict; no leakage to another project or revision; known component releasable while the unknown one is blocked; resolved flag keeps its history; no automatic promotion;
- shared-field type conflicts;
- question and help generation;
- deterministic IDs;
- a firewall check that the generic modules contain no project names, marks or grid references;
- schema completeness.

**Schemas exported:** `research/structural_engine_s2/*.json` (ENGINEERING_FLAG_SCHEMA, SOURCE_AUTHORITY_MODEL, PROJECT_CLAIM_SCHEMA, QUESTION_HELPER_SCHEMA, RULE_PROMOTION_SCHEMA), written by `write_schemas.py`.

---

## ALSENAN PROJECT DATA GENERATED

`research/alsenan_structural_s2/build_flags_s2.py` reads the frozen S1 registers, after checking their hashes. It maps them into the generic review view (`ALSENAN_REVIEW_VIEW.json`) and runs the generic engine.

### Outputs

| File | Content |
|---|---|
| `ALSENAN_ENGINEERING_FLAGS.json` | 71 flags, with source refs, interpretation, release effect and answer options |
| `ALSENAN_CONSULTANT_QUESTIONS.md / .json` | one consultant block per open flag |
| `ALSENAN_REVIEW_HELPER.md / .json` | help mode for Mohammad (terms, where to look, AutoCAD steps, effect of each answer) |
| `ALSENAN_PROJECT_CLAIMS.json` | claim store; empty until answers arrive |
| `ALSENAN_RULE_PROMOTION_REGISTRY.json` | empty registry plus 3 lessons that could be proposed after an answer, all PROJECT_ONLY |
| `ALSENAN_FACT_CLASSIFICATION.json` | which S1 content is SOURCE_FACT, DERIVED_GEOMETRY, PROJECT_RULE etc. |
| `ALSENAN_COMPONENT_RELEASE.json` | release state per element component, on the census measured basis (nr / m / m²), no kg |
| `ENGINEERING_FLAGS_SUMMARY.md / .json` | discipline, status, effect and front-summary lines |

### Flags (structural)

There are 71 flags: 47 OPEN and 24 PROVISIONAL_INTERPRETATION.

| Breakdown | Counts |
|---|---|
| Release effect | 31 blocked, 10 audit-only, 4 lower bound, 21 provisional, 5 no quantity impact |
| Issue type | SOURCE_CONFLICT 30, AMBIGUOUS_APPLICABILITY 17, MISSING_DIMENSION 7, UNBOUND_OCCURRENCE 6, MISSING_SCHEDULE 4, RULE_GAP 3, MISSING_DETAIL 2, ENGINEERING_METHOD_REQUIRED 2 |
| Severity | 8 high, 47 medium, 16 low |
| Trade | Concrete 53, formwork 50, reinforcement 67, other 1 |

Front summary (generated): "71 structural flags open · 67 affect reinforcement · 53 affect concrete · final quantity pending consultant = yes". The flag-summed quantities double-count elements that appear in several flags, so the de-duplicated picture is the component release below.

### Brief item → generic condition that produced it

| Brief item | Flag(s) | Condition |
|---|---|---|
| X04-Y01 C3 vs C | STR-COL-009 | equal-authority plan tags disagree |
| X12-Y02 C8 vs C7 | STR-COL-010 | same condition; the 30X80 size label corroborates C7 |
| CN axis / foundation distinction | STR-COL-001, STR-COL-011 | type exists at one level only; member missing on one plan |
| C7 at L = 80 cm | STR-COL-008 | value on a band limit no band includes; only the two adjacent bands are offered |
| 6Ø8/m sets vs single ties | STR-COL-002 | per-metre count on a multi-tie band |
| Tie vertical zone | STR-COL-007 | transverse zone length not established |
| Schedule bars vs detail sketch | STR-COL-003…006 | bar count differs from the band sketch |
| GF columns 20 cm < Tmin 25 | STR-COL-023 | below a rule minimum (schedule kept, provisional) |
| Drawn outline vs schedule | STR-COL-012…022, STR-BEA-012…016 | section override (provisional) |
| F / F10 | STR-FOO-005 | two marks on one drawn member |
| BOXED notation | STR-FOO-001 | schedule field with unstated meaning; only that component is blocked |
| Duplicate SB2 | STR-BEA-022 | duplicate schedule key; drawn width given as a hint only |
| Continuous-beam mismatches | STR-BEA-018…021 | span count or length mismatch, never forced |
| B3 (With Stair) vs CB3 | STR-BEA-017 | two marks on one drawn span |
| Ambiguous / untagged beams | STR-BEA-023…028, STR-BEA-008…011 | mark binding ambiguous; members without a mark |
| GB length basis | STR-BEA-001 | class depends on the length basis |
| Temperature table 160 / 180 mm | STR-SLA-002, STR-SLA-003 | no exact table row |
| Plan-note top bars vs p.15 | STR-SLA-001 | applicability of a candidate rule |
| Ground-slab scope | STR-GRO-001 | extent not drawn → lower bound |
| Stair-detail applicability | STR-STA-001 | blocked-method rule over the stair zones, including the stair inside the void |
| Lift pit / lift tie beam / lintels | STR-LIF-001, STR-LIF-002, STR-LIN-001 | missing dimension; required by rule but not drawn |
| Founding level / lower GB | STR-FOO-003 | missing dimension |
| Beam widening for services | STR-BEA-007 | extent unknown → concrete lower bound |
| Deep-beam side bars | STR-BEA-005 | method required |
| Boundary wall, formwork days | STR-PRO-001, STR-PRO-002 | rule-versus-rule / rule-versus-schedule conflict |
| Parapets, pool, curved GBs | STR-PAR-001, STR-POO-001, STR-BEA-006 | missing geometry |
| Domes, planted / turned columns | STR-DOM-001, STR-PLA-001, STR-TUR-001 | applicability of candidate details |
| Unused schedule rows (F7, B10, B12, B.W) | STR-FOO-002, STR-BEA-002…004 | schedule row with no occurrence |

### Release behaviour (examples from the census, no kg)

- **Columns:** MAIN_BARS released on 90 of 95 occurrences (blocked on 5 because of the two type conflicts). TIES blocked on all 95 (per-metre semantics and zone). CONCRETE released on 61, provisional on 29, blocked on 5.
- **Footings:** MAIN_BARS released on 25 of 26. The BOXED component is blocked on the 17 footings that print a BOXED value; the 9 without one stay verified.
- **Beams:** MAIN_BARS released on 166 of 211 spans; ambiguous or untagged spans are audit-only. Concrete is a lower bound on 113 bound slab-beam spans (possible 5 cm widening for services).
- **Slabs:** temperature steel blocked on 49 panels (no 160 / 180 mm table row). The ground-slab extent makes those cells a lower bound.

Nothing is forced to zero: on many elements a blocked component sits beside released ones.

---

## What worked / what is not working / recommendation

**Worked**
- Every brief item came out of a generic condition. The engine modules pass a firewall test against project names, marks and grid references.
- A column type conflict blocks the type-dependent bars. Concrete is blocked as well here, because the candidate types' sections differ; a shared section would leave concrete released, and the synthetic tests show this.
- The authority model keeps "schedule overrides drawing" visible for review (provisional), instead of silently winning.

**Not working / limits**
- The summed affected quantity counts an element once per flag. Use `ALSENAN_COMPONENT_RELEASE.json` for de-duplicated figures.
- The measured basis is counts / metres / m², not weight. Component weights arrive with the rebar round.
- Grouping is a judgement: 71 flags, several grouped (for example 11 section-override flags per column type). A reviewer may prefer coarser groups.
- No ARCHITECTURAL or MEP flags yet; the model supports them, but no adapter feeds them.

**Recommend next**
1. Mohammad reviews `ALSENAN_REVIEW_HELPER.md` and sends `ALSENAN_CONSULTANT_QUESTIONS.md` (HIGH first: tie semantics, tie zone, C7 band, two type conflicts, F/F10, SB2).
2. Record the answers as ADJUDICATION claims, re-run, and confirm the flags move to RESOLVED with history kept.
3. Only after that: the member-geometry round, then rebar consuming the resolved facts.
