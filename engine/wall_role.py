"""A paired face proves wall-like GEOMETRY. What the wall DOES is separate.

The profile's paired-face test answered "is this drawn like a wall". On
P7757 it answered yes for four layers, one of which is almost certainly the
site and plot layer — and feeding a plot boundary to the enclosure as a
wall face is what let a flood escaping a washroom still close, on the plot.

So there is a second stage, and it asks a different question:

    SITE_BOUNDARY            nothing the drawing treats as interior lies
                             beyond it, and interior lies within
    BUILDING_EXTERNAL_WALL   interior on one side, the space between
                             building and plot on the other
    INTERNAL_PARTITION       interior on BOTH sides
    OTHER_ARCHITECTURAL_WALL wall-like, but its sides do not resolve
    UNRESOLVED               not established

The test is occupancy, not naming: what lies on each side of the band. No
layer number appears anywhere in this module, and none may — on this source
the wall-like layers happen to be called 1, 2, 5 and W, and on the next one
they will be called something else.

WHY THIS IS NOT A SIZE TEST EITHER

A site boundary is not "a long line". A courtyard wall can be longer than a
plot edge on a narrow site. What distinguishes them is that one has
occupied space on both sides and the other does not.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

CLASSIFIER = "WALL_ROLE_CLASSIFIER_V1"

SITE_BOUNDARY = "SITE_BOUNDARY"
BUILDING_EXTERNAL_WALL = "BUILDING_EXTERNAL_WALL"
INTERNAL_PARTITION = "INTERNAL_PARTITION"
OTHER_ARCHITECTURAL_WALL = "OTHER_ARCHITECTURAL_WALL"
UNRESOLVED = "UNRESOLVED"

# How far off a band to look for occupancy. One metre: wider than any wall
# this engine will admit (the profile's band tops out at 600 mm) and
# narrower than any room, so the probe lands in the space beside the wall
# rather than two rooms away.
PROBE_OFFSET_MM = 1000.0

WHY = {
    SITE_BOUNDARY: "occupied space lies on one side only, and nothing the "
                   "drawing treats as interior lies beyond it",
    BUILDING_EXTERNAL_WALL: "interior on one side, the space between "
                            "building and plot on the other",
    INTERNAL_PARTITION: "interior on both sides — it divides rooms",
    OTHER_ARCHITECTURAL_WALL: "wall-like geometry whose sides do not resolve",
    UNRESOLVED: "not established. It supports no release on its own",
}


@dataclass(frozen=True)
class BandRole:
    band_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    role: str
    occupied_sides: int
    evidence: tuple

    def record(self) -> dict:
        return {"band_id": self.band_id, "axis": self.axis,
                "fixed_mm": round(self.fixed_mm, 2),
                "interval_mm": [round(self.start_mm, 2),
                                round(self.end_mm, 2)],
                "wall_role": self.role, "why": WHY.get(self.role, ""),
                "occupied_sides": self.occupied_sides,
                "evidence": list(self.evidence)}


@dataclass
class WallRoleReport:
    bands: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def by_role(self) -> dict:
        return dict(Counter(b.role for b in self.bands).most_common())

    def role_of(self, band_id: str) -> str:
        for b in self.bands:
            if b.band_id == band_id:
                return b.role
        return UNRESOLVED

    def record(self, *, limit: int = 40) -> dict:
        return {
            "classifier": CLASSIFIER,
            "WALL_ROLE_HASH": classifier_hash(),
            "bands_classified": len(self.bands),
            "by_role": self.by_role(),
            "frozen_parameters": frozen_parameters(),
            "sample": [b.record() for b in self.bands[:limit]],
            "notes": dict(self.notes),
            "never": ("no layer name takes part in any verdict here. On "
                      "this source the wall-like layers happen to be called "
                      "1, 2, 5 and W; on the next they will not be"),
        }


def frozen_parameters() -> dict:
    return {"CLASSIFIER": CLASSIFIER, "PROBE_OFFSET_MM": PROBE_OFFSET_MM,
            "why": {"PROBE_OFFSET_MM": (
                "wider than any wall this engine admits (the profile's band "
                "tops out at 600 mm) and narrower than any room, so the "
                "probe lands beside the wall rather than two rooms away")}}


def classifier_hash() -> str:
    parts = [CLASSIFIER, SITE_BOUNDARY, BUILDING_EXTERNAL_WALL,
             INTERNAL_PARTITION, OTHER_ARCHITECTURAL_WALL, UNRESOLVED,
             str(PROBE_OFFSET_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def classify(candidates, *, interior=None, envelope=None) -> WallRoleReport:
    """Classify each wall-like band by what occupies each of its sides.

    `interior` is a callable `(x, y) -> bool` — is this point inside a
    space the drawing treats as occupied. `envelope` is an optional
    callable saying whether a point is inside the building fabric. Both are
    geometry supplied by the caller.
    """
    rep = WallRoleReport()
    for n, c in enumerate(candidates, 1):
        mid = (c.start_mm + c.end_mm) / 2.0
        if c.axis == "H":
            a = (mid, c.fixed_mm + PROBE_OFFSET_MM)
            b = (mid, c.fixed_mm - PROBE_OFFSET_MM)
        else:
            a = (c.fixed_mm + PROBE_OFFSET_MM, mid)
            b = (c.fixed_mm - PROBE_OFFSET_MM, mid)

        if interior is None:
            rep.bands.append(BandRole(
                band_id=c.object_id, axis=c.axis, fixed_mm=c.fixed_mm,
                start_mm=c.start_mm, end_mm=c.end_mm, role=UNRESOLVED,
                occupied_sides=0,
                evidence=("no occupancy test was supplied, so no side "
                          "could be probed",)))
            continue

        ina, inb = bool(interior(*a)), bool(interior(*b))
        sides = int(ina) + int(inb)
        ev = [f"probe {PROBE_OFFSET_MM:.0f} mm each side: "
              f"{'occupied' if ina else 'empty'} / "
              f"{'occupied' if inb else 'empty'}"]

        if sides == 2:
            role = INTERNAL_PARTITION
            ev.append("occupied space on both sides — it divides two spaces")
        elif sides == 1:
            if envelope is not None:
                ea, eb = bool(envelope(*a)), bool(envelope(*b))
                if ea != eb:
                    role = BUILDING_EXTERNAL_WALL
                    ev.append("it also crosses the building envelope, so it "
                              "is where fabric meets open ground")
                else:
                    role = OTHER_ARCHITECTURAL_WALL
                    ev.append("one side occupied, and both sides fall the "
                              "same side of the envelope")
            else:
                role = OTHER_ARCHITECTURAL_WALL
                ev.append("one side occupied; no envelope test supplied to "
                          "distinguish an external wall from a boundary")
        else:
            role = SITE_BOUNDARY
            ev.append("nothing occupied on either side at this offset — it "
                      "bounds ground rather than space")

        rep.bands.append(BandRole(
            band_id=c.object_id, axis=c.axis, fixed_mm=c.fixed_mm,
            start_mm=c.start_mm, end_mm=c.end_mm, role=role,
            occupied_sides=sides, evidence=tuple(ev)))

    rep.notes["what_this_adds"] = (
        "the paired-face test said these are drawn like walls. This says "
        "what each one does. A band bounding ground is not a room boundary, "
        "however convincingly it is drawn")
    return rep
