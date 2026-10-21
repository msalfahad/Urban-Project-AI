"""R8.3 review package generator (§51). Research lab only; writes data/reports/ (gitignored).

Inputs (all produced by committed code):
    data/runs/pinned_redecode/PINNED_REDECODE_RESULTS.json        (r8_3_pinned_redecode.py)
    research/external_engine_lab/outputs/R8_3_REAL_STATUS.json     (r8_3_real_status.py)
    tests/r8_3/registers/R8_3_THRESHOLD_PROVENANCE.json
    tests/r8_0/registers/R8_0_EXPECTED_FAILURES.json
    <junit xml of the final full-suite run>  (argv[1])
    <commit sha>                              (argv[2])
    [spec evidence file]                      (argv[3], optional: R8_REVISED_SPEC.v1.md)

    python3 research/external_engine_lab/r8_3_package.py JUNIT.xml COMMIT [SPEC.md]
"""

from __future__ import annotations

import collections
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import cad_profile as P, decoder_pins as PINS, frame as FR, reconcile as R   # noqa: E402
from research.external_engine_lab import r8_2_path_and_independence as MAP                      # noqa: E402

NAME = "URBAN_QTO_R8_3_MEASUREMENT_FRAME"
OUT = ROOT / "data/reports" / NAME


def jload(p):
    return json.loads(Path(p).read_text())


def junit(path):
    root = ET.parse(path).getroot()
    ts = root if root.tag == "testsuite" else root.find("testsuite")
    c, by = collections.Counter(), collections.defaultdict(collections.Counter)
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
        d = next((x for x in ("tests.r8_3", "tests.r8_2", "tests.r8_1", "tests.r8_0") if cn.startswith(x)), "other")
        by[d][k] += 1
    return dict(ts.attrib), dict(c), {k: dict(v) for k, v in sorted(by.items())}


DECISIONS = [
    ("R8_3_D01", "FRAME_THRESHOLDS", "Preserve agreement <= 0.5 %, contradiction > 0.5 %, checked-dimension residual <= "
     "max(2 mm, 0.2 %) unchanged. Source R8_REVISED_SPEC.v1 §5, status EXTERNAL_FROZEN_SPEC_NOT_PREVIOUSLY_COMMITTED; "
     "decision record committed (tests/r8_3/registers/R8_3_THRESHOLD_PROVENANCE.json) and spec copied into the package.",
     "ACCEPTED_BY_BRIEF"),
    ("R8_3_D02", "HANDLE_DEFECT_ATTRIBUTION", "Promote OBSERVED_HANDLE_TRUNCATION_IN_EXISTING_LIBREDWG_JSON to "
     "PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT (pinned route reproduced it on 2 sources). Layer "
     "NOT_LOCALISED (parser, internal representation or JSON writer).", "ACCEPTED_BY_MIDCOURSE_REVIEW"),
    ("R8_3_D03", "TEXT_DECODING_DELTA", "The 40 U+FFFD rows are EXPLAINED_DELTA only with their row-by-row review; they "
     "carry DOCUMENT_CONTENT REVIEW + IDENTITY BLOCKING (TEXT_UNDECODABLE); no active consumer; future area-label / "
     "identity consumers blocked from using them.", "ACCEPTED_BY_MIDCOURSE_REVIEW"),
    ("R8_3_D04", "ONE_IDENTITY_CONTRACT", "Entity, INSERT, instance-path and block-record handles correlate through "
     "reconcile.handle_basis; no raw string lookup; every INSERT yields one lineage row.", "IMPLEMENTED"),
    ("R8_3_D05", "SET_VALUED_EVIDENCE_FAILS_CLOSED", "A set establishes only the set; intersection is deterministic; "
     "empty -> CONFLICT; >1 member -> no support; a singleton from independent sets is ONE class; membership of a "
     "declaration in a set is never support.", "ACCEPTED_BY_MIDCOURSE_REVIEW"),
    ("R8_3_D06", "DIMLFAC_CANDIDATE_ONLY", "Dimension display / geometry ratios rest on ASSUMPTION:DISPLAY_IN_STANDARD_UNIT "
     "and are CANDIDATE constraint sets: they may contradict or narrow, never verify.", "ACCEPTED_BY_MIDCOURSE_REVIEW"),
    ("R8_3_D07", "CANDIDATES_LOWER_NEVER_RAISE", "Candidate (agent / assumption-bearing) evidence may lower a status to "
     "CONFLICT when it contradicts, never raise one. Plausibility never moves a status; it raises "
     "UNIT_PLAUSIBILITY_QUESTION.", "IMPLEMENTED"),
    ("R8_3_D08", "RELEASE_POLICY_V1", "CONFIRMED_BY_HUMAN supports FINAL only when the confirmation is for the exact source "
     "hash, contradicts no admitted evidence and no constraint set, and at least one non-human item agrees. A human may "
     "resolve a DECLARATION conflict, never override evidence, never confirm in a vacuum.",
     "CLAUDE_RECOMMENDATION_REVIEW_REQUIRED"),
    ("R8_3_D09", "PARSER_INDEPENDENCE_POLICY_B", "Independent parser required when a parser-risk finding is in scope, the "
     "decode pin is not REGISTERED/REPRODUCED, for benchmark qualification and the first migration consumer; otherwise "
     "a QUALIFIED decoder build suffices. No build is qualified today, so B behaves as A for every real project.",
     "CLAUDE_RECOMMENDATION_REVIEW_REQUIRED"),
    ("R8_3_D10", "REFERENCE_REGION", "Only a model-space PLAN region designated as the unit reference is full-size by "
     "definition; other plan regions carry the full-size medium convention as a DECLARATION (UNCONFIRMED until "
     "evidence); a DETAIL without region evidence is BLOCKED (U-2).", "IMPLEMENTED"),
    ("R8_3_D11", "CHORD_TOLERANCE_NOT_IN_FRAME", "Curve approximation is not a frame property; exact ellipses kept, not "
     "flattened, downstream unsupported -> PREVIEW for scale-dependent quantities (R11 CURVE_APPROXIMATION_POLICY).",
     "AGREED_WITH_BRIEF"),
    ("R8_3_D12", "COLUMN_TWO_LAYERS", "Question A (is the column polygon closed?) is source geometry: YES, all 170 "
     "col.str LWPOLYLINEs carry flag 512 and K1 closes them. Question B (deduct from floor finish?) is a trade rule: "
     "TRADE_DEDUCTION_RULE_UNDECIDED (R9 rules-as-data). NET_INSTALL_AREA vs BILLING_MEASUREMENT_AREA recorded; "
     "neither value published.", "ACCEPTED_BY_BRIEF"),
    ("R8_3_D13", "R8_0_CONTRACT_DISPUTES", "F17 and MT-32 (plausibility-contested INSUNITS -> PROVISIONAL) kept unchanged "
     "and registered CONTRACT_DISPUTED: R8.3 computes UNCONFIRMED. MT-33 (Al Rashed PROVISIONAL / set 1) stays "
     "TARGET_NOT_IMPLEMENTED (needs URBAN_R8_REAL_SOURCE) and is contradicted by the R8.3 lab result (CONFLICT, 0 "
     "admitted). F19 (V-CAD-5) stays TARGET_NOT_IMPLEMENTED: V-CAD ids are undefined.", "REVIEW_REQUIRED"),
    ("R8_3_D14", "ACTIVE_UNIT_AUTHORITY_FINDING", "Qortuba QS01 releases quantities on INSUNITS alone "
     "(engine/ingest/source_units.py); Al Rashed R7 treats one unit as one metre (reader) against INSUNITS inch, on "
     "declaration + plausibility. Both AFFECTS_ACTIVE_PUBLISHED_PATH. Nothing changed.", "REPORTED"),
    ("R8_3_D15", "MIGRATION_READY_NO", "No independent real K1/K2 comparison exists, no real frame permits FINAL, no "
     "decoder build is qualified. MIGRATION_READY = NO.", "RESULT"),
]


def main(junit_xml, commit, spec=None):
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    red = jload(ROOT / "data/runs/pinned_redecode/PINNED_REDECODE_RESULTS.json")
    real = jload(ROOT / "research/external_engine_lab/outputs/R8_3_REAL_STATUS.json")
    prov = jload(ROOT / "tests/r8_3/registers/R8_3_THRESHOLD_PROVENANCE.json")
    ef = jload(ROOT / "tests/r8_0/registers/R8_0_EXPECTED_FAILURES.json")
    attrs, counts, by_dir = junit(junit_xml)
    projects = real["projects"]

    def dump(name, obj):
        (OUT / name).write_text(json.dumps(obj, indent=1, default=str, ensure_ascii=False) + "\n")

    dump("UNIT_CONTEXT_REGISTER.json", {"SCHEMA": "URBAN_R8_3_UNIT_CONTEXT_REGISTER_V1", "commit": commit,
                                        "contexts": {p: r["unit_context"] for p, r in projects.items()}})
    dump("UNIT_EVIDENCE_REGISTER.json", {"SCHEMA": "URBAN_R8_3_UNIT_EVIDENCE_REGISTER_V1", "commit": commit,
                                         "extractor": "engine/source/cad/unit_evidence.py (emits evidence; resolver decides)",
                                         "evidence": {p: {"rows": r["unit_evidence_rows"], "scale_notes": r["scale_notes"],
                                                          "excluded": r["unit_context"]["excluded_evidence"],
                                                          "contesting_candidates": r["unit_context"]["contesting_candidates"]}
                                                      for p, r in projects.items()}})
    dump("REGION_MEASUREMENT_TRANSFORM_REGISTER.json", {"SCHEMA": "URBAN_R8_3_REGION_REGISTER_V1", "commit": commit,
                                                        "regions": {p: {"region": r["region"], "region_findings": r["region_findings"]}
                                                                    for p, r in projects.items()}})
    dump("MEASUREMENT_FRAME_REGISTER.json", {"SCHEMA": "URBAN_R8_3_MEASUREMENT_FRAME_REGISTER_V1", "commit": commit,
                                             "frames": {p: r["frame"] for p, r in projects.items()},
                                             "release_policy": FR.DEFAULT_POLICY.policy_id})
    dump("CAD_VALIDATION_PROFILE.json", {
        "SCHEMA": "URBAN_R8_3_CAD_VALIDATION_PROFILE_V1", "commit": commit,
        "requirements": {"A_CAPABILITY": "capability row permits the use", "B_MAPPING": "D1 mapping VERIFIED*",
                         "C_SOURCE": "conservation balanced; decode pin REGISTERED or REPRODUCED",
                         "D_ROUTES": "K1 realised cleanly + parser-independence policy",
                         "E_UNIT": "UNIT_CONTEXT permits FINAL", "F_REGION": "region permits FINAL",
                         "G_FRAME": "MEASUREMENT_FRAME permits FINAL",
                         "H_FINDINGS": "no in-scope finding BLOCKING in a domain the method depends on",
                         "I_DOWNSTREAM": "downstream geometry supports the kind",
                         "METHOD": "scale_dependent declared (never assumed)"},
        "parser_policy": {"id": P.DEFAULT_PARSER_POLICY.policy_id, "option": P.DEFAULT_PARSER_POLICY.option,
                          "qualified_builds": sorted(P.DEFAULT_PARSER_POLICY.qualified_builds),
                          "parser_risk_codes": sorted(P.PARSER_RISK_CODES)},
        "release_policy": FR.DEFAULT_POLICY.policy_id,
        "qs_core_boundary": {"consumes": ["frame status", "allowed use", "blocking requirements + domains",
                                          "profile result", "evidence ids"],
                             "never_consumes": ["raw INSUNITS", "raw viewport scale", "decoder implementation detail"]},
        "real_results": {p: r["cad_profile"] for p, r in projects.items()}})
    dump("PINNED_REDECODE_RESULTS.json", red)
    dump("INDEPENDENT_RECONCILIATION_RESULTS.json", {
        "SCHEMA": "URBAN_R8_3_INDEPENDENT_RECONCILIATION_V1", "commit": commit,
        "INDEPENDENT_REAL_RECONCILIATION": real["INDEPENDENT_REAL_RECONCILIATION"],
        "independent_dxf_found": real["independent_dxf_found"],
        "searched": ["repository", "session uploads"], "expected_file": "P7757_AUTOCAD_2018_INDEPENDENT.dxf",
        "required_provenance": ["original DWG sha256 (P7757: 7f61f3ac...)", "DXF sha256", "export application / version",
                                "DXF format / version", "user confirmation: no explode / purge / audit / scale change / cleaning"],
        "declared_real_tolerance": {"formula_pass": "max(1024*eps*M, 2*M*10^-(digits-1))",
                                    "formula_warn": "max(1e6*eps*M, 10*pass)", "declared_in": "R8.2 (reconcile.real_tolerance)",
                                    "retuning": "forbidden after results are seen"},
        "lineage_fix_in_place": "R8.3 one identity contract (reconcile.handle_basis)",
        "parser_independence_if_run": "INDEPENDENT_PARSER (AutoCAD / ODA export); LibreDWG DWG -> LibreDWG DXF -> ezdxf "
                                      "remains SHARED_PARSER_LINEAGE",
        "real_verdict": "NONE — not fabricated"})
    status_rows = {}
    for p, r in projects.items():
        red_p = red["projects"][p]
        uc, rt, fr = r["unit_context"], r["region"], r["frame"]
        blocking = sorted({b["id"] for v in r["cad_profile"].values() for b in v["blocking"]})
        status_rows[p] = {
            "PROJECT": p, "SOURCE_FILE": r["source_file"], "SOURCE_HASH": r["source_sha256"],
            "ORIGINAL_DWG_AVAILABLE": r["original_dwg_available"],
            "HISTORICAL_DECODE_HASH": r["historical_decode_sha256"],
            "HISTORICAL_DECODER_PIN_STATUS": r["historical_decoder_pin_status"],
            "PINNED_REDECODE_STATUS": red_p["status"], "PINNED_REDECODE_HASH": red_p["output"]["sha256"],
            "HANDLE_REPRESENTATION_STATUS": red_p["handle_truncation_attribution"],
            "K1_STATUS": {"realised": r["k1"], "conservation_balanced": r["conservation_balanced"]},
            "INDEPENDENT_DXF_AVAILABLE": bool(real["independent_dxf_found"]),
            "K2_REAL_STATUS": "NOT_EXECUTED", "PARSER_INDEPENDENCE": "NOT_AVAILABLE (only LibreDWG-derived DXF)",
            "UNIT_CONTEXT_STATUS": uc["status"], "UNIT_CONTEXT_REASON": uc["status_reason"],
            "REGION_MEASUREMENT_TRANSFORM_STATUS": rt["status"], "MEASUREMENT_FRAME_STATUS": fr["status"],
            "CAD_PROFILE_STATUS": "FINAL_NOT_ELIGIBLE", "ALLOWED_USE": fr["allowed_use"],
            "BLOCKING_REASONS": blocking + [f"UNIT_CONTEXT {uc['status']}: {uc['status_reason']}"]}
    dump("REAL_PROJECT_R8_STATUS.json", {"SCHEMA": "URBAN_R8_3_REAL_PROJECT_STATUS_V1", "commit": commit,
                                         "rule": "no project is upgraded because its quantities look right",
                                         "projects": status_rows})
    dump("R8_3_DECISION_REGISTER.json", {"SCHEMA": "URBAN_R8_3_DECISION_REGISTER_V1", "commit": commit,
                                         "decisions": [dict(zip(("id", "topic", "decision", "status"), d)) for d in DECISIONS],
                                         "threshold_provenance": prov})
    dump("R8_3_TEST_RESULTS.json", {"SCHEMA": "URBAN_R8_3_TEST_RESULTS_V1", "commit": commit,
                                    "command": 'python3 -m pytest -p no:cacheprovider -m "not slow" -q --junitxml=full_r83.xml',
                                    "junit_attributes": attrs, "counts": counts, "total": sum(counts.values()),
                                    "by_directory": by_dir,
                                    "r8_0_register": dict(collections.Counter(e["class"] for e in ef["expected_failures"])),
                                    "note": "one run from the final committed tree; counts parsed from junit, not computed"})
    if spec and Path(spec).exists():
        (OUT / "SPEC_EVIDENCE").mkdir()
        shutil.copy(spec, OUT / "SPEC_EVIDENCE" / Path(spec).name)
    write_markdown(OUT, commit, counts, by_dir, attrs, red, real, prov, ef, status_rows)
    zp = OUT.parent / f"{NAME}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, f"{NAME}/{p.relative_to(OUT)}")
    return zp


def write_markdown(out, commit, counts, by_dir, attrs, red, real, prov, ef, rows):
    from research.external_engine_lab import r8_3_package_text as T
    for name, text in T.documents(commit=commit, counts=counts, by_dir=by_dir, attrs=attrs, red=red, real=real,
                                  prov=prov, ef=ef, rows=rows, path_map=MAP.UNIT_FRAME_BY_PATH).items():
        (out / f"{name}.md").write_text(text)


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
