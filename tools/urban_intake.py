"""URBAN INTAKE (M2) - one drawing file -> a plain, source-pointed geometry record for the generic engine.

DXF     read by ezdxf; placed by the K2 kernel (engine.source.cad.kernel_ezdxf: ezdxf's own block / MINSERT / OCS /
        reflection machinery, mirrored arcs and bulges included). Texts and MTEXT inside blocks are placed with
        ezdxf.disassemble. A block child on layer 0 takes the layer of the nearest enclosing INSERT that has one
        (standard CAD inheritance), and the record says it did.
PDF     vector paths and text spans per page (PyMuPDF), in page points, with the page size; no scale is assumed
        (the drawing model reads it from a printed scale or leaves it unresolved). A page with no vector paths and
        no text is RASTER_ONLY (lower confidence, reported, never measured here).
DWG     refused: no pinned DWG decoder in this repository; convert to DXF first.

Everything returned is plain data (lists of dicts) with a source pointer per entity: the engine never sees ezdxf.
"""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INSUNITS_M = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0, 14: 0.1}


class IntakeError(RuntimeError):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _dec(handle):
    """the kernel's observation id form: the DXF handle (hex) as a decimal string (K2 _hid)."""
    return str(int(handle, 16))


def _insert_layers(doc):
    """{K2 instance-path id: insert layer}. Keys are DECIMAL like the kernel's lineage ids - a hex key would look up
    an unrelated entity whenever a hex handle reads as another entity's decimal id (M2 defect-set finding)."""
    out = {}
    for e in doc.modelspace().query("INSERT"):
        out[f"D2:{_dec(e.dxf.handle)}"] = e.dxf.layer
    for b in doc.blocks:
        for e in b.query("INSERT"):
            out[f"D2:{_dec(e.dxf.handle)}"] = e.dxf.layer
    return out


def _uid(lin):
    """A source id unique per placed instance: the entity handle, the insert path that placed it, the span index."""
    path = "/".join(lin.instance_path)
    return f"{lin.obs_id}@{path}:{lin.sub_part}" if path else f"{lin.obs_id}:{lin.sub_part}"


def _eff_layer(layer, path, ins_layer):
    if layer not in (None, "0"):
        return layer, False
    for obs in reversed(path or ()):
        lay = ins_layer.get(obs.split("[")[0])
        if lay and lay != "0":
            return lay, True
    return layer or "0", False


def read_dxf(path):
    import ezdxf
    from ezdxf import disassemble
    from engine.source.cad import kernel_ezdxf as K2
    doc = ezdxf.readfile(str(path))
    g = K2.realise(doc)
    il = _insert_layers(doc)
    inherited = 0
    segs, arcs, circles, ell = [], [], [], []
    for s in g.segments:
        lay, inh = _eff_layer(s.lineage.layer, s.lineage.instance_path, il)
        inherited += inh
        segs.append({"id": _uid(s.lineage), "layer": lay, "a": s.a, "b": s.b,
                     "path": list(s.lineage.instance_path), "kind": s.lineage.kind})
    for a in g.arcs:
        lay, inh = _eff_layer(a.lineage.layer, a.lineage.instance_path, il)
        inherited += inh
        arcs.append({"id": _uid(a.lineage), "layer": lay, "c": a.center, "r": a.radius,
                     "s": a.start, "m": a.mid, "e": a.end, "dir": a.direction, "source": a.source,
                     "path": list(a.lineage.instance_path)})
    for c in g.circles:
        lay, _ = _eff_layer(c.lineage.layer, c.lineage.instance_path, il)
        circles.append({"id": _uid(c.lineage), "layer": lay, "c": c.center, "r": c.radius,
                        "path": list(c.lineage.instance_path)})
    for e in g.elliptical_arcs:
        lay, _ = _eff_layer(e.lineage.layer, e.lineage.instance_path, il)
        ell.append({"id": _uid(e.lineage), "layer": lay, "c": e.center, "u": e.axis_u, "v": e.axis_v,
                    "t0": e.t0, "t1": e.t1, "s": e.start, "e": e.end, "dir": e.direction, "full": e.full,
                    "path": list(e.lineage.instance_path)})
    texts = []
    n = 0
    for e in disassemble.recursive_decompose(doc.modelspace()):
        t = e.dxftype()
        if t not in ("TEXT", "MTEXT"):
            continue
        n += 1
        try:
            val = e.dxf.text if t == "TEXT" else e.plain_text()
        except Exception:                                                     # noqa: BLE001 - unreadable text
            continue
        p = e.dxf.insert
        if t == "TEXT" and (e.dxf.get("halign", 0) or e.dxf.get("valign", 0)) and e.dxf.hasattr("align_point"):
            p = e.dxf.align_point
        ocs_rot = None
        if t == "TEXT" and e.dxf.hasattr("extrusion") and tuple(e.dxf.extrusion) != (0.0, 0.0, 1.0):
            # M7: a TEXT's insert and rotation are in its OCS (a mirrored text carries extrusion 0,0,-1): read them
            # in world coordinates (MTEXT inserts are already WCS)
            from ezdxf.math import OCS, Vec3
            ocs = OCS(e.dxf.extrusion)
            p = ocs.to_wcs(p)
            r = math.radians(float(e.dxf.get("rotation", 0.0) or 0.0))
            d = ocs.to_wcs(Vec3(math.cos(r), math.sin(r), 0.0))
            ocs_rot = math.degrees(math.atan2(d.y, d.x)) % 360.0
        src = getattr(e, "source_block_reference", None)
        owner = f"D2:{_dec(src.dxf.handle)}" if src is not None and src.dxf.handle else None
        lay = e.dxf.layer
        if lay == "0" and src is not None:
            lay = src.dxf.layer
        h = float((e.dxf.get("height", 0.0) if t == "TEXT" else e.dxf.get("char_height", 0.0)) or 0.0)
        if ocs_rot is not None:
            rot = ocs_rot
        elif t == "MTEXT":
            # M7: an MTEXT's direction may be stored as a text_direction vector instead of a rotation angle (CAD
            # writes either; a transformed MTEXT always carries the vector): get_rotation reads both
            rot = float(e.get_rotation() or 0.0) % 360.0
        else:
            rot = float(e.dxf.get("rotation", 0.0) or 0.0)
        texts.append({"id": f"T{n}:{e.dxf.handle}" if e.dxf.handle else f"T{n}", "value": (val or "").strip(),
                      "x": float(p.x), "y": float(p.y), "layer": lay, "height": h, "rotation": rot,
                      "owner": owner, "block": src.dxf.name if src is not None else None})
    attrs = [{"owner": a.owner_insert_handle, "tag": a.tag, "value": a.value, "x": a.insertion[0],
              "y": a.insertion[1]} for a in g.attributes]
    inserts = []
    for e in doc.modelspace().query("INSERT"):
        inserts.append({"id": f"D2:{_dec(e.dxf.handle)}", "handle_hex": e.dxf.handle, "name": e.dxf.name, "x": float(e.dxf.insert.x),
                        "y": float(e.dxf.insert.y), "layer": e.dxf.layer,
                        "attribs": {a.dxf.tag: a.dxf.text for a in e.attribs}})
    hatches = []
    for e in doc.modelspace().query("HATCH"):
        try:
            pts = [(float(v[0]), float(v[1])) for v in e.paths[0].vertices] if hasattr(e.paths[0], "vertices") \
                else [(float(ed.start.x), float(ed.start.y)) for ed in e.paths[0].edges if hasattr(ed, "start")]
        except Exception:                                                     # noqa: BLE001
            pts = []
        hatches.append({"id": e.dxf.handle, "layer": e.dxf.layer, "pattern": e.dxf.pattern_name, "ring": pts})
    ins = int(doc.header.get("$INSUNITS", 0) or 0)
    return {"kind": "DXF", "file": Path(path).name, "sha256": sha256(path), "dxf_version": doc.dxfversion,
            "insunits": ins, "unit_m": INSUNITS_M.get(ins), "segments": segs, "arcs": arcs, "circles": circles,
            "ellipses": ell, "texts": texts, "attributes": attrs, "inserts": inserts, "hatches": hatches,
            "intake_findings": dict(_count(f.code for f in g.findings)),
            "inherited_layer_entities": inherited, "n_decomposed_texts": n}


def _count(it):
    out = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return out.items()


def read_pdf(path, max_pages=40):
    import fitz
    d = fitz.open(str(path))
    pages = []
    for i, pg in enumerate(d):
        if i >= max_pages:
            break
        try:
            drawings = pg.get_drawings()
        except Exception:                                                     # noqa: BLE001
            drawings = []
        segs = []
        for dr in drawings:
            for it in dr.get("items", []):
                if it[0] == "l":
                    segs.append((it[1].x, it[1].y, it[2].x, it[2].y))
                elif it[0] == "re":
                    r = it[1]
                    segs += [(r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1), (r.x1, r.y1, r.x0, r.y1),
                             (r.x0, r.y1, r.x0, r.y0)]
        words = pg.get_text("words")
        pages.append({"page": i + 1, "width_pt": pg.rect.width, "height_pt": pg.rect.height,
                      "n_segments": len(segs), "n_words": len(words),
                      "state": "VECTOR" if segs or words else "RASTER_ONLY",
                      "words": [{"x": w[0], "y": w[1], "value": w[4]} for w in words[:4000]],
                      "segments": segs[:20000]})
    return {"kind": "PDF", "file": Path(path).name, "sha256": sha256(path), "pages": pages,
            "n_pages": len(d)}


def read(path):
    p = Path(path)
    k = p.suffix.lower()
    if k == ".dxf":
        return read_dxf(p)
    if k == ".pdf":
        return read_pdf(p)
    if k == ".dwg":
        raise IntakeError("DWG is not read: no pinned DWG decoder in this repository; convert it to DXF first")
    raise IntakeError(f"not a drawing format the pipeline reads: {p.name}")


def arc_length(a):
    """Length of a placed arc from its three points (centre and radius as placed), sweep in the stated direction."""
    cx, cy = a["c"]
    a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
    a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
    sw = (a1 - a0) % (2 * math.pi) if a["dir"] == "CCW" else (a0 - a1) % (2 * math.pi)
    if sw < 1e-12:
        sw = 2 * math.pi
    return a["r"] * sw
