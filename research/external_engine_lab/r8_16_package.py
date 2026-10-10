"""R8.16 review package: URBAN_QTO_R8_16_OPENINGS_SKIRTING_CLOSURE (24 md + 22 json + 2 supporting + zip).

    python3 research/external_engine_lab/r8_16_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_16/registers); nothing is typed in.
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

REG = ROOT / "tests/r8_16/registers"
NAME = "URBAN_QTO_R8_16_OPENINGS_SKIRTING_CLOSURE"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_METHOD_RULE_REGISTER", "WINDOW_FLOOR_CONTACT_REGISTER", "DOOR_SKIRTING_POLICY",
         "DOORLESS_JAMB_REGISTER", "I1471_SOURCE_AUDIT", "OFFSET_CLOSURE_POLICY", "CLOSURE_BLIND_RESULT",
         "SKIRTING_V3_POLICY", "SKIRTING_BLIND_RESULT", "SKIRTING_REGISTER", "HIDDEN_PROFILE_REGISTER", "Q13_STATUS",
         "Q14_STATUS", "MARBLE_THRESHOLD_REGISTER", "OPENING_REVEAL_REGISTER", "WALL_FACE_ENGINE_READINESS",
         "SOURCE_ANCHOR_STATUS", "CLOSURE_RELEASE_STATUS", "QORTUBA_R8_16_STATUS", "R8_16_DECISION_REGISTER")
SUPPORT = ("R8_16_FREEZE", "DIGEST_HIERARCHY")
STOP = "STOP AFTER R8.16. NO PRODUCTION MIGRATION."


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
    rows = [[r, v["STATE"], f"{f4(v['VALUE'])} m2", f"{len(v['BASE_PHYSICAL_SITES'])} sites, "
             f"{f4(v['BASE_SITE_AREA_M2'])} m2", "; ".join(v["TRADE_AUTHORITY"])[:80],
             f"thr {v['THRESHOLD_CONTRIBUTION_M2']}; soffit {v['SOFFIT_EXCLUSION_M2']}; marble out "
             f"{v['MARBLE']['excluded_from_this_row_m2']}", f"{v['TOPOLOGY_DIGEST'][:10]} / "
             f"{v['ROW_AUTHORITY_DIGEST'][:10]} / {v['RELEASE_INPUT_DIGEST'][:10]}", "NOT_ESTABLISHED",
             len(v["RELEASE_BLOCKERS"])] for r, v in six.items()]
    for k, unit in (("SKIRTING", "lm"), ("HIDDEN_PROFILE", "lm")):
        v = ex[k]
        rows.append([k, v["state"], f"{v['value_lm']} {unit}", "V3 path, dry rooms", "QORTUBA-NEW-SKIRTING-METHOD@v2",
                     "windows continuous; doors 0; doorless jambs; glazed screen withheld", "-", "NOT_ESTABLISHED",
                     len(v["release_blockers"])])
    m = ex["MARBLE_THRESHOLD"]
    rows.append(["MARBLE_THRESHOLD", m["state"], f"{m['MARBLE_THRESHOLD_PLAN_AREA_M2']} m2 / "
                 f"{m['MARBLE_THRESHOLD_LENGTH_LM']} lm", f"{m['count']} door strips",
                 "URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1 + entrance fact", "whole strip, own row", "-",
                 "NOT_ESTABLISHED", len(m["release_blockers"])])
    return tbl(["Row", "State", "Quantity", "Geometry", "Authority", "Treatments", "Topology / row / release digest",
                "Anchor", "Blockers"], rows)


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS + SUPPORT}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_16_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_16_test_files": sorted(p.name for p in (ROOT / "tests/r8_16").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_16_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_16_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_16_STATUS"]
    A, G = D["answers"], D["gates"]
    SK, HP, W = R["SKIRTING_REGISTER"], R["HIDDEN_PROFILE_REGISTER"], R["WINDOW_FLOOR_CONTACT_REGISTER"]
    DJ, DL, AU = R["DOOR_SKIRTING_POLICY"], R["DOORLESS_JAMB_REGISTER"], R["I1471_SOURCE_AUDIT"]
    FZ, CB, OC = R["R8_16_FREEZE"], R["CLOSURE_BLIND_RESULT"], R["OFFSET_CLOSURE_POLICY"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    rt = row_table(S)
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.16 - floor-contact skirting, door / doorless jambs, I1471 offset-jamb closure, Q-14 rebuild\n\n"
        f"**{O['headline']}**\n\n" + rt +
        f"\n\n- I1471: {A['16_i1471_complete_site']}.\n- Q-14: {A['17_q14_removed_the_reveal']}.\n"
        f"- Skirting: {SK['SKIRTING_LM']} lm ({SK['state']}); breakdown {j(SK['breakdown_lm'])}; withheld "
        f"{SK['withheld_lm']} lm.\n- Hidden profile: {HP['HIDDEN_PROFILE_LM']} lm, its own row.\n"
        f"- Marble: {A['27_marble_regression']}.\n- New silent error: V3-O1 (counterfactual "
        f"{SK['counterfactuals']['with_v3_o1_fixed_lm']} lm).\n\n" + tests + "\n\n" + bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"required now": O["required_now"] or "NONE", "optional for release": O["optional_for_release"],
         "answered this round": O["answered_this_round"], "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    MR = R["OWNER_METHOD_RULE_REGISTER"]
    md["03_OWNER_SKIRTING_OPENING_RULE.md"] = "# Owner skirting / opening rule\n\n" + bullets(
        {"Urban rules": MR["urban_rules"], "Qortuba facts": MR["qortuba_facts"], "fact policy": MR["fact_policy"],
         "QP-09": MR["qp09"], "transfer forbidden": MR["transfer_forbidden"]}) + "\n"
    md["04_WINDOW_FLOOR_CONTACT.md"] = "# Window floor contact\n\n" + tbl(
        ["Site", "Zones", "Sources", "Length mm", "Hosted on wall line", "Floor contact", "Authority", "Span"],
        [[w["site"], "/".join(w["zones"]), ", ".join(w["sources"])[:60], w["length_mm"], w["hosted_on_wall_face_line"],
          w["floor_contact"]["state"], w["floor_contact"].get("authority"), w["span"]] for w in W["windows"]]) + \
        "\n\n" + bullets({k: W[k] for k in ("fact_binding", "source_exhaustion", "continuity_lm", "withheld_lm",
                                            "never")}) + "\n"
    md["05_DOOR_SKIRTING_METHOD.md"] = "# Door skirting method\n\n" + bullets(
        {k: v for k, v in DJ.items() if k not in ("SCHEMA", "door_jambs")}) + "\n\n" + tbl(
        ["Door", "Jamb depth lm", "Skirting lm", "Plaster surface"],
        [[x["opening"], x["length_lm"], x["skirting_lm"], x["plaster_surface"]] for x in DJ["door_jambs"]]) + "\n"
    md["06_DOORLESS_JAMB_METHOD.md"] = "# Doorless-opening jamb method\n\n" + tbl(
        ["Site", "Passage", "Side", "Record", "Source", "End kind", "Length lm", "Counted lm"],
        [[x["site"], x["opening"], x["side"], x["record"], x["source"], x["end_kind"], x["length_lm"], x["counted_lm"]]
         for x in DL["jambs"]]) + "\n\n" + bullets(
        {k: DL[k] for k in ("rule", "counted_lm", "across_opening_lm", "topology_closure_lm", "hall_far_jamb",
                            "v3_o1")}) + "\n"
    md["07_I1471_SOURCE_AUDIT.md"] = "# I1471 source audit\n\n" + bullets({k: v for k, v in AU.items()
                                                                           if k != "SCHEMA"}) + "\n"
    md["08_OFFSET_CLOSURE_POLICY.md"] = "# Offset-jamb closure policy (DOOR_OPENING_CLOSURE_POLICY_V2)\n\n" + bullets(
        {"policy": OC["policy"], "freeze": OC["freeze"], "in run manifest": OC["in_run_manifest"]}) + \
        "\n\nSynthetic tests (frozen):\n" + "\n".join(f"- {t}" for t in FZ["synthetic_tests"]) + "\n"
    nk = CB["NEW_K2"]
    md["09_CLOSURE_BLIND_RESULT.md"] = "# Closure blind result\n\n" + bullets(
        {"blind": CB["blind"], "freeze": CB["freeze"], "closure B rules": nk["closure_b_rules"],
         "closure B missing": nk["closure_b_missing"] or "NONE", "old revision": CB["OLD_K1"]["closure_b_rules"],
         "lab reproduces": OC["reproduced_by_the_lab"]}) + "\n\n" + tbl(
        ["Door", "Rule", "Width mm", "Caps", "Blocked"],
        [[k, v["rule"], v["width_mm"], ", ".join(v["caps"]), v["blocked"]] for k, v in nk["openings"].items()]) + \
        "\n\n" + tbl(["Threshold", "Door", "Site", "m2"], [[t["threshold"], t["opening"], t["site"], t["area_m2"]]
                                                           for t in nk["thresholds"]]) + "\n"
    SP = R["SKIRTING_V3_POLICY"]
    md["10_SKIRTING_V3_POLICY.md"] = "# Skirting path policy V3\n\n" + bullets(
        {"policy": SP["policy"], "method": SP["method"], "freeze": SP["freeze"]}) + "\n"
    SB = R["SKIRTING_BLIND_RESULT"]
    md["11_SKIRTING_BLIND_RESULT.md"] = "# Skirting blind result\n\n" + bullets(
        {"blind": SB["blind"], "freeze": SB["freeze"], "PAYABLE_LM": SB["PAYABLE_LM"], "state": SB["state"],
         "components": SB["components_lm"], "excluded": SB["excluded_lm"], "withheld": SB["withheld"],
         "lab reproduces": SK["reproduces_blind"]}) + "\n"
    md["12_QORTUBA_SKIRTING_REBUILD.md"] = "# Qortuba skirting rebuild (per room)\n\n" + tbl(
        ["Site", "Zones", "State", "Payable lm", "Walls", "Columns", "Duct", "Under window", "Doorless jambs",
         "Doors excluded", "Withheld"],
        [[s, "/".join(v["zones"]), v["state"], v["payable_lm"]] + [
            (v.get("components_lm") or {}).get(c, "") for c in ("REAL_WALL_FACE", "COLUMN_FACE",
                                                                 "AUTHORISED_OBSTACLE_FACE", "WINDOW_ABOVE_FLOOR",
                                                                 "PHYSICAL_OPENING_JAMB")] +
         [(v.get("excluded_lm") or {}).get("DOOR_PRESENT", ""),
          "; ".join(f"{w['class']} {w['length_lm']}" for w in v.get("withheld") or []) or "-"]
         for s, v in SK["per_room"].items()]) + "\n\n" + bullets(
        {"SKIRTING_LM": SK["SKIRTING_LM"], "breakdown": SK["breakdown_lm"], "excluded": SK["excluded_lm"],
         "withheld": SK["withheld"], "counterfactuals": SK["counterfactuals"],
         "reconciliation vs R8.15 (not a target)": SK["reconciliation_vs_r8_15"],
         "release blockers": SK["release_blockers"], "never": SK["never"]}) + "\n"
    md["13_HIDDEN_PROFILE.md"] = "# Hidden profile\n\n" + bullets({k: v for k, v in HP.items() if k != "SCHEMA"}) + "\n"
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    keys = ("STATE", "VALUE", "rebuild", "BASE_SITE_AREA_M2", "BASE_PHYSICAL_SITES", "THRESHOLD_TREATMENT", "MARBLE",
            "PASSAGE_TREATMENT", "SOFFIT_EXCLUSION_M2", "DUCT_TREATMENT", "OBJECT_FOOTPRINT_POLICY", "TRADE_AUTHORITY",
            "OWNER_FACTS_APPLIED", "ROW_AUTHORITY_DIGEST", "RELEASE_BLOCKERS", "regression_vs_r8_15",
            "historical_matching")
    md["14_Q14_REBUILD.md"] = "# Q-14 rebuild\n\n" + bullets(
        {k: q14[k] for k in keys} | {"door strips counted as ceiling": q14["door_strip_is_ceiling"] or "NONE"}) + \
        "\n\n## Floor rows (Q-03 / Q-03P / Q-11 / Q-12 / Q-13)\n" + bullets({k: q13[k] for k in keys}) + "\n\n" + \
        bullets(A["19_effect_on_floor_rows"]) + "\n"
    RV = R["OPENING_REVEAL_REGISTER"]
    md["15_OPENING_REVEAL_REGRESSION.md"] = "# Opening reveal regression\n\n" + tbl(
        ["Opening", "Surface", "Depth / width m", "Height m", "Area m2", "Skirting", "Ceiling"],
        [[x["opening"], x["surface"], x.get("depth_m", x.get("width_m")), x.get("height_m", ""),
          x.get("area_m2", x.get("plan_area_m2")), x["skirting"], x.get("ceiling", "")] for x in RV["door_reveals"]]) + \
        "\n\n## Passages\n" + bullets(RV["passages"]) + "\n\n" + bullets(
        {k: RV[k] for k in ("door_reveal_note", "i1471", "paint", "double_count_guard")}) + "\n"
    MT = R["MARBLE_THRESHOLD_REGISTER"]
    md["16_MARBLE_REGRESSION.md"] = "# Marble regression\n\n" + tbl(
        ["Threshold", "Door", "Authority", "Width mm", "Depth mm", "Plan m2", "lm"],
        [[t["threshold"], t["door_occurrence"], t["authority"], t["clear_width_mm"], t["depth_mm"], t["plan_area_m2"],
          t["length_lm"]] for t in MT["thresholds"]]) + "\n\n" + bullets(
        {"regression vs R8.15": MT["regression_vs_r8_15"], "release blockers": MT["release_blockers"]}) + \
        "\n\n## Every threshold\n" + tbl(["Threshold", "Door", "Class", "State", "m2", "Reconciles"],
                                         [[t["threshold"], t["door_occurrence"], t["classification"],
                                           t["allocation_state"], t["strip_m2"], t["reconciles"]]
                                          for t in S["threshold_audit"]]) + "\n"
    md["17_WALL_FACE_ENGINE_READINESS.md"] = "# Wall-face engine readiness\n\n" + bullets(
        {k: v for k, v in R["WALL_FACE_ENGINE_READINESS"].items() if k != "SCHEMA"}) + "\n"
    md["18_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    CRS = R["CLOSURE_RELEASE_STATUS"]
    md["19_CLOSURE_RELEASE.md"] = "# Closure release\n\n" + bullets(
        {"reached": CRS["reached"], "missing": CRS["missing"], "ceiling": CRS["ceiling"], "closures": CRS["closures"],
         "door closures": CRS["door_closures"], "released": CRS["released"] or "NOTHING"}) + "\n"
    DH = R["DIGEST_HIERARCHY"]
    md["20_ROW_STATUS.md"] = "# Row status\n\n" + rt + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: v[k] for k in ("TOPOLOGY_POLICY", "TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                 "RELEASE_INPUT_DIGEST", "BASE_PHYSICAL_SITES", "THRESHOLD_TREATMENT",
                                                 "PASSAGE_TREATMENT", "DUCT_TREATMENT", "OBJECT_FOOTPRINT_POLICY",
                                                 "OWNER_FACTS_APPLIED", "SOURCE_ANCHOR", "RELEASE_BLOCKERS")})
        for r, v in S["six_rows"].items()) + "\n\n## Extra rows\n" + bullets(S["extra_rows"]) + \
        "\n\n## Digests vs R8.15\n" + bullets({"per row": DH["vs_r8_15"], "reason": DH["reason"]}) + \
        "\n\nOld revision unchanged: " + j(S["old_revision_unchanged_vs_r8_15"]) + "\n\nDeterminism: " + \
        j(S["determinism"]) + "\n"
    md["21_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## Remaining release blockers\n{bullets(A['32_blockers'])}\n\n## R8.17\n{A['35_r8_17']}\n\n{STOP}\n"
    md["22_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.16 test files: " + \
        ", ".join(res["r8_16_test_files"]) + "\n"
    md["23_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + 1, "json +", len(SUPPORT), "supporting")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
