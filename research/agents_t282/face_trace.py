"""T-282 face tracing (research only, NOT engine code, nothing wired): the side and end faces of plan members (beam /
ground-beam bands, curved bands) closed on their carriers' drawn faces on EACH of their own edges.

Physical element (ENGINEERING_REASONING_STANDARD s.2.1): a beam side face is the concrete surface along one drawn
edge line of the member, between the faces of the members it meets on THAT edge. Rules (proposed, research scope, any
villa; every face-tracing trade: formwork, waterproofing, plaster):

  R-FACE-CLOSE-1  A member ends on its carrier's drawn face on each of its own edges (oblique, curved carrier, column).
                  A span cut square at one station (the shorter edge's, or the support's outermost) is refused: it
                  invents an end face and an earth pocket and shortens the longer edge.
  R-FACE-SNAP-1   An offset thinner than SNAP_MM (1 mm) between two outlines is not a member: a column outline 0.05 mm
                  inside a band edge is the column's face (neck / column line), never a beam face. Faces 1 mm or more
                  apart are two faces. A curved face is never snapped to a straight one at a tangent point.
  R-FACE-OWN-1    One owner per face piece (R-CONC-OWN-1): column faces, then other owners (lift / pit walls), then the
                  member edge the piece lies on, then a member's own end. A face inside a junction zone (tee, crossing,
                  a band framing into a ring) is no face at all; a tee covers its carrier over the incoming band's
                  width ON the carrier face (b / sin(angle); on an arc: the arc between the incoming edges' hits).
  R-FACE-END-1    An end face exists only where a member stops with nothing against it (free end, gap to a column,
                  end on a footing below); an end piece left by a drawn line that stops short of a named carrier is
                  closed onto the carrier (up to CLOSE_CAP x the member width) and is never an end face.

Inputs are plain geometry (mm), so the same function runs on a synthetic villa and on the development villa's DXF
(t282_extract.py). Output lengths in m."""
from __future__ import annotations

import math

SNAP_MM = 1.0
CLOSE_CAP = 2.0        # a drawn edge stopping short of its named carrier is closed only within 2 x the member width


class Refused(ValueError):
    """an input or a result the rules do not accept."""


def _dot(p, v):
    return p[0] * v[0] + p[1] * v[1]


def snap_owner(offset_mm, tol=SNAP_MM):
    """R-FACE-SNAP-1: offset between a column face and a parallel band edge -> 'COLUMN_FACE' (the column owns the
    face; the strip between them is not a member) or 'TWO_FACES'. A negative tolerance or a tolerance of 5 mm or more
    (the size of a real member) is refused."""
    if not 0 < tol < 5.0:
        raise Refused("snap tolerance %r mm is not a drafting tolerance" % tol)
    return "COLUMN_FACE" if abs(offset_mm) < tol else "TWO_FACES"


def tee_width_on_carrier(b_in, angle_deg):
    """the width an incoming band of width b_in covers on a straight carrier face it meets at angle_deg (90 = square)."""
    if not 0 < angle_deg <= 90:
        raise Refused("tee angle %r" % angle_deg)
    return b_in / math.sin(math.radians(angle_deg))


def square_cut_refused(La, Lb, billed_a, billed_b, tol=1e-4):
    """R-FACE-CLOSE-1 check of a billed pair of side lengths against the two traced edges (m)."""
    if abs(billed_a - La) > tol or abs(billed_b - Lb) > tol:
        raise Refused("billed sides %.4f / %.4f differ from the traced edges %.4f / %.4f (square cut)" % (
            billed_a, billed_b, La, Lb))
    return True


def trace(members, columns, arcs=None, others=None, snap=SNAP_MM, close_cap=CLOSE_CAP):
    """members: {id: {"edges": {"A": (p0, p1), "B": (p0, p1)}, "width": mm,
                      "spans": [(s0_m, s1_m, span_id)]  (face-to-face stations along u, m; one span = whole member),
                      "ends": {"start": {"kind": KIND, "carriers": [ids]}, "end": {...}}}}
         KIND in COLUMN / BEAM_JUNCTION / FREE_END / FOOTING_FACE / GAP_TO_COLUMN; "start" is the low-station end.
       columns / others: {id: [(x, y), ...]} outlines; arcs: {id: {"cx", "cy", "radii": {h: R}, "ranges": {h: (a0, a1)}}}
    -> dict(sides={(span_id, side): m}, ends={(span_id, end kind): m}, columns={id: m},
            others={id: m}, arcs={(arc_id, h): m}, closed=[...], held=[...], pieces=[...], gaps=[...])."""
    from shapely.geometry import LineString, MultiPoint, Point, Polygon, box
    from shapely.ops import unary_union

    arcs = arcs or {}
    others = others or {}
    col = {k: Polygon(v).buffer(0) for k, v in columns.items()}
    oth = {k: Polygon(v).buffer(0) for k, v in others.items()}

    def arc_region(ab, step=0.1):
        hs = sorted(ab["radii"], key=lambda h: -ab["radii"][h])
        pts = []
        for k, h in enumerate(hs):
            a0, a1 = ab["ranges"][h]
            if a1 < a0:
                a1 += 360.0
            m = max(8, int((a1 - a0) / step))
            seq = [a0 + (a1 - a0) * i / m for i in range(m + 1)]
            if k == 1:
                seq = seq[::-1]
            R = ab["radii"][h]
            pts += [(ab["cx"] + R * math.cos(math.radians(t)), ab["cy"] + R * math.sin(math.radians(t))) for t in seq]
        return Polygon(pts).buffer(0)
    arc_poly = {k: arc_region(v) for k, v in arcs.items()}

    frame = {}
    for mid, m in members.items():
        (a0, a1) = m["edges"]["A"]
        L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
        u = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
        n = (-u[1], u[0])
        oA = (_dot(a0, n) + _dot(a1, n)) / 2.0
        oB = (_dot(m["edges"]["B"][0], n) + _dot(m["edges"]["B"][1], n)) / 2.0
        frame[mid] = (u, n, oA, oB)

    def local(mid, P):
        u, n, _, _ = frame[mid]
        return Polygon([(_dot(p, u), _dot(p, n)) for p in P.exterior.coords]).buffer(0)

    def first_hit(t_from, off, sign, far, polys, snap_):
        """first station where the edge o = off meets one of polys, read on the two lines o = off -+ snap: the mean
        of the hits found (a straight oblique face: exactly its station at o = off; a face parallel to the edge within
        the snap: the one line inside it gives the face's own extent; a face drawn a hair out of parallel never reads
        as a crossing). None when neither line meets a carrier within `far`."""
        hits = []
        for o2 in (off - snap_, off + snap_):
            ln = LineString([(t_from, o2), (t_from + sign * far, o2)])
            best_ = None
            for P in polys:
                X = ln.intersection(P)
                if X.is_empty:
                    continue
                ts = [c[0] for g in getattr(X, "geoms", [X]) for c in g.coords]
                t = min(ts) if sign == 1 else max(ts)
                if best_ is None or (t - best_) * sign < 0:
                    best_ = t
            if best_ is not None:
                hits.append(best_)
        return sum(hits) / len(hits) if hits else None

    # 1. close each edge on its named carrier at junction ends (R-FACE-CLOSE-1 / R-FACE-END-1)
    closed, held = [], []
    edges_c = {}
    for mid, m in members.items():
        u, n, oA, oB = frame[mid]
        width = abs(oB - oA)
        hull_pts = []
        edges_c[mid] = {}
        for side in ("A", "B"):
            p0, p1 = m["edges"][side]
            off = (_dot(p0, n) + _dot(p1, n)) / 2.0
            t0, t1 = sorted((_dot(p0, u), _dot(p1, u)))
            for end, sign in (("start", -1), ("end", 1)):
                e = m["ends"][end]
                if e["kind"] != "BEAM_JUNCTION":
                    continue
                t_dr = t0 if sign == -1 else t1
                geoms = []
                for c in e["carriers"]:
                    if c in members:
                        cm = members[c]
                        geoms.append(MultiPoint([q for s_ in ("A", "B") for q in cm["edges"][s_]]).convex_hull)
                    elif c in arc_poly:
                        geoms.append(arc_poly[c])
                    elif c in col:
                        geoms.append(col[c])
                pt = Point(t_dr, off)
                if any(local(mid, G).distance(pt) <= snap for G in geoms):
                    continue
                best = first_hit(t_dr, off, sign, close_cap * width, [local(mid, G) for G in geoms], snap)
                if best is None:
                    held.append({"member": mid, "side": side, "end": end,
                                 "why": "edge stops short of its carrier by more than %.1f x the width" % close_cap})
                    continue
                closed.append({"member": mid, "side": side, "end": end, "closed_m": round(abs(best - t_dr) / 1000.0, 4)})
                if sign == -1:
                    t0 = best
                else:
                    t1 = best
            P0 = (t0 * u[0] + off * n[0], t0 * u[1] + off * n[1])
            P1 = (t1 * u[0] + off * n[0], t1 * u[1] + off * n[1])
            edges_c[mid][side] = (P0, P1)
            hull_pts += [P0, P1]
        edges_c[mid]["region"] = MultiPoint(hull_pts).convex_hull

    regions = {mid: edges_c[mid]["region"] for mid in members}
    U = unary_union(list(regions.values()) + list(arc_poly.values()) + list(col.values()) + list(oth.values()))
    # R-FACE-SNAP-1 between members: a slit or hole thinner than the snap between two outlines drawn a hair apart is
    # not a pair of faces (closing by snap / 2 with mitred joins: corners and straight faces unchanged)
    U = U.buffer(snap / 2.0, join_style=2, mitre_limit=10.0).buffer(-snap / 2.0, join_style=2, mitre_limit=10.0)
    segs = []
    for g in getattr(U, "geoms", [U]):
        for ring in [g.exterior] + list(g.interiors):
            cs = list(ring.coords)
            segs += list(zip(cs, cs[1:]))

    def on_arc(m):
        for aid, ab in arcs.items():
            for h, R in ab["radii"].items():
                if abs(math.hypot(m[0] - ab["cx"], m[1] - ab["cy"]) - R) <= snap:
                    a0, a1 = ab["ranges"][h]
                    ang = math.degrees(math.atan2(m[1] - ab["cy"], m[0] - ab["cx"])) % 360.0
                    if (ang - a0) % 360.0 <= (a1 - a0) % 360.0 + 1e-6:
                        return aid, h
        return None

    def edges_of(P):
        cs = list(P.exterior.coords)
        return [LineString([c0, c1]) for c0, c1 in zip(cs, cs[1:]) if math.hypot(c1[0] - c0[0], c1[1] - c0[1]) > 1e-6]
    owners = [("COLUMN", k, e, None) for k, P in col.items() for e in edges_of(P)] + \
        [("OTHER", k, e, None) for k, P in oth.items() for e in edges_of(P)] + \
        [("SIDE", mid, LineString(list(edges_c[mid][s])), s) for mid in members for s in ("A", "B")]

    def parallel(l1, l2):
        (x0, y0), (x1, y1) = l1.coords[0], l1.coords[-1]
        (a0, b0), (a1, b1) = l2.coords[0], l2.coords[-1]
        return abs((x1 - x0) * (b1 - b0) - (y1 - y0) * (a1 - a0)) <= 1e-3 * l1.length * l2.length

    def parts(g):
        return [x for x in getattr(g, "geoms", [g]) if x.geom_type == "LineString" and x.length > 1e-6]

    def split_on_spans(mid, a_m, c_m):
        a_m, c_m = sorted((a_m, c_m))
        iv = sorted(members[mid]["spans"])
        bounds = [(-1e12, iv[0][0], iv[0][2], "BEYOND_SQUARE")]
        for k, (s0, s1, sid) in enumerate(iv):
            lo = s0 if k == 0 else (iv[k - 1][1] + s0) / 2.0
            hi = s1 if k == len(iv) - 1 else (s1 + iv[k + 1][0]) / 2.0
            if lo < s0:
                bounds.append((lo, s0, sid, "BESIDE_SUPPORT"))
            bounds.append((s0, s1, sid, "IN_SPAN"))
            if hi > s1:
                bounds.append((s1, hi, sid, "BESIDE_SUPPORT"))
        bounds.append((iv[-1][1], 1e12, iv[-1][2], "BEYOND_SQUARE"))
        return [(sid, min(c_m, b1) - max(a_m, b0), kind, max(a_m, b0), min(c_m, b1))
                for b0, b1, sid, kind in bounds if min(c_m, b1) - max(a_m, b0) > 1e-7]

    out = dict(sides={}, ends={}, columns={}, others={}, arcs={}, closed=closed, held=held, pieces=[],
               gaps=[], unattributed=[])
    arc_iv = {}
    for p, q in segs:
        if math.hypot(q[0] - p[0], q[1] - p[1]) < 1e-6:
            continue
        m0 = ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)
        if on_arc(m0) and on_arc(p) and on_arc(q):
            aid, h = on_arc(m0)
            ab = arcs[aid]
            a_p = math.degrees(math.atan2(p[1] - ab["cy"], p[0] - ab["cx"])) % 360.0
            a_q = math.degrees(math.atan2(q[1] - ab["cy"], q[0] - ab["cx"])) % 360.0
            if (a_q - a_p) % 360.0 > 180.0:
                a_p, a_q = a_q, a_p
            if a_q < a_p:
                a_q += 360.0
            arc_iv.setdefault((aid, h), []).append((a_p, a_q))
            continue
        rest = [LineString([p, q])]
        for kind, ref, e, side in owners:
            nxt = []
            for ls in rest:
                if not parallel(ls, e) or ls.distance(e) > snap:
                    nxt.append(ls)
                    continue
                Z = e.buffer(snap, cap_style=2)
                for g in parts(ls.intersection(Z)):
                    if kind == "SIDE":
                        u = frame[ref][0]
                        for sid, part, where, f0, f1 in split_on_spans(ref, _dot(g.coords[0], u) / 1000.0,
                                                                       _dot(g.coords[-1], u) / 1000.0):
                            out["sides"][(sid, side)] = out["sides"].get((sid, side), 0.0) + part
                            out["pieces"].append(dict(span_id=sid, side=side, where=where, m=round(part, 4),
                                                      f0=f0, f1=f1))
                    else:
                        d = out["columns"] if kind == "COLUMN" else out["others"]
                        d[ref] = d.get(ref, 0.0) + g.length / 1000.0
                nxt += parts(ls.difference(Z))
            rest = nxt
            if not rest:
                break
        for ls in rest:
            M = Point(((ls.coords[0][0] + ls.coords[-1][0]) / 2.0, (ls.coords[0][1] + ls.coords[-1][1]) / 2.0))
            hit = None
            for mid, P in regions.items():
                if P.exterior.distance(M) <= snap:
                    u = frame[mid][0]
                    t = _dot((M.x, M.y), u) / 1000.0
                    iv = sorted(members[mid]["spans"])
                    k_ = min(range(len(iv)), key=lambda j: 0.0 if iv[j][0] <= t <= iv[j][1] else
                             min(abs(t - iv[j][0]), abs(t - iv[j][1])))
                    hit = iv[k_][2]
                    near_start = abs(t - iv[k_][0]) <= abs(t - iv[k_][1])
                    if near_start and k_ == 0:
                        end_kind = members[mid]["ends"]["start"]["kind"]
                    elif not near_start and k_ == len(iv) - 1:
                        end_kind = members[mid]["ends"]["end"]["kind"]
                    else:
                        end_kind = "COLUMN"            # an interior span end is a column cut (V2 splits only there)
                    break
            if hit is None:
                for aid, P in arc_poly.items():
                    if P.exterior.distance(M) <= snap:
                        hit, end_kind = aid, "ARC_END"
                        break
            if hit is None:
                out["unattributed"].append(round(ls.length / 1000.0, 4))
                continue
            if ls.length < snap:
                out.setdefault("end_artefacts_m", []).append(round(ls.length / 1000.0, 6))   # < snap: not a face
                continue
            out["ends"][(hit, end_kind)] = out["ends"].get((hit, end_kind), 0.0) + ls.length / 1000.0
    for (aid, h), ivs in arc_iv.items():
        ivs.sort()
        mg = []
        for a0, a1 in ivs:
            if mg and a0 <= mg[-1][1] + 1e-6:
                mg[-1][1] = max(mg[-1][1], a1)
            else:
                mg.append([a0, a1])
        out["arcs"][(aid, h)] = sum(arcs[aid]["radii"][h] * math.radians(a1 - a0) for a0, a1 in mg) / 1000.0
        out.setdefault("arc_pieces", {})[(aid, h)] = [(round(a0, 3), round(a1, 3)) for a0, a1 in mg]
    # gaps on each side inside each span (junction zones: tees, crossings)
    for mid, m in members.items():
        for s0, s1, sid in m["spans"]:
            for side in ("A", "B"):
                ivs = sorted((pc["f0"], pc["f1"]) for pc in out["pieces"] if pc["span_id"] == sid and pc["side"] == side)
                cur = s0
                for f0, f1 in ivs:
                    f0, f1 = max(f0, s0), min(f1, s1)
                    if f1 <= f0:
                        continue
                    if f0 > cur + 1e-4:
                        out["gaps"].append(dict(span_id=sid, side=side, gap_m=round(f0 - cur, 4)))
                    cur = max(cur, f1)
                if s1 > cur + 1e-4:
                    out["gaps"].append(dict(span_id=sid, side=side, gap_m=round(s1 - cur, 4)))
    for k in ("sides", "ends", "columns", "others", "arcs"):
        out[k] = {kk: round(v, 4) for kk, v in out[k].items()}
    return out
