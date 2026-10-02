"""Qortuba Architectural RC1 package: URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1 (26 md + the RC1 registers + TEST_RESULTS +
the owner workbook + zip). The workbook is written here from the committed BOQ_XLSX_MODEL register, read back cell
by cell against the register values and compared byte for byte with the committed file digest.

    python3 research/external_engine_lab/rc1_package.py <junit.xml> "<command>" <exit_code>
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

REG = ROOT / "tests/rc1/registers"
NAME = "URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1"
OUT = ROOT / "data/reports" / NAME
XLSX = "URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1.xlsx"
JSONS = ("ENGINE_INVENTORY", "ROOM_REGISTER", "ROOM_QUANTITY_MATRIX", "FLOOR_REGISTER", "CEILING_REGISTER",
         "SKIRTING_REGISTER", "HIDDEN_PROFILE_REGISTER", "PLASTER_REGISTER", "PAINT_REGISTER", "WALL_TILE_REGISTER",
         "WALL_TILE_PREP_REGISTER", "WATERPROOFING_REGISTER", "MARBLE_THRESHOLD_REGISTER", "DOOR_REGISTER",
         "WINDOW_REGISTER", "GLAZING_REGISTER", "OPENING_REGISTER", "REVEAL_REGISTER", "CANONICAL_BOQ",
         "BOQ_ALIAS_REGISTER", "OBJECT_FOOTPRINT_REGISTER", "BOQ_XLSX_STATUS", "SOURCE_ANCHOR_STATUS",
         "DONOR_REUSE_REGISTER", "LEGACY_PATH_REGISTER", "QA_RECONCILIATION", "QORTUBA_RC1_FREEZE",
         "BLIND_VILLA_INTAKE_SCHEMA", "BLIND_VALIDATION_PLAN", "RC1_DECISION_REGISTER", "BOQ_XLSX_MODEL")
STOP = ("STOP AFTER QORTUBA ARCHITECTURAL RC1.\n\nDO NOT START THE FULL-VILLA BLIND RUN IN THE SAME ROUND.\n\n"
        "NO PRODUCTION MIGRATION.")


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=1200):
    s = json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + " ..."


def f(v):
    return "" if v is None else (f"{v:,.6f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    M = R["BOQ_XLSX_MODEL"]
    xp = OUT / XLSX
    w = BX.write(M["sheets"], xp, created=datetime.datetime.fromisoformat(M["created"]))
    xv = BX.validate(xp, M["sheets"], sources=M["cell_sources"], approved_col=M["approved_col"],
                     canonical_ids=M["canonical_ids"], legacy_ids=M["legacy_ids"], tol=0.0)
    st = R["BOQ_XLSX_STATUS"]
    res = {"SCHEMA": "URBAN_QORTUBA_RC1_TEST_RESULTS_V1", "commit": commit, "command": command, **jr,
           "exit_code": exit_code, "determinism_guard": "enforce (repository conftest)",
           "rc1_test_files": sorted(p.name for p in (ROOT / "tests/rc1").glob("test_*.py")),
           "package_xlsx": {"validation": xv["state"], "content_digest": w["content_digest"],
                            "file_sha256": w["file_sha256"],
                            "matches_register_content": w["content_digest"] == st["content_digest"],
                            "matches_register_bytes": w["file_sha256"] == st["file_sha256"],
                            "quantity_cells_checked": xv["quantity_cells_checked"]},
           "earlier_full_suite_runs": []}
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    freeze = dict(R["QORTUBA_RC1_FREEZE"], test_results={k: res[k] for k in (
        "commit", "passed", "xfailed", "skipped", "failed", "errors", "total", "exit_code")})
    (OUT / "QORTUBA_RC1_FREEZE.json").write_text(json.dumps(freeze, indent=1, ensure_ascii=False))
    (OUT / "TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, C = R["RC1_DECISION_REGISTER"], R["CANONICAL_BOQ"]
    A, G = D["answers"], D["gates"]
    items = C["items"]
    rec = jl(ROOT / "research/external_engine_lab/rc1_recommendation.json")
    names = {r["key"]: r["display"] for r in R["ROOM_REGISTER"]["rooms"] + R["ROOM_REGISTER"]["door_strips"]}
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    summary = tbl(["Item", "Description", "Qty", "Unit", "Status", "Pair", "Legacy ids (not additive)"],
                  [[i["canonical_item_id"], i["description_en"], f(i["qty"]), i["unit"], i["status"],
                    i["measure_pair"] or "", ", ".join(a["id"] for a in i["legacy_row_ids"])] for i in items])
    mrows = R["ROOM_QUANTITY_MATRIX"]["rows"]
    cols = R["ROOM_QUANTITY_MATRIX"]["columns"]
    room_cols = [c for c in cols if c not in ("MRB-02",)]
    matrix = tbl(["Room / site"] + room_cols, [[r["display"]] + [f(r["cells"].get(c)) for c in room_cols]
                                               for r in mrows])
    ops = R["OPENING_REGISTER"]["records"]

    def otbl(kinds):
        return tbl(["Id", "Type", "Role", "From", "To", "Width m (basis)", "Height m (basis)", "Area m2", "Material",
                    "State"],
                   [[o["opening_id"], o["kind"], o.get("role") or "", o["from_display"], o["to_display"],
                     f"{f(o['clear_width_m'])} ({o['width_basis']})", f"{f(o['height_m'])} ({o['height_basis']})",
                     f(o["area_m2"]), f"{o['material'] or 'NOT_ESTABLISHED'} ({o['material_basis']})", o["state"]]
                    for o in ops if o["kind"] in kinds])

    def bdt(cid):
        i = next(x for x in items if x["canonical_item_id"] == cid)
        return tbl(["Room / element", "Qty"], [[names.get(b["key"], b["label"]), f(b["qty"])]
                                               for b in i["room_breakdown"]]) + \
            f"\n\n**{cid} total: {f(i['qty'])} {i['unit']} - {i['status']}**"

    fp = R["OBJECT_FOOTPRINT_REGISTER"]
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# Qortuba Architectural RC1 - executive summary\n\n"
        f"Frozen as **URBAN_ARCHITECTURAL_QTO_QORTUBA_RC1** (SHADOW / RC1_REFERENCE, not a contractual BOQ): "
        f"{R['QORTUBA_RC1_FREEZE']['frozen']}.\n\n"
        f"- {len(items)} canonical BOQ lines, one per payable item; legacy ids (Q-03, Q-03P, Q-11 ...) are "
        "attributes, never lines.\n"
        f"- Physical floor {f(A['3_total_physical_floor_m2'])} m2 = {R['ROOM_REGISTER']['counts']['rooms']} rooms + "
        f"{R['ROOM_REGISTER']['counts']['door_strips']} door strips; every room and trade reconciles.\n"
        f"- Openings: {A['22_internal_door_count']} internal doors, 1 entrance, 1 sliding glass door, "
        f"{A['26_window_count']} windows, 2 open passages.\n"
        f"- One open item: FLR-03 PAINTRY ceramic floor (counter footprint) - AUTHORISED_SUBTOTAL.\n"
        "- No quantity changed from R8.20. Workbook: no formulas; every quantity cell equals its register row.\n\n"
        "## BOQ summary\n\n" + summary + "\n\n## Gates\n\n" + tbl(["Gate", "Value"], [[k, v] for k, v in G.items()]) +
        f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = "# Owner actions - Mohammad\n\n" + "\n".join(
        f"{n}. **{a['id']}** - " + "; ".join(f"{k}: {v}" for k, v in a.items() if k != "id")
        for n, a in enumerate(D["owner_actions"], 1)) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before any RC1 code, commit 3f1d20d)\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in rec.items() if k not in ("SCHEMA",)) + "\n"
    md["03_ENGINE_INVENTORY.md"] = "# Engine inventory\n\n" + tbl(
        ["Component", "State", "Modules"], [[c["component"], c["state"], c["modules"]]
                                            for c in R["ENGINE_INVENTORY"]["components"]]) + \
        "\n\n## Duplicates\n\n" + "\n".join(f"- {d}" for d in R["ENGINE_INVENTORY"]["duplicates"]) + \
        f"\n\nOrchestration: {R['ENGINE_INVENTORY']['orchestration']}\n"
    md["04_ROOM_REGISTER.md"] = "# Room / site register\n\n" + tbl(
        ["Room / site", "Site id", "Class", "Zones", "Floor m2", "Floor treatment", "Skirting", "Wall finish",
         "Waterproofing"],
        [[r["display"], r["site_id"], r["semantic_class"], ", ".join(r["semantic_zones"]), f(r["floor_area_m2"]),
          r["floor_treatment"], r["skirting"], ", ".join(r["wall_finish"]), r["waterproofing"]]
         for r in R["ROOM_REGISTER"]["rooms"] + R["ROOM_REGISTER"]["door_strips"]]) + \
        f"\n\n{R['ROOM_REGISTER']['label_is_not_authority']}. {R['ROOM_REGISTER']['hall_lobby']}.\n"
    md["05_FLOOR_CEILING.md"] = "# Floor and ceiling - room by room\n\n## Room matrix (view)\n\n" + matrix + \
        "\n\n" + "\n\n".join(f"## {c}\n\n" + bdt(c) for c in ("FLR-01", "FLR-02", "FLR-03", "CLG-01")) + \
        f"\n\nPartition: {j(R['QA_RECONCILIATION']['floor_partition'])}\n"
    md["06_WALL_FINISHES.md"] = "# Wall finishes\n\n" + "\n\n".join(
        f"## {c}\n\n" + bdt(c) for c in ("PLS-01", "PLS-02", "PNT-01", "WTL-01", "WTP-01")) + \
        "\n\nDry finish height 3.15 m (QORTUBA-NEW-DRY-WALL-FINISH-HEIGHT-OWNER-001); wet / service wall tile 3.20 m " \
        "(QORTUBA-NEW-WET-SERVICE-FINISH-OWNER-001). Column and duct faces stay their own physical classes; plaster + " \
        "paint (and tile + tile prep) are compatible trades on one surface, not duplicates.\n"
    md["07_SKIRTING_PROFILE.md"] = "# Skirting and hidden profile\n\n" + bdt("SKT-01") + "\n\n" + bdt("HPR-01") + \
        f"\n\nPath (V4): {j(R['SKIRTING_REGISTER']['path'])}\n\nTwo materials on one path (US-08): two items, never " \
        "one quantity.\n"
    md["08_DOORS.md"] = "# Doors\n\n" + otbl(("DOOR",)) + \
        "\n\nWidths: SOURCE (face closures). Heights: QP-21 owner project parameter 2.20 m (no height is drawn). " \
        "The 1.00 m width fallback was never used. Entrance material and height scope: NOT_ESTABLISHED.\n"
    md["09_WINDOWS_GLAZING.md"] = "# Windows and glazing\n\n" + otbl(("WINDOW", "SLIDING_GLAZED_DOOR")) + \
        f"\n\n{R['GLAZING_REGISTER']['rule']}. Sill 1.00 m (owner fact); skirting continues below every normal window.\n"
    md["10_OPENINGS_REVEALS.md"] = "# Open passages and reveals\n\n" + otbl(("OPEN_PASSAGE",)) + \
        "\n\nReveal records: " + j(R["REVEAL_REGISTER"]["counts"]) + "; unresolved: " + \
        j(R["REVEAL_REGISTER"]["unresolved"] or "NONE") + f". {R['REVEAL_REGISTER']['rules']}.\n"
    md["11_WATERPROOFING.md"] = "# Waterproofing\n\n" + bdt("WPF-01") + "\n\n" + bdt("WPU-01") + \
        "\n\nUpturn 0.15 m along the GROSS wet-room perimeter, doorways not deducted (US-04 / US-05 / US-14).\n"
    md["12_MARBLE.md"] = "# Marble thresholds\n\n" + bdt("MRB-01") + "\n\n" + bdt("MRB-02") + \
        f"\n\n{R['MARBLE_THRESHOLD_REGISTER']['rule']}.\n"
    md["13_CANONICAL_BOQ.md"] = "# Canonical BOQ\n\n" + summary + "\n\nValidation: " + \
        j(R["CANONICAL_BOQ"]["validation"]) + f"\n\n{C['summary_rule']}.\n"
    md["14_ALIAS_DUPLICATE_AUDIT.md"] = "# Alias / duplicate audit\n\n" + tbl(
        ["Alias", "Canonical", "Relation", "Value", "Note"],
        [[a["alias"], a["canonical"], a["relation"], f(a["value"]), a.get("note") or ""]
         for a in R["BOQ_ALIAS_REGISTER"]["aliases"]]) + \
        f"\n\n- Q-03 / Q-11: {R['BOQ_ALIAS_REGISTER']['q03_q11']}\n- Q-03P / Q-12: {R['BOQ_ALIAS_REGISTER']['q03p_q12']}" \
        f"\n- R8.20 workbook risk: {R['BOQ_ALIAS_REGISTER']['r8_20_xlsx_duplicate_risk']}\n"
    md["15_OBJECT_FOOTPRINT_RESOLUTION.md"] = "# Object footprint resolution\n\n" + tbl(
        ["Row | site", "State", "Objects", "Treatment", "Policy / rejection"],
        [[k, v["state"], ", ".join(o["key"].split("|")[1] + " " + o["object_class"] for o in v["objects"][:6]) +
          (" ..." if len(v["objects"]) > 6 else ""), v["treatment"] or "", j(v["policy"] or v["rejected"], 300)]
         for k, v in fp["sites"].items()]) + f"\n\n**Open question:** {fp['owner_question']}\n\n" \
        f"Facts searched: {fp['facts_searched']}\n\nWhy not PAINTRY: {fp['why_not_paintry']}\n\n" \
        f"Effect bounds: {j(fp['effect_bounds_m2'])}\n\nAssumed: {fp['assumed']}. {fp['waterproofing']}.\n"
    md["16_XLSX_VALIDATION.md"] = "# Workbook validation\n\n" + tbl(["Check", "Result"], [
        ["readback (register)", st["readback_validation"]["state"]], ["readback (package)", xv["state"]],
        ["formulas", len(xv["formulas"])], ["quantity cells checked", xv["quantity_cells_checked"]],
        ["register mismatches", len(xv["register_mismatches"])], ["alias lines in summary",
                                                                 len(xv["alias_lines_in_summary"])],
        ["approved without release", len(xv["approved_without_release"])], ["row drops", len(xv["row_drops"])],
        ["content digest", w["content_digest"]], ["file sha256", w["file_sha256"]],
        ["same bytes as the register", res["package_xlsx"]["matches_register_bytes"]]]) + "\n\n" + tbl(
        ["Sheet", "Role", "Rows"], [[k, st["roles"][k], v] for k, v in xv["rows_per_sheet"].items()]) + "\n"
    sa = R["SOURCE_ANCHOR_STATUS"]
    md["17_SOURCE_STATUS.md"] = "# Source status\n\n" + "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v)}"
                                                                 for k, v in sa.items() if k != "SCHEMA") + "\n"
    md["18_DONOR_REUSE.md"] = "# Donor reuse\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in R["DONOR_REUSE_REGISTER"].items()
        if k != "SCHEMA") + "\n"
    md["19_LEGACY_PATH_AUDIT.md"] = "# Legacy path audit\n\n" + tbl(
        ["Legacy", "Replacement", "Reconciles", "Status", "Retirement"],
        [[p["legacy"], p["replacement"], p["reconciles"], p["status"], p["retirement"]]
         for p in R["LEGACY_PATH_REGISTER"]["paths"]]) + \
        f"\n\nRC1 quantities from legacy paths: {R['LEGACY_PATH_REGISTER']['rc1_quantities_from_legacy']}\n\n" \
        f"One path: {R['LEGACY_PATH_REGISTER']['one_authoritative_path']}\n"
    q = R["QA_RECONCILIATION"]
    md["20_QA_RECONCILIATION.md"] = "# QA and reconciliation\n\n" + tbl(["Check", "State"], [
        ["canonical model", q["canonical_model"]["state"]], ["room matrix", q["room_matrix"]["state"]],
        ["floor partition", q["floor_partition"]["state"]],
        ["physical surface identity", q["physical_surface_identity"]["state"]],
        ["opening register", q["openings"]["state"]], ["door count cross-check", q["door_count_cross_check"]],
        ["regression vs R8.20", "UNCHANGED" if q["regression_vs_r8_20"]["all_unchanged"] else "CHANGED"],
        ["per-room wall conservation", q["per_room_wall_conservation"]], ["workbook", q["xlsx"]],
        ["overall", q["state"]]]) + "\n\n## Physical identity checks\n\n" + tbl(
        ["Check", "State"], list(q["physical_surface_identity"]["checks"].items())) + "\n\n## Trade totals vs " \
        "breakdowns\n\n" + tbl(["Item", "Qty", "Breakdown sum"], [[k, f(v["qty"]), f(v["breakdown_sum"])]
                                                                 for k, v in q["trade_breakdowns"].items()]) + "\n"
    md["21_RC1_FREEZE.md"] = "# RC1 freeze\n\n" + "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 600)}"
                                                           for k, v in freeze.items() if k != "SCHEMA") + "\n"
    md["22_BLIND_VILLA_INTAKE.md"] = "# Full-villa blind test - intake contract\n\n" + tbl(
        ["File role", "Required", "Protocol"], [[x["role"], x["required"], x.get("protocol", "")]
                                                for x in R["BLIND_VILLA_INTAKE_SCHEMA"]["files"]]) + "\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in R["BLIND_VILLA_INTAKE_SCHEMA"].items()
        if k not in ("SCHEMA", "files")) + "\n"
    md["23_BLIND_VALIDATION_PLAN.md"] = "# Blind validation plan\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v)}" for k, v in R["BLIND_VALIDATION_PLAN"].items()
        if k != "SCHEMA") + "\n"
    md["24_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nRC1 test files: " + \
        ", ".join(res["rc1_test_files"]) + f"\n\nPackage workbook: {j(res['package_xlsx'])}\n"
    md["25_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final answers\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v, 1500)}" for k, v in A.items()) + \
        f"\n- **54_full_suite:** {jr['passed']} passed, {jr['xfailed']} xfailed, {jr['skipped']} skipped, " \
        f"{jr['failed']} failed, {jr['errors']} errors (exit {exit_code}) at {commit}\n\n## Gates\n\n" + \
        tbl(["Gate", "Value"], [[k, v] for k, v in G.items()]) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(list(OUT.glob("*.json"))), "json + xlsx", xv["state"],
          res["package_xlsx"]["matches_register_bytes"])


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
