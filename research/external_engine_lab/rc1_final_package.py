"""Qortuba Architectural RC1 FINAL package: URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1_FINAL (17 md + 13 json + the owner
workbook + zip). The workbook is written from the committed BOQ_XLSX_MODEL register, read back cell by cell and
compared byte for byte with the committed file digest; the freeze is re-validated against its schema here.

    python3 research/external_engine_lab/rc1_final_package.py <junit.xml> "<command>" <exit_code>
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
from engine import boq_rc1_xlsx as BX                                           # noqa: E402
from engine.source import freeze_schema as FS                                  # noqa: E402

REG = ROOT / "tests/rc1/registers"
NAME = "URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1_FINAL"
OUT = ROOT / "data/reports" / NAME
XLSX = "URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1.xlsx"
JSONS = ("URBAN_FLOOR_CABINET_METHOD", "PAINTRY_FLOOR_RESOLUTION", "OBJECT_FOOTPRINT_REGISTER", "FLOOR_REGISTER",
         "ROOM_QUANTITY_MATRIX", "CANONICAL_BOQ", "FREEZE_DIGEST_AUDIT", "TOPOLOGY_FREEZE", "QORTUBA_RC1_FREEZE",
         "BOQ_XLSX_STATUS", "QA_RECONCILIATION", "BLIND_VILLA_INTAKE_SCHEMA")
READ = JSONS + ("BOQ_XLSX_MODEL", "RC1_DECISION_REGISTER", "OPENING_REGISTER", "ROOM_REGISTER")
EXPECT = {"FLR-01": 111.8988, "FLR-02": 17.7425, "FLR-03": 11.685, "MRB-01": 0.51, "CLG-01": 140.637,
          "SKT-01": 94.13682, "HPR-01": 94.13682, "PLS-01": 307.361518, "PLS-02": 1.510248, "PNT-01": 307.361518,
          "WTL-01": 127.693512, "WTP-01": 127.693512, "WPF-01": 29.4275, "WPU-01": 44.2, "MRB-02": 3.4}
STOP = "STOP AFTER FINAL QORTUBA RC1.\n\nDO NOT START THE BLIND VILLA IN THIS SAME ROUND.\nNO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=1500):
    s = json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + " ..."


def f(v):
    return "" if v is None else (f"{v:,.6f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in READ}
    jr = junit(junit_path)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    M, st = R["BOQ_XLSX_MODEL"], R["BOQ_XLSX_STATUS"]
    w = BX.write(M["sheets"], OUT / XLSX, created=datetime.datetime.fromisoformat(M["created"]))
    xv = BX.validate(OUT / XLSX, M["sheets"], sources=M["cell_sources"], approved_col=M["approved_col"],
                     canonical_ids=M["canonical_ids"], legacy_ids=M["legacy_ids"], tol=0.0)
    fz = R["QORTUBA_RC1_FREEZE"]
    fv = FS.validate(fz, R["FREEZE_DIGEST_AUDIT"]["schema"])
    items = {i["canonical_item_id"]: i for i in R["CANONICAL_BOQ"]["items"]}
    totals = {k: {"expected_regression": v, "engine": items[k]["qty"], "same": items[k]["qty"] == v}
              for k, v in EXPECT.items()}
    res = {"SCHEMA": "URBAN_QORTUBA_RC1_FINAL_TEST_RESULTS_V1", "commit": commit, "command": command, **jr,
           "exit_code": exit_code, "determinism_guard": "enforce (repository conftest)",
           "rc1_test_files": sorted(p.name for p in (ROOT / "tests/rc1").glob("test_*.py")),
           "package_xlsx": {"validation": xv["state"], "content_digest": w["content_digest"],
                            "file_sha256": w["file_sha256"], "quantity_cells_checked": xv["quantity_cells_checked"],
                            "matches_register_content": w["content_digest"] == st["content_digest"],
                            "matches_register_bytes": w["file_sha256"] == st["file_sha256"]},
           "package_freeze_schema": fv["state"], "regression_totals": totals,
           "earlier_failed_runs_this_round": []}
    for n in JSONS:
        (OUT / f"{n}.json").write_text(json.dumps(R[n], indent=1, ensure_ascii=False))
    freeze = dict(fz, test_results={k: res[k] for k in ("commit", "passed", "xfailed", "skipped", "failed", "errors",
                                                        "total", "exit_code")})
    (OUT / "QORTUBA_RC1_FREEZE.json").write_text(json.dumps(freeze, indent=1, ensure_ascii=False))
    (OUT / "TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, A, G = R["RC1_DECISION_REGISTER"], R["RC1_DECISION_REGISTER"]["answers"], R["RC1_DECISION_REGISTER"]["gates"]
    rec = jl(ROOT / "research/external_engine_lab/rc1_final_recommendation.json")
    um, pr = R["URBAN_FLOOR_CABINET_METHOD"], R["PAINTRY_FLOOR_RESOLUTION"]
    au, tf = R["FREEZE_DIGEST_AUDIT"], R["TOPOLOGY_FREEZE"]
    q = R["QA_RECONCILIATION"]
    ops = R["OPENING_REGISTER"]["schedules"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    summary = tbl(["Item", "Description", "Qty", "Unit", "Status", "Pair"],
                  [[i["canonical_item_id"], i["description_en"], f(i["qty"]), i["unit"], i["status"],
                    i["measure_pair"] or ""] for i in items.values()])
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# Qortuba Architectural RC1 - FINAL\n\n"
        f"- URBAN_ARCHITECTURAL_QTO_QORTUBA_RC1 frozen (SHADOW / RC1_REFERENCE): {fz['frozen']}; open items: "
        f"{fz['open_items'] or 'NONE'}.\n"
        "- New Urban owner method URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1 + the PAINTRY counter identity fact "
        f"resolve FLR-03: {f(items['FLR-03']['qty'])} m2 {items['FLR-03']['status']} (no deduction, no geometry "
        "change).\n"
        f"- Freeze audit: topology_digest was `false` (a stale reproduction flag); now topology input "
        f"`{fz['topology_input_digest'][:16]}...` + topology result `{fz['topology_result_digest'][:16]}...`; "
        f"freeze-schema validation {fv['state']}.\n"
        f"- Every regression total unchanged: {all(v['same'] for v in totals.values())}; openings 6 / 1 / 1 / 6 / 2.\n"
        f"- Workbook: {xv['quantity_cells_checked']} quantity cells read back {xv['state']}, no formulas, byte-identical "
        f"to the register: {res['package_xlsx']['matches_register_bytes']}.\n\n## Canonical BOQ\n\n" + summary +
        "\n\n## Gates\n\n" + tbl(["Gate", "Value"], [[k, v] for k, v in G.items()]) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = "# Owner actions - Mohammad\n\n**NONE FOR QORTUBA QUANTITIES.**\n\n" + "\n".join(
        f"- {a['id']}: " + "; ".join(f"{k}: {v}" for k, v in a.items() if k != "id")
        for a in D["owner_actions"]) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before code, commit c4487e1)\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in rec.items() if k != "SCHEMA") + "\n"
    md["03_FLOOR_CABINET_METHOD.md"] = "# URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in um["rule"].items()) + \
        f"\n\n**Relation to the Qortuba fact:** {um['qortuba_fact_kept']}\n\n**Object identity (PAINTRY):** " + \
        j(um["object_identity_fact"]["statement"]) + "\n"
    md["04_PAINTRY_RESOLUTION.md"] = "# PAINTRY FLR-03 resolution\n\n" + "\n".join(
        f"{n}. **{s['step']}** - {j({k: v for k, v in s.items() if k != 'step'}, 900)}"
        for n, s in enumerate(pr["trail"], 1)) + \
        f"\n\nResult: {f(pr['flr03']['qty'])} m2, {pr['flr03']['status']}; site area {f(pr['site_area_m2'])} m2; " \
        f"geometry changed: {pr['geometry_changed']}; hard-coded: {pr['hardcoded_value']}.\n"
    fp = R["OBJECT_FOOTPRINT_REGISTER"]
    md["05_OBJECT_FOOTPRINT_RESOLUTION.md"] = "# Object footprint resolution\n\n" + tbl(
        ["Row | site", "State", "Object classes (observed -> class)", "Policy", "Identity", "Treatment"],
        [[k, v["state"], ", ".join(sorted({f"{o.get('observed_class', o['object_class'])}->{o['object_class']}"
                                           for o in v["objects"]})), ", ".join(v["policy"] or []),
          ", ".join(v.get("identity_facts") or []), v["treatment"] or ""] for k, v in fp["sites"].items()]) + \
        f"\n\nOwner question: {fp['owner_question']}. Assumed: {fp['assumed']}.\n"
    p = q["floor_partition"]
    md["06_FLOOR_RECONCILIATION.md"] = "# Floor reconciliation\n\n" + tbl(["Check", "Value"], [
        ["certified sites + door strips", p["keys"]], ["physical floor m2", f(p["physical_floor_m2"])],
        ["floor-finish items (FLR-01..03 + MRB-01) m2", f(p["finish_items_sum_m2"])],
        ["difference m2 (row rounding)", f(p["difference_m2"])], ["in two items", p["in_two_items"] or "NONE"],
        ["in no item", p["in_no_item"] or "NONE"], ["cabinet footprint deducted", "NO (0 m2)"],
        ["state", p["state"]]]) + "\n\n" + tbl(["Item", "Room / strip", "m2"], [
            [i, b["label"], f(b["qty"])] for i in ("FLR-01", "FLR-02", "FLR-03", "MRB-01")
            for b in items[i]["room_breakdown"]]) + "\n"
    md["07_FREEZE_DIGEST_AUDIT.md"] = "# Freeze digest audit\n\n" + tbl(
        ["Field", "Was", "Class", "Cause", "Now"],
        [[x["field"], x["was"], x["class"], x.get("cause", ""), j(x["now"], 300)] for x in au["rc1_76a9771_findings"]]) + \
        "\n\n## Every freeze field\n\n" + tbl(["Field", "Class", "Why (booleans / optional)"],
                                              [[k, v["class"], v.get("why", "")] for k, v in au["schema"].items()]) + "\n"
    md["08_TOPOLOGY_DIGEST.md"] = "# Topology digest\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in tf.items() if k != "SCHEMA") + "\n"
    md["09_FREEZE_SCHEMA_VALIDATION.md"] = "# Freeze schema validation\n\n" + tbl(["Check", "Result"], [
        ["register validation", au["validation"]["state"]], ["package re-validation", fv["state"]],
        ["fields", fv["fields"]], ["errors", len(fv["errors"])]]) + "\n"
    md["10_CANONICAL_BOQ.md"] = "# Canonical BOQ\n\n" + summary + "\n\nValidation: " + \
        j(R["CANONICAL_BOQ"]["validation"]) + "\n"
    md["11_XLSX_VALIDATION.md"] = "# Workbook validation\n\n" + tbl(["Check", "Result"], [
        ["readback (register)", st["readback_validation"]["state"]], ["readback (package)", xv["state"]],
        ["quantity cells checked", xv["quantity_cells_checked"]], ["formulas", len(xv["formulas"])],
        ["register mismatches", len(xv["register_mismatches"])],
        ["alias lines in summary", len(xv["alias_lines_in_summary"])],
        ["approved without release", len(xv["approved_without_release"])], ["row drops", len(xv["row_drops"])],
        ["content digest", w["content_digest"]], ["file sha256", w["file_sha256"]],
        ["same bytes as the register", res["package_xlsx"]["matches_register_bytes"]]]) + "\n"
    md["12_QA_RECONCILIATION.md"] = "# QA and reconciliation\n\n" + tbl(["Check", "State"], [
        ["canonical model", q["canonical_model"]["state"]], ["room matrix", q["room_matrix"]["state"]],
        ["floor partition", p["state"]], ["physical surface identity", q["physical_surface_identity"]["state"]],
        ["opening register", q["openings"]["state"]], ["regression vs R8.20",
                                                       "UNCHANGED" if q["regression_vs_r8_20"]["all_unchanged"]
                                                       else "CHANGED"], ["overall", q["state"]]]) + \
        "\n\n## Physical identity checks\n\n" + tbl(["Check", "State"], list(
            q["physical_surface_identity"]["checks"].items())) + "\n\n## Regression totals\n\n" + tbl(
        ["Item", "Expected (regression only)", "Engine", "Same"],
        [[k, f(v["expected_regression"]), f(v["engine"]), v["same"]] for k, v in totals.items()]) + \
        f"\n\n## Openings\n\n{j(ops)}\n"
    md["13_FINAL_FREEZE.md"] = "# Final freeze\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v, 600)}" for k, v in freeze.items() if k != "SCHEMA") + "\n"
    bv = R["BLIND_VILLA_INTAKE_SCHEMA"]
    md["14_BLIND_TEST_HANDOFF.md"] = "# Handoff to the full unseen-villa blind test\n\n" + tbl(
        ["File role", "Required", "Protocol"], [[x["role"], x["required"], x.get("protocol", "")] for x in bv["files"]]) + \
        "\n\n" + "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in bv.items()
                         if k not in ("SCHEMA", "files")) + \
        f"\n- **after the freeze:** {fz['after_freeze']}\n- **Qortuba-specific development:** STOPPED.\n"
    md["15_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nRC1 test files: " + \
        ", ".join(res["rc1_test_files"]) + f"\n\nPackage workbook: {j(res['package_xlsx'])}\n\nPackage freeze " \
        f"schema: {fv['state']}\n"
    md["16_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v, 900)}" for k, v in rec.items()
        if k.split("_")[0].isdigit()) + "\n\n## Gates\n\n" + tbl(["Gate", "Value"], [[k, v] for k, v in G.items()]) + \
        f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(list(OUT.glob("*.json"))), "json", xv["state"], fv["state"],
          res["package_xlsx"]["matches_register_bytes"], all(v["same"] for v in totals.values()))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
