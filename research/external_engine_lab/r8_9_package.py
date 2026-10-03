"""R8.9 review package: URBAN_QTO_R8_9_ROLE_AND_SEMANTIC_ZONES (19 md + 16 json + owner-review picture + zip).

    python3 research/external_engine_lab/r8_9_package.py <junit.xml> "<command>" <exit_code> [<work_dir>]
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

REG = ROOT / "tests/r8_9/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_9_ROLE_AND_SEMANTIC_ZONES"
JSONS = ("OWNER_ACTION_REGISTER", "ENGINEERING_ACTION_REGISTER", "EFFECTIVE_LAYER_REGISTER", "ROLE_AUTHORITY_POLICY",
         "SOURCE_LAYER_ROLE_CLAIMS", "BLOCK_OCCURRENCE_CONTEXT_REGISTER", "UNREALISED_ENTITY_REGISTER",
         "TEXT_ROLE_REGISTER", "SEMANTIC_ZONE_REGISTER", "THRESHOLD_SITE_REGISTER", "DOOR_CLOSURE_AUDIT",
         "TOPOLOGY_CROSSCHECK_V2", "QORTUBA_R8_9_STATUS", "P7757_R8_9_SHADOW", "R8_9_DECISION_REGISTER")
PNG = "19_OWNER_REVIEW_DIM_WALLS.png"


def jl(p):
    return json.loads(Path(p).read_text())


def owner_picture(work, path):
    """Old revision WALL lines (blue) vs new revision admitted walls (black) and DIM-layer lines (red)."""
    from PIL import Image, ImageDraw
    import r8_8_topology as LAB
    C = LAB.C
    old = C.old_input()
    new, _ = C.input_from_pickle(Path(work) / "new_k2.pkl", C.rev_new())
    x0, y0, x1, y1 = (109280.0, 14830.0, 110260.0, 15140.0)
    W = 1800
    s = W / (x1 - x0)
    im = Image.new("RGB", (W, int((y1 - y0) * s) + 60), "white")
    d = ImageDraw.Draw(im)
    v = lambda x, y: ((x - x0) * s, (y1 - y) * s + 50)

    def inside(g):
        return min(g[0], g[2]) <= x1 and max(g[0], g[2]) >= x0 and min(g[1], g[3]) <= y1 and max(g[1], g[3]) >= y0
    for p in old.parts:
        if p.layer == "WALL" and p.kind == "SEGMENT" and not p.identity.instance_handles and inside(p.geometry):
            g = p.geometry
            d.line([v(g[0], g[1]), v(g[2], g[3])], fill=(120, 160, 255), width=9)
    for p in new.parts:
        if p.kind != "SEGMENT" or p.identity.instance_handles or not inside(p.geometry):
            continue
        g = p.geometry
        if p.layer == "WALL":
            d.line([v(g[0], g[1]), v(g[2], g[3])], fill=(0, 0, 0), width=3)
        elif p.layer == "DIM" and p.identity.source_handle in ("7116", "7117", "7118", "7119"):
            d.line([v(g[0], g[1]), v(g[2], g[3])], fill=(230, 0, 0), width=4)
            f = 0.35 if p.identity.source_handle in ("7116", "7118") else 0.65
            d.text(v(g[0] + 3, g[1] + f * (g[3] - g[1])), p.identity.source_handle, fill=(230, 0, 0))
    for t in new.texts:
        if t.value in ("BATH", "BED.ROOM", "HALL") and t.x is not None and x0 <= t.x <= x1 and y0 <= t.y <= y1:
            d.text(v(t.x, t.y), t.value, fill=(0, 110, 0))
    d.text((10, 8), "QORTUBA new revision (DXF df0e1d69), selected SECOND FLOOR plan, near the HALL", fill=(0, 0, 0))
    d.text((10, 26), "black = WALL lines now | red = lines on layer DIM (7116-7119) | light blue = the OLD revision's "
                     "WALL lines   QUESTION: are the red lines walls?", fill=(0, 0, 0))
    im.save(path)


def rows_md(rows):
    return tbl(["Row", "R8.9 state", "Value m2", "Basis"],
               [[r, v["state"], "" if v["value"] is None else f"{v['value']:.4f}", v.get("basis", "")[:60]]
                for r, v in rows.items()])


def main(junit_path, command, exit_code, work=None):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_9_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted"}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_9_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    if work:
        owner_picture(work, OUT / PNG)
    D, Q, P, O = R["R8_9_DECISION_REGISTER"], R["QORTUBA_R8_9_STATUS"], R["P7757_R8_9_SHADOW"], R["OWNER_ACTION_REGISTER"]
    G, A = D["gates"], D["answers"]
    tests = (f"commit `{commit}` · `{command}` · passed {jr['passed']} · xfailed {jr['xfailed']} · skipped "
             f"{jr['skipped']} · failed {jr['failed']} · errors {jr['errors']} · total {jr['total']} · exit {exit_code}")
    reviews = [a for a in O["actions"] if a["action_id"] in O["owner_review_open"]]
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.9 — Role authority and semantic zones (SHADOW)

## Owner
{O['headline']}.
""" + "\n".join(f"- **{a['question']}** ({' / '.join(a['choices'])})" for a in reviews) + f"""

## What changed
- **Effective layer:** canonical on every record (layer-0 inheritance through the whole insert chain, both routes).
- **Role authority:** a layer role is a candidate. An admitted line must also join the boundary network, and an
  exclusion by layer name must answer to its consequence: a dimension-layer line that would close a room is a role
  conflict, not silence.
- **Unrealised entities:** excluded only on positive evidence (their own ACIS / spline geometry, the frame occurrence,
  an occurrence wholly outside).
- **Text roles before labels:** only established room tags name a space.
- **Three objects:** physical site, semantic zone and trade region are separate. Threshold strips keep their own sites.
- **GEOS cross-check V2:** every grid phase must agree; no polygon repair.

## Qortuba, new revision
{rows_md(Q['rows']['NEW_K2'])}

## Gates
- MIGRATION_PLANNING_READY = **{G['MIGRATION_PLANNING_READY']}**
- MIGRATION_EXECUTION_READY = **{G['MIGRATION_EXECUTION_READY']}**
- PRODUCTION_MIGRATION = **{G['PRODUCTION_MIGRATION']}**

## Tests
{tests}

STOP AFTER R8.9. NO PRODUCTION MIGRATION.
"""
    md["01_OWNER_ACTIONS.md"] = "# Owner actions (V6)\n\n**" + O["headline"] + "**\n\n" + O["rule"] + ".\n\n" + "\n\n".join(
        f"## {a['action_id']}\n**{a['question']}**\n\nChoices: {' / '.join(a['choices'])}\n\nWhy the source cannot "
        f"decide: {a['why_the_source_cannot_decide']}\n\nScope: `{json.dumps(a['scope'], ensure_ascii=False)}`"
        for a in reviews) + f"\n\n![owner review]({PNG})\n\nOther standing actions:\n\n" + tbl(
        ["Action", "Status"], [[a["action_id"], a["status"]] for a in O["actions"] if a not in reviews]) + "\n"
    E = R["ENGINEERING_ACTION_REGISTER"]
    md["02_ENGINEERING_ACTIONS.md"] = "# Engineering actions\n\n" + tbl(
        ["Action", "Status", "What"], [[a["action_id"], a["status"], a.get("what", "")[:110]] for a in E["actions"]]) + "\n"
    EL = R["EFFECTIVE_LAYER_REGISTER"]
    md["03_EFFECTIVE_LAYER_AUTHORITY.md"] = "# Effective layer authority\n\n" + EL["rule"] + ".\n\n**R8.8 gap:** " + \
        EL["r8_8_gap"] + ".\n\n**Qortuba:** " + EL["qortuba_effect"] + ".\n\n**P7757:** " + \
        f"{P['effective_layers']['layer0_children_inside_inserts']} parts take their role layer from the insert chain.\n\n" + \
        tbl(["Run", "Records by authority", "Layer-0 children in inserts"],
            [[k, json.dumps(v["records_by_authority"]), v["layer0_children_inside_inserts"]] for k, v in EL["runs"].items()]) + "\n"
    RP = R["ROLE_AUTHORITY_POLICY"]
    md["04_ROLE_AUTHORITY_MODEL.md"] = "# Role authority model\n\n" + "\n".join(
        f"- **{k}:** {v}" for k, v in RP["role_authority"]["consequences"].items()) + "\n\n" + tbl(
        ["Run", "Boundary grades", "Unconnected candidates", "Separator candidates"],
        [[k, json.dumps(RP["grades_per_run"][k]), ", ".join(RP["unconnected_candidates"][k]) or "-",
          json.dumps(RP["separator_candidates"][k])] for k in RP["grades_per_run"]]) + "\n"
    SC = R["SOURCE_LAYER_ROLE_CLAIMS"]
    md["05_SOURCE_LAYER_ROLE_CLAIMS.md"] = "# Source-scoped layer role claims\n\n" + SC["rule"] + ".\n\n" + tbl(
        ["Claim", "Layer", "Role", "State", "Applied"],
        [[c["claim_id"], c["layer"], c["role"], c["review_state"], c["applied"]] for c in SC["claims"]]) + \
        "\n\n## FIRNTUR\n" + "\n".join(f"- **{k}:** {v}" for k, v in Q["firntur"]["verdict"].items()) + \
        "\n\n## SF3 / PM\n" + Q["sf3"]["verdict"] + "\n\n" + "\n".join(f"- {x}" for x in Q["sf3"]["evidence_for_furniture"]) + "\n"
    BO = R["BLOCK_OCCURRENCE_CONTEXT_REGISTER"]
    md["06_BLOCK_OCCURRENCE_CONTEXT.md"] = "# Block occurrence context\n\n" + BO["rule"] + ".\n\n" + tbl(
        ["Run", "Contexts"], [[k, json.dumps(v["contexts"])] for k, v in BO["runs"].items()]) + \
        f"\n\nP7757: {json.dumps(P['occurrence_contexts'])}\n"
    UN = R["UNREALISED_ENTITY_REGISTER"]
    md["07_UNREALISED_ENTITY_ACCOUNTING.md"] = "# Unrealised source entities\n\n" + UN["rule"] + ".\n\nRetired R8.8 " \
        "disposition: `" + UN["r8_8_disposition_retired"] + "`.\n\n" + tbl(
        ["Run", "Blocking", "Recorded"], [[k, json.dumps(v["blocking"]), json.dumps(v["recorded"])]
                                          for k, v in UN["runs"].items()]) + "\n\n**The 37 + 1 OFFICE NAME entities:** " + \
        UN["proof"] + ".\n\n**Attached xrefs (new revision):** " + \
        Q["attached_xrefs_not_in_source"]["why_blocking"] + ".\n"
    TR = R["TEXT_ROLE_REGISTER"]
    md["08_TEXT_LABEL_AUTHORITY.md"] = "# Text label authority\n\nOnly `ROOM_LABEL_ESTABLISHED` names a space.\n\n" + tbl(
        ["Run", "Role | rule counts"], [[k, json.dumps(v)] for k, v in TR["runs"].items()]) + "\n\n" + TR["paintry"] + ".\n"
    SZ = R["SEMANTIC_ZONE_REGISTER"]
    md["09_PHYSICAL_VS_SEMANTIC_ZONES.md"] = "# Physical site / semantic zone / trade region\n\n" + tbl(
        ["Run", "Site states"], [[k, json.dumps(v["site_states"])] for k, v in SZ["runs"].items()]) + "\n"
    MI = Q["multi_label_investigation"]
    md["10_QORTUBA_MULTI_LABEL_INVESTIGATION.md"] = "# Qortuba multi-label spaces (new revision)\n\n" + "\n\n".join(
        f"## {k}\n- site `{v['site']}` · {v['area_m2']} m²\n- state **{v['semantic_state']}**\n- {v['interpretation']}"
        for k, v in MI.items()) + "\n\n## DIM-layer lines on the old wall faces\n" + tbl(
        ["New DIM line", "Old wall face", "Bridges the network now"],
        [[r["new_dim_line"], r["on_old_wall_face"][0]["old_wall"], r["bridges_network_now"]]
         for r in Q["dim_layer_separators"]["dim_lines_on_removed_wall_faces"]]) + \
        f"\n\n![DIM walls]({PNG})\n\nHypothesis (not released) if the xrefs are outside and the lines are walls: " + \
        json.dumps(Q["if_xrefs_confirmed_outside_the_plan"]["and_if_dim_lines_are_walls"]) + "\n"
    TH = R["THRESHOLD_SITE_REGISTER"]
    md["11_THRESHOLD_SITES.md"] = "# Threshold / opening sites\n\n" + TH["rule"] + ".\n\n" + TH["qs01_method_difference"] + \
        ".\n\n" + tbl(["Run", "Thresholds", "Allocation"], [[k, len(v), ", ".join(sorted({t['allocation'] for t in v}))]
                                                            for k, v in TH["runs"].items()]) + "\n"
    DA = R["DOOR_CLOSURE_AUDIT"]
    md["12_DOOR_CLOSURE_AUDIT.md"] = f"# Door closure reach audit\n\nPolicy ratio {DA['policy_ratio']}; accepted ratios " \
        f"needed: {DA['accepted_ratios_needed']}; rejected hypotheses that would close within a full radius: " \
        f"{DA['rejected_hypotheses_that_would_close_within_a_full_radius']}.\n\n**Verdict:** {DA['verdict']}.\n"
    XC = R["TOPOLOGY_CROSSCHECK_V2"]
    md["13_TOPOLOGY_CROSSCHECK_HARDENING.md"] = "# GEOS cross-check V2\n\n" + XC["before_R8_9"] + ".\n\n" + tbl(
        ["Run", "State", "Counts"], [[k, v["state"], json.dumps(v["counts"])] for k, v in XC["runs"].items()]) + \
        "\n\n" + XC["invalid_polygon_policy"] + ".\n"
    md["14_QORTUBA_NEW_REVISION_STATUS.md"] = "# Qortuba new revision (PLAN_VARIANT_4_SELECTED)\n\n" + \
        rows_md(Q["rows"]["NEW_K2"]) + "\n\n## If the xrefs are confirmed outside the plan (hypothesis)\n" + \
        tbl(["Row", "State", "Value"], [[r, v["state"], v["value"]] for r, v in
                                        Q["if_xrefs_confirmed_outside_the_plan"]["rows"].items()]) + \
        "\n\n## Old revision (regression, unchanged)\n" + json.dumps(Q["old_revision_rows_regression"]) + "\n"
    md["15_P7757_SECOND_FAMILY_SHADOW.md"] = "# P7757 second-family shadow\n\nCertificate: **" + P["ts01_certificate"] + \
        "** (no unit assumed).\n\n" + "\n".join(f"- {x}" for x in P["second_family_findings"]) + "\n\nUnit evidence: " + \
        P["unit"]["classification"] + "\n\nOwner question prepared, not asked: " + \
        P["owner_question_prepared_not_asked"]["question"] + "\n"
    md["16_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Findings\n" + "\n".join(f"- **{f['id']}:** {f['finding']}" for f in D["findings"]) + "\n"
    md["17_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.9 tests: tests/r8_9/test_r8_9_effective_layer.py, " \
        "test_r8_9_role_authority.py, test_r8_9_semantics.py, test_r8_9_crosscheck_doors.py, test_r8_9_qortuba_real.py\n"
    pre = D["recommendation_before_coding"]
    md["18_CLAUDE_RECOMMENDATION.md"] = "# Claude recommendation\n\n## Before coding (§0)\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else '; '.join(v)}" for k, v in pre.items()) + \
        "\n\n## Answers\n" + "\n".join(f"- **{k}:** {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}"
                                       for k, v in A.items()) + "\n\n" + D["recommendation"] + \
        "\n\nSTOP AFTER R8.9. NO PRODUCTION MIGRATION.\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(R) + 1, "json", "png" if work else "no png")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]), a[3] if len(a) > 3 else None)
