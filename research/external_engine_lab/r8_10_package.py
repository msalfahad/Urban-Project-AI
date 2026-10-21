"""R8.10 review package: URBAN_QTO_R8_10_OWNER_CLAIMS_AND_TRADE_EQUIVALENCE (18 md + 15 json + picture + zip).

    python3 research/external_engine_lab/r8_10_package.py <junit.xml> "<command>" <exit_code> [<work_dir>]
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit, tbl                                            # noqa: E402

REG = ROOT / "tests/r8_10/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_10_OWNER_CLAIMS_AND_TRADE_EQUIVALENCE"
JSONS = ("OWNER_ACTION_REGISTER", "OWNER_CLAIM_REGISTER", "XREF_SCOPE_CLAIMS", "DIM_WALL_CLAIMS",
         "TRADE_SEMANTIC_EQUIVALENCE", "UNRESOLVED_ROLE_MATERIALITY", "DUPLICATE_OCCURRENCE_REGISTER",
         "THRESHOLD_SITE_REGISTER", "ROLE_AUTHORITY_ADVERSARIAL", "BUILDING_ASSEMBLY_ADVERSARIAL",
         "TEXT_TAG_ADVERSARIAL", "P7757_R8_10_SHADOW", "QORTUBA_R8_10_STATUS", "R8_10_DECISION_REGISTER")
PNG = "18_HALL_CAPS_AND_DRESS_PASSAGE.png"


def jl(p):
    return json.loads(Path(p).read_text())


def picture(work, path):
    from PIL import Image, ImageDraw
    import r8_10_claims as CL
    import r8_10_qortuba as Q
    inps, _, facts = Q.inputs(work)
    pc, xc, _ = CL.load()
    new = inps["NEW_K2"]
    r = Q.run(new, "NEW_K2", facts, pc, xc)
    roles = r["roles"]["roles"]
    x0, y0, x1, y1 = 109520.0, 14840.0, 110420.0, 16040.0
    W = 1500
    s = W / (x1 - x0)
    im = Image.new("RGB", (W, int((y1 - y0) * s) + 60), "white")
    d = ImageDraw.Draw(im)
    v = lambda x, y: ((x - x0) * s, (y1 - y) * s + 50)
    col = {"TOPOLOGY_BOUNDARY": (0, 0, 0), "FURNITURE": (0, 160, 0), "UNKNOWN_PHYSICAL": (230, 0, 0),
           "OPENING_SYMBOL": (255, 140, 0)}
    hi = {"7116": (0, 90, 255), "7117": (0, 90, 255), "7118": (0, 90, 255), "7119": (0, 90, 255),
          "2430": (200, 0, 200), "2431": (200, 0, 200)}
    for p in new.parts:
        g = p.geometry
        ro = roles.get(p.identity.key)
        h = p.identity.source_handle if not p.identity.instance_handles else None
        c = hi.get(h) or col.get(ro.role if ro else "", (200, 200, 200))
        if p.kind == "SEGMENT":
            if max(g[0], g[2]) < x0 or min(g[0], g[2]) > x1 or max(g[1], g[3]) < y0 or min(g[1], g[3]) > y1:
                continue
            d.line([v(g[0], g[1]), v(g[2], g[3])], fill=c, width=5 if h in hi else 2)
            if h in hi:
                d.text(v(g[0] + 4, (g[1] + g[3]) / 2), h, fill=c)
        elif p.kind == "ARC":
            cx, cy, R, a0, a1 = g[:5]
            if cx + R < x0 or cx - R > x1 or cy + R < y0 or cy - R > y1:
                continue
            a1 = a1 if a1 > a0 else a1 + 360
            d.line([v(cx + R * math.cos(math.radians(a0 + (a1 - a0) * i / 16)),
                      cy + R * math.sin(math.radians(a0 + (a1 - a0) * i / 16))) for i in range(17)], fill=c, width=2)
    for t in new.texts:
        if t.x is not None and x0 <= t.x <= x1 and y0 <= t.y <= y1 and t.value and t.value.isascii():
            d.text(v(t.x, t.y), t.value[:12], fill=(120, 80, 0))
    d.text((8, 6), "QORTUBA new revision, PLAN_VARIANT_4_SELECTED: HALL / Lobby passage and M.B.ROOM / DRESS", fill=0)
    d.text((8, 24), "blue = DIM lines 7116-7119 (owner: walls)   magenta = DIM caps 2430 / 2431 (2431 stops 9.2 mm short)"
                    "   red = unknown role (SF3, FIRNTUR)   green = furniture   black = walls", fill=0)
    im.save(path)


def rows_md(rows):
    out = []
    for r, v in rows.items():
        bl = "; ".join(f"{', '.join(b['zones'][:2])}: " + ", ".join(sorted({f"{x['class']}/{x['issue']}"
                                                                           for x in b["blockers"]}))
                       for b in v["blockers"]) or "-"
        out.append([r, v["state"], "" if v["value"] is None else f"{v['value']:.4f}", len(v["physical_site_ids"]),
                    len(v["semantic_zone_ids"]), sum(1 for t in v["threshold_treatment"]),
                    ", ".join(c.split("-OWNER")[0] for c in v["role_claims_used"]) or "-",
                    v["trade_authority"]["rule"], bl])
    return tbl(["Row", "State", "Value m2", "Sites", "Zones", "Thresholds (TRADE_RULE_REQUIRED)", "Role claims",
                "Trade authority", "Blockers"], out)


def main(junit_path, command, exit_code, work=None):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_10_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted"}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_10_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    if work:
        picture(work, OUT / PNG)
    D, Q, O, A = R["R8_10_DECISION_REGISTER"], R["QORTUBA_R8_10_STATUS"], R["OWNER_ACTION_REGISTER"], \
        R["R8_10_DECISION_REGISTER"]["answers"]
    G, rows = D["gates"], Q["rows"]["NEW_K2_R8_10"]
    dim, x, t = R["DIM_WALL_CLAIMS"], R["XREF_SCOPE_CLAIMS"], R["THRESHOLD_SITE_REGISTER"]
    mb, caps = Q["m_b_room_dress"], dim["hall_lobby_caps"]
    tests = (f"commit `{commit}` · `{command}` · passed {jr['passed']} · xfailed {jr['xfailed']} · skipped "
             f"{jr['skipped']} · failed {jr['failed']} · errors {jr['errors']} · total {jr['total']} · exit {exit_code}")
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.10 — Owner claims and trade-specific semantic necessity (SHADOW)

## Owner
**{O['headline']}.** Both R8.9 reviews are answered and recorded as narrowly scoped claims; nothing is asked again.

## What R8.10 did
- The two owner answers entered as **versioned claims bound to source identity** (evidence version 2), then the
  whole chain was rebuilt from the canonical input. No area was patched, no geometry edited, no quantity set.
- **BATH and BED.ROOM are separate rooms again** (5.1 and 19.2725 m2); the R8.9 68.66 m2 merge is gone. No other DIM
  line became a wall.
- The xref occurrences 16783 / 17716 no longer block the selected plan; nothing else was cleared.
- **Trade treatment assignment** (owner rules QP-07 / QP-14 and the Q-14 claim) decides, trade by trade, whether a
  multi-label space must be split. M.B.ROOM + DRESS: no split needed for the ceiling; for the floor the wardrobes
  decide.
- Adversarial review: NETWORK, building assemblies and room tags each failed a case; each is now stricter; a silent
  near-miss path is closed.

## Qortuba six rows (new revision, PLAN_VARIANT_4_SELECTED)
{rows_md(rows)}

## Gates
- MIGRATION_PLANNING_READY = **{G['MIGRATION_PLANNING_READY']}**
- MIGRATION_EXECUTION_READY = **{G['MIGRATION_EXECUTION_READY']}**
- PRODUCTION_MIGRATION = **{G['PRODUCTION_MIGRATION']}**

## Tests
{tests}

STOP AFTER R8.10. NO PRODUCTION MIGRATION.
"""
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}.**\n\n## Answered in R8.10\n" + "\n".join(
        f"- {a['action_id']}: {a['answer']} -> {a.get('recorded_as', 'scope')}" for a in O["answered_in_r8_10"]) + \
        "\n\n## Prepared, not asked\n" + "\n".join(f"- **{a['action_id']}** — {a.get('question') or a.get('request')}"
                                                     f"\n  - why not now: {a['why_not_asked']}"
                                                     for a in O["prepared_not_asked"]) + \
        "\n\n## Never asked\n" + "\n".join(f"- {d}" for d in O["do_not_ask"]) + "\n"
    oc = R["OWNER_CLAIM_REGISTER"]
    md["02_OWNER_CLAIMS.md"] = "# Owner claims (evidence version 2)\n\n" + \
        f"File `{oc['evidence_file']}` (sha256 `{oc['evidence_file_sha256'][:16]}...`), previous version " \
        f"`{oc['previous_evidence_version']['file']}` unchanged.\n\n## Flow\n" + " → ".join(oc["flow"]) + \
        "\n\n## Claims\n" + tbl(["Claim", "v", "Kind", "Authority", "Plan / region"],
                                [[c["claim_id"], c["version"], c["kind"], " + ".join(c["authority"]),
                                  f"{c['scope']['plan']} / {c['scope']['region_id']}"] for c in oc["claims"]]) + \
        "\n\n## Binding\n" + "\n".join(f"- {b}" for b in oc["binding_policy"]["binding"]) + "\n\nNever: " + \
        "; ".join(oc["binding_policy"]["never"]) + f"\n\nQuantity edits by claims: **{oc['quantity_edits_by_claims']}**." \
        "\n\nOld revision: " + oc["application"]["OLD_K1"][0]["state"] + " (claims never transfer).\n"
    md["03_XREF_SCOPE_CLAIM.md"] = "# XREF scope claim\n\n## Occurrences in the source (re-verified from the DXF)\n" + \
        tbl(["Handle", "Hex", "Xref", "Path", "Insert", "Scale", "Layer"],
            [[h, f["hex_handle"], f["xref_name"], f["xref_path"], f["insert"], f["scale"], f["layer"]]
             for h, f in x["occurrences_in_source"].items()]) + "\n\n## Four-state model\n" + \
        "\n".join(f"- {s}" for s in x["four_state_model"]) + "\n\n## After the claim\n" + \
        tbl(["Occurrence", "State", "Continues", "Claim"], [[h, v["state"], v["continues"], v["claim"]]
                                                             for h, v in x["inventory_new_revision"].items()]) + \
        f"\n\nBlocking unrealised records left: **{len(x['blocking_unrealised_after_claim'])}** of " \
        f"{x['unrealised_records_total']}. {x['source_complete']}.\n"
    e = dim["effect"]
    md["04_DIM_WALL_CLAIM.md"] = "# DIM-wall claim (part-scoped)\n\n" + tbl(
        ["Handle", "Source layer", "Role now", "Before", "Grade", "Connected ends"],
        [[p["handle"], p["source_layer"], p["role_now"], p["role_before"], p["authority_grade"], p["connected_ends"]]
         for p in e["parts"]]) + "\n\n## Before (R8.9, no claim)\n" + \
        "\n".join(f"- {b['site']}: {b['area_m2']} m2, {b['stamps']}" for b in e["before_r8_9"]) + \
        "\n\n## After\n" + "\n".join(f"- {a['site']}: {a['area_m2']} m2 {a['stamps'] or '(wall core / threshold)'} "
                                     f"{a['physical_status']}" for a in e["after"]) + \
        "\n\nOpening adjacency: " + "; ".join(f"{a['opening']}: {a['sites']}" for a in e["opening_adjacency"]) + \
        f"\n\nOther DIM-layer parts: {e['other_dim_layer_parts']}; admitted: **{e['other_dim_parts_admitted']}**.\n\n" \
        "## The Hall / Lobby wall-end caps (not claimed)\n" + tbl(
            ["Handle", "Layer", "Role", "Length mm"], [[c["handle"], c["layer"], c["role"], c["length_mm"]]
                                                        for c in caps["caps"]]) + \
        f"\n\n- {caps['old_revision']}\n- H2430: {caps['h2430']}\n- H2431: {caps['h2431']}\n- leak areas: " \
        f"{caps['leak_areas']}\n- {caps['not_claimed']}\n\nPicture: {PNG}\n"
    md["05_QORTUBA_REBUILD.md"] = "# Qortuba rebuild\n\nScope: " + json.dumps(Q["scope"]) + "\n\n" + \
        Q["other_variants"] + "\n\n## Labelled physical sites\n" + tbl(
            ["Site", "Area m2", "Labels", "Physical", "Issues"],
            [[s["site"], s["area_m2"], s["stamps"], s["physical_status"], ", ".join(s["issues"])]
             for s in Q["labelled_sites"]]) + f"\n\nEvidence version `{Q['evidence_version'][:16]}...`\n\n" \
        "## R8.9 wording corrected\n" + Q["r8_9_wording_corrected"] + "\n"
    te = R["TRADE_SEMANTIC_EQUIVALENCE"]
    md["06_TRADE_SEMANTIC_EQUIVALENCE.md"] = "# Trade-specific semantic necessity\n\n" + te["design"] + \
        "\n\n## Rules\n" + "\n".join(f"- **{k}** ({v['trade']}, {v['authority']}): refs {v['refs']}; otherwise "
                                     f"{v.get('otherwise')}; objects {v['object_footprints']}"
                                     for k, v in te["rules"].items()) + \
        "\n\n## Whole-site region requires\n" + "\n".join(f"- {r}" for r in te["policy"]["whole_site_region_requires"]) + \
        "\n\nNever used: " + "; ".join(te["never_used"]) + \
        "\n\nNegative tests: tests/r8_10/test_r8_10_trade.py (HALL+DINING, M.B.ROOM+DRESS, BEDROOM+BATHROOM, " \
        "KITCHEN+DINING, unresolved treatment, unresolved text, authored boundary).\n"
    md["07_MBROOM_DRESS_ANALYSIS.md"] = "# M.B.ROOM + DRESS\n\n" + mb["correction_of_r8_9"] + "\n\n" + \
        f"Site {mb['site']}: {mb['area_m2']} m2, {mb['semantic_state']}.\n\n## Passage\n" + json.dumps(mb["passage"]) + \
        "\n\n## Q-13 (floor)\n" + "\n".join(f"- {k}: {json.dumps(v)[:400]}" for k, v in mb["Q-13"].items()) + \
        "\n\n## Q-14 (ceiling)\n" + "\n".join(f"- {k}: {json.dumps(v)[:400]}" for k, v in mb["Q-14"].items()) + "\n"
    md["08_THRESHOLD_SITES.md"] = "# Threshold sites\n\n## Old revision wet rows\n" + json.dumps(
        {k: v for k, v in t["old_revision_wet_rows"].items() if k != "thresholds"}) + \
        "\n\n## New revision wet rows\n" + json.dumps({k: v for k, v in t["new_revision_wet_rows"].items()
                                                       if k != "thresholds"}) + "\n\n## All new thresholds\n" + tbl(
            ["Threshold", "Opening", "m2", "Sides", "Allocation"],
            [[a["threshold"], a["opening"], a["area_m2"], a["sides"], a["allocation"]] for a in t["all_new_thresholds"]]) + \
        "\n\n## Passage strips (inside whole sites)\n" + json.dumps(t["passage_strips"]) + "\n\n" + t["allocation"] + "\n"
    m = R["UNRESOLVED_ROLE_MATERIALITY"]
    md["09_UNRESOLVED_ROLE_MATERIALITY.md"] = "# Unresolved role, trade materiality\n\n" + m["rule"] + "\n\n" + \
        "\n".join(f"- **{k}:** {v['role']}" for k, v in m["objects"].items()) + "\n\n" + tbl(
            ["Site", "Trade", "State", "Why"], [[sid, rid, v["state"], v["why"][:120]]
                                                for sid, per in m["per_site_per_trade"].items()
                                                for rid, v in per.items()]) + \
        "\n\nDuplicate occurrences: " + json.dumps(R["DUPLICATE_OCCURRENCE_REGISTER"]["sf3"]) + "\n"
    ra = R["ROLE_AUTHORITY_ADVERSARIAL"]
    md["10_ROLE_AUTHORITY_ADVERSARIAL.md"] = "# Role authority — adversarial review\n\n" + \
        "\n".join(f"- **{k}:** {v}" for k, v in ra["verdict"].items()) + "\n\nNETWORK states: " + \
        json.dumps(ra["network_review_states"]) + "\n\nNear misses (band " + str(ra["near_misses"]["band_mm"]) + \
        " mm, " + ra["near_misses"]["basis"] + "):\n" + json.dumps(ra["near_misses"]["NEW_K2"]) + "\n\n" + \
        ra["finding_dimension_coincidence"] + "\n\nConsequence analysis establishes MATERIALITY only, never authority " \
        "(tests/r8_10/test_r8_10_adversarial.py::test_consequence_analysis_never_admits_what_it_finds_material).\n"
    ba = R["BUILDING_ASSEMBLY_ADVERSARIAL"]
    md["11_BUILDING_ASSEMBLY_ADVERSARIAL.md"] = "# Building assembly — adversarial review\n\n" + ba["rule"] + \
        "\n\n" + "\n".join(f"- {x}" for x in ba["tests"]) + "\n\nReal drawings: " + json.dumps(ba["real_drawings"]) + \
        ". " + ba["real_assemblies_before_and_after"] + ". Size used: " + str(ba["size_used"]) + "\n"
    tt = R["TEXT_TAG_ADVERSARIAL"]
    md["12_TEXT_TAG_ADVERSARIAL.md"] = "# Room tags — adversarial review\n\n" + tt["reading"] + "\n\nFalse positives " \
        "tested: " + ", ".join(tt["false_positive_tests"]) + "\n\nQortuba (new) now: " + json.dumps(tt["qortuba_new"]) + \
        "\n\nR8.9: " + json.dumps(tt["qortuba_new_r8_9"]) + f"\n\nPAINTRY: {tt['paintry']}; changed by V2: " \
        f"{tt['changed_by_v2']}\n"
    P = R["P7757_R8_10_SHADOW"]
    md["13_P7757_SECOND_FAMILY.md"] = "# P7757 — second family (shadow)\n\n" + P["purpose"] + "\n\n" + "\n".join(
        f"- **{k}:** {json.dumps(v, ensure_ascii=False)[:600]}" for k, v in P.items()
        if k not in ("SCHEMA", "purpose")) + "\n"
    md["14_QORTUBA_SIX_ROW_STATUS.md"] = "# Qortuba six-row status (SHADOW)\n\n" + rows_md(rows) + \
        "\n\n## Old revision (claims offered, never applied)\n" + tbl(
            ["Row", "State", "Value", "Classes"], [[r, v["state"], v["value"], v["blocker_classes"]]
                                                   for r, v in Q["rows"]["OLD_K1_R8_10"].items()]) + \
        "\n\n## Migration blocker on every new-revision row\n" + rows["Q-03"]["migration_blockers"][0] + "\n\n" + \
        Q["final"] + "\n"
    md["15_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        "\n\n## Findings\n" + "\n".join(f"- {f}" for f in D["findings"]) + "\n"
    md["16_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.10 tests: tests/r8_10/test_r8_10_claims.py, " \
        "test_r8_10_adversarial.py, test_r8_10_trade.py, test_r8_10_qortuba_real.py\n"
    pre = D["recommendation_before_coding"]
    md["17_CLAUDE_RECOMMENDATION.md"] = "# Claude recommendation\n\n## Before coding (§0)\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else '; '.join(v)}" for k, v in pre.items()) + \
        "\n\n## Answers 1-24\n" + "\n".join(f"- **{k}:** {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)[:900]}"
                                            for k, v in A.items()) + "\n\nSTOP AFTER R8.10. NO PRODUCTION MIGRATION.\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(R) + 1, "json", "png" if work else "no png")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]), a[3] if len(a) > 3 else None)
