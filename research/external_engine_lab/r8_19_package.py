"""R8.19 review package: URBAN_QTO_R8_19_COLUMN_DUCT_FINISH_BOQ_RELEASE (25 md + 25 json + 2 supporting + zip).

    python3 research/external_engine_lab/r8_19_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_19/registers); nothing is typed in.
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

REG = ROOT / "tests/r8_19/registers"
NAME = "URBAN_QTO_R8_19_COLUMN_DUCT_FINISH_BOQ_RELEASE"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_METHOD_RULE_REGISTER", "COLUMN_FINISH_POLICY", "DUCT_FINISH_POLICY",
         "COLUMN_DUCT_FINISH_REGISTER", "PLASTER_REGISTER", "PAINT_REGISTER", "WALL_TILE_REGISTER",
         "WALL_TILE_PREP_REGISTER", "REVEAL_FINISH_REGISTER", "SLIDING_DOOR_REVEAL_PHYSICALITY",
         "WATERPROOFING_REGISTER", "SKIRTING_REGISTER", "HIDDEN_PROFILE_REGISTER", "Q13_STATUS", "Q14_STATUS",
         "MARBLE_THRESHOLD_REGISTER", "BOQ_REPORT_SCHEMA", "BOQ_REPORT_SHADOW", "CLOSURE_RELEASE_STATUS",
         "SOURCE_ANCHOR_STATUS", "SECOND_PROJECT_REGRESSION", "QORTUBA_R8_19_STATUS", "R8_19_DECISION_REGISTER")
SUPPORT = ("R8_19_FREEZE", "R8_19_BLIND_RESULT")
STOP = "STOP AFTER R8.19.\nNO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=900):
    return json.dumps(v, ensure_ascii=False)[:n]


def bullets(d):
    return "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 700)}" for k, v in d.items())


def row_table(S):
    six, ex = S["six_rows"], S["extra_rows"]
    rows = [[r, v["STATE"], f"{v['VALUE']:.4f} m2", "-", len(v["RELEASE_BLOCKERS"])] for r, v in six.items()]
    for k in ("DRY_WALL_PLASTER", "DRY_WALL_PAINT", "WET_SERVICE_WALL_TILE", "WET_WALL_TILE_PREP",
              "WET_SERVICE_REVEAL_PLASTER"):
        v = ex[k]
        rows.append([k, v["state"], f"{v['AUTHORISED_SUBTOTAL_M2']} m2", v["COMPLETE_M2"], len(v["release_blockers"])])
    for k in ("SKIRTING", "HIDDEN_PROFILE"):
        rows.append([k, ex[k]["state"], f"{ex[k]['value_lm']} lm", "-", len(ex[k]["release_blockers"])])
    m = ex["MARBLE_THRESHOLD"]
    rows.append(["MARBLE_THRESHOLD", m["state"], f"{m['MARBLE_THRESHOLD_PLAN_AREA_M2']} m2 / "
                 f"{m['MARBLE_THRESHOLD_LENGTH_LM']} lm", "-", len(m["release_blockers"])])
    for k, u in (("WATERPROOFING_FLOOR_M2", "value_m2"), ("WATERPROOFING_UPTURN_LM", "value_lm")):
        rows.append([k, ex[k]["state"], f"{ex[k][u]} {'m2' if u == 'value_m2' else 'lm'}", "-",
                     len(ex[k]["release_blockers"])])
    return tbl(["Row", "State", "Quantity", "COMPLETE", "Blockers"], rows)


def trade_table(r):
    return tbl(["Site", "Zones", "Height", "Wall plane m2", "Columns m2", "Duct m2", "Jamb reveals m2",
                "Head reveals m2", "Total m2", "Surfaces"],
               [[s, "/".join(v["zones"]), v["height_m"], v["wall_plane_m2"], v["column_face_m2"], v["obstacle_face_m2"],
                 v["jamb_reveals_m2"], v["head_reveals_m2"], v["total_m2"], v["surfaces"]]
                for s, v in r["per_room"].items()]) + "\n\n" + bullets(
        {k: r[k] for k in ("state", "AUTHORISED_SUBTOTAL_M2", "COMPLETE_M2", "FINAL", "reconciliation", "by_kind_m2",
                           "surfaces", "surface_ids_sha256", "unresolved_contributors", "release_blockers")})


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS + SUPPORT}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_19_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_19_test_files": sorted(p.name for p in (ROOT / "tests/r8_19").glob("test_*.py")),
           "synthetic_tests": R["R8_19_FREEZE"]["synthetic_tests"]}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_19_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_19_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_19_STATUS"]
    A, G = D["answers"], D["gates"]
    CD, PL, PA = R["COLUMN_DUCT_FINISH_REGISTER"], R["PLASTER_REGISTER"], R["PAINT_REGISTER"]
    WT, WP, SD = R["WALL_TILE_REGISTER"], R["WALL_TILE_PREP_REGISTER"], R["SLIDING_DOOR_REVEAL_PHYSICALITY"]
    BS, BQ, CR = R["BOQ_REPORT_SCHEMA"], R["BOQ_REPORT_SHADOW"], R["CLOSURE_RELEASE_STATUS"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    rt = row_table(S)
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.19 - column / duct finish authority, complete wall-finish rows, reveal physicality, BOQ report layer\n\n"
        f"**{O['headline']}**\n\n" + rt +
        f"\n\n- Columns: {A['2_dry_columns_plaster_paint']}; wet {A['4_wet_columns_wall_tile']}.\n"
        f"- Duct: {A['8_duct_plaster_paint']}.\n- Sliding-door south reveal: {A['22_south_reveal_established']} "
        "(wall-band OPENING_JAMB end; H480 fixture rejected).\n"
        "- Every wall-finish row COMPUTED_SHADOW_COMPLETE (not FINAL); skirting, hidden profile, waterproofing, floors, "
        "ceiling and marble unchanged.\n"
        f"- BOQ shadow report: {A['30_boq_layer']}; approved rows 0.\n"
        f"- New disclosed errors: WF3-L1 (blind double count of object faces), WF3-L2 (blind guard identity), "
        "amendment 1 (pre-output crash).\n\n" + tests + "\n\n" + bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"required now": O["required_now"] or "NONE", "optional for release only": O["optional_for_release_only"],
         "answered this round": O["answered_this_round"], "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    CF, DF = R["COLUMN_FINISH_POLICY"], R["DUCT_FINISH_POLICY"]
    md["03_COLUMN_FINISH_OWNER_RULE.md"] = "# Exposed column finish - owner rule\n\n" + bullets(
        {k: v for k, v in CF.items() if k != "SCHEMA"}) + "\n"
    md["04_DUCT_FINISH_OWNER_RULE.md"] = "# Exposed duct finish - owner rule\n\n" + bullets(
        {k: v for k, v in DF.items() if k != "SCHEMA"}) + "\n"
    md["05_COLUMN_PHYSICAL_EXPOSURE.md"] = "# Column physical exposure\n\n" + tbl(
        ["Column", "Segments", "Length m", "Exposed m", "Hidden m", "Sites", "State"],
        [[k.split("|")[1], v["segments"], v["length_m"], v["exposed_m"], v["hidden_m"], len(v["sites"]), v["state"]]
         for k, v in CD["columns"]["per_entity"].items()]) + "\n\n" + tbl(
        ["Segment", "Length m", "Exposed (site: m)", "Hidden m", "State"],
        [[k.split("|", 1)[1], v["length_m"], j(v["exposed_m"], 120), v["hidden_m"], v["state"]]
         for k, v in CD["columns"]["per_segment"].items()]) + "\n\n" + bullets(
        {"contribution m2": CD["columns"]["contribution_m2"], "hidden faces": CD["hidden_faces_excluded"],
         "skirting (no duplicate)": CD["skirting_no_duplicate"], "identity": CD["identity"]}) + "\n"
    md["06_DUCT_PHYSICAL_EXPOSURE.md"] = "# Duct physical exposure\n\n" + tbl(
        ["Segment", "Length m", "Exposed (site: m)", "Hidden m", "State"],
        [[k.split("|", 1)[1], v["length_m"], j(v["exposed_m"], 120), v["hidden_m"], v["state"]]
         for k, v in CD["duct"]["per_segment"].items()]) + "\n\n" + bullets(
        {"contribution m2": CD["duct"]["contribution_m2"], "owner physical authority":
         CD["duct"]["owner_physical_authority"], "after rebuild vs R8.18 diagnostic":
         CD["after_rebuild_vs_r8_18_diagnostic"]}) + "\n"
    md["07_PLASTER_REBUILD.md"] = "# Plaster rebuild\n\n## DRY_WALL_PLASTER\n" + trade_table(PL["DRY_WALL_PLASTER"]) + \
        "\n\n## WET_SERVICE_REVEAL_PLASTER\n" + trade_table(PL["WET_SERVICE_REVEAL_PLASTER"]) + "\n\n" + bullets(
        {k: PL[k] for k in ("PLASTER_ALL_SURFACES_M2", "plaster_all_note", "excluded", "after_rebuild_vs_r8_18")}) + "\n"
    md["08_PAINT_REBUILD.md"] = "# Paint rebuild\n\n" + trade_table(PA["DRY_WALL_PAINT"]) + "\n\n" + bullets(
        {"vs dry plaster": {k: v for k, v in PA["vs_dry_plaster"].items() if k not in ("only_plaster", "only_paint")},
         "PAINTRY": PA["paintry"]}) + "\n"
    md["09_WALL_TILE_REBUILD.md"] = "# Wall tile rebuild\n\n" + trade_table(WT["WET_SERVICE_WALL_TILE"]) + "\n\n" + \
        bullets({k: WT[k] for k in ("column_contribution_m2", "porcelain_reveals", "excluded", "height_conflict")}) + "\n"
    md["10_TILE_PREP_REBUILD.md"] = "# Wet wall-tile preparation\n\n" + trade_table(WP["WET_WALL_TILE_PREP"]) + "\n\n" + \
        bullets({k: WP[k] for k in ("same_physical_surfaces_as_wall_tile", "why_separate")}) + "\n"
    md["11_SLIDING_DOOR_REVEAL_PHYSICALITY.md"] = "# Sliding-door reveal physicality\n\n" + bullets(
        {k: SD[k] for k in ("opening", "ownership_and_depth", "outcome", "finish", "history", "cannot_recur")}) + \
        "\n\n## Jambs\n" + "\n".join(f"- {j(x, 900)}" for x in SD["jambs"]) + "\n\n## Bands used\n" + bullets(
        SD["bands_used"]) + "\n\n## Source parts\n" + tbl(
        ["Part", "Layer", "Role", "Geometry"], [[k.split("|")[1], v["layer"], v["role"], v["geometry"]]
                                                for k, v in SD["source_parts"].items()]) + "\n"
    RV = R["REVEAL_FINISH_REGISTER"]
    md["12_REVEAL_REGISTER.md"] = "# Reveal register\n\n" + tbl(
        ["Opening", "Kind", "Surface", "Owner", "Physicality", "Finish", "Depth m", "Area m2", "Included"],
        [[x["opening"][-30:], x["kind"], x["surface"], "/".join(x.get("owner_zones") or ["-"]),
          x["physicality"]["state"], x["finish"], x.get("depth_m"), x.get("area_m2"), x["included"]]
         for x in RV["reveals"]]) + "\n\n" + bullets(
        {k: RV[k] for k in ("order", "by_finish", "by_physicality", "unresolved", "two_finish_owners",
                            "fixture_evidence")}) + "\n"
    md["13_WATERPROOFING_REGRESSION.md"] = "# Waterproofing regression\n\n" + bullets(
        {k: R["WATERPROOFING_REGISTER"][k] for k in ("state", "rows", "regression_vs_r8_18", "doorways_deducted",
                                                     "skirting_path_used")}) + "\n"
    md["14_SKIRTING_PROFILE_REGRESSION.md"] = "# Skirting and hidden profile regression\n\n" + bullets(
        {"SKIRTING": R["SKIRTING_REGISTER"]["regression_vs_r8_18"], "HIDDEN_PROFILE":
         R["HIDDEN_PROFILE_REGISTER"]["regression_vs_r8_18"], "column / duct no duplicate":
         R["SKIRTING_REGISTER"]["column_duct_no_duplicate"]}) + "\n"
    md["15_FLOOR_CEILING_MARBLE_REGRESSION.md"] = "# Floor, ceiling and marble regression\n\n" + bullets(
        {"rows": S["vs_r8_18"], "digests": S["digest_vs_r8_18"], "Q-13": R["Q13_STATUS"]["regression_vs_r8_18"],
         "Q-14": R["Q14_STATUS"]["regression_vs_r8_18"],
         "marble": R["MARBLE_THRESHOLD_REGISTER"]["regression_vs_r8_18"],
         "old revision unchanged": S["old_revision_unchanged_vs_r8_18"], "determinism": S["determinism"]}) + "\n"
    md["16_BOQ_REPORT_DESIGN.md"] = "# BOQ report layer - design\n\n" + bullets(
        {k: BS[k] for k in ("policy", "columns", "statuses", "trace", "trade_registry", "pricing", "calculates")}) + \
        "\n\n## Items\n" + tbl(["Row", "Item code", "Trade", "Arabic", "English"],
                               [[k, v["item_code"], v["trade"], v["description_ar"], v["description_en"]]
                                for k, v in BS["items"].items()]) + "\n"
    md["17_BOQ_REPORT_SHADOW.md"] = f"# BOQ report - SHADOW\n\n**{BQ['banner']}**\n\n" + tbl(
        ["Item", "Trade", "Description (AR)", "Description (EN)", "Room / zone", "Qty", "Unit", "Status", "Approved"],
        [[r["ITEM_CODE"], r["TRADE"], r["DESCRIPTION_AR"], r["DESCRIPTION_EN"], j(r["ROOM_ZONE"], 40), r["QTY"],
          r["UNIT"], r["STATUS"], r["approved_for_boq"]] for r in BQ["report"]["rows"]]) + "\n\n" + bullets(
        {"validation": BQ["validation"], "status counts": BQ["status_counts"], "approved for BOQ": BQ["approved_for_boq"],
         "run": BQ["report"]["run"], "digest": BQ["report"]["digest"]}) + "\n"
    md["18_CLOSURE_RELEASE_REVIEW.md"] = "# Closure release review\n\n" + "\n\n".join(
        f"## {k}\n" + bullets(v) for k, v in CR["review_packets"].items()) + "\n\n" + bullets(
        {k: CR[k] for k in ("reached", "missing", "ceiling", "self_approved", "released", "production", "note")}) + "\n"
    md["19_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    md["20_SECOND_PROJECT_VALIDATION.md"] = "# Second-project validation\n\n" + bullets(
        {k: v for k, v in R["SECOND_PROJECT_REGRESSION"].items() if k != "SCHEMA"}) + "\n"
    md["21_ROW_STATUS.md"] = "# Row status\n\n" + rt + "\n\n" + bullets(
        {"blind vs rebuild": S["blind_vs_rebuild"], "plane check vs R8.18 METHOD B": S["plane_check_vs_r8_18_method_b"]
         ["all_agree"], "reproduces": S["reproduces"], "final": S["final"]}) + "\n"
    md["22_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## Remaining release blockers\n{bullets(A['39_release_blockers'])}\n\n## R8.20\n{A['41_r8_20']}" \
        f"\n\n{STOP}\n"
    md["23_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.19 test files: " + \
        ", ".join(res["r8_19_test_files"]) + f"\n\nFrozen synthetic tests: {len(res['synthetic_tests'])}\n"
    md["24_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + 1, "json +", len(SUPPORT), "supporting")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
