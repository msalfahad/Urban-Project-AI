"""R8.11 review package: URBAN_QTO_R8_11_WALL_BANDS_AND_RUN_MANIFEST (19 md + 15 json + picture + zip).

    python3 research/external_engine_lab/r8_11_package.py <junit.xml> "<command>" <exit_code> [<work_dir>]
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

REG = ROOT / "tests/r8_11/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_11_WALL_BANDS_AND_RUN_MANIFEST"
JSONS = ("OWNER_ACTION_REGISTER", "ENGINEERING_ACTION_REGISTER", "WALL_BAND_REGISTER", "TOPOLOGY_CLOSURE_REGISTER",
         "NEAR_MISS_REGISTER", "OPEN_PASSAGE_SITE_REGISTER", "THRESHOLD_SITE_REGISTER", "OBJECT_FOOTPRINT_POLICY",
         "SEMANTIC_CLASS_REGISTER", "QTO_RUN_MANIFEST", "Q13_STATUS", "Q14_STATUS", "QORTUBA_R8_11_STATUS",
         "R8_11_DECISION_REGISTER")
PNG = "19_HALL_LOBBY_BANDS_AND_CLOSURE.png"


def jl(p):
    return json.loads(Path(p).read_text())


def picture(work, path):
    from PIL import Image, ImageDraw
    import r8_10_claims as CL
    import r8_11_qortuba as Q
    from engine.source import topology_closures as TC
    inps, _, facts = Q.Q10.inputs(work)
    pc, xc, _ = CL.load()
    new = inps["NEW_K2"]
    r = Q.run(new, "NEW_K2", facts, pc, xc, TC.POLICY_ID)
    roles = r["roles"]["roles"]
    x0, y0, x1, y1 = 109280.0, 14840.0, 110420.0, 16060.0
    W = 1600
    s = W / (x1 - x0)
    im = Image.new("RGB", (W, int((y1 - y0) * s) + 70), "white")
    d = ImageDraw.Draw(im)
    v = lambda x, y: ((x - x0) * s, (y1 - y) * s + 60)
    faces = {Q.handle(x) for b in r["wall_bands"]["bands"] if b["state"] == "WALL_BAND_ESTABLISHED"
             for x in (b["face_a"], b["face_b"])}
    for p_ in r["passages"]:
        d.polygon([v(*q) for q in p_["polygon"]], fill=(255, 235, 150))
    hi = {"2430": (200, 0, 200), "2431": (200, 0, 200), "470": (255, 0, 0), "471": (255, 0, 0), "477": (255, 0, 0)}
    for p in new.parts:
        g = p.geometry
        ro = roles.get(p.identity.key)
        h = p.identity.source_handle if not p.identity.instance_handles else None
        if p.kind == "SEGMENT":
            if max(g[0], g[2]) < x0 or min(g[0], g[2]) > x1 or max(g[1], g[3]) < y0 or min(g[1], g[3]) > y1:
                continue
            c = hi.get(h) or ((0, 90, 255) if h in faces else (0, 0, 0) if ro and ro.role == "TOPOLOGY_BOUNDARY"
                              else (190, 190, 190))
            d.line([v(g[0], g[1]), v(g[2], g[3])], fill=c, width=5 if h in hi else 2)
            if h in hi:
                d.text(v(g[0] + 3, (g[1] + g[3]) / 2 + 6), h, fill=c)
        elif p.kind == "ARC":
            cx, cy, R, a0, a1 = g[:5]
            if cx + R < x0 or cx - R > x1 or cy + R < y0 or cy - R > y1:
                continue
            a1 = a1 if a1 > a0 else a1 + 360
            d.line([v(cx + R * math.cos(math.radians(a0 + (a1 - a0) * i / 16)),
                      cy + R * math.sin(math.radians(a0 + (a1 - a0) * i / 16))) for i in range(17)],
                   fill=(190, 190, 190), width=1)
    for c in r["topology_closures"]["closures"]:
        g = c["geometry"]
        col = (0, 170, 0) if c["release"] == TC.AUTHORISED_FOR_SHADOW else (0, 200, 200)
        d.line([v(g[0], g[1]), v(g[2], g[3])], fill=col, width=7)
    for t in new.texts:
        if t.x is not None and x0 <= t.x <= x1 and y0 <= t.y <= y1 and t.value and t.value.isascii():
            d.text(v(t.x, t.y), t.value[:12], fill=(120, 80, 0))
    d.text((8, 6), "QORTUBA new revision - R8.11 wall bands (blue faces), zero-material closures (green = "
                   "AUTHORISED_FOR_SHADOW, cyan = DIAGNOSTIC_PASS only)", fill=0)
    d.text((8, 22), "magenta = DIM lines 2430 / 2431; red = H470 + H471 (two fragments) vs H477: no band, so H2430 "
                    "stays UNRESOLVED; yellow = OPEN_PASSAGE_SITE strips", fill=0)
    d.text((8, 38), "a closure carries NO material and moves no source point: it joins the two face end points", fill=0)
    im.save(path)


def rows_md(rows):
    out = []
    for r, v in rows.items():
        bl = "; ".join(f"{', '.join(b['zones'][:2])}: " + ", ".join(sorted({
            f"{x['class']}/{x['issue']}" + (f"[{x['detail']['source']}]" if isinstance(x["detail"], dict)
                                            and "source" in x["detail"] else "") for x in b["blockers"]}))
            for b in v["blockers"]) or "-"
        out.append([r, v["state"], "" if v["value"] is None else f"{v['value']:.4f}", len(v["physical_site_ids"]),
                    len(v["wall_bands"]), ", ".join(v["topology_closures_applied"]) or "-",
                    len(v["opening_closures"]), len(v["threshold_sites"]), len(v["open_passage_sites"]),
                    v["trade_authority"]["rule"], v["footprint_authority"]["treatment"] or "NONE", bl])
    return tbl(["Row", "State", "Value m2", "Sites", "Bands", "Closures", "Openings", "Thresholds", "Passages",
                "Treatment", "Footprint", "Blockers"], out)


def main(junit_path, command, exit_code, work=None):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_11_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "r8_11_test_files": sorted(p.name for p in (ROOT / "tests/r8_11").glob("test_*.py"))}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_11_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    if work:
        picture(work, OUT / PNG)
    D, Q, O, A = R["R8_11_DECISION_REGISTER"], R["QORTUBA_R8_11_STATUS"], R["OWNER_ACTION_REGISTER"], \
        R["R8_11_DECISION_REGISTER"]["answers"]
    G, rows = D["gates"], Q["rows"]["NEW_K2_R8_11"]
    W, TCR, NM, OP = R["WALL_BAND_REGISTER"], R["TOPOLOGY_CLOSURE_REGISTER"], R["NEAR_MISS_REGISTER"], \
        R["OPEN_PASSAGE_SITE_REGISTER"]
    caps, leak = W["cap_analysis"], TCR["leak"]
    q13, q14, man = R["Q13_STATUS"], R["Q14_STATUS"], R["QTO_RUN_MANIFEST"]
    tests = (f"commit `{commit}` · `{command}` · passed {jr['passed']} · xfailed {jr['xfailed']} · skipped "
             f"{jr['skipped']} · failed {jr['failed']} · errors {jr['errors']} · total {jr['total']} · exit {exit_code}")
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.11 — Wall bands, topology-only closures, object-footprint authority, run manifest (SHADOW)

## Owner
**{O['headline']}** The wardrobe-floor fact is not the only Q-13 blocker, so it is prepared and not asked.

## What R8.11 did
- **Wall bands**: paired wall faces recognised from structure alone (topology-obstacle geometry, not masonry), with
  source-derived ids.
- **Zero-material topology closures**: a wall end is closed by joining its two face end points. A closure moves no
  source point and adds no wall or finish quantity. It is authorised for shadow only with a drawn-cap corroboration
  and a passing consequence safety test.
- **H2431**: WALL_END_CAP_CANDIDATE. Its band end is closed, so the {leak['removed_m2']} m2 core leaves the HALL
  ({leak['hall_area_r8_10_m2']} -> {leak['hall_area_r8_11_m2']} m2) and the HALL's near-miss is gone.
- **H2430**: UNRESOLVED. Its lower face is drawn as two fragments (H470 + H471), so the frozen rule forms no band
  there. Not fixed after seeing the result (anti-calibration): E-R8.12-01.
- **H1316**: NOT_WALL_CAP. It is the jamb line of a glazed opening.
- **Open-passage sites** are explicit records ({len(OP['NEW_K2'])} in the new revision); door thresholds remain
  separate TS01 sites.
- **Semantic class authority** and **object-footprint policies**: the ceiling proceeds through its policy (from the
  Q-14 claim). The floor has no authority, and none is invented.
- **Run manifest**: RUN_INPUT_DIGEST over inputs, claims (offered / applied / rejected), policies and method. The code
  commit is provenance only.

## Qortuba six rows (new revision, PLAN_VARIANT_4_SELECTED)
{rows_md(rows)}

## Gates
- MIGRATION_PLANNING_READY = **{G['MIGRATION_PLANNING_READY']}**
- MIGRATION_EXECUTION_READY = **{G['MIGRATION_EXECUTION_READY']}**
- PRODUCTION_MIGRATION = **{G['PRODUCTION_MIGRATION']}**

## Tests
{tests}

STOP AFTER R8.11. NO PRODUCTION MIGRATION.
"""
    md["01_OWNER_ACTIONS.md"] = f"# Owner actions\n\n**{O['headline']}**\n\n## Prepared, not asked\n" + "\n".join(
        f"- **{a['action_id']}** — {a.get('question') or a.get('request')}\n  - why not now: {a['why_not_asked']}"
        for a in O["prepared_not_asked"]) + "\n\n## Never asked again\n" + "\n".join(f"- {d}" for d in O["do_not_ask"]) \
        + "\n"
    pol = W["policy"]
    md["02_WALL_BAND_MODEL.md"] = "# Wall-band model\n\n" + W["means"] + "\n\n## Rule\n" + "\n".join(
        f"- {b}" for b in pol["band"]) + "\n\nNever: " + "; ".join(pol["never"]) + "\n\nEnds: " + ", ".join(pol["ends"]) \
        + "; caps: " + ", ".join(pol["caps"]) + "\n\n## Amendment A1 (post-freeze)\n" + "\n".join(
        f"- {a}" for a in pol["amendments"]) + f"\n\nFrozen at commit `{W['frozen_at_commit']}`; first run (V1): " + \
        json.dumps(W["frozen_v1_first_run"]) + "\n\n## Counts\n" + json.dumps(W["counts"]) + "\n\nEnd kinds: " + \
        json.dumps(W["end_kinds"]) + "\n\n## New-revision bands\n" + tbl(
            ["Band", "Faces", "State", "Width mm", "Overlap mm", "Ends"],
            [[b["band_id"], " / ".join(b["faces"]), b["state"], b["width_mm"], b["overlap_mm"],
              "; ".join(f"{e['kind']}" + (f" caps {[c['source'] + ':' + c['grade'] for c in e['caps']]}"
                                          if e["caps"] else "") for e in b["ends"])] for b in W["NEW_K2"]]) + \
        "\n\nNegative tests: tests/r8_11/test_r8_11_wall_bands.py, test_r8_11_amendment_a1.py, " \
        "test_r8_11_second_family.py\n"
    c31, c30 = caps["2431"], caps["2430"]
    md["03_HALL_LOBBY_CAP_ANALYSIS.md"] = "# Hall / Lobby wall-end caps — blind structural test\n\n" + tbl(
        ["Line", "Layer", "Role", "Geometry", "Length mm", "Classification"],
        [[f"H{h}", c["layer"], c["role"], c["geometry"], c["length_mm"], c["classification"]]
         for h, c in caps.items()]) + \
        f"\n\n## H2431 — {c31['classification']}\n- band {c31['band_id']}, faces {c31['faces']}, " \
        f"{c31['band_width_mm']} mm, end {c31['end_kind']}\n- gaps to the face end points: {c31['gap_to_face_ends_mm']} " \
        f"mm; shortfall across {c31['shortfall_across_mm']} mm; offset along {c31['offset_along_mm']} mm\n- closure: " \
        f"{json.dumps(c31['closure'])}\n- old revision: {c31['old_revision_counterpart']}\n\n" \
        f"## H2430 — {c30['classification']}\n- {c30['reason']}\n- faces at its ends: {c30['faces_at_its_ends']}\n" \
        f"- {c30['pairing']['finding']}\n- {c30['pairing']['not_done_in_r8_11']}\n- old revision: " \
        f"{c30['old_revision_counterpart']}\n\n## Consequence\n" + json.dumps(leak, indent=1) + f"\n\nPicture: {PNG}\n"
    md["04_TOPOLOGY_CLOSURE_POLICY.md"] = "# Topology closure policy\n\n" + "\n".join(
        f"- {x}" for x in TCR["separation"]) + "\n\n" + TCR["material"] + "\n\n## Policy\n" + json.dumps(
        TCR["policy"], indent=1) + "\n\n## New-revision closures\n" + tbl(
        ["Closure", "Band", "Release", "Geometry", "Evidence", "Separated pieces"],
        [[c["closure_id"], c["band_id"], c["release"], c["geometry"], c["source_evidence"],
          [(p["area_m2"], p["pure_band_interior"]) for p in c["safety"]["separated_pieces"]]] for c in TCR["NEW_K2"]]) + \
        "\n\n## Old-revision closures\n" + tbl(["Closure", "Release", "Evidence"],
                                               [[c["closure_id"], c["release"], c["source_evidence"]]
                                                for c in TCR["OLD_K1"]]) + f"\n\nApplied: {TCR['applied']}\n"
    c16 = caps["1316"]
    md["05_H1316_CONTROL.md"] = f"# H1316 control\n\n- layer {c16['layer']}, role {c16['role']} ({c16['rule']}), " \
        f"grade {c16['authority_grade']}, geometry {c16['geometry']}\n- classification **{c16['classification']}**: " \
        f"{c16['reason']}\n- glazing ending on it: {c16['glazing_ending_on_it']}\n- near-miss record: " + \
        json.dumps([m for m in NM["NEW_K2_R8_11"] if m["source"] == "1316"]) + \
        "\n- no row uses its site; no closure is derived (the same generic path as H2431)\n"
    md["06_OPEN_PASSAGE_SITES.md"] = "# Open-passage sites\n\n" + OP["no_width_rule"] + "\n\n" + tbl(
        ["Passage", "Band end", "Target", "Width mm", "Thickness mm", "m2", "Zones", "Head", "Allocation"],
        [[p["passage_id"], f"{p['band_id']}:{p['band_end']} ({p['end_kind']})", p["target"], p["width_mm"],
          p["wall_thickness_mm"], p["area_m2"], p["site_zones"], p["head_condition"], p["trade_allocation"]]
         for p in OP["NEW_K2"]]) + "\n\nFrozen V1 counts: " + json.dumps(OP["frozen_v1_passages"]) + \
        "\n\n## QP-17 / QP-18 / QP-19 (old revision) — corroboration only\n" + json.dumps(OP["qp_audit"], indent=1) + "\n"
    th = R["THRESHOLD_SITE_REGISTER"]
    md["07_THRESHOLD_VS_PASSAGE.md"] = "# Door threshold vs open passage\n\n" + "\n".join(
        f"- **{k}:** {v}" for k, v in th["distinction"].items()) + "\n\n## New-revision thresholds\n" + tbl(
        ["Threshold", "Opening", "m2", "Sides", "Allocation"],
        [[t["threshold"], t["opening"], t["area_m2"], t["sides"], t["allocation"]] for t in th["NEW_K2"]]) + \
        "\n\nWet rows: " + json.dumps(th["wet_rows_new"]) + "\n\n## Reveal / soffit guard\n" + \
        json.dumps(OP["NEW_K2"][0]["reveals"] if OP["NEW_K2"] else {}) + "\n"
    fp = R["OBJECT_FOOTPRINT_POLICY"]
    md["08_OBJECT_FOOTPRINT_AUTHORITY.md"] = "# Object-footprint authority\n\nTreatments: " + \
        ", ".join(fp["treatments"]) + "\n\n## CEILING\n" + json.dumps(fp["CEILING"]) + "\n\n## FLOOR_FINISH\n" + \
        json.dumps(fp["FLOOR_FINISH"], indent=1) + "\n\n## Implicit path\n" + json.dumps(fp["implicit_path"], indent=1) + \
        "\n\n" + fp["role_vs_footprint"] + "\n"
    md["09_Q13_ANALYSIS.md"] = f"# Q-13 (dry floor)\n\nState **{q13['state']}** (R8.10: {q13['r8_10']['state']}).\n\n" \
        "## Blockers\n" + "\n".join(f"- {b['zones']} ({b['area_m2']} m2): " + "; ".join(
            f"{x['class']}/{x['issue']} {json.dumps(x['detail'])[:200]}" for x in b["blockers"])
            for b in q13["blockers"]) + "\n\n## Sole-blocker test\n" + json.dumps(q13["sole_blocker_test"], indent=1) + \
        "\n\nRelease blockers: " + "; ".join(q13["release_blockers"]) + "\n"
    md["10_Q14_ANALYSIS.md"] = f"# Q-14 (ceiling)\n\nState **{q14['state']}** (R8.10: {q14['r8_10']['state']}; " \
        f"R8.10 classes {q14['r8_10']['blocker_classes']}).\n\n## Blockers\n" + json.dumps(q14["blockers"], indent=1) + \
        f"\n\nFootprint authority: {q14['footprint_authority']}\n\n## Path\n{q14['path_to_computed_shadow']}\n\n" \
        "Success criteria (§37): the HALL wall-core leakage is not yet resolved through valid topology authority, so " \
        "Q-14 stays BLOCKED.\n"
    sc = R["SEMANTIC_CLASS_REGISTER"]
    md["11_SEMANTIC_CLASS_AUTHORITY.md"] = "# Semantic class authority\n\n" + json.dumps(sc["rule"], indent=1) + \
        "\n\nFloor treatment by class: " + json.dumps(sc["floor_treatment_by_class"]) + "\n\nEquivalence with R8.10: " + \
        json.dumps(sc["equivalence_with_r8_10"]) + "\n\n" + sc["never"] + "\n"
    md["12_NETWORK_WALL_BAND_REVIEW.md"] = "# NETWORK review and wall bands\n\nA NETWORK_BOUNDARY_CANDIDATE that is a " \
        "face of an ESTABLISHED wall band is corroborated (paired_wall_face); single-line partitions keep working " \
        "(no band is needed to be a boundary).\n\n" + json.dumps(W["network_paired_face_corroboration"], indent=1) + "\n"
    n = man["NEW_K2"]
    md["13_RUN_MANIFEST.md"] = "# QTO run manifest\n\n" + tbl(["Field", "Value"], [
        [k, json.dumps(n[k], ensure_ascii=False)[:300]] for k in (
            "schema", "run_id", "RUN_INPUT_DIGEST", "code_commit", "CODE_BOUND_DIGEST", "source_revision_id",
            "source_anchor_sha256", "region_id", "frame_id", "unit_claim_id", "canonical_input_digest",
            "evidence_version", "method", "decoder_route", "kernel_versions", "not_in_digest")]) + \
        "\n\n## Policies\n" + tbl(["Policy", "Id", "Digest"], [[k, v[0], v[1]] for k, v in n["policies"].items()]) + \
        "\n\n## Claims\n- offered: " + json.dumps(n["claims_offered"]) + "\n- applied: " + \
        json.dumps([c["claim"] for c in n["claims_applied"]]) + "\n- rejected: " + json.dumps(n["claims_rejected"]) + \
        "\n- old revision rejected: " + json.dumps([(c["claim"], c["outcome"]) for c in man["OLD_K1"]["claims_rejected"]]) + \
        "\n\n## Determinism (shuffled source order)\n" + json.dumps({k: v for k, v in man[
            "determinism_shuffled_source_order"].items() if k not in ("bands", "closures")}) + "\n\n" + man["rule"] + \
        "\n\nRow-level authority (Q-14 claim, class rule, footprint policies) is bound per row by row_input_digest.\n"
    sco = Q["scope"]
    md["14_SOURCE_ANCHOR.md"] = f"# Source anchor\n\n- measured: DXF `{sco['anchor_dxf']}`\n- DWG candidate: " \
        f"`{sco['dwg_candidate']}` — identity **{sco['dwg_identity']}**\n- claims are anchored to the DXF only and are " \
        "not transferred to the DWG\n- every new-revision row carries the SOURCE_ANCHOR release blocker\n"
    md["15_QORTUBA_SIX_ROW_STATUS.md"] = "# Qortuba six-row status (SHADOW)\n\n" + rows_md(rows) + \
        "\n\n## Per-row provenance\n" + "\n".join(
            f"- **{r}**: run `{v['run_id']}` input `{v['run_input_digest'][:16]}...` row `{v['row_input_digest'][:16]}...`"
            f"; claims {v['claims_applied']}; anchor {v['source_anchor']}; release blockers {v['release_blockers']}"
            for r, v in rows.items()) + "\n\n## Old revision with closures\n" + tbl(
            ["Row", "State", "Value", "Unchanged vs R8.10"],
            [[r, v["state"], v["value"], Q["old_revision_unchanged_by_closures"][r]]
             for r, v in Q["rows"]["OLD_K1_R8_11"].items()]) + "\n\n" + Q["final"] + "\n"
    md["16_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## Decisions\n" + "\n".join(f"- **{d['id']}:** {d['decision']}" for d in D["decisions"]) + \
        "\n\n## Order (anti-calibration)\n" + "\n".join(f"- {o}" for o in D["order"]) + \
        "\n\n## Engineering actions\n" + "\n".join(f"- **{a['id']}** {a['title']}: {a['what']}"
                                                   for a in R["ENGINEERING_ACTION_REGISTER"]["actions"]) + "\n"
    md["17_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nR8.11 test files: " + \
        ", ".join(res["r8_11_test_files"]) + "\n"
    pre = D["recommendation_before_coding"]
    md["18_CLAUDE_RECOMMENDATION.md"] = "# Claude recommendation\n\n## §0 (1-10)\n" + "\n".join(
        f"- **{k}:** {v if isinstance(v, str) else '; '.join(v)}" for k, v in pre.items()) + \
        "\n\n## Answers 1-30\n" + "\n".join(
            f"- **{k}:** {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)[:900]}" for k, v in A.items()) + \
        "\n\nSTOP AFTER R8.11. NO PRODUCTION MIGRATION.\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(R) + 1, "json", "png" if work else "no png")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]), a[3] if len(a) > 3 else None)
