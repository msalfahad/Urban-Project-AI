"""R8.14 review package: URBAN_QTO_R8_14_THRESHOLD_SOFFIT_SKIRTING_RELEASE (22 md + 20 json + 2 supporting + zip).

    python3 research/external_engine_lab/r8_14_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_14/registers); nothing is typed in.
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

REG = ROOT / "tests/r8_14/registers"
NAME = "URBAN_QTO_R8_14_THRESHOLD_SOFFIT_SKIRTING_RELEASE"
OUT = ROOT / "data/reports" / NAME
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_METHOD_FACT_REGISTER", "DOOR_THRESHOLD_REGISTER", "DOOR_TRANSITION_POLICY",
         "MARBLE_THRESHOLD_EVIDENCE", "OPEN_PASSAGE_REVEAL_REGISTER", "SOFFIT_ALLOCATION_POLICY",
         "SKIRTING_METHOD_POLICY", "SKIRTING_READINESS", "V4_O1_REGISTER", "V4_O2_REGISTER", "WALL_BAND_POLICY_STATUS",
         "SOURCE_ANCHOR_STATUS", "CLOSURE_RELEASE_STATUS", "Q13_STATUS", "Q14_STATUS", "QORTUBA_R8_14_STATUS",
         "DIGEST_HIERARCHY", "R8_14_DECISION_REGISTER")
SUPPORT = ("R8_14_V5_FREEZE", "BLIND_QORTUBA_V5_RESULT")
STOP = "STOP AFTER R8.14. NO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=900):
    return json.dumps(v, ensure_ascii=False)[:n]


def bullets(d):
    return "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 700)}" for k, v in d.items())


def f4(v):
    return "" if v is None else f"{v:.4f}"


def six_table(six):
    return tbl(["Row", "State", "Value m2", "Base sites m2", "Thresholds m2", "Soffit m2", "Footprint policy",
                "Classes", "Trade authority", "Topology", "Row authority", "Anchor", "Release blockers"],
               [[r, v["STATE"], f4(v["VALUE"]), f4(v["BASE_SITE_AREA_M2"]), v["THRESHOLD_CONTRIBUTION_M2"],
                 v["PASSAGE_TREATMENT"]["soffit_exclusion_m2"], "; ".join(v["OBJECT_FOOTPRINT_POLICY"]),
                 ", ".join(v["SEMANTIC_CLASSES"] or ["-"]), "; ".join(v["TRADE_AUTHORITY"]),
                 v["TOPOLOGY_DIGEST"][:12], v["ROW_AUTHORITY_DIGEST"][:12], "NOT_ESTABLISHED",
                 len(v["RELEASE_BLOCKERS"])] for r, v in six.items()])


def threshold_table(T):
    return tbl(["Threshold", "Door", "Strip m2", "W x T mm", "Plane", "Side A", "Side B", "State", "Regions",
                "Receiving rows"],
               [[t["threshold"], t["door_occurrence"], t["strip_m2"], f"{t['width_mm']} x {t['thickness_mm']}",
                 t["transition_plane_authority"], f"{'/'.join(t['side_A']['zones'] or ['-'])} "
                 f"({t['side_A']['treatment']})", f"{'/'.join(t['side_B']['zones'] or ['-'])} "
                 f"({t['side_B']['treatment']})", t["allocation_state"],
                 "; ".join(f"{r['side']} {r['treatment']} {r['area_m2']}" for r in t["regions"]) or "-",
                 j(t["receiving_rows"], 200)] for t in T["thresholds"]])


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS + SUPPORT}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_14_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_14_test_files": sorted(p.name for p in (ROOT / "tests/r8_14").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_14_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_14_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_14_STATUS"]
    A, G, six = D["answers"], D["gates"], S["six_rows"]
    T, MB = R["DOOR_THRESHOLD_REGISTER"], R["MARBLE_THRESHOLD_EVIDENCE"]
    RV, SO = R["OPEN_PASSAGE_REVEAL_REGISTER"], R["SOFFIT_ALLOCATION_POLICY"]
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    WS, FZ = R["WALL_BAND_POLICY_STATUS"], R["R8_14_V5_FREEZE"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.14 - door thresholds, open-passage soffit / reveals, skirting path, V4-O1 / V4-O2, release preparation\n\n"
        f"**{O['headline']}**\n\n" + six_table(six) +
        f"\n\n- V5 frozen at `{FZ['frozen_commit'][:12]}` (`{FZ['wall_band_policy']['digest'][:16]}`), blind run "
        "committed before any comparison.\n"
        f"- Thresholds: {T['allocated']} of {T['count']} allocated ({j(T['by_state'], 200)}); every one reconciles "
        f"exactly: {T['reconciled_exactly']}. Marble: {MB['result']}.\n"
        f"- Hall / Lobby soffit {round(SO['footprint_m2_from_source'], 6)} m2 out of Q-14 ({SO['hall_lobby_audit']['state']})"
        "; jambs + soffit recorded as plaster reveal surfaces; no paint.\n"
        f"- Skirting: method explicit, quantity {R['SKIRTING_READINESS']['quantity']}.\n"
        f"- V4-O1 material ({R['V4_O1_REGISTER']['rows_affected']}): release blocker + counterfactual; V4-O2 "
        f"{R['V4_O2_REGISTER']['state']}.\n\n" + tests + "\n\n" + bullets(G) + f"\n\n{STOP}\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"why none": O["why_none"], "answered this round": O["answered_this_round"],
         "prepared for the release stage (NOT asked now)": O["prepared_for_release_stage_not_asked"],
         "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    F = R["OWNER_METHOD_FACT_REGISTER"]
    md["03_OWNER_METHOD_FACTS.md"] = "# Owner method facts\n\n" + "\n\n".join(
        f"## {f['ref']} ({f['kind']})\n- statement: {j(f['statement'], 800)}\n- scope: {j(f['scope'])}\n"
        f"- domains: {f['allowed_domains']}\n- binding: {f['binding']}\n- relations: {j(f['relations'], 600)}"
        for f in F["facts"]) + "\n\nSilent contradictions: " + (j(F["silent_contradictions"]) if
                                                                 F["silent_contradictions"] else "NONE") + "\n"
    DTP = R["DOOR_TRANSITION_POLICY"]
    md["04_DOOR_THRESHOLD_MODEL.md"] = "# Door threshold model\n\n" + bullets(
        {"policy": DTP["policy"]["policy_id"], "plane authority": DTP["policy"]["plane_authority"],
         "states": DTP["policy"]["states"], "params": DTP["policy"]["params"],
         "hierarchy applied": DTP["plane_hierarchy_applied"], "unit boundary rule": DTP["unit_boundary_rule"],
         "strip audit": DTP["strip_audit_policy"], "never": DTP["never"]}) + "\n"
    md["05_THRESHOLD_QORTUBA_RESULTS.md"] = "# Thresholds - Qortuba (new revision)\n\n" + threshold_table(T) + \
        "\n\n" + bullets({"reconciled exactly": T["reconciled_exactly"], "outside the unit": T["outside_measured_unit"],
                          "unit boundary": T["unit_boundary"], "ceiling": T["ceiling"],
                          "old revision": T["old_revision"]}) + "\n"
    md["06_MARBLE_EVIDENCE_REVIEW.md"] = "# Marble evidence review\n\n" + bullets(MB) + "\n"
    md["07_OPEN_PASSAGE_REVEAL_MODEL.md"] = "# Open-passage reveal model\n\n" + tbl(
        ["Surface", "Area m2", "Finish", "Trade"], [[s["surface"], round(s["area_m2"], 6), s["finish"], s["trade"]]
                                                    for s in RV["surfaces"]]) + "\n\n" + bullets(
        {"ownership": RV["hall_lobby"]["ownership"], "paint": RV["paint"],
         "double claims": RV["ownership_guard_double_claims"] or "NONE", "US-07": RV["us07_reconciliation"],
         "plaster quantity": RV["plaster_quantity"], "other passages": RV["other_passages"],
         "policy": RV["policy"]}) + "\n"
    md["08_Q14_SOFFIT_ALLOCATION.md"] = "# Q-14 soffit allocation\n\n" + bullets(SO) + "\n"
    SM = R["SKIRTING_METHOD_POLICY"]
    md["09_SKIRTING_METHOD.md"] = "# Skirting method\n\n" + bullets(SM) + "\n"
    SK = R["SKIRTING_READINESS"]
    md["10_SKIRTING_GEOMETRY_READINESS.md"] = "# Skirting geometry readiness\n\n" + tbl(
        ["Site", "Zones", "Edges by class", "Withheld"],
        [[s, "/".join(v["zones"]), j(v["edges_by_class"], 300), len(v["withheld"])]
         for s, v in SK["dry_rooms_classified"].items()]) + "\n\n" + bullets(
        {"quantity": SK["quantity"], "missing": SK["missing_components"], "never": SK["never_used"],
         "no-skirting classes": SK["no_skirting_classes"]}) + "\n"
    md["11_V4_O1_REVIEW.md"] = "# V4-O1 review\n\n" + bullets(R["V4_O1_REGISTER"]) + "\n"
    md["12_V4_O2_REVIEW.md"] = "# V4-O2 review\n\n" + bullets(R["V4_O2_REGISTER"]) + "\n"
    md["13_WALL_BAND_POLICY_STATUS.md"] = "# Wall-band policy status (V5)\n\n" + bullets(
        {k: WS[k] for k in ("version", "supersedes", "lab_reproduces_blind", "v4_to_v5", "h2430_h2431", "h1316",
                            "hall_m2", "labelled_sites_unchanged_vs_v4", "determinism")}) + \
        "\n\nFreeze:\n" + bullets({k: FZ[k] for k in ("frozen_commit", "wall_band_policy", "synthetic_test_digest",
                                                       "superseded_frozen_tests", "qortuba_before_freeze",
                                                       "owner_facts_available_to_v5", "order")}) + \
        "\n\nV5 tests:\n" + "\n".join(f"- {t}" for t in FZ["v5_synthetic_tests"]) + "\n"
    md["14_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    CRS = R["CLOSURE_RELEASE_STATUS"]
    md["15_CLOSURE_RELEASE_STATUS.md"] = "# Closure release status\n\n" + bullets(
        {"reached": CRS["reached"], "missing": CRS["missing"], "ceiling": CRS["ceiling"], "closures": CRS["closures"],
         "released": CRS["released"] or "NOTHING"}) + "\n"
    md["16_Q13_REBUILD.md"] = "# Q-13 rebuild\n\n" + bullets(
        {k: q13[k] for k in ("STATE", "VALUE", "rebuild", "BASE_SITE_AREA_M2", "THRESHOLD_CONTRIBUTION_M2",
                             "thresholds", "PASSAGE_TREATMENT", "PHYSICAL_SITES", "SEMANTIC_CLASSES",
                             "TRADE_AUTHORITY", "OBJECT_FOOTPRINT_POLICY", "OWNER_FACTS_APPLIED", "COUNTERFACTUALS",
                             "ROW_AUTHORITY_DIGEST", "RELEASE_BLOCKERS", "regression_vs_r8_13",
                             "historical_matching")}) + "\n"
    md["17_Q14_REBUILD.md"] = "# Q-14 rebuild\n\n" + bullets(
        {k: q14[k] for k in ("STATE", "VALUE", "rebuild", "BASE_SITE_AREA_M2", "soffit", "THRESHOLDS",
                             "PASSAGE_TREATMENT", "PHYSICAL_SITES", "OBJECT_FOOTPRINT_POLICY", "OWNER_FACTS_APPLIED",
                             "COUNTERFACTUALS", "ROW_AUTHORITY_DIGEST", "RELEASE_BLOCKERS", "regression_vs_r8_13",
                             "historical_matching")}) + "\n"
    DH = R["DIGEST_HIERARCHY"]
    md["18_SIX_ROW_STATUS.md"] = "# Six-row status\n\n" + six_table(six) + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: v[k] for k in ("TOPOLOGY_POLICY", "TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                 "RELEASE_INPUT_DIGEST", "THRESHOLDS", "PASSAGE_TREATMENT",
                                                 "OWNER_FACTS_APPLIED", "COUNTERFACTUALS", "RELEASE_BLOCKERS")})
        for r, v in six.items()) + "\n\n## Digests vs R8.13\n" + bullets(
        {"per row": DH["vs_r8_13"], "reasons": DH["reasons"], "facts": DH["facts_never_topology"]}) + \
        "\n\nPantry / service rows: " + j(S["pantry_service_rows"]) + "\n\nOld revision unchanged: " + \
        j(S["old_revision_unchanged_vs_r8_13"]) + "\n\nDeterminism: " + j(S["determinism"]) + "\n"
    md["19_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        f"\n\n## R8.15\n{A['35_r8_15']}\n\n{STOP}\n"
    md["20_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.14 test files: " + \
        ", ".join(res["r8_14_test_files"]) + "\n"
    md["21_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + f"\n\n{STOP}\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + 1, "json +", len(SUPPORT), "supporting")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
