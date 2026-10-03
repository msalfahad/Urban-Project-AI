"""R8.2 SHADOW IMPACT — what would each source defect change on the ACTIVE downstream path?

Research lab only. Nothing in engine/ imports this; nothing published is
touched; production keeps its path. The shadow bridge runs the REAL current
downstream code in-process twice or more:

    BASELINE          cad_adapter output exactly as today
    <DEFECT>_ONLY     the same output with ONE defect corrected, using K1 (D1 -> K1)
                      as the corrector for that defect only (§20 defect isolation)

and diffs the downstream registers. cad_adapter.normalize is patched in this
process only; the patch is removed after each run.

Paths (see ACTIVE_PATH_MAP.json):
    QORTUBA  QS01 room-by-room takeoff: engine/ingest pipeline7 via cad_adapter  (quantities released)
    P7757    PA07 supervised regression: engine/ingest pipeline7 via cad_adapter (BRIDGE_ALLOWED = 0)
    ALRASHED R7: project reader pa09/alrashed/geometry.py + qs_core (no cad_adapter)

No benchmark, workbook or manual BOQ total is read here. Deltas are old vs
corrected, never vs a target.

    python3 research/external_engine_lab/r8_2_shadow_impact.py [QORTUBA] [P7757] [ALRASHED] > out.json
"""

from __future__ import annotations

import copy
import json
import math
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import cad_adapter as CA                               # noqa: E402
from engine.source.cad import kernel, libredwg_map as L            # noqa: E402

DECODES = {"QORTUBA": "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json",
           "P7757": "data/runs/cad_convert/P7757_ARCHITECTURAL.json",
           "ALRASHED": "data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json"}
TOL = 1e-6


def _ang(c, p):
    return math.atan2(p[1] - c[1], p[0] - c[0])


def _ccw_mid(c, r, a0, a1):
    sw = (a1 - a0) % (2 * math.pi) or 2 * math.pi
    t = a0 + sw / 2
    return (c[0] + r * math.cos(t), c[1] + r * math.sin(t))


def _hkey(p):
    return (str(p.provenance.handle), tuple(str(x) for x in p.provenance.instance_path))


def _k1key(lin):
    h = lin.source_handle
    return (h, tuple(x.split(":", 1)[1].split("[")[0] for x in lin.instance_path))


# ---------------------------------------------------------------- variants (one defect each)
def hidden_filter(nd, dec, doc, rg):
    prims = [p for p in nd.primitives if not p.provenance.invisible]
    return replace(nd, primitives=prims), {"primitives_removed": len(nd.primitives) - len(prims)}


def mirror_fix(nd, dec, doc, rg):
    by = {}
    for a in rg.arcs:
        by.setdefault(_k1key(a.lineage), []).append(a)
    out, changed, objs = [], 0, []
    for p in nd.primitives:
        if p.kind == "ARC" and p.provenance.entity_type in ("17", "77"):
            cands = [a for a in by.get(_hkey(p), ()) if abs(a.center[0] - p.cx) < 1e-6 and abs(a.center[1] - p.cy) < 1e-6
                     and abs(a.radius - p.radius) < 1e-6]
            if len(cands) == 1:
                a = cands[0]
                m = _ccw_mid((p.cx, p.cy), p.radius, p.start_angle, p.end_angle)
                if math.hypot(m[0] - a.mid[0], m[1] - a.mid[1]) > 1e-6:
                    s, e = (a.start, a.end) if a.direction == "CCW" else (a.end, a.start)
                    p = replace(p, start_angle=_ang(a.center, s) % (2 * math.pi), end_angle=_ang(a.center, e) % (2 * math.pi))
                    changed += 1
                    objs.append({"handle": p.provenance.handle, "layer": p.provenance.layer,
                                 "instance_path": list(p.provenance.instance_path)})
        out.append(p)
    return replace(nd, primitives=out), {"arcs_corrected": changed, "objects": objs[:50]}


def nameless_placement(nd, dec, doc, rg):
    """Remove nameless-block content cad_adapter emitted at top level; add K1's placements of it."""
    nameless = {k: b for k, b in doc.blocks.items() if not b.name_readable}
    owned = {o.source_handle: o for b in nameless.values() for o in b.entities}
    model_vals = Counter(o.source_handle.split("+")[0] for o in doc.entities)
    removable, ambiguous = set(), set()
    for h in owned:
        v = h.split("+")[0]
        (ambiguous if model_vals[v] else removable).add(v)
    kept = [p for p in nd.primitives if not (not p.provenance.instance_path and str(p.provenance.handle) in removable)]
    removed = len(nd.primitives) - len(kept)
    added = []
    for s in rg.segments:
        if s.lineage.source_handle in owned and s.lineage.instance_path:
            added.append(CA.Primitive(kind="SEGMENT", provenance=_prov(s.lineage), x1=s.a[0], y1=s.a[1], x2=s.b[0], y2=s.b[1]))
    for a in rg.arcs:
        if a.lineage.source_handle in owned and a.lineage.instance_path:
            s, e = (a.start, a.end) if a.direction == "CCW" else (a.end, a.start)
            added.append(CA.Primitive(kind="ARC", provenance=_prov(a.lineage), cx=a.center[0], cy=a.center[1], radius=a.radius,
                                      start_angle=_ang(a.center, s) % (2 * math.pi), end_angle=_ang(a.center, e) % (2 * math.pi)))
    for c in rg.circles:
        if c.lineage.source_handle in owned and c.lineage.instance_path:
            added.append(CA.Primitive(kind="CIRCLE", provenance=_prov(c.lineage), cx=c.center[0], cy=c.center[1], radius=c.radius))
    return replace(nd, primitives=kept + added), {"nameless_headers": len(nameless), "owned_entities": len(owned),
                                                   "top_level_primitives_removed": removed, "placed_primitives_added": len(added),
                                                   "ambiguous_handle_values_left_untouched": len(ambiguous)}


def _prov(lin):
    path = tuple(int(x.split(":", 1)[1].split("[")[0].split("+")[0]) for x in lin.instance_path)
    return CA.Provenance(handle=int(lin.source_handle.split("+")[0]), entity_type={"LINE": "19", "ARC": "17", "CIRCLE": "18",
                         "LWPOLYLINE": "77"}.get(lin.kind, lin.kind), layer=str(lin.layer or "0"), instance_path=path,
                         sub_id="K1-SHADOW")


def handle_identity(dec_orig):
    """Decode rewrite (research only): give 3-byte handles a value above 0xFFFF so identity is unique.
    Only uniqueness is claimed, not the true handle. Relative references are left as printed."""
    dec = copy.deepcopy(dec_orig)
    n = 0
    for o in dec["OBJECTS"]:
        h = o.get("handle")
        if isinstance(h, list) and len(h) >= 3 and h[1] >= 3:
            h[-1] += 0x10000
            n += 1
        for k, v in list(o.items()):
            if k != "handle" and isinstance(v, list) and len(v) >= 3 and isinstance(v[0], int) and v[0] in (2, 3, 4, 5) \
                    and isinstance(v[1], int) and v[1] >= 3 and isinstance(v[-1], int):
                v[-1] += 0x10000
            if k == "entities" and isinstance(v, list):
                for r in v:
                    if isinstance(r, list) and len(r) >= 3 and r[1] >= 3:
                        r[-1] += 0x10000
    return dec, n


VARIANTS = {"INVISIBLE_GEOMETRY": hidden_filter, "MIRRORED_CURVE": mirror_fix, "NAMELESS_BLOCK_PLACEMENT": nameless_placement}


class Patched:
    """Patch cad_adapter.normalize in THIS process for one run."""

    def __init__(self, fn):
        self.fn, self.orig = fn, CA.normalize

    def __enter__(self):
        orig = self.orig
        fn = self.fn

        def wrapped(decoded, **kw):
            return fn(orig(decoded, **kw), decoded)
        CA.normalize = wrapped
        return self

    def __exit__(self, *a):
        CA.normalize = self.orig


# ---------------------------------------------------------------- per-path summaries
def summarise_p7(r):
    reg = r.registers
    sp = reg["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"]
    bands = reg["PA07_MATERIAL_BAND_REGISTER"]["ROWS"]
    ops = reg["PA07_OPENING_SITE_REGISTER"]["ROWS"]
    qs = reg["PA07_QUANTITY_SAFETY_REGISTER"]
    return {"spaces": len(sp), "space_area_m2_sum": round(sum(x["AREA_GEOMETRIC_M2"] or 0 for x in sp), 3),
            "spaces_by_geometry_status": dict(Counter(x["GEOMETRY_STATUS"] for x in sp)),
            "space_areas": sorted(round(x["AREA_GEOMETRIC_M2"] or 0, 3) for x in sp),
            "bands": len(bands), "bands_by_status": dict(Counter(b.get("STATUS") or b.get("BAND_STATUS") for b in bands)),
            "band_developed_length_mm": round(sum(b.get("DEVELOPED_LENGTH_MM") or 0 for b in bands), 1),
            "openings_by_class": dict(Counter(o["CLASS"] for o in ops)),
            "quantity_rows": qs["COUNT"], "bridge_allowed": qs["BRIDGE_ALLOWED"],
            "quantity_status": qs["BY_QUANTITY_STATUS"],
            "faces": reg["PA07_PLANAR_FACE_REGISTER"]["COUNT"]}


def summarise_qs01(o):
    return {"rooms": {f["ROOM"] or f["ROOM_ID"]: f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in o["floors"]},
            "room_status": {f["ROOM"] or f["ROOM_ID"]: f["STATUS"] for f in o["floors"]},
            "skirting_lm": {s.get("ROOM") or s.get("ROOM_ID"): s.get("NET_SKIRTING_LM") for s in o["skirt"]},
            "block_wall_length_by_thickness": o["by_thk"], "blue_elements": dict(Counter(b["TYPE"] for b in o["blue"])),
            "inventory": len(o["inv"]), "ceilings": {c.get("ROOM") or c.get("ROOM_ID"): c.get("AREA_M2") or c.get("CEILING_AREA_M2") for c in o["ceil"]}}


def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            out += diff(a.get(k), b.get(k), f"{path}.{k}" if path else str(k))
    elif a != b:
        out.append({"field": path, "baseline": a, "variant": b})
    return out


def _k1(dec):
    doc = L.to_document(dec)
    return doc, kernel.realise(doc)


def shadow_ingest(project, runner, summarise):
    dec = json.loads((ROOT / DECODES[project]).read_text())
    doc, rg = _k1(dec)
    base = summarise(runner())
    res = {"BASELINE": base, "VARIANTS": {}}
    for name, fn in VARIANTS.items():
        stats = {}

        def apply(nd, decoded, fn=fn, stats=stats):
            v, s = fn(nd, decoded, doc, rg)
            stats.update(s)
            return v
        with Patched(apply):
            got = summarise(runner())
        res["VARIANTS"][name] = {"correction": stats, "delta": diff(base, got)}
    dec2, n = handle_identity(dec)
    orig = CA.normalize

    def rewritten(decoded, **kw):                       # the one CAD decode of this run, identity rewritten
        return orig(dec2, **kw)
    CA.normalize = rewritten
    try:
        got = summarise(runner())
    finally:
        CA.normalize = orig
    res["VARIANTS"]["HANDLE_IDENTITY"] = {"correction": {"handles_rewritten": n}, "delta": diff(base, got)}
    return res


def run_qortuba():
    from research.qs_wall_treatment_01.pa08.qortuba.qs01 import takeoff as T
    return shadow_ingest("QORTUBA", T.run, summarise_qs01)


def run_p7757():
    from engine.ingest import pipeline7 as P7
    from research.qs_wall_treatment_01.pa07 import config as C7
    return shadow_ingest("P7757", lambda: P7.run(C7.supervised()), summarise_p7)


def run_alrashed():
    """Al Rashed R7 reads the decode through its own project reader, not cad_adapter.
    One reader-level defect is isolated: LWPOLYLINE 'closed' read from flag & 1 (the DWG
    extrusion bit) instead of flag & 512."""
    from research.qs_wall_treatment_01.pa09.alrashed import geometry as G, takeoff as TK
    ents = G.load()
    orig = G._segments

    def fixed(ents_, layers, window):
        patched = []
        for o in ents_:
            if o.get("entity") == "LWPOLYLINE" and (int(o.get("flag", 0) or 0) & 512) and not (int(o.get("flag", 0) or 0) & 1):
                o = dict(o)
                o["flag"] = int(o["flag"]) | 1                  # make the reader's own test see the DWG closed bit
            patched.append(o)
        return orig(patched, layers, window)

    def rooms_all():
        out = {}
        for floor in TK.FLOORS:
            _, _, _, rows, closure = TK.floor_rows(ents, floor)
            out[floor] = {"rooms": sorted((r["NAME"] or r["ROOM_REF"], r["AREA_M2"]) for r in rows),
                          "count": len(rows), "closure_residual_m2": closure["RESIDUAL_M2"]}
        return out
    base = rooms_all()
    G._segments = fixed
    try:
        got = rooms_all()
    finally:
        G._segments = orig
    closed = [o for o in ents if o.get("entity") == "LWPOLYLINE" and o.get("_layer") in G.WALL_LAYERS + G.COLUMN_LAYERS
              and int(o.get("flag", 0) or 0) & 512]
    return {"BASELINE": base, "VARIANTS": {"PROJECT_READER_LWPOLYLINE_CLOSED_FLAG": {
        "correction": {"closed_wall_or_column_polylines": len(closed)}, "delta": diff(base, got)}}}


if __name__ == "__main__":
    which = sys.argv[1:] or ["QORTUBA", "P7757", "ALRASHED"]
    fns = {"QORTUBA": run_qortuba, "P7757": run_p7757, "ALRASHED": run_alrashed}
    print(json.dumps({p: fns[p]() for p in which}, indent=1, default=str))
