# ALSENAN — Rebar Round 4: source exhaustion + carried-population re-audit

Baseline `487337c` (Round 3, frozen and untouched). Round 4 is a new candidate built on top of it. Architectural BOQ is
not touched. The freelancer total (44.19 t) is read **only** after the freeze, by
`post_freeze_rebar_comparison.py`, and it is reported as a finding, never as a target.

**Project status: `LOWER_BOUND_ONLY`.**
- `PROJECT_REBAR_FINAL_ESTABLISHED = false`
- `PROJECT_REBAR_PROCUREMENT_READY = false`

No single "total rebar" figure is shown anywhere.

## 1. What changed in the method

| Area | Round 3 | Round 4 |
|---|---|---|
| PDF detail values (pp. 8, 13–16) | carried V3a/V3b values, opaque | `VisualSourceClaim` per crop (`engine/source/visual_source_claim.py`). Each claim has a crop hash, OCR (tesseract 5.3.4), PDF vector geometry (`engine/pdf_vector_evidence.py`) and DXF where possible. The state is *derived*, so an AI-only reading is never VERIFIED. |
| Carried populations | 9 opaque populations (GB, ext GB, lintels, starters, boundary wall, dome, pool, residue, F/F10) | All 9 are rebuilt as component populations or retired; `carried_populations_remaining = 0`; budget kg = 0 |
| Slab bars | every bottom bar over span + embedment; drawn /Top bars over the whole panel | p.15 rules: 50 % of bottom bars stop 0.125 L short of a continuous support (that part is PROVISIONAL until continuity per panel is read); drawn top bars use their drawn extent |
| D5 columns (26) | all BLOCKED, audit kg | classified from storey evidence: 17 OFF_STOREY (NIS), 4 REAL (restored, lower bound), 2 several outlines (PROVISIONAL), 3 UNRESOLVED (no kg) |
| BBS | "BBS total" | `KNOWN_COMPONENTS_*_KG`, flagged as not procurement |

### Claim states (30 claims)

**CROSS_VERIFIED (16)** — at least 2 non-AI channels, at least one deterministic, and every facet covered:
- p.8: cover 25 / 70, slab 16 cm
- p.13: GB > 5 m / < 5 m / < 2.5 m bars / exterior; lintel schedule; boxed-bar existence; 40Ø starter projection
- p.14: lift values
- p.15: temperature table + notes; slab 0.25 L / 0.30 L / 0.125 L stop

**AI_VISUAL_TRANSCRIPTION (14)** — PROVISIONAL at most:
- p.8: note 9, note 19, note 21
- p.13: GB < 2.5 m section; lintel MIN.40 bearing; Min. 30 cm foot; deep-footing lower GB
- p.14: lift orientation, boundary-wall typical, parapets
- p.15: planted column; twisted column / casement
- p.16: stair, opening / ribs

The independent channel is the owner-relayed review named in the brief. It is used only for the facets the brief states.
- `human_claim_dependency_pct` = 0.11 % — the share of verified kg that would fall back to AI-only without the owner-relayed review.

## 2. Page findings

- **p.8:**
  - Cover is ≥ 25 mm for members and ≥ 70 mm against soil (Q-R3-13 cover is resolved).
  - Note 9's "70Ø tension / 40Ø compression" is the *development length of starter bars*. It is not hooks and not anchorage. The BBS uses 70Ø as a labelled lap *assumption* only.
  - Note 19: lift tie beams at 3.00 m when the storey is > 4.30 m. GF is 4.50 m, so they are required → a new BLOCKED population.
  - Note 21: side bars 2/3/4 Ø12 by width, but the mapping is not printed → PROVISIONAL.
- **p.13:**
  - The two lower 3Ø16 rows are real: vector dot rows count 3/3/3 (Q-R3-14 resolved). They are never de-duplicated.
  - `GROUND_BEAM_DETAIL_REGISTER` holds GT5, LT5, LT2_5 and EXT.
  - Of the 59 spans, 30 have an established governing detail and 29 are AMBIGUOUS (length basis or exterior evidence disagree). The V3 exterior flag disagrees with footprint adjacency on 27 spans. Verified kg is taken only where every candidate detail gives the same bars.
  - Lintel schedule (5 rows, 9 rules) is CROSS_VERIFIED. MIN.40 bearing is AI-only, so the bearing extension is PROVISIONAL.
- **p.14:**
  - Lift pit from DXF: 1.80 × 1.80 inner, 2.20 × 2.20 outer, 200 mm wall.
  - Components:
    - FF_FOOTING_MESH: verified lower bound
    - LIFT_PIT_BASE_2D16: partial
    - LIFT_PIT_WALL_12MM and LIFT_PIT_WALL_16MM: BLOCKED_DIMENSION, because the pit depth is "as per lift manufacturer"
    - OTHER_DETAIL_COMPONENTS: provisional
  - The boundary-wall typical detail (20×40 GB, 2Ø14 / 3Ø16, columns 20×30 4Ø14, pads 130×80×30) conflicts with schedule row B.W (20×60, 4Ø16 / 2Ø14). It is held as SOURCE_CONFLICT and no side is selected.
- **p.15:**
  - Temperature table is extracted exactly: 100 / 125 / 150 → Y10@200; 175 / 200 / 250 / 300 → Y12@200. Lap is 40Ø.
  - The villa slabs are 160 mm (GF, 1F) and 180 mm (2F). None is a table row → `SOURCE_RULE_NOT_EXACT_MATCH`, with no rounding. Three BLOCKED temperature populations are recorded with their candidate panels.
  - The slab rules compare against Round 3 as follows:
    - 111 rows OVERCOUNT
    - 4 MATCH_SOURCE
    - 2 UNCHANGED
  - As a result, verified slab steel goes from 5,019 to 4,190 kg, and 829 kg moves to provisional.
- **p.16:** the stair typical is READ as `TYPICAL_STAIR_DETAIL_SOURCE`, with applicability BLOCKED. G23 stays XFAIL.

## 3. Carried populations — old vs new (kg)

| Population | Old (R3) | New (R4) verified / provisional | Why |
|---|---|---|---|
| Ground beams (int + ext) | LB 1,253 + prov 2,977 | 2,114 / 1,755 | p.13 sections are CROSS_VERIFIED; per-span candidate envelope |
| Lintels | LB 582 / prov 44 | 374 / 271 | bearing AI-only → provisional; hooks BLOCKED |
| Column starters | prov 939 | 346 / 168 (+15 audit) | 40Ø projection verified; neck BLOCKED (founding level) |
| Boundary wall | prov 556 | 0 / 0 (BLOCKED) | schedule vs p.14 conflict |
| Domes | LB 2,054 / prov 25 | 1,264 / 833 | rise 1.72 / 2.15 (elevations) vs 1.90 (detail) no longer verified |
| Pool | LB 586 | 0 / 589 | AI mapping of the N.I.S. detail |
| Beam residue | budget 319 | audit 319 (BLOCKED) | no opaque kg |
| F/F10 | prov 63 | retired | duplicate of the blocked R3 pair |

## 4. Buckets (never summed into a project total)

| Bucket | kg |
|---|---|
| Verified complete | 48.9 |
| Verified lower bound | 20,366.2 |
| Provisional | 7,155.5 |
| Budget | 0 |
| Blocked / audit (never released) | 2,487.0 |

Populations by state:

| State | Count |
|---|---|
| BLOCKED | 42 |
| VERIFIED_COMPLETE | 4 |
| LOWER_BOUND | 289 |
| PROVISIONAL | 19 |
| NIS | 48 |

Scorecard: see `REBAR_ACCURACY_SCORECARD_V2.json`. Each metric is reported separately.

The known-components BBS (an audit only, **not procurement**):

| Measure | Value |
|---|---|
| Net | 20,415 kg |
| Used | 20,931 kg |
| Purchased | 21,424 kg |
| Waste | 493 kg (2.3 %) |

## 5. What worked

- OCR plus vector geometry corroborates printed values deterministically: dot rows for the ground-beam lower layers, table rules for row counts, dimension-line ratios for 0.125 L / 0.25 L / 0.30 L (measured 0.120 / 0.260 / 0.349), and DXF outlines for the lift pit.
- A derived-state claim cannot be promoted by hand. The tests caught a validator gap: the authority was compared with the stored state rather than the derived one. That is fixed.
- Splitting "read" from "applicable" lets the stair, deep footing, boundary wall and parapets be accounted without driving kg.
- D5 storey evidence restores 4 real columns: 295 kg verified, 266 kg provisional. 17 off-storey ones leave the scope without guessing.

## 6. What is not working

- Applicability, not reading, is now the bottleneck. Population completeness is 1.1 % and required-component completeness is 14.4 %, because anchorage / hooks, side bars, temperature steel, slab support continuity and the GB governing detail are still open.
- 29 of 59 ground-beam spans are ambiguous between length categories or interior / exterior.
- CB occurrences: only CB6 is accepted. CB3 / 4 / 5 / 8 / 12 have contradictions, and the CB2 / CB10 tags have no near band.
- The ground slab is still unresolved (G15). The second pass found 26 closed cells in FP-1 but only one holds the slab note.
- Three source conflicts are open: schedule SB2 duplicate, B.W vs p.14, and F/F10.

## 7. Recommendation for Round 5

1. Resolve the SOURCE_RESOLVABLE items first, from the drawings, before asking anyone:
   - slab support continuity per panel (Q-R4-9);
   - exterior ground-beam spans from the architectural wall layers (Q-R4-6);
   - a second deterministic channel for the AI-only p.13 notes (Q-R4-8).
2. Send **one** structural-engineer batch with only the remaining questions. The top 5 by kg impact are:
   - anchorage and hooks (Q-R3-4);
   - temperature steel for 160 / 180 mm (Q-R4-4);
   - boundary-wall conflict (Q-R4-5);
   - side bars (Q-R3-5);
   - the stair applicability (Q-R3-10).
3. Ask the owner / manufacturer for:
   - lift pit depth;
   - founding level;
   - dome rise.
4. Make the method decision (Q-R3-7a): per-metre counts. Under the end-bar convention, 698 more bars and +544 kg would move from provisional to verified.

## 8. Files

All registers are under `registers/`; `INDEX.json` holds the hashes and confirms the build was run twice with identical output:
- `VISUAL_SOURCE_CLAIM_REGISTER`
- `PROJECT_REBAR_RULE_REGISTER`
- `GROUND_BEAM_REBAR_V4`
- `TEMPERATURE_REBAR_RULE_REGISTER`
- `SLAB_DETAIL_RULE_REGISTER`
- `LIFT_REBAR_SOURCE_REGISTER`
- `CARRIED_POPULATION_REAUDIT`
- `CB_OCCURRENCE_CANDIDATE_REGISTER`
- `D5_COLUMN_SOURCE_RECONCILIATION`
- `GROUND_SLAB_SCOPE_REGISTER_V2`
- `ENGINEERING_QUESTION_TRIAGE_REGISTER`
- `PROJECT_REBAR_STATUS`
- `REBAR_ACCURACY_SCORECARD_V2`
- `KNOWN_COMPONENTS_BBS_REGISTER`
- `REBAR_POPULATION_REGISTER_V4`
- `REBAR_GATE_TRANSITIONS_R4`

Other files:
- `evidence/VISUAL_EVIDENCE_CAPTURE.json` — crop hashes, OCR and geometry. The crops themselves are git-ignored.
- `POST_FREEZE_REBAR_COMPARISON.json` — written after the freeze.

Tests: `tests/alsenan_rebar_source_exhaustion/test_rebar_r4.py`.
