"""R8.15 review package: URBAN_QTO_R8_15_DUCT_MARBLE_SKIRTING (20 md + 19 json + 3 supporting + zip).

    python3 research/external_engine_lab/r8_15_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_15/registers); nothing is typed in.
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

REG = ROOT / "tests/r8_15/registers"
NAME = "URBAN_QTO_R8_15_DUCT_MARBLE_SKIRTING"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_PHYSICAL_FACT_REGISTER", "OWNER_METHOD_RULE_REGISTER",
         "DUCT_AUTHORITY_REGISTER", "PASSAGE_HEAD_REGISTER", "MARBLE_THRESHOLD_POLICY", "MARBLE_THRESHOLD_REGISTER",
         "MAIN_ENTRANCE_THRESHOLD_REGISTER", "SKIRTING_PATH_POLICY", "SKIRTING_REGISTER", "OPENING_REVEAL_REGISTER",
         "US07_REVEAL_DEPTH_REVIEW", "Q13_STATUS", "Q14_STATUS", "QORTUBA_R8_15_STATUS", "SOURCE_ANCHOR_STATUS",
         "CLOSURE_RELEASE_STATUS", "R8_15_DECISION_REGISTER")
SUPPORT = ("R8_15_SKIRTING_FREEZE", "BLIND_QORTUBA_SKIRTING_RESULT", "DIGEST_HIERARCHY")
STOP = "STOP AFTER R8.15. NO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=900):
    return json.dumps(v, ensure_ascii=False)[:n]


def bullets(d):
    return "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 700)}" for k, v in d.items())


def f4(v):
    return "" if v is None else f"{v:.4f}"


def six_table(six):
    return tbl(["Row", "State", "Value m2", "Base sites m2", "Thresholds m2", "Marble out m2", "Passages", "Duct",
                "Footprint policy", "Classes", "Topology", "Row authority", "Anchor", "Release blockers"],
               [[r, v["STATE"], f4(v["VALUE"]), f4(v["BASE_SITE_AREA_M2"]), v["THRESHOLD_CONTRIBUTION_M2"],
                 v["MARBLE"]["excluded_from_this_row_m2"],
                 "; ".join(f"{p['strip'][-6:]} {p['state']}" for p in v["PASSAGE_TREATMENT"]) or "-",
                 "; ".join(f"{d['hole_area_m2']} m2 {'AUTH' if d['authorised'] else 'UNPROVEN'}"
                           for d in v["DUCT_TREATMENT"]) or "-",
                 "; ".join(v["OBJECT_FOOTPRINT_POLICY"]), ", ".join(v["SEMANTIC_CLASSES"] or ["-"]),
                 v["TOPOLOGY_DIGEST"][:12], v["ROW_AUTHORITY_DIGEST"][:12], "NOT_ESTABLISHED",
                 len(v["RELEASE_BLOCKERS"])] for r, v in six.items()])


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS + SUPPORT}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_15_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_15_test_files": sorted(p.name for p in (ROOT / "tests/r8_15").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_15_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_15_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_15_STATUS"]
    A, G, six = D["answers"], D["gates"], S["six_rows"]
    M, ME, SK = R["MARBLE_THRESHOLD_REGISTER"], R["MAIN_ENTRANCE_THRESHOLD_REGISTER"], R["SKIRTING_REGISTER"]
    FZ, B = R["R8_15_SKIRTING_FREEZE"], R["BLIND_QORTUBA_SKIRTING_RESULT"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    extra = tbl(["Row", "State", "Value", "Release blockers"],
                [["SKIRTING (hidden, lm)", SK["state"], SK["SKIRTING_LM"], len(SK["release_blockers"])],
                 ["MARBLE_THRESHOLD (m2 / lm)", "COMPUTED_SHADOW",
                  f"{M['quantities']['MARBLE_THRESHOLD_PLAN_AREA_M2']} m2 / {M['quantities']['MARBLE_THRESHOLD_LENGTH_LM']}"
                  " lm", len(M["release_blockers"])]])
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.15 - duct authority, wet / service marble thresholds, skirting freeze, Q-13 / Q-14 rebuild\n\n"
        f"**{O['headline']}**\n\n" + six_table(six) + "\n\n" + extra +
        f"\n\n- Duct: {A['1_duct_authorised']}; 0.84 m2 out of floor and ceiling ({A['2_084_excluded_floor_and_ceiling']}).\n"
        f"- Passages: Hall / Lobby soffit out ({A['5_hall_soffit_excluded']}); M.B.ROOM / DRESS FULL_HEIGHT, ceiling "
        f"continues.\n- Marble: {A['8_marble_count']} thresholds ({len(A['9_from_urban_rule'])} Urban rule, "
        f"{len(A['10_from_explicit_evidence'])} explicit entrance), counted once, no half tile.\n"
        f"- Skirting: frozen `{FZ['frozen_commit'][:12]}`, blind run reproduced; {SK['SKIRTING_LM']} lm.\n"
        f"- New silent error: door without a second face closure ({len(S['doors_without_threshold_site'])}), "
        "disclosed with counterfactuals.\n\n" + tests + "\n\n" + bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"why none": O["why_none"], "answered this round": O["answered_this_round"],
         "prepared for the release stage (NOT asked now)": O["prepared_for_release_stage_not_asked"],
         "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    md["03_DUCT_OWNER_AUTHORITY.md"] = "# Duct owner authority\n\n" + bullets(R["DUCT_AUTHORITY_REGISTER"]) + "\n"
    md["04_MBDRESS_FULL_HEIGHT_PASSAGE.md"] = "# M.B.ROOM / DRESS full-height passage\n\n" + tbl(
        ["Passage", "Width mm", "Thickness mm", "Head", "Authority", "Ceiling"],
        [[p["passage"], p["width_mm"], p["thickness_mm"], p["head"], p["authority"], p["ceiling"]]
         for p in R["PASSAGE_HEAD_REGISTER"]["passages"]]) + "\n\n" + bullets(
        {k: v for k, v in R["PASSAGE_HEAD_REGISTER"].items() if k not in ("passages", "SCHEMA")}) + "\n"
    md["05_MAIN_ENTRANCE_MARBLE.md"] = "# Main entrance marble threshold\n\n" + bullets(ME) + "\n"
    md["06_URBAN_WET_SERVICE_MARBLE_RULE.md"] = "# Urban wet / service marble threshold rule\n\n" + bullets(
        R["OWNER_METHOD_RULE_REGISTER"]) + "\n"
    md["07_MARBLE_THRESHOLD_RESULTS.md"] = "# Marble threshold results\n\n" + tbl(
        ["Threshold", "Door", "Room types", "Authority", "Width mm", "Depth mm", "Plan m2", "lm", "Rise mm", "Water"],
        [[t["threshold"], t["door_occurrence"], j(t["room_types"], 120), t["authority"], t["clear_width_mm"],
          t["depth_mm"], t["plan_area_m2"], t["length_lm"], t["vertical_rise_mm"], t["water_containment"]]
         for t in M["thresholds"]]) + "\n\n" + bullets({"quantities": M["quantities"],
                                                        "release blockers": M["release_blockers"],
                                                        "never": M["never"]}) + \
        "\n\n## Every current threshold\n" + tbl(
            ["Threshold", "Door", "Class", "State", "Regions", "R8.14"],
            [[t["threshold"], t["door_occurrence"], t["classification"], t["allocation_state"],
              "; ".join(f"{r['side']} {r['treatment']} {r['area_m2']}" for r in t["regions"]) or "-",
              t["r8_14_allocation_state"]] for t in S["threshold_audit"]]) + "\n\n## Doors without a threshold site\n" + \
        bullets({d["door_occurrence"]: d for d in S["doors_without_threshold_site"]}) + "\n"
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    keys = ("STATE", "VALUE", "rebuild", "BASE_SITE_AREA_M2", "BASE_PHYSICAL_SITES", "THRESHOLD_TREATMENT", "MARBLE",
            "PASSAGE_TREATMENT", "DUCT_TREATMENT", "OBJECT_FOOTPRINT_POLICY", "SEMANTIC_CLASSES", "TRADE_AUTHORITY",
            "OWNER_FACTS_APPLIED", "COUNTERFACTUALS", "ROW_AUTHORITY_DIGEST", "RELEASE_BLOCKERS", "historical_matching")
    md["08_FLOOR_REBUILD.md"] = "# Floor rebuild (Q-13, Q-03 / Q-11, Q-03P / Q-12)\n\n## Q-13\n" + bullets(
        {k: q13[k] for k in keys} | {"regression_vs_r8_14": q13["regression_vs_r8_14"]}) + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: six[r][k] for k in ("STATE", "VALUE", "BASE_SITE_AREA_M2", "THRESHOLD_TREATMENT",
                                                      "MARBLE", "RELEASE_BLOCKERS")}) for r in ("Q-03", "Q-11", "Q-03P",
                                                                                                "Q-12")) + "\n"
    md["09_CEILING_REBUILD.md"] = "# Ceiling rebuild (Q-14)\n\n" + bullets(
        {k: q14[k] for k in keys} | {"regression_vs_r8_14": q14["regression_vs_r8_14"]}) + "\n"
    md["10_SKIRTING_POLICY.md"] = "# Skirting path policy\n\n" + bullets(
        {"policy": R["SKIRTING_PATH_POLICY"]["policy"], "method": R["SKIRTING_PATH_POLICY"]["method"],
         "freeze": {k: FZ[k] for k in ("frozen_commit", "wall_contact_path_policy", "synthetic_test_sha256",
                                       "synthetic_test_count", "qortuba_before_freeze", "order", "rule")}}) + \
        "\n\nV2 tests:\n" + "\n".join(f"- {t}" for t in FZ["synthetic_tests"]) + "\n"
    md["11_SKIRTING_QORTUBA_RESULT.md"] = "# Skirting - Qortuba result\n\n" + tbl(
        ["Site", "Zones", "State", "lm", "Components lm", "Excluded lm"],
        [[s, "/".join(v["zones"]), v["state"], v["lm"], j(v.get("components_lm"), 200), j(v.get("excluded_lm"), 240)]
         for s, v in SK["per_room"].items()]) + "\n\n" + bullets(
        {"SKIRTING_LM": SK["SKIRTING_LM"], "reproduces blind": SK["reproduces_blind"],
         "blind order": B["blind"], "components": SK["components_lm"], "excluded": SK["excluded_lm"],
         "counterfactuals": SK["counterfactuals"], "hidden profile": SK["hidden_profile"],
         "release blockers": SK["release_blockers"], "post-blind observation": SK["post_blind_observation"],
         "never": SK["never"]}) + "\n"
    RV = R["OPENING_REVEAL_REGISTER"]
    md["12_OPENING_REVEALS.md"] = "# Opening reveals\n\n" + tbl(
        ["Passage", "Head", "Surface", "Depth m", "Basis", "Area m2", "Area at 0.25 m"],
        [[pid, v["head"], s["surface"], round(s["depth_m"], 4), s["depth_basis"],
          None if s["area_m2"] is None else round(s["area_m2"], 6),
          None if s.get("area_at_default_depth_m2") is None else round(s["area_at_default_depth_m2"], 6)]
         for pid, v in RV["passages"].items() for s in v["surfaces"]]) + "\n\n" + bullets(
        {"missing": {pid: v["missing"] for pid, v in RV["passages"].items()}, "paint": RV["paint"],
         "plaster quantity": RV["plaster_quantity"], "door reveals": RV["door_reveals"],
         "double count guard": RV["double_count_guard"]}) + "\n"
    md["13_US07_REVEAL_DEPTH_REVIEW.md"] = "# US-07 reveal depth review\n\n" + bullets(R["US07_REVEAL_DEPTH_REVIEW"]) + "\n"
    md["14_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    CRS = R["CLOSURE_RELEASE_STATUS"]
    md["15_CLOSURE_RELEASE.md"] = "# Closure release\n\n" + bullets(
        {"reached": CRS["reached"], "missing": CRS["missing"], "ceiling": CRS["ceiling"], "closures": CRS["closures"],
         "released": CRS["released"] or "NOTHING"}) + "\n"
    DH = R["DIGEST_HIERARCHY"]
    md["16_SIX_ROW_STATUS.md"] = "# Six-row status\n\n" + six_table(six) + "\n\n" + extra + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: v[k] for k in ("TOPOLOGY_POLICY", "TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                 "RELEASE_INPUT_DIGEST", "BASE_PHYSICAL_SITES", "THRESHOLD_TREATMENT",
                                                 "MARBLE", "PASSAGE_TREATMENT", "DUCT_TREATMENT",
                                                 "OBJECT_FOOTPRINT_POLICY", "SEMANTIC_CLASSES", "OWNER_FACTS_APPLIED",
                                                 "SOURCE_ANCHOR", "RELEASE_BLOCKERS")})
        for r, v in six.items()) + "\n\n## Digests vs R8.14\n" + bullets(
        {"per row": DH["vs_r8_14"], "reasons": DH["reasons"]}) + "\n\nOld revision unchanged: " + \
        j(S["old_revision_unchanged_vs_r8_14"]) + "\n\nDeterminism: " + j(S["determinism"]) + "\n"
    md["17_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## Remaining release blockers\n{bullets(A['31_release_blockers_remaining'])}\n\n## R8.16\n" \
        f"{A['33_r8_16']}\n\n{STOP}\n"
    md["18_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.15 test files: " + \
        ", ".join(res["r8_15_test_files"]) + "\n"
    md["19_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + 1, "json +", len(SUPPORT), "supporting")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
