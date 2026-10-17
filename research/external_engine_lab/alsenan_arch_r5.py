"""ALSENAN ROUND 5 - architectural BOQ truth engine (lab adapter; the calculators it calls are generic).

Three layers are kept apart: PHYSICAL SPACE (Route A sites, room_topology_v3) != SEMANTIC ZONE (labels) != TRADE
MEASUREMENT REGION (a physical space, or a part of one bounded by positive non-wall evidence). Route B
(planar_shadow_topology) re-derives faces independently and is used for validation, orphan recovery and positive
split evidence - never as a replacement. Every quantity carries its release state from arch_quantity_truth.

Benchmark firewall: no human benchmark quantity is read here. Rebar is not touched.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict

from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

import alsenan_phase_a as AP
import alsenan_phase_b2a as B2A
import alsenan_v3_geom as G
import alsenan_v3_layers as L
from engine.source import arch_quantity_truth as AQ
from engine.source import finish_height as FH
from engine.source import legacy_text as LT
from engine.source import planar_shadow_topology as PT
from engine.source import urban_methods_v3 as UM3

FLOORS = ("GF", "1F", "2F")
UP = {"GF": "1F", "1F": "2F", "2F": None}
WALL_L, COL_L, WIN_L, THIN_L, DOOR_L, FIX_L = "1", "S-COL.BON", "W", "5", "D", "TOI"
ROUTE_B_LAYERS = (WALL_L, COL_L, WIN_L, THIN_L)
BRIDGE_GAP_MM = (300.0, 3600.0)
EDGE_TOL = 25.0                   # mm: a region edge lies on a source line
MIN_SPACE_M2, MIN_WIDTH_M = 1.0, 0.6
WALL_PAIR_MM = (60.0, 450.0)
WET_WORDS = {"BATH", "WC", "WASH", "TOILET", "SHOWER"}
SERVICE_WORDS = {"KITCHEN", "LAUNDRY", "PANTRY"}
EXT_WORDS = {"GARDEN", "COURT", "POOL", "SWIMMING"}
BUILDUP_M = UM3.resolve("URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1")["parameters"]["buildup_m"]
UPTURN_M = 0.15
REVEAL_M = 0.25
ARCH_AREA_SHEET = {        # P7757 architectural PDF p.1 (area calculation sheet) - read after rendering; Route C
    "GF": {"rows": [[16.37, 13.50, 220.99], [4.40, 4.11, 18.08], [10.60, 4.89, 51.83], [4.40, 5.40, 23.76],
                    ["1/2 x (4.40 + 3.10) x 1.30", None, 4.87], ["2/3 x 0.38 x 1.84", None, 0.46]],
           "total_m2": 319.99, "deduction_m2": 0.0},
    "1F": {"rows": [[14.87, 12.00, 178.44], [4.40, 7.50, 33.00]], "total_m2": 211.44,
           "deduction": [1.80, 1.80, 3.24], "after_deduction_m2": 208.20},
    "2F": {"rows": [[8.10, 6.80, 55.08]], "total_m2": 55.08}}


def _r(v, n=6):
    return None if v is None else round(float(v), n)


def _m2(a):
    return a / 1e6


def label_class(en, ar=""):
    u = (en or "").upper().replace("W.C", "WC")
    words = set(re.findall(r"[A-Z]+", u))
    if words & WET_WORDS:
        return "WET"
    if words & SERVICE_WORDS:
        return "SERVICE"
    if "VOID" in words:
        return "VOID"
    if "ROOF" in words:
        return "ROOF"
    if words & EXT_WORDS:
        return "EXTERNAL"
    return "DRY" if words else "UNKNOWN"


# ============================================================================================ floor model
class Floor:
    def __init__(self, ctx, fl):
        self.ctx, self.fl = ctx, fl
        self.inp = ctx["a2_raw"][fl]["inp"]
        self.res = ctx["a2_raw"][fl]["res"]
        self.u = self.inp.unit_native_to_mm or 1.0
        self.plate = L._plate_in_arch(ctx, fl).buffer(0)
        self.sites = self._sites()
        self.labels = self._labels()
        self.fixtures = self._fixtures()
        self.doors = self._doors()
        self.lines = self._lines()
        self.route_b = self._route_b()
        self.cols = [Polygon(r) for r in self._column_rings() if len(r) >= 3]
        self.voids = [v for v in ctx["v3"]["voids"]["items"] if v["floor"] == fl]

    # ---------------------------------------------------------------- Route A sites
    def _sites(self):
        res, arr = self.res, self.res["_arr"]
        out = []
        for s in sorted(res["sites"], key=lambda z: z["site_id"]):
            P = B2A._site_polygon(arr, s["cycle"])
            if len(P) < 3:
                continue
            holes = []
            for hc in s.get("hole_cycles") or []:
                H = B2A._site_polygon(arr, hc)
                if len(H) >= 3:
                    holes.append(H)
            poly = Polygon(P, holes).buffer(0)
            if poly.is_empty:
                continue
            en, ar, _ = L._names(self.ctx, s)
            per = s["perimeter"] * self.u / 1000.0
            out.append({"site_id": s["site_id"], "poly": poly, "ring": P, "area_m2": s["area_m2"],
                        "perimeter_m": per, "eff_width_m": 2 * s["area_m2"] / per if per else 0.0,
                        "kind": s["kind"], "status": s["status"], "physical_status": s.get("physical_status"),
                        "names_en": en, "names_ar": ar, "label_occ": sorted(set(s.get("labels") or [])),
                        "contents": dict(s.get("contents") or {}),
                        "boundary_sources": sorted(set(s.get("boundary_source_ids") or [])), "_s": s})
        return out

    # ---------------------------------------------------------------- labels / fixtures / doors
    def _labels(self):
        dec = {d["occurrence"]: d for d in self.ctx["v3_topology"]["floors"][self.fl]["decoded_labels"]}
        out = []
        for l in self.ctx["arch"][self.fl]["labels"]:
            d = dec.get(l["occurrence"]) or {}
            en = l["label_en"]
            out.append({"occurrence": str(l["occurrence"]), "text_en": en, "text_ar": d.get("arabic"),
                        "arabic_corroboration": d.get("corroboration") if isinstance(d.get("corroboration"), str)
                        else (d.get("corroboration") or {}).get("state"),
                        "x": l["x"], "y": l["y"], "x_ar": d.get("x"), "y_ar": d.get("y"),
                        "class": label_class(en), "class_candidate": l["class_candidate"],
                        "roles": list(l["text_roles"]) if not isinstance(l["text_roles"], str) else [l["text_roles"]]})
        return out

    def _fixtures(self):
        ins = defaultdict(list)
        for p in self.inp.parts:
            if p.layer == FIX_L and p.lineage:
                ins[p.lineage[-1].insert_handle].append(p)
        out = []
        for h, ps in sorted(ins.items()):
            xs, ys = [], []
            for p in ps:
                g = p.geometry
                xs += [g[0]] + ([g[2]] if p.kind == "SEGMENT" else [])
                ys += [g[1]] + ([g[3]] if p.kind == "SEGMENT" else [])
            out.append({"insert": h, "block": ps[0].lineage[-1].block_name, "x": sum(xs) / len(xs),
                        "y": sum(ys) / len(ys), "parts": len(ps)})
        return out

    def _doors(self):
        eri = self.ctx["a2_raw"][self.fl]["eri"]
        out = {}
        for k, d in (eri.get("inferred_doors") or {}).items():
            out[k] = {"hinge": tuple(d["hinge"]), "radius": d["radius"], "ends": [tuple(e) for e in d["ends"]],
                      "block": d.get("block_name")}
        ins = defaultdict(list)
        for p in self.inp.parts:
            if p.layer == DOOR_L and p.lineage:
                ins[p.lineage[-1].insert_handle].append(p)
        for h, ps in ins.items():
            k = "I" + h
            if k in out:
                continue
            arcs = [p for p in ps if p.kind == "ARC"]
            if arcs:
                cx, cy, r, a0, a1 = arcs[0].geometry[:5]
                out[k] = {"hinge": (cx, cy), "radius": r,
                          "ends": [(cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))],
                          "block": ps[0].lineage[-1].block_name}
        return out

    def _column_rings(self):
        segs = [p for p in self.inp.parts if p.layer == COL_L and p.kind == "SEGMENT"]
        ls = [LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]) for p in segs]
        from shapely.ops import polygonize
        return [list(g.exterior.coords) for g in polygonize(unary_union(ls)) if g.area > 1000.0]

    # ---------------------------------------------------------------- classified source lines
    def _lines(self):
        """Every admitted linework part as a LineString with its class source (layer) and id."""
        out = defaultdict(list)
        for p in self.inp.parts:
            g = p.geometry
            if p.kind == "SEGMENT":
                geom = LineString([(g[0], g[1]), (g[2], g[3])])
            elif p.kind == "ARC":
                geom = LineString(PT.discretise_arc(g[0], g[1], g[2], g[3], g[4]))
            elif p.kind == "CIRCLE":
                geom = LineString(PT.discretise_arc(g[0], g[1], g[2], 0.0, 2 * math.pi))
            else:
                continue
            if geom.length <= 0:
                continue
            out[p.layer].append((geom, p.identity.key, p))
        return out

    # ---------------------------------------------------------------- Route B
    def _route_b(self):
        segs, arcs = [], []
        for p in self.inp.parts:
            if p.layer not in ROUTE_B_LAYERS:
                continue
            g = p.geometry
            if p.kind == "SEGMENT":
                segs.append((g[0], g[1], g[2], g[3], p.identity.key))
            elif p.kind == "ARC":
                arcs.append((g[0], g[1], g[2], g[3], g[4], p.identity.key))
            elif p.kind == "CIRCLE":
                arcs.append((g[0], g[1], g[2], 0.0, 2 * math.pi, p.identity.key))
        wall_pts = [(s[0], s[1]) for s in segs] + [(s[2], s[3]) for s in segs]
        doorc = []
        for k, d in sorted(self.doors.items()):
            best = None
            for q in d["ends"]:
                dd = min((math.dist(q, w) for w in wall_pts), default=1e9)
                if best is None or dd < best[0]:
                    best = (dd, q)
            if best and best[0] <= 150.0:
                doorc.append((d["hinge"][0], d["hinge"][1], best[1][0], best[1][1], f"DOORCLOSE|{k}"))
        bridges = PT.bridge_gaps(segs, min_gap=BRIDGE_GAP_MM[0], max_gap=BRIDGE_GAP_MM[1])
        r = PT.build(segs + doorc + bridges, arcs=arcs, eps=1.0)
        r["door_closures"] = doorc
        r["bridges"] = bridges
        for f in r["faces"]:
            f["poly"] = Polygon(f["ring"], f["holes"]).buffer(0)
        return r


def floors(ctx):
    return {fl: Floor(ctx, fl) for fl in FLOORS}


# ============================================================================================ edges
def edge_kinds(F, poly, *, sub_lines=()):
    """Classify every boundary piece of a region polygon by the source line it lies on. Priority: COLUMN > WALL >
    GLAZING > DOOR / OPEN_PASSAGE (closures) > ZONE_SPLIT (thin non-wall line or an explicit split line) >
    EXTERNAL_EDGE (floor-plate edge) > UNKNOWN_EDGE. Returns [{kind, length_m, a, b, sources}]."""
    cache = getattr(F, "_edge_cache", None)
    if cache is None:
        cols = unary_union([c.exterior for c in F.cols]).buffer(EDGE_TOL) if F.cols else None
        walls = unary_union([g for g, _, _ in F.lines.get(WALL_L, [])]).buffer(EDGE_TOL)
        glaz = unary_union([g for g, _, _ in F.lines.get(WIN_L, [])]).buffer(EDGE_TOL)
        thin = unary_union([g for g, _, _ in F.lines.get(THIN_L, [])]).buffer(EDGE_TOL)
        door_l, pass_l = [], []
        for x0, y0, x1, y1, sid in F.route_b["door_closures"]:
            door_l.append(LineString([(x0, y0), (x1, y1)]))
        for x0, y0, x1, y1, sid in F.route_b["bridges"]:
            ls = LineString([(x0, y0), (x1, y1)])
            near_door = any(Point(d["hinge"]).distance(ls) <= d["radius"] + 200.0 for d in F.doors.values())
            (door_l if near_door else pass_l).append(ls)
        ra = defaultdict(list)                        # Route A cycle edges with closure sources
        for s in F.sites:
            for pts, roles, srcs, Lm in L._cycle_edges(F.res, s["_s"], F.u):
                k = L._edge_kind(roles, srcs)
                if k in ("OPENING", "WALL_END_CLOSURE", "DRAFTING_JOIN"):
                    ra[k].append(LineString(pts))
        for k in ("OPENING",):
            for ls in ra[k]:
                near_door = any(Point(d["hinge"]).distance(ls) <= d["radius"] + 200.0 for d in F.doors.values())
                (door_l if near_door else pass_l).append(ls)
        pass_l += ra["WALL_END_CLOSURE"]
        drafting = unary_union(ra["DRAFTING_JOIN"]).buffer(EDGE_TOL) if ra["DRAFTING_JOIN"] else None
        cache = {"COLUMN": cols, "WALL": walls, "GLAZING": glaz,
                 "DOOR": unary_union(door_l).buffer(EDGE_TOL) if door_l else None,
                 "OPEN_PASSAGE": unary_union(pass_l).buffer(EDGE_TOL) if pass_l else None,
                 "DRAFTING_JOIN": drafting,
                 "ZONE_SPLIT": thin, "EXTERNAL_EDGE": F.plate.exterior.buffer(EDGE_TOL)}
        F._edge_cache = cache
    order = ["COLUMN", "WALL", "GLAZING", "DOOR", "OPEN_PASSAGE", "DRAFTING_JOIN", "ZONE_SPLIT", "EXTERNAL_EDGE"]
    extra = unary_union(list(sub_lines)).buffer(EDGE_TOL) if sub_lines else None
    out = []
    rings = [poly.exterior] + list(poly.interiors) if poly.geom_type == "Polygon" else \
        [g.exterior for g in poly.geoms] + [i for g in poly.geoms for i in g.interiors]
    for ri, ring in enumerate(rings):
        c = list(ring.coords)
        for a, b in zip(c, c[1:]):
            seg = LineString([a, b])
            if seg.length < 1e-6:
                continue
            rest = seg
            for k in (["ZONE_SPLIT_EXPLICIT"] if extra is not None else []) + order:
                geom = extra if k == "ZONE_SPLIT_EXPLICIT" else cache.get(k)
                if geom is None or rest.is_empty:
                    continue
                part = rest.intersection(geom)
                Lp = part.length
                if Lp > 1.0:
                    out.append({"kind": "ZONE_SPLIT" if k == "ZONE_SPLIT_EXPLICIT" else k, "length_m": Lp * F.u / 1000.0,
                                "ring": ri, "a": a, "b": b})
                    rest = rest.difference(geom)
            if not rest.is_empty and rest.length > 1.0:
                out.append({"kind": "UNKNOWN_EDGE", "length_m": rest.length * F.u / 1000.0, "ring": ri, "a": a, "b": b})
    return out


# ============================================================================================ physical spaces
def _wall_fraction(F, poly):
    c = F._edge_cache if getattr(F, "_edge_cache", None) else None
    if c is None:
        edge_kinds(F, Polygon([(0, 0), (1, 0), (1, 1)]))
        c = F._edge_cache
    ext = poly.exterior
    g = c["WALL"] if c["COLUMN"] is None else c["WALL"].union(c["COLUMN"])
    return ext.intersection(g).length / ext.length if ext.length else 0.0


def site_class(F, s, shaft_sites):
    c = s["poly"].representative_point()
    if not F.plate.buffer(500.0).contains(c):
        return "OUTSIDE_PLATE", "representative point outside the registered structural floor plate (sheet note / legend)"
    if s["site_id"] in shaft_sites:
        return "SHAFT", "same unnamed footprint on every storey (V3 shaft evidence)"
    if s["kind"] == "OBSTACLE_INTERIOR":
        if any(col.buffer(30.0).contains(c) for col in F.cols):
            return "COLUMN", "obstacle interior inside a column outline (S-COL.BON)"
        return "OBSTACLE", "obstacle interior (not a column outline)"
    if s["kind"] == "OPENING_SITE":
        return "OPENING_STRIP", "strip between two closures of one opening"
    if s["area_m2"] < MIN_SPACE_M2 or s["eff_width_m"] < MIN_WIDTH_M:
        if 0.04 <= s["eff_width_m"] <= 0.45 and _wall_fraction(F, s["poly"]) >= 0.6:
            return "WALL_BAND", f"thin face (effective width {s['eff_width_m']:.3f} m) bounded by wall / column lines"
        return "SLIVER", f"area {s['area_m2']:.3f} m2 / effective width {s['eff_width_m']:.3f} m below the room-like limit"
    return "SPACE", "room-like free space"


def physical_spaces(ctx, Fs):
    shaft_sites = {r["site"] for r in ctx["v3"]["rooms"]["rows"] if r["room_class"] == "SHAFT"}
    rows = []
    for fl, F in Fs.items():
        for s in F.sites:
            cls, why = site_class(F, s, shaft_sites)
            s["r5_class"] = cls
            poly = s["poly"]
            lab = [l for l in F.labels if poly.contains(Point(l["x"], l["y"]))]
            s["labels_r5"] = lab
            ek = edge_kinds(F, poly) if cls in ("SPACE", "SHAFT") else []
            kinds = defaultdict(float)
            for e in ek:
                kinds[e["kind"]] += e["length_m"]
            s["edge_kinds"] = ek
            vs = [v for v in F.voids if v.get("site") == s["site_id"]]
            status = ("EXTERNAL" if lab and all(l["class"] == "EXTERNAL" for l in lab) else
                      "CONTAINS_VOID" if vs else "OUTSIDE_PLATE" if cls == "OUTSIDE_PLATE" else "INTERNAL")
            obstacles = [i for i, col in enumerate(F.cols) if col.intersects(poly.buffer(30.0)) and
                         not col.within(poly.buffer(-30.0))]
            c = poly.centroid
            rows.append({"space_id": f"PS:{fl}:{s['site_id']}", "floor": fl, "site_id": s["site_id"], "route": "A",
                         "class": cls, "class_why": why, "area_m2": _r(s["area_m2"]),
                         "polygon_area_m2": _r(_m2(poly.area)), "perimeter_m": _r(s["perimeter_m"]),
                         "centroid": [_r(c.x, 1), _r(c.y, 1)], "effective_width_m": _r(s["eff_width_m"], 3),
                         "boundary_m_by_kind": {k: _r(v) for k, v in sorted(kinds.items())},
                         "closure_method": "ROUTE_A_ROOM_TOPOLOGY_V3 (source linework + door / gap closures)",
                         "closure_confidence": "CERTIFIED" if s["status"] == "CERTIFIED" else "REVIEW_REQUIRED",
                         "open_transitions_m": _r(kinds.get("OPEN_PASSAGE", 0.0)),
                         "doors_m": _r(kinds.get("DOOR", 0.0)),
                         "labels_inside": [{"occurrence": l["occurrence"], "text": l["text_en"], "class": l["class"]}
                                           for l in lab],
                         "structural_obstacles_touching": len(obstacles), "external_status": status,
                         "voids": [v["id"] for v in vs], "contains_stair": (s["contents"].get("STAIR_GEOMETRY") or 0) > 0,
                         "source_handles": s["boundary_sources"][:80],
                         "source_handles_total": len(s["boundary_sources"])})
    return rows


# ============================================================================================ recovery
def uncovered(F):
    inside = [s["poly"].intersection(F.plate) for s in F.sites if s.get("r5_class") != "OUTSIDE_PLATE"]
    U = unary_union([g for g in inside if not g.is_empty])
    D = F.plate.difference(U)
    return [g for g in getattr(D, "geoms", [D]) if g.geom_type == "Polygon" and not g.is_empty], U


def recover(F):
    """Plate area covered by no Route A site: Route B faces closed by source linework (+ recorded closures) lying in
    it become RECOVERED_PHYSICAL_REGION candidates; the rest stays UNRESOLVED_BLOCKED (accounted, never dropped)."""
    comps, U = uncovered(F)
    rec, rest = [], []
    faces = [f for f in F.route_b["faces"] if f["net_area_m2"] >= 0.3]
    for i, comp in enumerate(sorted(comps, key=lambda g: (-g.area, g.centroid.x))):
        if _m2(comp.area) < 1e-4:
            continue
        taken = []
        for f in faces:
            fp = f["poly"]
            if not fp.intersects(comp):
                continue
            inter = fp.intersection(comp)
            if _m2(inter.area) >= MIN_SPACE_M2 and inter.area >= 0.8 * fp.area:
                taken.append((f, inter))
        used = unary_union([g for _, g in taken]) if taken else None
        for f, g in taken:
            for part in getattr(g, "geoms", [g]):
                if part.geom_type != "Polygon" or _m2(part.area) < 0.05:
                    continue
                rec.append({"id": f"RR:{F.fl}:{f['face_id']}", "poly": part, "route_b_face": f["face_id"],
                            "component": i, "area_m2": _m2(part.area),
                            "closure_sources": sorted({s for s in f["boundary_sources"] if s.startswith(("BRIDGE", "DOORCLOSE"))})})
        left = comp.difference(used) if used is not None else comp
        for k, part in enumerate(getattr(left, "geoms", [left])):
            if part.geom_type == "Polygon" and part.area > 0:
                rest.append({"id": f"UR:{F.fl}:{i}:{k}", "poly": part, "area_m2": _m2(part.area), "component": i})
    return rec, rest


# ============================================================================================ route comparison
def shadow_comparison(Fs):
    rows, summary = [], {}
    for fl, F in Fs.items():
        A = [s for s in F.sites if s.get("r5_class") == "SPACE"]
        B = [f for f in F.route_b["faces"] if f["net_area_m2"] >= MIN_SPACE_M2 and
             f["poly"].intersection(F.plate).area >= 0.5 * f["poly"].area]
        tree = STRtree([f["poly"] for f in B])
        matched_b = defaultdict(list)
        for s in A:
            pa = s["poly"]
            cands = []
            for j in tree.query(pa):
                pb = B[j]["poly"]
                inter = pa.intersection(pb).area
                if inter <= 0:
                    continue
                iou = inter / pa.union(pb).area
                cands.append((iou, inter, j))
            cands.sort(reverse=True)
            cover = [c for c in cands if c[1] >= 0.5 * B[c[2]]["poly"].area]
            best = cands[0] if cands else None
            if best and best[0] >= 0.9:
                kind = "MATCH"
            elif best and len(cover) >= 2 and sum(c[1] for c in cover) >= 0.9 * pa.area:
                kind = "A_COARSER_SPLIT_IN_B"
            elif best and best[1] >= 0.9 * pa.area and best[0] < 0.9:
                kind = "B_COARSER_MERGED_IN_B"
            elif best:
                kind = "PARTIAL_OVERLAP"
            else:
                kind = "MISSING_IN_B"
            for c in cands:
                matched_b[c[2]].append(s["site_id"])
            pb = B[best[2]]["poly"] if best else None
            row = {"floor": fl, "route_a_site": s["site_id"], "labels": [l["text_en"] for l in s.get("labels_r5", [])],
                   "a_area_m2": _r(s["area_m2"]), "a_perimeter_m": _r(s["perimeter_m"]),
                   "b_face": B[best[2]]["face_id"] if best else None,
                   "b_area_m2": _r(B[best[2]]["net_area_m2"]) if best else None,
                   "b_perimeter_m": _r(B[best[2]]["perimeter_m"]) if best else None,
                   "iou": _r(best[0], 4) if best else 0.0,
                   "centroid_shift_m": _r(pa.centroid.distance(pb.centroid) * F.u / 1000.0, 3) if pb is not None else None,
                   "b_faces_covering": len(cover), "relation": kind}
            if kind != "MATCH":
                row["disagreement"] = {"MISSING_IN_B": "Route B closes no face here",
                                       "A_COARSER_SPLIT_IN_B": "Route B splits this space (thin / non-wall lines or "
                                                               "closures Route A does not use)",
                                       "B_COARSER_MERGED_IN_B": "Route B merges this space with a neighbour (an opening "
                                                                "Route A closes is not closed in B)",
                                       "PARTIAL_OVERLAP": "different boundary"}[kind]
            rows.append(row)
        extra = []
        for j, f in enumerate(B):
            if j not in matched_b:
                extra.append({"floor": fl, "b_face": f["face_id"], "b_area_m2": _r(f["net_area_m2"]),
                              "interior_point": [_r(f["interior_point"][0], 1), _r(f["interior_point"][1], 1)],
                              "relation": "MISSING_IN_A"})
        rel = Counter(r["relation"] for r in rows if r["floor"] == fl)
        summary[fl] = {"route_a_spaces": len(A), "route_b_faces_ge_1m2": len(B), "relations": dict(rel),
                       "missing_in_a": len(extra), "missing_in_a_m2": _r(sum(x["b_area_m2"] for x in extra)),
                       "route_b_counts": F.route_b["counts"], "route_b_bridges": len(F.route_b["bridges"]),
                       "route_b_door_closures": len(F.route_b["door_closures"])}
        rows += extra
    return rows, summary


# ============================================================================================ semantic + trade regions
def _hosts(F, rec):
    """Every space a label can belong to: Route A SPACE / SHAFT sites and recovered regions."""
    hs = []
    for s in F.sites:
        if s.get("r5_class") in ("SPACE", "SHAFT"):
            hs.append({"host_id": f"PS:{F.fl}:{s['site_id']}", "poly": s["poly"], "kind": "ROUTE_A_SITE",
                       "site": s, "space_class": s["r5_class"]})
    for r in rec:
        hs.append({"host_id": f"PS:{F.fl}:{r['id']}", "poly": r["poly"], "kind": "RECOVERED", "rec": r,
                   "space_class": "RECOVERED_SPACE"})
    return hs


def label_points(l):
    pts = [("EN", Point(l["x"], l["y"]))]
    if l.get("x_ar") is not None:
        pts.append(("AR", Point(l["x_ar"], l["y_ar"])))
    return pts


def assign_labels(F, hosts):
    """occurrence -> (host_id | None, authority). A label occurrence is one room. When its English and Arabic texts
    fall in two spaces, it belongs to the space that holds one of its texts and no other room label (the other text
    overhangs) - BILINGUAL_TWIN_PLACEMENT; otherwise the English anchor decides (flagged)."""
    hit = {}
    for l in F.labels:
        hs = []
        for _, p in label_points(l):
            h = next((h for h in hosts if h["poly"].contains(p)), None)
            if h is not None and h["host_id"] not in hs:
                hs.append(h["host_id"])
        hit[l["occurrence"]] = hs
    out = {}
    for occ, hs in hit.items():
        if not hs:
            out[occ] = (None, "NO_HOST")
        elif len(hs) == 1:
            out[occ] = (hs[0], "LABEL_INSIDE_SPACE")
        else:
            free = [h for h in hs if not any(h in v and o != occ for o, v in hit.items())]
            if len(free) == 1:
                out[occ] = (free[0], "BILINGUAL_TWIN_PLACEMENT (one text in a space with no other label; the other "
                                     "text overhangs into a neighbour)")
            else:
                out[occ] = (hs[0], "LABEL_SPANS_SPACES_EN_ANCHOR (ambiguous)")
    return out


def orphan_labels(Fs, recs):
    rows = []
    for fl, F in Fs.items():
        rec, rest = recs[fl]
        hosts = _hosts(F, rec)
        asg = assign_labels(F, hosts)
        for l in F.labels:
            p = Point(l["x"], l["y"])
            site = next((s for s in F.sites if s["poly"].contains(p)), None)
            hid = asg[l["occurrence"]][0]
            host = next((h for h in hosts if h["host_id"] == hid), None)
            if host is not None and host["kind"] == "ROUTE_A_SITE":
                continue                                                   # bound in Route A: not an orphan
            near_walls = sorted((g.distance(p) * F.u / 1000.0, sid) for g, sid, _ in F.lines.get(WALL_L, []))[:3]
            near_sp = sorted((s["poly"].distance(p) * F.u / 1000.0, s["site_id"]) for s in F.sites
                             if s.get("r5_class") == "SPACE")[:3]
            fix = [f["insert"] for f in F.fixtures if math.hypot(f["x"] - l["x"], f["y"] - l["y"]) <= 3000.0]
            doors = [k for k, d in F.doors.items() if math.dist(d["hinge"], (l["x"], l["y"])) <= 3500.0]
            obst = sum(1 for c in F.cols if c.distance(p) <= 2000.0)
            if not F.plate.buffer(500.0).contains(p) or (host is None and l["class"] in ("ROOF", "EXTERNAL")):
                outcome, why = "NOT_IN_SCOPE_EXTERNAL", ("external label (court / roof terrace / street): roof and "
                                                         "external trades, not an internal space")
            elif host is not None and host["kind"] == "RECOVERED":
                outcome = "RECOVERED_PHYSICAL_REGION"
                why = ("Route A left this plate area unclosed; Route B closes it from source linework + recorded "
                       "closures " + ", ".join(host["rec"]["closure_sources"][:4]))
            elif site is not None and site.get("r5_class") in ("WALL_BAND", "SLIVER", "OPENING_STRIP"):
                own = min(near_sp)[1] if near_sp else None
                outcome, why = "LABEL_BELONGS_TO_EXISTING_REGION", f"text placed over a {site['r5_class']}; nearest space {own}"
            else:
                outcome = "BLOCKED_TOPOLOGY"
                why = ("label in plate area that neither Route A nor Route B closes (the room shares an unclosed "
                       "opening with a neighbour; no wall is invented)")
            cand = [{"route_b_face": f["face_id"], "area_m2": _r(f["net_area_m2"])} for f in F.route_b["faces"]
                    if f["poly"].contains(p) and f["net_area_m2"] < 400]
            rows.append({"floor": fl, "occurrence": l["occurrence"], "text": l["text_en"], "text_ar": l["text_ar"],
                         "normalized_identity": l["class"], "xy": [_r(l["x"], 1), _r(l["y"], 1)],
                         "nearest_walls": [{"m": _r(d, 3), "source": s} for d, s in near_walls],
                         "nearest_spaces": [{"m": _r(d, 3), "site": s} for d, s in near_sp],
                         "sanitary_fixtures_nearby": fix, "doors_nearby": doors, "structural_obstacles_nearby": obst,
                         "candidate_polygons": cand, "route_a_site_under_label": site["site_id"] if site else None,
                         "reason_closure_failed": "no Route A site contains the label" if site is None else
                         f"Route A site under the label is a {site.get('r5_class')}",
                         "outcome": outcome, "why": why, "host": host["host_id"] if host else None})
    return rows


def trade_regions(ctx, Fs, recs):
    """Split each physical space into trade measurement regions. A space with one semantic class is one region. A
    space holding several classes is split ONLY along positive source boundaries (Route B faces: thin non-wall lines,
    door / gap closures); a piece that still holds several classes stays MIXED_UNRESOLVED; an unlabelled piece of a
    split space stays UNASSIGNED. A labelled void polygon (X-rect / arcs evidence) is its own VOID region."""
    zones, regions = [], []
    for fl, F in Fs.items():
        rec, _ = recs[fl]
        hosts = _hosts(F, rec)
        asg = assign_labels(F, hosts)
        for h in hosts:
            poly = h["poly"]
            labs = [l for l in F.labels if asg[l["occurrence"]][0] == h["host_id"]]
            # void evidence first
            vpolys = []
            if h["kind"] == "ROUTE_A_SITE":
                for v in F.voids:
                    if v.get("site") == h["site"]["site_id"] and v.get("_polygon"):
                        vpolys.append((v["id"], Polygon(v["_polygon"]).buffer(0).intersection(poly)))
            body = poly
            for vid, vp in vpolys:
                if not vp.is_empty:
                    regions.append(_region(F, h, vid, vp, "VOID", [l for l in labs if l["class"] == "VOID"],
                                           "VOID_OUTLINE_EVIDENCE (V3 void: X-rect / arcs)", AQ.VC))
                    body = body.difference(vp)
            labs_b = [l for l in labs if l["class"] != "VOID" or not vpolys]
            classes = sorted({l["class"] for l in labs_b})
            for l in labs:
                zones.append({"zone_id": f"SZ:{fl}:{l['occurrence']}", "floor": fl, "host": h["host_id"],
                              "label": l["text_en"], "label_ar": l["text_ar"], "class": l["class"],
                              "authority": ("ROOM_LABEL (EN + corroborated AR)" if l["arabic_corroboration"] ==
                                            "CORROBORATED" else "ROOM_LABEL (EN)") + " | " + asg[l["occurrence"]][1]})
            if h["space_class"] == "SHAFT":  # noqa
                regions.append(_region(F, h, "R", body, "SHAFT", labs_b, "SHAFT_EVIDENCE (same footprint every storey)",
                                       AQ.PROV))
                continue
            if len(classes) <= 1:
                cls = classes[0] if classes else ("STAIR" if h.get("site") and
                                                  (h["site"]["contents"].get("STAIR_GEOMETRY") or 0) > 0 else "UNKNOWN")
                twin = any(asg[l["occurrence"]][1].startswith("BILINGUAL") for l in labs_b)
                regions.append(_region(F, h, "R", body, cls, labs_b,
                                       ("SINGLE_CLASS_SPACE" + (" (BILINGUAL_TWIN_PLACEMENT)" if twin else ""))
                                       if classes else "UNLABELLED_SPACE",
                                       (AQ.PROV if twin else AQ.VC) if classes else AQ.BLK))
                continue
            # mixed: split along Route B faces
            pieces = []
            for f in F.route_b["faces"]:
                if f["net_area_m2"] > 400:
                    continue
                inter = f["poly"].intersection(body)
                if _m2(inter.area) >= 0.05 and not any(inter.intersection(g).area > 1.0 for _, g in pieces):
                    pieces.append((f, inter))
            cover = sum(g.area for _, g in pieces)
            if cover < 0.97 * body.area:
                regions.append(_region(F, h, "R", body, "MIXED_UNRESOLVED", labs_b,
                                       f"split impossible: Route B covers {cover / body.area:.0%} of the space", AQ.BLK))
                continue
            remainder = body.difference(unary_union([g for _, g in pieces]))
            if remainder.area > 0:
                regions.append(_region(F, h, "REMAINDER", remainder, "UNASSIGNED", [],
                                       "REMAINDER_OF_SPLIT (slivers below 0.05 m2 / outside every Route B face)", AQ.BLK))
            plist = []
            for f, g in sorted(pieces, key=lambda z: -z[1].area):
                pl = [l for l in labs_b if any(g.buffer(1.0).contains(p) for _, p in label_points(l))]
                plist.append({"id": f["face_id"], "area_m2": _m2(g.area), "classes": [l["class"] for l in pl],
                              "_f": f, "_g": g, "_pl": pl})
            auth_of = {"MIXED_UNRESOLVED": "PIECE_HOLDS_SEVERAL_CLASSES", "UNASSIGNED": "PIECE_OF_SPLIT_SPACE_WITHOUT_LABEL"}
            for d in AQ.assign_split(plist):
                regions.append(_region(F, h, d["id"], d["_g"], d["cls"], d["_pl"],
                                       auth_of.get(d["cls"], "SPLIT_BY_POSITIVE_SOURCE_BOUNDARY + LABEL"), d["state"],
                                       split_face=d["_f"]))
    return zones, regions


def _region(F, h, key, poly, cls, labels, authority, sem_state, split_face=None):
    indoor = cls not in ("EXTERNAL", "ROOF") and F.plate.buffer(10.0).contains(poly.representative_point())
    return {"region_id": f"TR:{F.fl}:{h['host_id'].split(':', 2)[2]}:{key}", "floor": F.fl, "host": h["host_id"],
            "host_kind": h["kind"], "class": cls, "labels": [l["text_en"] for l in labels],
            "label_occurrences": [l["occurrence"] for l in labels], "label_classes": sorted({l["class"] for l in labels}),
            "semantic_authority": authority,
            "semantic_state": sem_state, "indoor": indoor, "area_m2": _r(_m2(poly.area)),
            "split_face": split_face["face_id"] if split_face else None, "_poly": poly}


# ============================================================================================ floor conservation
INTERNAL_CLASSES = ("DRY", "WET", "SERVICE", "UNKNOWN", "STAIR", "MIXED_UNRESOLVED", "UNASSIGNED")


def floor_conservation(Fs, recs, regions):
    """plate (registered structural slab outline, arch coords) = Route A sites (by class) + recovered regions +
    UNRESOLVED residual. Every residual polygon is listed. The architect's area sheet (Route C) is reported beside."""
    rows, residuals, by_floor = [], [], {}
    for fl, F in Fs.items():
        rec, rest = recs[fl]
        parts = []
        reg_by_host = defaultdict(list)
        for r in regions:
            if r["floor"] == fl:
                reg_by_host[r["host"]].append(r)
        for s in F.sites:
            cls = s.get("r5_class")
            if cls == "OUTSIDE_PLATE":
                continue
            g = s["poly"].intersection(F.plate)
            a = _m2(g.area)
            if a <= 0:
                continue
            hid = f"PS:{fl}:{s['site_id']}"
            if cls in ("SPACE", "SHAFT"):
                for r in reg_by_host.get(hid, []):
                    ra = _m2(r["_poly"].intersection(F.plate).area)
                    comp = {"VOID": "VOID", "SHAFT": "SHAFT", "EXTERNAL": "EXTERNAL_SPACE"}.get(r["class"],
                                                                                              "INTERNAL_SPACE")
                    parts.append({"id": r["region_id"], "component": comp, "area_m2": ra, "class": r["class"]})
            else:
                comp = {"WALL_BAND": "WALL_BAND", "COLUMN": "COLUMN", "OBSTACLE": "COLUMN",
                        "OPENING_STRIP": "OPENING_STRIP", "SLIVER": "SLIVER"}[cls]
                parts.append({"id": hid, "component": comp, "area_m2": a, "class": cls})
        for r in rec:
            for t in reg_by_host.get(f"PS:{fl}:{r['id']}", []):
                ra = _m2(t["_poly"].intersection(F.plate).area)
                comp = "EXTERNAL_SPACE" if t["class"] == "EXTERNAL" else "RECOVERED_SPACE"
                parts.append({"id": t["region_id"], "component": comp, "area_m2": ra, "class": t["class"]})
        vpolys = [Polygon(v["_polygon"]).buffer(0) for v in F.voids if v.get("_polygon")]
        arcvoid = [Polygon(PT.discretise_arc(v["evidence"]["centre"][0], v["evidence"]["centre"][1],
                                             v["evidence"]["radius_mm"], 0, 2 * math.pi)) for v in F.voids
                   if (v.get("evidence") or {}).get("rule") == "ARCS"]
        for u in rest:
            g = u["poly"]
            vv = unary_union(vpolys + arcvoid) if (vpolys or arcvoid) else None
            if vv is not None and _m2(g.intersection(vv).area) > 0.05:
                vg = g.intersection(vv)
                parts.append({"id": u["id"] + ":VOID", "component": "VOID", "area_m2": _m2(vg.area),
                              "class": "VOID_OUTLINE_IN_UNCLOSED_AREA"})
                g = g.difference(vv)
            if g.area > 0:
                parts.append({"id": u["id"], "component": "UNRESOLVED_BLOCKED", "area_m2": _m2(g.area),
                              "class": "UNCLOSED_PLATE_AREA"})
                c = g.representative_point()
                labs = [l["text_en"] for l in F.labels if g.contains(Point(l["x"], l["y"]))]
                residuals.append({"id": u["id"], "floor": fl, "area_m2": _r(_m2(g.area)),
                                  "point": [_r(c.x, 1), _r(c.y, 1)], "labels_inside": labs,
                                  "state": "UNRESOLVED_BLOCKED",
                                  "why": "plate area that neither Route A nor Route B closes (open to a neighbour / "
                                         "outside across an unclosed gap); accounted, never dropped"})
        cons = AQ.floor_conservation(_m2(F.plate.area), parts, tol_m2=0.05)
        sites_out = sum(_m2(s["poly"].difference(F.plate).area) for s in F.sites if s.get("r5_class") != "OUTSIDE_PLATE")
        arch = ARCH_AREA_SHEET[fl]
        internal = sum(p["area_m2"] for p in parts if p["component"] in ("INTERNAL_SPACE", "RECOVERED_SPACE"))
        by_floor[fl] = {"plate_m2": _r(_m2(F.plate.area)), "plate_source": "ST7757 slab outline registered to P7757 "
                        "(b2a registration)", "architect_area_sheet_m2": arch["total_m2"],
                        "architect_area_sheet_after_deduction_m2": arch.get("after_deduction_m2", arch["total_m2"]),
                        "plate_minus_architect_m2": _r(_m2(F.plate.area) - arch["total_m2"]),
                        "conservation": {k: v for k, v in cons.items() if k != "violations"},
                        "violations": cons["violations"], "route_a_site_area_outside_plate_m2": _r(sites_out),
                        "internal_floor_area_m2": _r(internal),
                        "internal_by_class_m2": {k: _r(sum(p["area_m2"] for p in parts if p.get("class") == k and
                                                            p["component"] in ("INTERNAL_SPACE", "RECOVERED_SPACE")))
                                                 for k in INTERNAL_CLASSES}}
        rows += [dict(p, floor=fl, area_m2=_r(p["area_m2"])) for p in parts]
    return {"floors": by_floor, "components": rows, "residuals": residuals}


# ============================================================================================ wet / service
def wet_completeness(Fs, recs, regions, orphans):
    rows = []
    reg_by_occ = {}
    for r in regions:
        for o in r["label_occurrences"]:
            reg_by_occ[(r["floor"], o)] = r
    orph = {(o["floor"], o["occurrence"]): o for o in orphans}
    for fl, F in Fs.items():
        for l in F.labels:
            if l["class"] not in ("WET", "SERVICE") and "swimming" not in (l["text_en"] or "").lower():
                continue
            key = (fl, l["occurrence"])
            r = reg_by_occ.get(key)
            if "swimming" in (l["text_en"] or "").lower() or "POOL" in (l["text_en"] or "").upper():
                st, why = "NOT_IN_SCOPE", "swimming pool: pool population (structure + finish), not a wet room"
            elif r is None:
                o = orph.get(key)
                st, why = "BLOCKED", (o["why"] if o else "label host not established")
            elif r["class"] in ("WET", "SERVICE"):
                st, why = "BOUND", f"{r['region_id']} ({r['semantic_authority']})"
            elif r["class"] in ("MIXED_UNRESOLVED",):
                st, why = "BLOCKED", f"{r['region_id']} holds wet and dry zones without a source boundary"
            else:
                st, why = "BLOCKED", f"region class {r['class']}"
            rows.append({"floor": fl, "occurrence": l["occurrence"], "label": l["text_en"], "label_ar": l["text_ar"],
                         "class": l["class"], "state": st, "why": why, "region": r["region_id"] if r else None,
                         "fixtures_nearby": [f["insert"] for f in F.fixtures
                                             if math.hypot(f["x"] - l["x"], f["y"] - l["y"]) <= 3000.0]})
    return rows


# ============================================================================================ walls
def _unit(a, b):
    L = math.dist(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L), L


def wall_ledger(ctx, Fs):
    """Independent wall rebuild. Admitted candidates: every part on the wall (1), column (S-COL.BON), glazing (W) and
    thin-line (5) layers, plus the recorded zero-material closures (door closures, gap bridges). Each straight wall-
    layer segment is paired with parallel wall-layer segments 60-450 mm away (nearest partner per sub-interval) and
    split into pieces; every piece terminates in exactly ONE class. Masonry needs paired faces + the wall layer + a
    structural cross-check (registered floor) - thickness alone gives BLOCKED_MATERIAL."""
    pieces, admitted, bands = [], {}, []
    for fl, F in Fs.items():
        u = F.u
        roles = F.res["roles"]["roles"]
        reg_ok = ctx["b2a"]["registration"][fl]["state"] == "REGISTERED"
        plate_b = F.plate.buffer(300.0)
        voids = [Polygon(v["_polygon"]).buffer(0) for v in F.voids if v.get("_polygon")]
        void_edge = unary_union([v.exterior for v in voids]).buffer(60.0) if voids else None
        colu = unary_union([c.buffer(40.0) for c in F.cols]) if F.cols else None
        segs = []
        for g, sid, p in F.lines.get(WALL_L, []):
            if p.kind == "SEGMENT":
                segs.append((sid, tuple(g.coords[0]), tuple(g.coords[1])))
        seglen = {sid: math.dist(a_, b_) for sid, a_, b_ in segs}
        for sid, L_ in seglen.items():
            if L_ > 1.0:
                admitted[f"{fl}|{sid}"] = L_ * u / 1000.0
        for q in AQ.pair_wall_faces([x for x in segs if seglen[x[0]] > 1.0], min_mm=WALL_PAIR_MM[0],
                                    max_mm=WALL_PAIR_MM[1]):
            sid = q["seg"]
            pa, pb = q["a"], q["b"]
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            Lm = q["length"] * u / 1000.0
            rec = {"piece_id": f"{fl}|{sid}|{q['t0']:.1f}", "parent": f"{fl}|{sid}", "floor": fl, "layer": WALL_L,
                   "source": sid, "length_m": Lm, "a": pa, "b": pb}
            if q["partner"] is not None:
                w = q["width"] * u
                cm = ((q["centre_a"][0] + q["centre_b"][0]) / 2, (q["centre_a"][1] + q["centre_b"][1]) / 2)
                inside = plate_b.contains(Point(cm))
                rc = colu is not None and colu.contains(Point(cm))
                if not inside:
                    cls, auth, why = "EXCLUDED_WITH_REASON", None, "paired band outside the building plate (plot " \
                                                                   "boundary / external wall of the plot: separate trade)"
                else:
                    cls, auth, why = AQ.wall_class(width_mm=w, paired=True, on_wall_layer=True, rc_overlap=rc,
                                                   structural_checked=reg_ok)
                rec.update({"paired": True, "partner": q["partner"], "width_mm": _r(w, 1), "class": cls,
                            "material_authority": auth, "why": why, "centre_a": q["centre_a"], "centre_b": q["centre_b"],
                            "rc_at_centre": rc})
            else:
                role = getattr(roles.get(sid), "role", None)
                if role == "SHEET_FRAME":
                    cls, why = "NOT_WALL", "sheet frame"
                elif not plate_b.contains(Point(mid)):
                    cls, why = "EXTERNAL_BOUNDARY_NON_WALL", "single line outside the building plate"
                elif colu is not None and colu.contains(Point(mid)):
                    cls, why = "RC_COLUMN_INTERFACE", "single line inside a column outline"
                else:
                    cls, why = "AMBIGUOUS_BLOCKED", "single wall-layer line: no paired face, thickness unknown"
                rec.update({"paired": False, "class": cls, "why": why, "width_mm": None})
            pieces.append(rec)
        # other admitted layers: one piece per part
        for layer, default in ((COL_L, "RC_COLUMN_INTERFACE"), (WIN_L, "GLAZING"), (THIN_L, "NOT_WALL")):
            for g, sid, p in F.lines.get(layer, []):
                if layer == WALL_L:
                    continue
                Lm = g.length * u / 1000.0
                if Lm <= 0:
                    continue
                mid = g.interpolate(0.5, normalized=True)
                role = getattr(roles.get(sid), "role", None)
                if layer == THIN_L:
                    if void_edge is not None and void_edge.contains(g):
                        cls, why = "RAILING_VOID_EDGE", "thin line on a void outline (guard / railing edge)"
                    elif not plate_b.contains(mid):
                        cls, why = "EXTERNAL_BOUNDARY_NON_WALL", "thin line outside the building plate (plot / site)"
                    elif role == "STAIR_GEOMETRY":
                        cls, why = "NOT_WALL", "stair geometry"
                    else:
                        cls, why = "NOT_WALL", "thin-line layer inside the plate (counter / glazing frame / fixture / " \
                                               "pool / landscape edge): not a masonry wall"
                elif layer == WIN_L:
                    cls, why = ("GLAZING", "glazing layer") if plate_b.contains(mid) else \
                        ("EXTERNAL_BOUNDARY_NON_WALL", "glazing-layer line outside the plate")
                else:
                    cls, why = default, "column outline (S-COL.BON)"
                admitted[f"{fl}|{sid}"] = Lm
                pieces.append({"piece_id": f"{fl}|{sid}|0", "parent": f"{fl}|{sid}", "floor": fl, "layer": layer,
                               "source": sid, "length_m": Lm, "paired": False, "class": cls, "why": why,
                               "width_mm": None})
        # zero-material closures (openings in wall runs)
        for x0, y0, x1, y1, sid in F.route_b["door_closures"] + F.route_b["bridges"]:
            ls = LineString([(x0, y0), (x1, y1)])
            Lm = ls.length * u / 1000.0
            near_door = sid.startswith("DOORCLOSE") or any(Point(d["hinge"]).distance(ls) <= d["radius"] + 200.0
                                                           for d in F.doors.values())
            cls = "DOOR_OPENING" if near_door else "OPEN_TRANSITION"
            if not plate_b.contains(ls.interpolate(0.5, normalized=True)):
                cls = "EXTERNAL_BOUNDARY_NON_WALL"
            pid = f"{fl}|{sid}"
            admitted[pid] = Lm
            pieces.append({"piece_id": pid + "|0", "parent": pid, "floor": fl, "layer": "CLOSURE", "source": sid,
                           "length_m": Lm, "paired": False, "class": cls, "width_mm": None,
                           "why": "zero-material closure across a wall-face gap (" +
                                  ("door swing" if near_door else "no door symbol") + ")"})
    return pieces, admitted


def wall_summary(pieces, admitted):
    chk = AQ.ledger_check(admitted, pieces)
    by = defaultdict(lambda: defaultdict(float))
    run = defaultdict(lambda: defaultdict(float))
    for p in pieces:
        by[p["floor"]][p["class"]] += p["length_m"]
        if p["layer"] == WALL_L:
            run[p["floor"]][p["class"]] += p["length_m"] * (0.5 if p.get("paired") else 1.0)
    return chk, {fl: {k: _r(v) for k, v in sorted(d.items())} for fl, d in by.items()}, \
        {fl: {k: _r(v) for k, v in sorted(d.items())} for fl, d in run.items()}


# ============================================================================================ openings
R2_HEIGHT_MAP = {("RASTER_DERIVED", "PRINTED"): "EXACT_SOURCE",
                 ("RASTER_DERIVED", "RASTER_TYPE_MATCH"): "CROSS_VERIFIED_REPEATED_TYPE",
                 ("PROVISIONAL_SOURCE_DERIVED", "RASTER_TYPE_MATCH_SINGLE"): "SCALED_SOURCE_SINGLE",
                 ("PROVISIONAL_SOURCE_DERIVED", "RASTER_AMBIGUOUS"): "SCALED_SOURCE_SINGLE",
                 ("PROVISIONAL_GEOMETRIC_INFERENCE", "NO_WIDTH_MATCH"): "BUDGET",
                 ("BUDGET_ESTIMATE", "RASTER_AMBIGUOUS"): "BUDGET", ("BUDGET_ESTIMATE", "NO_WIDTH_MATCH"): "BUDGET"}


def _region_at(regions, fl, pt):
    for r in regions:
        if r["floor"] == fl and r["_poly"].buffer(1.0).contains(pt):
            return r
    return None


def openings(ctx, Fs, regions, pieces, r2_rows):
    """OPENING_EVIDENCE_V3: count / width / height / function / material / host wall / room adjacency / floor, each with
    its own state. Height from the typed ladder; no default window height; area only with width AND height."""
    b2 = {r["id"]: r for r in ctx["b2a"]["architecture"]["openings"]["rows"]}
    lint = {r["opening"]: r for r in ctx["v3"]["openings"]["lintels"]}
    masonry = defaultdict(list)
    for p in pieces:
        if p.get("paired") and p["class"] in AQ.MASONRY_CLASSES + ("RC_COLUMN_INTERFACE", "BLOCKED_MATERIAL"):
            masonry[p["floor"]].append(p)
    rows = []
    for r in r2_rows:
        fl = r["floor"]
        F = Fs[fl]
        geom, mid, axis = None, None, None
        if "-D-" in r["id"]:
            k = r["id"].split("-D-")[1]
            d = F.doors.get(k) or F.doors.get("I" + k)
            if d:
                hx, hy = d["hinge"]
                ends = sorted(d["ends"], key=lambda e: min(Point(e).distance(g) for g, _, _ in F.lines.get(WALL_L, [])))
                e = ends[0]
                geom = LineString([(hx, hy), e])
        elif r["id"] in b2 and b2[r["id"]].get("jambs_native"):
            j = b2[r["id"]]["jambs_native"]
            geom = LineString([tuple(j[0]), tuple(j[1])])
        host, adj = None, []
        if geom is not None:
            mid = geom.interpolate(0.5, normalized=True)
            (ux, uy), _ = _unit(geom.coords[0], geom.coords[-1])
            best = None
            for p in masonry[fl]:
                ca, cb = p.get("centre_a"), p.get("centre_b")
                if ca is None:
                    continue
                cl = LineString([ca, cb])
                (vx, vy), Lc = _unit(ca, cb)
                if Lc < 1.0 or abs(ux * vy - uy * vx) > 0.05:
                    continue
                dd = cl.distance(mid)
                if dd <= (p["width_mm"] or 200) / 2 + 150 + geom.length / 2 and (best is None or dd < best[0]):
                    best = (dd, p)
            if best:
                host = {"piece": best[1]["piece_id"], "class": best[1]["class"], "width_mm": best[1]["width_mm"]}
            t = (host or {}).get("width_mm") or 200.0
            for sgn in (1, -1):
                q = Point(mid.x + sgn * (-uy) * (t / 2 + 300), mid.y + sgn * ux * (t / 2 + 300))
                rr = _region_at(regions, fl, q)
                adj.append(rr["region_id"] if rr else ("OUTSIDE_PLATE" if not F.plate.contains(q) else "UNCLOSED"))
        kind = r["kind"]
        flags = r.get("flags") or []
        b2f = (b2.get(r["id"]) or {}).get("function")
        if "GLAZED_DOOR_CANDIDATE" in flags or b2f == "GLAZED_OPENING_FUNCTION_UNKNOWN":
            otype, fstate = "GLAZED_DOOR_CANDIDATE", AQ.BLK
        elif kind in ("DOOR", "DOUBLE_LEAF_DOOR"):
            ext = any(a in ("OUTSIDE_PLATE",) or (a.startswith("TR:") and next(
                (x for x in regions if x["region_id"] == a), {}).get("class") == "EXTERNAL") for a in adj)
            otype, fstate = ("EXTERNAL_DOOR" if ext else "INTERNAL_DOOR"), AQ.VC
        elif kind == "WINDOW":
            otype, fstate = "WINDOW", AQ.VC if b2f in (None, "WINDOW_CANDIDATE", "WINDOW") else AQ.PROV
        else:
            otype, fstate = "UNKNOWN_OPENING", AQ.BLK
        auth = R2_HEIGHT_MAP.get((r["height_class"], r["height_source_state"]))
        ev = [{"authority": auth, "height_m": r["height_m"], "ref": f"R2 {r['height_class']} / {r['height_source_state']}"}] \
            if auth else []
        hk = "WINDOW" if otype in ("WINDOW",) else ("GLAZED_DOOR_CANDIDATE" if otype == "GLAZED_DOOR_CANDIDATE" else "DOOR")
        h = AQ.opening_height(ev, kind=hk)
        wst = AQ.VC if r["width"]["state"] == "VERIFIED" else AQ.BLK
        area = AQ.opening_area(width_m=r["width_m"], width_state=wst, height_m=h["height_m"], height_state=h["state"])
        lt = lint.get(r["id"]) or {}
        rows.append({"id": r["id"], "floor": fl, "type": otype, "r2_kind": kind, "flags": flags,
                     "count": {"value": 1, "state": AQ.VC},
                     "width": {"m": r["width_m"], "state": wst},
                     "height": {"m": h["height_m"], "state": h["state"], "authority": h["authority"], "ref": h["ref"]},
                     "sill_m": r.get("sill_m"),
                     "area": area,
                     "function": {"value": otype, "state": fstate},
                     "material": {"value": "BY_SPEC", "state": AQ.BLK,
                                  "why": "no door / window schedule or specification in the source"},
                     "host_wall": host, "host_state": AQ.VC if host else AQ.BLK,
                     "room_adjacency": adj, "adjacency_state": AQ.VC if geom is not None and "UNCLOSED" not in adj
                     else AQ.BLK,
                     "geometry": [[_r(x, 1), _r(y, 1)] for x, y in geom.coords] if geom is not None else None,
                     "lintel_depth_m": lt.get("D_m")})
    return rows


# ============================================================================================ heights
class Heights:
    """Wall heights along a line (arch coords) from the registered structural framing: storey interval - terminating
    member depth (beam soffit or slab); paint / tile to the finished ceiling (interval - build-up - controlling soffit -
    ceiling allowance). Reuses finish_height (V3) unchanged."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.ivs = {iv["from"]: iv for iv in ctx["b2a"]["intervals"]}
        self.bands = {fl: L._bands(ctx, fl) for fl in FLOORS}

    def _sheet(self, fl):
        sh = self.ctx["b2a"]["sheets"][fl]
        t = sh["slab"]["sheet_thickness_tags_cm"]
        return sh["_plate"], (t[0] if len(t) == 1 else None)

    def room_ctrl(self, fl, poly):
        reg = self.ctx["b2a"]["registration"][fl]
        if reg["state"] != "REGISTERED":
            return None
        from shapely.affinity import translate
        rp = translate(poly, xoff=reg["translation"][0], yoff=reg["translation"][1])
        over = [o for o, bp in self.bands[fl] if bp.intersects(rp.buffer(-AP.EPS)) or bp.buffer(AP.EPS).intersects(rp.boundary)]
        if any(not o["bound"] for o in over):
            return None
        ctrl = max((o["D_cm"] for o in over), default=None)
        return ctrl if ctrl is not None else self._sheet(fl)[1]

    def along(self, fl, a, b, *, wet=False, room_ctrl=None):
        """[(length_mm, heights dict)] along the line a-b."""
        reg = self.ctx["b2a"]["registration"][fl]
        if reg["state"] != "REGISTERED":
            return [(math.dist(a, b), None)]
        dx, dy = reg["translation"]
        plate, t_cm = self._sheet(fl)
        out = []
        for pc in G.face_pieces(((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)), self.bands[fl], plate, t_cm,
                                eps=AP.EPS):
            hts = FH.wall_heights(interval=self.ivs.get(fl), term=pc["termination"], room_ctrl_D_cm=room_ctrl, wet=wet,
                                  buildup_above_m=BUILDUP_M)
            hts["_D_cm"] = pc["termination"].get("D_cm")
            out.append((pc["length"], hts))
        return out


def blockwork(ctx, Fs, pieces, ops, H):
    """BLOCKWORK_LENGTH (per floor / class) and BLOCKWORK_AREA: each masonry face piece contributes half the band
    (length / 2 x height at the band centreline); bands stop at openings and RC (the gaps and RC pieces are other
    classes), so no masonry is counted behind RC or across an opening. Masonry over / under an opening is separate and
    needs the opening height."""
    rows = []
    for p in pieces:
        if p["class"] not in AQ.MASONRY_CLASSES:
            continue
        fl = p["floor"]
        segs = H.along(fl, p["centre_a"], p["centre_b"])
        tot_len = sum(L_ for L_, _ in segs) or 1.0
        for k, (Ln, hts) in enumerate(segs):
            Lm = p["length_m"] * (Ln / tot_len) * 0.5
            hb = (hts or {}).get("BLOCKWORK") or {"height_m": None, "state": "BLOCKED_NO_REGISTRATION"}
            hst = AQ.VC if hb["height_m"] is not None else AQ.BLK
            q = AQ.blockwork_area(length_m=Lm, height_m=hb["height_m"], height_state=hst, material_state=AQ.PROV)
            rows.append({"floor": fl, "piece": p["piece_id"], "sub": k, "class": p["class"], "width_mm": p["width_mm"],
                         "length_m_half_band": _r(Lm), "height_m": hb["height_m"],
                         "height_basis": hb.get("basis") or hb.get("state"),
                         "termination": (hts or {}).get("termination"), "net_m2": q.get("net_m2"), "state": q["state"],
                         "material_authority": p.get("material_authority"),
                         "rule": "half band (one face) x masonry height; bands exclude openings and RC"})
    over = []
    host_cls = {}
    for p in pieces:
        host_cls[p["piece_id"]] = p
    for o in ops:
        hw = o.get("host_wall")
        if not hw or hw["class"] not in AQ.MASONRY_CLASSES or o["width"]["m"] is None:
            continue
        p = host_cls[hw["piece"]]
        hs = H.along(o["floor"], p["centre_a"], p["centre_b"])
        hb = next(((h or {}).get("BLOCKWORK") for _, h in hs if (h or {}).get("BLOCKWORK", {}).get("height_m")), None)
        if hb is None or o["height"]["m"] is None:
            over.append({"opening": o["id"], "floor": o["floor"], "class": hw["class"], "net_m2": None, "state": AQ.BLK,
                         "why": "opening height or wall height not established"})
            continue
        lint = o.get("lintel_depth_m") or 0.0
        sill = (o.get("sill_m") or 0.0) if o["type"] == "WINDOW" else 0.0
        m = AQ.masonry_around_opening(width_m=o["width"]["m"], wall_h_m=hb["height_m"], opening_h_m=o["height"]["m"],
                                      lintel_m=lint, sill_m=sill)
        over.append({"opening": o["id"], "floor": o["floor"], "class": hw["class"], "width_m": o["width"]["m"],
                     "wall_height_m": hb["height_m"], "opening_height_m": o["height"]["m"], "lintel_m": lint,
                     "sill_m": sill, "above_m2": m["above_m2"], "below_m2": m["below_m2"], "net_m2": m["total_m2"],
                     "state": AQ.weakest(AQ.PROV, o["height"]["state"]),
                     "rule": "width x (wall height - opening height - lintel): above the head + below the sill"})
    return rows, over


# ============================================================================================ finishes
FLOOR_FINISH = {"DRY": ("DRY_PORCELAIN_TILE", "PORCELAIN (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1)", AQ.PROV),
                "WET": ("WET_CERAMIC", "TILE BY_SPEC (URBAN-WET-FLOOR-TILED@v1)", AQ.PROV),
                "SERVICE": ("WET_CERAMIC", "TILE BY_SPEC (URBAN-WET-FLOOR-TILED@v1)", AQ.PROV),
                "STAIR": ("MARBLE_STAIR_FINISH", "BY_SPEC (stair finish not in source)", AQ.BLK),
                "EXTERNAL": ("EXTERNAL_FINISH", "BY_SPEC", AQ.BLK)}
UNKNOWN_FINISH = ("UNKNOWN_MATERIAL_MEASURABLE", "BY_SPEC (semantic class not established)", AQ.BLK)
NO_FLOOR = ("VOID", "SHAFT")


def _area_state(r):
    if r["host_kind"] == "RECOVERED" or r["split_face"] or r["class"] == "UNASSIGNED":
        return AQ.PROV
    return AQ.VC


def _void_above(ctx, Fs, r):
    up = UP.get(r["floor"])
    if not up:
        return 0.0
    gb, ub = ctx["sheets_by_floor"][r["floor"]]["bounds"], ctx["sheets_by_floor"][up]["bounds"]
    dx, dy = gb[0] - ub[0], gb[1] - ub[1]
    tot = 0.0
    for v in Fs[up].voids:
        if v.get("_polygon"):
            vp = Polygon([(x + dx, y + dy) for x, y in v["_polygon"]]).buffer(0)
            tot += _m2(r["_poly"].intersection(vp).area)
    return tot


def _skirt_kind(e, F, ops_fl, voids):
    k = e["kind"]
    if e.get("a") is None:
        return k
    mid = Point((e["a"][0] + e["b"][0]) / 2, (e["a"][1] + e["b"][1]) / 2)
    if voids and any(v.exterior.distance(mid) <= 40.0 for v in voids):
        return "VOID_EDGE"
    if k == "GLAZING":
        o = min(((LineString(o["geometry"]).distance(mid), o) for o in ops_fl if o["geometry"]), default=(1e9, None),
                key=lambda z: z[0])
        if o[1] is not None and o[0] <= 400.0:
            t = o[1]["type"]
            return {"WINDOW": "WINDOW", "GLAZED_DOOR_CANDIDATE": "GLAZING_UNKNOWN"}.get(t, "DOOR")
        return "GLAZING_UNKNOWN"
    return {"WALL": "WALL", "COLUMN": "COLUMN", "DOOR": "DOOR", "OPEN_PASSAGE": "OPEN_PASSAGE",
            "ZONE_SPLIT": "ZONE_SPLIT", "EXTERNAL_EDGE": "EXTERNAL_EDGE", "DRAFTING_JOIN": "DRAFTING_JOIN"}.get(k, "UNKNOWN_EDGE")


def assign_edges(Fs, regions, hosts_poly):
    """Wall faces and path edges are taken ONCE from the physical-space (host) boundary and each piece is given to the
    trade region holding a point 150 mm inside it - a sliver region never re-counts its neighbour's wall face. Region
    boundary not on the host boundary is a ZONE_SPLIT (or VOID_EDGE) edge of that region."""
    by_host = defaultdict(list)
    for r in regions:
        by_host[r["host"]].append(r)
    out = defaultdict(list)
    for host, rs in by_host.items():
        fl = rs[0]["floor"]
        F = Fs[fl]
        hp = hosts_poly[host]
        for e in edge_kinds(F, hp):
            (ux, uy), Lm = _unit(e["a"], e["b"]) if math.dist(e["a"], e["b"]) > 1e-6 else ((1.0, 0.0), 0.0)
            mx, my = (e["a"][0] + e["b"][0]) / 2, (e["a"][1] + e["b"][1]) / 2
            pts = [Point(mx - uy * 150.0, my + ux * 150.0), Point(mx + uy * 150.0, my - ux * 150.0)]
            inner = [q for q in pts if hp.contains(q)] or pts
            tgt = None
            for q in inner:
                tgt = next((r for r in rs if r["_poly"].buffer(1.0).contains(q)), None)
                if tgt:
                    break
            if tgt is None:
                tgt = min(rs, key=lambda r: r["_poly"].distance(inner[0]))
            out[tgt["region_id"]].append(e)
        if len(rs) > 1:
            hb = hp.boundary.buffer(30.0)
            voids = [Polygon(v["_polygon"]).buffer(0) for v in F.voids if v.get("_polygon")]
            vb = unary_union([v.boundary for v in voids]).buffer(40.0) if voids else None
            for r in rs:
                rest = r["_poly"].boundary.difference(hb)
                if rest.is_empty or rest.length < 1.0:
                    continue
                if vb is not None:
                    v_part = rest.intersection(vb)
                    if v_part.length > 1.0:
                        out[r["region_id"]].append({"kind": "VOID_EDGE", "length_m": v_part.length * F.u / 1000.0,
                                                    "a": None, "b": None})
                        rest = rest.difference(vb)
                if rest.length > 1.0:
                    out[r["region_id"]].append({"kind": "ZONE_SPLIT", "length_m": rest.length * F.u / 1000.0,
                                                "a": None, "b": None})
    return out


def finishes(ctx, Fs, regions, ops, H, hosts_poly):
    out = {k: [] for k in ("floor", "ceiling", "skirting", "wp", "tile", "plaster_paint", "faces", "sensitivity")}
    region_edges = assign_edges(Fs, regions, hosts_poly)
    ops_by_reg = defaultdict(list)
    for o in ops:
        for a in o["room_adjacency"]:
            ops_by_reg[a].append(o)
    for r in regions:
        fl, F, cls = r["floor"], Fs[r["floor"]], r["class"]
        poly = r["_poly"]
        area = _m2(poly.area)
        ast = _area_state(r)
        voids = [Polygon(v["_polygon"]).buffer(0) for v in F.voids if v.get("_polygon")]
        prov = {"drawing": "P7757.dxf", "revision": F.inp.revision.revision_id, "floor": fl, "region": r["region_id"],
                "host": r["host"], "semantic_authority": r["semantic_authority"],
                "geometry_method": ("ROUTE_A_SITE" if r["host_kind"] == "ROUTE_A_SITE" else "ROUTE_B_RECOVERED") +
                                   (" / SPLIT_BY_ROUTE_B_FACE" if r["split_face"] else "")}
        # ---------------- floor
        if cls in NO_FLOOR:
            out["floor"].append(dict(prov, cls=cls, internal=False, raw_area_m2=_r(area), net_area_m2=0.0,
                                     finish_class="NONE", state=AQ.NIS, why=f"{cls}: no floor finish"))
        else:
            fc_ = FLOOR_FINISH.get(cls, UNKNOWN_FINISH)
            internal = r["indoor"] and cls != "EXTERNAL"
            out["floor"].append(dict(prov, cls=cls, internal=internal, raw_area_m2=_r(area), excluded_m2=0.0,
                                     net_area_m2=_r(area), finish_class=fc_[0], material=fc_[1],
                                     material_state=fc_[2], state=ast,
                                     rule="quantity released independently of material (OD-V3-2)"))
        if cls in NO_FLOOR or cls == "EXTERNAL" or not r["indoor"]:
            out["ceiling"].append(dict(prov, cls=cls, area_m2=0.0, state=AQ.NIS,
                                       why=f"{cls if cls in NO_FLOOR + ('EXTERNAL',) else 'external'}: no ceiling plane"))
            continue
        # ---------------- ceiling
        dh = _void_above(ctx, Fs, r)
        if cls == "STAIR":
            out["ceiling"].append(dict(prov, cls=cls, area_m2=None, state=AQ.BLK,
                                       why="stair well: ceiling / soffit scope of the stair hall not established"))
        else:
            c = AQ.ceiling_area(area_m2=area, region_class=cls, covered_state=ast, double_height_m2=dh)
            out["ceiling"].append(dict(prov, cls=cls, **c, material="BY_SPEC (URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1)"))
        # ---------------- edges and faces (host boundary, assigned once)
        edges = region_edges.get(r["region_id"], [])
        ops_r = ops_by_reg.get(r["region_id"], [])
        wet = cls in ("WET", "SERVICE")
        ctrl = H.room_ctrl(fl, poly)
        face_rows = []
        for i, e in enumerate(edges):
            if e["kind"] not in ("WALL", "COLUMN") or e["a"] is None:
                continue
            ln = LineString([e["a"], e["b"]])
            for k, (Ln, hts) in enumerate(H.along(fl, e["a"], e["b"], wet=wet, room_ctrl=ctrl)):
                Lm = e["length_m"] * (Ln / max(ln.length, 1e-9))
                g = lambda q: ((hts or {}).get(q) or {}).get("height_m")
                face_rows.append({"region": r["region_id"], "floor": fl, "edge": i, "sub": k, "kind": e["kind"],
                                  "length_m": Lm, "plaster_h": g("PLASTER"), "paint_h": g("PAINT"),
                                  "tile_h": g("WALL_TILE") if wet else None,
                                  "termination": (hts or {}).get("termination"),
                                  "interval_m": (hts or {}).get("interval_m"), "D_cm": (hts or {}).get("_D_cm"),
                                  "height_m": g("PLASTER")})
        face_m = sum(f["length_m"] for f in face_rows)
        # ---------------- skirting
        sk_edges = [{"edge_id": f"{r['region_id']}#{i}", "kind": _skirt_kind(e, F, [o for o in ops if o["floor"] == fl],
                                                                            voids), "length_m": e["length_m"]}
                    for i, e in enumerate(edges)]
        dry = cls == "DRY"
        sk = AQ.skirting_path(sk_edges, region_wet_full_tile=wet, region_dry=dry)
        if not dry and not wet:
            sk["state"] = AQ.BLK
        out["skirting"].append(dict(prov, cls=cls, **{k: v for k, v in sk.items() if k != "segments"},
                                    segments=[{k2: (round(v2, 6) if isinstance(v2, float) else v2) for k2, v2 in s.items()}
                                              for s in sk["segments"]],
                                    rule="hidden skirting and hidden profile share this path; doors excluded; windows "
                                         "continuous below the sill; wet full-tile rooms none"))
        # ---------------- waterproofing
        if wet:
            elig = AQ.VC if cls == "WET" else AQ.PROV
            wp = AQ.waterproofing(floor_m2=area, edges=[{"kind": s["kind"], "length_m": s["length_m"]} for s in sk_edges],
                                  upturn_m=UPTURN_M, wet_state=elig, area_state=ast)
            out["wp"].append(dict(prov, cls=cls, eligibility=elig, **wp))
        # ---------------- wall tile / plaster / paint
        opr = [{"id": o["id"], "width_m": o["width"]["m"], "width_state": o["width"]["state"],
                "height_m": o["height"]["m"], "height_state": o["height"]["state"]} for o in ops_r]
        if wet:
            tile_known = [f for f in face_rows if f["tile_h"] is not None]
            hmean = (sum(f["length_m"] * f["tile_h"] for f in tile_known) / sum(f["length_m"] for f in tile_known)) \
                if tile_known else None
            fm = sum(f["length_m"] for f in tile_known)
            t = AQ.wall_tile(face_m=fm, height_m=hmean, height_state=AQ.PROV, openings=opr, reveal_depth_m=REVEAL_M,
                             wet_state=r["semantic_state"] if r["semantic_state"] != AQ.BLK else AQ.BLK)
            out["tile"].append(dict(prov, cls=cls, face_m_total=_r(face_m),
                                    face_m_height_blocked=_r(face_m - fm), **t,
                                    height_authority="URBAN-WET-WALL-TILE-FULL-HEIGHT@v1 to the finished ceiling "
                                                     "(interval - build-up fallback - soffit - 0.150)"))
            for f in face_rows:
                f["treatments"] = ["WALL_TILE_FULL", "SPATTER_TILE_PREP"]
        else:
            pl_known = [f for f in face_rows if f["plaster_h"] is not None]
            pa_known = [f for f in face_rows if f["paint_h"] is not None]
            hp = (sum(f["length_m"] * f["plaster_h"] for f in pl_known) / sum(f["length_m"] for f in pl_known)) \
                if pl_known else None
            hq = (sum(f["length_m"] * f["paint_h"] for f in pa_known) / sum(f["length_m"] for f in pa_known)) \
                if pa_known else None
            plaster_ok = cls in ("DRY", "STAIR", "UNKNOWN")
            paint_ok = cls == "DRY"
            pp = AQ.plaster_paint(face_m=sum(f["length_m"] for f in pl_known) if pl_known else face_m,
                                  plaster_h=hp if plaster_ok else None,
                                  plaster_state=(AQ.VC if cls == "DRY" else AQ.PROV) if plaster_ok else AQ.BLK,
                                  paint_h=hq if paint_ok else None, paint_state=AQ.PROV if paint_ok else AQ.BLK,
                                  openings=opr, reveal_depth_m=REVEAL_M)
            out["plaster_paint"].append(dict(prov, cls=cls, face_m_total=_r(face_m),
                                             plaster_eligibility="ELIGIBLE" if plaster_ok else "BLOCKED (semantic class)",
                                             paint_eligibility="ELIGIBLE" if paint_ok else "BLOCKED (semantic class)",
                                             plaster=pp["plaster"], paint=pp["paint"],
                                             plaster_height_authority="URBAN-PLASTER-TO-MASONRY-TERMINATION@v1 "
                                                                      "(interval - terminating member)",
                                             paint_height_authority="URBAN-PAINT-TO-FINISHED-CEILING@v1 + build-up "
                                                                    "URBAN_FALLBACK 0.10 m (OD-V3-1)"))
            for f in face_rows:
                f["treatments"] = (["PLASTER"] if plaster_ok else ["PLASTER_BLOCKED"]) + \
                                  (["PAINT"] if paint_ok else ["PAINT_BLOCKED"])
            if plaster_ok and pl_known:
                g = sum(f["length_m"] * f["plaster_h"] for f in pl_known)
                s_ceil = sum(f["length_m"] * (f["paint_h"] or f["plaster_h"]) for f in pl_known)
                out["sensitivity"].append({"region": r["region_id"], "floor": fl, "trade": "PLASTER",
                                           "source_supported_height_gross_m2": _r(g),
                                           "approved_urban_method_gross_m2": _r(g),
                                           "alternative_to_finished_ceiling_gross_m2": _r(s_ceil),
                                           "delta_m2": _r(g - s_ceil)})
            if paint_ok and pa_known:
                g = sum(f["length_m"] * f["paint_h"] for f in pa_known)
                soffit = sum(f["length_m"] * (f["paint_h"] + 0.150) for f in pa_known)
                out["sensitivity"].append({"region": r["region_id"], "floor": fl, "trade": "PAINT",
                                           "approved_urban_method_gross_m2": _r(g),
                                           "alternative_paint_to_structural_soffit_gross_m2": _r(soffit),
                                           "delta_m2": _r(soffit - g)})
        for f in face_rows:
            f["length_m"] = _r(f["length_m"])
            f["id"] = f"{f['region']}#{f['edge']}.{f['sub']}"
        out["faces"] += face_rows
    return out


# ============================================================================================ facade / stairs
def facade(ctx, Fs, ops):
    rows = []
    ivs = {iv["from"]: iv for iv in ctx["b2a"]["intervals"]}
    for fl, F in Fs.items():
        edges = edge_kinds(F, F.plate)
        by = defaultdict(float)
        for e in edges:
            by[e["kind"]] += e["length_m"]
        wall_m = by.get("WALL", 0.0) + by.get("COLUMN", 0.0)
        h = ivs.get(fl, {}).get("interval_m")
        ext_ops = [o for o in ops if o["floor"] == fl and "OUTSIDE_PLATE" in o["room_adjacency"]]
        ded = sum(o["area"]["area_m2"] for o in ext_ops if o["area"]["area_m2"] is not None)
        blocked = [o["id"] for o in ext_ops if o["area"]["area_m2"] is None]
        gross = wall_m * h if h else None
        rows.append({"floor": fl, "envelope_m_by_kind": {k: _r(v) for k, v in sorted(by.items())},
                     "external_wall_face_m": _r(wall_m), "storey_interval_m": h,
                     "gross_external_face_m2": _r(gross), "external_openings": len(ext_ops),
                     "opening_deduction_m2": _r(ded), "openings_not_deducted": blocked,
                     "net_external_face_m2": _r(gross - ded) if gross is not None else None,
                     "state": AQ.PROV if gross is not None else AQ.BLK,
                     "why": "envelope = the registered floor-plate outline; party walls on the plot boundary, plinth below "
                            "GF FFL, the finish system (Sigma / stone) and courtyard exposure are not established; opening "
                            "deduction only where the opening area is established",
                     "finish_system": "BLOCKED (no external finish schedule)"})
    par = ctx["v3"]["blockwork"].get("parapets") or []
    return {"floors": rows, "parapets": [dict(p, state=AQ.PROV) for p in (par if isinstance(par, list) else [par])]}


def stairs(ctx):
    st = ctx["b2a"]["stairs"]
    ki = st.get("known_inputs") or {}
    going = (ki.get("tread_going_m") or {}).get("value")
    rows = []
    for k, run in enumerate(ki.get("observed_tread_line_runs") or []):
        n = run["tread_lines"]
        rows.append({"floor": run["floor"], "run": k, "layer": run["layer"], "linetype": run["linetype"],
                     "tread_lines": n, "flight_width_m": run["width_m"], "tread_going_m": going,
                     "tread_finish_m2": _r(n * going * run["width_m"]) if going else None,
                     "riser_count_candidate": n + 1,
                     "state": AQ.PROV,
                     "why": "tread lines counted on the plan; going 0.30 (plan spacing + p.16 typical); the two "
                            "linetypes of one flight (cut / overhead) are the same flight - runs are NOT summed"})
    return {"runs": rows,
            "riser_height": {"state": AQ.BLK, "why": "total risers per storey not established from the plan alone"},
            "landings": {"state": AQ.BLK, "why": "landing outlines not separated from the stair hall region"},
            "handrail_m": {"state": AQ.BLK, "why": "no handrail / balustrade geometry on the plans"},
            "stair_skirting_m": {"state": AQ.BLK, "why": "stair-side wall path not separated"},
            "source": "STAIR_CONCRETE_V2 known inputs (architectural plan tread lines); p.16 structural typical not "
                      "used as architectural geometry"}


# ============================================================================================ source coverage
def source_coverage(ctx, Fs, pieces, orphans, ops, regions):
    by_parent = defaultdict(set)
    for p in pieces:
        by_parent[p["parent"]].add(p["class"])
    orph = {(o["floor"], o["occurrence"]): o["outcome"] for o in orphans}
    door_ins = {o["id"].split("-D-")[1].lstrip("I") for o in ops if "-D-" in o["id"]}
    wet_polys = defaultdict(list)
    for r in regions:
        if r["class"] in ("WET", "SERVICE"):
            wet_polys[r["floor"]].append(r["_poly"])
    rows, counts = [], defaultdict(Counter)
    NOT_REL_ROLES = {"ANNOTATION_GRAPHICS": "annotation graphics (dimension lines / arrows / marks)",
                     "SHEET_FRAME": "sheet frame", "FURNITURE": "furniture", "PRESENTATION_OVERHEAD":
                     "overhead presentation line"}
    for fl, F in Fs.items():
        roles = F.res["roles"]["roles"]
        label_text_inst = {}
        for l in F.labels:
            label_text_inst[l["occurrence"]] = l
        for p in F.inp.parts:
            sid = p.identity.key
            role = getattr(roles.get(sid), "role", None)
            key = f"{fl}|{sid}"
            if key in by_parent:
                cl = by_parent[key]
                if cl <= {"NOT_WALL"} and role == "SHEET_FRAME":
                    st, why = "NOT_RELEVANT", "sheet frame"
                elif cl & {"AMBIGUOUS_BLOCKED", "BLOCKED_MATERIAL"}:
                    st = "BLOCKED" if not (cl - {"AMBIGUOUS_BLOCKED", "BLOCKED_MATERIAL"}) else "CONSUMED_PARTIAL"
                    why = "wall ledger: " + ", ".join(sorted(cl))
                else:
                    st, why = "CONSUMED_COMPLETE", "wall ledger: " + ", ".join(sorted(cl))
            elif p.layer == DOOR_L:
                ins = p.lineage[-1].insert_handle if p.lineage else None
                st, why = ("CONSUMED_COMPLETE", "door symbol -> opening register") if ins in door_ins else \
                    ("CONSUMED_PARTIAL", "door-layer geometry not bound to an opening record")
            elif p.layer == FIX_L:
                ins = p.lineage[-1].insert_handle if p.lineage else None
                fx = next((f for f in F.fixtures if f["insert"] == ins), None)
                inwet = fx is not None and any(w.buffer(300.0).contains(Point(fx["x"], fx["y"])) for w in wet_polys[fl])
                st, why = ("CONSUMED_COMPLETE", "sanitary fixture corroborates a wet / service region") if inwet else \
                    ("CONSUMED_PARTIAL", "sanitary fixture not inside an established wet / service region")
            elif role == "STAIR_GEOMETRY":
                st, why = "CONSUMED_PARTIAL", "stair geometry -> stair register (tread lines counted)"
            elif role == "OPENING_SYMBOL":
                st, why = "CONSUMED_COMPLETE", "opening symbol -> opening evidence"
            elif p.layer == "LEVEL":
                st, why = "CONSUMED_PARTIAL", "level mark graphics (storey levels corroborated, not reconciled per mark)"
            elif role in NOT_REL_ROLES:
                st, why = "NOT_RELEVANT", NOT_REL_ROLES[role]
            else:
                st, why = "BLOCKED", f"physical role {role} not consumed by any quantity this round"
            counts[fl][st] += 1
            rows.append({"floor": fl, "object": sid, "kind": p.kind, "layer": p.layer, "role": role, "state": st,
                         "why": why})
        for t in F.inp.texts:
            sid = t.identity.key
            v = (t.value or "").strip()
            occ = (t.identity.instance_handles or ("",))[0]
            if occ in label_text_inst:
                o = orph.get((fl, occ))
                if o is None:
                    st, why = "CONSUMED_COMPLETE", "room label -> semantic zone"
                elif o == "RECOVERED_PHYSICAL_REGION" or o == "LABEL_BELONGS_TO_EXISTING_REGION":
                    st, why = "CONSUMED_COMPLETE", f"room label -> {o}"
                elif o == "NOT_IN_SCOPE_EXTERNAL":
                    st, why = "NOT_RELEVANT", "external label (court / roof / street)"
                else:
                    st, why = "BLOCKED", f"room label {o}"
            elif v.startswith("\\A1;") or re.fullmatch(r"\d{2,4}", v):
                st, why = "BLOCKED", "dimension value: dimension reconciliation not run this round"
            elif re.fullmatch(r"[+%\-]*[\dp.%]+", v.replace("%%p", "")):
                st, why = "CONSUMED_PARTIAL", "level value (storey levels corroborated)"
            else:
                st, why = "NOT_RELEVANT", "title / orientation / annotation text"
            counts[fl][st] += 1
            rows.append({"floor": fl, "object": sid, "kind": "TEXT", "layer": t.layer, "value": v[:40], "state": st,
                         "why": why})
    docs = [("P7757.dxf", "CONSUMED_PARTIAL", "all three floor regions consumed; dimension values not reconciled"),
            ("P7757.dwg", "CONSUMED_COMPLETE", "read through its DXF export (same model)"),
            ("P7757_Architectural.dwf", "NOT_RELEVANT", "presentation export of the same drawing"),
            ("P7757_Architectural_Plan_Pages_01-06.pdf p.1", "CONSUMED_COMPLETE",
             "area calculation sheet (GF 319.99, 1F 211.44 - 3.24 = 208.20, 2F 55.08 m2): Route C floor-plate check"),
            ("P7757_Architectural_Plan_Pages_01-06.pdf p.2-6", "CONSUMED_PARTIAL",
             "raster plans / elevation: visual cross-check only (the DXF is the measured source)"),
            ("P7757_Architectural_Plan_Pages_07-12.pdf", "CONSUMED_PARTIAL",
             "elevations / sections: opening heights through the V3b raster lane; storey heights 450 / 420"),
            ("ST7757.dxf / ST7757.pdf", "CONSUMED_PARTIAL",
             "floor plate outline, framing bands (wall terminations), column outlines - read only (reinforcement registers not touched)"),
            ("sanitary-7757.pdf", "BLOCKED",
             "vector sheet not registered to the architectural plan this round; the plan's own fixture blocks (TOI) "
             "are used as corroboration instead")]
    tot = Counter()
    for c in counts.values():
        tot.update(c)
    return {"SCHEMA": "URBAN_ALSENAN_ARCH_SOURCE_COVERAGE_R5",
            "states": ["CONSUMED_COMPLETE", "CONSUMED_PARTIAL", "BLOCKED", "SOURCE_CONFLICT", "NOT_RELEVANT"],
            "documents": [{"document": d, "state": s, "why": w} for d, s, w in docs],
            "counts_by_floor": {fl: dict(c) for fl, c in counts.items()}, "counts_total": dict(tot),
            "objects_total": len(rows), "unterminated": 0, "objects": rows}


# ============================================================================================ build
def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, float):
        return round(o, 6)
    if isinstance(o, (Polygon, MultiPolygon)):
        return None
    return o


def build(ctx, r2_rows):
    Fs = floors(ctx)
    ps = physical_spaces(ctx, Fs)
    recs = {fl: recover(F) for fl, F in Fs.items()}
    orph = orphan_labels(Fs, recs)
    zones, regions = trade_regions(ctx, Fs, recs)
    fc = floor_conservation(Fs, recs, regions)
    wet = wet_completeness(Fs, recs, regions, orph)
    shadow, shadow_sum = shadow_comparison(Fs)
    pieces, admitted = wall_ledger(ctx, Fs)
    chk, face_by, run = wall_summary(pieces, admitted)
    ops = openings(ctx, Fs, regions, pieces, r2_rows)
    H = Heights(ctx)
    bw, over = blockwork(ctx, Fs, pieces, ops, H)
    hosts_poly = {}
    for fl, F in Fs.items():
        for h in _hosts(F, recs[fl][0]):
            hosts_poly[h["host_id"]] = h["poly"]
    fin = finishes(ctx, Fs, regions, ops, H, hosts_poly)
    fac = facade(ctx, Fs, ops)
    st = stairs(ctx)
    cov = source_coverage(ctx, Fs, pieces, orph, ops, regions)
    return {"Fs": Fs, "ps": ps, "recs": recs, "orphans": orph, "zones": zones, "regions": regions, "fc": fc,
            "wet": wet, "shadow": shadow, "shadow_summary": shadow_sum, "pieces": pieces, "admitted": admitted,
            "ledger_check": chk, "face_by": face_by, "run": run, "ops": ops, "bw": bw, "over": over, "fin": fin,
            "facade": fac, "stairs": st, "coverage": cov}
