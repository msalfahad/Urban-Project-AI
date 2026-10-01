"""R8.13 review package: URBAN_QTO_R8_13_V4_AND_FLOOR_AUTHORITY (21 md + 16 json + 4 supporting json + zip).

    python3 research/external_engine_lab/r8_13_package.py <junit.xml> "<command>" <exit_code>

Every number comes from the committed registers (tests/r8_13/registers); nothing is typed in.
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

REG = ROOT / "tests/r8_13/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_13_V4_AND_FLOOR_AUTHORITY"
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_FINISH_FACT_REGISTER", "TRADE_OBJECT_FOOTPRINT_POLICY",
         "SEMANTIC_SPACE_CLASS_REGISTER", "WALL_BAND_V4_POLICY", "R8_13_V4_FREEZE", "BLIND_QORTUBA_V4_RESULT",
         "V3_DEFECT_RESOLUTION", "Q13_STATUS", "Q14_STATUS", "QORTUBA_R8_13_STATUS", "DIGEST_HIERARCHY",
         "SOURCE_ANCHOR_STATUS", "CLOSURE_RELEASE_MODEL", "R8_13_DECISION_REGISTER")
SUPPORT = ("BLIND_COMPARISON", "WET_SERVICE_FINISH_SCOPE", "SKIRTING_METHOD_FACT", "ENGINEERING_ACTION_REGISTER")


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=900):
    return json.dumps(v, ensure_ascii=False)[:n]


def bullets(d):
    return "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 600)}" for k, v in d.items())


def six_table(six):
    return tbl(["Row", "State", "Value m2", "Sites", "Classes", "Footprint policy", "Strips (excl / incl m2)",
                "Row authority", "Release blockers"],
               [[r, v["STATE"], "" if v["VALUE"] is None else f"{v['VALUE']:.4f}", len(v["PHYSICAL_SITES"]),
                 ", ".join(v["SEMANTIC_CLASSES"] or ["-"]), "; ".join(v["OBJECT_FOOTPRINT_POLICY"]),
                 f"{v['THRESHOLD_PASSAGE_TREATMENT']['excluded_area_m2']} / "
                 f"{v['THRESHOLD_PASSAGE_TREATMENT']['included_area_m2']}", v["ROW_AUTHORITY_DIGEST"][:12],
                 len(v["RELEASE_BLOCKERS"])] for r, v in six.items()])


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS + SUPPORT}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_13_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_13_test_files": sorted(p.name for p in (ROOT / "tests/r8_13").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_13_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_13_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_13_STATUS"]
    A, G, six = D["answers"], D["gates"], S["six_rows"]
    V, BC, FZ = R["V3_DEFECT_RESOLUTION"], R["BLIND_COMPARISON"], R["R8_13_V4_FREEZE"]
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    tests = tbl(["Commit", "Command", "Passed", "XFailed", "Skipped", "Failed", "Errors", "Total", "Exit"],
                [[commit, f"`{command}`", jr["passed"], jr["xfailed"], jr["skipped"], jr["failed"], jr["errors"],
                  jr["total"], exit_code]])
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = (
        "# R8.13 - wall-band V4, Qortuba floor / finish owner authority, Q-13 completion\n\n"
        f"**{O['headline']}**\n\n" + six_table(six) +
        f"\n\n- V4 frozen at `{FZ['frozen_commit'][:12]}` ({FZ['wall_band_policy']['id']} "
        f"`{FZ['wall_band_policy']['digest'][:16]}`), blind run committed before any comparison.\n"
        f"- V3-D1: {V['V3_D1']['state']}; V3-D2: {V['V3_D2']['state']} (false 6.0 m passage "
        f"{V['V3_D2']['blind_result']['false_passage_OP_a38c9a827025e4a9']}).\n"
        f"- H2430 / H2431 keep their V3 geometry and areas ({BC['h2430']['separated_m2']} / "
        f"{BC['h2431']['separated_m2']} m2); H1316 stays NOT_WALL_CAP.\n"
        f"- Q-13 {q13['STATE']} {q13['VALUE']} m2 with the scoped floor fact; Q-14 {q14['regression']['result']} "
        f"({q14['VALUE']} m2).\n\n" + tests + "\n\n" + bullets(G) + "\n\nSTOP AFTER R8.13. NO PRODUCTION MIGRATION.\n")
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n" + bullets(
        {"answered": O["answered"], "why_none": O["why_none"], "do not ask again": O["do_not_ask"]}) + "\n"
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Recommendation (written before coding)\n\n" + bullets(
        D["recommendation_before_coding"]) + "\n"
    F = R["OWNER_FINISH_FACT_REGISTER"]
    md["03_OWNER_FINISH_FACTS.md"] = "# Owner finish facts\n\n" + "\n\n".join(
        f"## {f['ref']} ({f['kind']})\n- statement: {j(f['statement'], 700)}\n- scope: {j(f['scope'])}\n- binding: "
        f"{f['binding']}\n- row outcomes: {f['row_outcomes']}\n- relations: {j(f['relations'], 900)}"
        for f in F["facts"]) + f"\n\n## Reconciliation rule\n{F['rule']}\n\nSilent contradictions: " \
        f"{F['silent_contradictions'] or 'NONE'}\n"
    FP = R["TRADE_OBJECT_FOOTPRINT_POLICY"]
    md["04_FLOOR_OBJECT_FOOTPRINT_POLICY.md"] = "# Floor object-footprint policy\n\n" + bullets(
        {"policies": FP["policies"], "applied_to": FP["applied_to"], "leak check": FP["leak_check_other_rows_changed"],
         "Q-13 without it": FP["q13_without_the_policy"], "blockers it clears": FP["blockers_cleared_by_the_policy"],
         "never": FP["never"]}) + "\n"
    md["05_WALL_BAND_V4.md"] = "# WALL_BAND_POLICY_V4\n\n" + bullets(
        {k: R["WALL_BAND_V4_POLICY"]["policy"]["params"][k] for k in (
            "elongation_basis", "structural_support", "support_loop_roles", "chain_identity", "band_identity",
            "id_collision", "passage_target_roles")}) + "\n\nHistory:\n" + "\n".join(
        f"- {h}" for h in R["WALL_BAND_V4_POLICY"]["policy"]["history"]) + "\n"
    md["06_V4_SYNTHETIC_FREEZE.md"] = "# V4 synthetic freeze\n\n" + bullets(
        {k: FZ[k] for k in ("frozen_commit", "wall_band_policy", "closure_policy", "synthetic_test_digest",
                            "superseded_frozen_tests", "qortuba_before_freeze", "floor_fact_available_to_v4",
                            "order", "rule")}) + "\n\nTests:\n" + "\n".join(f"- {t}" for t in FZ["v4_synthetic_tests"]) + "\n"
    md["07_BLIND_QORTUBA_V4.md"] = "# Blind Qortuba V4 run\n\n" + bullets(
        {k: BC[k] for k in ("order", "lab_reproduces_blind", "counts", "h2430", "h2431", "h1316", "hall_m2",
                            "labelled_site_areas_unchanged", "ids", "passages", "topology_digest")}) + "\n"
    md["08_V3_DEFECT_RESOLUTION.md"] = "# V3 defect resolution\n\n" + bullets(
        {"V3-D1": V["V3_D1"], "V3-D2": V["V3_D2"], "band diff": V["band_diff_v3_to_v4"],
         "post-blind observations (R8.14)": V["post_blind_observations_for_r8_14"]}) + "\n"
    md["09_Q13_REBUILD.md"] = "# Q-13 rebuild\n\n" + bullets(
        {k: q13[k] for k in ("STATE", "VALUE", "PHYSICAL_SITES", "SEMANTIC_CLASSES", "TRADE_RULES",
                             "OBJECT_FOOTPRINT_POLICY", "object_footprints", "strips", "OWNER_FACTS_CLAIMS",
                             "ROW_AUTHORITY_DIGEST", "RELEASE_BLOCKERS", "without_the_floor_fact", "r8_12",
                             "historical_matching")}) + "\n"
    md["10_Q14_REGRESSION.md"] = "# Q-14 regression\n\n" + bullets(
        {k: q14[k] for k in ("STATE", "VALUE", "regression", "PHYSICAL_SITES", "RELEASE_BLOCKERS",
                             "OWNER_FACTS_CLAIMS")}) + "\n"
    SC = R["SEMANTIC_SPACE_CLASS_REGISTER"]
    md["11_SEMANTIC_SPACE_CLASSES.md"] = "# Semantic space classes\n\n" + bullets(
        {k: SC[k] for k in ("rule", "supersedes", "classes", "owner_room_types", "floor_treatment_by_class",
                            "never")}) + "\n"
    W = R["WET_SERVICE_FINISH_SCOPE"]
    md["12_WET_SERVICE_FINISH_SCOPE.md"] = "# Wet / service finish scope (this Qortuba case only)\n\n" + bullets(W) + "\n"
    md["13_SKIRTING_METHOD_FACT.md"] = "# Skirting method fact\n\n" + bullets(R["SKIRTING_METHOD_FACT"]) + "\n"
    DH = R["DIGEST_HIERARCHY"]
    md["14_DIGEST_PROVENANCE.md"] = "# Digest provenance\n\n" + tbl(
        ["Row", "Topology", "Row authority", "Release", "Facts applied to row"],
        [[r, v["TOPOLOGY_RUN_INPUT_DIGEST"][:16], v["ROW_AUTHORITY_DIGEST"]["digest"][:16],
          v["RELEASE_INPUT_DIGEST"]["digest"][:16], ", ".join(v["ROW_AUTHORITY_DIGEST"]["owner_facts_applied"]) or "-"]
         for r, v in DH["rows"].items()]) + "\n\n" + bullets(
        {k: DH[k] for k in ("floor_fact", "changed_in_r8_13", "q13_row_authority_without_the_floor_fact",
                            "generic_in_engine", "still_lab")}) + "\n"
    md["15_SOURCE_ANCHOR.md"] = "# Source anchor\n\n" + bullets(R["SOURCE_ANCHOR_STATUS"]) + "\n"
    CRM = R["CLOSURE_RELEASE_MODEL"]
    md["16_CLOSURE_RELEASE_MODEL.md"] = "# Reviewed closure release model\n\n" + bullets(
        {"policy": CRM["policy"], "closures": CRM["closures"], "cross route": CRM["cross_route_note"],
         "released": CRM["released"] or "NOTHING"}) + "\n"
    md["17_SIX_ROW_STATUS.md"] = "# Six-row status\n\n" + six_table(six) + "\n\n" + "\n\n".join(
        f"## {r}\n" + bullets({k: v[k] for k in ("TOPOLOGY_POLICY", "RUN_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                 "RELEASE_INPUT_DIGEST", "TRADE_RULES", "OBJECT_FOOTPRINT_POLICY",
                                                 "OWNER_FACTS_CLAIMS", "SOURCE_ANCHOR", "RELEASE_BLOCKERS")})
        for r, v in six.items()) + "\n\nOld revision unchanged: " + j(S["old_revision_unchanged"]) + \
        "\n\nDeterminism: " + j(S["determinism"]) + "\n"
    md["18_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        "\n\n## Engineering actions (R8.14)\n" + "\n".join(
            f"- **{a['id']}** (P{a['priority']}) {a['title']}" for a in R["ENGINEERING_ACTION_REGISTER"]["actions"]) + \
        "\n\nSTOP AFTER R8.13. NO PRODUCTION MIGRATION.\n"
    md["19_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.13 test files: " + \
        ", ".join(res["r8_13_test_files"]) + "\n"
    md["20_CLAUDE_FINAL_RECOMMENDATION.md"] = "# Final recommendation\n\n" + "\n".join(
        f"{i}. **{k.split('_', 1)[1].replace('_', ' ')}:** {v if isinstance(v, str) else j(v, 900)}"
        for i, (k, v) in enumerate(A.items(), 1)) + "\n\nSTOP AFTER R8.13. NO PRODUCTION MIGRATION.\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(JSONS) + 1, "json +", len(SUPPORT), "supporting")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
