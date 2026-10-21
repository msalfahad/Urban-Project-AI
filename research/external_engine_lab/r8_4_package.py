"""R8.4 review package generator (§40). Research lab only; writes data/reports/ (gitignored).

Inputs (all produced by committed code):
    research/external_engine_lab/outputs/r8_4/*.json      (r8_4_qualification.py, r8_4_regions.py, r8_4_shadow_diff.py)
    tests/r8_0/registers/R8_CONTRACT_SUPERSESSION.json
    tests/r8_0/registers/R8_0_EXPECTED_FAILURES.json
    <junit xml of the ONE final full-suite run>  (argv[1])
    <commit sha>                                 (argv[2])
    <exact suite command>                        (argv[3])

    python3 research/external_engine_lab/r8_4_package.py JUNIT.xml COMMIT "COMMAND"
"""

from __future__ import annotations

import collections
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import cad_profile as P, frame as FR, qualification as Q        # noqa: E402

NAME = "URBAN_QTO_R8_4_QUALIFICATION_SHADOW"
OUT = ROOT / "data/reports" / NAME
LAB = ROOT / "research/external_engine_lab/outputs/r8_4"
REG = ROOT / "tests/r8_0/registers"
SPECS = [ROOT / "data/reports/URBAN_QTO_R8_SPEC/R8_REVISED_SPEC.md",
         ROOT / "data/reports/URBAN_QTO_R8_SPEC/R8_DECISION_LOG.md"]


def jload(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def junit(path):
    root = ET.parse(path).getroot()
    ts = root if root.tag == "testsuite" else root.find("testsuite")
    c, by = collections.Counter(), collections.defaultdict(collections.Counter)
    r84 = collections.defaultdict(collections.Counter)
    for tc in ts.iter("testcase"):
        k = "passed"
        for ch in tc:
            if ch.tag == "failure":
                k = "failed"
            elif ch.tag == "error":
                k = "errors"
            elif ch.tag == "skipped":
                k = "xfailed" if ch.get("type") == "pytest.xfail" else "skipped"
        c[k] += 1
        cn = tc.get("classname", "")
        d = next((x for x in ("tests.r8_4", "tests.r8_3", "tests.r8_2", "tests.r8_1", "tests.r8_0") if cn.startswith(x)),
                 "other")
        by[d][k] += 1
        if d == "tests.r8_4":
            r84[cn.split(".")[-1]][k] += 1
    return dict(ts.attrib), dict(c), {k: dict(v) for k, v in sorted(by.items())}, {k: dict(v) for k, v in sorted(r84.items())}


def policy_dict(p):
    return {"policy_id": p.policy_id, "human_confirmed_final": p.human_confirmed_final,
            "require_admitted_corroboration": p.require_admitted_corroboration,
            "require_role_and_scope": p.require_role_and_scope, "authorised_roles": list(p.authorised_roles)}


DECISIONS = [
    ("R8_4_D01", "HUMAN_AUTHORITY_MODEL", "Default URBAN_FRAME_RELEASE_V2 = H3 'authoritative informed project confirmation': a "
     "versioned claim (id, source sha256, coordinate space, native_to_mm, author, authorised role, timestamp, scope, supersedes, "
     "acknowledges, notes) may carry FINAL only if every declaration / candidate contradiction is acknowledged and no admitted "
     "physical evidence contradicts it. H2 (corroboration required) kept as RELEASE_V2_H2; V1 kept reproducible.", "IMPLEMENTED"),
    ("R8_4_D02", "CANDIDATE_NEVER_POSITIVE", "Candidate evidence (DIMLFAC / display families, set-valued) can lower or question, "
     "never support a human claim toward FINAL. Fixes the V1 'CONSISTENT_WITH_ALL_EVIDENCE' inconsistency.", "IMPLEMENTED"),
    ("R8_4_D03", "HUMAN_CLAIM_LIFECYCLE", "Two active disagreeing claims -> HUMAN_CONFIRMATION_CONFLICT; a correction supersedes "
     "and never erases; an unknown supersession target -> REVIEW; no 'last human wins'.", "IMPLEMENTED"),
    ("R8_4_D04", "F17_MT32_SUPERSEDED", "Declaration + contradictory plausibility -> UNCONFIRMED + UNIT_PLAUSIBILITY_QUESTION, "
     "no FINAL. Legacy contracts kept byte-for-byte (hash-checked) as strict xfail CONTRACT_SUPERSEDED.", "IMPLEMENTED"),
    ("R8_4_D05", "MT33_SUPERSEDED", "MT-33 depended on admitting DIMLFAC display ratio, plot size and wall spacing (D-08); all "
     "are candidate / support-only. Superseded; the admitted independent set is 0.", "IMPLEMENTED"),
    ("R8_4_D06", "F19_V_CAD_5_BOUND", "V-CAD-5 IS defined (later spec edition §6a). R8.3's 'undefined' statement was wrong. "
     "F19 expectation retained and now PASSES through cad_profile.region_class_findings -> H_FINDINGS.", "IMPLEMENTED"),
    ("R8_4_D07", "DECODER_QUALIFICATION_ENVELOPE", "A decoder is qualified for the envelope an independent comparison exercised; "
     "target features ⊆ envelope. Parser policy V2 / CAD profile V2 use it; qualified_builds kept for V1 only. Handle risk by "
     "representation (byte size vs value, collisions, reference resolution), not by object count.", "IMPLEMENTED"),
    ("R8_4_D08", "INDEPENDENT_P7757_RECONCILIATION", "BLOCKED_EXTERNAL_INPUT. Every P7757 DXF on disk was written by LibreDWG "
     "0.13.3 (same lineage as D1); autocad.zip is a GitHub error body. No build qualified; register status "
     "BLOCKED_EXTERNAL_INPUT (P7757) / NOT_EXECUTED (others).", "RECORDED"),
    ("R8_4_D09", "REFERENCE_REGION_DESIGNATION", "Bare reference=True confers no authority under V2 "
     "(REFERENCE_REGION_UNDESIGNATED). Authority only through an ACCEPTED ReferenceRegionDesignation; human designation -> "
     "CONFIRMED_BY_HUMAN, machine bases -> VERIFIED; evidence digests on regions and frames.", "IMPLEMENTED"),
    ("R8_4_D10", "REGION_CANDIDATES", "Deterministic clusters with role candidates (plan / detail / section / elevation / unknown) "
     "are candidates, not designations. UNKNOWN -> MODEL_SPACE_UNKNOWN (U-2 BLOCKED without evidence). Project windows stay in "
     "project adapters; the Al Rashed adapter windows are recorded as PENDING_REVIEW designations, not accepted.", "IMPLEMENTED"),
    ("R8_4_D11", "U2_AND_PAPER_SPACE_KEPT", "U-2 unchanged; paper-space viewports keep MEASURE_IN_MODEL_FRAME.", "KEPT"),
    ("R8_4_D12", "V_CAD_5_LOCATION", "An unrealised entity inside a block instance is located by its root INSERT; a top-level one "
     "with no placeable geometry stays IN SCOPE (fail closed). The shadow reports the 'unplaceable excluded' sensitivity "
     "separately; it is not the canonical result.", "IMPLEMENTED_IN_SHADOW"),
    ("R8_4_D13", "PROFILE_RELEVANT_LAYERS", "Shadow uses the active path's own deterministic LAYER_PROFILE roles (walls, doors, "
     "glazing, dimensions, text) as V-CAD-5 relevant layers; engine/source holds no layer names; columns have no role there.",
     "SHADOW_ONLY"),
    ("R8_4_D14", "NO_VALUE_RECOMPUTATION", "R8.4 shadow changes status only; no canonical re-measurement, so no "
     "VALUE_CHANGED_SOURCE_GEOMETRY row can arise and none is claimed.", "RECORDED"),
    ("R8_4_D15", "OUT_OF_SCOPE_KEPT", "Column rule stays out of R8.4; ellipses stay exact (no flattening); the R8.3 40-row "
     "U+FFFD text-delta review (R8_3_D03) is preserved unchanged.", "KEPT"),
    ("R8_4_D16", "THRESHOLDS", "0.5 % / 0.5 % / max(2 mm, 0.2 %) unchanged; both spec editions cited (v1 9bb2433d…, later "
     "17e1a9cd…); not retuned on any project.", "KEPT"),
    ("R8_4_D17", "MIGRATION_GATE", "MIGRATION_PLANNING_READY = YES (planning inputs complete); PRODUCTION_MIGRATION = NO.",
     "RECORDED"),
]


def main(junit_xml, commit, command):
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    attrs, counts, by_dir, r84 = junit(junit_xml)
    sup = jload(REG / "R8_CONTRACT_SUPERSESSION.json")
    ef = jload(REG / "R8_0_EXPECTED_FAILURES.json")
    qreg = jload(LAB / "DECODER_QUALIFICATION_REGISTER.json")
    env = jload(LAB / "DECODER_QUALIFICATION_ENVELOPE.json")
    rec = jload(LAB / "INDEPENDENT_RECONCILIATION_RESULTS.json")
    rreg = jload(LAB / "REFERENCE_REGION_REGISTER.json")
    diff = jload(LAB / "SHADOW_ROW_DIFF.json")
    status = jload(LAB / "REAL_PROJECT_R8_4_STATUS.json")

    def dump(name, obj):
        (OUT / name).write_text(json.dumps(obj, indent=1, default=str, ensure_ascii=False) + "\n")

    dump("R8_CONTRACT_SUPERSESSION.json", sup)
    dump("FRAME_RELEASE_POLICY.json", {
        "SCHEMA": "URBAN_R8_4_FRAME_RELEASE_POLICY_V1", "default": FR.DEFAULT_POLICY.policy_id,
        "policies": [policy_dict(p) for p in (FR.RELEASE_V1, FR.RELEASE_V2, FR.RELEASE_V2_H2)],
        "final_human_bases_v2": list(FR.FINAL_HUMAN_BASES_V2),
        "human_claim_fields": ["confirmation_id", "source_sha256", "coordinate_space_id", "native_to_mm", "author",
                               "author_role", "timestamp", "scope", "supersedes", "acknowledges", "notes"],
        "designation_bases": list(FR.DESIGNATION_BASES),
        "parser_policies": [{"policy_id": p.policy_id, "option": p.option, "qualified_builds": sorted(p.qualified_builds),
                             "qualifications": [q.qualification_id for q in p.qualifications]}
                            for p in (P.PARSER_POLICY_V1, P.PARSER_POLICY_V2)],
        "cad_profiles": [{"profile_id": c.profile_id, "parser_policy": c.parser_policy.policy_id,
                          "frame_policy": c.frame_policy.policy_id} for c in (P.CAD_PROFILE_V1, P.CAD_PROFILE_V2)],
        "default_cad_profile": P.DEFAULT_CAD_PROFILE.profile_id,
        "v_cad_checks": {k: {"requirement": v[0], "definition": v[1]} for k, v in P.V_CAD_CHECKS.items()},
        "thresholds": {"AGREEMENT_REL": FR.AGREEMENT_REL, "CHECKED_DIM_ABS_MM": FR.CHECKED_DIM_ABS_MM,
                       "CHECKED_DIM_REL": FR.CHECKED_DIM_REL}})
    dump("REFERENCE_REGION_REGISTER.json", rreg)
    dump("DECODER_QUALIFICATION_REGISTER.json", qreg)
    dump("DECODER_QUALIFICATION_ENVELOPE.json", env)
    dump("INDEPENDENT_RECONCILIATION_RESULTS.json", rec)
    dump("SHADOW_ROW_DIFF.json", diff)
    dump("REAL_PROJECT_R8_4_STATUS.json", status)
    dump("R8_4_DECISION_REGISTER.json", {"SCHEMA": "URBAN_R8_4_DECISION_REGISTER_V1", "commit": commit,
                                         "decisions": [dict(zip(("id", "topic", "decision", "status"), d)) for d in DECISIONS]})
    dump("R8_4_TEST_RESULTS.json", {"SCHEMA": "URBAN_R8_4_TEST_RESULTS_V1", "commit": commit, "command": command,
                                    "junit_attributes": attrs, "counts": counts, "by_directory": by_dir,
                                    "r8_4_by_module": r84,
                                    "expected_failures_by_class": dict(collections.Counter(e["class"] for e in ef["expected_failures"])),
                                    "expected_failure_entries": len(ef["expected_failures"])})
    sp = OUT / "SPEC_EVIDENCE"
    sp.mkdir()
    for s in SPECS:
        if s.exists():
            shutil.copy(s, sp / s.name)
    write_markdown(OUT, commit, command, attrs, counts, by_dir, r84, sup, ef, qreg, env, rec, rreg, diff, status)
    zp = OUT.parent / f"{NAME}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, f"{NAME}/{p.relative_to(OUT)}")
    print(zp, sha(zp))


def _tbl(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def write_markdown(out, commit, command, attrs, counts, by_dir, r84, sup, ef, qreg, env, rec, rreg, diff, status):
    S = {k: v["summary"] for k, v in diff["projects"].items()}
    st = status["projects"]
    q_fin, a_fin = S["QORTUBA"]["current_FINAL_becomes"], S["ALRASHED"]["current_FINAL_becomes"]
    tot = sum(counts.values())
    suite = (f"{tot} tests: {counts.get('passed', 0)} passed, {counts.get('xfailed', 0)} xfailed (strict, registered), "
             f"{counts.get('skipped', 0)} skipped, {counts.get('failed', 0)} failed, {counts.get('errors', 0)} errors")
    prof = {k: v["feature_profile"] for k, v in env["target_feature_profiles"].items()}
    files = {}

    files["00_EXECUTIVE_SUMMARY.md"] = f"""# R8.4 — Independent source qualification, frame policy hardening, model-space region designation, shadow integration

Commit `{commit}` · base accepted `e43fba5` · SHADOW ONLY · MIGRATION_READY = NO · PRODUCTION_MIGRATION = NO

## What changed (engine/source, shadow)
- **Frame release V2 (default)** — H3 *authoritative informed project confirmation*. A human confirmation is a versioned claim
  with author, authorised role, timestamp, exact source hash, scope, `supersedes` and `acknowledges`. Candidate evidence is never
  positive support (the V1 defect). Disagreeing active claims → `HUMAN_CONFIRMATION_CONFLICT`; corrections supersede, never erase.
  V1 is kept and reproducible.
- **Contract supersessions** — F17, MT-32, MT-33 superseded with frozen legacy hashes; F19 bound to V-CAD-5 (defined in the later
  spec edition — R8.3's "undefined" claim was wrong) and now passes.
- **Decoder qualification** — capability-scoped envelope; handle risk by representation. Parser policy V2 / CAD profile V2.
- **Reference-region designation** — bare `reference=True` no longer confers authority; `MODEL_SPACE_UNKNOWN`; evidence digests.
- **Deterministic region candidates** — candidates only.

## Real sources (canonical V2, nothing supplied by Mohammad)
| Project | UNIT_CONTEXT | Independent reconciliation | Current FINAL rows | Canonical outcome of those rows |
|---|---|---|---|---|
| Qortuba | {st['QORTUBA']['unit_context_V2']['status']} | NOT_EXECUTED | {S['QORTUBA']['current_FINAL']} | {q_fin} |
| Al Rashed | {st['ALRASHED']['unit_context_V2']['status']} | NOT_EXECUTED | {S['ALRASHED']['current_FINAL']} | {a_fin} |
| P7757 | {st['P7757']['unit_context_V2']['status']} | **BLOCKED_EXTERNAL_INPUT** | {S['P7757']['current_FINAL']} | — ({S['P7757']['eligibility']}) |

No current FINAL row survives as FINAL: every one is blocked first by the frame (unit context not FINAL-eligible), and
independently by parser policy V2 (no qualified envelope). No value changes (not recomputed). No output was modified.

## Suite (one run, final commit)
`{command}` → {suite}.

MIGRATION_PLANNING_READY = **YES** · PRODUCTION_MIGRATION = **NO** · STOP AFTER R8.4. NO R9.
"""

    files["01_R8_3_POLICY_HARDENING.md"] = f"""# 01 — R8.3 policy hardening (§2)

## The V1 inconsistency
R8.3's release V1 let a human claim reach FINAL when it was "CONSISTENT_WITH_ALL_EVIDENCE". Set-valued candidate families
(DIMLFAC display ratio × {{mm, cm, m, in, ft}}) contain many values, so *membership* counted as agreement: candidate evidence
**helped raise** a claim to FINAL. R8.3's own rule says membership is never support. R8.3 test
`test_a_human_confirmation_consistent_with_every_family_resolves_a_contradicted_declaration` encoded that V1 behaviour.

## Fix
- `frame.assess` V2 branch: candidates are never positive support; a declaration or candidate contradiction must be listed in the
  claim's `acknowledges`, else `UNACKNOWLEDGED_CONTRADICTION` → `HUMAN_CONFIRMATION_REVIEW_REQUIRED`, no FINAL.
- The R8.3 test is pinned to `RELEASE_V1` with a docstring naming the defect: V1 stays reproducible, not silently rewritten.
- Exhaustive check (`tests/r8_4/test_r8_4_human_confirmation.py`): over every combination of candidate families, adding
  candidates never raises the status or adds FINAL.

## Versioning (§32)
`URBAN_FRAME_RELEASE_V1` (R8.3), `URBAN_FRAME_RELEASE_V2` (default), `URBAN_FRAME_RELEASE_V2_H2`;
`URBAN_CAD_PROFILE_V1/V2`; `URBAN_PARSER_INDEPENDENCE_V1/V2`. Every UnitContext / region carries its `policy_id`; a region
inherits its unit context's policy unless one is passed.

## Corrections to R8.3 reporting
""" + "\n".join(f"- {c}" for c in sup["corrections_to_r8_3"]) + "\n"

    files["02_HUMAN_CONFIRMATION_POLICY.md"] = """# 02 — Human confirmation policy (§3-§7, §33)

## Recommendation: H3 — authoritative informed project confirmation (default V2)
| Model | Rule | Why not / why |
|---|---|---|
| H1 authoritative | any recorded human claim is FINAL | lets a person overrule contradicting physical evidence silently |
| H2 corroborated | human + ≥1 admitted physical corroboration | safest, but Al Rashed-type drawings may have *no* admissible physical evidence, so a correct owner answer could never publish; kept as `RELEASE_V2_H2` |
| **H3 own (recommended)** | an authorised, scoped, source-bound claim that **acknowledges** every declaration / candidate contradiction is FINAL-capable; any admitted physical contradiction → CONFLICT | puts the decision with the accountable person, informed, and never lets it override measured evidence |

## Claim record
`human_confirmation(confirmation_id, source_sha256, coordinate_space_id, native_to_mm, author, author_role, timestamp,
scope, supersedes, acknowledges, notes)`. Authorised roles: PROJECT_OWNER, PROJECT_ARCHITECT, PROJECT_ENGINEER, URBAN_QS_LEAD.

## Rules (tested A-L)
- A agent-generated human record → rejected (`AGENT_GENERATED_HUMAN_RECORD`).
- B missing author / role / timestamp → `HUMAN_CONFIRMATION_INCOMPLETE`; unauthorised role → `HUMAN_ROLE_NOT_AUTHORISED`.
- C source hash mismatch → rejected; D scope not covering the assessed space → `HUMAN_CONFIRMATION_SCOPE_MISMATCH`.
- D2 `supersedes` an unknown id → REVIEW.
- E candidate evidence never positive (V1 behaviour reproduced separately).
- F unacknowledged contradiction → `human_basis = UNACKNOWLEDGED_CONTRADICTION:<family>`, no FINAL.
- G acknowledged contradiction → `AUTHORITATIVE_PROJECT_CONFIRMATION`, FINAL.
- H H2 policy requires admitted corroboration.
- I admitted physical contradiction → CONFLICT whatever the human says.
- J two active disagreeing claims → `HUMAN_CONFIRMATION_CONFLICT`.
- K correction supersedes (both kept, audit trail); L no "human[-1] wins".

## What was supplied in R8.4
**No human confirmation was supplied.** None was created. No unit was guessed from villa dimensions, geometry, INSUNITS, DIMLFAC or
Kuwait practice. Source hashes bound: Al Rashed 299c61b1…660c, P7757 7f61f3ac…41e3, Qortuba 2ec3a9c8…d355.
"""

    rows = []
    for e in sup["entries"]:
        rows.append((e["legacy_id"], e["decision"], "`" + e["legacy_hash"][:16] + "…`", json.dumps(e["legacy_expectation"]),
                     json.dumps(e["new_expectation"])[:160]))
    files["03_CONTRACT_SUPERSESSIONS.md"] = "# 03 — Contract supersessions (§8-§10, §31)\n\n" + sup["rule"] + "\n\n" + _tbl(
        ("id", "decision", "legacy hash", "legacy expectation", "new expectation"), rows) + "\n\n" + "\n\n".join(
        f"## {e['legacy_id']}\n**Problem.** {e['problem']}\n\n**Decision.** {e['new_decision']}\n\n**Authority.** "
        f"{e['superseding_authority']}\n\n**Migration effect.** {e['migration_effect']}\n\n**Tests.** " + "; ".join(e["tests"])
        for e in sup["entries"]) + """

## MT-33 reviewed separately (§9)
R8_DECISION_LOG D-08 predicted Al Rashed PROVISIONAL because "two independent kinds agree and they contradict a declaration",
the kinds being the printed plot size, the dimension display ratio and wall-pair spacing. The display ratio is a DIMLFAC /
display family (display unit not authored → a candidate set); plot size and wall spacing are plausibility (support-only). The
expectation therefore **depended on admitting evidence R8.3 found inadmissible** → superseded, not retained.

## F19 / V-CAD-5 (§10) — disagreement with the brief's premise
The brief proposed a LEGACY_UNDEFINED_CHECK_ID record. That premise came from R8.3's report, which was wrong: V-CAD-1..6 are
defined in the later spec edition (`data/reports/URBAN_QTO_R8_SPEC/R8_REVISED_SPEC.md`, sha 17e1a9cd…, §6a). No id is invented;
the record is `LEGACY_CHECK_ID_RESOLVED`, the expectation is unchanged and now passes.
"""

    files["04_REFERENCE_REGION_AUTHORITY.md"] = f"""# 04 — Reference-region authority (§18, §21, §22, §35)

`reference=True` alone no longer grants anything under V2: it raises `REFERENCE_REGION_UNDESIGNATED` (REVIEW) and the plan
region stays at its declaration (UNCONFIRMED). Authority comes only from a `ReferenceRegionDesignation`:

`designation_id, source_sha256, coordinate_space_id, region_id, basis, source_ref, producer, review_status, author, timestamp,
author_role, notes`

| basis | confers | conditions |
|---|---|---|
| SOURCE_PLAN_LABEL / PROJECT_ADAPTER_CLAIM / DETERMINISTIC_REGION_ROLE / OTHER_AUTHORIZED_EVIDENCE | VERIFIED | ACCEPTED, not AGENT, source ref present, hash / space / region match |
| HUMAN_DESIGNATION | CONFIRMED_BY_HUMAN (FINAL-capable) | producer HUMAN, author, timestamp, authorised role |

A designation never overrides region evidence that contradicts full size (it is applied only when the region is otherwise
declaration-only). Regions and frames carry an `evidence_digest` (the version of the evidence the status was computed from).

**U-2 kept** (detail / unknown region without region-local evidence → BLOCKED). **Paper space kept**: viewports are never
measurement authority (`MEASURE_IN_MODEL_FRAME`).

## R8.4 register
Accepted designations: **{len(rreg['accepted_designations'])}**. Pending (not accepted):
""" + "\n".join(f"- `{d['designation_id']}` {d['basis']} — {d['review_status']}: {d['notes']}; effect if accepted: {d['effect_if_accepted']}"
                for p in rreg["projects"].values() for d in p["pending_designations"]) + "\n"

    rc_rows = [(n, p["candidate_count"], json.dumps(p["candidates_by_role"]), len(p["active_path_view_roles"]),
                f"{p['parameters'].get('cell'):.4g}" if p['parameters'].get('cell') else "-") for n, p in rreg["projects"].items()]
    files["05_REGION_SEGMENTATION.md"] = """# 05 — Deterministic region segmentation (§19-§20)

`engine/source/region_candidates.py`: realised geometry sampled onto an occupancy grid (cell = 1/150 of the robust 1st-99th
percentile extent — unit-free, one rule for every source), 8-connected clusters ≥ 4 cells. Role candidates from generic English /
Arabic drawing-type words and scale notes inside the cluster; several role classes → UNKNOWN.

| role candidate | region kind without designation | effect |
|---|---|---|
| PLAN | MODEL_SPACE_PLAN | full-size convention is a declaration → UNCONFIRMED, preview at most |
| DETAIL | MODEL_SPACE_DETAIL | U-2 BLOCKED without region evidence |
| SECTION / ELEVATION / UNKNOWN | MODEL_SPACE_UNKNOWN | never inherits plan authority; BLOCKED without evidence |

""" + _tbl(("project", "candidates", "by role", "active-path views", "cell (native)"), rc_rows) + """

Observations:
- **Al Rashed**: the three adapter plan windows (FIRST / GROUND / BASEMENT) fall inside ONE unlabelled cluster (three plans drawn
  side by side with no gap larger than a cell). The one PLAN-labelled cluster is the site / location plan sheet. So the rows'
  region is UNKNOWN until the adapter windows are accepted as designations.
- **Qortuba**: the 'SECOND FLOOR PLAN' title sits in the main plan cluster → PLAN candidate.
- **P7757**: 11 clusters, none labelled by the generic vocabulary (titles are not in plain model-space TEXT inside the clusters);
  the active path's own view-role register marks 3 views FLOOR_PLAN (GEOMETRY_HINT_DETERMINISTIC_INCOMPLETE) — used only as a
  candidate hint for the dominant cluster of that view.

Candidate ≠ designation: no candidate raises any status above UNCONFIRMED.
"""

    files["06_DECODER_QUALIFICATION_MODEL.md"] = """# 06 — Decoder qualification model (§11-§13, §36)

`engine/source/qualification.py`
- `source_feature_profile(document, decode)` → entity kinds, transform classes (IDENTITY, TRANSLATION, ROTATION, REFLECTION,
  UNIFORM_SCALE, NON_UNIFORM_SCALE, OCS_NON_DEFAULT), max block depth, MINSERT / dynamic / xref flags, handle representation.
- `handle_representation(decode)` — **representation, not count**: declared byte size vs the size the value needs
  (`size_value_inconsistent`), own-handle value collisions, absolute references naming no object, max size / value.
- `QualificationEnvelope.covers(profile)` → () or the uncovered features; unresolved absolute references are outside every envelope.
- `DecoderQualification` — QUALIFIED only with an independent route, a reference source hash and a PASS reconciliation
  (constructor refuses otherwise); non-PASS items and excluded capabilities recorded. Statuses: QUALIFIED, NOT_EXECUTED,
  BLOCKED_EXTERNAL_INPUT, FAILED.

Parser policy **V2** (default) asks `qualification_for(build, profile, qualifications)`: a build is "qualified" for THIS source only
if an envelope covers its profile. `qualified_builds` (V1) is kept for compatibility and ignored by V2.

## Parser policy after the envelope (§36) — recommendation
Keep **option B**, now envelope-scoped: independent parser REQUIRED when (a) a parser-risk finding is in scope, (b) the decode pin is
not REGISTERED / REPRODUCED, (c) the source's feature profile is not covered by a QUALIFIED envelope, (d) benchmark qualification,
(e) the first migration consumer. Disagreement with the later spec edition's V-CAD-6 ("parser independence recorded, not
required"): the pinned-route handle defect shows a single LibreDWG route can silently mis-identify objects, so recording alone is
not enough for FINAL.

## Correction
R8.3 said the handle defect "appears only in files with more than 65k handles" — a count proxy. The actual criterion is
representation: a 3-byte handle printed with a 16-bit value. Qortuba (2-byte handles) is consistent; Al Rashed and P7757 are not.
"""

    hrow = [(n, p["handle"]["objects"], p["handle"]["max_byte_size"], p["handle"]["size_value_inconsistent"],
             p["handle"]["value_collisions"], p["handle"]["unresolved_absolute_refs"]) for n, p in prof.items()]
    files["07_INDEPENDENT_P7757_RECONCILIATION.md"] = f"""# 07 — Independent P7757 reconciliation (§14-§17)

**INDEPENDENT_REAL_RECONCILIATION = {rec['INDEPENDENT_REAL_RECONCILIATION']}.** The build is **not** qualified.

Required input: {rec['required_input']}.

## What was searched (repo `data/`, upload store, scratchpad)
""" + _tbl(("file", "bytes", "writer", "verdict"), [(Path(x["path"]).name, x["bytes"], x["writer_comment"] or "-", x["verdict"][:110])
                                                  for x in rec["search"]]) + f"""

## Planned procedure once supplied
""" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(rec["planned_procedure"])) + """

## Handle representation of the three decodes (why P7757 needs it)
""" + _tbl(("project", "objects", "max bytes", "size/value inconsistent", "value collisions", "unresolved abs refs"), hrow) + "\n"

    miss = {n: v["features_an_envelope_must_cover"] for n, v in env["target_feature_profiles"].items()}
    files["08_QUALIFICATION_ENVELOPE.md"] = "# 08 — Qualification envelope (§12, §34)\n\nQualified envelopes: **" + str(
        len(env["qualified_envelopes"])) + "**. Rule: " + env["rule"] + ".\n\nFeatures each source would need covered:\n\n" + "\n".join(
        f"- **{n}**: " + ", ".join(m) for n, m in miss.items()) + """

Tests A-I (`tests/r8_4/test_r8_4_qualification.py`): A no qualification → independent parser required; B profile inside envelope →
covered; C entity kind outside; D reflection / non-uniform outside; E depth, MINSERT, dynamic, xref must be exercised; F handle risk
by representation not count (a 2-object decode with an inconsistent 3-byte handle is risky, a 65 000-object consistent decode is
not); G collisions and unresolved references; H only an executed PASS comparison qualifies; I scope by build, risk findings still
require an independent parser, V1 reproducible.
"""

    files["09_SHADOW_INTEGRATION_ARCHITECTURE.md"] = """# 09 — Shadow integration architecture (§23-§27)

`research/external_engine_lab/r8_4_shadow_diff.py` (read-only over current rows):

```
current row ──► region mapping (candidate cluster; adapter window / active-path view / title label)
             ──► UNIT_CONTEXT (unit_evidence.extract → frame.unit_context, V2)
             ──► REGION (region_transform: PLAN candidate → plan kind, UNKNOWN → MODEL_SPACE_UNKNOWN; no accepted designation)
             ──► FRAME (measurement_frame)
             ──► CAD_PROFILE V2 (evaluate: capability, mapping, source, parser V2 envelope, V-CAD-5 region findings, E-G, I)
             ──► eligibility FINAL / PREVIEW / COUNT_ONLY / BLOCKED  ──► delta class
```

- Values are not recomputed: status only. Every value delta is VALUE_IDENTICAL or NOT_COMPARABLE.
- Methods declare scale dependence from the row unit (m2, lm → scale-dependent; nr → count). Undeclared → reported separately
  (none in R8.4).
- V-CAD-5: census unrealised classes on profile-relevant layers (active-path LAYER_PROFILE roles); located by root INSERT;
  unplaceable → in scope (fail closed); the "unplaceable excluded" sensitivity is reported beside the canonical result.
- Nothing is written to any published / approved / frozen artefact.
"""

    def row_table(name, limit=None):
        rows = diff["projects"][name]["rows"]
        sel = rows if limit is None else rows[:limit]
        return _tbl(("row", "current", "value", "unit", "UNIT", "REGION", "FRAME", "CAD_PROFILE", "eligibility", "delta"),
                    [(r["row_id"][:48], r["current_status"], r["current_value"], r["unit"], r["canonical"]["UNIT_CONTEXT"],
                      r["canonical"]["REGION"], r["canonical"]["FRAME"], r["canonical"]["CAD_PROFILE"], r["eligibility"],
                      r["delta_class"]) for r in sel])

    def summ(name):
        s = S[name]
        return "\n".join(f"- {k}: {v}" for k, v in s.items())

    qb = st["QORTUBA"]["regions_evaluated"]
    files["10_QORTUBA_SHADOW_DIFF.md"] = f"""# 10 — Qortuba shadow diff (APPROVED_QUANTITIES, 28 rows)

{summ('QORTUBA')}

**Current FINAL rows: {S['QORTUBA']['current_FINAL']} → {q_fin}.** Primary cause: FRAME_BLOCKS_CURRENT_FINAL — UNIT_CONTEXT
UNCONFIRMED (INSUNITS 5 = cm declared, no admitted physical evidence) and the plan region has no accepted designation. Parser
policy V2 also blocks FINAL (no qualified envelope). V-CAD-5 PASSES for the plan: the one custom entity on FRAME sits inside a
block instance placed outside the plan cluster; the 37 REGION / 1 SPLINE entities are on 'OFFICE NAME', not a profile-relevant layer.

What would lift these rows to FINAL: (1) an H3 human unit confirmation for Qortuba (or admitted physical unit evidence), (2) an
accepted plan designation, (3) a qualified decoder envelope or an independent reconciliation. Values would not change.

{row_table('QORTUBA')}
"""

    ar = diff["projects"]["ALRASHED"]["rows"]
    by = collections.Counter((r["current_status"], r["eligibility"], r["delta_class"]) for r in ar)
    floors = collections.Counter((r["row_id"].split("|")[0][:5], r["region_mapping"][:30]) for r in ar)
    files["11_ALRASHED_SHADOW_DIFF.md"] = f"""# 11 — Al Rashed shadow diff (ALRASHED_DETAILED_QUANTITY_EXPORT, 265 records)

{summ('ALRASHED')}

**Current FINAL rows: {S['ALRASHED']['current_FINAL']} → {a_fin}.** The UNIT_CONTEXT is CONFLICT: INSUNITS declares inches while
every dimension-display candidate family excludes inches; the adapter's "1 unit = 1 m" is a project assumption, not admitted
evidence, and no H3 confirmation exists. CONFLICT allows no measured use (COUNT_ONLY only; these rows are m2 / lm, so BLOCKED).
The rows' region is the unlabelled cluster holding the three adapter windows (PENDING_REVIEW designations) — UNKNOWN; accepting the
windows would make the region VERIFIED and change nothing while the unit context is CONFLICT. V-CAD-5 also FAILs
independently (unrealised entities on profile-relevant layers): """ + "; ".join(sorted({d for v in st["ALRASHED"]["regions_evaluated"].values()
                                                                                         for d in v["vcad5_detail"]})[:4]) + """.

The Al Rashed floor quantity and every published value are unchanged; pa09/alrashed/geometry.py was read, not modified.

""" + _tbl(("current status", "eligibility", "delta class", "rows"), [(*k, v) for k, v in sorted(by.items())]) + "\n\nFirst 40 rows (all rows in SHADOW_ROW_DIFF.json):\n\n" + row_table("ALRASHED", 40) + "\n"

    pr = diff["projects"]["P7757"]["rows"]
    pv = collections.Counter((r["region_candidate"], r["region_role_candidate"], r["eligibility"],
                              r["eligibility_if_unplaceable_unrealised_excluded"]) for r in pr)
    files["12_P7757_SHADOW_DIFF.md"] = f"""# 12 — P7757 shadow diff (PA07 quantity safety register, 585 rows)

{summ('P7757')}

Current: 583 SOURCE_REQUIRED + 2 HUMAN_REVIEW, BRIDGE_ALLOWED 0 — no current value, no current FINAL. Canonical: every row
BLOCKED. Causes, in order: (1) a top-level custom entity (type 763) on dimension layer '4' with no placeable geometry → V-CAD-5
FAIL in every region (fail closed) — blocks even PREVIEW; (2) UNKNOWN regions (no role) → U-2 BLOCKED; (3) UNIT_CONTEXT UNCONFIRMED
(INSUNITS 4 declared, no admitted evidence); (4) HANDLE_VALUE_TRUNCATED parser risk + no qualified envelope + independent DXF
BLOCKED_EXTERNAL_INPUT.

Sensitivity (not canonical): if unplaceable unrealised entities were out of scope, {S['P7757']['eligibility_if_unplaceable_excluded']}.

""" + _tbl(("region candidate", "role", "eligibility", "if unplaceable excluded", "rows"), [(*k, v) for k, v in sorted(pv.items(), key=str)]) + "\n"

    files["13_ACTIVE_PATH_STATUS_DIFF.md"] = f"""# 13 — Active path vs canonical status

| project | active path unit | active path basis | canonical UNIT_CONTEXT (V2) | canonical value |
|---|---|---|---|---|
| Al Rashed | metre | pa09 adapter (`blind.py` declares m; `geometry.py` treats 1 unit = 1 m) | {st['ALRASHED']['unit_context_V2']['status']} ({st['ALRASHED']['unit_context_V2']['status_reason']}) | none established |
| Qortuba | centimetre | engine/ingest/source_units.py: INSUNITS 5 first | {st['QORTUBA']['unit_context_V2']['status']} ({st['QORTUBA']['unit_context_V2']['status_reason']}) | {st['QORTUBA']['unit_context_V2']['native_to_mm']} mm (declaration) |
| P7757 | millimetre | source_units.py: INSUNITS 4 first | {st['P7757']['unit_context_V2']['status']} ({st['P7757']['unit_context_V2']['status_reason']}) | {st['P7757']['unit_context_V2']['native_to_mm']} mm (declaration) |

Values agree for Qortuba and P7757 (the canonical path uses the declaration as the value) — only the STATUS differs: the active path
treats INSUNITS (or a plausibility override) as sufficient for FINAL; the canonical path treats it as a declaration (UNCONFIRMED).
For Al Rashed the active path's metre is an adapter assumption the canonical path cannot admit.

Unchanged from R8.3: active path still has no region, frame or profile concept; cad_adapter not migrated.
"""

    gates = [("G1", "policies versioned, V1 reproducible", "YES"),
             ("G2", "historical contracts preserved (hash-checked supersessions)", "YES"),
             ("G3", "row-by-row shadow diff for all three projects", "YES"),
             ("G4", "every current FINAL row's blocking gate named", "YES"),
             ("G5", "no published / approved / frozen output modified", "YES"),
             ("G6", "suite green from the final commit", "YES" if not counts.get("failed") and not counts.get("errors") else "NO"),
             ("G7", "external inputs identified (independent DXF, H3 confirmations, designations)", "YES")]
    mig = [("M1", "independent P7757 reconciliation executed", "NO (BLOCKED_EXTERNAL_INPUT)"),
           ("M2", "a QUALIFIED decoder envelope covering a real source", "NO"),
           ("M3", "unit contexts FINAL-eligible for the migrated projects", "NO (no confirmation supplied)"),
           ("M4", "accepted plan designations", "NO"),
           ("M5", "unplaceable unrealised entities located or dispositioned", "NO"),
           ("M6", "value-level canonical re-measurement compared", "NO (not in R8.4)")]
    files["14_MIGRATION_PLANNING_GATE.md"] = "# 14 — Migration planning gate (§37-§38)\n\n## Planning gate\n" + _tbl(
        ("gate", "criterion", "met"), gates) + "\n\n**MIGRATION_PLANNING_READY = " + (
        "YES" if all(g[2] == "YES" for g in gates) else "NO") + "** — the shadow tells a planner exactly what a migration would do to every current row and which input clears each block.\n\n## Production migration gate\n" + _tbl(
        ("gate", "criterion", "met"), mig) + "\n\n**PRODUCTION_MIGRATION = NO.** cad_adapter not migrated; no live publication from engine/source.\n"

    files["15_TEST_RESULTS.md"] = f"""# 15 — Test results (§41)

One complete run from commit `{commit}`:

```
{command}
```

junit: {attrs}

**{suite}.**

""" + _tbl(("directory", "counts"), [(k, json.dumps(v)) for k, v in by_dir.items()]) + "\n\nR8.4 modules:\n\n" + _tbl(
        ("module", "counts"), [(k, json.dumps(v)) for k, v in r84.items()]) + "\n\nExpected-failure register: " + json.dumps(
        dict(collections.Counter(e["class"] for e in ef["expected_failures"]))) + """ (strict; an unexpected pass fails the run).
R8.4 changes: F17 / MT-32 / MT-33 → CONTRACT_SUPERSEDED; F19 TARGET_NOT_IMPLEMENTED → PASS.
"""

    files["16_CLAUDE_RECOMMENDATION.md"] = """# 16 — Claude recommendation (§39)

1. **Human authority** — H3 (default V2). H1 lets a person silently overrule evidence; H2 can make a correct owner answer
   unpublishable on drawings with no admissible physical evidence (Al Rashed). Keep H2 available as a stricter project option.
2. **Candidate evidence** — never positive, only lowering / questioning. Agree with the brief.
3. **F17** — supersede to UNCONFIRMED + UNIT_PLAUSIBILITY_QUESTION. Agree.
4. **MT-32** — same; its "not counted toward VERIFIED" half is kept. Agree.
5. **MT-33** — supersede: its PROVISIONAL rested on DIMLFAC / plausibility being admitted (D-08).
6. **F19 / V-CAD-5** — *disagree* with the LEGACY_UNDEFINED_CHECK_ID premise: V-CAD-5 is defined in the later spec edition.
   Bind to it; the legacy expectation is retained and passes.
7. **Qualification model** — capability-scoped envelopes; never a global "qualified build".
8. **Handle risk** — by representation. Withdraw R8.3's ">65k handles" phrasing.
9. **Parser policy** — option B, envelope-scoped (06). *Disagree* with the spec's V-CAD-6 "not required" for FINAL.
10. **Independent P7757 DXF** — the one input that unblocks qualification. Ask Mohammad for an AutoCAD- or ODA-written DXF of the
    P7757 architectural DWG, exported as-is, with who / what / when. A LibreDWG-written DXF will be rejected again.
11. **Reference regions** — designation-only authority. The Al Rashed adapter windows are the obvious first PROJECT_ADAPTER_CLAIM
    to review — but accepting them changes nothing while the Al Rashed unit context is CONFLICT.
12. **Segmentation** — keep it a candidate generator. Do not tune the cell fraction on these projects.
13. **V-CAD-5 location** — the fail-closed choice is right, but it currently blocks all of P7757 over one unplaceable entity on the
    dimension layer. Next round: disposition unrealised top-level entities (identify class, extents from the raw object, or a human
    CAD inspection citing handles), rather than relaxing the rule.
14. **Migration** — planning YES, production NO. The shadow shows **no current FINAL row would stay FINAL** under the canonical
    stack; migrating now would turn all published FINAL rows into PREVIEW (Qortuba) or BLOCKED (Al Rashed). That is correct behaviour
    given the evidence, and it is why the inputs in 10 and 11 must come first.

## Next round (proposal, not started)
R8.5: (a) run the independent P7757 reconciliation the day the DXF arrives and qualify only its exercised envelope; (b) record any
H3 confirmations Mohammad chooses to give (Qortuba cm, Al Rashed unit), each acknowledging its contradictions; (c) review the Al
Rashed adapter windows as designations; (d) disposition the unplaceable unrealised entities; (e) a value-level canonical
re-measurement on one project, shadow only.

STOP AFTER R8.4. NO PRODUCTION MIGRATION. NO R9.
"""
    for name, text in files.items():
        (out / name).write_text(text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
