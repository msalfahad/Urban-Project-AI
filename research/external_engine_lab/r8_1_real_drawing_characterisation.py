"""R8.1 — read-only characterisation of K1 on the real Urban decodes.

Research lab only. Reads LibreDWG JSON decodes given on the command line,
runs the PRODUCTION D1 mapper + K1 on them, runs the existing cad_adapter on
the same bytes, and reports counts only. It changes nothing, publishes
nothing, and no number here may be used as a target in production logic.

    python3 research/external_engine_lab/r8_1_real_drawing_characterisation.py DECODE.json [...] > out.json

Sections per decode:
  field_audit      presence of every FIELD_REGISTER path on real rows
  k1               dispositions, findings by code, realised primitive counts
  cad_adapter      primitive counts, how many carry invisible=1
  arc_comparison   K1 circular arcs vs cad_adapter arcs (same centre + radius,
                   compare the mid-sweep point: a mismatch is the mirror defect)
  dynamic_blocks   anonymous *U blocks: invisible content, EED parent kinds
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import cad_adapter as CA                                   # noqa: E402
from engine.source.cad import kernel, libredwg_map as L                 # noqa: E402

TOL = 1e-3            # native units; for matching the SAME source curve across two engines only


def _h(x):
    return x[-1] if isinstance(x, list) and x else None


def field_audit(objs):
    paths = {"LINE": (19, ["start", "end", "extrusion"]), "ARC": (17, ["center", "radius", "start_angle", "end_angle", "extrusion"]),
             "CIRCLE": (18, ["center", "radius", "extrusion"]), "LWPOLYLINE": (77, ["points", "bulges", "flag", "extrusion", "elevation"]),
             "INSERT": (7, ["ins_pt", "scale", "rotation", "extrusion", "block_header"]),
             "ATTRIB": (2, ["tag", "text_value", "ins_pt", "extrusion"]),
             "ELLIPSE": (35, ["center", "sm_axis", "axis_ratio", "start_angle", "end_angle", "extrusion"]),
             "TEXT": (1, ["ins_pt", "text_value"]), "MTEXT": (44, ["ins_pt", "text"])}
    out = {}
    for kind, (t, fields) in paths.items():
        rows = [o for o in objs if "entity" in o and o.get("type") == t and (o.get("entity") or "") in (kind, "")]
        out[kind] = {"rows": len(rows), "rows_with_empty_entity_name": sum(1 for o in rows if not o.get("entity")),
                     **{f: sum(1 for o in rows if f in o) for f in fields}}
    lw = [o for o in objs if o.get("type") == 77 and (o.get("entity") or "") in ("LWPOLYLINE", "")]
    out["LWPOLYLINE"]["flag_bit1_set"] = sum(1 for o in lw if int(o.get("flag", 0) or 0) & 1)
    out["LWPOLYLINE"]["bulges_non_empty_iff_flag16"] = all(bool(o.get("bulges")) == bool(int(o.get("flag", 0) or 0) & 16) for o in lw)
    out["LWPOLYLINE"]["const_width_present_iff_flag4"] = all(("const_width" in o) == bool(int(o.get("flag", 0) or 0) & 4) for o in lw)
    bh = [o for o in objs if o.get("type") == 49 or o.get("object") == "BLOCK_HEADER"]
    out["BLOCK_HEADER"] = {"rows": len(bh), "empty_name": sum(1 for o in bh if not o.get("name")),
                           "empty_object_name": sum(1 for o in bh if not o.get("object")),
                           "base_pt_present": sum(1 for o in bh if "base_pt" in o),
                           "base_pt_non_zero": sum(1 for o in bh if o.get("base_pt") and any(abs(v) > 1e-9 for v in o["base_pt"])),
                           "blkisxref_1": sum(1 for o in bh if o.get("blkisxref")),
                           "is_xref_ref_1": sum(1 for o in bh if o.get("is_xref_ref"))}
    tc = Counter((o.get("type"), o.get("entity")) for o in objs if "entity" in o)
    out["type_name_pairs"] = {f"{t}:{n}": c for (t, n), c in sorted(tc.items(), key=lambda kv: -kv[1])}
    return out


def k1_section(doc):
    rg = kernel.realise(doc)
    fc = Counter(f.code for f in rg.findings)
    return rg, {"visits": rg.visits, "dispositions": dict(rg.dispositions), "findings_by_code": dict(fc),
                "blocking_findings": sum(1 for f in rg.findings if f.blocks_final),
                "segments": len(rg.segments), "circular_arcs_ARC": sum(1 for a in rg.arcs if a.source == "ARC"),
                "circular_arcs_BULGE": sum(1 for a in rg.arcs if a.source == "BULGE"),
                "circular_arcs_CW": sum(1 for a in rg.arcs if a.direction == "CW"),
                "circles": len(rg.circles), "elliptical_arcs": len(rg.elliptical_arcs),
                "attributes": len(rg.attributes), "carried": len(rg.carried), "hidden": len(rg.hidden),
                "document_notes": dict(doc.notes),
                "blocks_name_unreadable": sum(1 for b in doc.blocks.values() if not b.name_readable)}


def _ccw_mid(c, r, a0, a1):
    sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
    t = a0 + sweep / 2
    return (c[0] + r * math.cos(t), c[1] + r * math.sin(t))


def cad_adapter_section(decode):
    nd = CA.normalize(decode)
    kinds = Counter(p.kind for p in nd.primitives)
    inv = Counter(p.kind for p in nd.primitives if p.provenance.invisible)
    return nd, {"primitives_by_kind": dict(kinds), "primitives_with_invisible_flag": dict(inv)}


def arc_comparison(rg, nd):
    cad = [p for p in nd.primitives if p.kind == "ARC" and not p.provenance.invisible]
    index = {}
    for p in cad:
        key = (round(p.cx / TOL), round(p.cy / TOL), round(p.radius / TOL))
        index.setdefault(key, []).append(_ccw_mid((p.cx, p.cy), p.radius, p.start_angle, p.end_angle))
    agree = mid_differs = unmatched = 0
    by_layer = Counter()
    for a in rg.arcs:
        key = (round(a.center[0] / TOL), round(a.center[1] / TOL), round(a.radius / TOL))
        mids = index.get(key)
        if not mids:
            unmatched += 1
        elif any(math.hypot(m[0] - a.mid[0], m[1] - a.mid[1]) <= TOL for m in mids):
            agree += 1
        else:
            mid_differs += 1
            by_layer[(a.lineage.layer, a.source, a.direction)] += 1
    return {"k1_circular_arcs": len(rg.arcs), "cad_adapter_visible_arcs": len(cad),
            "same_centre_radius_same_mid": agree, "same_centre_radius_DIFFERENT_MID": mid_differs,
            "no_cad_adapter_arc_with_same_centre_radius": unmatched,
            "different_mid_by_layer_source_dir": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in by_layer.most_common()}}


def dynamic_blocks(objs, rg):
    by_h = {_h(o.get("handle")): o for o in objs}
    U = [o for o in objs if (o.get("type") == 49) and str(o.get("name", "")).upper().startswith("*U")]
    u_keys = {_h(o.get("handle")) for o in U}
    inv = sum(1 for o in objs if "entity" in o and _h(o.get("ownerhandle")) in u_keys and o.get("invisible"))
    tot = sum(1 for o in objs if "entity" in o and _h(o.get("ownerhandle")) in u_keys)
    parents = Counter()
    for o in U:
        refs = [e.get("value") for e in (o.get("eed") or []) if e.get("code") == 5]
        tgt = by_h.get(_h(refs[0])) if refs else None
        parents["NONE" if tgt is None else (tgt.get("object") or tgt.get("entity") or f"type{tgt.get('type')}")] += 1
    inserts_to_u = sum(1 for o in objs if o.get("type") == 7 and _h(o.get("block_header")) in u_keys)
    return {"anonymous_U_blocks": len(U), "entities_in_U": tot, "invisible_entities_in_U": inv,
            "inserts_referencing_U": inserts_to_u, "eed_code5_target_kind": dict(parents),
            "k1_hidden_total": len(rg.hidden)}


def characterise(path):
    raw = Path(path).read_bytes()
    decode = json.loads(raw)
    objs = decode.get("OBJECTS", [])
    doc = L.to_document(decode, source_sha256=hashlib.sha256(raw).hexdigest())
    rg, k1 = k1_section(doc)
    nd, ca = cad_adapter_section(decode)
    return {"source_file": Path(path).name, "sha256": hashlib.sha256(raw).hexdigest(),
            "INSUNITS": decode.get("HEADER", {}).get("INSUNITS"),
            "srd_1": L.source_representation_digest(decode),
            "field_audit": field_audit(objs), "k1": k1, "cad_adapter": ca,
            "arc_comparison": arc_comparison(rg, nd), "dynamic_blocks": dynamic_blocks(objs, rg)}


if __name__ == "__main__":
    print(json.dumps([characterise(p) for p in sys.argv[1:]], indent=1, default=str))
