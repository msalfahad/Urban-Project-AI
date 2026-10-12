"""ARCH INTAKE (M9 S2 / S3) - the architectural route's extra readings of a DXF, next to tools/urban_intake.py
(unchanged; route G and every structural output keep their own reader).

    hatches(path) -> [{"id", "layer", "pattern", "rings": [outer, island, ...], "area_native", "owner", "mirrored"}]
    read_arch(path) -> {"hatches", "texts", "inserts", "extra_segments", "extra_arcs", "report"}   (S3, one read)

S3 additions (entity normalisation the K2 kernel leaves to findings, read here for the architectural route only):
    texts     every TEXT / MTEXT / ATTRIB in model space and inside blocks (any nesting, mirrored and non-uniform
              inserts placed by ezdxf), with its text style, font file and a Unicode reading:
                UNICODE              the text is Unicode already
                SHX_KEYBOARD         the font is a keyboard-mapped Arabic SHX font (xarb.shx): each Latin key is the
                                     Arabic letter of the Arabic (101) keyboard layout, a public layout - decoded exactly
                SHX_UNMAPPED         an Arabic SHX font whose glyph table is not public (X-ARAB*): kept raw, counted,
                                     never guessed
              ATTRIB values are texts too (room-tag blocks carry their name in attributes)
    inserts   every block reference with its WCS insertion point, layer, nesting path and the WCS extent of its
              content: room-tag and fixture evidence
    extra     MLINE (exploded by ezdxf), SPLINE (flattened to 1 mm chords at mm scale) and old-style 2D POLYLINE
              (exploded, bulges kept as arcs) - entities K2 reports as UNHANDLED - as segments / arcs with their
              source handle; nothing is approximated silently: the report lists every type read, converted or skipped

Why a second reader: urban_intake.read_dxf keeps only the FIRST boundary path of a model-space hatch, in the hatch's
own OCS. That loses islands (a hatch with a hole reads as the full outer ring) and places a mirrored hatch (extrusion
0,0,-1) at mirrored coordinates; hatches inside blocks are not read at all. Route G reads those hatch records, so the
M2-M8 outputs depend on them: the fix is NOT applied there (it would change frozen results and needs owner approval).
This reader is used by the architectural route only:
    - every boundary path (external + islands), polyline bulges flattened, edge paths (lines / arcs / ellipses /
      splines) flattened by ezdxf
    - OCS -> WCS for every vertex (a mirrored hatch lands where it is drawn)
    - hatches inside blocks placed by ezdxf's virtual entities (INSERT transforms, mirrored INSERTs included)
    - area = outer ring - islands (nested-path parity), in drawing units squared
"""

from __future__ import annotations

import re

import math


def _ring_area(r):
    return abs(sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r)))) / 2.0


def _point_in(p, ring):
    ins = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1 + 1e-300) + x1:
            ins = not ins
    return ins


def _path_points(path, ocs, elevation):
    """one boundary path as WCS points: ezdxf.path converts the OCS path (bulges / arcs / ellipses / splines) to WCS."""
    from ezdxf import path as P_
    p = P_.from_hatch_boundary_path(path, ocs=ocs, elevation=elevation)
    pts = [(v.x, v.y) for v in p.flattening(distance=0.5)]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9:
        pts = pts[:-1]
    return pts


def _read(h, owner=None):
    ocs = h.ocs()
    elev = h.dxf.elevation.z if h.dxf.hasattr("elevation") else 0.0
    rings = []
    for path in h.paths:
        try:
            r = _path_points(path, ocs, elev)
        except Exception:                                             # noqa: BLE001 - an unreadable path is reported
            r = []
        if len(r) >= 3:
            rings.append(r)
    rings.sort(key=_ring_area, reverse=True)
    # parity: a ring inside an odd number of others is an island
    area = 0.0
    for i, r in enumerate(rings):
        depth = sum(1 for j, o in enumerate(rings) if j != i and _point_in(r[0], o))
        area += _ring_area(r) * (1 if depth % 2 == 0 else -1)
    ext = tuple(h.dxf.get("extrusion", (0, 0, 1)))
    return {"id": h.dxf.handle, "layer": h.dxf.layer, "pattern": h.dxf.pattern_name, "rings": rings,
            "area_native": area, "owner": owner, "mirrored": ext[2] < 0, "islands": max(len(rings) - 1, 0)}


def hatches(path, doc=None):
    import ezdxf
    doc = doc if doc is not None else ezdxf.readfile(str(path))
    out = []
    msp = doc.modelspace()
    for h in msp.query("HATCH"):
        out.append(_read(h))
    for ins in msp.query("INSERT"):
        try:
            for e in ins.virtual_entities():
                if e.dxftype() == "HATCH":
                    out.append(_read(e, owner=ins.dxf.handle))
        except Exception:                                             # noqa: BLE001 - a block that cannot explode
            continue
    return out


# ---------------------------------------------------------------- S3: texts, inserts, extra geometry
# the Arabic (101) keyboard layout, unshifted keys (a public layout); a keyboard-mapped SHX font draws the Arabic
# letter of the key a Latin character sits on
_LA = "\u0644\u0627"                   # the b key types lam-alef (two letters: kept out of the one-to-one zip)
KEYBOARD_AR101 = {**dict(zip("qwertyuiop[]asdfghjkl;'zxcv",
                             "\u0636\u0635\u062b\u0642\u0641\u063a\u0639\u0647\u062e\u062d\u062c\u062f"
                             "\u0634\u0633\u064a\u0628\u0644\u0627\u062a\u0646\u0645\u0643\u0637"
                             "\u0626\u0621\u0624\u0631")),
                  "b": _LA,
                  **dict(zip("nm,./`", "\u0649\u0629\u0648\u0632\u0638\u0630"))}
KEYBOARD_SHX = ("xarb",)                 # font file stems whose glyphs follow KEYBOARD_AR101
UNMAPPED_ARABIC_SHX = ("x-arab",)       # Arabic SHX families without a public glyph table


def _stem(font):
    f = (font or "").replace("\\", "/").rsplit("/", 1)[-1].lower()
    return f[:-4] if f.endswith(".shx") or f.endswith(".ttf") else f


_DXF_UNICODE = re.compile(r"\\[Uu]\+([0-9A-Fa-f]{4})")


def decode_text(value, font):
    """-> (unicode text, state) for one text drawn in `font`. S5: a text of a pre-2007 DXF stores every character
    outside the drawing code page as a \\U+XXXX escape (the DXF rule); it is decoded exactly (state
    DXF_UNICODE_ESCAPE; the raw text is kept by the caller)."""
    st = _stem(font)
    if _DXF_UNICODE.search(value):
        value = _DXF_UNICODE.sub(lambda m: chr(int(m.group(1), 16)), value)
        return value, "DXF_UNICODE_ESCAPE"
    if any("\u0600" <= ch <= "\u06ff" for ch in value) or not any(c.isalpha() for c in value):
        return value, "UNICODE"
    if any(st.startswith(k) for k in KEYBOARD_SHX):
        out = []
        for ch in value:
            c = ch.lower()
            out.append(_LA if c == "b" else KEYBOARD_AR101.get(c, ch))
        return "".join(out), "SHX_KEYBOARD"
    if any(st.startswith(k) for k in UNMAPPED_ARABIC_SHX):
        return value, "SHX_UNMAPPED"
    return value, "UNICODE"


def _style_fonts(doc):
    return {s.dxf.name.upper(): s.dxf.get("font", "") for s in doc.styles}


def _wcs_text_point(e):
    t = e.dxftype()
    p = e.dxf.insert
    if t in ("TEXT", "ATTRIB") and (e.dxf.get("halign", 0) or e.dxf.get("valign", 0)) and e.dxf.hasattr("align_point"):
        p = e.dxf.align_point
    if t in ("TEXT", "ATTRIB") and e.dxf.hasattr("extrusion") and tuple(e.dxf.extrusion) != (0.0, 0.0, 1.0):
        from ezdxf.math import OCS
        p = OCS(e.dxf.extrusion).to_wcs(p)
    return float(p.x), float(p.y)


def _texts(doc, fonts):
    from ezdxf import disassemble
    out, n = [], 0
    for e in disassemble.recursive_decompose(doc.modelspace()):
        t = e.dxftype()
        if t not in ("TEXT", "MTEXT", "ATTRIB"):
            continue
        n += 1
        try:
            raw = e.dxf.text if t != "MTEXT" else e.plain_text()
        except Exception:                                             # noqa: BLE001 - an unreadable text is counted
            continue
        style = (e.dxf.get("style") or "STANDARD").upper()
        font = fonts.get(style, "")
        val, state = decode_text((raw or "").strip(), font)
        x, y = _wcs_text_point(e)
        src = getattr(e, "source_block_reference", None)
        lay = e.dxf.layer
        if lay == "0" and src is not None:
            lay = src.dxf.layer
        h = float((e.dxf.get("char_height", 0.0) if t == "MTEXT" else e.dxf.get("height", 0.0)) or 0.0)
        out.append({"id": f"AT{n}:{e.dxf.handle}" if e.dxf.handle else f"AT{n}", "value": val, "raw": raw,
                    "encoding": state, "kind": t, "style": style, "font": _stem(font), "x": x, "y": y,
                    "layer": lay, "height": h, "tag": e.dxf.get("tag") if t == "ATTRIB" else None,
                    "owner": src.dxf.handle if src is not None else None,
                    "block": src.dxf.name if src is not None else None})
    return out


def _inserts(doc):
    from ezdxf import bbox
    out = []

    def walk(ins, path, depth):
        if depth > 8:
            return
        try:
            subs = list(ins.virtual_entities())
        except Exception:                                             # noqa: BLE001 - a block that cannot explode
            subs = []
        geo = [e for e in subs if e.dxftype() not in ("TEXT", "MTEXT", "ATTDEF", "INSERT")]
        try:
            ext = bbox.extents(geo, fast=True) if geo else None
        except Exception:                                             # noqa: BLE001
            ext = None
        p = ins.ocs().to_wcs(ins.dxf.insert)
        box = (ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y) if ext is not None and ext.has_data else None
        out.append({"id": f"I:{ins.dxf.handle}:{len(out)}", "name": ins.dxf.name, "layer": ins.dxf.layer,
                    "x": float(p.x), "y": float(p.y), "box": box, "path": list(path), "depth": depth,
                    "attribs": {a.dxf.tag: a.dxf.text for a in getattr(ins, "attribs", [])}})
        for e in subs:
            if e.dxftype() == "INSERT":
                walk(e, path + [ins.dxf.name], depth + 1)
    for ins in doc.modelspace().query("INSERT"):
        walk(ins, [], 0)
    return out


def _arc_record(e, hid, layer, path):
    sa, ea = e.dxf.start_angle, e.dxf.end_angle
    sw = (ea - sa) % 360.0 or 360.0
    s_, m_, e_ = list(e.vertices([sa, sa + sw / 2.0, sa + sw]))
    c = e.ocs().to_wcs(e.dxf.center)
    d = "CCW" if e.dxf.extrusion[2] > 0 else "CW"
    return {"id": hid, "layer": layer, "c": (c.x, c.y), "r": float(e.dxf.radius), "s": (s_.x, s_.y),
            "m": (m_.x, m_.y), "e": (e_.x, e_.y), "dir": d, "source": "S3_EXTRA", "path": path}


def _extra(doc, unit_m):
    """segments / arcs of MLINE, SPLINE and 2D POLYLINE in model space and inside blocks (any nesting; ezdxf places
    the block content, mirrored and non-uniform inserts included), with a count by type."""
    from collections import Counter
    segs, arcs, read, skipped = [], [], Counter(), Counter()
    chord = 0.001 / (unit_m or 0.001)                         # 1 mm chords

    def lay_of(e, parent_layer):
        return parent_layer if (e.dxf.layer == "0" and parent_layer) else e.dxf.layer

    def emit_line(a, b, hid, layer, path, kind):
        if (a.x, a.y) != (b.x, b.y):
            segs.append({"id": hid, "layer": layer, "a": (a.x, a.y), "b": (b.x, b.y), "path": list(path), "kind": kind})

    def walk(entities, path, parent_layer, depth):
        for e in entities:
            t = e.dxftype()
            hid = f"X:{e.dxf.handle or '?'}:{'/'.join(path)}"
            if t == "INSERT" and depth < 8:
                try:
                    walk(e.virtual_entities(), path + [e.dxf.handle or "?"], lay_of(e, parent_layer), depth + 1)
                except Exception:                                     # noqa: BLE001 - a block that cannot explode
                    skipped["INSERT_NOT_EXPLODABLE"] += 1
            elif t == "MLINE":
                read[t] += 1
                for i, v in enumerate(e.virtual_entities()):
                    if v.dxftype() == "LINE":
                        emit_line(v.dxf.start, v.dxf.end, f"{hid}:{i}", lay_of(e, parent_layer), path, "MLINE")
                    elif v.dxftype() == "ARC":
                        arcs.append(_arc_record(v, f"{hid}:{i}", lay_of(e, parent_layer), path))
            elif t == "SPLINE":
                try:
                    pts = list(e.flattening(chord))
                except Exception:                                     # noqa: BLE001
                    skipped[t] += 1
                    continue
                read[t] += 1
                for i in range(len(pts) - 1):
                    emit_line(pts[i], pts[i + 1], f"{hid}:{i}", lay_of(e, parent_layer), path, "SPLINE")
            elif t == "POLYLINE":
                if e.is_3d_polyline or e.is_poly_face_mesh or e.is_polygon_mesh:
                    skipped["POLYLINE_3D_OR_MESH"] += 1
                    continue
                read[t] += 1
                for i, v in enumerate(e.virtual_entities()):
                    if v.dxftype() == "LINE":
                        emit_line(v.dxf.start, v.dxf.end, f"{hid}:{i}", lay_of(e, parent_layer), path, "POLYLINE")
                    elif v.dxftype() == "ARC":
                        arcs.append(_arc_record(v, f"{hid}:{i}", lay_of(e, parent_layer), path))
    walk(doc.modelspace(), [], None, 0)
    return segs, arcs, dict(read), dict(skipped)


ELLIPSE_CHORD_M = 0.001


def ellipse_chords(ellipses, unit_m):
    """the K2 kernel's placed ellipses (an ELLIPSE, or a circle / arc under a non-uniform block scale) as chords with a
    sagitta of at most ELLIPSE_CHORD_M: the architectural route reads segments and circular arcs only, so an elliptical
    wall or a stretched door swing would otherwise drop out silently."""
    out = []
    tol = ELLIPSE_CHORD_M / unit_m
    for e in ellipses:
        (cx, cy), (ux, uy), (vx, vy) = e["c"], e["u"], e["v"]
        a = max(math.hypot(ux, uy), math.hypot(vx, vy))
        t0, t1 = e["t0"], e["t1"]
        if t1 <= t0:
            t1 += 2 * math.pi
        step = 2 * math.acos(max(-1.0, 1 - tol / a)) if a > tol else math.pi / 2
        n = max(2, math.ceil((t1 - t0) / max(step, 1e-6)))
        pts = [(cx + ux * math.cos(t) + vx * math.sin(t), cy + uy * math.cos(t) + vy * math.sin(t))
               for t in (t0 + (t1 - t0) * k / n for k in range(n + 1))]
        for k in range(n):
            out.append({"id": f"{e['id']}~{k}", "layer": e["layer"], "a": pts[k], "b": pts[k + 1],
                        "path": list(e.get("path") or ()), "kind": "ELLIPSE_CHORD"})
    return out


def read_arch(path, unit_m=None):
    """one read of the drawing for the architectural route: hatches, texts, inserts, extra geometry, report."""
    import ezdxf
    from collections import Counter
    doc = ezdxf.readfile(str(path))
    fonts = _style_fonts(doc)
    txt = _texts(doc, fonts)
    ins = _inserts(doc)
    segs, arcs, read, skipped = _extra(doc, unit_m)
    types = Counter(e.dxftype() for e in doc.modelspace())
    for blk in doc.blocks:
        if not blk.name.startswith("*"):
            types.update(e.dxftype() for e in blk)
    rep = {"entity_types": dict(sorted(types.items())),
           "texts": dict(Counter(t["encoding"] for t in txt)), "texts_by_kind": dict(Counter(t["kind"] for t in txt)),
           "undecoded_fonts": dict(Counter(t["font"] for t in txt if t["encoding"] == "SHX_UNMAPPED")),
           "extra_read": read, "extra_skipped": skipped, "inserts": len(ins),
           "not_read_here": sorted(t for t in types if t in ("RTEXT", "ACAD_PROXY_ENTITY", "OLE2FRAME", "IMAGE",
                                                             "WIPEOUT", "ACAD_TABLE", "MLEADER", "LEADER"))}
    return {"hatches": hatches(path, doc), "texts": txt, "inserts": ins, "extra_segments": segs, "extra_arcs": arcs,
            "report": rep}
