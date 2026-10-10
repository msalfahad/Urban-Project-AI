"""R8.17 review package: URBAN_QTO_R8_17_SKIRTING_V4_WALL_FACES (24 md + 23 json + 3 supporting + zip).

    python3 research/external_engine_lab/r8_17_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_17/registers); nothing is typed in.
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

REG = ROOT / "tests/r8_17/registers"
NAME = "URBAN_QTO_R8_17_SKIRTING_V4_WALL_FACES"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_PHYSICAL_FACT_REGISTER", "OWNER_METHOD_RULE_REGISTER",
         "HALL_PAINTRY_SLIDING_DOOR_REGISTER", "SKIRTING_V3_O1_REGISTER", "SKIRTING_V4_POLICY", "SKIRTING_REGISTER",
         "HIDDEN_PROFILE_REGISTER", "OPENING_REVEAL_REGISTER", "Q13_STATUS", "Q14_STATUS", "MARBLE_THRESHOLD_REGISTER",
         "WALL_FACE_ENGINE_DESIGN", "WALL_FACE_ENGINE_READINESS", "WALL_SURFACE_REGISTER", "SECOND_PROJECT_REGRESSION",
         "SOURCE_ANCHOR_STATUS", "CLOSURE_RELEASE_STATUS", "QORTUBA_R8_17_STATUS", "R8_17_DECISION_REGISTER")
COPIES = {"SKIRTING_V4_FREEZE": "R8_17_V4_FREEZE", "SKIRTING_V4_BLIND_RESULT": "SKIRTING_V4_BLIND_RESULT"}
SUPPORT = ("WALL_FACE_BLIND_RESULT", "R8_17_WALL_FACE_FREEZE", "DIGEST_HIERARCHY")
STOP = "STOP AFTER R8.17. NO PRODUCTION MIGRATION."


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
    rows = [[r, v["STATE"], f"{f4(v['VALUE'])} m2", f"{len(v['BASE_PHYSICAL_SITES'])} sites",
             "; ".join(v["TRADE_AUTHORITY"])[:70], f"{v['TOPOLOGY_DIGEST'][:10]} / {v['ROW_AUTHORITY_DIGEST'][:10]}",
             "NOT_ESTABLISHED", len(v["RELEASE_BLOCKERS"])] for r, v in six.items()]
    for k in ("SKIRTING", "HIDDEN_PROFILE"):
        v = ex[k]
        rows.append([k, v["state"], f"{v['value_lm']} lm", "V4 path, dry rooms", "QORTUBA-NEW-SKIRTING-METHOD@v3",
                     "-", "NOT_ESTABLISHED", len(v["release_blockers"])])
    m = ex["MARBLE_THRESHOLD"]
    rows.append(["MARBLE_THRESHOLD", m["state"], f"{m['MARBLE_THRESHOLD_PLAN_AREA_M2']} m2 / "
                 f"{m['MARBLE_THRESHOLD_LENGTH_LM']} lm", f"{m['count']} strips",
                 "URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1 + entrance fact", "-", "NOT_ESTABLISHED",
                 len(m["release_blockers"])])
    for k in ("WALL_TILE", "PLASTER", "PAINT"):
        v = ex[k]
        rows.append([k, v["state"], "NOT PUBLISHED", "wall-face engine V1", "QORTUBA-NEW-WALL-FACE-METHOD@v1", "-",
                     "NOT_ESTABLISHED", len(v["blockers"])])
    return tbl(["Row", "State", "Quantity", "Geometry", "Authority", "Topology / row digest", "Anchor", "Blockers"],
               rows)


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS + SUPPORT} | {k: jl(REG / f"{v}.json") for k, v in COPIES.items()}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_17_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_17_test_files": sorted(p.name for p in (ROOT / "tests/r8_17").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_17_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_17_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_17_STATUS"]
    A, G = D["answers"], D["gates"]
    SK, HP, SD, V1 = R["SKIRTING_REGISTER"], R["HIDDEN_PROFILE_REGISTER"], R["HALL_PAINTRY_SLIDING_DOOR_REGISTER"], \
        R["SKIRTING_V3_O1_REGISTER"]
    FZ, B = R["SKIRTING_V4_FREEZE"], R["SKIRTING_V4_BLIND_RESULT"]
    WS, WR, WD = R["WALL_SURFACE_REGISTER"], R["WALL_FACE_ENGINE_READINESS"], R["WALL_FACE_ENGINE_DESIGN"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    rt = row_table(S)
    trade_states = "; ".join(f"{t}: {v['state']}" for t, v in WR["trades"].items())
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.17 - sliding glass door, skirting path V4 (V3-O1 fixed), hidden profile, wall-face surface engine\n\n"
        f"**{O['headline']}**\n\n" + rt +
        f"\n\n- Sliding glass door: {A['3_removed_from_withheld']}.\n- V3-O1: {A['9_h518_payable']}.\n"
        f"- Skirting: blind {A['11_blind_v4_result']}; rebuilt {A['12_rebuilt_result']}.\n"
        f"- Hidden profile: {HP['HIDDEN_PROFILE_LM']} lm, its own row.\n"
        f"- Wall faces: {A['27_wall_face_engine_implemented']}; no trade row published "
        f"({trade_states}).\n"
        f"- New silent error: WF-O1 (frozen wall-face engine self-check), disclosed.\n\n" + tests + "\n\n" +
        bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"required now": O["required_now"] or "NONE", "needed for the wall-finish rows": O["needed_for_wall_finish_rows"],
         "answered this round": O["answered_this_round"], "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    md["03_HALL_PAINTRY_SLIDING_DOOR_OWNER_FACT.md"] = "# HALL / PAINTRY sliding glass door\n\n" + bullets(
        {k: v for k, v in SD.items() if k != "SCHEMA"}) + "\n\n## Fact\n" + bullets(
        R["OWNER_PHYSICAL_FACT_REGISTER"]["new_fact"]["statement"]) + "\n"
    md["04_SKIRTING_V3_O1_ROOT_CAUSE.md"] = "# V3-O1 root cause\n\n" + bullets(
        {k: v for k, v in V1.items() if k != "SCHEMA"}) + "\n"
    SP = R["SKIRTING_V4_POLICY"]
    md["05_SKIRTING_V4_POLICY.md"] = "# Skirting path policy V4\n\n" + bullets(
        {"policy": SP["policy"], "method": SP["method"], "opening class policy": SP["opening_class_policy"]}) + "\n"
    md["06_SKIRTING_V4_FREEZE.md"] = "# V4 freeze\n\n" + bullets(
        {k: FZ[k] for k in ("frozen_commit", "wall_contact_path_policy", "unchanged", "synthetic_test_count",
                            "qortuba_before_freeze", "order", "rule", "amendments")}) + "\n\nV4 tests:\n" + \
        "\n".join(f"- {t}" for t in FZ["synthetic_tests"]) + "\n"
    md["07_SKIRTING_V4_BLIND_RESULT.md"] = "# V4 blind result\n\n" + bullets(
        {"blind": B["blind"], "freeze": B["freeze"], "PAYABLE_LM": B["PAYABLE_LM"], "state": B["state"],
         "components": B["components_lm"], "excluded": B["excluded_lm"], "withheld": B["withheld"] or "NONE",
         "conservation (all sites)": B["conservation_all_sites"], "sliding door fact": B["sliding_door_fact"],
         "windows fact": B["windows_fact"]}) + "\n"
    md["08_SKIRTING_REBUILD.md"] = "# Skirting rebuild (per room)\n\n" + tbl(
        ["Site", "Zones", "State", "Payable lm", "Walls", "Columns", "Duct", "Under window", "Doorless jambs",
         "Doors", "Sliding door", "Closures", "Withheld"],
        [[s, "/".join(v["zones"]), v["state"], v["payable_lm"]] + [
            (v.get("components_lm") or {}).get(c, "") for c in ("REAL_WALL_FACE", "COLUMN_FACE",
                                                                 "AUTHORISED_OBSTACLE_FACE", "WINDOW_ABOVE_FLOOR",
                                                                 "PHYSICAL_OPENING_JAMB")] +
         [(v.get("excluded_lm") or {}).get(c, "") for c in ("DOOR_PRESENT", "SLIDING_GLAZED_DOOR_TO_FLOOR",
                                                           "TOPOLOGY_CLOSURE")] +
         ["; ".join(f"{w['class']} {w['length_lm']}" for w in v.get("withheld") or []) or "-"]
         for s, v in SK["per_room"].items()]) + "\n\n" + bullets(
        {"SKIRTING_LM": SK["SKIRTING_LM"], "reproduces blind": SK["reproduces_blind"], "breakdown": SK["breakdown_lm"],
         "excluded": SK["excluded_lm"], "withheld": SK["withheld"] or "NONE",
         "conservation (all sites)": SK["conservation_all_sites"],
         "reconciliation vs R8.16 (not a target)": SK["reconciliation_vs_r8_16"],
         "known defects open": SK["known_defects_open"] or "NONE", "release blockers": SK["release_blockers"]}) + "\n"
    md["09_HIDDEN_PROFILE.md"] = "# Hidden profile\n\n" + bullets({k: v for k, v in HP.items() if k != "SCHEMA"}) + "\n"
    RV = R["OPENING_REVEAL_REGISTER"]
    md["10_OPENING_REGRESSION.md"] = "# Opening regression\n\n" + bullets(
        {"doors": A["18_doors_zero_jamb"], "doorless": A["19_doorless_jambs_kept"], "Hall / Lobby":
         A["20_hall_lobby_regress"], "M.B.ROOM / DRESS": A["21_mb_dress_regress"], "I1471": A["22_i1471_regress"],
         "sliding door": A["5_its_jambs_carry_skirting"], "closures": A["35_closures_zero"]}) + \
        "\n\n## Opening reveal surfaces\n" + tbl(
            ["Opening", "Kind", "Surface", "Depth m", "Basis", "Height / width", "Area m2", "Trade"],
            [[x["opening"][-28:], x["kind"], x["surface"], x.get("depth_m"), x.get("depth_basis", "")[:30],
              x.get("height_m", x.get("width_m")), x.get("area_m2"), x["trade"][:40]] for x in RV["reveals"]]) + \
        "\n\n" + bullets({k: RV[k] for k in ("by_trade", "blocked", "skirting", "never", "double_count_guard")}) + "\n"
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    keys = ("STATE", "VALUE", "BASE_SITE_AREA_M2", "THRESHOLD_TREATMENT", "PASSAGE_TREATMENT", "SOFFIT_EXCLUSION_M2",
            "DUCT_TREATMENT", "OWNER_FACTS_APPLIED", "ROW_AUTHORITY_DIGEST", "RELEASE_BLOCKERS")
    md["11_Q14_REGRESSION.md"] = "# Q-14 regression\n\n" + bullets(
        {k: q14[k] for k in keys} | {"regression_vs_r8_16": q14["regression_vs_r8_16"], "preserved": q14["preserved"]}) \
        + "\n"
    md["12_FLOOR_MARBLE_REGRESSION.md"] = "# Floor and marble regression\n\n" + bullets(
        {"floor rows": A["25_floor_rows_changed"], "Q-13": {k: q13[k] for k in ("STATE", "VALUE", "regression_vs_r8_16")},
         "marble": R["MARBLE_THRESHOLD_REGISTER"]["regression_vs_r8_16"]}) + "\n"
    md["13_WALL_FACE_ENGINE_DESIGN.md"] = "# Wall-face engine design\n\n" + bullets(
        {"policy": WD["policy"], "layers": WD["layers"], "freeze": WD["freeze"]}) + "\n\n## Qortuba method (data)\n" + \
        bullets(WD["method"]) + "\n"
    md["14_WALL_FACE_ENGINE_RESULT_OR_READINESS.md"] = "# Wall-face engine: result / readiness\n\n" + tbl(
        ["Trade", "State", "Blockers"], [[t, v["state"], "; ".join(v["blockers"])] for t, v in WR["trades"].items()]) + \
        "\n\n## Per room\n" + tbl(
            ["Site", "Zones", "Class", "Trade", "State", "Height", "Wall m", "Column m", "Opening m", "Net m2",
             "Blockers"],
            [[s, "/".join(v["zones"]), v["class"], t, f["state"], f["height_m"],
              f["lengths_m"].get("WALL_FACE"), f["lengths_m"].get("COLUMN_FACE"), f["lengths_m"].get("OPENING_SPAN"),
              (f.get("areas_m2") or {}).get("WALL_FACE_NET"), "; ".join(f["blockers"])[:90]]
             for s, v in WS["per_site"].items() for t, f in v["faces"].items()]) + "\n\n" + bullets(
            {"WALL_TILE": {k: WS["WALL_TILE"][k] for k in ("state", "value_m2", "computed_rooms_m2",
                                                             "counterfactual_all_rooms_primary_form_m2", "reveals")},
             "WF-O1": WS["WF_O1"], "blind vs rebuild": WS["blind_vs_rebuild"],
             "dry counterfactual": WS["dry_counterfactual_note"], "next": WR["next"]}) + "\n"
    md["15_OPENING_SURFACE_RECONCILIATION.md"] = "# Opening and surface reconciliation\n\n" + tbl(
        ["Site", "Trade", "Opening", "Kind", "Width m", "Height m", "Authority", "Sill", "Deduction m2", "Lintel m2"],
        [[s, t, (o["opening"] or "")[-26:], o["kind"], o["width_m"], o["height_m"], (o["height_authority"] or "")[:40],
          o["sill_m"], o.get("deduction_m2"), o.get("lintel_m2")]
         for s, v in WS["per_site"].items() for t, f in v["faces"].items() for o in f["openings"]]) + "\n\n" + bullets(
        {"conservation": {s: {t: f["conservation"] for t, f in v["faces"].items()} for s, v in WS["per_site"].items()},
         "double count guard": WS["double_count_guard"], "topology closures": WS["topology_closures"]}) + "\n"
    md["16_WATERPROOFING_RECOMMENDATION.md"] = "# Waterproofing recommendation\n\n" + bullets(
        {"decision": A["36_waterproofing"], "rules": "US-04 / US-05 / US-14 / QP-13 (PAINTRY): floor membrane (m2) + "
                                                     "0.15 m upturn on the GROSS wet perimeter, doorways NOT deducted",
         "why separate": "a different path from skirting and wall face; it depends only on the wet-site boundary and "
                         "the doorway closures"}) + "\n"
    SP2 = R["SECOND_PROJECT_REGRESSION"]
    md["17_SECOND_PROJECT_REGRESSION.md"] = "# Second-project regression\n\n" + bullets(
        {k: v for k, v in SP2.items() if k != "SCHEMA"}) + "\n"
    md["18_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    CRS = R["CLOSURE_RELEASE_STATUS"]
    md["19_CLOSURE_RELEASE.md"] = "# Closure release\n\n" + bullets(
        {"reached": CRS["reached"], "missing": CRS["missing"], "ceiling": CRS["ceiling"], "closures": CRS["closures"],
         "tracked": CRS["tracked"], "production": CRS["production"], "released": CRS["released"] or "NOTHING"}) + "\n"
    DH = R["DIGEST_HIERARCHY"]
    md["20_ROW_STATUS.md"] = "# Row status\n\n" + rt + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: v[k] for k in ("TOPOLOGY_POLICY", "TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                 "RELEASE_INPUT_DIGEST", "BASE_PHYSICAL_SITES", "THRESHOLD_TREATMENT",
                                                 "PASSAGE_TREATMENT", "DUCT_TREATMENT", "OBJECT_FOOTPRINT_POLICY",
                                                 "OWNER_FACTS_APPLIED", "SOURCE_ANCHOR", "RELEASE_BLOCKERS")})
        for r, v in S["six_rows"].items()) + "\n\n## Extra rows\n" + bullets(S["extra_rows"]) + \
        "\n\n## Digests vs R8.16\n" + bullets({"per row": DH["vs_r8_16"], "reason": DH["reason"]}) + \
        "\n\nOld revision unchanged: " + j(S["old_revision_unchanged_vs_r8_16"]) + "\n\nDeterminism: " + \
        j(S["determinism"]) + "\n\nReproduces: " + j(S["reproduces"]) + "\n"
    md["21_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## Remaining release blockers\n{bullets(A['39_release_blockers'])}\n\n## R8.18\n{A['41_r8_18']}\n\n{STOP}\n"
    md["22_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.17 test files: " + \
        ", ".join(res["r8_17_test_files"]) + "\n"
    md["23_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + len(COPIES) + 1, "json +", len(SUPPORT), "supporting")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
