"""E1.1 — a radial line crossing a circle is not a room wall.

E1 v1 kept the drawing's arcs exactly, which was right. Then it fed the
pool's radial setting-out lines to the same tracer as the walls, and
polygonize did what polygonize does: it cut the circle into wedges and
handed back closed faces. Two of them were RELEASED as physical regions.

    The arcs were never the problem. The ROLE of the linework was.

So this module reads circular geometry as circular geometry:

    a family of curves about ONE centre is a round object
    the outermost ring is its construction outline
    a ring a wall-thickness inside it is that object's built face
    rings further in describe what is inside the object
    a straight line through the centre is how it was SET OUT

and returns a semantic for every curve and for every line that belongs to
one of those families. Nothing here knows this project. A round object
becomes a POOL only when a label group beside it says so, in the general
vocabulary of round water bodies, and otherwise stays an unnamed round
object whose internal geometry is still barred from bounding a room.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from engine import cad_entity_role as cer

MODEL = "A_RADIAL_LINE_CROSSING_A_CIRCLE_IS_NOT_A_ROOM_WALL_V1"

# --- the seven curve semantics ------------------------------------------
POOL_OUTER_CONSTRUCTION = "POOL_OUTER_CONSTRUCTION"
POOL_WALL_FACE = "POOL_WALL_FACE"
POOL_WATER_BOUNDARY = "POOL_WATER_BOUNDARY"
POOL_INTERNAL_REFERENCE = "POOL_INTERNAL_REFERENCE"
RADIAL_CONSTRUCTION_LINE = "RADIAL_CONSTRUCTION_LINE"
CURVED_ROOM_BOUNDARY = "CURVED_ROOM_BOUNDARY"
UNKNOWN_CURVE = "UNKNOWN_CURVE"

CURVE_SEMANTICS = (POOL_OUTER_CONSTRUCTION, POOL_WALL_FACE,
                   POOL_WATER_BOUNDARY, POOL_INTERNAL_REFERENCE,
                   RADIAL_CONSTRUCTION_LINE, CURVED_ROOM_BOUNDARY,
                   UNKNOWN_CURVE)

# What each semantic licenses as an ENTITY role.
ENTITY_ROLE_OF = {
    POOL_OUTER_CONSTRUCTION: cer.POOL_CONTOUR,
    POOL_WALL_FACE: cer.POOL_CONTOUR,
    POOL_WATER_BOUNDARY: cer.POOL_INTERNAL_GEOMETRY,
    POOL_INTERNAL_REFERENCE: cer.POOL_INTERNAL_GEOMETRY,
    RADIAL_CONSTRUCTION_LINE: cer.CONSTRUCTION_LINE,
    CURVED_ROOM_BOUNDARY: cer.MATERIAL_WALL_FACE,
    UNKNOWN_CURVE: cer.UNKNOWN,
}

A_RADIAL_LINE_IS_NOT_A_PARTITION = (
    "a line drawn from the centre of a round object to its edge is how the "
    "object was set out. Letting it bound a face turns one pool into six "
    "wedge-shaped rooms, each with a perfectly good arc on its outside")

WHY_CURVE_SUPPORT_IS_NOT_THE_PROBLEM = (
    "exact ARC, CIRCLE and COMPOSITE_CURVE support is correct and is "
    "unchanged. What is corrected here is the ROLE of the linework inside "
    "and across a curve, which is a semantic question, not a geometric one")

# --- GENERAL vocabulary, not a project answer ---------------------------
#
# The names POOL_* are the approved vocabulary for a round water body. A
# round object earns them from the LABEL BESIDE IT, in this general list,
# and never from its coordinates or its radius.
GENERAL_ROUND_WATER_TERMS = ("POOL", "SWIMMING POOL", "JACUZZI",
                             "FOUNTAIN", "WATER FEATURE", "PLUNGE POOL")

# --- GENERAL geometric tolerances ---------------------------------------
CONCENTRIC_TOL_MM = 60.0        # two curves share a centre
RADIAL_TOL_MM = 120.0           # a line's own line passes through a centre
RING_WALL_MIN_MM = cer.WALL_SEPARATION_MIN_MM
RING_WALL_MAX_MM = cer.WALL_SEPARATION_MAX_MM
INSIDE_SHARE = 0.60
# A SETTING-OUT LINE RUNS FROM THE CENTRE. A winder tread points at the
# same centre and STOPS SHORT of it, running between two concentric arcs.
# Without this one ratio the stair beside the reception - thirteen treads
# fanning about a point - reads as thirteen construction lines.
MIN_INNER_RADIUS_SHARE = 0.15             # how much of a line lies within a radius

SCOPE = ("GENERAL circular-object geometry. No project coordinate, radius "
         "or region id appears here")


def model_hash() -> str:
    parts = ([MODEL] + list(CURVE_SEMANTICS) + list(GENERAL_ROUND_WATER_TERMS)
             + [f"{CONCENTRIC_TOL_MM}", f"{RADIAL_TOL_MM}",
                f"{INSIDE_SHARE}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class RoundObject:
    """A family of curves about one centre, and what lies inside it."""

    object_key: str = ""
    cx: float = 0.0
    cy: float = 0.0
    radii_mm: tuple = ()
    curve_ids: tuple = ()
    radial_line_ids: tuple = ()
    inner_line_ids: tuple = ()
    named_by: str = ""
    identity: str = "UNNAMED_ROUND_OBJECT"

    def record(self) -> dict:
        return {
            "ROUND_OBJECT": self.object_key,
            "centre_mm": [round(self.cx, 3), round(self.cy, 3)],
            "radii_mm": [round(r, 3) for r in self.radii_mm],
            "rings": len(self.curve_ids),
            "curve_entities": list(self.curve_ids),
            "radial_construction_lines": list(self.radial_line_ids),
            "other_internal_lines": list(self.inner_line_ids),
            "identity": self.identity,
            "named_by_label_group": self.named_by,
            "a_radial_line_is_not_a_partition":
                A_RADIAL_LINE_IS_NOT_A_PARTITION,
        }


def _centre(p):
    return (p.cx, p.cy)


def classify(primitives, *, label_points=(), water_terms=None) -> dict:
    """A semantic for every curve, and for the lines inside round objects.

    `label_points` is a sequence of (x_mm, y_mm, token). A round object
    takes a water-body identity only when one of those tokens is in the
    general vocabulary and its point lies inside the object's outer ring.
    """
    terms = tuple(t.upper() for t in (water_terms
                                      or GENERAL_ROUND_WATER_TERMS))
    curves = [p for p in primitives if p.kind in ("ARC", "CIRCLE")]
    lines = [p for p in primitives if p.kind == "SEGMENT" and p.length_mm > 0]

    # --- group curves by centre -----------------------------------------
    families = []
    for c in curves:
        cx, cy = _centre(c)
        for fam in families:
            if math.hypot(fam["cx"] - cx, fam["cy"] - cy) <= CONCENTRIC_TOL_MM:
                fam["members"].append(c)
                break
        else:
            families.append({"cx": cx, "cy": cy, "members": [c]})

    out_curves, objects = {}, []
    for n, fam in enumerate(sorted(families,
                                   key=lambda f: -max(m.radius
                                                      for m in f["members"])),
                            start=1):
        members = sorted(fam["members"], key=lambda m: -m.radius)
        radii = [m.radius for m in members]
        outer = radii[0]
        cx, cy = fam["cx"], fam["cy"]

        # which straight lines belong to this family
        radial, inner = [], []
        for L in lines:
            d_mid = math.hypot((L.x1 + L.x2) / 2 - cx, (L.y1 + L.y2) / 2 - cy)
            if d_mid > outer:
                continue
            inside = sum(1 for (x, y) in ((L.x1, L.y1), (L.x2, L.y2))
                         if math.hypot(x - cx, y - cy) <= outer + RADIAL_TOL_MM)
            if inside < 1:
                continue
            # distance from the centre to the line the segment lies on
            dx, dy = L.x2 - L.x1, L.y2 - L.y1
            nrm = math.hypot(dx, dy) or 1.0
            perp = abs((dx * (cy - L.y1) - dy * (cx - L.x1)) / nrm)
            r_a = math.hypot(L.x1 - cx, L.y1 - cy)
            r_b = math.hypot(L.x2 - cx, L.y2 - cy)
            r_in, r_out = min(r_a, r_b), max(r_a, r_b)
            reaches_centre = r_out <= 0 or (r_in / r_out) < (
                MIN_INNER_RADIUS_SHARE)
            if perp <= RADIAL_TOL_MM and reaches_centre:
                radial.append(L)
            elif inside == 2:
                inner.append(L)

        identity, named_by = "UNNAMED_ROUND_OBJECT", ""
        for (x, y, token) in label_points:
            if math.hypot(x - cx, y - cy) <= outer and str(
                    token).upper() in terms:
                identity, named_by = "ROUND_WATER_BODY", str(token).upper()
                break

        obj = RoundObject(object_key=f"ROUND-{n:03d}", cx=cx, cy=cy,
                          radii_mm=tuple(radii),
                          curve_ids=tuple(m.object_id for m in members),
                          radial_line_ids=tuple(L.object_id for L in radial),
                          inner_line_ids=tuple(L.object_id for L in inner),
                          identity=identity, named_by=named_by)
        objects.append(obj)

        water = identity == "ROUND_WATER_BODY"
        if not water:
            # AN UNNAMED ROUND OBJECT DOES NOT OWN THE LINES INSIDE IT.
            # The reception stair is drawn between concentric arcs; if this
            # module claimed its treads as internal geometry, the stair
            # pass would never see them. Only a named water body's
            # internals are classified here.
            radial, inner = [], []
            obj.radial_line_ids = ()
            obj.inner_line_ids = ()
        for i, m in enumerate(members):
            if len(members) == 1:
                sem = UNKNOWN_CURVE
                why = ("a single ring with no concentric partner. Whether "
                       "it is a built face is not established here")
                conf = cer.NOT_ESTABLISHED
            elif i == 0:
                sem = POOL_OUTER_CONSTRUCTION if water else UNKNOWN_CURVE
                why = ("the outermost ring of a round object. It is the "
                       "outline the object was built to")
                conf = cer.MEDIUM if water else cer.NOT_ESTABLISHED
            elif RING_WALL_MIN_MM <= (radii[i - 1] - radii[i]) \
                    <= RING_WALL_MAX_MM and i == 1:
                sem = POOL_WALL_FACE if water else CURVED_ROOM_BOUNDARY
                why = ("a ring one wall thickness inside the outline, which "
                       "is how a curved built face is drawn")
                conf = cer.MEDIUM
            elif i == len(members) - 1 and water:
                sem = POOL_WATER_BOUNDARY
                why = "the innermost ring of a water body"
                conf = cer.LOW
            else:
                sem = POOL_INTERNAL_REFERENCE if water else UNKNOWN_CURVE
                why = ("a ring inside the object's face, describing what is "
                       "inside it rather than bounding a space")
                conf = cer.LOW if water else cer.NOT_ESTABLISHED
            out_curves[m.object_id] = {
                "curve_semantic": sem,
                "entity_role": ENTITY_ROLE_OF[sem],
                "confidence": conf,
                "round_object": obj.object_key,
                "radius_mm": round(m.radius, 3),
                "ring_index_from_outside": i,
                "why": why,
                "exact_parameters_retained": True,
            }
        for L in radial:
            out_curves[L.object_id] = {
                "curve_semantic": RADIAL_CONSTRUCTION_LINE,
                "entity_role": ENTITY_ROLE_OF[RADIAL_CONSTRUCTION_LINE],
                "confidence": cer.MEDIUM,
                "round_object": obj.object_key,
                "why": A_RADIAL_LINE_IS_NOT_A_PARTITION,
            }
        for L in inner:
            out_curves[L.object_id] = {
                "curve_semantic": (POOL_INTERNAL_REFERENCE if water
                                   else UNKNOWN_CURVE),
                "entity_role": ENTITY_ROLE_OF[
                    POOL_INTERNAL_REFERENCE if water else UNKNOWN_CURVE],
                "confidence": cer.LOW if water else cer.NOT_ESTABLISHED,
                "round_object": obj.object_key,
                "why": ("it lies wholly inside a round object, so it "
                        "describes the object rather than bounding a room"),
            }

    counts = {}
    for row in out_curves.values():
        counts[row["curve_semantic"]] = counts.get(
            row["curve_semantic"], 0) + 1
    return {
        "curve_roles": out_curves,
        "round_objects": objects,
        "counts": counts,
        "curves_seen": len(curves),
        "families": len(families),
        "why_curve_support_is_not_the_problem":
            WHY_CURVE_SUPPORT_IS_NOT_THE_PROBLEM,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "CURVE_SEMANTICS": list(CURVE_SEMANTICS),
        "ENTITY_ROLE_OF": dict(ENTITY_ROLE_OF),
        "GENERAL_ROUND_WATER_TERMS": list(GENERAL_ROUND_WATER_TERMS),
        "CONCENTRIC_TOL_MM": CONCENTRIC_TOL_MM,
        "RADIAL_TOL_MM": RADIAL_TOL_MM,
        "RING_WALL_MIN_MM": RING_WALL_MIN_MM,
        "RING_WALL_MAX_MM": RING_WALL_MAX_MM,
        "INSIDE_SHARE": INSIDE_SHARE,
        "SCOPE": SCOPE,
        "why": {
            "a_radial_line_is_not_a_partition":
                A_RADIAL_LINE_IS_NOT_A_PARTITION,
            "curve_support_is_not_the_problem":
                WHY_CURVE_SUPPORT_IS_NOT_THE_PROBLEM,
        },
    }
