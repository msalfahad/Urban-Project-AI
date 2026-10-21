"""E1.2 §7 — this layer checks the drawing. It never looks at it.

E1.1 called its gate `visual_gate`, gave it a `sheet=` argument, and then
checked entity roles, dimensions, label counts and whether the raster had
registered. It never read a pixel of the sheet, and it could still return

    VISUALLY_CONSISTENT

which told a reader that something had been looked at. Nothing had.

So the same checks live on here under the name that describes them, and
the word VISUAL is gone from this layer entirely. Looking is done by the
cold challenger in `visual_challenger`, by an agent that can actually see,
and its verdict is recorded separately.
"""

from __future__ import annotations

import hashlib
import math

from engine import cad_geometry as cg
from engine import interval_role as ir

MODEL = "THIS_LAYER_CHECKS_THE_DRAWING_IT_NEVER_LOOKS_AT_IT_V1"

DETERMINISTICALLY_CONSISTENT = "DETERMINISTICALLY_CONSISTENT"
DIMENSION_CONFLICT = "DIMENSION_CONFLICT"
ENTITY_ROLE_CONFLICT = "ENTITY_ROLE_CONFLICT"
LABEL_CONFLICT = "LABEL_CONFLICT"
OVERLAP_CONFLICT = "OVERLAP_CONFLICT"
TOPOLOGY_CONFLICT = "TOPOLOGY_CONFLICT"
UNRESOLVED = "UNRESOLVED"

QA_STATES = (DETERMINISTICALLY_CONSISTENT, DIMENSION_CONFLICT,
             ENTITY_ROLE_CONFLICT, LABEL_CONFLICT, OVERLAP_CONFLICT,
             TOPOLOGY_CONFLICT, UNRESOLVED)

NEVER_EMITS_A_VISUAL_VERDICT = (
    "no state in this vocabulary claims anything was seen. "
    "DETERMINISTICALLY_CONSISTENT means the drawing does not contradict "
    "itself here - the roles, the dimensions, the labels and the overlaps "
    "agree. Whether the boundary follows what a builder would read as "
    "enclosure is a question for a pass that looks at the sheet")

BANNED_STATE = "VISUALLY_CONSISTENT"

DIMENSION_DISAGREEMENT_MM = 100.0


class DeterministicQAError(RuntimeError):
    """Something asked this layer to claim it had seen the drawing."""


def model_hash() -> str:
    parts = [MODEL] + list(QA_STATES) + [f"{DIMENSION_DISAGREEMENT_MM}"]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _dist_point_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n2 = dx * dx + dy * dy
    if n2 <= 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n2))
    return math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1])


def _near_any_wall(pt, walls, tol) -> bool:
    for s in walls:
        if s.kind == cg.LINE:
            if _dist_point_seg(pt, (s.x1, s.y1), (s.x2, s.y2)) <= tol:
                return True
        else:
            if abs(math.hypot(pt[0] - s.cx, pt[1] - s.cy) - s.radius) <= tol:
                return True
    return False


def dimension_cross_check(boundary, dimensions, *, wall_face_tol_mm=60.0):
    """What the drawing's own dimensions say about this candidate's span."""
    from shapely.geometry import LineString, Point, Polygon
    out = []
    if boundary is None:
        return out
    try:
        poly = Polygon(boundary.points())
        if not poly.is_valid:
            poly = poly.buffer(0)
    except Exception:
        return out
    walls = [s for s in boundary.segments if s.role in cg.MATERIAL_ROLES]
    for d in dimensions:
        span = math.hypot(d.x2 - d.x1, d.y2 - d.y1)
        if span <= 0:
            continue
        mid = Point((d.x1 + d.x2) / 2.0, (d.y1 + d.y2) / 2.0)
        if not poly.contains(mid):
            continue
        origins = sum(1 for pt in ((d.x1, d.y1), (d.x2, d.y2))
                      if _near_any_wall(pt, walls, wall_face_tol_mm))
        line = LineString([(d.x1, d.y1), (d.x2, d.y2)])
        crossed = 0
        for s in walls:
            try:
                pts = s.points(tol_mm=cg.DENSIFY_TOL_MM)
                if len(pts) >= 2 and LineString(pts).distance(line) \
                        <= wall_face_tol_mm:
                    crossed += 1
            except Exception:
                pass
        inter = poly.intersection(line)
        got = inter.length if not inter.is_empty else 0.0
        if got <= 0:
            continue
        short = span - got
        out.append({
            "dimension_mm": round(span, 2),
            "printed_value": d.display_value,
            "candidate_span_along_it_mm": round(got, 2),
            "difference_mm": round(short, 2),
            "origins_on_established_wall_faces": origins,
            "established_wall_faces_crossing_it": crossed,
            "usable": bool(origins == 2 and crossed <= 2),
            "verdict": (DIMENSION_CONFLICT
                        if abs(short) > DIMENSION_DISAGREEMENT_MM
                        else DETERMINISTICALLY_CONSISTENT),
            "direction": ("THE_CANDIDATE_IS_SHORTER_THAN_THE_DIMENSION"
                          if short > 0 else
                          "THE_CANDIDATE_IS_LONGER_THAN_THE_DIMENSION"),
        })
    return out


def check(*, boundary, interval_roles, distinct_label_groups,
          dimension_rows, overlap_relations=(), a18_topology_conflict=False,
          ambiguous_band_on_ring=()) -> dict:
    """The deterministic states. Never a claim about what was seen."""
    states, notes = [], []
    if boundary is None:
        return {"DETERMINISTIC_QA_STATE": [UNRESOLVED],
                "notes": ["no boundary to check"],
                "dimension_cross_check": list(dimension_rows or ()),
                "never_emits_a_visual_verdict": NEVER_EMITS_A_VISUAL_VERDICT}

    bad = []
    for s in boundary.segments:
        if s.role not in cg.MATERIAL_ROLES:
            continue
        row = interval_roles.get(s.object_id)
        if row is None or not row.get("may_bound_material"):
            bad.append((s.object_id, (row or {}).get("role", "NOT_IN_REGISTER")))
    if bad:
        states.append(ENTITY_ROLE_CONFLICT)
        notes.append(f"{len(bad)} ring segments come from intervals whose "
                     f"role may not bound material: "
                     f"{sorted({r for _o, r in bad})}")
    if ambiguous_band_on_ring:
        states.append(ENTITY_ROLE_CONFLICT)
        notes.append("the ring uses an AMBIGUOUS_PAIRED_BAND, which CAD "
                     "cannot tell from a counter, a bar or casework: "
                     f"{sorted(set(ambiguous_band_on_ring))}")

    roles_on_ring = {s.role for s in boundary.segments}
    if roles_on_ring & {cg.ROLE_UNRESOLVED, cg.DIMENSION_WITNESS,
                        cg.ANNOTATION_ONLY}:
        states.append(ENTITY_ROLE_CONFLICT)
        notes.append(f"the ring carries {sorted(roles_on_ring)}")

    if len(distinct_label_groups) > 1:
        states.append(LABEL_CONFLICT)
        notes.append("more than one physical-space label is seen inside: "
                     f"{sorted(distinct_label_groups)}")

    blocking = [r for r in overlap_relations
                if r.get("blocks_release")]
    if blocking:
        states.append(OVERLAP_CONFLICT)
        notes.append(f"{len(blocking)} overlap relations block release")

    usable = [r for r in dimension_rows if r["usable"]]
    conflicts = [r for r in usable if r["verdict"] == DIMENSION_CONFLICT]
    if conflicts:
        states.append(DIMENSION_CONFLICT)
        worst = max(conflicts, key=lambda r: abs(r["difference_mm"]))
        notes.append(
            f"a dimension between two established wall faces states "
            f"{worst['dimension_mm']:.0f} mm across this space and the "
            f"candidate spans {worst['candidate_span_along_it_mm']:.0f} mm "
            "along the same line")

    if a18_topology_conflict:
        states.append(TOPOLOGY_CONFLICT)
        notes.append("the frozen reading and the CAD ring disagree about "
                     "whether this space is open")

    if not states:
        states.append(DETERMINISTICALLY_CONSISTENT)
        notes.append("the drawing does not contradict itself here. Nothing "
                     "in this result says the sheet was looked at")
    out = {"DETERMINISTIC_QA_STATE": sorted(set(states)),
           "notes": notes,
           "dimension_cross_check": list(dimension_rows or ()),
           "never_emits_a_visual_verdict": NEVER_EMITS_A_VISUAL_VERDICT}
    if BANNED_STATE in out["DETERMINISTIC_QA_STATE"]:
        raise DeterministicQAError(
            f"{BANNED_STATE} is not a state this layer may emit. "
            + NEVER_EMITS_A_VISUAL_VERDICT)
    return out


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "QA_STATES": list(QA_STATES),
        "BANNED_STATE": BANNED_STATE,
        "DIMENSION_DISAGREEMENT_MM": DIMENSION_DISAGREEMENT_MM,
        "why": {"never_emits_a_visual_verdict": NEVER_EMITS_A_VISUAL_VERDICT},
    }
