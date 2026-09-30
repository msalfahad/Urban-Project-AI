"""Neutral REALISED geometry records — the physical output schema shared by K1 and K2.

Sharing the output SHAPE is allowed (R8.2 §8); sharing transformation
mathematics is not. Nothing here computes a placement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


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
    unplaced: list = field(default_factory=list)
    other_layout: list = field(default_factory=list)
    obs_dispositions: dict = field(default_factory=dict)     # obs_id -> Counter(disposition), for conservation

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
            "unplaced": list(self.unplaced),
            "other_layout": list(self.other_layout),
            "dispositions": dict(self.dispositions),
        }
