"""INDEPENDENT DRAWING READER (Phase 2B-8) - a second reading of a DXF plan with ezdxf, shapely and arithmetic only:
no engine module is imported, no engine output is read. tools/arch_change_verify.py checks a BOQ change against it.

    D = Drawing(path, roles=None, unit_m=None)
    D.pieces(role=None, layer=None)   every drawn entity in world metres, through every block level (an entity on
                                      layer 0 inside a block takes its INSERT's layer, the DXF convention): its layer,
                                      type, handle, insert path (block names) and points (curves flattened)
    D.face_at(point)                  the closed face containing a point, from the wall and column lines plus a
                                      closure across every gap of 0.30 - 2.60 m between two collinear wall-line
                                      pieces (a door or window gap in a wall face): area, perimeter, holes, the
                                      closures on its boundary
    D.doors() / D.windows()           door symbols (door-layer pieces within 0.06 m of each other): width = the
                                      extent, across the leaf, of the short lines parallel to the leaf (the jamb
                                      lines across the wall - the jamb span); wall thickness = their length.
                                      Windows: window-layer pieces, width = their extent along the longest line
    D.openings_on(face)               the doors / windows whose mid-wall line lies on the face boundary (0.30 m reach,
                                      90 % of the width), and the closure length no opening covers (a passage)
    D.arc_census()                    concentric wall-layer arc pairs 0.08 - 0.45 m apart (ARC entities and polyline
                                      bulges, read from their own parameters): the curved bands, mid-radius x sweep
    D.fixture_census(polygon)         the inserts inside a polygon by block-name word (basin / water closet / shower
                                      or bath) and the loose sanitary-layer pieces (not a fixture block's own lines)
Layer roles: given ({layer: role}) or read from the layer name: WALL, COL -> COLUMN, GLAZ / WIN -> WINDOW, DOOR.
The words and limits are stated here; a drawing the reader cannot resolve gives None, never a guess."""

from __future__ import annotations

import math
import re
from collections import defaultdict

import ezdxf
from ezdxf.math import Matrix44, OCS, Vec3, bulge_to_arc
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union

POLICY = "URBAN_INDEPENDENT_READER_V1"
UNITS_M = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0}
WALL, COLUMN, WINDOW, DOOR = "WALL", "COLUMN", "WINDOW", "DOOR"
NAME_ROLES = ((WALL, ("WALL",)), (COLUMN, ("COL",)), (WINDOW, ("GLAZ", "WIN")), (DOOR, ("DOOR",)))
GAP_MIN_M, GAP_MAX_M = 0.30, 2.60          # a door or window gap in a wall face
CLUSTER_M = 0.06                           # pieces of one symbol touch (a frame line 50 mm inside its jamb)
JAMB_MAX_M = 0.45                          # a line across a wall is no longer than the thickest wall
LEAF_MIN_M = 0.40
REACH_M = 0.30                             # an opening's mid-wall line to the face boundary
FLAT_M = 0.005                             # curve flattening step
GRID_M = 1e-6                              # noding grid
SAG_M = 1e-5                               # curve flattening: largest chord-to-curve distance
FIXTURE_WORDS = {"basins": ("WASH", "BASIN", "SINK", "LAV", "VANITY"),
                 "water_closets": ("WC", "W.C", "TOILET", "CLOSET"),
                 "showers_baths": ("SHOWER", "BATH", "TUB", "JACUZZI")}
SANITARY_WORDS = ("SANIT", "PLUMB")


def role_of_name(layer):
    up = layer.upper()
    for role, words in NAME_ROLES:
        if any(w in up for w in words):
            return role
    return None


def fixture_kind(block_name):
    up = block_name.upper()
    if up.startswith("*") or re.match(r"^A\$C[0-9A-F]+$", up):
        return None                                           # an anonymous block names nothing
    toks = set(re.split(r"[^A-Z.]+", up))
    for kind, words in FIXTURE_WORDS.items():
        if any(w in toks or (len(w) > 3 and w in up) for w in words):
            return kind
    return None


def _ang(c, p):
    return math.atan2(p[1] - c[1], p[0] - c[0])


def _ccw_interval(c, p0, pm, p1):
    """the CCW interval (start, sweep) from p0 through pm to p1 on a circle about c (any orientation)."""
    a0, am, a1 = _ang(c, p0), _ang(c, pm), _ang(c, p1)
    tw = 2 * math.pi
    if (am - a0) % tw < (a1 - a0) % tw:
        return a0 % tw, (a1 - a0) % tw or tw
    return a1 % tw, (a0 - a1) % tw or tw


def _overlap(s1, w1, s2, w2):
    best = 0.0
    for k in (-1, 0, 1):
        b = s2 + k * 2 * math.pi
        best = max(best, min(s1 + w1, b + w2) - max(s1, b))
    return max(0.0, best)


class Drawing:
    def __init__(self, path, roles=None, unit_m=None):
        self.doc = ezdxf.readfile(str(path))
        k = unit_m if unit_m else UNITS_M.get(self.doc.header.get("$INSUNITS", 0))
        if not k:
            raise ValueError("the drawing names no length unit ($INSUNITS) and none was given")
        self.k = k
        self._roles_given = dict(roles or {})
        self._pieces = []
        self._arcs = []
        self._inserts = []
        self._walk(self.doc.modelspace(), Matrix44(), None, ())
        self._faces = None

    # ----------------------------------------------------------------------------------------- reading
    def role(self, layer):
        if layer in self._roles_given:
            return self._roles_given[layer]
        return role_of_name(layer)

    def _walk(self, layout, m, parent_layer, ipath):
        for e in layout:
            t = e.dxftype()
            lay = e.dxf.get("layer", "0")
            eff = parent_layer if (lay == "0" and parent_layer) else lay
            if t == "INSERT":
                blk = self.doc.blocks.get(e.dxf.name)
                if blk is None:
                    continue
                mm = Matrix44.chain(e.matrix44(), m)
                self._inserts.append({"name": e.dxf.name, "layer": eff, "handle": e.dxf.handle,
                                      "insert_path": ipath, "point": self._xy(mm.transform(Vec3(blk.block.dxf.base_point)))})
                self._walk(blk, mm, eff, ipath + (e.dxf.name,))
                continue
            if t not in ("LINE", "ARC", "CIRCLE", "ELLIPSE", "LWPOLYLINE", "POLYLINE", "SPLINE"):
                continue
            rec = {"layer": eff, "type": t, "handle": e.dxf.handle, "insert_path": ipath}
            if t == "LWPOLYLINE":
                self._bulged(e, [tuple(p) for p in e.get_points("xyb")], e.closed, OCS(e.dxf.extrusion),
                             e.dxf.elevation, m, rec)
                continue
            if t == "POLYLINE":
                if e.is_2d_polyline:
                    vs = [(v.dxf.location.x, v.dxf.location.y, v.dxf.get("bulge", 0.0)) for v in e.vertices]
                    self._bulged(e, vs, e.is_closed, OCS(e.dxf.extrusion), e.dxf.elevation.z, m, rec)
                else:
                    pts = [self._xy(m.transform(Vec3(v))) for v in e.points()]
                    for i in range(len(pts) - 1 + bool(e.is_closed)):
                        a, b = pts[i], pts[(i + 1) % len(pts)]
                        if math.dist(a, b) > 1e-9:
                            self._pieces.append(dict(rec, part=i, pts=[a, b], closed=False, straight=True))
                continue
            if t == "LINE":
                pts = [self._xy(m.transform(Vec3(e.dxf.start))), self._xy(m.transform(Vec3(e.dxf.end)))]
            else:
                # the entity's own vertices on the true curve (ezdxf's path form approximates arcs by Bezier curves)
                try:
                    pts = [self._xy(m.transform(v)) for v in e.flattening(SAG_M / self.k)]
                except Exception:                              # noqa: BLE001 - an entity ezdxf cannot flatten
                    continue
            if len(pts) < 2:
                continue
            closed = t == "CIRCLE" or (t == "ELLIPSE" and abs(abs(e.dxf.end_param - e.dxf.start_param) - 2 * math.pi)
                                       < 1e-9)
            if closed and math.dist(pts[0], pts[-1]) < 1e-9:
                pts = pts[:-1]
            self._pieces.append(dict(rec, pts=pts, closed=closed, straight=(t == "LINE")))
            if t == "ARC":
                ocs, c = OCS(e.dxf.extrusion), Vec3(e.dxf.center)
                a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
                sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
                loc = [Vec3(c.x + e.dxf.radius * math.cos(a), c.y + e.dxf.radius * math.sin(a), c.z)
                       for a in (a0, a0 + sweep / 2, a0 + sweep)]
                self._arc(rec, m, ocs, c, loc)

    def _xy(self, v):
        return (v.x * self.k, v.y * self.k)

    def _arc(self, rec, m, ocs, c, loc):
        cw = self._xy(m.transform(ocs.to_wcs(c)))
        p0, pm, p1 = (self._xy(m.transform(ocs.to_wcs(v))) for v in loc)
        s, w = _ccw_interval(cw, p0, pm, p1)
        self._arcs.append(dict(rec, centre=cw, r=math.dist(cw, p0), start=s, sweep=w))

    def _bulged(self, e, pts, closed, ocs, z, m, rec):
        """a 2D polyline (LWPOLYLINE or POLYLINE) segment by segment: straight, or the true arc of its bulge."""
        n = len(pts) if closed else len(pts) - 1
        for i in range(n):
            (x0, y0, b), (x1, y1, _b) = pts[i], pts[(i + 1) % len(pts)]
            r = dict(rec, part=i)
            if abs(b) < 1e-12:
                w = [self._xy(m.transform(ocs.to_wcs(Vec3(x, y, z)))) for x, y in ((x0, y0), (x1, y1))]
                if math.dist(*w) > 1e-9:
                    self._pieces.append(dict(r, pts=w, closed=False, straight=True))
                continue
            c, sa, ea, rad = bulge_to_arc((x0, y0), (x1, y1), b)
            sweep = (ea - sa) % (2 * math.pi)
            nseg = max(4, int(sweep * rad * self.k / FLAT_M) + 1)
            loc = [Vec3(c.x + rad * math.cos(sa + sweep * j / nseg), c.y + rad * math.sin(sa + sweep * j / nseg), z)
                   for j in range(nseg + 1)]
            if b < 0:                                          # clockwise: the polyline runs from the arc's end
                loc.reverse()
            w = [self._xy(m.transform(ocs.to_wcs(v))) for v in loc]
            self._pieces.append(dict(r, pts=w, closed=False, straight=False))
            self._arc(r, m, ocs, Vec3(c.x, c.y, z), [loc[0], loc[len(loc) // 2], loc[-1]])

    def pieces(self, role=None, layer=None):
        return [p for p in self._pieces if (layer is None or p["layer"] == layer) and
                (role is None or self.role(p["layer"]) == role)]

    def layer_roles(self):
        return {lay: self.role(lay) for lay in sorted({p["layer"] for p in self._pieces})}

    # ----------------------------------------------------------------------------------------- faces
    def _segments(self, roles):
        segs = []
        for p in self._pieces:
            if self.role(p["layer"]) not in roles:
                continue
            pts = p["pts"] + ([p["pts"][0]] if p["closed"] else [])
            for a, b in zip(pts, pts[1:]):
                if math.dist(a, b) > 1e-9:
                    segs.append((a, b, p["straight"]))
        return segs

    @staticmethod
    def _closures(segs):
        """a closure across each gap of GAP_MIN_M .. GAP_MAX_M between consecutive collinear straight pieces."""
        lines = []
        for a, b, straight in segs:
            L = math.dist(a, b)
            if not straight or L < 0.05:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            if ux < -1e-6 or (abs(ux) <= 1e-6 and uy < 0):
                ux, uy = -ux, -uy
            th = math.atan2(uy, ux)
            d = -uy * (a[0] + b[0]) / 2 + ux * (a[1] + b[1]) / 2
            lines.append((a, b, ux, uy, th, d))
        buckets = defaultdict(list)
        for i, (_a, _b, _ux, _uy, th, d) in enumerate(lines):
            buckets[(math.floor(th / 5e-4), math.floor(d / 0.002))].append(i)
        parent = list(range(len(lines)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i, (a, b, ux, uy, th, d) in enumerate(lines):
            kt, kd = math.floor(th / 5e-4), math.floor(d / 0.002)
            for dt in (-1, 0, 1):
                for dd in (-1, 0, 1):
                    for j in buckets.get((kt + dt, kd + dd), ()):
                        if j <= i:
                            continue
                        a2, b2, ux2, uy2 = lines[j][:4]
                        if abs(ux * uy2 - uy * ux2) > 2e-4:
                            continue
                        if all(abs(-uy * (p[0] - a[0]) + ux * (p[1] - a[1])) <= 0.001 for p in (a2, b2)):
                            parent[find(j)] = find(i)
        groups = defaultdict(list)
        for i in range(len(lines)):
            groups[find(i)].append(i)
        out = []
        for idx in groups.values():
            if len(idx) < 2:
                continue
            ux, uy = lines[idx[0]][2], lines[idx[0]][3]
            ends = []
            for i in idx:
                a, b = lines[i][:2]
                ta, tb = a[0] * ux + a[1] * uy, b[0] * ux + b[1] * uy
                ends.append(((ta, a), (tb, b)) if ta <= tb else ((tb, b), (ta, a)))
            ends.sort(key=lambda x: x[0][0])
            hi = ends[0][1]
            for lo2, hi2 in ends[1:]:
                g = lo2[0] - hi[0]
                if GAP_MIN_M - 1e-9 <= g <= GAP_MAX_M + 1e-9:
                    out.append((hi[1], lo2[1]))
                if hi2[0] > hi[0]:
                    hi = hi2
        return out

    def faces(self):
        if self._faces is None:
            segs = self._segments((WALL, COLUMN))
            self._closure_lines = self._closures(segs)
            geo = [LineString([a, b]) for a, b, _s in segs] + [LineString([a, b]) for a, b in self._closure_lines]
            # coordinates on a 1 micrometre grid: an arc's computed end meets the line drawn to it
            geo = [shapely.set_precision(g, GRID_M) for g in geo]
            self._faces = list(polygonize(unary_union([g for g in geo if not g.is_empty]))) if geo else []
            self._closure_union = unary_union([LineString([a, b]) for a, b in self._closure_lines]) \
                if self._closure_lines else None
        return self._faces

    def face_at(self, point):
        pt = Point(point)
        hit = [f for f in self.faces() if f.contains(pt)]
        if not hit:
            return None
        f = min(hit, key=lambda x: x.area)
        clos = f.boundary.intersection(self._closure_union.buffer(1e-6)) if self._closure_union is not None else None
        return {"polygon": f, "area_m2": f.area, "perimeter_m": f.exterior.length,
                "holes": len(f.interiors), "holes_perimeter_m": sum(r.length for r in f.interiors),
                "closure_m": clos.length if clos is not None else 0.0, "closure_geom": clos}

    # ----------------------------------------------------------------------------------------- openings
    def _clusters(self, role):
        ps = [p for p in self.pieces(role) if len(p["pts"]) >= 2]
        geo = [LineString(p["pts"]) for p in ps]
        parent = list(range(len(ps)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        boxes = [g.bounds for g in geo]
        order = sorted(range(len(ps)), key=lambda i: boxes[i][0])
        for n, i in enumerate(order):
            for j in order[n + 1:]:
                if boxes[j][0] > boxes[i][2] + CLUSTER_M:
                    break
                if boxes[j][1] > boxes[i][3] + CLUSTER_M or boxes[j][3] < boxes[i][1] - CLUSTER_M:
                    continue
                if geo[i].distance(geo[j]) <= CLUSTER_M:
                    parent[find(j)] = find(i)
        groups = defaultdict(list)
        for i in range(len(ps)):
            groups[find(i)].append(ps[i])
        return list(groups.values())

    def doors(self):
        out = []
        for cl in self._clusters(DOOR):
            st = [(p["pts"][0], p["pts"][-1]) for p in cl if p["straight"]]
            if not st:
                continue
            leaf = max(st, key=lambda s: math.dist(*s))
            if math.dist(*leaf) < LEAF_MIN_M:
                continue
            L = math.dist(*leaf)
            lx, ly = (leaf[1][0] - leaf[0][0]) / L, (leaf[1][1] - leaf[0][1]) / L
            ux, uy = -ly, lx                                    # across the leaf: along the wall
            jambs = [s for s in st if 0.05 <= math.dist(*s) <= JAMB_MAX_M and
                     abs(((s[1][0] - s[0][0]) * ly - (s[1][1] - s[0][1]) * lx) / math.dist(*s)) <= math.sin(
                         math.radians(3))]
            if len(jambs) < 2:
                continue
            mids = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in jambs]
            pos = [m[0] * ux + m[1] * uy for m in mids]
            lo, hi = min(pos), max(pos)
            if hi - lo < LEAF_MIN_M:
                continue
            along = sum(m[0] * lx + m[1] * ly for m in mids) / len(mids)
            seg = [(ux * lo + lx * along, uy * lo + ly * along), (ux * hi + lx * along, uy * hi + ly * along)]
            ts = sorted(round(math.dist(*s), 4) for s in jambs)
            out.append({"kind": "DOOR", "width_m": hi - lo, "wall_t_m": ts[len(ts) // 2], "mid_wall": seg,
                        "jamb_lines": len(jambs), "handles": sorted({p["handle"] for p in cl})})
        return out

    def windows(self):
        out = []
        for cl in self._clusters(WINDOW):
            st = [(p["pts"][0], p["pts"][-1]) for p in cl if p["straight"]]
            if not st:
                continue
            a, b = max(st, key=lambda s: math.dist(*s))
            L = math.dist(a, b)
            if L < 0.2:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            pts = [q for p in cl for q in p["pts"]]
            pos = [q[0] * ux + q[1] * uy for q in pts]
            nx, ny = -uy, ux
            off = sum(q[0] * nx + q[1] * ny for q in pts) / len(pts)
            lo, hi = min(pos), max(pos)
            seg = [(ux * lo + nx * off, uy * lo + ny * off), (ux * hi + nx * off, uy * hi + ny * off)]
            out.append({"kind": "WINDOW", "width_m": hi - lo, "mid_wall": seg,
                        "handles": sorted({p["handle"] for p in cl})})
        return out

    def openings_on(self, face):
        """-> (openings on the face boundary, the closure length on the boundary no opening covers)."""
        if face is None:
            return [], None
        bd = face["polygon"].boundary
        found = []
        cover = []
        for o in self.doors() + self.windows():
            band = LineString(o["mid_wall"]).buffer(REACH_M, cap_style=2)
            on = bd.intersection(band)
            if on.length >= 0.9 * o["width_m"]:
                found.append(o)
                cover.append(band)
        clos = face["closure_geom"]
        free = 0.0
        if clos is not None and not clos.is_empty:
            rest = clos.difference(unary_union(cover)) if cover else clos
            free = rest.length
        return found, free

    def opening_near(self, point, kind="DOOR", reach=0.5):
        best = None
        for o in (self.doors() if kind == "DOOR" else self.windows()):
            d = LineString(o["mid_wall"]).distance(Point(point))
            if d <= reach and (best is None or d < best[0]):
                best = (d, o)
        return best[1] if best else None

    # ----------------------------------------------------------------------------------------- census
    def arc_census(self, layers=None):
        arcs = [a for a in self._arcs if (self.role(a["layer"]) == WALL if layers is None else a["layer"] in layers)]
        uniq = []
        for a in arcs:
            if not any(math.dist(a["centre"], b["centre"]) <= 1e-4 and abs(a["r"] - b["r"]) <= 1e-4 and
                       abs(a["start"] - b["start"]) <= 1e-6 and abs(a["sweep"] - b["sweep"]) <= 1e-6 for b in uniq):
                uniq.append(a)
        pairs = []
        for i, a in enumerate(uniq):
            for b in uniq[i + 1:]:
                dr = abs(a["r"] - b["r"])
                if math.dist(a["centre"], b["centre"]) > 0.01 or not (0.08 <= dr <= 0.45):
                    continue
                w = _overlap(a["start"], a["sweep"], b["start"], b["sweep"])
                if w > 0.01:
                    pairs.append((dr, a, b, w))
        pairs.sort(key=lambda x: x[0])
        used, bands = set(), []
        for dr, a, b, w in pairs:
            if id(a) in used or id(b) in used:
                continue
            used |= {id(a), id(b)}
            rm = (a["r"] + b["r"]) / 2
            bands.append({"centre": [round(a["centre"][0], 6), round(a["centre"][1], 6)],
                          "r_inner_m": round(min(a["r"], b["r"]), 6), "r_outer_m": round(max(a["r"], b["r"]), 6),
                          "sweep_rad": round(w, 9), "mid_lm": round(rm * w, 6), "t_m": round(dr, 6),
                          "handles": sorted({a["handle"], b["handle"]})})
        return {"bands": bands, "mid_lm": round(sum(x["mid_lm"] for x in bands), 6)}

    def fixture_census(self, polygon):
        poly = polygon.buffer(0.01)
        out = {k: 0 for k in FIXTURE_WORDS}
        fixture_blocks = set()
        for ins in self._inserts:
            kind = fixture_kind(ins["name"])
            if kind:
                fixture_blocks.add(ins["name"])
                if poly.contains(Point(ins["point"])):
                    out[kind] += 1
        n = 0
        for p in self._pieces:
            if not any(w in p["layer"].upper() for w in SANITARY_WORDS):
                continue
            if any(b in fixture_blocks for b in p["insert_path"]):
                continue                                      # a fixture block's own linework is the fixture
            if all(poly.contains(Point(q)) for q in p["pts"]):
                n += 1
        out["sanitary_layer_lines"] = n
        return out
