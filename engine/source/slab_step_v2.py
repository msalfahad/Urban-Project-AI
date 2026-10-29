"""SLAB_STEP_V2 (T-224): the step at the edge of a SUNKEN slab panel, from the drawn panel outline and its framing
members (any villa). A NEW method version beside the opt-in M8 bound SLAB_STEP of SCOPE_QUANTITIES_V1
(engine/source/scope_quantities.py, `_bound_of`, convention SLAB_STEP_DROP_M), which stays as it is (FROZEN) and stays
selectable here, flagged, for a sunken outline with no drawn outline and no framing evidence (`legacy_bound`).

NOT wired into any method version (ARCH_TAKEOFF_V2.9 + route G and every V3.0.x candidate are unchanged); a later
Gate B integration package wires it. Standard library only (K1: no shapely / ezdxf); it imports no engine module.

Why a new version (T-213, MERGED 0ec8c496): the V1 bound 0 .. 4 sqrt(A) x drop_high x t is wrong twice for a panel
framed by beams: (a) the step concrete there is 0 by geometry and (b) 4 sqrt(A) is a square-equivalent perimeter, not
the drawn one (Alsenan: 47.69 m summed over six panels vs the drawn step perimeter P_ext 41.451 m).

Physical element (ENGINEERING_REASONING_STANDARD s.2 - s.3). A sunken panel is a floor-slab panel lowered by a drop d
(top AND soffit lower by d) at its full printed thickness t, so the panel's own slab volume A x t, its soffit form A and
its meshes do not depend on d (T-213 s.4: a thickness printed for the panel rules out the thinned-slab reading). What
the drop creates depends on what lies along each piece of the outline (classified per piece, never per whole edge):

  EXTERNAL_MEMBER   a beam or column face with normal slab (or the outside) across the member. The member top stays at
                    the normal slab top (it carries that slab), so the step IS the member's side face:
                      step concrete            0 m3 for any d (DRAWING-CONFIRMED by geometry)
                      riser form (top side)    + L x d   (member face between the sunken top and the normal top)
                      member-side form below   - L x d   (the member face under the slab is shorter by d)
                    Net formed area 0 for any d; the two terms are different BOQ items and both stay HELD on d.
  SHARED_MEMBER     a beam with ANOTHER sunken panel across it. Whether a step exists depends on the beam-top level
                    (it may drop with both panels): riser + L x d / member side - L x d, both HELD on d AND on the beam
                    top level (never resolved by preference).
  FREE_SLAB_EDGE    no framing member: the normal slab continues across a step in the slab itself. The two faces exist
                    in every reading of the step:
                      riser form (top side)    + L x d   (stop-end above the sunken top)
                      soffit step form         + L x d   (vertical face, normal soffit down to the sunken soffit)
                    The ADDED step concrete (beyond the two slabs' own A x t) is NOT a geometric fact (T-224 r2,
                    Checker 2026-10-28 23:01): with d < t the two slabs abut and share t - d of face (no added
                    concrete in that reading); with d > t they do not meet and a web is needed whose width / height /
                    haunch only a drawn cranked-step section gives. So it is taken ONLY from a printed StepDetail:
                      web printed (b_w, h)     L x h x b_w   (h printed, or printed as the drop: L x d x b_w)
                      abutting, no web printed 0 m3          (refused when d > t: the slabs would not meet)
                      no detail                HELD with its formula (never L x d x t by convention, never 0)
  PERIMETER_MEMBER  a beam with the OUTSIDE of the storey slab across it (an edge beam carrying only the sunken
                    panel): its top may be at the normal slab top or dropped with the panel; riser + L x d / member side
                    - L x d HELD on d AND on that beam-top level (unprinted), like SHARED_MEMBER.
  ADJACENT_SUNKEN   another sunken panel across with no member between: a step only if the two drops differ; HELD on
                    the relative drop (never 0, never assumed equal).
  PERIMETER_EDGE    outside the storey slab extent across the edge (no member): the panel edge is the slab's own edge;
                    no step item (its edge form is the slab edge's, owned by the edge-form line, not this method).

With d unprinted (Alsenan: designer item D-41) every d-driven quantity is HELD (value None, never 0) and carries its
formula in metres; a drop or thickness without a printed source is an assumption and refused. Evidence statuses are
those of WORKFLOW_CONTROLS_2026-10-21 s.5.

Default-guard class (T-212 P1): UNWIRED_PRODUCER: it produces quantities and no released or candidate method imports it.

Guards (SlabStepError): a drop / thickness without a source; d <= 0 (a missing drop is None); values in millimetres
(t > 0.6 m, d > 1.5 m, a member width > 2.0 m, an outline larger than 400 m2 or a side above 60 m); a degenerate or
self-intersecting outline; two sunken panels overlapping; edge pieces that do not close the drawn perimeter; a drop
that leaves a bounding beam no projection below the sunken soffit (h - t - d <= 0: BEAM DEPTH CONFLICT, the beam
cannot be the step); the legacy square-equivalent bound requested for a panel whose outline is drawn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

METHOD = "SLAB_STEP_V2"
SUPERSEDES = "SCOPE_QUANTITIES_V1 SLAB_STEP bound (4 sqrt(A) x SLAB_STEP_DROP_M x t), opt-in M8; kept as legacy_bound"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"      # T-212 P1: unwired producer, no released / candidate importer
RULES = ("T-213 (MERGED 0ec8c496): panel lowered at full thickness, step = beam side on framed edges",
         "D-41 (designer item, open): drop d HELD, never defaulted",
         "WORKFLOW_CONTROLS_2026-10-21 s.5 statuses", "ENGINEERING_REASONING_STANDARD s.2 - s.4",
         "T-224 r2 (Checker 2026-10-28 23:01): free-edge step concrete from the drawn step detail, else HELD")

DC, AOA, VER, HELD, UNKNOWN = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "VERIFIED", "HELD", "UNKNOWN"
STATUSES = (VER, DC, AOA, HELD, UNKNOWN)
MEMBER_KINDS = ("BEAM", "COLUMN")
EDGE_KINDS = ("EXTERNAL_MEMBER", "SHARED_MEMBER", "PERIMETER_MEMBER", "FREE_SLAB_EDGE", "ADJACENT_SUNKEN",
              "PERIMETER_EDGE")
MAX_T_M, MAX_D_M, MAX_MEMBER_W_M, MAX_AREA_M2, MAX_SIDE_M = 0.6, 1.5, 2.0, 400.0, 60.0
MAX_WEB_W_M, MAX_WEB_H_M = 1.0, MAX_D_M + MAX_T_M      # a printed step web wider / taller than this: millimetres?
PROBE_M = 0.01          # first probe just outside the outline
PIECE_M = 0.05          # outline split into pieces <= this, so a member along part of a side owns that part only
TOUCH_M = 0.005         # a member face within this of the outline frames it
EPS = 1e-9

__all__ = ["METHOD", "SUPERSEDES", "DEFAULT_GUARD_CLASS", "RULES", "STATUSES", "EDGE_KINDS", "SlabStepError",
           "Member", "SunkenPanel", "StepDetail", "classify_outline", "step_quantities", "legacy_bound", "totals"]


class SlabStepError(ValueError):
    pass


def _num(v, what, cap, *, allow_none=False, positive=True):
    if v is None:
        if allow_none:
            return None
        raise SlabStepError(f"{what} is required")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
        raise SlabStepError(f"{what} must be a number, got {v!r}")
    if positive and v <= 0:
        raise SlabStepError(f"{what} must be positive (a missing value is None, never 0), got {v!r}")
    if v > cap:
        raise SlabStepError(f"{what} = {v!r} m is above {cap} m: millimetres passed as metres?")
    return float(v)


def _seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    u = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - u * dx, p[1] - ay - u * dy)


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) <= 1e-12 else (1 if v > 0 else -1)


def _cross_proper(a, b, c, d):
    """segments ab and cd cross at one interior point of both (no touching, no collinear overlap)."""
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


def _segs_meet(a, b, c, d):
    if _cross_proper(a, b, c, d):
        return True
    return min(_seg_dist(c, a, b), _seg_dist(d, a, b), _seg_dist(a, c, d), _seg_dist(b, c, d)) <= 1e-9


class _Ring:
    """A simple polygon (metres), standard library only: area, perimeter, orientation, point tests with a tolerance."""

    def __init__(self, pts, what):
        try:
            pts = [(float(x), float(y)) for x, y in pts]
        except (TypeError, ValueError) as e:
            raise SlabStepError(f"{what}: not a polygon ({e})") from e
        if len(pts) > 1 and math.dist(pts[0], pts[-1]) <= EPS:
            pts = pts[:-1]
        pts = [q for i, q in enumerate(pts) if math.dist(q, pts[i - 1]) > EPS] if len(pts) > 1 else pts
        if len(pts) < 3:
            raise SlabStepError(f"{what}: degenerate outline")
        self.pts = pts
        self.edges = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        n = len(self.edges)
        for i in range(n):
            for j in range(i + 1, n):
                if j == i + 1 or (i == 0 and j == n - 1):
                    continue                         # neighbours share a vertex
                if _segs_meet(*self.edges[i], *self.edges[j]):
                    raise SlabStepError(f"{what}: self-intersecting outline (never repaired silently)")
        sa = sum(a[0] * b[1] - b[0] * a[1] for a, b in self.edges) / 2.0
        if abs(sa) <= 1e-6:
            raise SlabStepError(f"{what}: degenerate outline")
        self.area, self.ccw = abs(sa), sa > 0
        self.length = sum(math.dist(a, b) for a, b in self.edges)

    def dist(self, p):
        return min(_seg_dist(p, a, b) for a, b in self.edges)

    def inside(self, p):
        x, y, c = p[0], p[1], False
        for a, b in self.edges:
            if (a[1] > y) != (b[1] > y) and x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                c = not c
        return c

    def covers(self, p, tol):
        """inside or within tol of the boundary (the outline grown by tol)."""
        return self.dist(p) <= tol or self.inside(p)

    def strictly(self, p, tol):
        """inside and more than tol from the boundary (the outline shrunk by tol)."""
        return self.inside(p) and self.dist(p) > tol

    def distance(self, other):
        if any(self.inside(q) for q in other.pts) or any(other.inside(q) for q in self.pts):
            return 0.0
        best = math.inf
        for a, b in self.edges:
            for c, d in other.edges:
                if _cross_proper(a, b, c, d):
                    return 0.0
                best = min(best, _seg_dist(c, a, b), _seg_dist(d, a, b), _seg_dist(a, c, d), _seg_dist(b, c, d))
        return best

    def overlaps(self, other, tol=1e-6):
        """the two outlines share area: a crossing, or a vertex / edge midpoint / the centroid of one strictly inside
        the other (touching along a side or at a corner is not an overlap)."""
        for a, b in self.edges:
            for c, d in other.edges:
                if _cross_proper(a, b, c, d):
                    return True

        def probes(r):
            mids = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in r.edges]
            cx = sum(q[0] for q in r.pts) / len(r.pts)
            cy = sum(q[1] for q in r.pts) / len(r.pts)
            return r.pts + mids + ([(cx, cy)] if r.inside((cx, cy)) else [])
        return any(other.strictly(q, tol) for q in probes(self)) or any(self.strictly(q, tol) for q in probes(other))


def _poly(pts, what):
    return _Ring(pts, what)


@dataclass
class Member:
    """A framing member's plan footprint (metres). h_m = its printed depth (schedule), None when unprinted."""
    mid: str
    kind: str
    footprint: list
    h_m: float | None = None
    h_source: str | None = None

    def __post_init__(self):
        if self.kind not in MEMBER_KINDS:
            raise SlabStepError(f"member {self.mid}: kind {self.kind!r} not in {MEMBER_KINDS}")
        self.poly = _poly(self.footprint, f"member {self.mid}")
        w = min(_side_lengths(self.poly))
        if w > MAX_MEMBER_W_M:
            raise SlabStepError(f"member {self.mid}: narrow side {w:.3f} m above {MAX_MEMBER_W_M} m: millimetres?")
        if self.h_m is not None:
            _num(self.h_m, f"member {self.mid} depth", 3.0)
            if not self.h_source:
                raise SlabStepError(f"member {self.mid}: a depth without a printed source is an assumption (refused)")


@dataclass
class SunkenPanel:
    """One sunken panel: its drawn outline (metres, from the hatch region / face polygon), its printed thickness and
    drop (each with its source, or None = not printed)."""
    pid: str
    outline: list
    t_m: float | None = None
    t_source: str | None = None
    d_m: float | None = None
    d_source: str | None = None
    notes: list = field(default_factory=list)

    def __post_init__(self):
        self.poly = _poly(self.outline, f"panel {self.pid}")
        if self.poly.area > MAX_AREA_M2 or max(_side_lengths(self.poly)) > MAX_SIDE_M:
            raise SlabStepError(f"panel {self.pid}: outline too large ({self.poly.area:.1f} m2): millimetres?")
        if self.t_m is not None:
            _num(self.t_m, f"panel {self.pid} thickness", MAX_T_M)
            if not self.t_source:
                raise SlabStepError(f"panel {self.pid}: a thickness without a printed source is an assumption "
                                    "(refused)")
        if self.d_m is not None:
            _num(self.d_m, f"panel {self.pid} drop", MAX_D_M)
            if not self.d_source:
                raise SlabStepError(f"panel {self.pid}: a drop without a printed source is a default (refused; "
                                    "HELD while D-41 is open)")
        elif self.d_source:
            raise SlabStepError(f"panel {self.pid}: a drop source without a drop")

    @property
    def area(self):
        return self.poly.area

    @property
    def perimeter(self):
        return self.poly.length


@dataclass
class StepDetail:
    """A PRINTED cranked-step section for the panel's free slab edges (T-224 r2). ref = the drawing / detail reference.
    Exactly one reading:
      web:      b_w_m (web width) with b_w_source, and its height either h_m with h_source or h_is_drop=True with
                h_source (the section prints the web over the drop height) -> added concrete L x h x b_w;
      abutting: no_web=True with no_web_source (the section prints the two slabs meeting with no web or haunch)
                -> added concrete 0 m3, refused when the drop exceeds the thickness (d > t: the slabs do not meet).
    Every value needs its printed source; a convention (b_w = t, h = d) without one is refused."""
    ref: str
    b_w_m: float | None = None
    b_w_source: str | None = None
    h_m: float | None = None
    h_source: str | None = None
    h_is_drop: bool = False
    no_web: bool = False
    no_web_source: str | None = None

    def __post_init__(self):
        if not self.ref:
            raise SlabStepError("step detail: a detail without a drawing reference is not a printed detail (refused)")
        web = self.b_w_m is not None or self.h_m is not None or self.h_is_drop
        if self.no_web and web:
            raise SlabStepError(f"step detail {self.ref}: 'no web' and a web are both given (one reading only)")
        if self.no_web:
            if not self.no_web_source:
                raise SlabStepError(f"step detail {self.ref}: 'no web' without a printed source is an assumption "
                                    "(refused)")
            return
        if not web:
            raise SlabStepError(f"step detail {self.ref}: neither a web nor 'no web' is given")
        _num(self.b_w_m, f"step detail {self.ref} web width", MAX_WEB_W_M)
        if not self.b_w_source:
            raise SlabStepError(f"step detail {self.ref}: a web width without a printed source is a convention "
                                "(refused; never b_w = t by default)")
        if self.h_is_drop and self.h_m is not None:
            raise SlabStepError(f"step detail {self.ref}: web height given both as a value and as the drop")
        if not self.h_is_drop:
            _num(self.h_m, f"step detail {self.ref} web height", MAX_WEB_H_M)
        if not self.h_source:
            raise SlabStepError(f"step detail {self.ref}: a web height without a printed source is a convention "
                                "(refused; never h = d by default)")


def _side_lengths(p):
    return [math.dist(a, b) for a, b in p.edges]


def _pieces(p):
    ccw = p.ccw
    for a, b in p.edges:
        ln = math.dist(a, b)
        if ln <= EPS:
            continue
        n = max(1, math.ceil(ln / PIECE_M - 1e-9))
        dx, dy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
        nx, ny = (dy, -dx) if ccw else (-dy, dx)            # outward normal
        for i in range(n):
            s, e = i / n, (i + 1) / n
            m = (a[0] + (b[0] - a[0]) * (s + e) / 2, a[1] + (b[1] - a[1]) * (s + e) / 2)
            yield ln / n, m, (nx, ny)


def classify_outline(panel, members, other_panels, slab_extent):
    """Split the panel's drawn outline by what lies across each piece. members: [Member] footprints (members away
    from the panel are ignored); other_panels: the other sunken panels of the same slab; slab_extent: the storey
    slab's outer outline (metres) or None when it is not drawn / not read: then a piece whose far side is neither a
    member nor another sunken panel is UNKNOWN (never guessed as normal slab or as the outside).
    Returns {kind: length_m, 'UNKNOWN': m, 'members': {mid: m}, 'shared_with': {pid: m}, 'P': m}."""
    ext = _poly(slab_extent, "slab extent") if slab_extent is not None else None
    others = [o for o in other_panels if o.pid != panel.pid]
    for o in others:
        if o.poly.overlaps(panel.poly):
            raise SlabStepError(f"panels {panel.pid} and {o.pid} overlap: one element counted twice")
    near = [m for m in members if m.poly.distance(panel.poly) <= TOUCH_M]
    out = {k: 0.0 for k in EDGE_KINDS}
    out.update({"UNKNOWN": 0.0, "members": {}, "shared_with": {}, "P": panel.perimeter})
    for ln, (mx, my), (nx, ny) in _pieces(panel.poly):
        q = (mx + nx * PROBE_M, my + ny * PROBE_M)
        hit = next((m for m in near if m.poly.covers(q, TOUCH_M)), None)
        if hit is not None:
            # walk across the member(s) to see what is on the far side
            k, far = 1, None
            while k * PROBE_M <= MAX_MEMBER_W_M + PROBE_M:
                r = (mx + nx * (PROBE_M + k * PROBE_M), my + ny * (PROBE_M + k * PROBE_M))
                if not any(m.poly.covers(r, TOUCH_M) for m in near):
                    far = r
                    break
                k += 1
            across = next((o for o in others if far is not None and o.poly.covers(far, TOUCH_M)), None)
            if across is not None:
                out["SHARED_MEMBER"] += ln
                out["shared_with"][across.pid] = out["shared_with"].get(across.pid, 0.0) + ln
            elif far is None or ext is None:
                out["UNKNOWN"] += ln
            elif ext.strictly(far, TOUCH_M):
                out["EXTERNAL_MEMBER"] += ln
            else:
                out["PERIMETER_MEMBER"] += ln
            out["members"][hit.mid] = out["members"].get(hit.mid, 0.0) + ln
            continue
        across = next((o for o in others if o.poly.covers(q, TOUCH_M)), None)
        if across is not None:
            out["ADJACENT_SUNKEN"] += ln
            out["shared_with"][across.pid] = out["shared_with"].get(across.pid, 0.0) + ln
        elif ext is None:
            out["UNKNOWN"] += ln
        elif ext.strictly(q, TOUCH_M):
            out["FREE_SLAB_EDGE"] += ln
        else:
            out["PERIMETER_EDGE"] += ln
    closure = sum(out[k] for k in EDGE_KINDS) + out["UNKNOWN"] - out["P"]
    if abs(closure) > 1e-6:
        raise SlabStepError(f"panel {panel.pid}: edge pieces do not close the perimeter (residual {closure:.6f} m)")
    out["near_members"] = [m.mid for m in near]
    return out


def _held(formula, missing):
    return {"value": None, "status": HELD, "formula": formula, "missing": list(missing)}


def _val(v, formula, status, missing=()):
    return {"value": round(v, 4), "status": status, "formula": formula, "missing": list(missing)}


def _area_status(edges):
    return DC if edges["UNKNOWN"] <= EPS else HELD


def _free_edge_concrete(F, d, t, detail, miss_d):
    """Added step concrete on the free slab edges (L_free = F > 0) from the printed step detail only (T-224 r2)."""
    readings = (f"d < t: slabs abut over t - d, no added concrete; d > t: a web whose width / height only a drawn "
                f"cranked-step section gives")
    if detail is None:
        return _held(f"L_free x h_web x b_w = {F:.4f} x h_web x b_w from the drawn step detail ({readings})",
                     ["printed step detail (web width, height) for %.4f m of free slab edge" % F])
    if not isinstance(detail, StepDetail):
        raise SlabStepError(f"step detail must be a StepDetail, got {type(detail).__name__}")
    if detail.no_web:
        if d is None or t is None:
            return _held(f"0 if d <= t (detail {detail.ref}: slabs abut, no web printed); d > t contradicts the "
                         "detail", miss_d + ([] if t is not None else ["slab thickness t"]))
        if d - t > EPS:
            raise SlabStepError(f"step detail {detail.ref}: 'no web' with d = {d:g} > t = {t:g}: the two slabs "
                                "do not meet (a web is needed: read the section again)")
        return _val(0.0, f"detail {detail.ref}: slabs abut, no web printed ({detail.no_web_source})", DC)
    if detail.h_is_drop:
        if d is None:
            return _held(f"L_free x d x b_w = {F:.4f} x d x {detail.b_w_m:g} (detail {detail.ref}: web over the "
                         "drop)", miss_d)
        return _val(F * d * detail.b_w_m, f"L_free x d x b_w = {F:.4f} x {d:g} x {detail.b_w_m:g} (detail "
                    f"{detail.ref}: web {detail.b_w_source}, height = drop {detail.h_source})", DC)
    return _val(F * detail.h_m * detail.b_w_m, f"L_free x h_web x b_w = {F:.4f} x {detail.h_m:g} x "
                f"{detail.b_w_m:g} (detail {detail.ref}: web {detail.b_w_source}, height {detail.h_source})", DC)


def step_quantities(panel, edges, members=(), step_detail=None):
    """The step quantities of one panel from its classified outline (classify_outline). Every d-driven value is HELD
    (None) while d is unprinted; nothing is ever 0 by default. The panel's own slab concrete (A x t) and soffit form
    (A) are reported for the record only (they belong to the slab line; independent of d). step_detail: the printed
    StepDetail for the panel's free slab edges, or None (then the free-edge step concrete is HELD, T-224 r2)."""
    A, d, t = panel.area, panel.d_m, panel.t_m
    E, S, F = edges["EXTERNAL_MEMBER"], edges["SHARED_MEMBER"] + edges["PERIMETER_MEMBER"], edges["FREE_SLAB_EDGE"]
    J, U = edges["ADJACENT_SUNKEN"], edges["UNKNOWN"]
    st = DC
    q = {"pid": panel.pid, "method": METHOD, "area_m2": round(A, 4), "perimeter_m": round(panel.perimeter, 4),
         "edges_m": {k: round(edges[k], 4) for k in EDGE_KINDS + ("UNKNOWN",)}}
    # record-only slab terms (owned by the slab line)
    q["panel_slab_concrete_m3_record"] = (_val(A * t, f"A x t = {A:.4f} x {t:g} (full-thickness drop; any d)", st)
                                          if t is not None else _held("A x t", ["slab thickness t"]))
    q["panel_soffit_form_m2_record"] = _val(A, "A (area unchanged; soffit lower by d)", st)
    # beam depth conflict: a bounding member must still project below the sunken soffit
    by_id = {m.mid: m for m in members}
    for mid in edges.get("members", {}):
        m = by_id.get(mid)
        if m is not None and m.kind == "BEAM" and m.h_m is not None and d is not None and t is not None:
            if m.h_m - t - d <= EPS:
                raise SlabStepError(f"panel {panel.pid}: beam {mid} depth {m.h_m} leaves no projection below the "
                                    f"sunken soffit (h - t - d = {m.h_m - t - d:.3f} m): BEAM DEPTH CONFLICT")
    miss_d = [] if d is not None else ["drop d (D-41)"]
    unknown = ["what lies across %.4f m of outline (slab extent not given)" % U] if U > EPS else []
    # step concrete: 0 on member-framed pieces for any d; on free slab edges ONLY from the printed step detail (r2)
    if step_detail is not None and F <= EPS:
        raise SlabStepError(f"panel {panel.pid}: a step detail is given but the outline has no free slab edge "
                            "(a detail is never applied to member-framed pieces)")
    if F <= EPS and J <= EPS and U <= EPS:
        q["step_concrete_m3"] = _val(0.0, f"every piece is a member face (P_ext {E:.4f} + P_shared / perimeter "
                                          f"{S:.4f} m): the "
                                          "step is the member side, no slab concrete for any d", DC)
    else:
        fc = (_free_edge_concrete(F, d, t, step_detail, miss_d) if F > EPS
              else _val(0.0, "no free slab edge", DC))
        others = unknown + (["relative drop over %.4f m of adjacent sunken edge" % J] if J > EPS else [])
        if others:
            q["step_concrete_m3"] = _held(f"{fc['formula']} (member pieces 0) + adjacent / unclassified pieces",
                                          fc["missing"] + others)
        elif fc["value"] is None:
            q["step_concrete_m3"] = _held(f"{fc['formula']} (member pieces 0)", fc["missing"])
        else:
            q["step_concrete_m3"] = _val(fc["value"], f"{fc['formula']} (member pieces 0)", DC)
    # formwork
    if d is None:
        q["riser_form_member_m2"] = _held(f"+ P_ext x d = + {E:.4f} x d", miss_d)
        q["member_side_form_adjust_m2"] = _held(f"- P_ext x d = - {E:.4f} x d", miss_d)
        q["riser_form_free_edge_m2"] = (_held(f"+ L_free x d = + {F:.4f} x d", miss_d) if F > EPS
                                        else _val(0.0, "no free slab edge", DC))
        q["soffit_step_form_free_edge_m2"] = (_held(f"+ L_free x d = + {F:.4f} x d", miss_d) if F > EPS
                                              else _val(0.0, "no free slab edge", DC))
    else:
        q["riser_form_member_m2"] = _val(E * d, f"+ P_ext x d = + {E:.4f} x {d:g}", st)
        q["member_side_form_adjust_m2"] = _val(-E * d, f"- P_ext x d = - {E:.4f} x {d:g}", st)
        q["riser_form_free_edge_m2"] = _val(F * d, f"+ L_free x d = + {F:.4f} x {d:g}", st)
        q["soffit_step_form_free_edge_m2"] = _val(F * d, f"+ L_free x d = + {F:.4f} x {d:g}", st)
    q["shared_member_riser_m2"] = (_held(f"+ P_shared x d = + {S:.4f} x d (only if the shared / perimeter beam top "
                                         "stays at the normal slab top)", miss_d + ["shared beam top level"]) if S > EPS
                                   else _val(0.0, "no shared member edge", DC))
    q["shared_member_side_adjust_m2"] = (_held(f"- P_shared x d = - {S:.4f} x d (same condition)",
                                               miss_d + ["shared beam top level"]) if S > EPS
                                         else _val(0.0, "no shared member edge", DC))
    q["adjacent_sunken_step"] = (_held(f"L_adj x |d - d_other| = {J:.4f} x |d - d_other|",
                                       ["relative drop of the adjacent sunken panel"]) if J > EPS
                                 else _val(0.0, "no adjacent sunken edge without a member", DC))
    q["unknown_edge"] = (_held(f"{U:.4f} m of outline with nothing classified across", ["slab extent"])
                         if U > EPS else _val(0.0, "every piece classified", DC))
    q["net_member_form_change_m2"] = _val(0.0, "riser (+P_ext x d) + member side (-P_ext x d) = 0 for any d", DC)
    q["area_status"] = _area_status(edges)
    return q


def legacy_bound(area_m2, drop_high_m, t_high_m, *, outline_drawn, framing_evidence):
    """The V1 bound of SCOPE_QUANTITIES_V1 (SLAB_STEP), kept selectable ONLY for a sunken finding with no drawn
    outline and no framing evidence: 0 .. 4 sqrt(A) x drop_high x t_high, flagged. Refused where the outline is
    drawn (use classify_outline + step_quantities: the real perimeter) or where framing members are known."""
    if outline_drawn:
        raise SlabStepError("legacy 4 sqrt(A) bound refused: the panel outline is drawn (measure its real perimeter)")
    if framing_evidence:
        raise SlabStepError("legacy 4 sqrt(A) bound refused: framing members are known (classify the outline)")
    a = _num(area_m2, "area", MAX_AREA_M2)
    dh = _num(drop_high_m, "drop high (convention SLAB_STEP_DROP_M)", MAX_D_M)
    th = _num(t_high_m, "slab thickness high", MAX_T_M)
    hi = 4 * math.sqrt(a) * dh * th
    return {"low": 0.0, "high": round(hi, 6), "status": HELD, "flag": "LEGACY_SQUARE_EQUIVALENT_BOUND",
            "formula": f"0 .. 4 sqrt({a:.4f}) x {dh:g} x {th:g}", "method": "SCOPE_QUANTITIES_V1 SLAB_STEP"}


def totals(results):
    """Sum each quantity over panels by status; a HELD term is listed with its formula, never added as 0."""
    keys = ("step_concrete_m3", "riser_form_member_m2", "member_side_form_adjust_m2", "riser_form_free_edge_m2",
            "soffit_step_form_free_edge_m2", "shared_member_riser_m2", "shared_member_side_adjust_m2")
    out = {}
    for k in keys:
        known, held = 0.0, []
        for r in results:
            v = r[k]
            if v["value"] is None:
                held.append((r["pid"], v["formula"]))
            else:
                known += v["value"]
        out[k] = {"known": round(known, 4), "held": held, "complete": not held}
    out["P_ext_m"] = round(sum(r["edges_m"]["EXTERNAL_MEMBER"] for r in results), 4)
    out["P_shared_m"] = round(sum(r["edges_m"]["SHARED_MEMBER"] + r["edges_m"]["PERIMETER_MEMBER"]
                                  for r in results), 4)
    out["L_free_m"] = round(sum(r["edges_m"]["FREE_SLAB_EDGE"] for r in results), 4)
    return out
