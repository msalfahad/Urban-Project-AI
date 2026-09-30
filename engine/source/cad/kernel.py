"""K1 — Urban's canonical CAD geometry kernel.

SOURCE OBSERVATIONS -> complete physical placement -> WCS REALISED GEOMETRY,
plus a visible SourceFinding for everything it cannot establish.

K1 does not identify walls or rooms, apply trade rules, assign materials,
infer units or publish quantities. Coordinates stay in native units.

TRANSFORM MODEL (one composed affine map per realised instance)

    placed(INSERT in parent) = parent @ OCS(insert.extrusion)
                               @ T(insertion + R(rotation) . (col*cs, row*rs))
                               @ R(rotation) @ S(xscale, yscale)
                               @ T(-block.base_point)

    ARC / CIRCLE / LWPOLYLINE : full = container @ OCS(entity.extrusion)
    LINE                      : full = container            (WCS-native)
    ELLIPSE                   : full = container; its normal only orients the minor axis

    MINSERT spacing is rotated with the insert and never scaled by it.

CURVES ARE REALISED BY MAPPING POINTS, never by angle arithmetic: centre,
start, mid-sweep and end are computed in the entity's own frame and pushed
through the full map. Sweep direction comes from the sign of det(full) — the
COMPLETE composed transform, not the extrusion, a local scale or a rotation
field — and is then cross-checked against the orientation of the mapped
points themselves; a disagreement is KERNEL_ORIENTATION_INCONSISTENT.

A circular curve under a non-similarity map is an exact ELLIPTICAL arc (the
affine image of a circle): K1 realises it as such, with conjugate
semi-diameters, and notes NON_UNIFORM_SCALE_CURVE. It never manufactures a
circle.

Every observation reached at every instance gets exactly one disposition:
REALISED, HIDDEN (source invisibility flag), CARRIED (a kind K1 observes but
does not realise, e.g. TEXT/DIMENSION), or FINDING. Nothing disappears.

The functions scale_matrix, frame_matrix, insert_matrix and
curve_orientation are module-level on purpose: the R8.1 mutation tests
(MT-01/02/03/49) monkeypatch them to prove the acceptance tests catch each
reintroduced defect.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .. import findings as F
from ..findings import SourceFinding
from .. import observations as O
from . import kernel_ocs
from .affine import Affine2
from .kernel_ocs import SourceFrameError

MAX_NESTING_DEPTH = 16
# Relative tolerance for "this linear map is a similarity" (float64 noise on
# composed rotations is ~1e-16 relative; 1e-9 leaves margin for decoder
# rounding of scale factors while rejecting any authored non-uniform scale).
SIMILARITY_REL_TOL = 1e-9
TWO_PI = 2.0 * math.pi

REALISED, HIDDEN, CARRIED, FINDING = "REALISED", "HIDDEN", "CARRIED", "FINDING"


# ---------------------------------------------------------------- composition

def scale_matrix(sx: float, sy: float) -> Affine2:
    return Affine2.scale(sx, sy)


def rotation_matrix(theta: float) -> Affine2:
    return Affine2.rotation(theta)


def frame_matrix(extrusion) -> Affine2:
    """OCS plan map; raises SourceFrameError (never returns identity for an unreadable frame)."""
    return Affine2.linear(*kernel_ocs.plan_frame(extrusion).linear)


def grid_offsets(grid: O.GridSpec | None, rotation: float) -> list:
    """(label, (dx, dy)) per cell, offsets rotated with the insert, not scaled."""
    if grid is None:
        return [("", (0.0, 0.0))]
    rot = rotation_matrix(rotation)
    return [(f"[{c},{r}]", rot.apply_linear((c * grid.column_spacing, r * grid.row_spacing)))
            for r in range(grid.rows) for c in range(grid.columns)]


def insert_matrix(ins: O.InsertGeom, base_point, offset=(0.0, 0.0)) -> Affine2:
    return (Affine2.translation(ins.insertion[0] + offset[0], ins.insertion[1] + offset[1])
            @ rotation_matrix(ins.rotation)
            @ scale_matrix(ins.scale[0], ins.scale[1])
            @ Affine2.translation(-base_point[0], -base_point[1]))


def curve_orientation(full: Affine2, entity_frame: Affine2) -> int:
    """Orientation of the COMPLETE composed map. entity_frame is accepted so a
    mutation can (wrongly) key the decision on the frame alone (MT-49)."""
    return 1 if full.det() > 0 else -1


def points_orientation(p0, pm, p1, centre) -> str:
    """CCW / CW of the traversal p0 -> pm -> p1 about centre, from points only."""
    a0 = math.atan2(p0[1] - centre[1], p0[0] - centre[0])
    am = math.atan2(pm[1] - centre[1], pm[0] - centre[0])
    a1 = math.atan2(p1[1] - centre[1], p1[0] - centre[0])
    return "CCW" if (am - a0) % TWO_PI < (a1 - a0) % TWO_PI else "CW"


def _flip(d):
    return "CW" if d == "CCW" else "CCW"


# ---------------------------------------------------------------- realised records

@dataclass(frozen=True)
class Lineage:
    obs_id: str
    source_handle: str
    instance_path: tuple
    layer: str | None
    kind: str


@dataclass(frozen=True)
class RealisedSegment:
    a: tuple
    b: tuple
    lineage: Lineage


@dataclass(frozen=True)
class RealisedCircularArc:
    """source ARC: start/end are the images of the entity's start/end angles.
    source BULGE: start = VERTEX_A, end = VERTEX_B; direction is A -> B."""

    center: tuple
    radius: float
    start: tuple
    mid: tuple
    end: tuple
    direction: str
    source: str
    lineage: Lineage


@dataclass(frozen=True)
class RealisedCircle:
    center: tuple
    radius: float
    lineage: Lineage


@dataclass(frozen=True)
class RealisedEllipticalArc:
    """point(t) = center + cos t * axis_u + sin t * axis_v, t from t0 to t1
    (conjugate semi-diameters; exact, not an approximation)."""

    center: tuple
    axis_u: tuple
    axis_v: tuple
    t0: float
    t1: float
    start: tuple
    mid: tuple
    end: tuple
    direction: str
    full: bool
    source: str
    lineage: Lineage


@dataclass(frozen=True)
class RealisedAttribute:
    tag: str
    value: str
    insertion: tuple
    owner_insert_handle: str
    lineage: Lineage


@dataclass
class RealisedGeometry:
    segments: list = field(default_factory=list)
    arcs: list = field(default_factory=list)
    circles: list = field(default_factory=list)
    elliptical_arcs: list = field(default_factory=list)
    attributes: list = field(default_factory=list)
    carried: list = field(default_factory=list)
    hidden: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    dispositions: Counter = field(default_factory=Counter)
    visits: int = 0

    def as_contract_dict(self) -> dict:
        """The frozen R8 physical-geometry interface (tests/r8_0 acceptance tests)."""
        arcs, bulges = [], []
        for a in self.arcs:
            meta = {"obs_id": a.lineage.obs_id, "instance_path": list(a.lineage.instance_path), "layer": a.lineage.layer}
            if a.source == "BULGE":
                bulges.append({"VERTEX_A": a.start, "VERTEX_B": a.end, "ARC_MIDPOINT": a.mid, "CENTER": a.center,
                               "DIR_A_TO_B": a.direction, "RADIUS": a.radius, **meta})
            else:
                arcs.append({"CENTER": a.center, "P0": a.start, "PM": a.mid, "P1": a.end, "DIR": a.direction,
                             "RADIUS": a.radius, **meta})
        return {
            "segments": [(s.a, s.b) for s in self.segments],
            "segment_lineage": [{"obs_id": s.lineage.obs_id, "instance_path": list(s.lineage.instance_path),
                                 "layer": s.lineage.layer} for s in self.segments],
            "arcs": arcs, "bulges": bulges,
            "circles": [{"CENTER": c.center, "RADIUS": c.radius, "obs_id": c.lineage.obs_id} for c in self.circles],
            "elliptical_arcs": [{"CENTER": e.center, "AXIS_U": e.axis_u, "AXIS_V": e.axis_v, "T0": e.t0, "T1": e.t1,
                                 "START_POINT": e.start, "MID_SWEEP_POINT": e.mid, "END_POINT": e.end,
                                 "SWEEP_DIRECTION": e.direction, "FULL": e.full, "source": e.source,
                                 "obs_id": e.lineage.obs_id, "instance_path": list(e.lineage.instance_path)}
                                for e in self.elliptical_arcs],
            "attributes": [{"tag": a.tag, "value": a.value, "insertion": a.insertion,
                            "owner_insert_handle": a.owner_insert_handle} for a in self.attributes],
            "findings": [f.as_dict() for f in self.findings],
            "hidden": list(self.hidden),
            "carried": list(self.carried),
            "dispositions": dict(self.dispositions),
        }


# ---------------------------------------------------------------- the walk

def realise(document: O.SourceDocument) -> RealisedGeometry:
    out = RealisedGeometry()
    out.findings.extend(document.findings)
    for obs in document.entities:
        _emit(document, obs, Affine2.identity(), (), True, 0, out)
    return out


def _dispose(out, kind):
    out.dispositions[kind] += 1
    out.visits += 1


def _finding(out, code, obs, path, detail=""):
    out.findings.append(SourceFinding(code, obs.obs_id if obs is not None else None, tuple(path), detail))


def _lineage(obs, path):
    return Lineage(obs.obs_id, obs.source_handle, tuple(path), obs.layer, obs.kind)


def _emit(doc, obs, parent: Affine2, path: tuple, visible: bool, depth: int, out: RealisedGeometry):
    kind = obs.kind
    if kind == O.UNSUPPORTED_KIND:
        g = obs.geometry
        _finding(out, g.category, obs, path, g.reason)
        _dispose(out, FINDING)
        return
    if not (visible and obs.visible):
        out.hidden.append({"obs_id": obs.obs_id, "kind": kind, "instance_path": list(path)})
        _dispose(out, HIDDEN)
        return
    if kind in O.CARRIED_KINDS:
        out.carried.append({"obs_id": obs.obs_id, "kind": kind, "instance_path": list(path)})
        _dispose(out, CARRIED)
        return
    try:
        if kind == O.LINE:
            g = obs.geometry
            out.segments.append(RealisedSegment(parent.apply(g.start), parent.apply(g.end), _lineage(obs, path)))
        elif kind == O.ARC:
            frame = frame_matrix(obs.extrusion)
            _realise_arc(obs, parent @ frame, frame, path, out)
        elif kind == O.CIRCLE:
            frame = frame_matrix(obs.extrusion)
            _realise_circle(obs, parent @ frame, path, out)
        elif kind == O.LWPOLYLINE:
            frame = frame_matrix(obs.extrusion)
            _realise_polyline(obs, parent @ frame, frame, path, out)
        elif kind == O.ELLIPSE:
            _realise_ellipse(obs, parent, path, out)
        elif kind == O.INSERT:
            _realise_insert(doc, obs, parent, path, depth, out)
            return
        else:
            _finding(out, F.UNHANDLED, obs, path, f"kind {kind!r} has no K1 realisation")
            _dispose(out, FINDING)
            return
    except SourceFrameError as err:
        _finding(out, err.code, obs, path, err.detail)
        _dispose(out, FINDING)
        return
    _dispose(out, REALISED)


def _check_orientation(out, obs, path, start, mid, end, centre, direction):
    if points_orientation(start, mid, end, centre) != direction:
        _finding(out, F.KERNEL_ORIENTATION_INCONSISTENT, obs, path,
                 "sweep from det(full) disagrees with the orientation of the realised points")


def _circle_points(c, r, t):
    return (c[0] + r * math.cos(t), c[1] + r * math.sin(t))


def _elliptical_from_circle(obs, full, c_loc, r, t0, sweep, local_dir_sign, path, source, out,
                            start=None, end=None, mid=None):
    """Exact affine image of a circular arc under a non-similarity map."""
    C = full.apply(c_loc)
    u = full.apply_linear((r, 0.0))
    v = full.apply_linear((0.0, r))
    tt = [t0, t0 + local_dir_sign * sweep / 2.0, t0 + local_dir_sign * sweep]
    pts = [(C[0] + math.cos(t) * u[0] + math.sin(t) * v[0], C[1] + math.cos(t) * u[1] + math.sin(t) * v[1]) for t in tt]
    direction = "CCW" if (curve_orientation(full, full) * local_dir_sign) > 0 else "CW"
    out.elliptical_arcs.append(RealisedEllipticalArc(
        C, u, v, tt[0], tt[2], start or pts[0], mid or pts[1], end or pts[2], direction,
        abs(sweep - TWO_PI) < 1e-15, source, _lineage(obs, path)))
    _finding(out, F.NON_UNIFORM_SCALE_CURVE, obs, path,
             "circular curve under a non-similarity map realised exactly as an elliptical arc")


def _realise_arc(obs, full, frame, path, out):
    g = obs.geometry
    sweep = (g.end_angle - g.start_angle) % TWO_PI or TWO_PI
    if not full.is_similarity(SIMILARITY_REL_TOL):
        _elliptical_from_circle(obs, full, g.center, g.radius, g.start_angle, sweep, 1, path, "ARC", out)
        return
    s_loc = _circle_points(g.center, g.radius, g.start_angle)
    m_loc = _circle_points(g.center, g.radius, g.start_angle + sweep / 2.0)
    e_loc = _circle_points(g.center, g.radius, g.start_angle + sweep)
    C, S, M, E = full.apply(g.center), full.apply(s_loc), full.apply(m_loc), full.apply(e_loc)
    direction = "CCW" if curve_orientation(full, frame) > 0 else "CW"
    _check_orientation(out, obs, path, S, M, E, C, direction)
    out.arcs.append(RealisedCircularArc(C, g.radius * math.sqrt(abs(full.det())), S, M, E, direction, "ARC",
                                        _lineage(obs, path)))


def _realise_circle(obs, full, path, out):
    g = obs.geometry
    if not full.is_similarity(SIMILARITY_REL_TOL):
        _elliptical_from_circle(obs, full, g.center, g.radius, 0.0, TWO_PI, 1, path, "CIRCLE", out)
        return
    out.circles.append(RealisedCircle(full.apply(g.center), g.radius * math.sqrt(abs(full.det())), _lineage(obs, path)))


def _realise_polyline(obs, full, frame, path, out):
    g = obs.geometry
    verts = g.vertices
    n = len(verts)
    spans = range(n) if (g.closed and n > 2) else range(n - 1)
    for i in spans:
        a, b = verts[i], verts[(i + 1) % n]
        bulge = g.bulges[i] if i < len(g.bulges) else 0.0
        if a[0] == b[0] and a[1] == b[1]:
            _finding(out, F.DEGENERATE_GEOMETRY, obs, path, f"span {i} has coincident end points")
            continue
        A, B = full.apply(a), full.apply(b)
        if abs(bulge) < 1e-12:
            out.segments.append(RealisedSegment(A, B, _lineage(obs, path)))
            continue
        chord = math.hypot(b[0] - a[0], b[1] - a[1])
        theta = 4.0 * math.atan(abs(bulge))
        rad = chord / (2.0 * math.sin(theta / 2.0))
        sgn = 1.0 if bulge > 0 else -1.0
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        lx, ly = -(b[1] - a[1]) / chord, (b[0] - a[0]) / chord          # left normal of a->b
        h = rad * math.cos(theta / 2.0) * sgn
        c_loc = (mx + lx * h, my + ly * h)                              # centre: left for CCW (+), right for CW (-)
        sag = rad * (1.0 - math.cos(theta / 2.0)) * sgn
        m_loc = (mx - lx * sag, my - ly * sag)                          # arc midpoint: opposite side from the centre
        if not full.is_similarity(SIMILARITY_REL_TOL):
            ta = math.atan2(a[1] - c_loc[1], a[0] - c_loc[0])
            _elliptical_from_circle(obs, full, c_loc, rad, ta, theta, int(sgn), path, "BULGE", out,
                                    start=A, end=B, mid=full.apply(m_loc))
            continue
        C, M = full.apply(c_loc), full.apply(m_loc)
        local_dir = "CCW" if bulge > 0 else "CW"
        direction = local_dir if curve_orientation(full, frame) > 0 else _flip(local_dir)
        _check_orientation(out, obs, path, A, M, B, C, direction)
        out.arcs.append(RealisedCircularArc(C, rad * math.sqrt(abs(full.det())), A, M, B, direction, "BULGE",
                                            _lineage(obs, path)))


def _realise_ellipse(obs, container, path, out):
    """ELLIPSE: centre and major axis are WCS-native (in the container); the
    normal orients the minor axis: minor = ratio * (N x major)."""
    g = obs.geometry
    s = kernel_ocs.plan_normal_sign(obs.extrusion)
    mx, my = g.major_axis[0], g.major_axis[1]
    minor = (-s * my * g.ratio, s * mx * g.ratio)
    sweep = (g.end_param - g.start_param) % TWO_PI or TWO_PI
    C = container.apply(g.center)
    u = container.apply_linear((mx, my))
    v = container.apply_linear(minor)
    tt = [g.start_param, g.start_param + sweep / 2.0, g.start_param + sweep]
    pts = [(C[0] + math.cos(t) * u[0] + math.sin(t) * v[0], C[1] + math.cos(t) * u[1] + math.sin(t) * v[1]) for t in tt]
    direction = "CCW" if s * curve_orientation(container, container) > 0 else "CW"
    out.elliptical_arcs.append(RealisedEllipticalArc(C, u, v, tt[0], tt[2], pts[0], pts[1], pts[2], direction,
                                                     abs(sweep - TWO_PI) < 1e-15, "ELLIPSE", _lineage(obs, path)))


def _realise_insert(doc, obs, parent, path, depth, out):
    g: O.InsertGeom = obs.geometry
    blk = doc.blocks.get(g.block_key)
    here = path + (obs.obs_id,)
    if blk is None:
        _finding(out, F.MISSING_BLOCK_DEFINITION, obs, here, f"block {g.block_key!r} is not defined in the source")
        _dispose(out, FINDING)
        return
    if blk.xref is not None:
        x = blk.xref
        code = (F.XREF_UNLOADED if x.unloaded else
                F.XREF_CONTENT_NOT_IN_SOURCE if x.resolved else F.XREF_NOT_RESOLVED)
        _finding(out, code, obs, here,
                 f"xref {blk.name!r} path={x.path!r} attachment={x.attachment} mapping={x.mapping_status}; "
                 "its content is not in this source: zero children is not evidence of no geometry")
        _dispose(out, FINDING)
        # any locally present entities are still realised, but the instance stays incomplete
        if not blk.entities:
            return
    if not blk.name_readable:
        _finding(out, F.BLOCK_NAME_UNREADABLE, obs, here, f"block {blk.key!r} has no readable name in the source")
    if depth >= MAX_NESTING_DEPTH:
        _finding(out, F.NESTING_LIMIT, obs, here, f"nesting deeper than {MAX_NESTING_DEPTH}")
        _dispose(out, FINDING)
        return
    try:
        ocs = frame_matrix(obs.extrusion)
    except SourceFrameError as err:
        _finding(out, err.code, obs, here, err.detail)
        _dispose(out, FINDING)
        return
    if blk.xref is None:
        _dispose(out, REALISED)
    for label, off in grid_offsets(g.grid, g.rotation):
        placed = parent @ ocs @ insert_matrix(g, blk.base_point, off)
        cell_path = path + (obs.obs_id + label,)
        for child in blk.entities:
            _emit(doc, child, placed, cell_path, obs.visible, depth + 1, out)
    for att in g.attributes:
        try:
            p = (parent @ frame_matrix(att.extrusion)).apply(att.insertion)
        except SourceFrameError as err:
            _finding(out, err.code, obs, here, f"attribute {att.tag}: {err.detail}")
            continue
        out.attributes.append(RealisedAttribute(att.tag, att.value, p, obs.source_handle, _lineage(obs, here)))
