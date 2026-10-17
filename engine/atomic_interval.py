"""E1.2 — a CAD entity is not one semantic role.

E1.1 established ENTITY_ESTABLISHED_ROLE for a whole CAD entity. A long
line can be parallel to a wall face for 600 mm of its 4 m, and E1.1 let
that 600 mm of evidence establish the whole entity as MATERIAL_WALL_FACE.
Evidence licenses the stretch it exists on and nothing more.

So the unit of role in E1.2 is not the entity. It is the

    ATOMIC_ENTITY_INTERVAL

a stretch of one entity between two evidence-change points, carrying its
own role, confidence, evidence, the partner intervals that support it and
the evidence that contradicts it.

An entity is cut wherever the evidence could change:

    a partner's overlap starts or ends
    a wall junction
    an opening jamb
    a portal
    an intersection with any other admitted entity
    a casework return
    a column or pier boundary
    a block boundary
    a semantic-role transition

The parameter `t` runs 0 to 1 along the entity's own parameterisation -
along the line for a LINE, along the sweep for an ARC - so an interval can
always be turned back into exact geometry without a chord ever being
stored. START_MM and END_MM are computed from `t`, never the other way
round.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

MODEL = "A_CAD_ENTITY_IS_NOT_ONE_SEMANTIC_ROLE_V1"

EVIDENCE_LICENSES_ONLY_ITS_OWN_INTERVAL = (
    "evidence establishes the stretch it exists on. A partner running "
    "along 600 mm of a 4 m line says what that 600 mm is, and says "
    "nothing whatever about the other 3.4 m")

WHOLE_ENTITY_PROMOTION_IS_BANNED = (
    "no role is ever assigned to a parent entity and inherited by its "
    "intervals. The register records the role of every interval "
    "separately, and an entity's 'role' is a summary of its intervals "
    "rather than a fact about the entity")

# --- why an entity gets cut ---------------------------------------------
CUT_PARTNER_START = "A_PARALLEL_PARTNERS_OVERLAP_BEGINS"
CUT_PARTNER_END = "A_PARALLEL_PARTNERS_OVERLAP_ENDS"
CUT_WALL_JUNCTION = "A_WALL_JUNCTION"
CUT_OPENING_JAMB = "AN_OPENING_JAMB"
CUT_PORTAL = "A_PORTAL"
CUT_INTERSECTION = "AN_INTERSECTION_WITH_ANOTHER_ENTITY"
CUT_CASEWORK_RETURN = "A_CASEWORK_RETURN"
CUT_COLUMN_BOUNDARY = "A_COLUMN_OR_PIER_BOUNDARY"
CUT_BLOCK_BOUNDARY = "A_BLOCK_BOUNDARY"
CUT_ROLE_TRANSITION = "A_SEMANTIC_ROLE_TRANSITION"
CUT_REASONS = (CUT_PARTNER_START, CUT_PARTNER_END, CUT_WALL_JUNCTION,
               CUT_OPENING_JAMB, CUT_PORTAL, CUT_INTERSECTION,
               CUT_CASEWORK_RETURN, CUT_COLUMN_BOUNDARY,
               CUT_BLOCK_BOUNDARY, CUT_ROLE_TRANSITION)

# Two cut points closer than this are one cut point. Below it an interval
# would be shorter than the drawing's own precision.
MIN_INTERVAL_MM = 1.0
CUT_MERGE_MM = 0.5


def model_hash() -> str:
    parts = [MODEL] + list(CUT_REASONS) + [f"{MIN_INTERVAL_MM}",
                                           f"{CUT_MERGE_MM}"]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- geometry

def entity_length(prim) -> float:
    return float(getattr(prim, "length_mm", 0.0) or 0.0)


def point_at(prim, t: float) -> tuple:
    """The exact point at parameter t on this entity. No chord is used."""
    t = max(0.0, min(1.0, t))
    if prim.kind == "SEGMENT":
        return (prim.x1 + (prim.x2 - prim.x1) * t,
                prim.y1 + (prim.y2 - prim.y1) * t)
    if prim.kind == "ARC":
        sweep = (prim.end_angle - prim.start_angle) % (2 * math.pi)
        a = prim.start_angle + sweep * t
        return (prim.cx + prim.radius * math.cos(a),
                prim.cy + prim.radius * math.sin(a))
    if prim.kind == "CIRCLE":
        a = 2 * math.pi * t
        return (prim.cx + prim.radius * math.cos(a),
                prim.cy + prim.radius * math.sin(a))
    return (0.0, 0.0)


def t_of_length(prim, mm: float) -> float:
    """Turn a distance along the entity into its parameter."""
    L = entity_length(prim)
    return 0.0 if L <= 0 else max(0.0, min(1.0, mm / L))


def angle_at(prim, t: float) -> float:
    """The direction the entity runs at t, in radians."""
    if prim.kind == "SEGMENT":
        return math.atan2(prim.y2 - prim.y1, prim.x2 - prim.x1)
    if prim.kind in ("ARC", "CIRCLE"):
        p = point_at(prim, t)
        return math.atan2(p[0] - prim.cx, -(p[1] - prim.cy))
    return 0.0


# ------------------------------------------------------------- intervals

@dataclass
class Interval:
    """One stretch of one entity, with its own role and its own evidence."""

    interval_id: str = ""
    parent_object_id: str = ""
    t_start: float = 0.0
    t_end: float = 1.0
    start_mm: tuple = (0.0, 0.0)
    end_mm: tuple = (0.0, 0.0)
    length_mm: float = 0.0
    layer: str = ""
    entity_type: str = ""
    kind: str = ""
    role: str = ""
    confidence: str = ""
    evidence: tuple = ()
    supporting_partner_intervals: tuple = ()
    conflicting_evidence: tuple = ()
    may_bound_material: bool = False
    provenance: dict = field(default_factory=dict)
    cut_reasons: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {
            "INTERVAL_ID": self.interval_id,
            "PARENT_OBJECT_ID": self.parent_object_id,
            "T_START": round(self.t_start, 9),
            "T_END": round(self.t_end, 9),
            "START_MM": [round(self.start_mm[0], 4),
                         round(self.start_mm[1], 4)],
            "END_MM": [round(self.end_mm[0], 4), round(self.end_mm[1], 4)],
            "LENGTH_MM": round(self.length_mm, 4),
            "LAYER": self.layer,
            "ENTITY_TYPE": self.entity_type,
            "KIND": self.kind,
            "ROLE": self.role,
            "CONFIDENCE": self.confidence,
            "EVIDENCE": list(self.evidence),
            "SUPPORTING_PARTNER_INTERVALS":
                [dict(x) for x in self.supporting_partner_intervals],
            "CONFLICTING_EVIDENCE": list(self.conflicting_evidence),
            "MAY_BOUND_MATERIAL": self.may_bound_material,
            "PROVENANCE": dict(self.provenance),
            "cut_at": list(self.cut_reasons),
            "why": self.why,
            "evidence_licenses_only_its_own_interval":
                EVIDENCE_LICENSES_ONLY_ITS_OWN_INTERVAL,
        }


def merge_cuts(cuts, *, length_mm) -> list:
    """Sorted unique cut parameters, with 0 and 1, close ones collapsed."""
    if length_mm <= 0:
        return [0.0, 1.0]
    eps = CUT_MERGE_MM / length_mm
    rows = sorted({round(max(0.0, min(1.0, float(t))), 12)
                   for t, _why in cuts} | {0.0, 1.0})
    out = [rows[0]]
    for t in rows[1:]:
        if t - out[-1] > eps:
            out.append(t)
    if out[-1] < 1.0:
        out[-1] = 1.0
    return out


def cut(prim, cuts, *, prefix="IV") -> list:
    """Split one entity into atomic intervals at the given parameters.

    `cuts` is a sequence of (t, why). The reasons are carried onto the
    intervals that meet at that point, so a reader can see what changed.
    """
    L = entity_length(prim)
    ts = merge_cuts(cuts, length_mm=L)
    eps = CUT_MERGE_MM / L if L > 0 else 0.0
    why_at = {}
    for t, why in cuts:
        t = max(0.0, min(1.0, float(t)))
        near = min(ts, key=lambda q: abs(q - t))
        if abs(near - t) <= max(eps, 1e-12):
            why_at.setdefault(near, set()).add(why)
    prov = prim.provenance
    out = []
    for i, (a, b) in enumerate(zip(ts, ts[1:]), start=1):
        if (b - a) * L < MIN_INTERVAL_MM and len(ts) > 2:
            continue
        p0, p1 = point_at(prim, a), point_at(prim, b)
        out.append(Interval(
            interval_id=f"{prefix}:{prim.object_id}#{i:02d}",
            parent_object_id=prim.object_id,
            t_start=a, t_end=b, start_mm=p0, end_mm=p1,
            length_mm=(b - a) * L,
            layer=prov.layer, entity_type=prov.entity_type, kind=prim.kind,
            cut_reasons=tuple(sorted(why_at.get(a, set())
                                     | why_at.get(b, set()))),
            provenance={"dwg_handle": prov.handle,
                        "object_id": prim.object_id,
                        "layer": prov.layer,
                        "entity_type": prov.entity_type,
                        "block_path": list(getattr(prov, "block_path", ())),
                        "instance_path": [str(h) for h in
                                          getattr(prov, "instance_path", ())]}))
    if not out:                                   # an entity shorter than
        p0, p1 = point_at(prim, 0.0), point_at(prim, 1.0)   # one interval
        out.append(Interval(
            interval_id=f"{prefix}:{prim.object_id}#01",
            parent_object_id=prim.object_id, t_start=0.0, t_end=1.0,
            start_mm=p0, end_mm=p1, length_mm=L, layer=prov.layer,
            entity_type=prov.entity_type, kind=prim.kind,
            provenance={"dwg_handle": prov.handle,
                        "object_id": prim.object_id, "layer": prov.layer,
                        "entity_type": prov.entity_type}))
    return out


# ------------------------------------------------------- interval algebra

def union(ranges) -> list:
    """Merge overlapping (lo, hi) ranges. The union of fragment support."""
    rows = sorted((a, b) for a, b in ranges if b > a)
    out = []
    for a, b in rows:
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def total(ranges) -> float:
    return sum(b - a for a, b in union(ranges))


def intersect(ranges, lo, hi) -> list:
    out = []
    for a, b in ranges:
        x, y = max(a, lo), min(b, hi)
        if y > x:
            out.append((x, y))
    return out


def covers(ranges, lo, hi, *, tol=1e-9) -> bool:
    """Is (lo, hi) wholly inside the union of these ranges?"""
    for a, b in union(ranges):
        if a - tol <= lo and hi <= b + tol:
            return True
    return False


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "CUT_REASONS": list(CUT_REASONS),
        "MIN_INTERVAL_MM": MIN_INTERVAL_MM,
        "CUT_MERGE_MM": CUT_MERGE_MM,
        "why": {
            "evidence_licenses_only_its_own_interval":
                EVIDENCE_LICENSES_ONLY_ITS_OWN_INTERVAL,
            "whole_entity_promotion_is_banned":
                WHOLE_ENTITY_PROMOTION_IS_BANNED,
        },
    }
