"""E31C — what is missing around a room, without repairing it from the raster."""

from __future__ import annotations

from engine.local_topology import (SIDE_HAS_WALL, SIDE_NO_WALL_PAIR,
                                   analyse_space, compare_to_printed,
                                   positive_controls)
from engine.wall_graph import WallEdge


def e(eid, axis, centre, a, b, sep=200.0):
    return WallEdge(edge_id=eid, axis=axis, centreline_mm=centre, start_mm=a,
                    end_mm=b, face_a_mm=centre - sep / 2,
                    face_b_mm=centre + sep / 2, pair_id="WP-1",
                    wall_face_separation_mm=sep)


CLOSED = [e("N", "H", 0.0, 0.0, 3000.0), e("S", "H", 2400.0, 0.0, 3000.0),
          e("W", "V", 0.0, 0.0, 2400.0), e("E", "V", 3000.0, 0.0, 2400.0)]


def test_a_fully_walled_room_can_hold_a_cycle():
    out = analyse_space("BTH-X", (0, 0, 3000, 2400), edges=CLOSED)
    assert out["sides_with_a_wall"] == 4
    assert out["can_a_cycle_exist"] is True


def test_a_missing_side_is_named_with_what_is_nearby():
    """"BTH-01 cannot be enclosed" is a result. "its north side has no wall
    pair within 2 m" is a repair instruction."""
    out = analyse_space("BTH-X", (0, 0, 3000, 2400), edges=CLOSED[1:])
    assert out["sides_missing"] >= 1
    missing = [s for s in out["sides"] if s["status"] != SIDE_HAS_WALL]
    assert missing and all(s["likely_cause"] for s in missing)


def test_nothing_is_repaired_from_the_raster_region():
    out = analyse_space("BTH-X", (0, 0, 3000, 2400), edges=[])
    assert out["repaired"] is False
    assert "never what to find" in out["why_not_repaired"]


def test_a_printed_dimension_is_never_used_to_manufacture_a_candidate():
    out = compare_to_printed("WSH-01", candidate_area_m2=None,
                             candidate_perimeter_m=None,
                             printed_w_mm=1500, printed_h_mm=2400)
    assert out["verdict"] == "NO_CANDIDATE_GENERATED"
    assert "NOT used to manufacture one" in out["why"]


def test_a_candidate_is_compared_to_the_printed_dimension_afterwards():
    out = compare_to_printed("WSH-01", candidate_area_m2=3.55,
                             candidate_perimeter_m=7.7,
                             printed_w_mm=1500, printed_h_mm=2400)
    assert out["verdict"] == "CONSISTENT_WITH_PRINTED"
    assert "not a licence to adjust it" in out["why"]


def test_a_face_that_merely_contains_a_room_is_not_a_reproduction():
    """Reporting a 981 m2 building outline as this bathroom with a 29,676%
    area difference dresses a total failure as a near miss."""
    from engine.planar import BOUNDED, Face
    huge = Face(face_id="F1", component_id="GC-1", half_edge_ids=("h",),
                polygon_mm=((0, 0), (40000, 0), (40000, 30000), (0, 30000)),
                signed_area_mm2=1.2e9, perimeter_mm=140000.0,
                orientation="COUNTERCLOCKWISE", kind=BOUNDED)
    regions = {1: {"space_id": "BTH-05", "room_type": "BATHROOM",
                   "area_m2": 3.3, "centroid_mm": (5000.0, 5000.0),
                   "bbox_mm": (4000, 4000, 6000, 6000)}}
    out = positive_controls([huge], regions, ["BTH-05"])
    assert out[0]["result"] == "NOT_REPRODUCED"
    assert "contains the room rather than being it" in out[0]["why"]
