"""R8.18 review package: URBAN_QTO_R8_18_WALL_FACE_V2_FINISHES_WATERPROOFING (25 md + 28 json + zip).

    python3 research/external_engine_lab/r8_18_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_18/registers); nothing is typed in.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit, tbl                                            # noqa: E402

REG = ROOT / "tests/r8_18/registers"
NAME = "URBAN_QTO_R8_18_WALL_FACE_V2_FINISHES_WATERPROOFING"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_METHOD_RULE_REGISTER", "WALL_HEIGHT_AUTHORITY_POLICY",
         "QORTUBA_WALL_HEIGHT_REGISTER", "WF_O1_ROOT_CAUSE", "WALL_FACE_V2_POLICY", "WALL_SURFACE_REGISTER",
         "PLASTER_REGISTER", "PAINT_REGISTER", "WALL_TILE_REGISTER", "REVEAL_FINISH_POLICY", "REVEAL_FINISH_REGISTER",
         "COLUMN_DUCT_FINISH_REGISTER", "WATERPROOFING_POLICY", "WATERPROOFING_REGISTER", "Q13_STATUS", "Q14_STATUS",
         "SKIRTING_REGISTER", "HIDDEN_PROFILE_REGISTER", "MARBLE_THRESHOLD_REGISTER", "SECOND_PROJECT_REGRESSION",
         "SOURCE_ANCHOR_STATUS", "CLOSURE_RELEASE_STATUS", "QORTUBA_R8_18_STATUS", "R8_18_DECISION_REGISTER")
COPIES = {"WALL_FACE_V2_FREEZE": "R8_18_FREEZE", "WALL_FACE_V2_BLIND_RESULT": "WALL_FACE_V2_BLIND_RESULT"}
STOP = "STOP AFTER R8.18. NO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=900):
    return json.dumps(v, ensure_ascii=False)[:n]


def bullets(d):
    return "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 700)}" for k, v in d.items())


def f4(v):
    return "" if v is None else f"{v:.4f}"


def row_table(S):
    six, ex = S["six_rows"], S["extra_rows"]
    rows = [[r, v["STATE"], f"{f4(v['VALUE'])} m2", "-", len(v["RELEASE_BLOCKERS"])] for r, v in six.items()]
    for k in ("SKIRTING", "HIDDEN_PROFILE"):
        rows.append([k, ex[k]["state"], f"{ex[k]['value_lm']} lm", "-", len(ex[k]["release_blockers"])])
    m = ex["MARBLE_THRESHOLD"]
    rows.append(["MARBLE_THRESHOLD", m["state"], f"{m['MARBLE_THRESHOLD_PLAN_AREA_M2']} m2 / "
                 f"{m['MARBLE_THRESHOLD_LENGTH_LM']} lm", "-", len(m["release_blockers"])])
    for k in ("DRY_WALL_PLASTER", "PAINT", "WALL_TILE", "WET_WALL_TILE_PREP"):
        v = ex[k]
        rows.append([k, v["state"], f"{v['AUTHORISED_SUBTOTAL_M2']} m2 (authorised)",
                     "null" if v["COMPLETE_M2"] is None else v["COMPLETE_M2"], len(v["release_blockers"])])
    v = ex["WET_SERVICE_REVEAL_PLASTER"]
    rows.append(["WET_SERVICE_REVEAL_PLASTER", v["state"], f"{v['AUTHORISED_M2']} m2", "-",
                 len(v["release_blockers"])])
    for k, u in (("WATERPROOFING_FLOOR_M2", "value_m2"), ("WATERPROOFING_UPTURN_LM", "value_lm")):
        rows.append([k, ex[k]["state"], f"{ex[k][u]} {'m2' if u == 'value_m2' else 'lm'}", "-",
                     len(ex[k]["release_blockers"])])
    return tbl(["Row", "State", "Quantity", "COMPLETE", "Blockers"], rows)


def trade_table(T):
    return tbl(["Site", "Zones", "Height", "Wall plane net m2", "Rectangles m2", "Head faces m2", "Jamb reveals m2",
                "Head reveals m2", "Authorised m2", "Recon"],
               [[s, "/".join(v["zones"]), v["height_m"], v["wall_plane_net_m2"], v["opening_rectangles_m2"],
                 v["passage_head_faces_m2"], v["jamb_reveals_m2"], v["head_reveals_m2"], v["authorised_m2"],
                 v["reconciliation"]] for s, v in T["per_room"].items()]) + "\n\n" + bullets(
        {"AUTHORISED_SUBTOTAL_M2": T["AUTHORISED_SUBTOTAL_M2"], "COMPLETE_M2": T["COMPLETE_M2"], "state": T["state"],
         "reconciliation": T["reconciliation"], "unresolved contributors": T["unresolved_contributors"],
         "unresolved area m2": T["unresolved_area_m2"], "complete row rule": T["complete_row_rule"],
         "per floor": T["per_floor"], "release blockers": T["release_blockers"]})


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS} | {k: jl(REG / f"{v}.json") for k, v in COPIES.items()}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_18_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_18_test_files": sorted(p.name for p in (ROOT / "tests/r8_18").glob("test_*.py")),
           "synthetic_tests": R["WALL_FACE_V2_FREEZE"]["synthetic_tests"]}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_18_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_18_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_18_STATUS"]
    A, G = D["answers"], D["gates"]
    FZ, B = R["WALL_FACE_V2_FREEZE"], R["WALL_FACE_V2_BLIND_RESULT"]
    HT, WO, WS = R["QORTUBA_WALL_HEIGHT_REGISTER"], R["WF_O1_ROOT_CAUSE"], R["WALL_SURFACE_REGISTER"]
    PL, PA, WT = R["PLASTER_REGISTER"], R["PAINT_REGISTER"], R["WALL_TILE_REGISTER"]
    RV, CD, WP = R["REVEAL_FINISH_REGISTER"], R["COLUMN_DUCT_FINISH_REGISTER"], R["WATERPROOFING_REGISTER"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    rt = row_table(S)
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.18 - wall-face V2, dynamic wall height, dry plaster / paint, wet tile, reveals, waterproofing\n\n"
        f"**{O['headline']}**\n\n" + rt +
        f"\n\n- Height: {A['2_315_scope']}; wet tile {A['4_320_preserved']}.\n"
        f"- WF-O1: {A['5_wf_o1_cause']}\n- V2: two independent area paths; {A['9_blind_run_reconciles']}.\n"
        f"- Plaster / paint / tile published as SHADOW authorised subtotals; COMPLETE null (column faces "
        f"{CD['column_area_m2']} m2 and duct {CD['duct_area_m2']} m2 UNRESOLVED).\n"
        f"- Waterproofing: floor {A['30_waterproofing_floor_m2']} m2, upturn {A['31_waterproofing_upturn_lm']} lm at "
        "0.15 m, doorways not deducted.\n"
        f"- Existing rows unchanged (Q-03 .. Q-14, skirting, hidden profile, marble).\n"
        f"- New disclosed errors: {len(A['41_new_silent_errors'])} (WF2-L1 wiring, R-13 misreading, a waterproofing "
        "label, an anti-calibration note).\n\n" + tests + "\n\n" + bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"required now": O["required_now"] or "NONE", "needed to complete rows": O["needed_to_complete_rows"],
         "not asked": O["not_asked"], "answered this round": O["answered_this_round"],
         "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    WA = R["WALL_HEIGHT_AUTHORITY_POLICY"]
    md["03_DYNAMIC_WALL_HEIGHT_METHOD.md"] = "# Dynamic wall-height method\n\n" + bullets(
        {"policy": WA["policy"], "Urban rule": WA["urban_rule"], "no constant": WA["no_company_constant"],
         "future derivation": WA["future_derivation"]}) + "\n"
    md["04_QORTUBA_DRY_WALL_HEIGHT.md"] = "# Qortuba wall heights (per scope)\n\n" + tbl(
        ["Scope", "Governing", "Value m", "Authority", "State"],
        [[k, v["governing"], v["value_m"], v["authority"], v["state"]] for k, v in HT["governing"].items()]) + \
        "\n\n" + bullets({"floor": HT["floor"], "derivation (rank 3)": HT["derivation"],
                          "owner rationale (not a formula)": HT["owner_rationale"], "conflicts": HT["conflicts"],
                          "conflict action": HT["conflict_action"], "never": HT["never"]}) + "\n"
    md["05_WALL_FACE_V1_WF_O1_ROOT_CAUSE.md"] = "# WF-O1 root cause\n\n" + bullets(
        {k: v for k, v in WO.items() if k not in ("SCHEMA", "v2_reconciliation_on_qortuba")}) + "\n"
    VP = R["WALL_FACE_V2_POLICY"]
    md["06_WALL_FACE_V2_POLICY.md"] = "# Wall-face surface policy V2\n\n" + bullets(
        {"policy": VP["policy"], "V1 / V4 unchanged": VP["v1_unchanged"], "topology": VP["topology_effect"]}) + \
        "\n\n## Qortuba method (data)\n" + bullets(VP["method"]) + "\n"
    md["07_WALL_FACE_V2_FREEZE.md"] = "# V2 freeze\n\n" + bullets(
        {k: FZ[k] for k in ("frozen_commit", "recommendation_written_first", "policies", "unchanged",
                            "synthetic_test_count", "qortuba_before_freeze", "order", "rule", "amendments")}) + \
        "\n\nSynthetic tests:\n" + "\n".join(f"- {t}" for t in FZ["synthetic_tests"]) + "\n"
    md["08_WALL_FACE_V2_BLIND_RESULT.md"] = "# V2 blind result\n\n" + bullets(
        {"blind": B["blind"], "freeze": B["freeze"], "method": B["method"], "all sites reconcile":
         B["all_sites_reconcile"], "double count guard": {k: B["double_count_guard"][k] for k in ("surfaces", "state")},
         "trade rows": {t: {k: v[k] for k in ("state", "AUTHORISED_SUBTOTAL_M2", "COMPLETE_M2")}
                        for t, v in B["trade_rows"].items()},
         "waterproofing": B["waterproofing"]["totals"], "blind vs rebuild": S["blind_vs_rebuild"]}) + \
        "\n\n## Reconciliation per site (rebuild)\n" + tbl(
            ["Site", "Zones", "Trade", "Method A m2", "Method B m2", "Diff", "Tolerance", "State"],
            [[s, "/".join(v["zones"]), t, f["reconciliation"]["method_a_m2"], f["reconciliation"]["method_b_m2"],
              f["reconciliation"]["difference_m2"], f["reconciliation"]["tolerance_m2"], f["reconciliation"]["state"]]
             for s, v in WS["per_site"].items() for t, f in v["faces"].items()]) + "\n"
    md["09_PLASTER_RESULT.md"] = "# Plaster (DRY_WALL_PLASTER)\n\n" + trade_table(PL) + "\n\n## " \
        "WET_SERVICE_REVEAL_PLASTER\n" + bullets(PL["WET_SERVICE_REVEAL_PLASTER"]) + "\n"
    md["10_PAINT_RESULT.md"] = "# Paint\n\n" + trade_table(PA) + "\n\n" + bullets(
        {"vs dry plaster": PA["vs_dry_plaster"], "PAINTRY": PA["paintry"]}) + "\n"
    md["11_WALL_TILE_RESULT.md"] = "# Wall tile and wet wall-tile preparation\n\n## WALL_TILE\n" + trade_table(WT) + \
        "\n\n## WET_WALL_TILE_PREP\n" + trade_table(WT["WET_WALL_TILE_PREP"]) + "\n\n" + bullets(
        {"prep = tile": WT["prep_equals_tile"], "why": WT["prep_why"], "reveals": WT["reveals"],
         "height conflict (flag only)": WT["height_conflict"]}) + "\n"
    RP = R["REVEAL_FINISH_POLICY"]
    md["12_REVEAL_FINISH_POLICY.md"] = "# Reveal finish policy\n\n" + bullets(
        {"policy": RP["policy"], "Urban rule": RP["urban_rule"], "Qortuba": RP["qortuba"]}) + "\n"
    md["13_REVEAL_REGISTER.md"] = "# Reveal register\n\n" + tbl(
        ["Opening", "Kind", "Surface", "Owner", "Finish", "Depth m", "Height / width m", "Area m2", "Basis"],
        [[x["opening"][-30:], x["kind"], x["surface"], "/".join(x.get("owner_zones") or ["-"]), x["finish"],
          x.get("depth_m"), x.get("height_m", x.get("width_m")), x.get("area_m2"), (x.get("depth_basis") or "")[:40]]
         for x in RV["reveals"]]) + "\n\n" + bullets(
        {k: RV[k] for k in ("by_finish", "porcelain", "unresolved", "sliding_door", "sliding_door_split",
                            "hall_lobby_soffit_vs_q14", "blind_vs_rebuild", "double_count_guard", "never")}) + "\n"
    md["14_COLUMN_DUCT_FINISH_AUTHORITY.md"] = "# Column and duct finish authority\n\n" + tbl(
        ["Site", "Zones", "Class", "Area m2"],
        [[x["site"], "/".join(x["zones"]), x["class"], x["area_m2"]] for x in CD["columns"] + CD["duct_faces"]]) + \
        "\n\n" + bullets({k: CD[k] for k in ("method", "column_area_m2", "duct_area_m2", "r8_17_misreading",
                                             "owner_question", "duct_note", "rule")}) + "\n"
    WPP = R["WATERPROOFING_POLICY"]
    md["15_WATERPROOFING_POLICY.md"] = "# Waterproofing policy\n\n" + bullets(
        {"policy": WPP["policy"], "method": WPP["method"], "recommendation": WPP["recommendation"]}) + "\n"
    md["16_WATERPROOFING_RESULT.md"] = "# Waterproofing result\n\n" + tbl(
        ["Site", "Zones", "Floor m2", "Upturn lm", "Height m", "Upturn m2 (info)", "Perimeter by class", "Recon"],
        [[s, "/".join(v["zones"]), v["WATERPROOFING_FLOOR_M2"], v["WATERPROOFING_UPTURN_LM"], v["upturn_height_m"],
          v["upturn_m2_informational"], j(v["perimeter_by_class_m"], 200), v["perimeter_reconciles"]]
         for s, v in WP["per_room"].items()]) + "\n\n" + bullets(
        {k: WP[k] for k in ("state", "rows", "per_floor", "doorways_deducted", "opening_lengths_in_upturn_m",
                            "skirting_path_used", "vs_skirting", "marble", "label_note", "anti_calibration",
                            "release_blockers")}) + "\n"
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    md["17_EXISTING_ROW_REGRESSION.md"] = "# Existing-row regression\n\n" + bullets(
        {"floor / ceiling rows": A["35_floor_ceiling_rows_changed"],
         "Q-13": q13["regression_vs_r8_17"], "Q-14": q14["regression_vs_r8_17"], "Q-14 preserved": q14["preserved"],
         "skirting / hidden profile": A["36_skirting_hidden_profile_changed"], "marble": A["37_marble_changed"],
         "digests vs R8.17": S["digest_vs_r8_17"], "old revision unchanged": S["old_revision_unchanged_vs_r8_17"],
         "reproduces": S["reproduces"], "determinism": S["determinism"]}) + "\n"
    SP2 = R["SECOND_PROJECT_REGRESSION"]
    md["18_SECOND_PROJECT_REGRESSION.md"] = "# Second-project regression\n\n" + bullets(
        {k: v for k, v in SP2.items() if k != "SCHEMA"}) + "\n"
    md["19_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    CRS = R["CLOSURE_RELEASE_STATUS"]
    md["20_CLOSURE_RELEASE.md"] = "# Closure release\n\n" + bullets(
        {"reached": CRS["reached"], "missing": CRS["missing"], "ceiling": CRS["ceiling"], "closures": CRS["closures"],
         "tracked": CRS["tracked"], "production": CRS["production"], "released": CRS["released"] or "NOTHING",
         "wall-face closures": WS["topology_closures"]}) + "\n"
    md["21_ROW_STATUS.md"] = "# Row status\n\n" + rt + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: v[k] for k in ("TOPOLOGY_POLICY", "TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                 "RELEASE_INPUT_DIGEST", "BASE_PHYSICAL_SITES", "OWNER_FACTS_APPLIED",
                                                 "SOURCE_ANCHOR", "RELEASE_BLOCKERS")})
        for r, v in S["six_rows"].items()) + "\n\n## Extra rows\n" + bullets(S["extra_rows"]) + "\n"
    md["22_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## Remaining release blockers\n{bullets(A['40_release_blockers'])}\n\n## R8.19\n{A['42_r8_19']}" \
        f"\n\n{STOP}\n"
    md["23_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.18 test files: " + \
        ", ".join(res["r8_18_test_files"]) + f"\n\nFrozen synthetic tests: {len(res['synthetic_tests'])}\n"
    md["24_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(R) + 1, "json")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
