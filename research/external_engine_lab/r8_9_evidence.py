"""R8.9 lab: positive PLACEMENT evidence for source entities the kernels do not realise (ACIS REGION / BODY /
3DSOLID). The engine never infers an unrealised entity's location from the absence of realised peers; this module
reads the entity's OWN geometry where the source carries it and supplies a world extent.

ACIS evidence (both routes read the same source entity; the extent is keyed by source handle):
  K1  the pinned LibreDWG decode keeps the binary ACIS body (acis_data = ["ACIS BinaryFile", <hex>])
  K2  an AutoCAD-family DXF keeps it in its ACDSDATA section (ezdxf Region.sab)
A SPLINE's extent is the bbox of its control points (convex hull; rational only with positive weights).
The ACIS extent = bbox of every vertex point and every B-spline (nubs) control point of the body, mapped through the
body's ACIS transform (rotation rows, translation, scale). A B-spline lies inside the convex hull of its control
points, so the bbox is a rigorous bound of the body (straight edges end at vertices). Anything not understood ->
no extent (the entity stays unplaced and fails closed)."""

from __future__ import annotations

from ezdxf.acis import sab

SAB_SIGNATURE = b"ACIS BinaryFile"
SAB_SIGNATURES = (b"ACIS BinaryFile", b"ASM BinaryFile")      # ACIS SAB and the newer ASM SAB (AutoCAD 2013+)


def _transform(body):
    tr = [e for e in body.entities if e.name == "transform"]
    if len(tr) > 1:
        return None
    if not tr:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0), 1.0
    vec = [t.value for t in tr[0].data if t.tag == 20]
    sc = [t.value for t in tr[0].data if t.tag == 6]
    if len(vec) != 4 or len(sc) < 1:
        return None
    return tuple(vec[:3]), vec[3], float(sc[0])


def acis_extent(raw: bytes):
    """World (x0, y0, x1, y1) of one ACIS body (SAB bytes, with or without the signature), or None."""
    if not raw:
        return None
    if not raw.startswith(SAB_SIGNATURES):            # LibreDWG strips the signature into its own field
        raw = SAB_SIGNATURE + raw
    try:
        body = sab.parse_sab(raw)
    except Exception:                                   # noqa: BLE001 - unreadable body: no evidence
        return None
    tf = _transform(body)
    if tf is None:
        return None
    rows, trans, scale = tf
    pts = []
    for e in body.entities:
        if e.name == "point":
            pts += [t.value for t in e.data if t.tag == 19]
        elif e.name.endswith("curve") and e.name != "straight-curve":
            run = []
            for t in e.data + [None]:
                if t is not None and t.tag == 6 and isinstance(t.value, float):
                    run.append(t.value)
                    continue
                if len(run) >= 3:                        # control points: (x, y, z) triples (a trailing fit
                    n = len(run) // 3 * 3                # tolerance double is dropped)
                    pts += [tuple(run[k:k + 3]) for k in range(0, n, 3)]
                run = []
    if not pts:
        return None
    world = []
    for x, y, z in pts:                                 # ACIS row-vector convention: p' = (p R) s + t
        wx = (x * rows[0][0] + y * rows[1][0] + z * rows[2][0]) * scale + trans[0]
        wy = (x * rows[0][1] + y * rows[1][1] + z * rows[2][1]) * scale + trans[1]
        world.append((wx, wy))
    xs, ys = [p[0] for p in world], [p[1] for p in world]
    return (min(xs), min(ys), max(xs), max(ys))


def spline_extent(ctrl, weights=None):
    """Convex-hull bound of a (rational) B-spline: the bbox of its control points, valid only when every weight is
    positive (a NURBS with positive weights lies inside the convex hull of its control points)."""
    if not ctrl or (weights is not None and any(w is None or not w > 0 for w in weights)):
        return None
    xs, ys = [float(p[0]) for p in ctrl], [float(p[1]) for p in ctrl]
    return (min(xs), min(ys), max(xs), max(ys))


def k1_acis_extents(decode: dict) -> dict:
    """{source handle (decimal str): extent} from the pinned LibreDWG decode (ACIS bodies and splines)."""
    out = {}
    for o in decode.get("OBJECTS", []):
        if o.get("entity") == "SPLINE" and isinstance(o.get("handle"), list) and isinstance(o.get("ctrl_pts"), list):
            cp = o["ctrl_pts"]
            if all(isinstance(c, dict) and "x" in c and "y" in c for c in cp):
                ext = spline_extent([(c["x"], c["y"]) for c in cp],
                                    [c.get("w", 1.0) for c in cp] if o.get("rational") else None)
                if ext is not None:
                    out[str(o["handle"][-1])] = ext
    for o in decode.get("OBJECTS", []):
        if o.get("entity") in ("REGION", "BODY", "3DSOLID") and isinstance(o.get("acis_data"), list):
            h = o.get("handle")
            ad = o["acis_data"]
            if not (isinstance(h, list) and len(ad) >= 2 and ad[0] == "ACIS BinaryFile"):
                continue
            try:
                raw = bytes.fromhex("".join(ad[1:]))
            except ValueError:
                continue
            ext = acis_extent(raw)
            if ext is not None:
                out[str(h[-1])] = ext
    return out


def k2_acis_extents(doc) -> dict:
    """{source handle (decimal str): extent} from an ezdxf document (AutoCAD-family DXF with ACDSDATA)."""
    out = {}
    for e in doc.modelspace():
        if e.dxftype() == "SPLINE":
            cp = [tuple(v) for v in e.control_points]
            w = list(e.weights) if len(e.weights) else None
            ext = spline_extent(cp, w)
            if ext is not None:
                out[str(int(e.dxf.handle, 16))] = ext
            continue
        if e.dxftype() in ("REGION", "BODY", "3DSOLID"):
            raw = getattr(e, "sab", b"") or b""
            ext = acis_extent(bytes(raw)) if raw else None
            if ext is not None:
                out[str(int(e.dxf.handle, 16))] = ext
    return out


def attach(unrealised, extents, basis):
    """Unrealised records with their placement evidence (only where the source carries it)."""
    out = []
    for u in unrealised:
        h = (u.get("obs_id") or "").split(":")[-1]
        if not u.get("path") and h in extents:
            out.append(dict(u, extent=list(extents[h]), extent_basis=basis))
        else:
            out.append(u)
    return out
