"""One model space, twelve drawings, and no relationship allowed to cross.

P7757's model space is 808 m wide and holds twelve unrelated drawings side
by side: plans, elevations, sections and a schedule. Round 3 ran every
global test across the whole strip and the cost was visible in its own
report — the boundary authority found ZERO site bands, because "the
outermost boundary of everything the lines enclose" spans all twelve
drawings at once, and removing it cannot free a room that an elevation's
label was never inside.

That is not a defect in the authority. It is a defect in its FRAME.

    NO WALL, PORTAL, ENCLOSURE, ADJACENCY OR CONTAINMENT RELATIONSHIP MAY
    CROSS A DRAWING REGION.

A section drawn forty metres from a plan must not be able to host that
plan's door, close that plan's room, or be the "outer ring" that plan is
measured against. Isolating the drawings first is what makes every local
test mean what it says.

HOW THE REGIONS ARE FOUND, AND WHY NO DISTANCE IS CHOSEN HERE EITHER

`cad_regions` already answers the threshold problem: it clusters at every
rung of a fixed ladder and reports where the partition is STABLE. This
module does the one thing it deliberately left to a caller — it PICKS, on
a stated rule:

    the most stable plateau; ties to the FINER partition; the rung nearest
    the geometric middle of that plateau

Ties break towards MORE regions on purpose. Splitting one drawing in two
costs measurement — some rooms go unmeasured. Merging two drawings invents
relationships that do not exist, which is the failure this module was
built to remove. Those costs are not symmetric, so the tie is not either.

If no plateau exists at all, the drawing is treated as ONE region and the
report says so. Declining to split is the safe answer: it is exactly the
behaviour of every round before this one.

WHAT A REGION IS NOT

It is not a floor, a sheet or a storey. `floor_name` is UNKNOWN here and
stays UNKNOWN — naming a floor needs evidence this module does not have,
and §1 does not ask for one. Title text is gathered as EVIDENCE and never
becomes an identity.

NOTHING HERE READS A COORDINATE, A FLOOR POSITION, A FLOOR COUNT OR A
TITLE FROM ANY PARTICULAR PROJECT.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_regions

ALGORITHM = "STABILITY_SELECTED_DRAWING_REGION_ISOLATION_V1"

# Floor identity is out of scope, by instruction and by evidence.
FLOOR_UNKNOWN = "FLOOR_UNKNOWN"

# A point that belongs to no region. Nothing may relate through it.
UNASSIGNED = ""

SELECTION_RULE = (
    "the most stable plateau in the frozen ladder sweep; ties to the FINER "
    "partition (more regions); the rung nearest the geometric middle of "
    "that plateau. No distance is chosen by hand and no rung is privileged")

WHY_TIES_GO_FINER = (
    "splitting one drawing in two costs measurement. Merging two drawings "
    "INVENTS relationships — a section hosting a plan's door, an "
    "elevation's outline acting as a plan's outer ring. Those costs are "
    "not symmetric, so the tie is not symmetric either")


@dataclass(frozen=True)
class DrawingRegion:
    """One isolated drawing inside the model space."""

    region_id: str
    object_ids: frozenset
    x0: float
    y0: float
    x1: float
    y1: float
    pad_mm: float = 0.0
    is_major: bool = True
    populations: dict = field(default_factory=dict)
    evidence: tuple = ()
    floor_name: str = FLOOR_UNKNOWN

    @property
    def width_mm(self) -> float:
        return self.x1 - self.x0

    @property
    def height_mm(self) -> float:
        return self.y1 - self.y0

    @property
    def bbox_area_mm2(self) -> float:
        return max(0.0, self.width_mm) * max(0.0, self.height_mm)

    @property
    def marks(self) -> int:
        return len(self.object_ids)

    def contains(self, x: float, y: float, *, pad: float | None = None
                 ) -> bool:
        p = self.pad_mm if pad is None else pad
        return (self.x0 - p <= x <= self.x1 + p
                and self.y0 - p <= y <= self.y1 + p)

    def holds(self, object_id: str) -> bool:
        return object_id in self.object_ids

    def record(self) -> dict:
        return {
            "region_id": self.region_id,
            "floor_name": self.floor_name,
            "marks": self.marks,
            "is_major": self.is_major,
            "extent_mm": [round(self.x0, 1), round(self.y0, 1),
                          round(self.x1, 1), round(self.y1, 1)],
            "size_mm": [round(self.width_mm, 1), round(self.height_mm, 1)],
            "assignment_pad_mm": round(self.pad_mm, 1),
            "populations": dict(self.populations),
            "evidence": list(self.evidence),
            "what_this_is_not": (
                "a floor, a sheet or a storey. Title text below is evidence "
                "about the marks in this box and never an identity"),
        }


@dataclass
class RegionReport:
    regions: list = field(default_factory=list)
    chosen_distance_mm: float | None = None
    plateau: object = None
    alternatives: list = field(default_factory=list)
    total_marks: int = 0
    notes: dict = field(default_factory=dict)
    _by_object: dict = field(default_factory=dict, repr=False)

    def major(self) -> list:
        return [r for r in self.regions if r.is_major]

    def of_object(self, object_id: str):
        return self._by_object.get(object_id)

    def of_point(self, x: float, y: float):
        """Which region owns this point. Ambiguity resolves to NOTHING.

        A point inside two regions' unpadded boxes belongs to the more
        specific one — the smaller box — because a nested box is a drawing
        inside a frame. A point that only the pad reaches, and that two
        pads reach, belongs to neither: an unassigned point relates to
        nothing, which is the safe half of §1.
        """
        inside = [r for r in self.regions if r.contains(x, y, pad=0.0)]
        if len(inside) == 1:
            return inside[0]
        if len(inside) > 1:
            inside.sort(key=lambda r: (r.bbox_area_mm2, r.region_id))
            return inside[0]
        near = [r for r in self.regions if r.contains(x, y)]
        return near[0] if len(near) == 1 else None

    def region_id_of_point(self, x: float, y: float) -> str:
        r = self.of_point(x, y)
        return r.region_id if r else UNASSIGNED

    def same_region(self, a_object_id: str, b_object_id: str) -> bool:
        """The guard §1 asks for: may these two relate at all?"""
        a, b = self.of_object(a_object_id), self.of_object(b_object_id)
        return bool(a and b and a.region_id == b.region_id)

    def counts(self) -> dict:
        return {
            "drawing_regions": len(self.regions),
            "major_regions": len(self.major()),
            "chosen_clustering_distance_mm": self.chosen_distance_mm,
            "marks_assigned": sum(r.marks for r in self.regions),
            "marks_total": self.total_marks,
        }

    def record(self, *, limit: int = 40) -> dict:
        return {
            "algorithm": ALGORITHM,
            "DRAWING_REGION_HASH": freeze_hash(),
            "selection_rule": SELECTION_RULE,
            "why_ties_go_finer": WHY_TIES_GO_FINER,
            "counts": self.counts(),
            "plateau": (self.plateau.record() if self.plateau else None),
            "alternatives_considered": [p.record()
                                        for p in self.alternatives[:8]],
            "regions": [r.record() for r in self.regions[:limit]],
            "the_rule_this_enforces": (
                "no wall, portal, enclosure, adjacency or containment "
                "relationship may cross a drawing region"),
            "floor_naming": (
                "UNKNOWN, deliberately. Isolating the drawings is what this "
                "stage is for; naming them needs evidence it does not have"),
            "notes": dict(self.notes),
        }


def _populations(texts, dimensions, instances, primitives, region) -> tuple:
    """The evidence §1 lists, counted. None of it decides anything."""
    ids = region.object_ids
    inside_p = [p for p in primitives if p.object_id in ids]
    t = [x for x in texts if region.contains(x.x, x.y)]
    d = [x for x in dimensions if region.contains(x.x1, x.y1)]
    i = [x for x in instances if region.contains(*x.insertion_mm)]
    arcs = sum(1 for p in inside_p if p.kind in ("ARC", "CIRCLE"))
    titleish = [x.value for x in t
                if ":" in x.value or "PLAN" in x.value.upper()
                or "ELEVATION" in x.value.upper()
                or "SECTION" in x.value.upper()]
    pops = {
        "geometry_marks": len(inside_p),
        "annotation_texts": len(t),
        "authored_dimensions": len(d),
        "block_instances": len(i),
        "arc_and_circle_symbols": arcs,
        "layers_present": len({p.provenance.layer for p in inside_p}),
    }
    ev = [f"{pops['geometry_marks']} marks in a "
          f"{region.width_mm / 1000:.1f} x {region.height_mm / 1000:.1f} m "
          "concentration of connected geometry"]
    if pops["authored_dimensions"]:
        ev.append(f"{pops['authored_dimensions']} authored dimensions sit "
                  "inside it")
    if pops["block_instances"]:
        ev.append(f"{pops['block_instances']} block placements sit inside "
                  "it")
    if titleish:
        ev.append("title-like text present: "
                  + "; ".join(sorted(titleish)[:3])
                  + " — evidence about the marks, never a floor name")
    return pops, tuple(ev)


def _merge_nested(clusters) -> list:
    """A drawing that stands INSIDE another one is not a second drawing.

    The clustering answers "how far apart are these marks", and a plot
    boundary is far from the villa inside it — far enough that a coarse
    rung separates them. Separating them would be wrong: a site line and
    the building it encloses are one drawing, and round 3's whole point
    was that a site line must be able to be RECOGNISED as one, which needs
    the building in the same frame.

    Containment is the evidence that settles it, and it needs no distance:
    if one group's extent lies wholly inside another's, they are nested,
    not unrelated. Side-by-side drawings never nest, so P7757's twelve
    stay twelve.
    """
    from engine.cad_regions import Cluster

    rows = list(clusters)
    changed = True
    while changed and len(rows) > 1:
        changed = False
        for i, a in enumerate(rows):
            for j, b in enumerate(rows):
                if i == j:
                    continue
                inside = (a.x0 <= b.x0 and a.y0 <= b.y0
                          and a.x1 >= b.x1 and a.y1 >= b.y1)
                bigger = ((a.x1 - a.x0) * (a.y1 - a.y0)
                          > (b.x1 - b.x0) * (b.y1 - b.y0))
                if not (inside and bigger):
                    continue
                merged = Cluster(
                    cluster_id=a.cluster_id,
                    object_ids=tuple(a.object_ids) + tuple(b.object_ids),
                    x0=min(a.x0, b.x0), y0=min(a.y0, b.y0),
                    x1=max(a.x1, b.x1), y1=max(a.y1, b.y1))
                rows = [merged] + [r for k, r in enumerate(rows)
                                   if k not in (i, j)]
                changed = True
                break
            if changed:
                break
    return rows


def _choose(sweep) -> tuple:
    """Pick the partition. The rule is stated, not tuned."""
    plateaus = [p for p in sweep["plateaus"] if p.major_count >= 1]
    if not plateaus:
        return None, None, []
    ordered = sorted(plateaus,
                     key=lambda p: (-p.stability, -p.major_count, p.from_mm))
    best = ordered[0]
    middle = math.sqrt(best.from_mm * best.to_mm)
    rungs = [d for d in sweep["ladder_mm"] if best.from_mm <= d <= best.to_mm]
    rung = min(rungs, key=lambda d: (abs(math.log(d / middle)), d))
    return best, rung, ordered[1:]


def isolate(normalized, *, sweep=None) -> RegionReport:
    """Split one model space into the drawings it actually contains."""
    sw = sweep if sweep is not None else cad_regions.sweep(
        normalized.primitives)
    rep = RegionReport(total_marks=sw["total_marks"])
    plateau, distance, others = _choose(sw)

    if plateau is None or distance is None:
        x0, y0, x1, y1 = normalized.extent()
        whole = DrawingRegion(
            region_id="DR-001",
            object_ids=frozenset(p.object_id for p in normalized.primitives),
            x0=x0, y0=y0, x1=x1, y1=y1, pad_mm=0.0, is_major=True)
        pops, ev = _populations(normalized.texts, normalized.dimensions,
                                normalized.instances, normalized.primitives,
                                whole)
        whole = DrawingRegion(**{**whole.__dict__, "populations": pops,
                                 "evidence": ev})
        rep.regions = [whole]
        rep._by_object = {oid: whole for oid in whole.object_ids}
        rep.notes["no_plateau"] = (
            "no cluster count survived two consecutive rungs of the ladder, "
            "so no partition is evidenced. The drawing is treated as ONE "
            "region — the behaviour of every round before this one, and the "
            "safe answer when the evidence does not support a split")
        return rep

    part = next(p for p in sw["partitions"] if p.distance_mm == distance)
    majors = {c.cluster_id for c in part.major(sw["total_marks"])}
    clusters = sorted(_merge_nested(part.clusters),
                      key=lambda c: (-c.marks, round(c.x0, 3), round(c.y0, 3)))

    regions = []
    for n, c in enumerate(clusters, 1):
        r = DrawingRegion(
            region_id=f"DR-{n:03d}", object_ids=frozenset(c.object_ids),
            x0=c.x0, y0=c.y0, x1=c.x1, y1=c.y1, pad_mm=distance,
            is_major=c.cluster_id in majors)
        pops, ev = _populations(normalized.texts, normalized.dimensions,
                                normalized.instances, normalized.primitives, r)
        regions.append(DrawingRegion(**{**r.__dict__, "populations": pops,
                                        "evidence": ev}))

    rep.regions = regions
    rep.chosen_distance_mm = distance
    rep.plateau = plateau
    rep.alternatives = others
    rep._by_object = {oid: r for r in regions for oid in r.object_ids}
    rep.notes["assignment_pad_mm"] = (
        f"{distance:.0f} mm — the very distance the partition was read at. "
        "A text or a symbol just outside a cluster's geometry box belongs "
        "to it at the scale that defined it, and no separate tolerance was "
        "invented for this")
    rep.notes["nesting"] = (
        "a group lying wholly inside another group's extent was merged "
        "into it. A plot boundary and the villa inside it are ONE drawing, "
        "and separating them would hide the site line from the building it "
        "encloses. Side-by-side drawings do not nest")
    rep.notes["ambiguity"] = (
        "a point two regions' pads reach belongs to NEITHER. An unassigned "
        "point relates to nothing, which is the safe half of the rule")
    return rep


def scope(region, normalized) -> dict:
    """Everything inside ONE region, and nothing outside it.

    This is how §1 is enforced in practice: the downstream stages are
    handed a region's own geometry and never see another drawing's.
    """
    ids = region.object_ids
    return {
        "region_id": region.region_id,
        "primitives": [p for p in normalized.primitives
                       if p.object_id in ids],
        "texts": [t for t in normalized.texts
                  if region.contains(t.x, t.y)],
        "dimensions": [d for d in normalized.dimensions
                       if region.contains(d.x1, d.y1)],
        "instances": [i for i in normalized.instances
                      if region.contains(*i.insertion_mm)],
    }


def scope_candidates(region, candidates) -> list:
    """Wall-like bands belonging to this region. §1, applied to walls."""
    return [c for c in candidates if c.object_id in region.object_ids]


def frozen_parameters() -> dict:
    return {
        "ALGORITHM": ALGORITHM,
        "SELECTION_RULE": SELECTION_RULE,
        "LADDER_MM": list(cad_regions.LADDER_MM),
        "MINOR_CLUSTER_SHARE": cad_regions.MINOR_CLUSTER_SHARE,
        "why": {
            "no_new_distance": (
                "the ladder and the minor-cluster share are the frozen "
                "sweep's, unchanged. This module adds a SELECTION RULE, "
                "not a threshold"),
            "ties_go_finer": WHY_TIES_GO_FINER,
            "no_plateau": (
                "one region, and the report says so. Declining to split is "
                "a legitimate answer and it is the conservative one"),
        },
    }


def freeze_hash() -> str:
    parts = [ALGORITHM, SELECTION_RULE, cad_regions.freeze_hash(),
             FLOOR_UNKNOWN]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
