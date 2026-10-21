"""ARCHITECTURAL DRAWING DISCOVERY (M9 S6) - the ezdxf side of engine.source.discovery: a source census of the whole
DXF (model space, every paper-space layout, every block reached from model space) and the admission stages built from
it, before any quantity.

    census(doc)                                    layouts, blocks, XREFs, MINSERTs, nesting, hidden layers, kinds
    admit_intake(report, path, E, doc, ...)        stages 0 (intake), 1 (inventory), 4 (units); -> unit_m to use
    admit_regions(report, E, P, ...)               stages 2 (sheets) and 5 (floors) on the regions the method uses
    shapes(doc)                                    every filled shape (HATCH / SOLID) in WCS at every block depth, and
                                                   the blocks with arcs inserted at a non-uniform scale (stage 6)
    UNITS                                          the --units names a reviewer may give

The census reads, it never changes the drawing; the K2 kernel's own dispositions (k2_census) prove that no model-space
entity was dropped without a record. Called only by the opt-in paths (ARCH_TAKEOFF_V2 and the V1
--strict-admission mode): ARCH_TAKEOFF_V1 without --strict-admission never runs it.
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_plan as AP              # noqa: E402
from engine.source import discovery as DS              # noqa: E402
from engine.source import drawing_model as DM          # noqa: E402

POLICY_ID = "ARCH_DISCOVERY_V1"
UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0, "in": 0.0254}
MAX_DEPTH = 8


def _layer(e):
    """an entity's layer; None for an entity kind ezdxf keeps as raw tags (RTEXT, proxies: no layer attribute)."""
    try:
        return e.dxf.layer
    except Exception:                                             # noqa: BLE001
        return None


def census(doc):
    msp = doc.modelspace()
    out = {"layouts": [], "xrefs": [], "minserts": 0, "max_insert_depth": 0, "hatches_below_first_level": 0,
           "hidden_layers": [], "kinds": {}}
    for lay in doc.layouts:
        types = Counter(e.dxftype() for e in lay)
        out["layouts"].append({"name": lay.name, "kind": "MODEL" if lay.name == "Model" else "PAPER",
                               "entities_by_type": dict(sorted(types.items())),
                               "viewports": max(types.get("VIEWPORT", 0) - 1, 0) if lay.name != "Model" else 0})
    # every block reached from model space, with the depth it is reached at and how many placed instances it has
    kinds = Counter(e.dxftype() for e in msp)
    on_layer = Counter(_layer(e) for e in msp)
    reached = Counter()
    inserted = set()

    def cells(ins):
        return max(int(ins.dxf.get("row_count", 1) or 1), 1) * max(int(ins.dxf.get("column_count", 1) or 1), 1)

    def walk(entities, depth, mult):
        for e in entities:
            if e.dxftype() != "INSERT":
                continue
            if cells(e) > 1:
                out["minserts"] += 1
            name = e.dxf.name
            inserted.add(name)
            blk = doc.blocks.get(name)
            if blk is None or depth >= MAX_DEPTH or blk.block_record.is_xref:
                continue
            n = mult * cells(e)
            out["max_insert_depth"] = max(out["max_insert_depth"], depth + 1)
            reached[(name, depth + 1)] += n
            for c in blk:
                kinds[c.dxftype()] += n
                on_layer[_layer(c)] += n
                if c.dxftype() == "HATCH" and depth + 1 >= 2:
                    out["hatches_below_first_level"] += n
            walk(blk, depth + 1, n)
    walk(msp, 0, 1)
    out["kinds"] = dict(sorted(kinds.items()))
    for b in doc.blocks:
        if b.block_record.is_xref:
            out["xrefs"].append({"block": b.name, "path": b.block.dxf.get("xref_path", "") if b.block else "",
                                 "inserted": b.name in inserted})
    for L in doc.layers:
        n = on_layer.get(L.dxf.name, 0)
        if n and (L.is_off() or L.is_frozen()):
            out["hidden_layers"].append({"layer": L.dxf.name, "off": L.is_off(), "frozen": L.is_frozen(),
                                         "entities": n})
    return out


def _hatch_rings(h):
    rings = []
    for path in h.paths:
        if hasattr(path, "vertices"):
            pts = [(float(v[0]), float(v[1])) for v in path.vertices]
        else:
            pts = [(float(e.start[0]), float(e.start[1])) for e in path.edges if hasattr(e, "start")]
        if pts:
            rings.append(pts)
    ext = h.dxf.extrusion
    if ext is not None and ext[2] < 0:                            # a mirrored hatch: OCS x is WCS -x
        rings = [[(-x, y) for x, y in r] for r in rings]
    return rings


def shapes(doc):
    """-> {"fills": [{fill_id, kind, depth, layer, ring}], "nonuniform_arc_inserts": [{block, at, xscale, yscale,
    depth}], "errors": [...]}: model space read through ezdxf's own block transforms (virtual entities) at every depth
    up to MAX_DEPTH, every MINSERT cell expanded. Independent of the plan reader (whose hatch reader reads one block
    level and no SOLID), so the two can be compared (engine.source.arch_completeness.column_evidence)."""
    out = {"fills": [], "nonuniform_arc_inserts": [], "errors": []}
    arcs_in = {}

    def has_arcs(name):
        if name not in arcs_in:
            blk = doc.blocks.get(name)
            arcs_in[name] = bool(blk) and any(e.dxftype() in ("ARC", "CIRCLE") for e in blk)
        return arcs_in[name]

    def eff(e, inherit):
        lay = _layer(e)
        return inherit if lay == "0" and inherit else lay       # CAD: layer-0 block content takes the INSERT's layer

    def walk(entities, depth, inherit=None, cell=False):
        for e in entities:
            t = e.dxftype()
            if t == "INSERT":
                if depth >= MAX_DEPTH:
                    continue
                sx, sy = abs(e.dxf.get("xscale", 1.0) or 1.0), abs(e.dxf.get("yscale", 1.0) or 1.0)
                if abs(sx - sy) > 1e-6 * max(sx, sy) and has_arcs(e.dxf.name):
                    p = e.dxf.insert
                    out["nonuniform_arc_inserts"].append({"block": e.dxf.name, "at": (float(p[0]), float(p[1])),
                                                          "xscale": e.dxf.get("xscale", 1.0),
                                                          "yscale": e.dxf.get("yscale", 1.0), "depth": depth})
                try:
                    cells = list(e.multi_insert()) if e.mcount > 1 else [e]
                    for k, c in enumerate(cells):
                        walk(list(c.virtual_entities()), depth + 1, eff(e, inherit), cell or k > 0)
                except Exception as ex:                           # noqa: BLE001 - recorded, never dropped silently
                    out["errors"].append({"block": e.dxf.name, "depth": depth, "error": str(ex)[:200]})
            elif t == "HATCH":
                for r in _hatch_rings(e):
                    out["fills"].append({"kind": "HATCH", "depth": depth, "layer": eff(e, inherit), "ring": r,
                                         "unread_by_plan_reader": depth >= 2 or cell})
            elif t in ("SOLID", "TRACE"):
                v = [e.dxf.get(f"vtx{i}") for i in range(4)]
                pts = [(float(q[0]), float(q[1])) for q in v if q is not None]
                if len(pts) == 4:                                 # SOLID vertex order 1-2-4-3
                    pts = [pts[0], pts[1], pts[3], pts[2]]
                out["fills"].append({"kind": t, "depth": depth, "layer": eff(e, inherit), "ring": pts,
                                     "unread_by_plan_reader": True})
    walk(doc.modelspace(), 0)
    for i, f in enumerate(out["fills"]):
        f["fill_id"] = f"FILL-{i:05d}"
    return out


def k2_census(doc):
    """what the K2 kernel (engine.source.cad.kernel_ezdxf) does with every entity it visits, and the model-space
    entities it gives no disposition (realised / carried / hidden / finding) - a silent drop, expected empty. The kernel
    runs again on the admission's own document (read-only): tools/urban_intake.py is not changed (its hash is part of
    the M7 / M8 engine freezes)."""
    from engine.source.cad import kernel_ezdxf as K2
    from tools import urban_intake as UI
    g = K2.realise(doc)
    top = [e.dxf.handle for e in doc.modelspace() if e.dxf.handle]
    missing = [h for h in top if f"D2:{UI._dec(h)}" not in g.obs_dispositions]
    return {"dispositions": dict(sorted(g.dispositions.items())), "visits": g.visits, "top_level": len(top),
            "missing_top_level": missing}


def documents_record(path, doc, sha=None):
    data_sha = sha or hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return {"file": Path(path).name, "sha256": data_sha, "bytes": Path(path).stat().st_size, "format": "DXF",
            "parse_status": "PARSED",
            "header": {"dxf_version": doc.dxfversion, "INSUNITS": doc.header.get("$INSUNITS"),
                       "DIMLFAC": doc.header.get("$DIMLFAC"), "MEASUREMENT": doc.header.get("$MEASUREMENT")}}


def admit_intake(report, path, E, doc, *, units=None, accept_xrefs=()):
    """stages 0, 1 and 4. E = urban_intake.read(path). -> the unit (m per drawing unit) the measurement must use, or
    None when the units are not established (then stage 4 stops the run)."""
    DS.set_stage(report, "0_intake", [], dxf_version=doc.dxfversion)
    C = census(doc)
    k2 = k2_census(doc)
    DS.set_stage(report, "1_inventory", DS.inventory_findings(C, k2, accepted_xrefs=accept_xrefs), census=C,
                 entity_support={k: DS.ARCH_SUPPORT.get(k, "UNKNOWN_KIND") for k in C["kinds"]}, k2=k2)
    if units is not None and units not in UNITS:
        raise ValueError(f"--units must be one of {sorted(UNITS)}")
    # every closed rectangle (no size floor: a metre drawing's 0.4 m columns are below the 1.0-unit default)
    inferred = DM.infer_units(E, DM.closed_rectangles(E["segments"], eps=1e-9))
    over = UNITS.get(units) if units else None
    fu = DS.unit_findings(E.get("unit_m"), inferred, over, units)
    used = over if over is not None else (E.get("unit_m") if not any(f["level"] == DS.BLOCKED_ITEM for f in fu)
                                          else None)
    DS.set_stage(report, "4_units", fu, declared_unit_m=E.get("unit_m"), insunits=E.get("insunits"),
                 inferred_unit_m=inferred.get("unit_m"), member_fit=inferred.get("member_fit"),
                 unit_m_used=used, k2_findings=E.get("intake_findings") or {})
    return used, C


def paper_space_content(C):
    return any(sum(v for k, v in p["entities_by_type"].items() if k != "VIEWPORT")
               for p in C["layouts"] if p["kind"] == "PAPER")


def admit_regions(report, E, P, C, *, split, overrides=False):
    """stages 2 and 5 on the regions the method will measure (P = arch_plan.plan_regions of that method, or the
    reviewer's regions)."""
    titles = [t for t in E["texts"] if AP.floor_of_title(t["value"])[0]]
    model = DM.build(E)
    frames = [s["box"] for s in model["sheets"]]
    in_frames = [t for t in titles if any(b[0] <= t["x"] <= b[2] and b[1] <= t["y"] <= b[3] for b in frames)]
    crossings = AP.cut_crossings(E, P["regions"]) if split == "TITLE_MIDPOINTS" and not overrides else {}
    sheets, floors = DS.region_findings(
        P["regions"], other_frames=P.get("other_frames") or (), blocked_frames=P.get("blocked_frames") or (),
        unassigned=P.get("unassigned_pieces") or (), held_frames=P.get("held_frames") or (),
        crossings=crossings, titles_found=len(titles),
        titles_in_frames=len(in_frames),
        paper_space_content=paper_space_content(C), frames_from_lines=bool(P.get("frames_from_lines")),
        overrides=overrides)
    DS.set_stage(report, "2_sheets", sheets,
                 frames=[{"sheet_id": s["sheet_id"], "role": s["role"], "storey": s["storey"],
                          "frame_source": s["frame_source"], "box": s["box"]} for s in model["sheets"]],
                 frames_from_lines=bool(P.get("frames_from_lines")))
    DS.set_stage(report, "5_floors", floors, split=split,
                 floors=[{"floor_id": r["floor"], "region_id": r["region_id"], "sheet_id": r["sheet_id"],
                          "box": r["box"], "evidence": r["evidence"], "title_text_id": r.get("title_text_id")}
                         for r in P["regions"]], cut_crossings=crossings)


def override_regions(specs):
    """--region FLOOR=x0,y0,x1,y1 (drawing units) -> plan regions recorded as reviewer input."""
    order = {fl: o for fl, o, _p in AP.FLOOR_TITLES}
    out = []
    for spec in specs or ():
        fl, _, box = spec.partition("=")
        fl = fl.strip()
        if fl not in order:
            raise ValueError(f"--region: unknown floor {fl!r} (one of {sorted(order)})")
        try:
            x0, y0, x1, y1 = (float(v) for v in box.split(","))
        except ValueError:
            raise ValueError(f"--region {spec!r}: FLOOR=x0,y0,x1,y1 in drawing units") from None
        if not (x1 > x0 and y1 > y0):
            raise ValueError(f"--region {spec!r}: x1 > x0 and y1 > y0")
        out.append({"region_id": f"REVIEWER:{fl}", "sheet_id": "REVIEWER", "floor": fl, "order": order[fl],
                    "box": (x0, y0, x1, y1), "title_text_id": None,
                    "evidence": "plan region given by a reviewer (--region); recorded"})
    out.sort(key=lambda r: (r["order"], r["region_id"]))
    return {"policy": AP.POLICY_ID, "regions": out, "other_frames": [], "overrides": True}


def policy_record():
    return {"policy_id": POLICY_ID, "units": UNITS, "max_insert_depth": MAX_DEPTH,
            "shapes": "HATCH boundary paths + SOLID / TRACE outlines through ezdxf virtual entities (every depth, "
                      "MINSERT cells expanded); never used as a quantity",
            "discovery": DS.policy_record()["policy_id"]}
