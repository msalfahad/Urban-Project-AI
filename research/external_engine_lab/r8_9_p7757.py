"""R8.9 lab: P7757 as a SECOND DRAWING FAMILY (shadow; no quantity; no published output changes).

    python3 research/external_engine_lab/r8_9_p7757.py <register_dir>

The P7757 native unit is an open owner action: no unit is assumed. Everything that does not need the physical
authored band (eps_r) is run: canonical admission, effective layers, role evidence, occurrence contexts, text roles,
unrealised-entity accounting, door closures (eps_n only), numeric checks and an UNCERTIFIED eps_n-only arrangement.
The TS01 certificate is UNIT_UNRESOLVED. Unit evidence is collected and classified, never adopted.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import canonical_build as CB, canonical_input as CI, geometry_role as GR       # noqa: E402
from engine.source import region_membership as RM, role_authority as RA, room_topology as RT       # noqa: E402
from engine.source import text_role as TX, topology as T, topology_policy as TP                    # noqa: E402
from engine.source.cad import kernel, libredwg_map as L                                            # noqa: E402

DECODE = ROOT / "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
DWG_SHA = "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3"
REV = CI.SourceRevision("P7757_REV_DECODED", CI.EXACT_SOURCE, DWG_SHA, None, "SECOND_FAMILY_SHADOW")


def build():
    dec = json.loads(DECODE.read_text())
    doc = L.to_document(dec)
    real = kernel.realise(doc)
    k = CB.K1(REV.revision_id, dec, doc, real)
    parts, texts, dims = k.parts(), k.texts(), k.dimensions()
    boxes = [b for b in (RM.exact_bbox(p.kind, p.geometry) for p in parts) if b]
    ext = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    inp = CB.assemble(REV, "P7757:MODEL_SPACE:WHOLE", ext, "MF:P7757", None, None, parts, texts, dims,
                      notes={"route": "K1", "insunits": dec.get("HEADER", {}).get("INSUNITS"),
                             "dimlfac": dec.get("HEADER", {}).get("DIMLFAC")})
    unreal = [{"code": f.code, "obs_id": f.obs_id, "layer": None, "path": [p.split(":", 1)[1].split("[")[0]
                                                                          for p in f.instance_path]}
              for f in real.findings]
    return dec, inp, unreal


def unit_evidence(dec, inp, adm):
    hdr = dec.get("HEADER", {})
    radii = sorted(d["radius"] for d in adm["doors"].values())
    ratios = []
    for d in inp.dimensions:
        if d.placed_points and d.measurement:
            (x1, y1), (x2, y2) = d.placed_points
            g = math.hypot(x2 - x1, y2 - y1)
            if g > 0:
                ratios.append(round(d.measurement / g, 6))
    rc = Counter(ratios).most_common(5)
    med = radii[len(radii) // 2] if radii else None
    return {"INSUNITS": hdr.get("INSUNITS"), "INSUNITS_meaning": "4 = millimetres (a DECLARATION, not a confirmation)",
            "DIMLFAC": hdr.get("DIMLFAC"),
            "DIMLFAC_meaning": "printed dimension text = measured length x DIMLFAC: 0.1 means the sheet prints one tenth "
                               "of the drawn length (e.g. drawn in mm, printed in cm)",
            "door_leaf_radii_native": {"count": len(radii), "median": med, "min": radii[0] if radii else None,
                                       "max": radii[-1] if radii else None},
            "door_radius_reading": None if med is None else
            f"median {med:.1f} native units: {med:.0f} mm if mm, {med * 10:.0f} mm if cm",
            "dimension_measurement_over_placed_length": rc,
            "classification": "SOURCE_UNIT_CANDIDATE (mm): the declaration, the door leaves and DIMLFAC 0.1 are "
                              "consistent with millimetres; consistency is not confirmation - the unit claim policy "
                              "requires an owner-confirmed claim",
            "state": "UNIT_UNRESOLVED"}


def main(regdir):
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    dec, inp, unreal = build()
    v = CI.validate(inp, RT.TS01, expected_revision_id=REV.revision_id, selected_region_id=inp.region_id)
    m = RT.max_abs_coordinate(inp.parts)
    eps_n = TP.eps_noise(m)
    tol = TP.tolerances(m, inp.unit_native_to_mm)
    adm = GR.admit(inp, frame_insert=None, eps=eps_n)
    ctx = RA.occurrence_contexts(inp, adm, None)
    assemblies = frozenset(o for o, x in ctx.items() if x["context"] == RA.BUILDING_ASSEMBLY)
    if assemblies:
        adm = GR.admit(inp, frame_insert=None, eps=eps_n, assemblies=assemblies)
    roles = adm["roles"]
    troles = TX.classify(inp)
    items = [T.BoundaryItem(p.identity.key, p.kind, tuple(p.geometry), roles[p.identity.key].role)
             for p in sorted(inp.parts, key=lambda q: q.identity.key or "")
             if p.visibility == CI.VISIBLE and roles[p.identity.key].role in GR.TOPOLOGY_ADMITTED
             and p.kind in ("SEGMENT", "ARC", "CIRCLE")]
    closures, status = T.opening_closures(adm["doors"], items, eps_n)
    audit = T.opening_audit(adm["doors"], items, eps_n)
    arr = T.build(items + closures, eps_n)
    faces = T.sites_of(arr, REV.revision_id, inp.region_id)
    d = T.end_distances(items, 1e6 * eps_n)
    dec_hist = Counter("0" if x == 0 else f"1e{math.floor(math.log10(x / eps_n))} eps_n" for x in d)
    disp = Counter()
    for u in unreal:
        path = u["path"]
        disp[("IN_OCCURRENCE" if path else "MODEL_SPACE", u["code"])] += 1
    cand = {}
    for lay in ("W", "D", "TOI", "ST", "5", "1", "2", "LEVEL"):
        ps = [p for p in inp.parts if CI.effective_layer(p)[0] == lay]
        cand[lay] = {"parts": len(ps), "kinds": dict(Counter(p.kind for p in ps)),
                     "in_inserts": sum(1 for p in ps if p.identity.instance_handles),
                     "blocks": dict(Counter(p.lineage[-1].block_name for p in ps if p.lineage).most_common(6))}
    reg = {
        "SCHEMA": "URBAN_R8_9_P7757_SHADOW_V1", "purpose": "second drawing family: does the R8.9 machinery survive "
        "another drafting style? NOT quantities; no P7757 published output changes",
        "source": {"decode": str(DECODE.relative_to(ROOT)), "dwg_sha256": DWG_SHA, "route": "K1 (pinned LibreDWG decode)"},
        "canonical_input": {"parts": len(inp.parts), "texts": len(inp.texts), "dimensions": len(inp.dimensions),
                            "validation": v["state"], "missing": v.get("missing")},
        "effective_layers": {"by_authority": dict(Counter(CI.effective_layer(p)[1] for p in inp.parts)),
                             "layer0_children_inside_inserts": sum(1 for p in inp.parts if p.layer == "0" and
                                                                   p.identity.instance_handles),
                             "differs_from_source": sum(1 for p in inp.parts if CI.effective_layer(p)[0] != p.layer)},
        "roles": {"by_rule": {f"{r} | {k}": n for (r, k), n in sorted(Counter((a.role, a.rule_id)
                                                                              for a in roles.values()).items())},
                  "unknown_by_layer": dict(Counter(CI.effective_layer(p)[0] for p in inp.parts
                                                   if roles.get(p.identity.key) and
                                                   roles[p.identity.key].role == GR.UNKNOWN_PHYSICAL).most_common(15))},
        "occurrence_contexts": dict(Counter(x["context"] for x in ctx.values())),
        "text_roles": {f"{r} | {k}": n for (r, k), n in sorted(Counter((a.role, a.rule_id)
                                                                       for a in troles.values()).items())},
        "unrealised_entities": {" | ".join(k): n for k, n in sorted(disp.items())},
        "doors": {"proven_signatures": len(adm["doors"]), "closed": sum(1 for s in status.values()
                                                                        if s.get("state") == "CLOSED"),
                  "unresolved": sum(1 for s in status.values() if s.get("state") != "CLOSED"),
                  "accepted_ratios_needed": dict(Counter(round(a["accepted_ratio_needed"], 4) for a in audit.values()
                                                         if a["accepted_ratio_needed"] is not None).most_common(8)),
                  "rejected_would_close_within_a_radius": sum(1 for a in audit.values()
                                                              if a["rejected_ratio_needed"] is not None)},
        "numeric": {"max_abs_coordinate": m, "eps_n": eps_n, "end_to_curve_distance_decades": dict(dec_hist)},
        "uncertified_numeric_topology": {"faces_at_eps_n": len(faces), "state": "UNCERTIFIED: no eps_r without a unit"},
        "unit": unit_evidence(dec, inp, adm),
        "source_scoped_layer_candidates": {
            "layers": cand,
            "reading": "single-letter / numeric layer names (W, D, 5, 1, 2) and TOI / ST: the generic exact-token "
                       "lexicon admits none of them, so about 95% of the parts are UNKNOWN and TS01 fails closed. The "
                       "door blocks D315 / D120 / D115 sit on layer D. Candidate claims for THIS source only "
                       "(W -> WALL, D -> DOOR, TOI -> SANITARY, ST -> STAIR) need the evidence paths of "
                       "role_authority (paired faces, network connectivity, door signatures inside D blocks) and a "
                       "review; they are NOT added to the Urban lexicon",
            "state": "SOURCE_EVIDENCE_CANDIDATE (not applied)"},
        "second_family_findings": [
            "effective layer decides 3328 parts (layer-0 children of inserts): the R8.8 gap would have mattered here",
            "the generic layer lexicon does not survive this drafting style: source-scoped role claims are the "
            "mechanism, not a bigger generic lexicon",
            "no door is proven: the door symbols are blocks named by size code (D315 ...) on layer D",
            "text roles survive: 60 room tags established structurally (26 TR-03 + 34 TR-04 family), 55 tag "
            "candidates without corroboration",
            "numeric separation is clean: end-to-curve decisions are 0 or ~1e5 x eps_n, none near eps_n",
            "267 dimensions store 0.1 x their geometric length (= DIMLFAC): consistent with mm drawn / cm printed"],
        "ts01_certificate": tol["reason"] and "UNIT_UNRESOLVED",
        "owner_question_prepared_not_asked": {
            "question": "P7757: what is the native drawing unit of the architectural DWG 7f61f3ac (one drawing unit = "
                        "how many millimetres)? Choices: mm / cm / m / other.",
            "why_not_asked_now": "the second-family shadow needs no physical value; ask only when P7757 quantities are "
                                 "in scope"}}
    (regdir / "P7757_R8_9_SHADOW.json").write_text(json.dumps(reg, indent=1, default=str) + "\n")
    print(json.dumps({k: reg[k] for k in ("canonical_input", "occurrence_contexts", "doors", "ts01_certificate")},
                     indent=1, default=str))
    return reg


if __name__ == "__main__":
    main(sys.argv[1])
