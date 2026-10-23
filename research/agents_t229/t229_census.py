"""T-229 census on the development villa: every beam piece of the three roof-slab plans against the drawn members
at its ends, in its cuts and under it. Writes ALSENAN_BEAM_SUPPORT_INPUT.json (DXF handles, band ids, marks, areas,
shares, lengths; no coordinates, no drawing content).

Inputs (never committed):
  - private copy of Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179...38079, the route G input),
    read with research/agents_t217/t217_extract.py (column outlines per slab plan + their S-COL.HAT hatch:
    SOLID = column under that slab = SUPPORT; pattern ANSI35 = member that STARTS on that slab = CARRIED);
  - route G band polygons in drawing metres from the committed overlays:
    `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <bands.json>`
Committed inputs read: route G PROVISIONAL_REGISTER.csv / UNRESOLVED_CONCRETE_EXCEPTIONS.csv (depth, width, state),
research/agents_t110/BEAM_MEMBER_REGISTER.csv (member, status), research/agents_t217/ALSENAN_SECTION_INPUT.json
(outline -> column instance -> released column line), research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv (ledger
joint).

    python3 -I research/agents_t229/t229_census.py <ST7757 dxf> <bands.json> [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t217"))
import beam_support as bs  # noqa: E402

SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
RG = ROOT / "research/urban_engine_m4_correctness/st7757_route_g"
SHEET = {"GFRS": "GF", "FFRS": "1F", "SFRS": "2F"}
EDGE_LAYERS = ("1", "5", "S-BEAM")   # beam edge lines on the slab plans (T-110 check 2; B26 / B27 on S-BEAM)
EDGE_TOL = 0.015          # m, an edge line lies on a gap side
PROBE = 0.03              # m, end probe beyond a piece face
GAP_REACH = 1.5           # m, two pieces of one band further apart are not one cut


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def released_dims():
    out = {}
    for r in csv.DictReader(open(RG / "PROVISIONAL_REGISTER.csv", encoding="utf-8")):
        if r["ITEM_ID"].startswith("P-C:BEAMS:") and r["UNIT"] == "m3":
            d = json.loads(r["DIMENSIONS"])
            out[r["COMPONENT_ID"].split(":", 1)[1]] = {
                "state": "RELEASED", "m3": float(r["BASE"]), "depth_m": d.get("depth_m"), "width_m": d.get("width_m"),
                "length_m": d.get("length_m")}
    for r in csv.DictReader(open(RG / "UNRESOLVED_CONCRETE_EXCEPTIONS.csv", encoding="utf-8")):
        if r["FAMILY"] == "BEAMS":
            g = dict(kv.split("=") for kv in r["GEOMETRY"].split("; ") if "=" in kv)
            out[r["COMPONENT_ID"].split(":", 1)[1]] = {
                "state": "HELD (route G " + r["BLOCKER"] + ")", "m3": None, "exposure_m3": _num(r["EXPOSURE_LOW_M3"]),
                "depth_m": _num(g.get("depth_m")), "width_m": _num(g.get("width_m")), "length_m": _num(g.get("length_m"))}
    return out


def register_t110():
    out = {}
    for r in csv.DictReader(open(ROOT / "research/agents_t110/BEAM_MEMBER_REGISTER.csv", encoding="utf-8")):
        out.setdefault(r["component"].split(":", 1)[1], []).append(r)
    return out


def _seg_cover(side, segs, tol=EDGE_TOL):
    """Share of segment `side` (a, b) covered by collinear segments."""
    a, b = side
    L = math.dist(a, b)
    if L <= 1e-9:
        return 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    iv = []
    for p, q in segs:
        dp = (p[0] - a[0]) * -u[1] + (p[1] - a[1]) * u[0]
        dq = (q[0] - a[0]) * -u[1] + (q[1] - a[1]) * u[0]
        if abs(dp) > tol or abs(dq) > tol:
            continue
        s0, s1 = sorted(((p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1], (q[0] - a[0]) * u[0] + (q[1] - a[1]) * u[1]))
        s0, s1 = max(s0, 0.0), min(s1, L)
        if s1 > s0:
            iv.append((s0, s1))
    iv.sort()
    cov, cur = 0.0, None
    for s0, s1 in iv:
        if cur is None or s0 > cur[1]:
            if cur:
                cov += cur[1] - cur[0]
            cur = [s0, s1]
        else:
            cur[1] = max(cur[1], s1)
    if cur:
        cov += cur[1] - cur[0]
    return cov / L


def _sides_along(poly, u):
    """The two sides of a quad parallel to direction u."""
    q = poly
    out = []
    for i in range(4):
        a, b = q[i], q[(i + 1) % 4]
        L = math.dist(a, b)
        if L > 1e-9 and abs((b[0] - a[0]) / L * u[0] + (b[1] - a[1]) / L * u[1]) > 0.99:
            out.append((a, b))
    return out


def extract(dxf: Path, bands: Path) -> dict:
    import ezdxf
    import t217_extract as T
    raw = dxf.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit("not the route G input (sha256 differs)")
    ex = T.extract(dxf)
    B = json.loads(bands.read_text())
    rel, t110 = released_dims(), register_t110()
    sec = json.loads((ROOT / "research/agents_t217/ALSENAN_SECTION_INPUT.json").read_text(encoding="utf-8"))
    by_handle = {}
    for i in sec["instances"]:
        for st, s in i["storeys"].items():
            for d in s.get("drawn", []):
                by_handle[d["handle"]] = (i["id"], i["mark"], i.get("engine_col_id"))
    released_cols = {}
    for r in csv.DictReader(open(RG / "PROVISIONAL_REGISTER.csv", encoding="utf-8")):
        if r["ITEM_ID"].startswith("P-C:COL:") and r["UNIT"] == "m3":
            released_cols[r["COMPONENT_ID"]] = float(r["BASE"])
    ledger = list(csv.DictReader(open(ROOT / "research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv",
                                      encoding="utf-8")))
    # beam edge segments per slab frame (drawing metres of the frame, the band coordinates)
    msp = ezdxf.readfile(str(dxf)).modelspace()
    segs = []
    for e in msp.query("LINE"):
        if e.dxf.layer not in EDGE_LAYERS:
            continue
        segs.append(((e.dxf.start.x / 1000, e.dxf.start.y / 1000), (e.dxf.end.x / 1000, e.dxf.end.y / 1000)))
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer not in EDGE_LAYERS:
            continue
        p = [(x / 1000, y / 1000) for x, y in e.get_points("xy")]
        segs += list(zip(p, p[1:] + ([p[0]] if e.closed else [])))

    members = {st: [] for st in SHEET.values()}
    outl = {}
    for r in ex["rects"]:
        if r["fr"] not in SHEET or r["hatch"] not in ("SOLID", "PATTERN"):
            continue
        st = SHEET[r["fr"]]
        kind = "COLUMN_BELOW" if r["hatch"] == "SOLID" else "CARRIED_COLUMN"
        poly = bs.rect(r["cx"] / 1000, r["cy"] / 1000, r["w"] / 1000, r["d"] / 1000)
        members[st].append(bs.Member(r["h"], kind, poly))
        outl[r["h"]] = {"storey": st, "kind": kind, "w_mm": r["w"], "d_mm": r["d"], "A_m2": r["w"] * r["d"] / 1e6}

    pieces, rings = {st: [] for st in SHEET.values()}, []
    meta = {}
    for k, v in B.items():
        bid, st = k.split("@")
        mark = v["title"].split()[0]
        bind = v["title"].split()[-1]
        key = f"{st}:{bid}"
        base = bid.split(".")[0]
        reg = t110.get(f"{st}:{bid}") or t110.get(f"{st}:{base}") or []
        dims = rel.get(f"{st}:{bid}") or {}
        meta[key] = {"storey": st, "band": bid, "mark": mark, "binding": bind, "route_g": dims.get("state", "NONE"),
                     "route_g_m3": dims.get("m3"), "route_g_held_exposure_m3": dims.get("exposure_m3"),
                     "depth_m": dims.get("depth_m"), "width_m": dims.get("width_m"),
                     "length_m": dims.get("length_m"),
                     "t110": [(r["member_id"], r["mark"], r["type"], r["status"]) for r in reg]}
        projection = any(r["status"] == "HELD" and ("strip" in r["type"] or "box" in r["type"]) and
                         r["mark"].startswith("(none)") for r in reg)
        width_conflict = any(r["status"] == "CONFLICT" for r in reg)
        meta[key]["projection"] = projection
        meta[key]["width_conflict"] = width_conflict
        if len(v["pts"]) != 4:
            rings.append(key)
            continue
        p = bs.piece_from_quad(key, mark, v["pts"], dims.get("depth_m"), beam=f"{st}:{base}")
        pieces[st].append(p)
        meta[key]["plan_m2"] = round(abs(bs.area(p.plan())), 5)

    gaps, ends, through = [], [], []
    gap_polys = {}
    for st, P in pieces.items():
        M = members[st]
        # column outline faces (both hatch kinds): a beam edge that coincides with a column face is drawn there
        out_edges = [e for m in M for e in zip(m.plan, m.plan[1:] + m.plan[:1])]
        used_ends = set()
        # gaps: consecutive collinear pieces of one band (route G split the band there)
        byb = {}
        for p in P:
            byb.setdefault(p.beam, []).append(p)
        for beam, ps in byb.items():
            if len(ps) < 2:
                continue
            u = ps[0].u
            ps.sort(key=lambda p: min(p.p0[0] * u[0] + p.p0[1] * u[1], p.p1[0] * u[0] + p.p1[1] * u[1]))
            for a, b in zip(ps, ps[1:]):
                if not bs.collinear(a, b):
                    gaps.append({"storey": st, "a": a.id, "b": b.id, "cls_hint": "NOT_COLLINEAR"})
                    continue
                g = bs.gap(a, b)
                if g is None or g[1] > GAP_REACH:
                    continue
                poly, L, w = g
                sh = bs.shares(poly, M)
                sides = _sides_along(poly, a.u)
                cov = [round(_seg_cover(s, segs), 3) for s in sides]
                # a side lying on a support outline counts as drawn there (the support face is the beam edge)
                on_sup = [round(_seg_cover(s, out_edges), 3) for s in sides]
                both = all(max(c, o) >= 0.9 for c, o in zip(cov, on_sup))
                proj = meta[a.id]["projection"] or meta[b.id]["projection"]
                gaps.append({"storey": st, "a": a.id, "b": b.id, "mark_a": a.mark, "mark_b": b.mark,
                             "length_m": round(L, 4), "width_m": round(w, 4), "area_m2": round(abs(bs.area(poly)), 5),
                             "support_share": round(sh.get("COLUMN_BELOW", 0.0), 4),
                             "carried_share": round(sh.get("CARRIED_COLUMN", 0.0), 4),
                             "other_beam_share": round(sum(bs.inter_area(q.plan(), poly) for q in P
                                                           if q.beam != a.beam) / abs(bs.area(poly)), 4),
                             "other_beams": [q.id for q in P if q.beam != a.beam and
                                             bs.inter_area(q.plan(), poly) > 1e-6],
                             "members": [(h, k, s) for h, k, s in sh.get("ids", [])],
                             "edge_line_cover": cov, "outline_face_cover": on_sup, "edges_continuous": both,
                             "depth_m": a.depth if a.depth == b.depth else None,
                             "depth_note": None if a.depth == b.depth else f"pieces differ {a.depth} / {b.depth}",
                             "projection": proj,
                             "width_conflict": meta[a.id]["width_conflict"] or meta[b.id]["width_conflict"]})
                gap_polys.setdefault(st, []).append((f"gap {a.id.split(':')[1]}|{b.id.split(':')[1]}", poly))
                used_ends.add((a.id, "far"))
                used_ends.add((b.id, "near"))
        # ends: every piece face that is not one side of a gap
        for p in P:
            for e in (0, 1):
                c = p.p0 if e == 0 else p.p1
                d = (-p.u[0], -p.u[1]) if e == 0 else p.u
                n = (-d[1] * p.width * 0.45, d[0] * p.width * 0.45)
                probe = bs._ccw([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1]),
                                 (c[0] + d[0] * PROBE + n[0], c[1] + d[1] * PROBE + n[1]),
                                 (c[0] + d[0] * PROBE - n[0], c[1] + d[1] * PROBE - n[1])])
                # skip faces that open onto a gap of the same band
                other_same = [q for q in P if q.beam == p.beam and q is not p and bs.collinear(p, q)]
                if any(bs.inter_area(q.plan(), _probe(c, d, p.width, GAP_REACH)) > 1e-6
                       for q in other_same):
                    continue
                hit = []
                for m in M:
                    if bs.inter_area(m.plan, probe) > 1e-6:
                        hit.append((m.id, m.kind))
                for q in P:
                    if q is not p and q.beam != p.beam and bs.inter_area(q.plan(), probe) > 1e-6:
                        hit.append((q.id, "PROJECTION" if meta[q.id]["projection"] else "BEAM"))
                for gid, gp in gap_polys.get(st, []):
                    if bs.inter_area(gp, probe) > 1e-6 and p.id.split(':')[1] not in gid:
                        hit.append((gid, "BEAM"))
                for rk in rings:
                    rp = [tuple(x) for x in B[rk.split(":")[1] + "@" + rk.split(":")[0]]["pts"]]
                    if _touch_any(rp, probe):
                        hit.append((rk, "RING"))
                kinds = {k for _, k in hit}
                # a beam that lands on the piece's side faces near this end: the piece owns the junction square and
                # its end face is flush with the outer face of the crossing line (route G 'junction squares owned
                # by one band')
                side_hits = []
                for sgn in (-1, 1):
                    m_ = (-p.u[1] * sgn, p.u[0] * sgn)
                    h0 = (c[0] + m_[0] * p.width / 2, c[1] + m_[1] * p.width / 2)
                    back = (h0[0] - d[0] * p.width, h0[1] - d[1] * p.width)
                    sp = bs._ccw([h0, back, (back[0] + m_[0] * PROBE, back[1] + m_[1] * PROBE),
                                  (h0[0] + m_[0] * PROBE, h0[1] + m_[1] * PROBE)])
                    for q in P:
                        if q is not p and q.beam != p.beam and bs.inter_area(q.plan(), sp) > 1e-6:
                            side_hits.append(q.id)
                # a support under the end zone of the piece (the piece runs onto / over the column)
                zone = _probe(c, (-d[0], -d[1]), p.width, 0.6)
                over = [m.id for m in M if m.kind in bs.SUPPORT_KINDS and
                        bs.inter_area(m.plan, zone) / abs(bs.area(m.plan)) > bs.NET_MAX]
                touch = ("SUPPORT" if kinds & set(bs.SUPPORT_KINDS) else "BEAM" if kinds & {"BEAM", "RING"}
                         else "CARRIED" if "CARRIED_COLUMN" in kinds else "PROJECTION" if "PROJECTION" in kinds
                         else "OVER_SUPPORT" if over else "JUNCTION_OWNER" if side_hits else "NONE")
                rec = {"storey": st, "piece": p.id, "mark": p.mark, "end": e, "touch": touch, "members": hit,
                       "depth_m": p.depth}
                if over:
                    rec["over_support"] = over
                if side_hits:
                    rec["side_beams"] = side_hits
                if touch != "PROJECTION":
                    rec.update(_beyond(p, e, touch, M, P, gap_polys.get(st, []), rings, B, segs, out_edges))
                ends.append(rec)
        # members under a piece (billed through or partly)
        for m in M:
            for p in P:
                s = bs.inter_area(m.plan, p.plan()) / abs(bs.area(m.plan))
                if s > bs.NET_MAX:
                    o = outl[m.id]
                    inst = by_handle.get(m.id)
                    col_released = released_cols.get(f"{inst[2]}|{st}") if inst and inst[2] else None
                    led = [r for r in ledger if r["storey"] == st and
                           math.hypot(float(r["x"]) - bs_centre(m.plan)[0], float(r["y"]) - bs_centre(m.plan)[1]) < 0.2]
                    through.append({"storey": st, "outline": m.id, "kind": m.kind, "A_m2": o["A_m2"],
                                    "piece": p.id, "mark": p.mark, "share": round(s, 4), "depth_m": p.depth,
                                    "column_instance": inst[0] if inst else None, "column_mark": inst[1] if inst else None,
                                    "released_column_m3": col_released,
                                    "ledger": [{"id": r["id"], "joint_m3_lo": _num(r["joint_m3_lo"]),
                                                "joint_m3_hi": _num(r["joint_m3_hi"]), "status": r["status"]}
                                               for r in led]})
    counts = {st: {"pieces": len(P), "supports": sum(m.kind == "COLUMN_BELOW" for m in members[st]),
                   "carried": sum(m.kind == "CARRIED_COLUMN" for m in members[st])} for st, P in pieces.items()}
    return {"schema": "T229_BEAM_SUPPORT_INPUT_V1", "source_dxf_sha256": SHA,
            "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' + route G overlays (committed)",
            "counts": counts, "rings": rings, "outlines": outl, "pieces": meta, "gaps": gaps, "ends": ends,
            "through": through}


def _probe(c, d, width, reach):
    n = (-d[1] * width * 0.45, d[0] * width * 0.45)
    return bs._ccw([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1]),
                    (c[0] + d[0] * reach + n[0], c[1] + d[1] * reach + n[1]),
                    (c[0] + d[0] * reach - n[0], c[1] + d[1] * reach - n[1])])


def _beyond(p, end, touch, M, P, gpolys, rings, B, segs, out_edges):
    """Concrete of the drawn beam beyond a piece's end face that no line bills: the part of a strip of the beam's
    width beyond the face, bounded by the members the beam frames into (supports, other beams, cut regions of other
    beams). A member the beam carries does not bound it. Measured with polygon booleans (shapely, census only)."""
    from shapely.geometry import Polygon, LineString
    from shapely.ops import unary_union
    reach = 2.0 if touch == "CARRIED" else 0.8
    strip = Polygon(_box(p, end, reach))
    stops = [Polygon(m.plan) for m in M if m.kind != "CARRIED_COLUMN"]
    stops += [Polygon(q.plan()) for q in P if q is not p and q.beam != p.beam]
    stops += [Polygon(gp) for gid, gp in gpolys if p.id.split(":")[1] not in gid]
    for rk in rings:
        st, band = rk.split(":")
        stops.append(Polygon(B[band + "@" + st]["pts"]).buffer(0))
    free = strip.difference(unary_union(stops).buffer(0))
    c = p.p0 if end == 0 else p.p1
    d = (-p.u[0], -p.u[1]) if end == 0 else p.u
    n = (-d[1] * p.width / 2, d[0] * p.width / 2)
    face = LineString([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1])]).buffer(0.002)
    comps = [g for g in getattr(free, "geoms", [free]) if not g.is_empty and g.intersects(face)]
    if not comps:
        return {"beyond_area_m2": 0.0, "beyond_closed": True}
    g = unary_union(comps)
    far = LineString([(c[0] + d[0] * reach - n[0], c[1] + d[1] * reach - n[1]),
                      (c[0] + d[0] * reach + n[0], c[1] + d[1] * reach + n[1])]).buffer(0.002)
    closed = not g.intersects(far)
    # extent of the region along each lateral side of the beam, and the drawn-edge cover of that side
    ts, cov = [], []
    for k in (-1, 1):
        side = LineString([(c[0] + k * n[0] * 0.995, c[1] + k * n[1] * 0.995),
                           (c[0] + d[0] * reach + k * n[0] * 0.995, c[1] + d[1] * reach + k * n[1] * 0.995)])
        part = g.intersection(side)
        t = 0.0
        if not part.is_empty:
            t = max((q[0] - c[0]) * d[0] + (q[1] - c[1]) * d[1] for q in
                    [pt for geom in getattr(part, "geoms", [part]) for pt in geom.coords])
        ts.append(round(t, 4))
        a0 = (c[0] + k * n[0], c[1] + k * n[1])
        a1 = (a0[0] + d[0] * t, a0[1] + d[1] * t)
        cov.append(round(max(_seg_cover((a0, a1), segs), _seg_cover((a0, a1), out_edges)), 3) if t > 0.005 else 1.0)
    return {"beyond_area_m2": round(g.area, 5), "beyond_closed": closed, "beyond_side_t_m": ts,
            "beyond_edge_cover": cov}


def _box(p, end, L):
    c = p.p0 if end == 0 else p.p1
    d = (-p.u[0], -p.u[1]) if end == 0 else p.u
    n = (-d[1] * p.width / 2, d[0] * p.width / 2)
    return bs._ccw([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1]),
                    (c[0] + d[0] * L + n[0], c[1] + d[1] * L + n[1]), (c[0] + d[0] * L - n[0], c[1] + d[1] * L - n[1])])


def bs_centre(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def _touch_any(poly, probe):
    """A ring band (non-convex arc polygon) touching the probe: any ring vertex or probe vertex inside the other."""
    def inside(pt, pg):
        x, y = pt
        c = False
        for i in range(len(pg)):
            a, b = pg[i], pg[i - 1]
            if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
                c = not c
        return c
    return any(inside(q, probe) for q in poly) or any(inside(q, poly) for q in probe)


if __name__ == "__main__":
    out = extract(Path(sys.argv[1]), Path(sys.argv[2]))
    if "--write" in sys.argv:
        (HERE / "ALSENAN_BEAM_SUPPORT_INPUT.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"]), len(out["gaps"]), "gaps", len(out["ends"]), "ends", len(out["through"]), "under")
