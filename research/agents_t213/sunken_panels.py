"""T-213: sunken wet-slab panels as structural elements (any villa).

A 'sunken slab' panel is a floor-slab panel lowered by a drop d under a wet room so that the wet-room build-up
(fill / bed, falls, waterproofing tray) finishes at the storey's FFL. This module turns the drawn panel (a hatch
region) into ONE physical element and derives, per trade, the quantity FORMULAS that the drop drives. It never invents
d: with d unprinted every d-driven quantity is HELD (value None, never 0) and carries its formula.

Physical model (one geometry per trade, ERS s.3):
- Region: the hatch's fill region = the union of its region loops. Islands inside it that hold an annotation
  (a bar label, a beam mark, a thickness tag) are where the hatch pattern stops for legibility: the slab continues
  under them, so they are NOT deducted. An island with no annotation is an UNEXPLAINED void: reported, never silently
  deducted or ignored (the panel area is then HELD between the two readings).
- Concrete: the slab volume is A x t with t the thickness printed for that panel (tag or general note). A printed t
  for the sunken panel means the panel is not thinned: the whole slab is lowered (soffit lower by d), so the volume
  does not depend on d.
- Edges: every boundary edge is classified by what lies across the bounding beam (probe up to `max_beam_m`):
  SHARED (another sunken panel: whether a step exists there depends on the beam-top level, CONDITIONAL) or EXTERNAL
  (normal slab, exterior or anything not sunken: a step of height d exists on the panel side).
- Step on an EXTERNAL edge with the beam top at the normal slab top: a riser face of height d above the sunken slab
  top (top-side form) and a beam side face below the soffit shorter by d. Net formed area = 0 by geometry; the two
  pieces are separate BOQ items (edge / riser form vs beam side form) and both are HELD on d.
- Lane A / ceilings (listed once here, owned elsewhere): fill / build-up = A x d (lane A nets wall footprints and
  splits bed / fill); waterproofing tray = A floor + P_ext x d upturn on the step faces (lane A); ceiling below:
  area unchanged, level lower by d (CEILINGS).

No drawing data is stored here: geometry is passed in by the caller (a private reader or a synthetic fixture).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

__all__ = ["PanelError", "Panel", "build_panel", "classify_edges", "panel_quantities", "match_sets",
           "floor_carried", "beam_projection_check"]

AREA_EPS = 1e-6
STOREYS = ["B", "GF", "1F", "2F", "3F", "4F"]


class PanelError(ValueError):
    pass


@dataclass
class Panel:
    pid: str
    sheet_storey: str            # storey whose SLAB sheet draws the panel (the slab over that storey)
    polygon: Polygon             # physical panel (region loops united, annotation islands not deducted)
    annotation_islands: list = field(default_factory=list)   # [(area, label)]
    unexplained_voids: list = field(default_factory=list)    # [area]
    region_loops: int = 1

    @property
    def area(self) -> float:
        return self.polygon.area

    @property
    def perimeter(self) -> float:
        return self.polygon.exterior.length

    @property
    def area_status(self) -> str:
        return "HELD" if self.unexplained_voids else "DRAWING-CONFIRMED"


def floor_carried(sheet_storey: str) -> str:
    """The slab drawn on the slab sheet of storey X is the floor of the storey above (GF slab sheet -> 1F floor)."""
    if sheet_storey not in STOREYS[:-1]:
        raise PanelError(f"unknown storey {sheet_storey!r}")
    return STOREYS[STOREYS.index(sheet_storey) + 1]


def _poly(pts) -> Polygon:
    p = Polygon(pts)
    if not p.is_valid:
        p = p.buffer(0)
    if p.is_empty or p.area <= AREA_EPS:
        raise PanelError("degenerate loop")
    return p


def _ann_geom(a):
    """(x, y, label) = an anchor point; (x0, y0, x1, y1, label) = the annotation's drawn extent."""
    if len(a) == 3:
        return Point(a[0], a[1]), a[2]
    return box(a[0], a[1], a[2], a[3]), a[4]


def build_panel(pid, sheet_storey, loops, annotations=(), anchor_tol=0.02):
    """loops: list of point lists (metres) of ONE hatch. annotations: [(x, y, label)] anchor points or
    [(x0, y0, x1, y1, label)] drawn extents of texts / tags (an island is an annotation island when it holds one).

    The largest loop seeds the region; a loop that only touches the region (no shared area) is another region part
    (a hatch split by an annotation arc or a drawing line); a loop that overlaps the region is an island."""
    if not loops:
        raise PanelError(f"{pid}: no boundary loop")
    polys = sorted((_poly(lp) for lp in loops), key=lambda p: -p.area)
    region, islands = [polys[0]], []
    pending = polys[1:]
    changed = True
    while changed:              # touching parts may chain (a part touching a part)
        changed = False
        for p in list(pending):
            u = unary_union(region)
            if u.intersection(p).area <= AREA_EPS and u.distance(p) <= anchor_tol:
                region.append(p)
                pending.remove(p)
                changed = True
    u = unary_union(region)
    for p in pending:
        if u.intersection(p).area <= AREA_EPS:
            raise PanelError(f"{pid}: a loop lies apart from the panel region (two panels in one hatch?)")
        islands.append(p)
    ann, voids = [], []
    for isl in islands:
        zone = isl.buffer(anchor_tol)
        hit = [lab for g, lab in map(_ann_geom, annotations)
               if (zone.contains(g) if g.geom_type == "Point" else zone.intersection(g).area > 0.25 * min(g.area, isl.area))]
        if hit:
            ann.append((round(isl.area, 4), hit[0]))
        else:
            voids.append(round(isl.intersection(u).area, 4))
    if u.geom_type != "Polygon":
        raise PanelError(f"{pid}: region parts do not form one panel")
    return Panel(pid, sheet_storey, Polygon(u.exterior), ann, voids, len(region))


def classify_edges(panels, max_beam_m=1.0, probe_step_m=0.025, piece_m=0.05):
    """{pid: {'P_ext': m, 'P_shared': m, 'shared_with': {pid: m}, 'gap_m': {pid: m}}}. A boundary piece is SHARED
    when the outward probe from its midpoint meets another sunken panel within max_beam_m (across one beam: set it to
    the widest scheduled beam), else EXTERNAL. gap_m = the largest probe distance found (= that beam's width)."""
    out = {}
    for p in panels:
        ring = p.polygon.exterior
        ccw = ring.is_ccw
        cs = list(ring.coords)
        ext = 0.0
        shared: dict = {}
        gap: dict = {}
        pieces = []
        for a, b in zip(cs, cs[1:]):             # split every edge into pieces <= piece_m so that a beam facing only
            ln = LineString([a, b]).length       # part of an edge is attributed to that part only
            n = max(1, math.ceil(ln / piece_m - 1e-9))
            for i in range(n):
                pieces.append(((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n),
                               (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)))
        for a, b in pieces:
            ln = LineString([a, b]).length
            if ln <= 1e-9:
                continue
            dx, dy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
            nx, ny = (dy, -dx) if ccw else (-dy, dx)        # outward normal
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            hit = None
            k = 1
            while k * probe_step_m <= max_beam_m + 1e-9 and hit is None:
                q = Point(mx + nx * k * probe_step_m, my + ny * k * probe_step_m)
                for o in panels:
                    if o.pid != p.pid and o.polygon.buffer(1e-6).contains(q):
                        hit = o.pid
                        gap[hit] = max(gap.get(hit, 0.0), round(k * probe_step_m, 3))
                        break
                k += 1
            if hit is None:
                ext += ln
            else:
                shared[hit] = shared.get(hit, 0.0) + ln
        out[p.pid] = {"P_ext": ext, "P_shared": sum(shared.values()), "shared_with": shared, "gap_m": gap}
    return out


def _held(formula, missing):
    return {"value": None, "status": "HELD", "formula": formula, "missing": missing}


def _val(v, formula, status):
    return {"value": round(v, 4), "status": status, "formula": formula, "missing": []}


def panel_quantities(panel, edges, t_m=None, t_source=None, d_m=None, d_source=None, edges_on_beams=None):
    """Per-trade quantities of one panel. t_m: slab thickness PRINTED for this panel (tag or general note), with its
    source; d_m: the drop, only when printed (d_source required). Anything unprinted stays HELD (None, never 0)."""
    if d_m is not None and not d_source:
        raise PanelError(f"{panel.pid}: a drop without a printed source is an assumption (refused)")
    if t_m is not None and not t_source:
        raise PanelError(f"{panel.pid}: a thickness without a printed source is an assumption (refused)")
    if d_m is not None and d_m <= 0:
        raise PanelError(f"{panel.pid}: drop must be positive (a missing drop is None, never 0)")
    A, P_ext, P_sh = panel.area, edges["P_ext"], edges["P_shared"]
    a_st = panel.area_status
    q = {}
    if t_m is None:
        q["slab_concrete_m3"] = _held("A x t", ["slab thickness t"])
    else:
        q["slab_concrete_m3"] = _val(A * t_m, f"A x t = {A:.4f} x {t_m}", a_st)
        q["slab_concrete_m3"]["basis"] = "panel lowered at full thickness (t printed for the panel); volume independent of d"
    q["soffit_form_m2"] = _val(A, "A (area unchanged; soffit lower by d)", a_st)
    # Step concrete: where every edge is a beam / column face (edges_on_beams = its drawing basis), the step is the
    # side of a beam whose top carries the normal slab: no slab concrete is added, for any d. Where an edge is not on
    # a beam, the step is a vertical slab piece P_ext x d x t, HELD on d (and on t).
    if edges_on_beams:
        q["step_concrete_extra_m3"] = _val(0.0, "step = side of the bounding beams (h unchanged)", "DRAWING-CONFIRMED")
        q["step_concrete_extra_m3"]["basis"] = edges_on_beams
    elif d_m is None or t_m is None:
        q["step_concrete_extra_m3"] = _held(f"P_ext x d x t = {P_ext:.4f} x d x t",
                                            (["drop d"] if d_m is None else []) + (["slab thickness t"] if t_m is None
                                                                                  else []) + ["edge support"])
    else:
        q["step_concrete_extra_m3"] = _val(P_ext * d_m * t_m, f"P_ext x d x t = {P_ext:.4f} x {d_m} x {t_m}", "HELD")
        q["step_concrete_extra_m3"]["missing"] = ["edge support"]
    if d_m is None:
        miss = ["drop d"]
        q["step_riser_form_m2"] = _held(f"P_ext x d = {P_ext:.4f} x d", miss)
        q["beam_side_form_adjust_m2"] = _held(f"-(P_ext x d) = -{P_ext:.4f} x d", miss)
        q["shared_edge_riser_m2"] = _held(f"P_shared x d = {P_sh:.4f} x d (only if the shared beam top stays at the "
                                          "normal slab top)", miss + ["shared beam top level"])
        q["fill_buildup_m3_laneA"] = _held(f"A x d = {A:.4f} x d (gross; lane A nets wall footprints, splits bed / fill)",
                                           miss)
        q["waterproof_upturn_m2_laneA"] = _held(f"P_ext x d = {P_ext:.4f} x d", miss)
        q["ceiling_below_level_drop_m"] = _held("d", miss)
    else:
        st = "DRAWING-CONFIRMED" if a_st == "DRAWING-CONFIRMED" else "HELD"
        q["step_riser_form_m2"] = _val(P_ext * d_m, f"P_ext x d = {P_ext:.4f} x {d_m}", st)
        q["beam_side_form_adjust_m2"] = _val(-P_ext * d_m, f"-(P_ext x d) = -{P_ext:.4f} x {d_m}", st)
        q["shared_edge_riser_m2"] = _held(f"P_shared x d = {P_sh:.4f} x {d_m}", ["shared beam top level"]) if P_sh > 0 \
            else _val(0.0, "no shared edge", st)
        q["fill_buildup_m3_laneA"] = _val(A * d_m, f"A x d = {A:.4f} x {d_m} (gross)", st)
        q["waterproof_upturn_m2_laneA"] = _val(P_ext * d_m, f"P_ext x d = {P_ext:.4f} x {d_m}", st)
        q["ceiling_below_level_drop_m"] = _val(d_m, "d", "DRAWING-CONFIRMED")
        q["drop_source"] = d_source
    q["net_formwork_change_m2"] = _val(0.0, "riser (+P_ext x d) + beam side (-P_ext x d) = 0 by geometry, any d",
                                       "DRAWING-CONFIRMED")
    return q


def beam_projection_check(h_m, t_m, d_m):
    """A beam whose top stays at the normal slab top still projects below the sunken soffit only if h - t - d > 0."""
    if d_m is None:
        return {"status": "HELD", "projection_m": None, "missing": ["drop d"]}
    proj = h_m - t_m - d_m
    return {"status": "OK" if proj > 0 else "BEAM DEPTH CONFLICT", "projection_m": round(proj, 4), "missing": []}


def match_sets(set_a, set_b, rel_tol=0.005, abs_tol=0.02):
    """Two registers of the same panels under different naming / storey conventions: one-to-one by area.
    set_*: {id: area}. Returns (pairs [(a, b, area_a, area_b, residual b-a)], unmatched_a, unmatched_b)."""
    pairs, ua, ub = [], dict(set_a), dict(set_b)
    for a, aa in sorted(set_a.items(), key=lambda kv: -kv[1]):
        best = None
        for b, ab in ub.items():
            r = abs(ab - aa)
            if r <= max(abs_tol, rel_tol * aa) and (best is None or r < best[1]):
                best = (b, r)
        if best:
            b = best[0]
            pairs.append((a, b, aa, ub[b], round(ub[b] - aa, 4)))
            del ub[b]
            del ua[a]
    return pairs, sorted(ua), sorted(ub)
