"""R8.9 lab: Qortuba role authority, semantic zones and the new-revision rerun (SHADOW, project semantics here only).

    python3 research/external_engine_lab/r8_9_qortuba.py <work_dir> <register_dir>

Inputs as R8.8 (old K1 decode, old K2 = LibreDWG's DXF of the same DWG, new K2 = the selected new-revision DXF).
Investigations are BLIND to the desired quantities: geometry, block structure, layer use, labels, dimensions,
source metadata and the cross-revision delta only. A hypothesis run (a claim applied in a sandbox copy) is
labelled HYPOTHESIS and never registered as authority.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_8_topology as LAB                                                                 # noqa: E402
from engine.source import canonical_input as CI, geometry_role as GR                        # noqa: E402
from engine.source import region_membership as RM, role_authority as RA, room_topology as RT  # noqa: E402
from engine.source import semantic_zones as SZ, text_role as TX, topology as T              # noqa: E402
from engine.source import topology_crosscheck as XC, topology_policy as TP                  # noqa: E402

C = LAB.C
ROWS = LAB.ROUND1


def m2(inp, a):
    return a * (inp.unit_native_to_mm ** 2) / 1e6


def handle(key):
    return key.split("|")[1][1:] if key and "|" in key else key


# ====================================================================== row status with R8.9 blocker classes
def classify_blocker(b, site):
    why = b.get("why")
    if isinstance(why, str) and "row classes" in why:
        if site is not None and RA.ROLE_CONFLICT_SEPARATOR in site["issues"]:
            return "BLOCKED_ROLE"                     # the space only looks multi-zone because a separator is excluded
        return "BLOCKED_SEMANTIC_ZONE"
    if isinstance(why, str) and "Q-14 ceiling basis" in why:
        return "BLOCKED_OWNER_SCOPE"
    iss = set(why or []) if isinstance(why, list) else set()
    if iss & {T.TOPOLOGY_ROLE_UNRESOLVED, RA.ROLE_CONFLICT_SEPARATOR, T.OPENING_CLOSURE_UNRESOLVED}:
        return "BLOCKED_ROLE"
    if iss & {"REGION_REVIEW_REQUIRED", "OCCURRENCE_REVIEW_REQUIRED", "UNREALISED_ENTITY_POSSIBLY_IN_SITE",
              "UNREALISED_ENTITY_ON_BOUNDARY_LAYER"}:
        return "BLOCKED_UNREALISED_ENTITY"
    if iss & {TX.TEXT_ROLE_UNRESOLVED_IN_SITE, T.LABEL_ON_BOUNDARY, T.LABEL_OCCURRENCE_SPLIT}:
        return "BLOCKED_SEMANTIC_ZONE"
    if iss & {RA.UNKNOWN_OBJECT_IN_SITE}:
        return "BLOCKED_TRADE_RULE"
    return "BLOCKED_PHYSICAL"


XREF_CODES = ("XREF_CONTENT_NOT_IN_SOURCE", "XREF_NOT_RESOLVED", "XREF_UNLOADED")


def rows_r89(res, revision_id):
    rows = LAB.six_rows(res, revision_id)
    by = {s["site_id"]: s for s in (res["sites"] or [])}
    blocking = res.get("unrealised", {}).get("blocking_input") or []
    xref_only = bool(blocking) and all(b["code"] in XREF_CODES for b in blocking)
    th = res.get("semantic", {}).get("thresholds", [])
    for rid, r in rows.items():
        classes = {classify_blocker(b, by.get(b.get("site"))) for b in r["blockers"]}
        if xref_only and "BLOCKED_UNREALISED_ENTITY" in classes:
            classes = (classes - {"BLOCKED_UNREALISED_ENTITY"}) | {"BLOCKED_SOURCE_COMPLETENESS"}
        classes = sorted(classes)
        r["r8_9_state"] = classes[0] if len(classes) == 1 else ("BLOCKED_MULTIPLE: " + ", ".join(classes)) \
            if classes else r["state"]
        r["blocker_classes"] = classes
        used = {u["site"] for u in r["sites_used"]}
        r["basis"] = "PHYSICAL_ROOM_FOOTPRINT (threshold strips are their own sites, not included)"
        r["pending_trade_rules"] = [{"threshold": t["threshold_id"], "area_m2": round(m2_from(res, t["area"]), 6),
                                     "sides": t["sides"], "allocation": t["allocation"]}
                                    for t in th if used & set(t["sides"])]
    return rows


def m2_from(res, a):
    return a * res.get("_unit2", 1.0)


# ====================================================================== investigations (blind)
def rect_with_diagonal(parts):
    """Groups of 2 axis-parallel + 1 diagonal segment sharing end points: the rectangle-with-diagonal symbol."""
    segs = [p for p in parts if p.kind == "SEGMENT"]
    out = []
    for d in segs:
        x1, y1, x2, y2 = d.geometry
        if abs(x1 - x2) < 1e-6 or abs(y1 - y2) < 1e-6:
            continue
        w, h = abs(x2 - x1), abs(y2 - y1)
        out.append({"diagonal": handle(d.identity.key), "box_native": [round(min(x1, x2), 1), round(min(y1, y2), 1),
                                                                       round(max(x1, x2), 1), round(max(y1, y2), 1)],
                    "short_side_native": round(min(w, h), 3), "long_side_native": round(max(w, h), 3)})
    return out


def firntur_investigation(inp, res, all_parts, frames):
    roles = res["roles"]["roles"]
    ps = [p for p in inp.parts if p.layer == "FIRNTUR"]
    sites = {s["site_id"]: s for s in res["sites"]}
    per_part = []
    for p in ps:
        hit = res["probe_sites"].get(p.identity.key, [])
        per_part.append({"handle": handle(p.identity.key), "kind": p.kind, "entity": p.entity_type,
                         "geometry_native": [round(v, 3) for v in p.geometry],
                         "role": roles[p.identity.key].role, "rule": roles[p.identity.key].rule_id,
                         "sites": [{"site": sid, "stamps": list(LAB.stamps(sites[sid]).values()),
                                    "area_m2": round(sites[sid]["area_m2"], 3)} for sid in hit]})
    usage = {}
    for name, f in frames.items():
        x0, y0, x1, y1 = f["extent"]
        n = 0
        for p in all_parts:
            if p.layer != "FIRNTUR":
                continue
            b = RM.exact_bbox(p.kind, p.geometry)
            if b and not (b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1):
                n += 1
        usage[name] = n
    xref_layer = Counter(roles[k].role for k, p in ((q.identity.key, q) for q in inp.parts)
                         if p.layer == "MY BLOCKS$0$FIRNTUR")
    grades = res["roles"]["grades"]
    contacts = []
    adm_items = [k for k, g in grades.items()]
    sym = rect_with_diagonal(ps)
    unit = inp.unit_native_to_mm
    mb = [x for x in per_part if any("M.B.ROOM" in str(s["stamps"]) for s in x["sites"])]
    roof = [x for x in per_part if any("ROOF" in str(s["stamps"]) for s in x["sites"])]
    return {
        "layer": "FIRNTUR (host model-space layer)", "parts_in_region": len(ps), "parts": per_part,
        "usage_by_plan_variant": usage,
        "same_token_in_this_source": {"layer": "MY BLOCKS$0$FIRNTUR (the bound xref's layer of the same name)",
                                      "roles_of_its_parts": dict(xref_layer),
                                      "meaning": "the author's own furniture library places a proven FURNITURE block "
                                                 "(BED 3, GR-03) on a layer with this exact token"},
        "rectangle_with_diagonal_symbols": [dict(s, short_side_mm=round(s["short_side_native"] * unit, 1),
                                                 long_side_mm=round(s["long_side_native"] * unit, 1)) for s in sym],
        "in_master_bedroom": [x["handle"] for x in mb], "on_roof": [x["handle"] for x in roof],
        "verdict": {
            "MB_wardrobe_lines": "SOURCE_SCOPED_CANDIDATE: FURNITURE / built-in joinery (wardrobe): rectangle-with-"
                                 "diagonal symbols 600 mm deep against the walls, on a layer whose token the same "
                                 "source uses for proven furniture. NOT a generic rule (FIRNTUR is not added to the "
                                 "lexicon); a candidate claim does not change the role",
            "roof_double_lines": "ROLE_UNRESOLVED: two double lines 100 mm apart forming an L on the roof; no symbol, "
                                 "no block, no corroboration - could be a planter, a kerb, a pergola beam or furniture",
            "participates_in_a_physical_boundary": "the MB wardrobe chain touches the walls at both ends and would "
                                                   "split the site (CHANGES_AREA) if it were a boundary: wardrobe "
                                                   "zone vs room - which is exactly why its role matters for trades"}}


def sf3_investigation(inp, res):
    roles = res["roles"]["roles"]
    occ = defaultdict(list)
    for p in inp.parts:
        if p.lineage and p.lineage[-1].block_name and p.lineage[-1].block_name.endswith("$SF3"):
            occ[p.identity.instance_handles[0]].append(p)
    out = {}
    sigs = {}
    for o, ps in sorted(occ.items()):
        bb = [RM.exact_bbox(p.kind, p.geometry) for p in ps]
        ext = (min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb))
        lens = sorted(round(math.hypot(p.geometry[2] - p.geometry[0], p.geometry[3] - p.geometry[1]), 4)
                      for p in ps if p.kind == "SEGMENT")
        radii = sorted(round(p.geometry[2], 4) for p in ps if p.kind == "ARC")
        sigs[o] = (tuple(lens), tuple(radii))
        hit = sorted({s for p in ps for s in res["probe_sites"].get(p.identity.key, [])})
        touches_wall = any(res["roles"]["grades"].get(k) for k in ())
        out[o] = {"parts": len(ps), "kinds": dict(Counter(p.kind for p in ps)), "layer": sorted({p.layer for p in ps}),
                  "block": ps[0].lineage[-1].block_name, "xref_library": ps[0].lineage[-1].block_name.split("$")[0],
                  "extent_native": [round(v, 3) for v in ext],
                  "size_mm": sorted([round((ext[2] - ext[0]) * inp.unit_native_to_mm, 1),
                                     round((ext[3] - ext[1]) * inp.unit_native_to_mm, 1)]),
                  "roles": dict(Counter(roles[p.identity.key].role for p in ps)), "sites_touched": hit}
    names = sorted(out)
    same = {f"{a}~{b}": sigs[a] == sigs[b] for i, a in enumerate(names) for b in names[i + 1:]}
    dup = [k for k, v in same.items() if v and out[k.split("~")[0]]["extent_native"] == out[k.split("~")[1]]["extent_native"]]
    lib = Counter((p.lineage[-1].block_name, roles[p.identity.key].role, roles[p.identity.key].rule_id)
                  for p in inp.parts if p.lineage and p.lineage[-1].block_name and
                  p.lineage[-1].block_name.startswith("MY BLOCKS$"))
    return {"occurrences": out, "geometrically_identical_pairs": same, "exact_duplicate_placements": dup,
            "same_library_blocks_in_region": {" | ".join(k): n for k, n in sorted(lib.items())},
            "evidence_for_furniture": ["no wall / column / glazing layer in the block (NO_BOUNDARY_LAYER)",
                                       "12 arcs + 15 segments: cushion-like rounded outline",
                                       "about 2385 x 995 mm (size is NOT evidence on its own)",
                                       "the same bound xref library 'MY BLOCKS' holds the proven furniture block BED 3",
                                       "two of three occurrences are exact duplicates at the same placement - "
                                       "typical of a copied symbol, meaningless for a building element"],
            "evidence_against_or_missing": ["block name 'SF3' and layer 'PM' are not in the generic lexicon",
                                            "no FURNITURE-role layer or block-name token: GR-03 cannot prove it",
                                            "a closed outline inside a room: if it were a column / shaft it would "
                                            "remove floor area (CHANGES_AREA)"],
            "verdict": "ROLE_UNRESOLVED (FURNITURE_CANDIDATE, source-scoped; not applied). Not PHYSICAL_BOUNDARY: it "
                       "touches no admitted wall and cannot separate the space"}


def dim_separator_investigation(old, new, rnew):
    """The new revision's dimension-layer lines that bridge the wall network: exact cross-revision identity with
    the previous revision's WALL lines, pairing, and the door they meet."""
    old_walls = {handle(p.identity.key): p for p in old.parts if p.layer == "WALL" and not p.identity.instance_handles}
    new_keys = {handle(p.identity.key) for p in new.parts}
    gone = {h: p for h, p in old_walls.items() if h not in new_keys}
    cands = {c.source_id: o for c, o in rnew["roles"]["separator_candidates"]}
    rows = []
    for p in new.parts:
        if p.layer != "DIM" or p.kind != "SEGMENT" or p.identity.instance_handles:
            continue
        g = p.geometry
        a, b = (g[0], g[1]), (g[2], g[3])
        same = []
        for h, w in gone.items():
            wa, wb = (w.geometry[0], w.geometry[1]), (w.geometry[2], w.geometry[3])
            col = abs(a[0] - b[0]) < 1e-6 and abs(wa[0] - wb[0]) < 1e-6 and abs(a[0] - wa[0]) < 1e-6 or \
                abs(a[1] - b[1]) < 1e-6 and abs(wa[1] - wb[1]) < 1e-6 and abs(a[1] - wa[1]) < 1e-6
            if col:
                lo = (min(a[0], b[0], ), min(a[1], b[1]))
                if (min(wa[0], wb[0]) - 1e-6 <= lo[0] <= max(wa[0], wb[0]) + 1e-6 and
                        min(wa[1], wb[1]) - 1e-6 <= lo[1] <= max(wa[1], wb[1]) + 1e-6):
                    same.append({"old_wall": "H" + h, "old_geometry": [round(v, 1) for v in w.geometry]})
        if same:
            rows.append({"new_dim_line": "H" + handle(p.identity.key), "geometry": [round(v, 1) for v in g],
                         "on_old_wall_face": same, "bridges_network_now": p.identity.key in cands})
    return {"removed_old_wall_lines": sorted("H" + h for h in gone),
            "dim_lines_on_removed_wall_faces": rows,
            "pairing": "7116 / 7117 at x = 109623.1 / 109608.1 and 7118 / 7119 at x = 109928.1 / 109943.1: two pairs "
                       "15 units (150 mm) apart - the two faces of a 150 mm wall each",
            "door": "door I2044 (proven symbol, hinge at 109608.1 / 14949.7) keeps its jamb cap H2045 between 7116 and "
                    "7117; with those lines excluded the cap touches nothing and is not admitted: the door closure "
                    "becomes UNRESOLVED",
            "wall_network": "new free wall ends exactly where the DIM lines meet the network (H471, H477, H486, H488, "
                            "H2296, H2297)"}


def hypothesis_dim_walls(new, unrealised, dim_keys):
    """HYPOTHESIS ONLY: the topology if the DIM-layer lines on the removed wall faces were walls (a reviewed,
    part-scoped claim applied in a sandbox). Never registered as authority."""
    c = RA.SourceLayerRoleClaim("HYPOTHESIS-DIM-AS-WALL", new.revision.revision_id, new.revision.anchor_sha256,
                                "DIM", "EFFECTIVE", GR.TOPOLOGY_BOUNDARY, ("cross-revision identity",), "HYPOTHESIS",
                                RA.REVIEWED, part_keys=tuple(dim_keys))
    r = LAB.run(new, unrealised, claims=[c])
    r["_unit2"] = (new.unit_native_to_mm ** 2) / 1e6
    rooms = [{"site": s["site_id"], "stamps": list(LAB.stamps(s).values()), "area_m2": round(s["area_m2"], 4),
              "physical_status": s["physical_status"], "issues": s["issues"]}
             for s in sorted(r["sites"], key=lambda z: -z["area"]) if s["labels"]]
    rows = rows_r89(r, new.revision.revision_id)
    return {"state": "HYPOTHESIS_NOT_RELEASED", "claim_parts": [handle(k) for k in dim_keys],
            "labelled_physical_sites": rooms,
            "row_states_if_confirmed": {k: v["r8_9_state"] for k, v in rows.items()}}


# ====================================================================== registers
def run_all(work):
    inps = LAB.inputs(Path(work))
    all_new = inps.pop("_NEW_ALL_PARTS")
    res = {k: LAB.run(v, LAB.UNREALISED[k]) for k, v in inps.items()}
    for k, r in res.items():
        r["_unit2"] = (inps[k].unit_native_to_mm ** 2) / 1e6
    return inps, res, all_new


def registers(inps, res, all_new):
    names = LAB.apartment_names()
    frames = json.loads((ROOT / "tests/r8_7/registers/REGION_CLASSIFICATION_NEW_REVISION.json").read_text())["frames"]
    new, rnew = inps["NEW_K2"], res["NEW_K2"]
    regs = {}
    regs["EFFECTIVE_LAYER_REGISTER"] = {
        "SCHEMA": "URBAN_R8_9_EFFECTIVE_LAYER_REGISTER_V1",
        "rule": "AutoCAD layer-0 semantics through the whole insert chain; source layer kept; role reads the "
                "effective layer (canonical_input.effective_layer)",
        "r8_8_gap": "CONFIRMED in code: geometry_role.admit() took an optional insert_layers map that TS01 never "
                    "supplied, and it looked at the top-level insert only (no nesting); fixed at the canonical record",
        "runs": {k: {"records_by_authority": dict(Counter(CI.effective_layer(p)[1] for p in v.parts)),
                     "texts_by_authority": dict(Counter(CI.effective_layer(t)[1] for t in v.texts)),
                     "layer0_children_inside_inserts": sum(1 for p in v.parts if p.layer == "0" and
                                                           p.identity.instance_handles),
                     "effective_differs_from_source": sum(1 for p in v.parts if CI.effective_layer(p)[0] != p.layer)}
                 for k, v in inps.items()},
        "qortuba_effect": "none in either revision: no layer-0 child inside an insert in the selected region (the gap "
                          "was latent here; it would decide roles in a drawing whose blocks are authored on layer 0)",
        "tests": "tests/r8_9/test_r8_9_effective_layer.py (A-F on K1 and K2)"}
    regs["ROLE_AUTHORITY_POLICY"] = {
        "SCHEMA": "URBAN_R8_9_ROLE_AUTHORITY_POLICY_V1", "role_authority": RA.policy_record(),
        "geometry_role_policy": {"id": GR.POLICY_ID, "digest": GR.policy_record()["digest"]},
        "grades_per_run": {k: dict(Counter(g["grade"] for g in r["roles"]["grades"].values())) for k, r in res.items()},
        "unconnected_candidates": {k: [handle(x) for x, g in r["roles"]["grades"].items() if g["grade"] == RA.CANDIDATE]
                                   for k, r in res.items()},
        "separator_candidates": {k: dict(Counter(o for _, o in r["roles"]["separator_candidates"])) for k, r in res.items()},
        "site_consequences": {k: {s["site_id"]: s["consequence"] for s in r["sites"] if s.get("consequence")}
                              for k, r in res.items()}}
    fi = firntur_investigation(new, rnew, all_new, frames)
    fi_old = firntur_investigation(inps["OLD_K1"], res["OLD_K1"], [], {})
    sf = sf3_investigation(new, rnew)
    dim = dim_separator_investigation(inps["OLD_K1"], new, rnew)
    dim_keys = [p.identity.key for p in new.parts if p.layer == "DIM" and p.kind == "SEGMENT"
                and "H" + handle(p.identity.key) in {r["new_dim_line"] for r in dim["dim_lines_on_removed_wall_faces"]}]
    hyp = hypothesis_dim_walls(new, LAB.UNREALISED["NEW_K2"], dim_keys)
    no_xref = [u for u in LAB.UNREALISED["NEW_K2"] if u["code"] not in XREF_CODES]
    r_nx = LAB.run(new, no_xref)
    r_nx["_unit2"] = (new.unit_native_to_mm ** 2) / 1e6
    rows_nx = rows_r89(r_nx, new.revision.revision_id)
    hyp_nx = hypothesis_dim_walls(new, no_xref, dim_keys)
    xrefs = [u for u in LAB.UNREALISED["NEW_K2"] if u["code"] in XREF_CODES]

    def claim(cid, rev, layer, role, ev, keys=(), state=RA.SOURCE_EVIDENCE_CANDIDATE):
        return {"claim_id": cid, "source_revision_id": rev.revision_id, "source_anchor_sha256": rev.anchor_sha256,
                "layer": layer, "layer_basis": "EFFECTIVE", "role": role, "evidence": ev, "authority": "SOURCE_STRUCTURE",
                "review_state": state, "scope": C.REGION_ID, "version": 1, "supersedes": None, "inherits_to": [],
                "part_keys": [handle(k) for k in keys], "applied": state == RA.REVIEWED}
    regs["SOURCE_LAYER_ROLE_CLAIMS"] = {
        "SCHEMA": "URBAN_R8_9_SOURCE_LAYER_ROLE_CLAIMS_V1",
        "rule": "a claim names ONE source revision and its anchor hash; it never travels to another project or revision "
                "without an explicit inheritance; a candidate claim never changes a role; a claim changes role "
                "authority only, never geometry",
        "claims": [
            claim("QORTUBA-NEW-FIRNTUR-MB-JOINERY", new.revision, "FIRNTUR", GR.FURNITURE,
                  ["rectangle-with-diagonal wardrobe symbols 600 mm deep", "same token hosts proven furniture "
                   "(MY BLOCKS$0$FIRNTUR / BED 3) in this source"],
                  [p.identity.key for p in new.parts if p.layer == "FIRNTUR" and handle(p.identity.key) in fi["in_master_bedroom"]]),
            claim("QORTUBA-NEW-SF3-FURNITURE", new.revision, "MY BLOCKS$0$PM", GR.FURNITURE,
                  sf["evidence_for_furniture"]),
            claim("QORTUBA-NEW-DIM-LINES-ARE-WALLS", new.revision, "DIM", GR.TOPOLOGY_BOUNDARY,
                  ["exact geometric identity with the previous revision's WALL lines", "150 mm face pairs",
                   "bridge the wall network at both ends", "door I2044 and its jamb cap remain"], dim_keys)],
        "firntur_old_revision": "the old revision has its own FIRNTUR parts (same pattern); a claim on the new revision "
                                "does not apply to it (test_r8_9_role_authority: source scope)"}
    regs["BLOCK_OCCURRENCE_CONTEXT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_9_BLOCK_OCCURRENCE_CONTEXT_V1",
        "rule": "BUILDING_ASSEMBLY only from boundary-layer children + one independent corroboration (nested door, "
                "room-label text child, dimension child, reviewed claim); never by size; unknown fails closed",
        "runs": {k: {"contexts": dict(Counter(v["context"] for v in r["roles"]["occurrence_contexts"].values())),
                     "occurrences": {o: v for o, v in sorted(r["roles"]["occurrence_contexts"].items())}}
                 for k, r in res.items()}}
    regs["UNREALISED_ENTITY_REGISTER"] = {
        "SCHEMA": "URBAN_R8_9_UNREALISED_ENTITY_REGISTER_V1",
        "rule": "excluded ONLY on positive evidence (frame / presentation occurrence, own placement, occurrence fully "
                "outside); absence of realised same-layer peers proves nothing",
        "r8_8_disposition_retired": "NOT_IN_ANY_BOUNDED_SITE_BY_LAYER_EVIDENCE",
        "runs": {k: {"blocking": dict(Counter(b["disposition"] for b in r["unrealised"]["blocking_input"])),
                     "recorded": dict(Counter(b["disposition"] for b in r["unrealised"]["recorded"]))}
                 for k, r in res.items()},
        "office_name_regions": {k: [{"obs": u["obs_id"], "extent": u.get("extent"), "basis": u.get("extent_basis"),
                                     "disposition": u["disposition"]} for u in r["unrealised"]["recorded"]
                                    if u.get("layer") == "OFFICE NAME" and not u.get("path")]
                                for k, r in res.items() if k != "NEW_K2"},
        "office_name_regions_new_count": sum(1 for u in rnew["unrealised"]["recorded"] if u.get("layer") == "OFFICE NAME"),
        "proof": "ACIS bodies: vertices + B-spline control points through the body transform (convex hull) - all inside "
                 "the sheet's title / logo strip (y 13878-13958) below every apartment room (y >= 14494); the K1 decode "
                 "(old DWG) and the new DXF give identical extents for the 37 shared handles"}
    tx = {k: Counter((a.role, a.rule_id) for a in r["roles"]["text_roles"].values()) for k, r in res.items()}
    regs["TEXT_ROLE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_9_TEXT_ROLE_REGISTER_V1", "policy": TX.policy_record(),
        "runs": {k: {" | ".join(kk): n for kk, n in sorted(v.items())} for k, v in tx.items()},
        "established_room_tags_new": sorted({a.evidence["occurrence"] for a in rnew["roles"]["text_roles"].values()
                                              if a.role == TX.ROOM_LABEL_ESTABLISHED}),
        "paintry": "PAINTRY (misspelled) is established by TR-04: same tag composition as the source's lexicon-"
                   "established tags; the misspelling is never added to the vocabulary"}
    regs["SEMANTIC_ZONE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_9_SEMANTIC_ZONE_REGISTER_V1", "policy": SZ.POLICY_ID,
        "runs": {k: {"site_states": dict(Counter(v["state"] for v in r["semantic"]["sites"].values())),
                     "zones": r["semantic"]["zones"],
                     "trade_regions_floor_finish": SZ.trade_regions(r["semantic"], r, "FLOOR_FINISH")}
                 for k, r in res.items()}}
    regs["THRESHOLD_SITE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_9_THRESHOLD_SITE_REGISTER_V1",
        "rule": "an opening site is its own physical object; its trade allocation is TRADE_RULE_REQUIRED",
        "runs": {k: [dict(t, area_m2=round(m2(inps[k], t["area"]), 6)) for t in r["semantic"]["thresholds"]]
                 for k, r in res.items()},
        "qs01_method_difference": "legacy QS01 wet floor 17.8625 vs TS01 17.7425: one 0.12 m2 door-threshold strip; "
                                  "TS01 keeps it as a threshold site and does not move it into the bath"}
    audits = {k: r["roles"]["door_audit"] for k, r in res.items()}
    needed = sorted({round(a["accepted_ratio_needed"], 6) for au in audits.values() for a in au.values()
                     if a["accepted_ratio_needed"] is not None})
    regs["DOOR_CLOSURE_AUDIT"] = {
        "SCHEMA": "URBAN_R8_9_DOOR_CLOSURE_AUDIT_V1", "policy_ratio": TP.JAMB_ALLOWANCE_RATIO, "runs": audits,
        "accepted_ratios_needed": needed,
        "rejected_hypotheses_that_would_close_within_a_full_radius": sum(
            1 for au in audits.values() for a in au.values() if a["rejected_ratio_needed"] is not None),
        "verdict": "NEEDS_MORE_EVIDENCE: on this drawing family every accepted closure needs 1/15 of the leaf radius "
                   "(the door block's own frame inset) and no rejected hypothesis closes even at a full radius, so the "
                   "0.25 ratio decides nothing here; it is not shown OVERBROAD, not shown generic. Recommendation: "
                   "derive the reach from the door symbol's own geometry (its frame / jamb parts) on a second family"}
    regs["TOPOLOGY_CROSSCHECK_V2"] = {
        "SCHEMA": "URBAN_R8_9_TOPOLOGY_CROSSCHECK_V2", "check": XC.CHECK_ID,
        "before_R8_9": "R8.8 V1 counted a site as AGREES when ANY of four grid phases agreed (old K1/K2 75, new 67)",
        "runs": {k: {"state": r["crosscheck"]["state"], "counts": r["crosscheck"]["counts"],
                     "inconclusive": r["crosscheck"]["inconclusive"]} for k, r in res.items()},
        "invalid_polygon_policy": "CHECK_INPUT_INVALID; buffer(0) removed; interior stubs removed exactly"}
    rows = {k: rows_r89(r, inps[k].revision.revision_id) for k, r in res.items()}
    pub = lambda s: LAB.public_site(s, names) | {"physical_status": s["physical_status"],
                                                 "physical_issues": s["physical_issues"],
                                                 "semantic_issues": s["semantic_issues"],
                                                 "trade_issues": s["trade_issues"],
                                                 "trade_notes": s.get("trade_notes", []),
                                                 "authority_grade": s.get("authority_grade"),
                                                 "interior_stub_source_ids": s["interior_stub_source_ids"]}
    multi = {}
    for label, word in (("A_HALL_BED_BATH", "HALL"), ("B_MB_ROOM_DRESS", "DRESS")):
        s = next(x for x in rnew["sites"] if any(lt["value"] == word for lt in x["label_texts"]))
        multi[label] = {"site": s["site_id"], "area_m2": round(s["area_m2"], 4), "stamps": list(LAB.stamps(s).values()),
                        "semantic_state": rnew["semantic"]["sites"][s["site_id"]]["state"],
                        "physical_issues": s["physical_issues"], "consequence": s.get("consequence"),
                        "old_revision": None}
    multi["A_HALL_BED_BATH"]["interpretation"] = (
        SZ.BOUNDARY_MISSING + ": the old revision's BATH / BED.ROOM walls are drawn in the new revision on the DIM "
        "layer (exact geometric identity, 150 mm face pairs, bridging the network); an excluded separator, not an open "
        "plan. Owner decision needed: are these lines walls?")
    multi["B_MB_ROOM_DRESS"]["interpretation"] = (
        SZ.MULTI_UNRESOLVED + " (identical in both revisions): no wall, door or finish line separates DRESS from "
        "M.B.ROOM; the wardrobe joinery (FIRNTUR) lines touch the walls; no subdivision evidence. Legitimately one "
        "connected physical space with two zones; the zone boundary is not authored")
    regs["QORTUBA_R8_9_STATUS"] = {
        "SCHEMA": "URBAN_R8_9_QORTUBA_STATUS_V1", "revision": C.REV_NEW_ID, "variant": "PLAN_VARIANT_4_SELECTED",
        "physical_sites": [pub(s) for s in sorted(rnew["sites"], key=lambda z: -z["area"]) if s["labels"] or
                           s["area_m2"] >= 1.0],
        "semantic_zones": rnew["semantic"]["zones"],
        "trade_zone_blockers": SZ.trade_regions(rnew["semantic"], rnew, "FLOOR_FINISH"),
        "unknown_roles": LAB.role_summary(rnew).get("unknown"),
        "unrealised_entity_blockers": rnew["unrealised"]["blocking_input"],
        "doors": rnew["openings"], "thresholds": rnew["semantic"]["thresholds"],
        "rows": {k: {r: {"state": v["r8_9_state"], "value": v["value"], "blockers": v["blockers"],
                         "basis": v["basis"], "pending_trade_rules": v["pending_trade_rules"]}
                     for r, v in rows[k].items()} for k in rows},
        "old_revision_rows_regression": {r: [rows["OLD_K1"][r]["state"], rows["OLD_K1"][r]["value"]] for r in ROWS},
        "multi_label_investigation": multi, "firntur": fi, "firntur_old_revision_parts": fi_old["parts_in_region"],
        "sf3": sf, "dim_layer_separators": dim, "hypothesis_dim_lines_are_walls": hyp,
        "attached_xrefs_not_in_source": {
            "records": xrefs,
            "facts": {"16783": "INSERT of xref 'block' (..\\Autocad blocks\\block.dwg) at (0, 0), scale 2.54, layer DIM",
                      "17716": "INSERT of xref 'blocks and details of solid facades' (Arabic file name) at (0, 0), "
                               "scale 0.1, layer DIM"},
            "why_blocking": "the xref drawings are not in the file: their content can lie anywhere (R8.8 skipped them "
                            "silently because their occurrence had no realised parts - absence, not evidence)",
            "old_revision": "no xref in the old revision"},
        "if_xrefs_confirmed_outside_the_plan": {
            "state": "HYPOTHESIS_NOT_RELEASED",
            "rows": {r: {"state": v["r8_9_state"], "value": v["value"]} for r, v in rows_nx.items()},
            "and_if_dim_lines_are_walls": hyp_nx["row_states_if_confirmed"],
            "labelled_physical_sites_if_dim_lines_are_walls": hyp_nx["labelled_physical_sites"]}}
    return regs, rows


def main(work, regdir):
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    inps, res, all_new = run_all(work)
    regs, rows = registers(inps, res, all_new)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, default=str) + "\n")
    print(json.dumps({k: {r: (v["r8_9_state"], v["value"]) for r, v in rows[k].items()} for k in rows}, indent=1))
    return regs, res


if __name__ == "__main__":
    main(*sys.argv[1:3])
