"""DRAWING INVENTORY (M1) - what a DXF holds, before any quantity (generic).

inventory(doc, path)     sha256, DXF version and units, every layer with its entity counts by type, the sheet frames
                         (outermost closed axis-aligned rectangles at least `min_frame` in size), the text tag families
                         (short codes such as F3, C12, GB2 grouped by prefix, per layer and per frame), the block
                         inserts by name, and the closed rectangles per layer (candidate members).
                         A layer gets a ROLE GUESS from its name only; the guess is never used as a quantity authority.
profile_template(inv)    a starting profile for profile_takeoff: every guess marked UNCONFIRMED, every value a person
                         must supply (storey of each sheet, schedule rows, storey heights) left empty, never defaulted.
segments(doc, layers, box) / texts(doc, box)
                         the drawn segments of some layers and the text items inside a frame, in drawing units, for
                         profile_takeoff (straight edges only; an arc or a bulge is reported, not straightened).

The caller opens the DXF (ezdxf.readfile) and passes the document in; it is used by duck typing, so this module imports
no third-party library (engine/source stays stdlib-only). Everything returned is plain data.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict

POLICY_ID = "DRAWING_INVENTORY_V1"
TAG_RE = re.compile(r"^([A-Z]{1,3})[-.]?(\d{1,3}[A-Z]?)$")
ROLE_KEYWORDS = (                   # first match wins: annotation roles before member roles
    ("REBAR", ("REBAR", "REIN", "BAR")),
    ("TEXT", ("TEXT", "TXT", "ANNO", "NOTE")),
    ("DIMENSION", ("DIM",)),
    ("HATCH", ("HATCH", ".HAT")),
    ("FRAME", ("DEFPOINTS", "FRAME", "BORDER", "TITLE", "SHEET")),
    ("GRID", ("GRID", "AXIS", "AXES")),
    ("FOOTING", ("FOOT", "FTG", "FDN", "FOUND", "PILE CAP", "PAD")),
    ("GROUND_BEAM", ("GRADE", "G-B", "GB", "TIE BEAM", "STRAP", "PLINTH")),
    ("COLUMN", ("COL", "PIER")),
    ("BEAM", ("BEAM", "BM", "LINTEL")),
    ("SLAB", ("SLAB", "DECK")),
    ("WALL", ("WALL", "SHEAR", "CORE")),
    ("STAIR", ("STAIR", "STEP")),
)
TAG_FAMILY_GUESS = {"F": "FOOTINGS", "PC": "FOOTINGS", "C": "COLUMNS", "B": "BEAMS", "CB": "BEAMS", "GB": "GROUND_BEAMS",
                    "SB": "GROUND_BEAMS", "TB": "GROUND_BEAMS", "S": "SLABS", "L": "LINTELS", "W": "WALLS"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def role_guess(layer_name):
    n = layer_name.upper()
    for role, keys in ROLE_KEYWORDS:
        if any(k in n for k in keys):
            return role
    return "UNKNOWN"


def _pts(e):
    """Vertices of a closed straight LWPOLYLINE / POLYLINE, or None (open, curved or another type)."""
    t = e.dxftype()
    if t == "LWPOLYLINE":
        if not e.closed:
            return None
        pts = list(e.get_points("xyb"))
        if any(abs(b) > 1e-12 for _, _, b in pts):
            return None
        return [(float(x), float(y)) for x, y, _ in pts]
    if t == "POLYLINE" and e.is_2d_polyline and e.is_closed:
        vs = list(e.vertices)
        if any(abs(v.dxf.get("bulge", 0.0)) > 1e-12 for v in vs):
            return None
        return [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in vs]
    return None


def axis_rect(pts, eps=1e-6):
    """(x0, y0, x1, y1) when the closed outline is an axis-aligned rectangle (a repeated closing vertex allowed)."""
    if pts is None:
        return None
    if len(pts) == 5 and math.dist(pts[0], pts[-1]) <= eps:
        pts = pts[:4]
    if len(pts) != 4:
        return None
    xs, ys = sorted({round(p[0] / eps) * eps for p in pts}), sorted({round(p[1] / eps) * eps for p in pts})
    if len(xs) != 2 or len(ys) != 2:
        return None
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if abs(ax - bx) > eps and abs(ay - by) > eps:
            return None
    return (xs[0], ys[0], xs[1], ys[1])


def _layer(e):
    """An entity's layer; an unsupported entity (e.g. RTEXT) carries none and is counted under '?'."""
    try:
        return e.dxf.layer
    except AttributeError:
        return "?"


def _inside(box, x, y):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def _contains(a, b):
    return a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3] and a != b


def text_items(msp):
    """Every TEXT / MTEXT value and every attribute value of an INSERT: {key, value, x, y, layer, kind}."""
    out = []
    for e in msp.query("TEXT MTEXT INSERT"):
        t = e.dxftype()
        if t == "TEXT":
            p = e.dxf.insert
            out.append({"key": e.dxf.handle, "value": e.dxf.text.strip(), "x": p.x, "y": p.y, "layer": e.dxf.layer,
                        "kind": "TEXT"})
        elif t == "MTEXT":
            p = e.dxf.insert
            out.append({"key": e.dxf.handle, "value": e.plain_text().strip(), "x": p.x, "y": p.y,
                        "layer": e.dxf.layer, "kind": "MTEXT"})
        else:
            for a in e.attribs:
                p = a.dxf.insert
                out.append({"key": a.dxf.handle, "value": a.dxf.text.strip(), "x": p.x, "y": p.y,
                            "layer": a.dxf.layer, "kind": "ATTRIB", "tag": a.dxf.tag, "owner": e.dxf.name})
    return out


def frames(msp, min_frame=(10000.0, 7000.0)):
    """Sheet frames: outermost closed axis-aligned rectangles at least min_frame (w, h) in drawing units."""
    boxes = []
    for e in msp.query("LWPOLYLINE POLYLINE"):
        b = axis_rect(_pts(e))
        if b and b[2] - b[0] >= min_frame[0] and b[3] - b[1] >= min_frame[1]:
            boxes.append((b, e.dxf.handle, e.dxf.layer))
    outer = [x for x in boxes if not any(_contains(y[0], x[0]) for y in boxes)]
    seen, out = set(), []
    for b, h, layer in sorted(outer):
        if b in seen:
            continue
        seen.add(b)
        out.append({"frame_id": f"FR{len(out) + 1:02d}", "handle": h, "layer": layer, "box": [round(v, 3) for v in b]})
    return out


def _title_guess(texts_in):
    words = ("PLAN", "SCHEDULE", "DETAIL", "SECTION", "ELEVATION", "LAYOUT", "FOUNDATION", "ROOF", "FLOOR")
    cands = [t["value"] for t in texts_in if any(w in t["value"].upper() for w in words) and len(t["value"]) <= 80]
    return sorted(cands, key=lambda s: (-len(s), s))[:3]


def inventory(doc, path, min_frame=(10000.0, 7000.0)):
    msp = doc.modelspace()
    by_layer = defaultdict(Counter)
    rects = defaultdict(list)
    curved = Counter()
    for e in msp:
        by_layer[_layer(e)][e.dxftype()] += 1
        if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            p = _pts(e)
            b = axis_rect(p)
            if b:
                rects[e.dxf.layer].append(b)
            elif p is None and getattr(e, "closed", False):
                curved[e.dxf.layer] += 1
    texts = text_items(msp)
    fr = frames(msp, min_frame)
    for f in fr:
        inside = [t for t in texts if _inside(f["box"], t["x"], t["y"])]
        f["n_texts"] = len(inside)
        f["title_guess"] = _title_guess(inside)
        f["inserts"] = dict(sorted(Counter(i.dxf.name for i in msp.query("INSERT")
                                           if _inside(f["box"], i.dxf.insert.x, i.dxf.insert.y)).items()))
    tags = defaultdict(lambda: {"count": 0, "values": Counter(), "layers": Counter(), "frames": Counter()})
    for t in texts:
        m = TAG_RE.match(t["value"].upper())
        if not m:
            continue
        g = tags[m.group(1)]
        g["count"] += 1
        g["values"][t["value"].upper()] += 1
        g["layers"][t["layer"]] += 1
        fid = next((f["frame_id"] for f in fr if _inside(f["box"], t["x"], t["y"])), "OUTSIDE_FRAMES")
        g["frames"][fid] += 1
    layers = []
    for lay in sorted(by_layer):
        c = by_layer[lay]
        layers.append({"layer": lay, "role_guess": role_guess(lay), "n_entities": sum(c.values()),
                       "by_type": dict(sorted(c.items())), "closed_rectangles": len(rects[lay]),
                       "closed_curved_outlines": curved[lay],
                       "texts": sum(1 for t in texts if t["layer"] == lay)})
    tag_rows = [{"prefix": k, "family_guess": TAG_FAMILY_GUESS.get(k, "UNKNOWN"), "count": v["count"],
                 "distinct": len(v["values"]), "examples": sorted(v["values"])[:8],
                 "layers": dict(v["layers"].most_common(4)), "frames": dict(sorted(v["frames"].items()))}
                for k, v in sorted(tags.items(), key=lambda kv: (-kv[1]["count"], kv[0]))]
    return {"policy": POLICY_ID, "file": str(path), "sha256": sha256_file(path), "dxf_version": doc.dxfversion,
            "insunits": doc.header.get("$INSUNITS", 0), "n_entities": sum(sum(c.values()) for c in by_layer.values()),
            "n_layers": len(layers), "layers": layers, "frames": fr, "tag_families": tag_rows,
            "blocks_inserted": dict(sorted(Counter(i.dxf.name for i in msp.query("INSERT")).items())),
            "n_texts": len(texts)}


def profile_template(inv):
    """A starting profile. Every guess says UNCONFIRMED; nothing a person must read off the drawing is filled in."""
    fam_layers = defaultdict(list)
    for lay in inv["layers"]:
        if lay["role_guess"] in ("FOOTING", "COLUMN") and lay["closed_rectangles"]:
            fam_layers[lay["role_guess"]].append(lay["layer"])
    fam_tags = defaultdict(list)
    for t in inv["tag_families"]:
        fam_tags[t["family_guess"]].append(t["prefix"])
    return {
        "profile": "NEW_PROJECT_PROFILE_UNCONFIRMED", "drawing_sha256": inv["sha256"], "units_to_mm": None,
        "_note": "Fill every null; confirm every guess. A null leaves that part UNRESOLVED, it is never defaulted.",
        "sheets": [{"sheet_id": f["frame_id"], "box": f["box"], "title_guess": f["title_guess"], "storey": None,
                    "storey_height_m": None, "storey_height_source": None} for f in inv["frames"]],
        "families": {
            "FOOTINGS": {"layers": fam_layers.get("FOOTING", []), "layers_state": "UNCONFIRMED_GUESS",
                         "tag_regex": "^(" + "|".join(sorted(fam_tags.get("FOOTINGS", ["F"]))) + r")\d+[A-Z]?$",
                         "sheets": [], "schedule": {}, "schedule_source": None, "size_tol_mm": 10},
            "COLUMNS": {"layers": fam_layers.get("COLUMN", []), "layers_state": "UNCONFIRMED_GUESS",
                        "tag_regex": "^(" + "|".join(sorted(fam_tags.get("COLUMNS", ["C"]))) + r")\d+[A-Z]?$",
                        "sheets": [], "schedule": {}, "schedule_source": None, "size_tol_mm": 10},
        },
    }


def segments(doc, layers, box=None):
    """Straight drawn segments (key, x1, y1, x2, y2) on the layers, inside box when given; curved edges counted."""
    msp = doc.modelspace()
    out, curved = [], 0
    for e in msp.query("LINE LWPOLYLINE POLYLINE"):
        if e.dxf.layer not in layers:
            continue
        t = e.dxftype()
        if t == "LINE":
            s, f = e.dxf.start, e.dxf.end
            segs = [(s.x, s.y, f.x, f.y)]
        elif t == "LWPOLYLINE":
            pts = list(e.get_points("xyb"))
            n = len(pts) if e.closed else len(pts) - 1
            segs = []
            for i in range(n):
                (x1, y1, b), (x2, y2, _) = pts[i], pts[(i + 1) % len(pts)]
                if abs(b) > 1e-12:
                    curved += 1
                    continue
                segs.append((x1, y1, x2, y2))
        else:
            if not e.is_2d_polyline:
                continue
            vs = [(v.dxf.location.x, v.dxf.location.y, v.dxf.get("bulge", 0.0)) for v in e.vertices]
            n = len(vs) if e.is_closed else len(vs) - 1
            segs = []
            for i in range(n):
                (x1, y1, b), (x2, y2, _) = vs[i], vs[(i + 1) % len(vs)]
                if abs(b) > 1e-12:
                    curved += 1
                    continue
                segs.append((x1, y1, x2, y2))
        for j, (x1, y1, x2, y2) in enumerate(segs):
            if box and not (_inside(box, x1, y1) and _inside(box, x2, y2)):
                continue
            out.append((f"{e.dxf.handle}:{j}", float(x1), float(y1), float(x2), float(y2)))
    return out, curved


def texts(doc, box=None):
    return [t for t in text_items(doc.modelspace()) if box is None or _inside(box, t["x"], t["y"])]


def policy_record():
    return {"policy": POLICY_ID, "rule": "an inventory counts and guesses; a guess is never a quantity authority",
            "role_keywords": [r for r, _ in ROLE_KEYWORDS], "tag_pattern": TAG_RE.pattern}
