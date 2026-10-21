"""ARCH DIMENSIONS (M9 Phase 2A P2-09a) - the DIMENSION entities of a plan DXF as plain records for the read-only
cross-check in engine/source/dimension_evidence.py (that module stays stdlib-only; this one uses ezdxf).

    read_doc(doc) -> {"dimensions": [record], "header_dimlfac": float | None, "not_read": {reason: n}}

record: handle, type (LINEAR / ALIGNED / other), layer, p1 (dimension line point), p2 / p3 (extension origins), angle
(LINEAR), dimstyle, style_dimlfac (the style's own value or None when the style does not set it), override_dimlfac
(the entity's own DSTYLE override or None), measurement (group 42 when present; its scaling is not assumed), text
(the text override, "" / "<>" = none), shown_text (the text of the rendered dimension block, when present).
Dimensions inside blocks are counted in not_read (model space only in P2-09a).
"""

from __future__ import annotations

from collections import Counter

TYPES = {0: "LINEAR", 1: "ALIGNED", 2: "ANGULAR", 3: "DIAMETER", 4: "RADIUS", 5: "ANGULAR_3P", 6: "ORDINATE"}


def _xy(v):
    return [float(v[0]), float(v[1])] if v is not None else None


def _shown(doc, d):
    name = d.dxf.get("geometry")
    blk = doc.blocks.get(name) if name else None
    if blk is None:
        return None
    for e in blk:
        if e.dxftype() == "MTEXT":
            return e.plain_text()
        if e.dxftype() == "TEXT":
            return e.dxf.text
    return None


def read_doc(doc):
    hdr = doc.header.get("$DIMLFAC")
    out, skip = [], Counter()
    for d in doc.modelspace().query("DIMENSION"):
        try:
            dt = d.dimtype
        except Exception:                                        # noqa: BLE001 - an unreadable entity is counted
            skip["UNREADABLE"] += 1
            continue
        style = doc.dimstyles.get(d.dxf.get("dimstyle", "Standard")) if d.dxf.get("dimstyle") else None
        try:
            ov = d.override().dimstyle_attribs.get("dimlfac")
        except Exception:                                        # noqa: BLE001
            ov = None
        out.append({"handle": d.dxf.handle, "type": TYPES.get(dt, str(dt)), "layer": d.dxf.layer,
                    "p1": _xy(d.dxf.get("defpoint")), "p2": _xy(d.dxf.get("defpoint2")),
                    "p3": _xy(d.dxf.get("defpoint3")), "angle": float(d.dxf.get("angle", 0.0) or 0.0),
                    "dimstyle": d.dxf.get("dimstyle"),
                    "style_dimlfac": (style.dxf.get("dimlfac") if style is not None else None),
                    "override_dimlfac": ov, "measurement": d.dxf.get("actual_measurement"),
                    "text": d.dxf.get("text", "") or "", "shown_text": _shown(doc, d)})
    for blk in doc.blocks:
        if blk.name.startswith("*") or blk.is_any_layout:
            continue
        n = sum(1 for e in blk if e.dxftype() == "DIMENSION")
        if n:
            skip["INSIDE_A_BLOCK"] += n
    return {"dimensions": out, "header_dimlfac": float(hdr) if hdr is not None else None, "not_read": dict(skip)}


def read(path):
    import ezdxf
    return read_doc(ezdxf.readfile(str(path)))
