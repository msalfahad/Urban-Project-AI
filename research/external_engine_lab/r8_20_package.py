"""R8.20 review package: URBAN_QTO_R8_20_HUMAN_REVIEW_BOQ_EXPORT_SOURCE_ANCHOR (18 md + 19 json + the shadow BOQ xlsx
+ zip). The xlsx is generated here from the committed BOQ_REPORT_SHADOW register and validated cell by cell.

    python3 research/external_engine_lab/r8_20_package.py <junit.xml> "<command>" <exit_code>
"""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit, tbl                                            # noqa: E402
from engine import boq_xlsx as BX                                               # noqa: E402

REG = ROOT / "tests/r8_20/registers"
NAME = "URBAN_QTO_R8_20_HUMAN_REVIEW_BOQ_EXPORT_SOURCE_ANCHOR"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_PHYSICAL_FACT_REGISTER", "HUMAN_REVIEW_REGISTER",
         "I1471_COLUMN_CONCEALMENT_REGISTER", "CLOSURE_RELEASE_STATUS", "QUANTITY_REGRESSION", "BOQ_REPORT_SCHEMA",
         "BOQ_REPORT_SHADOW", "BOQ_XLSX_SCHEMA", "BOQ_XLSX_STATUS", "SOURCE_ANCHOR_STATUS", "SOURCE_ANCHOR_PLAN",
         "MCP_DONOR_REVIEW", "PDF_ENGINE_ROADMAP", "SECOND_PROJECT_PLAN", "PRODUCTION_GATE_STATUS",
         "QORTUBA_R8_20_STATUS", "R8_20_DECISION_REGISTER")
STOP = "STOP AFTER R8.20.\nNO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=900):
    return json.dumps(v, ensure_ascii=False)[:n]


def bullets(d):
    return "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 900)}" for k, v in d.items())


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    xp = OUT / "URBAN_QTO_R8_20_SHADOW_BOQ.xlsx"
    rep = R["BOQ_REPORT_SHADOW"]["report"]
    w = BX.write(rep, xp, created=datetime.datetime(2026, 10, 2))
    xv = BX.validate(xp, rep)
    res = {"SCHEMA": "URBAN_R8_20_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest)",
           "r8_20_test_files": sorted(p.name for p in (ROOT / "tests/r8_20").glob("test_*.py")),
           "package_xlsx": {"validation": xv["state"], "content_digest": w["content_digest"],
                            "matches_register": w["content_digest"] == R["BOQ_XLSX_STATUS"]["content_digest"]}}
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_20_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O = R["R8_20_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"]
    A, G = D["answers"], D["gates"]
    CL, H, I = R["CLOSURE_RELEASE_STATUS"], R["HUMAN_REVIEW_REGISTER"], R["I1471_COLUMN_CONCEALMENT_REGISTER"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    cl_tbl = tbl(["Closure", "Human review", "Level before", "Maximum justified", "Missing for next level"],
                 [[k, v["human_review"], v["current_level_before_review"], v["maximum_justified_level"],
                   ", ".join(v["missing_for_next_level"])] for k, v in CL["closures"].items()])
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.20 - human closure review, I1471 rationale, release review, BOQ XLSX, source-anchor / second-project "
        f"plan\n\n**{O['headline']}**\n\n" + cl_tbl +
        f"\n\n- Quantities: {A['7_quantity_changed']}.\n- I1471: {A['4_200mm_intentional']}.\n"
        f"- BOQ XLSX: {A['15_xlsx_implemented']}; rows {A['17_rows_exported']}; package file validation {xv['state']}.\n"
        f"- Silent-error path: {A['29_new_silent_error']}\n\n" + tests + "\n\n" + bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {k: O[k] for k in ("required_now", "recommended_now", "when_available", "answered_this_round",
                           "do_not_ask")}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    md["03_H2430_H2431_HUMAN_REVIEW.md"] = "# H2430 / H2431 human review\n\n" + bullets(
        {r["closure_name"]: r for r in H["reviews"] if r["closure_name"] != "I1471"}) + "\n\n" + bullets(
        {k: v for k, v in H["states"].items() if k != "I1471"}) + "\n"
    md["04_I1471_HUMAN_REVIEW.md"] = "# I1471 human review\n\n" + bullets(
        {"review": next(r for r in H["reviews"] if r["closure_name"] == "I1471"), "state": H["states"]["I1471"]}) + "\n"
    md["05_I1471_COLUMN_CONCEALMENT_FACT.md"] = "# I1471 column-concealment rationale\n\n" + bullets(
        {k: v for k, v in I.items() if k != "SCHEMA"}) + "\n\n## Fact\n" + bullets(
        R["OWNER_PHYSICAL_FACT_REGISTER"]) + "\n"
    md["06_CLOSURE_RELEASE_REVIEW.md"] = "# Closure release review\n\n" + cl_tbl + "\n\n" + bullets(
        {k: CL[k] for k in ("policy", "levels", "released_level_exists", "i1471_grading", "cross_route",
                            "production")}) + "\n"
    QR = R["QUANTITY_REGRESSION"]
    md["07_QUANTITY_REGRESSION.md"] = "# Quantity regression\n\n" + tbl(
        ["Row", "R8.19", "R8.20", "Unchanged"], [[k, v["R8.19"], v["R8.20"], v["unchanged"]]
                                                for k, v in QR["rows"].items()]) + "\n\n" + bullets(
        {k: QR[k] for k in ("all_unchanged", "all_digests_same", "digests", "reproduces_r8_19_blind")}) + "\n"
    md["08_BOQ_XLSX_DESIGN.md"] = "# BOQ XLSX design\n\n" + bullets(
        {k: v for k, v in R["BOQ_XLSX_SCHEMA"].items() if k != "SCHEMA"}) + "\n\n## Evidence mapping\n" + bullets(
        R["BOQ_REPORT_SCHEMA"]["evidence_mapping"]) + "\n"
    B = R["BOQ_REPORT_SHADOW"]
    md["09_BOQ_XLSX_RESULT.md"] = f"# BOQ XLSX result\n\n**{B['banner']}**\n\n" + tbl(
        ["Item", "Description (EN)", "Qty", "Unit", "Status"],
        [[r["ITEM_CODE"], r["DESCRIPTION_EN"], r["QTY"], r["UNIT"], r["STATUS"]] for r in rep["rows"]
         if r["ROW_KIND"] == "TOTAL"]) + "\n\n" + bullets(
        {"register": R["BOQ_XLSX_STATUS"], "package file": res["package_xlsx"],
         "status changes vs R8.19": B["status_changes_vs_r8_19"], "why": B["why"], "status counts":
         B["status_counts"]}) + "\n"
    md["10_SOURCE_ANCHOR_PLAN.md"] = "# Source-anchor plan\n\n" + bullets(
        {k: v for k, v in R["SOURCE_ANCHOR_PLAN"].items() if k != "SCHEMA"}) + "\n\n## Status\n" + bullets(
        R["SOURCE_ANCHOR_STATUS"]) + "\n"
    md["11_MCP_DONOR_REVIEW.md"] = "# MCP / donor review\n\n" + bullets(
        {k: v for k, v in R["MCP_DONOR_REVIEW"].items() if k != "SCHEMA"}) + "\n"
    md["12_PDF_ENGINE_ROADMAP.md"] = "# PDF / document engine roadmap\n\n" + bullets(
        {k: v for k, v in R["PDF_ENGINE_ROADMAP"].items() if k != "SCHEMA"}) + "\n"
    md["13_SECOND_PROJECT_PLAN.md"] = "# Second-project plan\n\n" + bullets(
        {k: v for k, v in R["SECOND_PROJECT_PLAN"].items() if k != "SCHEMA"}) + "\n"
    md["14_PRODUCTION_GATES.md"] = "# Production gates\n\n" + tbl(
        ["Gate", "State", "Met"], [[k, v["state"], v["met"]] for k, v in R["PRODUCTION_GATE_STATUS"]["gates"].items()]) \
        + "\n\n" + bullets({k: R["PRODUCTION_GATE_STATUS"][k] for k in ("firestore_approved_writes",
                                                                        "production_migration")}) + "\n"
    md["15_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## R8.21\n{A['30_r8_21']}\n\n{STOP}\n"
    md["16_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.20 test files: " + \
        ", ".join(res["r8_20_test_files"]) + "\n"
    md["17_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + 1, "json + xlsx", xv["state"], res["package_xlsx"]["matches_register"])


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
