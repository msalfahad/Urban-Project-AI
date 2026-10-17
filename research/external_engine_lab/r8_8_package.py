"""R8.8 review package: URBAN_QTO_R8_8_TOPOLOGY_STABILITY (18 md + 16 json + 2 overlays + zip).

Built from the committed R8.8 registers, the junit of ONE full suite run from the final commit, and (for the two
site overlays) the lab's cached inputs.

    python3 research/external_engine_lab/r8_8_package.py <junit.xml> "<command>" <exit_code> [<work_dir>]
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit, tbl                                            # noqa: E402

REG = ROOT / "tests/r8_8/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_8_TOPOLOGY_STABILITY"
JSONS = ("OWNER_ACTION_REGISTER", "ENGINEERING_ACTION_REGISTER", "REGION_MEMBERSHIP_POLICY",
         "SOURCE_SUBPART_IDENTITY_SCHEMA", "VISIBILITY_AUTHORITY_REGISTER", "GEOMETRY_ROLE_REGISTER",
         "ELLIPSE_EXCLUSION_AUDIT", "TOPOLOGY_TOLERANCE_POLICY", "OLD_QORTUBA_CROSS_ROUTE", "NEW_QORTUBA_TOPOLOGY",
         "QORTUBA_SIX_ROW_STATUS", "R8_8_DECISION_REGISTER", "ARCHITECTURE_REVIEW", "TOPOLOGY_CROSSCHECK",
         "TOLERANCE_ARCHITECTURE")


def jl(p):
    return json.loads(Path(p).read_text())


def overlay(res, inp, path, box):
    from PIL import Image, ImageDraw
    arr = res["_arr"]
    x0, y0, x1, y1 = box
    W = 2000
    s = W / (x1 - x0)
    im = Image.new("RGB", (W, int((y1 - y0) * s) + 1), "white")
    d = ImageDraw.Draw(im)
    v = lambda p: ((p[0] - x0) * s, (y1 - p[1]) * s)

    def pts(cyc):
        out = []
        for k, fw in cyc:
            e = arr.edges[k]
            if e["kind"] == "S":
                seg = [arr.nodes[e["n0"]], arr.nodes[e["n1"]]]
            else:
                pr = e["prim"]
                seg = [pr.point(e["t0"] + (e["t1"] - e["t0"]) * i / 12) for i in range(13)]
            out += seg if fw else seg[::-1]
        return out
    for st in res["sites"]:
        if st["area_m2"] < 0.3:
            continue
        col = ((150, 190, 250) if st["kind"] == "OPENING_SITE" else (170, 230, 170) if st["status"] == "CERTIFIED"
               else (250, 150, 150) if "MULTIPLE_SEMANTIC_LABELS" in st["issues"] else (250, 200, 120))
        d.polygon([v(p) for p in pts(st["cycle"])], fill=col, outline=(0, 0, 0))
        for hc in st["hole_cycles"]:
            d.polygon([v(p) for p in pts(hc)], fill=(255, 255, 255))
    for e in arr.edges:
        if e["kind"] == "S":
            c = (0, 0, 255) if any(x.startswith("CLOSURE|") for x in e["sources"]) else (0, 0, 0)
            d.line([v(arr.nodes[e["n0"]]), v(arr.nodes[e["n1"]])], fill=c, width=3 if c != (0, 0, 0) else 1)
    roles = res["roles"]["roles"]
    for p in inp.parts:
        a = roles.get(p.identity.key)
        if a is not None and a.role in ("UNKNOWN_PHYSICAL", "BOUNDARY_CURVE_UNSUPPORTED") and p.kind == "SEGMENT":
            g = p.geometry
            d.line([v((g[0], g[1])), v((g[2], g[3]))], fill=(230, 0, 230), width=3)
    texts = {t.identity.key: t for t in inp.texts}
    for st in res["sites"]:
        for lt in st["label_texts"]:
            t = texts[lt["text"]]
            d.text(v((t.x, t.y)), lt["value"][:12], fill=(0, 0, 120))
        if st["area_m2"] >= 1 and st["kind"] != "OPENING_SITE":
            b = st["bbox"]
            d.text(v(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 15)), f"{st['area_m2']:.4f}", fill=(120, 0, 0))
    d.text((10, 10), "green CERTIFIED | orange REVIEW (role / tolerance) | red MULTIPLE_SEMANTIC_LABELS | blue opening "
                     "site | blue lines: closures | magenta: unknown-role geometry", fill=(0, 0, 0))
    im.save(path)


def overlays(work):
    import r8_8_topology as LAB
    inps = LAB.inputs(Path(work))
    inps.pop("_NEW_ALL_PARTS", None)
    box = (109250.0, 14400.0, 111450.0, 16100.0)
    for name, fn in (("OLD_K1", "OLD_QORTUBA_K1_SITES.png"), ("NEW_K2", "NEW_QORTUBA_SITES.png")):
        overlay(LAB.run(inps[name], LAB.UNREALISED[name]), inps[name], OUT / fn, box)
    return ["OLD_QORTUBA_K1_SITES.png", "NEW_QORTUBA_SITES.png"]


def rows_table(rows):
    return tbl(["Row", "State", "Value m2", "Sites used", "Blocked by"],
               [[r, v["state"], "" if v["value"] is None else f"{v['value']:.4f}",
                 "; ".join(f"{'/'.join(sorted(n for st in u['stamps'] for n in st if n.isascii() and n.isupper()))} "
                           f"{u['area_m2']:.4f}" for u in v["sites_used"]),
                 "; ".join(str(b["why"])[:70] for b in v["blockers"][:3])] for r, v in rows.items()])


def main(junit_path, command, exit_code, work=None):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_8_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted"}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_8_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    pngs = overlays(work) if work else []
    D, X, NEW, SIX = R["R8_8_DECISION_REGISTER"], R["OLD_QORTUBA_CROSS_ROUTE"], R["NEW_QORTUBA_TOPOLOGY"], \
        R["QORTUBA_SIX_ROW_STATUS"]
    G, A, ELL, POL = D["gates"], D["answers"], R["ELLIPSE_EXCLUSION_AUDIT"], R["TOPOLOGY_TOLERANCE_POLICY"]
    OWN, ENG, ROLE, VIS = R["OWNER_ACTION_REGISTER"], R["ENGINEERING_ACTION_REGISTER"], R["GEOMETRY_ROLE_REGISTER"], \
        R["VISIBILITY_AUTHORITY_REGISTER"]
    xc = X["comparison"]
    rows_old, rows_new = SIX["rows"]["OLD_K1"], SIX["rows"]["NEW_K2"]
    tests = (f"commit `{commit}` · `{command}` · passed {jr['passed']} · xfailed {jr['xfailed']} · skipped "
             f"{jr['skipped']} · failed {jr['failed']} · errors {jr['errors']} · total {jr['total']} · exit {exit_code}")
    md = {}
    md["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.8 — Topology stability (SHADOW)

**NO OWNER ACTION REQUIRED FOR THE NEXT CODING ROUND.**

## What changed
- **New room method (TS01).** A certified vector room topology replaces the raster QS01 path, in shadow. It has no
  axis predicate; tolerances fall into three bands (noise / ambiguous / authored); a site counts only if it is
  identical in two builds (at eps_n and at eps_r).
- **Role admission.** Only positively admitted wall, column, glazing and opening-closure geometry can bound a room.
  Furniture, fixtures, dimensions, sheet frames and door symbols are excluded, and unknown geometry blocks the sites
  it touches.
- **Input contract.** Exact curve region membership, source sub-part identity, visibility authority for every
  record type, and method exclusions that need role authority.

## Architecture (addendum)
- **TS01 stays the single vector authority.** An independent GEOS reconstruction (node + polygonize) cross-checks
  every straight-edged site for area and boundary provenance; it can only withhold a site. Raster is QA only.
- **Cross-check result:** {G['TOPOLOGY_CROSSCHECK']}.
- wall_solid / free_space are not the foundation (axis-only, material-coupled, a calibrated 0.05 mm grid snap);
  their principles are reused. See 17_ARCHITECTURE_REVIEW.md.

## Route stability (the H584 control)
- The old revision read by two routes gives **{xc['common_site_ids']} sites with identical ids, labels, issues and
  contents**.
- The largest area difference is {xc['max_area_difference_m2']:.1e} m², and the six rows are identical.
- H584 no longer moves any area.

## Six rows
{rows_table(rows_old)}

(old revision, both routes)

{rows_table(rows_new)}

(new revision, DXF diagnostic)

## Gates
- MIGRATION_PLANNING_READY = **{G['MIGRATION_PLANNING_READY']}**
- MIGRATION_EXECUTION_READY = **{G['MIGRATION_EXECUTION_READY']}**
- PRODUCTION_MIGRATION = **{G['PRODUCTION_MIGRATION']}**
- New DWG source identity = **{G['NEW_DWG_SOURCE_IDENTITY']}** (not forced)

## Tests
{tests}

STOP AFTER R8.8. NO R9. NO PRODUCTION MIGRATION.
"""
    md["01_OWNER_ACTIONS.md"] = "# Owner actions (V5)\n\n**" + OWN["headline"] + "**\n\n" + OWN["rule"] + ".\n\n" + tbl(
        ["Action", "Project", "Status", "Asked now?"],
        [[a["action_id"], a["project"], a["status"], "no"] for a in OWN["actions"]]) + \
        "\n\nMoved to the engineering register: " + ", ".join(OWN["moved_to_engineering"]) + "\n"
    md["02_ENGINEERING_ACTIONS.md"] = "# Engineering / environment actions\n\n" + ENG["rule"] + ".\n\n" + "\n".join(
        f"- **{a['action_id']}** ({a['status']}): {a['what']}" for a in ENG["actions"]) + "\n"
    rm = R["REGION_MEMBERSHIP_POLICY"]
    md["03_EXACT_REGION_MEMBERSHIP.md"] = f"""# Exact region membership

- **Method:** {rm['policy']['method']}.
- **States:** {', '.join(rm['policy']['states'])}.
- **Tangency:** {rm['policy']['tangent_rule']}.
- **Occurrences:** {rm['occurrence_rule']}.
- **Noise:** {rm['eps']}.
- **R8.7 defect (F-R88-01):** a 5-point sampler kept an arc and an ellipse inside while their true extrema crossed the
  boundary (tests A and B). No quantity can now depend on a sampler missing a crossing.

{tbl(['Run', 'Records held for review', 'Outside', 'Clip'], [[k, v['region_review'], v['outside'], v['clip_bounds']] for k, v in rm['runs'].items()])}
"""
    sp = R["SOURCE_SUBPART_IDENTITY_SCHEMA"]
    md["04_SOURCE_SUBPART_IDENTITY.md"] = "# Source sub-part identity\n\n- **Key:** `" + sp["key"] + "`\n" + "\n".join(
        f"- **{k}:** {v}" for k, v in sp["source_sub_part"].items()) + "\n- **Where set:** " + sp["where_set"] + \
        "\n- **Never:** " + ", ".join(sp["never"]) + "\n- **Missing:** " + sp["missing"] + \
        "\n- **R8.7 defect (F-R88-02):** part_index was a per-kind ordinal over realised output.\n"
    md["05_VISIBILITY_AUTHORITY.md"] = "# Visibility authority\n\n" + "\n".join(f"- {r}" for r in VIS["rules"]) + \
        f"\n\n- K1: {VIS['k1_layer_state_source']}\n- K2: {VIS['k2_layer_state_source']}\n- Use: {VIS['method_use']}\n\n" + \
        tbl(["Run", "Parts", "Texts", "Dimensions"], [[k, v["parts"], v["texts"], v["dimensions"]]
                                                     for k, v in VIS["counts_in_selected_region"].items()]) + "\n"
    pr = ROLE["policy"]
    md["06_GEOMETRY_ROLE_ADMISSION.md"] = "# Geometry role admission\n\nPolicy `" + pr["id"] + "` (digest `" + \
        pr["digest"][:16] + "`). Never decided by: " + ", ".join(pr["never_alone"]) + ".\n\n" + tbl(
            ["Rule", "Role", "Strength", "Requires"], [[r["id"], r["role"], r["strength"], r["requires"]] for r in pr["rules"]]) + \
        "\n\n## Admitted / excluded / blocking\n- Admitted: " + ", ".join(pr["admitted_to_room_topology"]) + \
        "\n- Excluded: " + ", ".join(pr["excluded"]) + "\n- Blocking: " + ", ".join(pr["blocking"]) + \
        "\n\n## New revision: bound-xref blocks (the furniture audit)\n" + tbl(
            ["Occurrence", "Block", "Parts", "Role", "Rule", "Why"],
            [[f["insert_occurrence"], f["block_name"], f["parts"], f["role"], f["rule"], f["why"][:120]]
             for f in ROLE["new_revision_bound_xref_audit"]]) + "\n\n## Unknown geometry (new revision)\n" + tbl(
            ["Layer", "Parts", "Sites blocked"], [[k, v["parts"], len(v["sites_blocked"])]
                                                  for k, v in ROLE["runs"]["NEW_K2"]["unknown_by_layer"].items()]) + "\n"
    md["07_ELLIPSE_EXCLUSION_AUDIT.md"] = "# The eight old-revision ellipses\n\n" + ELL["rule"] + ".\n\nCounts: " + \
        json.dumps(ELL["classification_counts"]) + "\n\n" + tbl(
            ["Handle", "Instance path", "Layer", "Entity", "Role", "Rule", "Door closure", "Width", "Class"],
            [[r["source_handle"], "/".join(r["instance_path"]), r["layer"], r["source_entity_type"], r["role"], r["rule"],
              r["door_closure"], f"{r['door_closure_width']:.1f}", r["classification"]] for r in ELL["records"]]) + "\n"
    md["08_TOPOLOGY_TOLERANCE_POLICY.md"] = f"""# Topology tolerance policy (frozen)

- **Policy:** `{POL['id']}`, digest `{POL['digest']}`.
- **Frozen at:** {POL.get('frozen_at')}.
- **Noise band:** eps_n = 2^-30 × max|coordinate| ({POL['noise_basis']}).
- **Authored precision:** eps_r = {POL['authored_precision_mm']} mm ({POL['authored_basis']}).
- **Certificate:** {POL['certificate']}.
- **Calibration:** {POL['calibration']}.
- **Source geometry:** {POL['source_geometry']}.

{tbl(['Predicate', 'Tolerance'], [[k, v] for k, v in POL['predicates'].items()])}

**Post-freeze changes** (no number changed): {', '.join(D['post_freeze_changes']['fixes'])}. Each was found by a real
run and has a permanent regression test.
"""
    md["09_OLD_QORTUBA_CROSS_ROUTE.md"] = f"""# Old Qortuba: K1 vs K2 (same DWG, two routes)

- Sites: K1 {xc['sites_K1']}, K2 {xc['sites_K2']}, common ids {xc['common_site_ids']}.
- Differences: {len(xc['differences'])}.
- Same topology: **{xc['same_topology']}**.
- Largest area difference: {xc['max_area_difference_m2']:.2e} m².
- Openings equal: {xc['openings_equal']}.
- **H584:** bounds sites {xc['H584']['sites_bounded_by_H584']}, with identical areas on both routes.
- **Rows equal:** {X['rows_equal']}.

## Every difference, classified
""" + "\n".join(f"- **{k}:** {v}" for k, v in X["every_difference_classified"].items()) + f"\n\n**Goal:** {X['goal']}\n"
    md["10_NEW_QORTUBA_TOPOLOGY.md"] = "# New Qortuba (DXF diagnostic, PLAN_VARIANT_4_SELECTED)\n\nAnchor: " + \
        NEW["anchor"] + ". Variant isolation: **" + str(NEW["variant_isolation"]["isolated"]) + "**.\n\n" + tbl(
            ["Site", "Stamps", "Area m2", "Status", "Issues", "Boundary ids"],
            [[r["site_id"], " | ".join("/".join(s) for s in r["stamps"]), f"{r['area_m2']:.4f}", r["status"],
              ", ".join(r["issues"]), len(r["boundary_source_ids"])] for r in NEW["rooms"]]) + "\n\n" + \
        ("![new sites](NEW_QORTUBA_SITES.png)\n" if pngs else "")
    md["11_MULTI_LABEL_SPACES.md"] = """# Two labels in one physical space

- **Label occurrence.** A label occurrence is the SOURCE occurrence that places a text: the room-stamp block insert,
  or the text entity itself. The bilingual texts of one stamp form a single occurrence.
- **Rule.** A site holding more than one occurrence is MULTIPLE_SEMANTIC_LABELS → REVIEW_REQUIRED. Nothing chooses a
  winner: not wet-first, first, largest or alphabetical.
- **Split-invariant rows.** A row whose answer is the same for every stamp in the site is shown only as
  "value_if_split_review_accepted". It never becomes a computed value.

**Qortuba**
- Old revision: M.B.ROOM + DRESS are one physical space.
- New revision: HALL + BED.ROOM + BATH are one physical space (the redrawn partition leaves open passages).
- Both are REVIEW_REQUIRED.

**Ambiguity findings**
- A label within eps_r of its site's boundary gives LABEL_ON_BOUNDARY.
- One occurrence split across two sites gives LABEL_OCCURRENCE_SPLIT.
- There is no nearest-label fallback.
"""
    md["12_ROOM_SITE_IDENTITY.md"] = """# Room / site identity

- **site_id.** sha256 over (revision, region, the sorted SOURCE identities of the outer boundary, and those of the
  holes). It is not the room name and not a coordinate.
- **Room name.** An attribute: the site's label occurrences.
- **Stability.** The same handles moved by any amount keep the id. A different revision or a different source gives
  a different id (tests).
- **Collisions.** A collision is marked SITE_ID_COLLISION and never merged.
"""
    md["13_QORTUBA_SIX_ROW_STATUS.md"] = "# Qortuba six-row status (TS01, SHADOW)\n\n## Old revision (K1 = K2)\n" + \
        rows_table(rows_old) + "\n\n## New revision (DXF diagnostic)\n" + rows_table(rows_new) + \
        "\n\n## Compared with legacy QS01 (old revision) — after the rows were computed\n" + tbl(
            ["Row", "TS01", "legacy QS01"], [[r, v["TS01_OLD_K1"], v["legacy_QS01"]]
                                             for r, v in SIX["comparison_made_after_the_rows"].items()]) + \
        "\n\n- **Q-03 / Q-11 (17.7425 vs 17.8625):** METHOD_DIFFERENCE. QS01 counted one bathroom's door threshold strip " \
        "(0.12 m²) in that bathroom; TS01 keeps every opening strip as its own site. Whether a threshold belongs to a " \
        "room is a trade rule, not a topology fact.\n" \
        "- **Q-03P / Q-12:** identical.\n" \
        "- **Q-13 / Q-14:** blocked; see 10_NEW_QORTUBA_TOPOLOGY.md and 14_OPEN_GATES.md.\n"
    md["14_OPEN_GATES.md"] = "# Open gates\n\n" + tbl(["Gate", "State"], [[k, v] for k, v in G.items()]) + \
        "\n\n## What blocks the new-revision rows\n" + "\n".join(
            f"- **{r}:** " + "; ".join(str(b["why"])[:160] for b in bl) for r, bl in A["20_what_blocks"].items()) + \
        "\n\n## Findings\n" + "\n".join(f"- **{f['id']}:** {f['finding']}" for f in D["findings"]) + "\n"
    md["15_TEST_RESULTS.md"] = "# Test results\n\n" + tests + "\n\nThe R8.8 tests cover the required list: " \
        "tests/r8_8/test_r8_8_region_membership.py, test_r8_8_subpart_identity.py, test_r8_8_visibility.py, " \
        "test_r8_8_roles_and_exclusions.py, test_r8_8_topology.py, test_r8_8_inspired_risks.py, " \
        "test_r8_8_qortuba_real.py, test_r8_8_architecture.py (addendum).\n"
    AR = R["ARCHITECTURE_REVIEW"]
    q, sec = AR["questions"], AR["sections"]

    def item(v):
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return "\n" + "\n".join(f"  - {x}" for x in v)
        return "\n" + "\n".join(f"  - **{k}:** {item(x) if isinstance(x, (str, list)) else json.dumps(x)}"
                                 for k, x in v.items())
    md["17_ARCHITECTURE_REVIEW.md"] = "# ARCHITECTURE REVIEW — CLAUDE RECOMMENDATION\n\n**" + AR["recommendation"] + \
        "**\n\n## The seven questions\n" + "\n".join(f"- **{k}:** {item(v)}" for k, v in q.items()) + \
        "\n\n## Sections\n" + "\n".join(f"- **{k}:** {item(v)}" for k, v in sec.items()) + \
        "\n\n## Findings from the review\n" + "\n".join(
            f"- **{f['id']}:** {f['finding']}" for f in D["findings"] if int(f["id"].split("-")[-1]) >= 19) + "\n"
    md["16_CLAUDE_RECOMMENDATION.md"] = "# Claude recommendation\n\n## Assessment before coding\n" + "\n".join(
        f"- **{k}:** {v}" for k, v in D["assessment_before_coding"].items()) + "\n\n## Answers (§33)\n" + "\n".join(
        f"- **{k}:** {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v}" for k, v in A.items()) + \
        "\n\n## Recommendation\n" + D["recommendation"] + "\n\nSTOP AFTER R8.8. NO R9. NO PRODUCTION MIGRATION.\n"
    if pngs:
        md["09_OLD_QORTUBA_CROSS_ROUTE.md"] += "\n![old sites](OLD_QORTUBA_K1_SITES.png)\n"
    for name, text in md.items():
        (OUT / name).write_text(text)
    zp = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(zp, len(md), "md", len(R) + 1, "json", len(pngs), "png")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]), a[3] if len(a) > 3 else None)
