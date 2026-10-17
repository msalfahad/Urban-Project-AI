"""R8.12 review package: URBAN_QTO_R8_12_FRAGMENT_AWARE_WALL_BANDS (19 md + 16 json + zip).

    python3 research/external_engine_lab/r8_12_package.py <junit.xml> "<command>" <exit_code>
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

REG = ROOT / "tests/r8_12/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_12_FRAGMENT_AWARE_WALL_BANDS"
JSONS = ("OWNER_ACTION_REGISTER", "ENGINEERING_ACTION_REGISTER", "FRAGMENT_FACE_POLICY", "FACE_CHAIN_REGISTER",
         "BAND_SPAN_REGISTER", "WALL_BAND_ASSEMBLY_REGISTER", "R8_12_FRAGMENT_BAND_FREEZE", "BLIND_QORTUBA_RESULT",
         "TOPOLOGY_CLOSURE_REGISTER", "OWNER_FACT_COMPARISON", "Q14_STATUS", "Q13_STATUS", "DIGEST_HIERARCHY",
         "POLICY_PROVENANCE_AUDIT", "R8_12_DECISION_REGISTER", "QORTUBA_R8_12_STATUS")


def jl(p):
    return json.loads(Path(p).read_text())


def j(v, n=700):
    return json.dumps(v, ensure_ascii=False)[:n]


def rows_md(rows):
    return tbl(["Row", "State", "Value m2", "Sites", "Bands", "Closures", "Passages", "Treatment", "Footprint",
                "Release blockers"],
               [[r, v["state"], "" if v["value"] is None else f"{v['value']:.4f}", len(v["physical_site_ids"]),
                 len(v["wall_bands"]), ", ".join(v["topology_closures_applied"]) or "-", len(v["open_passage_sites"]),
                 v["trade_authority"]["rule"], v["footprint_authority"]["treatment"] or "NONE",
                 len(v["release_blockers"])] for r, v in rows.items()])


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_12_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_12_test_files": sorted(p.name for p in (ROOT / "tests/r8_12").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_12_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    D, O, S = R["R8_12_DECISION_REGISTER"], R["OWNER_ACTION_REGISTER"], R["QORTUBA_R8_12_STATUS"]
    A, G, rows = D["answers"], D["gates"], S["rows"]["NEW_K2_R8_12"]
    B, FZ, P = R["BLIND_QORTUBA_RESULT"], R["R8_12_FRAGMENT_BAND_FREEZE"], R["FRAGMENT_FACE_POLICY"]["policy"]
    q14, q13 = R["Q14_STATUS"], R["Q13_STATUS"]
    tests = (f"commit `{commit}` · `{command}` · passed {jr['passed']} · xfailed {jr['xfailed']} · skipped "
             f"{jr['skipped']} · failed {jr['failed']} · errors {jr['errors']} · total {jr['total']} · exit {exit_code}")
    owner = ("**ONE OWNER QUESTION** - " + O["required_now"][0]["question"]) if O["required_now"] else \
        "**NO OWNER ACTION REQUIRED.**"
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.12 — Fragment-aware wall bands, local band spans, blind Qortuba re-run (SHADOW)

## Owner
{owner}

## What R8.12 did
- **WALL_BAND_POLICY_V3** pairs walls locally:
  - **face chains** join source fragments only when continuity is positively established, with typed nodes;
  - **local band spans** use local mutual nearest per interval;
  - **wall-band assemblies** carry the ends;
  - crossings subdivide a strip instead of rejecting it.

  It was frozen with synthetic tests **before** any Qortuba run (`{FZ['frozen_commit'][:12]}`).
- **Blind run, H2430:** the band forms from H470 + H471 against H477.
  - Column H718 blocks only its own interval.
  - H2430 is a WALL_END_CAP_PROVEN, and a zero-material closure is AUTHORISED_FOR_SHADOW. It removes the 0.3813 m2
    wall core.
  - The H2431 closure is kept, and H1316 still gets no closure.
  - The Hall / Lobby passage is now detected by the engine (1196.45 mm) and stays open.
- **The owner fact, compared afterwards, agrees on all 7 parts.** It is corroboration only: no owner role claim was
  needed.
- **Q-14 = COMPUTED_SHADOW {q14['value']} m2** (not FINAL). The release blockers are the source anchor and the passage
  soffit allocation.
- **Q-13:** the only remaining blocker is the floor-under-objects fact. This is shown by a counterfactual over both
  answers.
- Digest hierarchy: TOPOLOGY / ROW_AUTHORITY / RELEASE_INPUT. Generic owner physical-fact model.
- Two V3 findings are recorded for R8.13 and not patched: a chain-id collision, and elongation measured on the chain
  overlap.

## Qortuba six rows (new revision)
{rows_md(rows)}

## Gates
- MIGRATION_PLANNING_READY = **{G['MIGRATION_PLANNING_READY']}**
- MIGRATION_EXECUTION_READY = **{G['MIGRATION_EXECUTION_READY']}**
- PRODUCTION_MIGRATION = **{G['PRODUCTION_MIGRATION']}**

## Tests
{tests}

STOP AFTER R8.12. NO PRODUCTION MIGRATION.
"""
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n{owner}\n\n" + ("\n".join(
        f"- why now: {a['why_now']}\n- recorded as: {a['records_as']}" for a in O["required_now"])) + \
        "\n\n## Never asked again\n" + "\n".join(f"- {x}" for x in O["do_not_ask"]) + "\n"
    rec = D["recommendation_before_coding"]
    md["02_CLAUDE_RECOMMENDATION.md"] = "# Claude recommendation (written before coding)\n\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else j(v, 1500)}" for k, v in rec.items() if k[0].isdigit()) + \
        "\n\n## Answers 1-29\n" + "\n".join(f"- **{k}:** {v if isinstance(v, str) else j(v, 900)}"
                                            for k, v in A.items()) + "\n"
    md["03_FRAGMENT_FACE_MODEL.md"] = "# Fragment face model (FACE_CHAIN)\n\n" + "\n".join(
        f"- **{k}:** {v}" for k, v in P["params"].items() if k in ("chain_join", "duplicate")) + \
        "\n\nNodes: " + ", ".join(P["chain_nodes"]) + "\n\n## Qortuba (new revision)\n" + j(
            {k: v for k, v in R["FACE_CHAIN_REGISTER"]["NEW_K2"].items() if k != "multi_fragment"}, 2500) + \
        "\n\n## Multi-fragment chains\n" + tbl(["Chain", "Fragments", "Nodes"], [
            [c["chain_id"], ", ".join(c["fragments"]), "; ".join(f"{n['kind']}@{n['s']}" + (f"({n['by']})" if n["by"]
                                                                                           else "") for n in c["nodes"])]
            for c in R["FACE_CHAIN_REGISTER"]["NEW_K2"]["multi_fragment"]]) + \
        "\n\n## Finding V3-D1\n" + R["FACE_CHAIN_REGISTER"]["finding_V3_D1"] + "\n"
    md["04_LOCAL_BAND_SPANS.md"] = "# Local band spans\n\n" + "\n".join(
        f"- **{k}:** {v}" for k, v in P["params"].items() if k in ("parallel", "elongation_ratio", "elongation_basis",
                                                                     "local_mutual_nearest", "one_side_margin",
                                                                     "nearest_tie", "strip")) + \
        "\n\nInterval classes: " + ", ".join(P["interval_classes"]) + "\n\n" + R["BAND_SPAN_REGISTER"]["rule"] + \
        f"\n\nSpans (new revision): {len(R['BAND_SPAN_REGISTER']['NEW_K2'])}; the H2430 band:\n\n" + \
        tbl(["Span", "s", "Source intervals"], [[sp["span_id"], sp["s"], j(sp["source_intervals"], 400)]
                                                for b in B["NEW_K2"]["watched_bands"] if "2430" in json.dumps(b["ends"])
                                                for sp in b["span_records"]]) + "\n"
    W = R["WALL_BAND_ASSEMBLY_REGISTER"]
    md["05_BAND_ASSEMBLY.md"] = "# Wall-band assemblies\n\n" + W["means"] + "\n\nCounts: " + j(W["counts"]) + \
        "\n\nEnds: " + ", ".join(P["ends"]) + "\n\n## Finding V3-D2\n" + W["finding_V3_D2"] + "\n\n" + tbl(
            ["Band", "Faces", "Width mm", "Length mm", "Intervals", "Ends"],
            [[b["band_id"], ", ".join(b["faces"]), b["width_mm"], b["length_mm"],
              "; ".join(iv["class"] for iv in b["intervals"]), ", ".join(b["ends"])] for b in W["wide_bands"]]) + "\n"
    md["06_SYNTHETIC_FREEZE.md"] = "# Synthetic freeze\n\n" + tbl(["Field", "Value"], [
        ["frozen commit", FZ["frozen_commit"]], ["wall band policy", j(FZ["wall_band_policy"])],
        ["closure policy", j(FZ["closure_policy"])], ["synthetic test digest", FZ["synthetic_test_digest"]],
        ["Qortuba runs before freeze", FZ["qortuba_runs_before_freeze"]]]) + "\n\n" + "\n".join(
        f"- {f}: `{h[:16]}...`" for f, h in FZ["synthetic_test_sha256"].items()) + "\n\nOrder: " + \
        " -> ".join(FZ["order"]) + "\n\n" + FZ["rule"] + "\n"
    md["07_BLIND_QORTUBA_RESULT.md"] = "# Blind Qortuba result\n\n" + j(B["blind"], 2000) + "\n\n## Counts\n" + \
        j({k: B[k]["counts"] for k in ("NEW_K2", "OLD_K1")}) + "\n\n## Closures (new)\n" + tbl(
            ["Closure", "Release", "Geometry", "Evidence", "Separated"],
            [[c["closure_id"], c["release"], c["geometry"], c["evidence"],
              j(c["safety"]["separated_pieces"], 300)] for c in B["NEW_K2"]["closures"]]) + \
        "\n\n## Passages (new)\n" + tbl(["Passage", "End", "Target", "Width mm", "Thickness mm"],
                                        [[p["passage_id"], p["end_kind"], p["target"], p["width_mm"], p["thickness_mm"]]
                                         for p in B["NEW_K2"]["passages"]]) + \
        f"\n\nHALL: {j(B['NEW_K2']['hall'])}\n"
    md["08_H2430_ANALYSIS.md"] = "# H2430\n\n" + j(A["9_blind_h2430"], 4000) + "\n\n- column: " + A["8_column_718"] + \
        "\n- west core: " + A["13_west_core_0_3813"] + "\n- owner fact: " + A["11_owner_fact_agrees"] + \
        "\n- fallback: " + A["12_fallback_role_claim"] + "\n"
    T = R["TOPOLOGY_CLOSURE_REGISTER"]
    md["09_H2431_REGRESSION.md"] = "# H2431 regression\n\n" + j(T["h2431_regression"], 3000) + "\n"
    md["10_H1316_NEGATIVE_CONTROL.md"] = "# H1316 negative control\n\n" + j(T["h1316_control"]) + \
        "\n\nSynthetic: tests/r8_12/test_r8_12_fragment_bands.py::test_a_window_jamb_line_beside_glazing_is_still_" \
        "not_a_wall_end\n"
    OFC = R["OWNER_FACT_COMPARISON"]
    md["11_OWNER_FACT_COMPARISON.md"] = "# Owner fact vs engine\n\n" + OFC["order"] + "\n\n" + tbl(
        ["Part", "Owner", "Engine", "Matrix"], [[x["part"], x["owner_reading"], f"{x['engine_state']} "
                                                f"{x['engine_reading']}", x["matrix"]] for x in OFC["per_part"]]) + \
        "\n\n## Domains\n" + tbl(["Domain", "Outcome", "Note"], [[k, v["outcome"], v["note"]]
                                                                 for k, v in OFC["domains"].items()]) + \
        "\n\n## Matrix definition\n" + "\n".join(f"- {k}: {v}" for k, v in OFC["matrix_definition"].items()) + "\n"
    md["12_Q14_REBUILD.md"] = f"# Q-14 rebuild\n\nState **{q14['state']}**, value **{q14['value']} m2** (R8.11: " \
        f"{q14['r8_11']['state']}). Not FINAL.\n\n" + tbl(["Site zones", "m2", "Decision"], [
            [u["zones"], u["area_m2"], u["decision"]] for u in q14["sites_used"]]) + "\n\n## Rebuild\n" + "\n".join(
        f"- **{k}:** {j(v, 600)}" for k, v in q14["rebuild"].items()) + "\n\n## Owner facts\n" + j(q14["owner_facts"]) + \
        "\n\n## Release blockers\n" + "\n".join(f"- {b}" for b in q14["release_blockers"]) + "\n"
    md["13_Q13_STATUS.md"] = f"# Q-13\n\nState **{q13['state']}**.\n\nBlocker set: {q13['blocker_set']}\n\n" \
        "## Sole-blocker test\n" + j(q13["sole_blocker_test"], 3000) + "\n"
    DH = R["DIGEST_HIERARCHY"]
    md["14_DIGEST_HIERARCHY.md"] = "# Digest hierarchy\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in
                                                                         DH["definition"].items()) + \
        "\n\n## Rows\n" + tbl(["Row", "Topology", "Row authority", "Release"], [
            [r, v["TOPOLOGY_RUN_INPUT_DIGEST"][:16], v["ROW_AUTHORITY_DIGEST"]["digest"][:16],
             v["RELEASE_INPUT_DIGEST"]["digest"][:16]] for r, v in DH["rows"].items()]) + \
        "\n\n## The Hall / Lobby owner fact\n" + "\n".join(f"- {k}: {v}" for k, v in DH["hall_lobby_fact"].items()) + "\n"
    md["15_OWNER_PHYSICAL_FACT_MODEL.md"] = "# Owner physical fact model\n\n`engine/source/owner_facts.py` (" + \
        OFC["policy"]["policy_id"] + ")\n\n- outcomes: " + ", ".join(OFC["policy"]["outcomes"]) + "\n- domains: " + \
        ", ".join(OFC["policy"]["domains"]) + "\n- kind domains: " + j(OFC["policy"]["kind_domains"]) + \
        "\n- binding: " + OFC["policy"]["binding"] + "\n- never: " + "; ".join(OFC["policy"]["never"]) + \
        "\n\nStatus: " + A["25_owner_facts_generic"] + "\n"
    PA = R["POLICY_PROVENANCE_AUDIT"]
    md["16_POLICY_PROVENANCE_AUDIT.md"] = "# Policy provenance audit\n\n" + j(PA, 6000) + "\n"
    md["17_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        "\n\n## Order\n" + "\n".join(f"- {o}" for o in D["order"]) + "\n\n## Engineering actions\n" + "\n".join(
            f"- **{a['id']}** {a['title']}" + (f": {a['what']}" if a.get("what") else "")
            for a in R["ENGINEERING_ACTION_REGISTER"]["actions"]) + "\n\nSTOP AFTER R8.12. NO PRODUCTION MIGRATION.\n"
    md["18_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.12 test files: " + \
        ", ".join(res["r8_12_test_files"]) + "\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(R) + 1, "json")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]))
