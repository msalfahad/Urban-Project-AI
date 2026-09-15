"""E102 — eleven doorways, three answers each, and no real drawing involved.

§6. Every case states its expected MATERIAL connectivity, ROOM PARTITION
and NAVIGABILITY independently, so a change that trades one for another
fails rather than looking like progress.

The cases that matter most for generalisation are the ink ones. A door leaf
drawn across both jambs, and one drawn touching neither, must produce THE
SAME room partition: the partition comes from a supported portal, not from
whether this particular architect's leaf happens to close the pixels.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.evidence_tiers import (CH_ANNOTATION, CH_GEOMETRY, CH_STRUCTURE,
                                   CH_SYMBOL, Observation, SRC_SAME_DOCUMENT_SET,
                                   grade_portal)
from engine.space_topologies import (MATERIAL_GEOMETRY,
                                     NAVIGABLE_FREE_SPACE,
                                     PARTITION_DIAGNOSTIC,
                                     PARTITION_RELEASABLE,
                                     PARTITION_UNRESOLVED,
                                     ROOM_PARTITION_TOPOLOGY,
                                     boundary_from_portal)


class _Portal:
    """The fields a partition boundary reads off a portal."""

    def __init__(self, pid, axis="H", jamb_a=1000.0, jamb_b=1900.0,
                 fixed=0.0, thickness=200.0, host="WB-0001"):
        self.portal_id, self.axis = pid, axis
        self.jamb_a_mm, self.jamb_b_mm = jamb_a, jamb_b
        self.host_wall_band_id = host
        self._fixed, self._t = fixed, thickness

    @property
    def opening_width_mm(self):
        return abs(self.jamb_b_mm - self.jamb_a_mm)

    @property
    def polygon(self):
        from shapely.geometry import box
        if self.axis == "H":
            return box(self.jamb_a_mm, self._fixed,
                       self.jamb_b_mm, self._fixed + self._t)
        return box(self._fixed, self.jamb_a_mm,
                   self._fixed + self._t, self.jamb_b_mm)


@dataclass
class Case:
    """One doorway, with all three expected answers stated separately."""

    name: str
    space_a: str
    space_b: str
    portal: object = None
    material_between: bool = False
    observations: list = field(default_factory=list)
    geometry_exact: bool = True
    host_compatible: bool = True
    expect_material_connected: bool = True
    expect_rooms_distinct: bool = True
    expect_navigable: bool = True
    expect_partition_status: str = PARTITION_RELEASABLE
    door_ink_closes_pixels: bool | None = None
    note: str = ""

    def record(self) -> dict:
        return {
            "case": self.name,
            "between": [self.space_a, self.space_b],
            "expected": {
                MATERIAL_GEOMETRY: self.expect_material_connected,
                ROOM_PARTITION_TOPOLOGY: (
                    "DISTINCT" if self.expect_rooms_distinct else "ONE"),
                "partition_status": self.expect_partition_status,
                NAVIGABLE_FREE_SPACE: self.expect_navigable,
            },
            "door_ink_closes_pixels": self.door_ink_closes_pixels,
            "note": self.note,
        }


def _geom_and_symbol(pid):
    return [Observation(f"{pid}-G", "opening gap", CH_GEOMETRY),
            Observation(f"{pid}-S", "door swing arc", CH_SYMBOL)]


def _geom_only(pid):
    return [Observation(f"{pid}-G", "opening gap", CH_GEOMETRY)]


# --------------------------------------------------------------- the eleven

def bedroom_to_corridor() -> Case:
    return Case(
        name="BEDROOM_TO_CORRIDOR_THROUGH_HINGED_DOOR",
        space_a="BED-09", space_b="COR-09",
        portal=_Portal("PT-B-C"), observations=_geom_and_symbol("PT-B-C"),
        door_ink_closes_pixels=True,
        note="the ordinary case. One opening, two rooms, one connection")


def bedroom_to_ensuite() -> Case:
    return Case(
        name="BEDROOM_TO_ENSUITE_THROUGH_HINGED_DOOR",
        space_a="BED-09", space_b="BTH-09",
        portal=_Portal("PT-B-E", jamb_a=500.0, jamb_b=1300.0),
        observations=_geom_and_symbol("PT-B-E"),
        door_ink_closes_pixels=True,
        note=("§7's worked example. A bedroom and its ensuite are two "
              "rooms with an opening between them and a person can walk "
              "through: all three answers differ and all three are true"))


def room_to_room_sliding_door() -> Case:
    return Case(
        name="ROOM_TO_ROOM_THROUGH_SLIDING_DOOR",
        space_a="SAL-09", space_b="DIN-09",
        portal=_Portal("PT-SLIDE", jamb_a=800.0, jamb_b=2400.0),
        observations=[
            Observation("PT-SLIDE-G", "opening gap", CH_GEOMETRY),
            Observation("PT-SLIDE-A", "printed 1600 opening width",
                        CH_ANNOTATION)],
        door_ink_closes_pixels=False,
        note=("a sliding door has no swing arc. The printed opening width "
              "is a different authoring channel and does the same job"))


def open_plan_with_no_portal_boundary() -> Case:
    return Case(
        name="OPEN_PLAN_DINING_TO_LIVING_WITH_NO_PHYSICAL_PORTAL",
        space_a="DIN-09", space_b="LIV-09",
        portal=None, material_between=False,
        expect_material_connected=True,
        expect_rooms_distinct=False,
        expect_navigable=True,
        expect_partition_status=PARTITION_UNRESOLVED,
        door_ink_closes_pixels=False,
        note=("no wall and no portal: the two labels are functional zones "
              "of ONE space. Nothing here supports a room boundary, and "
              "inventing one because two names exist is the error §13 of "
              "the previous round forbids"))


def double_doors() -> Case:
    return Case(
        name="DOUBLE_DOORS",
        space_a="HAL-09", space_b="SAL-09",
        portal=_Portal("PT-DBL", jamb_a=0.0, jamb_b=1800.0),
        observations=_geom_and_symbol("PT-DBL"),
        door_ink_closes_pixels=True,
        note=("1.8 m of opening in two leaves is still one portal "
              "partition boundary, and still zero material"))


def door_with_swing_arc() -> Case:
    return Case(
        name="DOOR_WITH_SWING_ARC",
        space_a="BED-10", space_b="COR-09",
        portal=_Portal("PT-ARC"), observations=_geom_and_symbol("PT-ARC"),
        door_ink_closes_pixels=True,
        note="geometry plus symbol: two authoring channels, releasable")


def door_without_swing_arc() -> Case:
    return Case(
        name="DOOR_WITHOUT_SWING_ARC",
        space_a="BED-11", space_b="COR-09",
        portal=_Portal("PT-NOARC"), observations=_geom_only("PT-NOARC"),
        expect_partition_status=PARTITION_DIAGNOSTIC,
        door_ink_closes_pixels=False,
        note=("a gap with nothing else supporting it. The rooms stay "
              "DISTINCT — the partition exists — but it is DIAGNOSTIC, "
              "which is different from merging them"))


def leaf_ink_touching_both_jambs() -> Case:
    return Case(
        name="DOOR_LEAF_INK_THAT_TOUCHES_BOTH_JAMBS",
        space_a="BED-12", space_b="COR-09",
        portal=_Portal("PT-INK1"), observations=_geom_only("PT-INK1"),
        expect_partition_status=PARTITION_DIAGNOSTIC,
        door_ink_closes_pixels=True,
        note=("the generalisation case. This architect's leaf closes the "
              "pixels; the partition must be identical to the case below, "
              "where it does not"))


def graphics_that_do_not_touch() -> Case:
    return Case(
        name="DOOR_GRAPHICS_THAT_DO_NOT_TOUCH",
        space_a="BED-13", space_b="COR-09",
        portal=_Portal("PT-INK2"), observations=_geom_only("PT-INK2"),
        expect_partition_status=PARTITION_DIAGNOSTIC,
        door_ink_closes_pixels=False,
        note=("the same doorway drawn by an architect whose leaf floats "
              "clear of both jambs. Same partition, or the room topology "
              "does not travel between offices"))


def passage_or_archway() -> Case:
    return Case(
        name="PASSAGE_OR_ARCHWAY",
        space_a="COR-09", space_b="SAL-09",
        portal=_Portal("PT-ARCH", jamb_a=0.0, jamb_b=1200.0),
        observations=[
            Observation("PT-ARCH-G", "opening gap", CH_GEOMETRY),
            Observation("PT-ARCH-D", "schedule row for the archway",
                        CH_STRUCTURE, SRC_SAME_DOCUMENT_SET)],
        door_ink_closes_pixels=False,
        note=("an archway has no leaf and no swing at all. The schedule "
              "carries it, and the opening is still zero material"))


def unresolved_gap_with_no_portal_evidence() -> Case:
    return Case(
        name="UNRESOLVED_GAP_WITH_NO_PORTAL_EVIDENCE",
        space_a="RGN-09", space_b="RGN-10",
        portal=None, material_between=False,
        expect_material_connected=True,
        expect_rooms_distinct=False,
        expect_navigable=True,
        expect_partition_status=PARTITION_UNRESOLVED,
        door_ink_closes_pixels=False,
        note=("a hole in the drawing. Not a doorway, not a room boundary, "
              "and not something to guess at: UNRESOLVED, releasable as "
              "neither one space nor two"))


ALL = (bedroom_to_corridor, bedroom_to_ensuite, room_to_room_sliding_door,
       open_plan_with_no_portal_boundary, double_doors, door_with_swing_arc,
       door_without_swing_arc, leaf_ink_touching_both_jambs,
       graphics_that_do_not_touch, passage_or_archway,
       unresolved_gap_with_no_portal_evidence)


def cases() -> list:
    return [make() for make in ALL]


def grade_of(case) -> str:
    """The evidence grade this case's portal earns."""
    if case.portal is None:
        return ""
    return grade_portal(
        case.portal.portal_id, case.observations,
        geometry_exact=case.geometry_exact,
        host_compatible=case.host_compatible,
        opening_width_mm=case.portal.opening_width_mm).grade


def boundary_of(case):
    """The partition boundary this case's portal produces, if any."""
    if case.portal is None:
        return None
    return boundary_from_portal(case.portal, grade_of(case))
