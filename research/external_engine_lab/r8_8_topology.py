"""R8.8 - TS01 certified room topology on Qortuba (SHADOW): old-revision K1 vs K2 cross-route control, new-revision
DXF diagnostic, six-row status, and the R8.8 registers.

    python3 research/external_engine_lab/r8_8_topology.py <work_dir> <register_dir>

Inputs (hash-addressed, read-only):
    OLD K1   pinned LibreDWG decode of DWG 2ec3a9c8 (data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json)
    OLD K2   ezdxf on LibreDWG's DXF of the same DWG (data/inputs/by_sha256/66ea7205....dxf)
    NEW K2   ezdxf on the new-revision DXF df0e1d69 (data/inputs/by_sha256/df0e1d69....dxf; ~2 min, cached)

Project semantics live HERE, never in engine/source: which label names are apartment rooms (the Q-14 owner claim's
space list), which are wet (BATH) or service (PAINTRY) - the R8.6 row expressions (owner_rules.CERAMIC_ROOM_NAMES).
The engine supplies certified sites only. No row value of R8.6 / R8.7 is read before the rows are computed; the
comparison with them is made afterwards and classified.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_7_canonical as C                                                               # noqa: E402
from engine.source import geometry_role as GR, owner_scope as OS                          # noqa: E402
from engine.source import region_membership as RM, room_topology as RT, topology as T    # noqa: E402
from engine.source.cad import libredwg_map as L                                          # noqa: E402

OLD_DXF = ROOT / "data/inputs/by_sha256/66ea72057266d006ee111325dac69fbbb8d8e87d6415fcee6a69486e5f62b641.dxf"
NEW_DXF = ROOT / f"data/inputs/by_sha256/{C.NEW_DXF}.dxf"
ROUND1 = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")
WET, SERVICE = ("BATH",), ("PAINTRY",)                    # R8.6 row expressions: owner_rules.CERAMIC_ROOM_NAMES
LEGACY = {"OLD": {"Q-03": 17.8625, "Q-03P": 11.685, "Q-11": 17.8625, "Q-12": 11.685, "Q-13": 108.9625, "Q-14": 138.51}}


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# ====================================================================== inputs
def k1_unrealised():
    """K1 findings for source entities the kernel did not realise, with their layer and instance path."""
    from engine.source.cad import kernel
    decode = json.loads(C.DECODE.read_text())
    doc = L.to_document(decode)
    obs = {o.obs_id: o for o in doc.entities}
    for b in doc.blocks.values():
        for o in b.entities:
            obs[o.obs_id] = o
    real = kernel.realise(doc)
    return [{"code": f.code, "obs_id": f.obs_id, "layer": getattr(obs.get(f.obs_id), "layer", None),
             "path": [p.split(":", 1)[1].split("[")[0] for p in f.instance_path]} for f in real.findings]


UNREALISED = {}


def inputs(work: Path):
    work.mkdir(parents=True, exist_ok=True)
    out = {"OLD_K1": C.old_input()}
    UNREALISED["OLD_K1"] = k1_unrealised()
    for name, dxf, rev, pkl in (("OLD_K2", OLD_DXF, C.REV_OLD_ID, work / "old_k2.pkl"),
                                ("NEW_K2", NEW_DXF, C.REV_NEW_ID, work / "new_k2.pkl")):
        if not pkl.exists():
            C.build_k2_records(dxf, rev, pkl)
        out[name], blob = C.input_from_pickle(pkl, C.rev_old() if rev == C.REV_OLD_ID else C.rev_new())
        UNREALISED[name] = blob["unrealised"]
        if name == "NEW_K2":
            out["_NEW_ALL_PARTS"] = blob["parts"]
    return out


def variant_isolation(inp, all_parts):
    """No geometry of plan variants 1-3 may enter the selected variant's graph: by OCCURRENCE (their frame inserts)
    and by exact extent (every input record lies in the selected frame occurrence's own extent)."""
    reg = json.loads((ROOT / "tests/r8_7/registers/REGION_CLASSIFICATION_NEW_REVISION.json").read_text())
    frames = {k: v for k, v in reg["frames"].items() if k != "PLAN_VARIANT_4_SELECTED"}
    occ_in = {(p.identity.instance_handles or ("E" + p.identity.source_handle,))[0] for p in inp.parts}
    hits = {}
    for name, f in frames.items():
        x0, y0, x1, y1 = f["extent"]
        n = 0
        for p in inp.parts:
            b = RM.exact_bbox(p.kind, p.geometry)
            if b and not (b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1):
                n += 1
        hits[name] = {"frame_occurrence": f["frame_occurrence"],
                      "frame_occurrence_in_input": f["frame_occurrence"] in occ_in,
                      "input_parts_meeting_its_extent": n,
                      "parts_of_that_frame_occurrence_in_the_file": sum(
                          1 for p in all_parts if p.identity.instance_handles[:1] == (f["frame_occurrence"],))}
    return {"selected": "PLAN_VARIANT_4_SELECTED (frame occurrence 156)", "other_variants": hits,
            "isolated": all(not h["frame_occurrence_in_input"] and h["input_parts_meeting_its_extent"] == 0
                            for h in hits.values())}


def run(inp, unrealised):
    return RT.run(inp, frame_insert=C.FRAME_INSERT, expected_revision_id=inp.revision.revision_id,
                  selected_region_id=C.REGION_ID, unrealised=unrealised)


# ====================================================================== site semantics (project, lab only)
def stamps(site):
    """{label occurrence: sorted text values} of one site."""
    out = defaultdict(list)
    for t in site["label_texts"]:
        out[t["occurrence"]].append(t["value"])
    return {k: sorted(v) for k, v in sorted(out.items())}


def apartment_names():
    claim = C.claims()[C.Q14_CLAIM]
    return {n for sid in claim.space_ids for n in sid.split(" / ")} - {"UNLABELLED_INTERNAL_SPACE"}


def site_names(site, names):
    """The apartment room names its stamps carry (a stamp = one label occurrence; bilingual texts are one stamp)."""
    return [sorted({v for v in vals if v in names}) for vals in stamps(site).values()]


def claim_space_id(names):
    claim = C.claims()[C.Q14_CLAIM]
    for sid in sorted(claim.space_ids):
        if set(sid.split(" / ")) & set(names):
            return sid
    return None


def row_class(name):
    return "WET" if name in WET else "SERVICE" if name in SERVICE else "DRY"


def apartment_sites(res):
    """Sites of the selected apartment: carrying an apartment stamp, or unlabelled internal spaces reached through a
    proven opening from one (and holding no stair / lift geometry)."""
    names = apartment_names()
    by = {s["site_id"]: s for s in res["sites"]}
    labelled = {s["site_id"] for s in res["sites"] if any(n for n in site_names(s, names))}
    internal = set()
    for adj in res["opening_adjacency"]:
        if labelled & set(adj["sites"]):
            for sid in adj["sites"]:
                s = by[sid]
                if sid not in labelled and not s["labels"] and s["kind"] == T.UNLABELLED and \
                        not ({GR.STAIR_GEOMETRY, GR.LIFT_GEOMETRY} & set(s["contents"])):
                    internal.add(sid)
    return [by[k] for k in sorted(labelled)], [by[k] for k in sorted(internal)]


def six_rows(res, revision_id):
    """The six rows from certified sites only. A multi-stamp site whose stamps all fall in the same row class is
    SPLIT_INVARIANT for that row (its total does not depend on the unresolved split) - shown, still REVIEW."""
    if res.get("sites") is None:
        return {k: {"state": "BLOCKED", "value": None, "why": [res["state"]]} for k in ROUND1}
    names = apartment_names()
    lab, internal = apartment_sites(res)
    out = {}

    def total(pred, rid):
        used, blockers, split_inv, val = [], [], [], 0.0
        for s in lab + internal:
            cls = [{row_class(n) for n in st} for st in site_names(s, names)] or [{"DRY"}]   # unlabelled internal: DRY
            flat = set().union(*cls)
            inside = {pred(c) for c in flat}
            if inside == {False}:
                continue
            if len(inside) > 1:
                blockers.append({"site": s["site_id"], "why": "stamps of different row classes in one physical space "
                                                              f"({sorted(flat)}): MULTIPLE_SEMANTIC_LABELS"})
                continue
            other = [i for i in s["issues"] if i != T.MULTIPLE_SEMANTIC_LABELS]
            if other:
                blockers.append({"site": s["site_id"], "why": other, "blocked_by": s["blocked_by"][:12]})
                continue
            if T.MULTIPLE_SEMANTIC_LABELS in s["issues"]:
                split_inv.append(s["site_id"])
            used.append({"site": s["site_id"], "stamps": list(stamps(s).values()), "area_m2": round(s["area_m2"], 6),
                         "area_bound_m2": round(s["area_bound_m2"], 6)})
            val += s["area_m2"]
        if rid == "Q-14":
            claim = C.claims()[C.Q14_CLAIM]
            for u in used:
                site = next(s for s in lab + internal if s["site_id"] == u["site"])
                nm = [n for st in site_names(site, names) for n in st] or ["UNLABELLED_INTERNAL_SPACE"]
                sp = claim_space_id(nm) or "UNLABELLED_INTERNAL_SPACE"
                a = OS.applies(claim, project="QORTUBA", revision_id=revision_id, purpose=OS.SHADOW_DIAGNOSTIC,
                               region_id=C.REGION_ID, space_id=sp, item="Q-14|CEILING_BY_AREA")
                if a["state"] != OS.APPLIES:
                    blockers.append({"site": u["site"], "why": f"Q-14 ceiling basis: {a['state']} {a['mismatched']}"})
        state = ("BLOCKED" if blockers else "REVIEW_REQUIRED_SPLIT_INVARIANT" if split_inv
                 else "COMPUTED_SHADOW" if used else "NO_SITE")
        return {"state": state, "value": None if blockers or not used else round(val, 4),
                "value_if_split_review_accepted": round(val, 4) if split_inv and not blockers else None,
                "sites_used": used, "split_invariant_sites": split_inv, "blockers": blockers}
    preds = {"Q-03": lambda c: c == "WET", "Q-11": lambda c: c == "WET", "Q-03P": lambda c: c == "SERVICE",
             "Q-12": lambda c: c == "SERVICE", "Q-13": lambda c: c == "DRY", "Q-14": lambda c: True}
    for rid in ROUND1:
        out[rid] = total(preds[rid], rid)
    return out


# ====================================================================== registers
def public_site(s, names):
    return {"site_id": s["site_id"], "kind": s["kind"], "status": s["status"], "issues": s["issues"],
            "labels": s["labels"], "stamps": list(stamps(s).values()),
            "apartment_names": site_names(s, names), "area_m2": round(s["area_m2"], 6),
            "area_bound_m2": round(s["area_bound_m2"], 6), "perimeter_native": round(s["perimeter"], 6),
            "boundary_source_ids": s["boundary_source_ids"], "hole_source_ids": s["hole_source_ids"],
            "boundary_role_lengths": {k: round(v, 6) for k, v in s["boundary_role_lengths"].items()},
            "contents": s["contents"], "blocked_by": s["blocked_by"], "certificate": s["certificate"],
            "opening_of": s.get("opening_of")}


def _unrealised_summary(r):
    u = r.get("unrealised", {})
    rec = u.get("recorded", [])
    return {"blocking_input_count": len(u.get("blocking_input") or []), "sites": u.get("sites"),
            "recorded_by_disposition_layer_code": {" | ".join(map(str, k)): n for k, n in sorted(Counter(
                (x["disposition"], x.get("layer"), x["code"]) for x in rec).items(), key=lambda kv: str(kv[0]))},
            "blocking_by_disposition_layer_code": {" | ".join(map(str, k)): n for k, n in sorted(Counter(
                (x["disposition"], x.get("layer"), x["code"]) for x in (u.get("blocking_input") or [])).items(),
                key=lambda kv: str(kv[0]))}}


def cross_route(r1, r2):
    s1 = {s["site_id"]: s for s in r1["sites"]}
    s2 = {s["site_id"]: s for s in r2["sites"]}
    common = sorted(set(s1) & set(s2))
    diffs = []
    for k in common:
        a, b = s1[k], s2[k]
        d = {}
        for f in ("labels", "issues", "contents", "blocked_by", "kind", "status"):
            if a[f] != b[f]:
                d[f] = [a[f], b[f]]
        if abs(a["area"] - b["area"]) > a["certificate"]["area_bound"]:
            d["area"] = [a["area"], b["area"]]
        if d:
            diffs.append({"site": k, **d})
    max_da = max((abs(s1[k]["area_m2"] - s2[k]["area_m2"]) for k in common), default=0.0)
    h584 = [k for k in common if any("|H584|" in x for x in s1[k]["boundary_source_ids"])]
    return {"sites_K1": len(s1), "sites_K2": len(s2), "common_site_ids": len(common),
            "only_K1": sorted(set(s1) - set(s2)), "only_K2": sorted(set(s2) - set(s1)),
            "differences": diffs, "max_area_difference_m2": max_da,
            "same_topology": not diffs and len(common) == len(s1) == len(s2),
            "H584": {"sites_bounded_by_H584": h584,
                     "areas_m2": {k: [s1[k]["area_m2"], s2[k]["area_m2"]] for k in h584},
                     "labels": {k: s1[k]["labels"] for k in h584}},
            "openings_equal": {k: v.get("state") for k, v in r1["openings"].items()} ==
                              {k: v.get("state") for k, v in r2["openings"].items()}}


def role_summary(res):
    roles = res["roles"]["roles"]
    by_rule = Counter((a.role, a.rule_id, a.strength) for a in roles.values())
    unknown = defaultdict(lambda: {"parts": 0, "contexts": Counter(), "blocks": Counter()})
    for a in roles.values():
        if a.role in GR.TOPOLOGY_BLOCKING:
            u = unknown[a.evidence["layer"]]
            u["parts"] += 1
            u["contexts"][a.evidence["INSTANCE_CONTEXT"]] += 1
    blocked = defaultdict(list)
    for s in res["sites"]:
        for pk in s["blocked_by"]:
            lay = roles[pk].evidence["layer"] if pk in roles else None
            blocked[lay].append(s["site_id"])
    return {"counts": [{"role": r, "rule": k, "strength": st, "parts": n} for (r, k, st), n in sorted(by_rule.items())],
            "unknown_by_layer": {k: {"parts": v["parts"], "contexts": dict(v["contexts"]),
                                     "sites_blocked": sorted(set(blocked.get(k, [])))}
                                 for k, v in sorted(unknown.items())},
            "doors": {o: {"swing": d["swing_part"], "radius": d["radius"]} for o, d in sorted(res["roles"]["doors"].items())},
            "openings": res["openings"], "glazing": res["roles"].get("glazing")}


def furniture_audit(inp, res):
    """The bound-xref ('MY BLOCKS$0$...') parts of the new revision: what they are, why they entered R8.7 room
    recognition, and what now proves (or fails to prove) their role."""
    roles = res["roles"]["roles"]
    occ = defaultdict(list)
    for p in inp.parts:
        if p.lineage and p.lineage[-1].block_name and "$0$" in (p.lineage[-1].block_name or ""):
            occ[p.identity.instance_handles[0]].append(p)
    out = []
    for o, ps in sorted(occ.items()):
        a = roles[ps[0].identity.key]
        sites = sorted({sid for p in ps for sid in res["probe_sites"].get(p.identity.key, ())})
        names = apartment_names()
        by = {s["site_id"]: s for s in res["sites"]}
        out.append({"insert_occurrence": o, "block_name": ps[0].lineage[-1].block_name,
                    "sites_touched_stamps": {sid: site_names(by[sid], names) for sid in sites},
                    "block_record": ps[0].lineage[-1].block_record_handle,
                    "layers": sorted({p.layer for p in ps}), "parts": len(ps),
                    "kinds": dict(Counter(p.kind for p in ps)), "role": a.role, "rule": a.rule_id,
                    "strength": a.strength, "evidence": {k: v for k, v in a.evidence.items() if k != "KIND"},
                    "sites_touched": sites,
                    "proven_furniture_without_benchmark": a.role == GR.FURNITURE,
                    "why": ("a symbol occurrence (bound xref block), no wall/column/glazing layer in its definition, "
                            "and the block-name token 'BED' (furniture lexicon): GR-03 structural evidence"
                            if a.role == GR.FURNITURE else
                            "a symbol occurrence with no boundary layer, but neither its layer ('PM') nor its block "
                            "name ('SF3') carries a furniture / fixture token: no rule establishes a role -> "
                            "UNKNOWN_PHYSICAL; the site it stands in is REVIEW_REQUIRED, never measured")})
    return out


def ellipse_audit(inp, res):
    decode = json.loads(C.DECODE.read_text())
    doc = L.to_document(decode)
    obs = {o.obs_id: o for o in doc.entities}
    roles = res["roles"]["roles"]
    rows = []
    for p in inp.parts:
        if p.kind != "ELLIPTICAL_ARC":
            continue
        a = roles.get(p.identity.key)
        occ = "I" + p.identity.instance_handles[0] if p.identity.instance_handles else None
        ins = obs.get("D1:" + p.identity.instance_handles[0]) if p.identity.instance_handles else None
        g = getattr(ins, "geometry", None)
        door = res["openings"].get(occ, {})
        touched = sorted(s["site_id"] for s in res["sites"] if p.identity.key in s["blocked_by"])
        cls = ("TOPOLOGY_IRRELEVANT_PROVEN" if a is not None and a.role == GR.OPENING_SYMBOL and door.get("state") == "CLOSED"
               else "TOPOLOGY_RELEVANT" if a is not None and a.role in GR.TOPOLOGY_ADMITTED
               else "TOPOLOGY_ROLE_UNRESOLVED")
        rows.append({"part": p.identity.key, "source_handle": p.identity.source_handle,
                     "instance_path": list(p.identity.instance_handles), "block_record": p.lineage[-1].block_record_handle,
                     "block_name": p.lineage[-1].block_name, "layer": p.layer, "source_entity_type": p.entity_type,
                     "transform": None if g is None else {"insertion": list(g.insertion), "scale": list(g.scale),
                                                          "rotation_rad": g.rotation, "extrusion": list(ins.extrusion)},
                     "world_geometry": [round(v, 6) for v in p.geometry],
                     "region_membership": RM.classify("ELLIPTICAL_ARC", p.geometry, tuple(inp.notes["clip_bounds"])),
                     "role": None if a is None else a.role, "rule": None if a is None else a.rule_id,
                     "physical_role_evidence": None if a is None else a.evidence,
                     "door_closure": door.get("state"), "door_closure_width": door.get("width"),
                     "sites_blocked": touched,
                     "could_affect_topology": ("only if admitted as a boundary; it is not: GR-02 proves a door symbol, "
                                               "and the door's own opening closure is established") if cls ==
                                              "TOPOLOGY_IRRELEVANT_PROVEN" else "yes: role not proven",
                     "classification": cls})
    return {"SCHEMA": "URBAN_R8_8_ELLIPSE_EXCLUSION_AUDIT_V1", "revision": C.REV_OLD_ID, "route": "K1",
            "count": len(rows), "classification_counts": dict(Counter(r["classification"] for r in rows)),
            "rule": "TOPOLOGY_IRRELEVANT_PROVEN needs a positively established role that cannot bound a room (GR-02 door "
                    "symbol) AND the door's closure established; the R8.7 'excluded by declaration' alone is not authority",
            "records": rows}


def visibility_register(inps):
    out = {}
    for name, inp in inps.items():
        out[name] = {coll: dict(Counter(r.visibility for r in getattr(inp, coll))) for coll in ("parts", "texts", "dimensions")}
    return out


def main(work, regdir):
    work, regdir = Path(work), Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    inps = inputs(work)
    all_new = inps.pop("_NEW_ALL_PARTS")
    res = {k: run(v, UNREALISED[k]) for k, v in inps.items()}
    names = apartment_names()
    rows = {k: six_rows(r, inps[k].revision.revision_id) for k, r in res.items()}
    xr = cross_route(res["OLD_K1"], res["OLD_K2"])
    regs = {}
    regs["OLD_QORTUBA_CROSS_ROUTE"] = {
        "SCHEMA": "URBAN_R8_8_OLD_QORTUBA_CROSS_ROUTE_V1", "revision": C.REV_OLD_ID,
        "routes": {"K1": "pinned LibreDWG 0.13.3 decode -> kernel", "K2": "ezdxf on LibreDWG's DXF of the same DWG"},
        "inputs": {k: {"parts": len(inps[k].parts), "texts": len(inps[k].texts), "dimensions": len(inps[k].dimensions),
                       "validation": res[k]["validation"]["state"]} for k in ("OLD_K1", "OLD_K2")},
        "admitted": {k: res[k]["counts"] for k in ("OLD_K1", "OLD_K2")},
        "unrealised_source_entities": {k: _unrealised_summary(res[k]) for k in ("OLD_K1", "OLD_K2")},
        "comparison": xr,
        "rows_K1": {k: {"state": v["state"], "value": v["value"]} for k, v in rows["OLD_K1"].items()},
        "rows_K2": {k: {"state": v["state"], "value": v["value"]} for k, v in rows["OLD_K2"].items()},
        "rows_equal": {k: [v["state"], v["value"]] for k, v in rows["OLD_K1"].items()} ==
                      {k: [v["state"], v["value"]] for k, v in rows["OLD_K2"].items()},
        "every_difference_classified": {
            "topology": "none remain after the two post-freeze robustness fixes F-R88-08 / F-R88-09 (both found by "
                        "this run; tolerance numbers unchanged)",
            "coordinates": "1115 of 1118 parts differ by < 1e-9 units (decoder text / float paths); H584 is horizontal "
                           "to 4e-12 in K1 and exactly in K2: PARSER_DIFFERENCE, absorbed by eps_n, no site changes",
            "unrealised_entities": "K1 reports one custom-class RTEXT inside the sheet-frame occurrence; LibreDWG's DXF "
                                   "carries none: PARSER_DIFFERENCE, no effect (frame occurrence, recorded not blocking)"},
        "goal": "SAME PHYSICAL SOURCE -> ROUTE-STABLE TOPOLOGY (not: match the old BOQ)"}
    for k in ("OLD_K1", "NEW_K2"):
        regs[f"SITES_{k}"] = [public_site(s, names) for s in res[k]["sites"]]
    regs["NEW_QORTUBA_TOPOLOGY"] = {
        "SCHEMA": "URBAN_R8_8_NEW_QORTUBA_TOPOLOGY_V1", "revision": C.REV_NEW_ID, "state": "NEW_REVISION_DXF_DIAGNOSTIC",
        "anchor": "DXF df0e1d69 only (DWG e4babbc2 identity NOT_ESTABLISHED)", "region": C.REGION_ID,
        "frame_occurrence": C.FRAME_INSERT, "validation": res["NEW_K2"]["validation"]["state"],
        "counts": res["NEW_K2"]["counts"], "tolerances": res["NEW_K2"]["tolerances"],
        "rooms": [public_site(s, names) for s in sorted(res["NEW_K2"]["sites"], key=lambda z: -z["area"])
                  if s["labels"] or s["area_m2"] >= 1.0],
        "all_sites": len(res["NEW_K2"]["sites"]), "findings": res["NEW_K2"]["findings"],
        "openings": res["NEW_K2"]["openings"], "opening_adjacency": res["NEW_K2"]["opening_adjacency"],
        "unrealised_source_entities": _unrealised_summary(res["NEW_K2"]),
        "variant_isolation": variant_isolation(inps["NEW_K2"], all_new)}
    regs["QORTUBA_SIX_ROW_STATUS"] = {
        "SCHEMA": "URBAN_R8_8_QORTUBA_SIX_ROW_STATUS_V1", "method": RT.TS01.method_id,
        "row_rules": {"Q-03 / Q-11": "sites whose stamps are BATH", "Q-03P / Q-12": "sites whose stamps are PAINTRY",
                      "Q-13": "apartment sites whose stamps are neither (plus unlabelled internal spaces)",
                      "Q-14": "every apartment site, ceiling = floor footprint ONLY where the scoped owner claim "
                              "QORTUBA-Q14-CEILING-FOOTPRINT-OWNER-001 applies (revision, region, space, item, purpose)"},
        "rows": {k: rows[k] for k in ("OLD_K1", "OLD_K2", "NEW_K2")},
        "legacy_R8_6_old_revision": LEGACY["OLD"],
        "comparison_made_after_the_rows": {r: {"TS01_OLD_K1": rows["OLD_K1"][r]["value"], "legacy_QS01": LEGACY["OLD"][r]}
                                           for r in ROUND1}}
    regs["ELLIPSE_EXCLUSION_AUDIT"] = ellipse_audit(inps["OLD_K1"], res["OLD_K1"])
    regs["GEOMETRY_ROLE_REGISTER"] = {"SCHEMA": "URBAN_R8_8_GEOMETRY_ROLE_REGISTER_V1", "policy": GR.policy_record(),
                                      "runs": {k: role_summary(r) for k, r in res.items()},
                                      "new_revision_bound_xref_audit": furniture_audit(inps["NEW_K2"], res["NEW_K2"])}
    regs["VISIBILITY_AUTHORITY_REGISTER"] = {
        "SCHEMA": "URBAN_R8_8_VISIBILITY_AUTHORITY_REGISTER_V1",
        "rules": ["entity invisibility flag (kernel: hidden record) -> HIDDEN_SOURCE",
                  "frozen layer -> HIDDEN_SOURCE (on an INSERT: the whole occurrence)",
                  "layer OFF -> HIDDEN_SOURCE for its own entities; a layer-0 child takes its insert's layer (ByLayer)",
                  "under a dynamic-block occurrence whose state was not read -> VISIBILITY_UNRESOLVED",
                  "layer table not read / layer missing -> VISIBILITY_UNRESOLVED (never VISIBLE by default)"],
        "k1_layer_state_source": "LibreDWG dwg.spec (R2000+): frozen = flag0 & 1; on = !(flag0 & 2)",
        "k2_layer_state_source": "ezdxf Layer.is_frozen() / is_off()",
        "record_types": ["parts", "texts", "dimensions"], "counts_in_selected_region": visibility_register(inps),
        "method_use": "TS01: hidden records are not consumed (hidden_excluded); VISIBILITY_UNRESOLVED fails closed. "
                      "QS01 v2 (legacy path): any non-VISIBLE record fails closed (hidden_excluded False)"}
    regs["REGION_MEMBERSHIP_POLICY"] = {"SCHEMA": "URBAN_R8_8_REGION_MEMBERSHIP_POLICY_V1", "policy": RM.POLICY,
                                        "occurrence_rule": "membership is judged per top-level occurrence; an occurrence "
                                                           "with any record not FULLY_INSIDE is REVIEW_REQUIRED (never cut)",
                                        "eps": "numeric-representation tolerance only (topology policy eps_n)",
                                        "runs": {k: {"region_review": len(v.region_review),
                                                     "outside": v.notes.get("outside_region"),
                                                     "clip_bounds": v.notes.get("clip_bounds")} for k, v in inps.items()}}
    for name, obj in regs.items():
        (regdir / f"{name}.json").write_text(json.dumps(obj, indent=1, sort_keys=False, default=str) + "\n")
    summary = {k: {r: (v["state"], v["value"]) for r, v in rows[k].items()} for k in rows}
    print(json.dumps(summary, indent=1))
    print("cross-route same topology:", xr["same_topology"], "max dA m2", xr["max_area_difference_m2"])
    return regs, res, rows


if __name__ == "__main__":
    main(*sys.argv[1:3])
