"""R8.3 package markdown (used by r8_3_package.py). Every number is read from the inputs."""

from __future__ import annotations


def _tbl(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def documents(commit, counts, by_dir, attrs, red, real, prov, ef, rows, path_map):
    P = real["projects"]
    d = red["defect"]
    tr = red["projects"]["ALRASHED"]["text_delta_review"]
    ef_classes = {}
    for e in ef["expected_failures"]:
        ef_classes[e["class"]] = ef_classes.get(e["class"], 0) + 1
    total = sum(counts.values())
    docs = {}

    docs["00_EXECUTIVE_SUMMARY"] = f"""# URBAN QTO R8.3: executive summary

Commit `{commit}`. Base: `d3da02e` (R8.2 approved). **Mode: SHADOW.**
- cad_adapter, the published BOQ, frozen owner answers, benchmark targets and the Al Rashed takeoff are all unchanged.
- No module outside `engine/source` consumes the new frame records.

| Topic | Result |
|---|---|
| Original DWGs | All three are present in the session uploads. R8.2 wrongly said Al Rashed and Qortuba had none: its search looked only in repo paths. |
| Pinned re-decode | P7757 and Qortuba: **byte-identical**. Al Rashed: identical except **40 U+FFFD text rows**, reviewed row by row (EXPLAINED_DELTA, with its own text impact). |
| Handle defect | **{d['id']}**: reproduced on {d['reproduction_count']} sources by the pinned binary. Not localised to the parser, the internal representation or the JSON writer. |
| Decoder pins | Historical decodes are now **REPRODUCED_BY_REGISTERED_BUILD**. Build status is BUILD_CONFIGURATION_NOT_FULLY_RECORDED (configure line and CFLAGS recovered). |
| Block lineage | R8.2 gap fixed: one identity contract, and every INSERT gets exactly one lineage row. 10 required tests plus a mutation test. |
| UNIT_CONTEXT / REGION / FRAME | Implemented in `engine/source/frame.py`. The frozen R8 thresholds are unchanged, and their provenance gap is recorded. |
| Evidence | Formal lineage independence. Set-valued evidence fails closed. DIMLFAC evidence is candidate-only. Plausibility raises a question, never a status. Agents cannot admit evidence or set status. |
| CAD_PROFILE | Scoped requirements A–I. Parser-independence policy B is stored as data. A method must declare `scale_dependent`. |
| Al Rashed | UNIT_CONTEXT **{P['ALRASHED']['unit_context']['status']}**, frame **{P['ALRASHED']['frame']['status']}** → {P['ALRASHED']['frame']['allowed_use']} |
| P7757 | UNIT_CONTEXT **{P['P7757']['unit_context']['status']}**, frame **{P['P7757']['frame']['status']}** → PREVIEW only |
| Qortuba | UNIT_CONTEXT **{P['QORTUBA']['unit_context']['status']}**, frame **{P['QORTUBA']['frame']['status']}** → PREVIEW only |
| Independent DXF | **{real['INDEPENDENT_REAL_RECONCILIATION']}**. No real K1/K2 comparison is claimed. |
| R8.0 ratchet | 22 frozen contracts moved TARGET_NOT_IMPLEMENTED → PASS. F17 and MT-32 are **CONTRACT_DISPUTED**; their frozen expectations are unchanged. |
| Column | Question A: the column polygon **is closed per source** (170/170). Question B: **TRADE_DEDUCTION_RULE_UNDECIDED**. |
| Final suite | {counts.get('passed', 0)} passed, {counts.get('xfailed', 0)} xfailed, {counts.get('skipped', 0)} skipped, {counts.get('failed', 0)} failed, {counts.get('errors', 0)} errors ({total}) |
| **MIGRATION_READY** | **NO** |

STOP AFTER R8.3. No migration and no R9 work has been started.
"""

    docs["01_R8_2_HARDENING"] = f"""# 01: R8.2 hardening

## 1. Handle-truncation attribution (§3, clarification 1)
The neutral name **OBSERVED_HANDLE_TRUNCATION_IN_EXISTING_LIBREDWG_JSON** is promoted to
**{d['id']}**. The promotion rests only on the pinned reproduction:
- route: {d['route']};
- binary sha256: `{d['binary_sha256']}`;
- reproduction count: {d['reproduction_count']} ({', '.join(d['reproduced_on'])}).

""" + _tbl(["source", "source DWG sha256", "output sha256", "3-byte handles printed 16-bit", "colliding values",
            "affected refs (absolute, resolved by size)", "affected refs (relative, untrusted)"],
           [[p, v["source_sha256"][:16] + "…", v["output_sha256"][:16] + "…", v["handles_3_byte_printed_16_bit"],
             v["colliding_handle_values"], v["affected_references"].get("absolute_resolved_by_size"),
             v["affected_references"].get("relative_untrusted")] for p, v in d["per_project"].items()]) + f"""

Localisation: {d['localisation']}. The defect is **not** attributed to "LibreDWG's JSON writer".
Commands are in PINNED_REDECODE_RESULTS.json (`defect.per_project.*.command`).

## 2. Block-lineage reconciliation gap (§5–§7)
**The gap was real.** R8.2 compared lineage with `insert_blocks_b.get(ins)`, which had two failures:
1. a truncated D1 INSERT (`v+3B`) never matched the full D2 handle, so its lineage was **silently skipped**;
2. an exact INSERT whose D1 block record was truncated compared `'v+3B' != 'full'`, a **false BLOCK_LINEAGE conflict**.

The fix (`engine/source/reconcile.py`) uses one identity contract, `handle_basis(x, y)`, for entity keys,
instance-path elements, INSERT handles and block-record handles. There is no raw string comparison anywhere.
Every INSERT on either side yields exactly one row:
- PASS
- BLOCK_LINEAGE_CONFLICT
- UNMATCHED_INSERT_LINEAGE
- AMBIGUOUS_INSERT_LINEAGE
- AMBIGUOUS_BLOCK_RECORD_LINEAGE

Names are carried for audit only (BLOCK NAME ≠ BLOCK IDENTITY).

D1 `insert_blocks` now also includes other-layout INSERTs, as K2's always did.

Tests: `tests/r8_3/test_r8_3_lineage.py` covers the ten required cases, plus:
- lineage requires both sides;
- one row per INSERT;
- names never enter identity;
- **a mutation test that disables low-bit correlation**, and a test re-creating the R8.2 behaviour to show it skipped and falsely conflicted.

All R8.2 synthetic K1/K2 scenes still PASS under the stricter lineage.
"""

    rows_txt = [[r["handle"], r["entity"], r["layer"], r["field"], repr(r["historical_string"])[:40],
                 r["pinned_raw_bytes_hex"], r["readings"]["cp1252"]] for r in tr["rows"]]
    docs["02_PINNED_LIBREDWG_REDECODE"] = f"""# 02: Pinned LibreDWG re-decode (§3, §4, §27)

Decoder: `{red['decoder']['path']}`, sha256 `{red['decoder']['sha256']}`, reported `{red['decoder']['reported_version']}`,
pin **{red['decoder']['pin_status']}**. Platform: {red['platform']}.

Build provenance: **{red['build_provenance']['status']}**.
- Recovered from `/tmp/ldwg/config.log`: `{red['build_provenance']['configure_invocation']}`, CC={red['build_provenance']['CC']}, CFLAGS={red['build_provenance']['CFLAGS']}, host={red['build_provenance']['host']}.
- Not recorded: compiler version, libc, source tarball hash.

The historical JSON was not touched. New artifacts are in `data/runs/pinned_redecode/`.

""" + _tbl(["project", "DWG sha256", "status", "byte identical", "after UTF-8 normalisation", "handle attribution", "SRD same", "census same"],
           [[p, (r.get("source_sha256") or "")[:16] + "…", r["status"], r["comparison"]["byte_identical"],
             r["comparison"]["identical_after_utf8_replacement_normalisation"], r["handle_truncation_attribution"],
             r["comparison"]["field_comparison"]["srd"], all(v == "SAME" for v in r["comparison"]["field_comparison"].values())]
            for p, r in red["projects"].items()]) + f"""

Duplicate uploads are byte-identical to the file used: two Al Rashed copies, two Qortuba copies, and P7757 in both the repo and the uploads.

## The 40 text differences (clarification 2)
Al Rashed is **not** "exactly identical". The pinned output contains {tr['invalid_sequences_in_pinned']} bytes that are not
valid UTF-8, and the historical file replaced each with U+FFFD.

The cp1252 readings are {tr['rows_by_reading']}:
- 37 × `²` in `m²` area markers;
- 1 × `°`;
- 2 × `î` inside legacy-font Arabic strings.

**Reason:** {tr['rows'][0]['reason']}.

**Consumers**
- active: {tr['consumers']['ACTIVE']};
- future: {tr['consumers']['FUTURE']}.

**Impact:** {tr['impact']}; the finding is {tr['finding']}.

Geometry effect: {tr['geometry_effect']}. Classification: {tr['classification']}.

""" + _tbl(["handle", "entity", "layer", "field", "historical", "pinned byte", "cp1252"], rows_txt) + "\n"

    docs["03_UNIT_CONTEXT"] = """# 03: UNIT_CONTEXT

`engine/source/frame.py` answers one question: what does one coordinate unit mean in one coordinate space?

**Coordinate spaces.** There is **exactly one UNIT_CONTEXT per coordinate space** (U-1): MODEL_SPACE, a PAPER_LAYOUT,
and later a PDF_PAGE or RASTER_PAGE. `FrameRegistry` refuses a second one. Evidence scoped to a region is rejected
(UNIT_REDEFINITION_REJECTED): a detail may not redefine the native unit.

**Record fields:** unit_context_id, source_sha256, coordinate_space_id / kind, declared_unit_code / name / native_to_mm,
status, native_to_mm (the value the status stands behind, or None), status_reason, machine_status,
machine_support, evidence_ids, excluded_evidence (id, why), contesting_candidates, confirmation, allowed_use, findings.

**INSUNITS is declaration evidence.** `declaration_evidence()` turns it into a DECLARATION item. It is never
physical truth, and INSUNITS 0 or absent infers nothing (UNIT_DECLARATION_UNITLESS).

**Status rule** (frozen spec §5): VERIFIED / CONFIRMED_BY_HUMAN / PROVISIONAL / UNCONFIRMED / CONFLICT / BLOCKED.
- VERIFIED needs at least 2 independent classes of different non-plausibility kinds agreeing within 0.5 %, no contradiction, and passing checked-dimension residuals.
- If 2 or more agreeing classes overrule the declaration, the result is PROVISIONAL.
- A declaration contradicted by one class is a CONFLICT.
- Candidate evidence may **lower** a status to CONFLICT, never raise one.
- Plausibility never moves a status; it raises UNIT_PLAUSIBILITY_QUESTION.

**Human confirmation** (exact source hash, author, timestamp) gives CONFIRMED_BY_HUMAN, never VERIFIED.
Under `URBAN_FRAME_RELEASE_V1` it supports FINAL only when it:
- contradicts no admitted evidence and no constraint set; and
- has at least one non-human item agreeing with it.

So a human may resolve a *declaration* conflict, but never overrides evidence and never confirms in a vacuum.
A confirmation for another source hash is inadmissible (HUMAN_CONFIRMATION_SOURCE_MISMATCH).

**Agents** may only add CANDIDATE evidence. An agent item marked ADMITTED is excluded (AGENT_STATUS_ESCALATION_REJECTED),
`FrameRegistry.set_status` always raises, and the records are frozen dataclasses.

**Generic for DWG / DXF / PDF / raster.** The space kind is data; evidence kinds include SCALE_BAR,
PAPERSPACE_VIEWPORT_SCALE, OTHER_SOURCE_DOCUMENT, KNOWN_PLOT_DIMENSION and HUMAN_CONFIRMATION. The PDF and raster
*validation profiles* are not approved, so their regions are capped below FINAL.
"""

    docs["04_UNIT_EVIDENCE_INDEPENDENCE"] = """# 04: Unit-evidence independence

**Independence is formal, never a flag.** Every item carries a failure-domain `lineage`, and items that share any
relevant lineage element form ONE class (union-find). The element types are:
- AUTHORED:<fact>
- TRANSCRIPTION:<model/run>
- DOCUMENT:<sha>
- FAMILY:<family>:<sha>
- PRIMITIVE:<x>
- HUMAN:<who>
- PARSER:<lib>
- ASSUMPTION:<what>

**Families.** Everything one drafter *typed* into one drawing is ONE family (DOCUMENT_SOURCE), however many styles
or notes carry it (R8.0 MT-28). A DIMSTYLE factor is a separate family (DIMENSION_STYLE; F26 needs two families).

| rule | effect |
|---|---|
| the same INSUNITS read by LibreDWG and by ezdxf | one class: they share `AUTHORED:<sha>:HEADER.INSUNITS` |
| the same OCR / model run twice | one class: they share `TRANSCRIPTION:<model>@<cfg>` |
| two dimensions of one DIMSTYLE | one class: shared style |
| a PDF plotted from the DWG, a raster render of a vector page | one class: shared `PRIMITIVE:`; reported SHARED_SOURCE_PRIMITIVE |
| an auto dimension | CIRCULAR_WITH_MEASURED_GEOMETRY: carries no unit or scale information |
| plausibility ("villa looks 15 m wide") | support-only: never counted, may raise a QUESTION |
| an assumption-bearing item | CANDIDATE: may lower to CONFLICT, never raise |
| PARSER:* | recorded, but ignored for the unit and scale questions: a parser defect cannot make two different authored facts agree |

## Set-valued evidence fails closed (clarifications 3–4)
A dimension family gives a *ratio* (display ÷ geometry). With no authored display unit, it implies one native
interpretation per standard display unit {mm, cm, m, in, ft}: **a set**.
- The set establishes only the set.
- Sets intersect deterministically. An empty intersection gives CONFLICT. More than one member gives no support.
- A singleton reached by independent sets is ONE class.
- **A declaration that is a member of the set is never support.** P7757 and Qortuba stay UNCONFIRMED for exactly this reason.
- No AI picks the "most plausible" member.

Tests: `tests/r8_3/test_r8_3_frame.py` (A–L, sets) and `tests/r8_3/test_r8_3_unit_evidence.py`.
"""

    docs["05_REGION_MEASUREMENT_TRANSFORM"] = """# 05: REGION_MEASUREMENT_TRANSFORM

This record answers: how does this drawing region relate to the real building?

Fields: region_transform_id, unit_context_id, region_id, region_kind, parent_region_id, bounds, matrix (2×3),
local_scale, rotation_rad, reflection, reference, status, status_reason, evidence, allowed_use.

| case | behaviour |
|---|---|
| A. model-space plan, **reference** region | full size *by definition* (it defines the unit): VERIFIED unless region evidence contradicts it |
| model-space plan, not the reference | carries the full-size medium convention as a DECLARATION: UNCONFIRMED until it earns its scale |
| B. model-space enlarged detail | same UNIT_CONTEXT; local scale from region evidence; **no evidence gives BLOCKED (U-2)** |
| C. paper-space viewport | ANNOTATION_MAPPING / COUNT_ONLY only; refusal MEASURE_IN_MODEL_FRAME; never measurement authority |
| D. vector PDF region | schema exists; profile not approved; ceiling PREVIEW |
| E. raster region | PREVIEW only |

Rotation and reflection are decomposed from the matrix. A non-uniform region scale is a CONFLICT.
Tests `test_1` … `test_12` in `tests/r8_3/test_r8_3_frame.py` cover all twelve §36 cases.

Real sources: each model space is one unsegmented MODEL_SPACE_WHOLE region, with no reference designated,
so each is UNCONFIRMED by convention.
- Al Rashed also raises REGION_MIXED_SCALE_NOTES twice: scale notes 1:100/1:200/1:500/1:2000, and two dimension families (ratio 100 and ratio 1).
- Region segmentation is future work.
"""

    docs["06_MEASUREMENT_FRAME"] = """# 06: MEASUREMENT_FRAME

MEASUREMENT_FRAME = UNIT_CONTEXT + REGION_MEASUREMENT_TRANSFORM.

**Composition:** the frame is no stronger than its weakest required component. The strength order is
VERIFIED > CONFIRMED_BY_HUMAN > PROVISIONAL > UNCONFIRMED > BLOCKED > CONFLICT. CONFIRMED_BY_HUMAN ranks below
VERIFIED, so a human component always shows in the frame status. The composition is tested for all 36 status pairs.

| status | FINAL_MEASUREMENT | PREVIEW_MEASUREMENT | COUNT_ONLY | ANNOTATION_MAPPING |
|---|---|---|---|---|
| VERIFIED | ✓ | ✓ | ✓ | ✓ |
| CONFIRMED_BY_HUMAN | only under URBAN_FRAME_RELEASE_V1 | ✓ | ✓ | ✓ |
| PROVISIONAL / UNCONFIRMED | – | ✓ (if a value exists) | ✓ | ✓ |
| CONFLICT / BLOCKED | – | – | ✓ | – |

Region-kind caps apply on top. A frame with no established value cannot even PREVIEW.

**Counts.** A count may proceed only when its method **declares** `scale_dependent = False`. An undeclared method is
never assumed count-only.
"""

    docs["07_CAD_VALIDATION_PROFILE"] = """# 07: CAD validation profile (§22, §41)

`engine/source/cad_profile.py`. A measurement is FINAL-eligible only if every applicable requirement passes:

| id | requirement | domain |
|---|---|---|
| A | capability row permits the use | GEOMETRY / IDENTITY |
| B | D1 mapping VERIFIED* | GEOMETRY_COMPLETENESS |
| C | conservation balanced; decode pin REGISTERED / REPRODUCED | SOURCE_COMPLETENESS |
| D | K1 realised cleanly, and the parser-independence policy holds | GEOMETRY |
| E / F / G | unit / region / frame permit FINAL | MEASUREMENT_FRAME |
| H | no **in-scope** finding BLOCKING in a domain the method depends on | per finding |
| I | downstream geometry supports the kind | DOWNSTREAM_SUPPORT |
| METHOD | `scale_dependent` declared | – |

**Scoped.** A finding counts only if it is on this observation, its instance path, the measured region, or is a
document-wide finding. An OLE in a title block does not block a floor. A count method (`scale_dependent = False`)
skips E–G and I. IDENTITY and SEMANTICS count only when the method requires identity.

**Independence of the gates.** Good geometry never cures bad units, because E–G are independent of A–D and H.
Verified units never cure XREF, unsupported or custom geometry. Both directions are tested.

**Parser-independence policy B** (data: `ParserIndependencePolicy`). An independent parser is required when:
- a parser-risk finding is in scope; or
- the pin is not REGISTERED or REPRODUCED; or
- the work is benchmark qualification or the first migration consumer.

Otherwise a *qualified* decoder build suffices. `qualified_builds` is empty today, so B behaves as A.

**qs_core boundary (§40).**
- qs_core consumes: frame status, allowed use, blocking requirements with their domains, profile result, evidence ids.
- It never consumes: raw INSUNITS, raw viewport scale, or decoder detail.
"""

    docs["08_RECONCILIATION_LINEAGE_FIX"] = ("# 08: Reconciliation lineage fix\n\n## "
                                             + docs["01_R8_2_HARDENING"].split("## 2. ")[1])

    docs["09_INDEPENDENT_REAL_DXF_REPORT"] = f"""# 09: Independent real DXF

**INDEPENDENT_REAL_RECONCILIATION = {real['INDEPENDENT_REAL_RECONCILIATION']}**

`P7757_AUTOCAD_2018_INDEPENDENT.dxf` was not provided. The repository and the session uploads were searched and
found: {real['independent_dxf_found'] or 'nothing'}.

Having the three original DWGs fixed the pinned re-decode, but **it does not create parser independence**.
LibreDWG DWG → LibreDWG DXF → ezdxf remains SHARED_PARSER_LINEAGE, and R8.2 showed that route fails in ezdxf anyway.

When the file arrives, the run is already prepared:
- record the original DWG sha256 (`7f61f3ac…`), the DXF sha256, the exporter and version, the DXF format, and Mohammad's confirmation (no explode, purge, audit, scale change or cleaning);
- run D1/K1 vs D2/K2 with the **already-declared REAL tolerance** (`reconcile.real_tolerance`, R8.2; no retuning);
- apply the R8.3 lineage fix;
- report the census, conservation, correlation bases, every non-PASS source handle, and the unit declaration as each parser read it.

No real verdict is claimed.
"""

    docs["10_ELLIPSE_DOWNSTREAM_POLICY"] = """# 10: Ellipse downstream policy

- K1 and K2 keep the exact `RealisedEllipticalArc`. SOURCE_GEOMETRY_EXACT = true.
- DOWNSTREAM_MEASUREMENT_SUPPORTED = false, because the current stack has no elliptical primitive. CAD_PROFILE requirement I fails, so a scale-dependent measurement is PREVIEW at most. The capability row allows PREVIEW only.
- **Nothing is flattened in R8.3.**
- **Chord tolerance does not belong in MEASUREMENT_FRAME.** The frame states what physical distance a coordinate relationship represents; curve approximation states how accurately an exact curve may be discretised for one algorithm. These are different authorities with different revision cycles.
- Recommendation: an R11 `CURVE_APPROXIMATION_POLICY` (physical-error tolerance in mm, method, revision) that *consumes* a verified frame, since mm tolerances need one.
"""

    col = P["ALRASHED"].get("column_question_A", {})
    docs["11_COLUMN_MEASUREMENT_DECISION"] = f"""# 11: Al Rashed column / floor decision (§33–§35)

`pa09/alrashed/geometry.py` was **not modified**.

## Question A: physical geometry (a source question)
Is the column polygon physically closed? **Yes, per source.**
- {col.get('source_closed_flag_512')} of {col.get('lwpolylines')} `{col.get('layer')}` LWPOLYLINEs carry the DWG closed flag (512).
- {col.get('flag_bit_1_set_on_closed')} of them carry bit 1, which is the bit the project reader tests.
- K1 realises the closing span on {col.get('k1_realises_closing_span')}.

The reader's missing closing edge is a **source-reader defect**:
SOURCE_GEOMETRY_CORRECTION_IDENTIFIED.

## Question B: trade measurement (a rule question)
Should a permanent column footprint be deducted from floor finish? **TRADE_DEDUCTION_RULE_UNDECIDED.**
- Source parsing never answers this.
- No rule was implemented: not "always", not "never", no area or width threshold.
- A future rule belongs in versioned rules-as-data (rule_id, authority, scope, trade, basis, threshold, unit, revision, effective date). That is R9.

## Two quantity bases (recorded, neither published)
- **NET_INSTALL_AREA**: the finishable physical surface after physical obstructions.
- **BILLING_MEASUREMENT_AREA**: the contractual / selected measurement-method area.

They may be equal, or intentionally differ. The R8.2 shadow values are **not** published:
- 146.97 m² is the published row;
- 146.7697 m² is the geometry-corrected net.

## Answer
The 0.2003 m² difference involves **both layers**. The geometry correction is a source fact; whether it changes the BOQ is a trade rule.
"""

    rows_s = [[p, r["UNIT_CONTEXT_STATUS"], r["REGION_MEASUREMENT_TRANSFORM_STATUS"], r["MEASUREMENT_FRAME_STATUS"],
               ", ".join(r["ALLOWED_USE"]), r["HISTORICAL_DECODER_PIN_STATUS"], r["PINNED_REDECODE_STATUS"],
               r["HANDLE_REPRESENTATION_STATUS"]] for p, r in rows.items()]
    ex = {p: P[p]["unit_context"] for p in P}
    docs["12_REAL_PROJECT_STATUS"] = f"""# 12: Real-project status (§28–§30, §42)

Each source is evaluated from its **own** evidence only. No interpretation is transferred between projects, and no
project is upgraded because its quantities "look right". The full records are in REAL_PROJECT_R8_STATUS.json.

""" + _tbl(["project", "UNIT_CONTEXT", "REGION", "FRAME", "allowed use", "historical pin", "pinned re-decode", "handles"], rows_s) + f"""

## Al Rashed: **{ex['ALRASHED']['status']}**
- INSUNITS = 1 declares **inch**.
- 504 authored dimensions display 100 × their geometry. Under every standard display unit that family implies
  {{100, 1000, 100000, 2540, 30480}} mm per unit, and **25.4 is not among them**. The family therefore contradicts the declaration.
- 7 more dimensions (Standard style, ratio 1) are compatible with inch. That is membership, not support.
- No admitted physical evidence exists: the family is candidate-only, and plausibility does not count.
- Result: {ex['ALRASHED']['status_reason']}. Allowed use: {ex['ALRASHED']['allowed_use']}.
- The R7 reader's metres are not admissible as they stand.
- Route to FINAL: Mohammad confirms "`299c61b1…` DWG: 1 unit = 1 metre" (HUMAN_CONFIRMATION, exact hash). The value is consistent with the family set, so under URBAN_FRAME_RELEASE_V1 it would permit FINAL for the unit component. The region must still be segmented or confirmed.

## P7757: **{ex['P7757']['status']}**
- INSUNITS = 4 declares **mm**.
- 386 dimensions at ratio 0.1 imply {{0.1, 1, 100, 2.54, 30.48}}. The declared 1 mm is a member, which is **not support**.
- Result: {ex['P7757']['status_reason']}, PREVIEW only.

## Qortuba: **{ex['QORTUBA']['status']}**
- INSUNITS = 5 declares **cm**.
- 101 dimensions at ratio 1.0 imply {{1, 10, 1000, 25.4, 304.8}}. The declared 10 mm is a member, which is **not support**.
- Result: {ex['QORTUBA']['status_reason']}, PREVIEW only.

## Blockers common to all three
- CAD_PROFILE D (no qualified decoder build; no independent-parser reconciliation);
- E–G (frame not FINAL);
- for ellipses, A and I as well.

Source conservation is balanced on all three, and pins are REPRODUCED_BY_REGISTERED_BUILD on all three.
"""

    docs["13_ACTIVE_PATH_UPDATE"] = "# 13: Active path update (§43)\n\nThe R8.2 path classes are preserved. For each current path, this is the unit / frame / profile authority it uses **today**:\n\n" + _tbl(
        ["project", "path", "unit authority today", "frame", "CAD profile", "R8.3 unit context", "class"],
        [[m["project"], m["path"], m["unit_authority_today"], m["frame_authority_today"], m["cad_profile_today"],
          m["r8_3_unit_context"], m["classification"]] for m in path_map]) + """

**Finding (reported, nothing changed).** Both paths that publish quantities rest on unit authority R8.3 would not admit alone:
- `engine/ingest/source_units.py` accepts INSUNITS first, and lets a declared unit overrule it on a wall-thickness plausibility band.
- The Al Rashed reader assumes metres.

Neither is an R8.3 change. Migration must replace both with MEASUREMENT_FRAME.
"""

    docs["14_MIGRATION_GATE"] = """# 14: Migration gate (§45)

**MIGRATION_READY = NO**

| condition | status |
|---|---|
| validated UNIT_CONTEXT for the consumer's source | ✗ (P7757 UNCONFIRMED; Qortuba UNCONFIRMED; Al Rashed CONFLICT) |
| validated region transform | ✗ (unsegmented; convention only) |
| CAD_PROFILE FINAL-eligible for the consumer's scope | ✗ (D, E, F, G fail) |
| source conservation | ✓ (all three balanced) |
| no critical unresolved source finding in scope | ~ (handle defect mitigated; parser risk remains) |
| real independent K1/K2 comparison for the consumer | ✗ (BLOCKED_EXTERNAL_INPUT) |
| downstream support for the required kinds | ✗ for ellipses (PREVIEW); ✓ for lines, arcs, polylines |
| pinned decoder | ✓ (REPRODUCED_BY_REGISTERED_BUILD; build not *qualified*) |

**Recommended gate.** YES only when, for ONE selected consumer, all of the following hold:
1. the independent DXF reconciliation PASSes or WARNs;
2. that source's frame permits FINAL (machine VERIFIED, or CONFIRMED_BY_HUMAN under V1);
3. CAD_PROFILE is FINAL-eligible for the consumer's measured scopes;
4. the two CONTRACT_DISPUTED R8.0 rows are resolved by review.

## First consumer (§46)
**P7757 PA07 first**, as a sealed shadow-to-live integration test. It publishes nothing, so a failed migration cannot
move a BOQ, and it is the only project with an independent DXF on the way.

Its limitation is real: it cannot prove the FINAL publication path. So add a **second step**: a sealed,
non-published copy of Qortuba QS01, run through the new source path with publication disabled, to exercise FINAL
logic end to end before any live switch.
"""

    docs["15_TEST_RESULTS"] = f"""# 15: Test results

One complete run from the **final committed tree** (`{commit}`, clean working tree):

```
python3 -m pytest -p no:cacheprovider -m "not slow" -q --junitxml=full_r83.xml
```

Counts are read from junit, not computed:

| passed | xfailed | skipped | failed | errors | total |
|---|---|---|---|---|---|
| {counts.get('passed', 0)} | {counts.get('xfailed', 0)} | {counts.get('skipped', 0)} | {counts.get('failed', 0)} | {counts.get('errors', 0)} | {total} |

By directory: """ + "; ".join(f"{k}: " + ", ".join(f"{n} {kk}" for kk, n in v.items()) for k, v in by_dir.items()) + f""".

**R8.0 register:** {ef_classes}.
- R8.3 moved 22 TARGET_NOT_IMPLEMENTED → PASS (UNIT_CONTEXT, FRAMES, FRAME_EVIDENCE, SOURCE_PROFILE, bound via `tests/r8_0/frame_harness.py`).
- It moved 2 → CONTRACT_DISPUTED (F17, MT-32; expectations unchanged).
- MT-33 and F19 remain TARGET_NOT_IMPLEMENTED, with updated reasons.
- Strict xfail is unchanged; the new class is strict too.
"""

    docs["16_CLAUDE_RECOMMENDATION"] = """# 16: Claude's recommendations

1. **Should INSUNITS ever be sufficient alone?** No, not for FINAL. It is a declaration a drafter can leave wrong
   (Al Rashed says inch and is plainly not). But INSUNITS **plus a human confirmation of that exact file** is
   reasonable for FINAL, and URBAN_FRAME_RELEASE_V1 allows it.
2. **Keep machine VERIFIED and CONFIRMED_BY_HUMAN distinct?** Yes. They answer different questions: "the drawing
   proves it" versus "a named person vouches for it". Keep the distinction in every record and every BOQ row.
3. **Mandatory independent parser for every project?** Not permanently; option B. A parser defect is
   data-dependent (the handle defect appears only in files with more than 65k handles), so every *decoder build*
   must be qualified against at least one independent-parser real comparison. Every *project* needs one only when
   a parser-risk finding is in scope, or for benchmark and first-consumer work. Until one build is qualified,
   B is A.
4. **Was the R8.2 block-lineage gap real?** Yes, and worse than described: it both **skipped** truncated INSERTs
   and **falsely conflicted** truncated block records. Fixed; mutation-tested.
5. **Does the pinned re-decode reproduce the truncation?** Yes, on Al Rashed and P7757, byte-for-byte (Al Rashed
   modulo 40 documented text bytes). It is attributed to the pinned dwgread JSON route; the layer is not localised.
6. **Chord tolerance in the frame?** No. The frame states physical meaning; curve approximation is an algorithm
   policy that *consumes* a verified frame. R11 CURVE_APPROXIMATION_POLICY.
7. **The Al Rashed 0.2003 m²?** Both layers. The column is closed per source (170/170), so the source geometry
   correction is identified. Whether to deduct it from floor finish is an undecided trade rule (R9 rules-as-data).
   NET_INSTALL_AREA and BILLING_MEASUREMENT_AREA are recorded, and neither is published.
8. **Is UNIT_CONTEXT generic enough for DWG / DXF / PDF / raster?** The schema is: the space kind is data,
   the evidence kinds include scale bar, viewport scale and external documents, and F18 (rotated PDF + scale bar)
   and F30 (raster DPI conflict) pass. What is *not* generic yet is extraction: only the CAD extractor exists.
9. **Does the impact model need adjustment?** Only one: an explicit `scope` on findings (added, optional,
   backward-compatible) so frame findings can name a coordinate space or region. All 17 frame findings sit in
   MEASUREMENT_FRAME, and count methods ignore that domain. No second blocker graph.
10. **Is R8.3 sufficient to begin migration planning?** Planning, yes. Migration, no (MIGRATION_READY = NO).
11. **Next round (R8.4, before any migration):**
    1. the independent P7757 DXF reconciliation;
    2. Mohammad's unit confirmations (three one-line statements tied to the three DWG hashes);
    3. model-space region segmentation (a deterministic plan/detail split with reference designation);
    4. a decision on the two CONTRACT_DISPUTED rows and the V-CAD numbering;
    5. qualify the pinned dwgread build;
    6. replace the active paths' unit authority with MEASUREMENT_FRAME in shadow and diff the BOQs row by row.

## Where Claude disagrees
- **With the frozen R8.0 F17 / MT-32** (plausibility-contested INSUNITS → PROVISIONAL): R8.3 computes
  UNCONFIRMED, because plausibility must not raise a status. The expectation is kept, registered CONTRACT_DISPUTED.
- **With the frozen R8.0 MT-33 prediction** (Al Rashed PROVISIONAL, independent set 1): with DIMLFAC
  candidate-only (the mid-course review), Al Rashed has 0 admitted physical evidence and is CONFLICT.
- **With my own R8.2 report**: it said Al Rashed and Qortuba had no DWG here. They were in the uploads the whole time.
- **Frozen spec vs brief on CONFIRMED_BY_HUMAN**: the spec's row requires a PROVISIONAL base, which would make
  Al Rashed impossible to finalise by owner confirmation. V1 instead requires consistency with all evidence plus
  one agreeing non-human item. This needs review.
"""
    return docs
