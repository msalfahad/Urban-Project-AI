"""DOORWAY OVERLAP CHECK V1 (T-460 item 3, research, unwired): does a wet room's doorway waterproofing piece overlap its
floor membrane (FIN.WP.FLOOR) or its wall upturn (FIN.WP.WALL_UPTURN)?

PHYSICAL ELEMENTS (UP-WP-001 .. 003, Q-35 C):
    floor membrane   the room's floor face, bounded by the room-side faces of its walls and the closures of its openings
    doorway piece    the horizontal membrane in the door's wall thickness: door width x wall thickness (a band opening),
                     or the face between the door's two closures (leaf face and the wall's other face)
    wall upturn      0.20 m up the walls ONLY (Q-35 C: walls only, plus one doorway transition per physical door): the
                     door width is not in the upturn run
One square metre of membrane belongs to one of them. The floor and a doorway piece overlap only if the floor face runs
into the wall thickness (a room face drawn to the wall's far face, or a doorway face that is also a cell of the room).

    band_box_overlap(space_polygon, holes, opening, unit_m) -> {"box_m2", "overlap_m2"}
    face_overlap(space_polygon, holes, face_polygon, unit_m) -> overlap m2
    upturn_check(perimeter_lm, door_lm, upturn_h_m, line_m2) -> {"walls_only_m2", "with_doors_m2", "state"}
State per pair: NO_OVERLAP (overlap <= TOL_M2), OVERLAP (a double count of that many m2; the doorway piece is already in
the floor face). Stdlib + shapely (the engine's own dependency). Mirrored / rotated / mm / m plans read alike.
"""

from __future__ import annotations

from shapely.geometry import Polygon

POLICY = "DOORWAY_OVERLAP_CHECK_V1"
RULES = ("UP-WP-001", "UP-WP-002", "UP-WP-003", "Q-35")
TOL_M2 = 1e-4                # 1 cm2: numerical coincidence of shared edges, never a drafting allowance


def _poly(ring, holes=None):
    return Polygon(ring, holes or None).buffer(0)


def band_box(opening):
    (ux, uy), (nx, ny) = opening["u"], opening["n"]
    return [(ux * s + nx * t, uy * s + ny * t) for s, t in ((opening["s0"], opening["o0"]), (opening["s1"], opening["o0"]),
                                                          (opening["s1"], opening["o1"]), (opening["s0"], opening["o1"]))]


def band_box_overlap(space_polygon, holes, opening, unit_m):
    P = _poly(space_polygon, holes)
    B = _poly(band_box(opening))
    ov = P.intersection(B).area * unit_m * unit_m
    return {"box_m2": round(B.area * unit_m * unit_m, 6), "overlap_m2": round(ov, 6),
            "state": "OVERLAP" if ov > TOL_M2 else "NO_OVERLAP"}


def face_overlap(space_polygon, holes, face_polygon, unit_m):
    ov = _poly(space_polygon, holes).intersection(_poly(face_polygon)).area * unit_m * unit_m
    return {"overlap_m2": round(ov, 6), "state": "OVERLAP" if ov > TOL_M2 else "NO_OVERLAP"}


def upturn_check(perimeter_lm, door_lm, upturn_h_m, line_m2, tol_m2=5e-4):
    """the candidate upturn line against the walls-only reading (Q-35 C) and the with-doors reading (the double count
    with the doorway transition); None anywhere -> HELD"""
    if None in (perimeter_lm, door_lm, upturn_h_m, line_m2):
        return {"walls_only_m2": None, "with_doors_m2": None, "state": "HELD"}
    wo = (perimeter_lm - door_lm) * upturn_h_m
    wd = perimeter_lm * upturn_h_m
    if abs(line_m2 - wo) <= tol_m2:
        st = "WALLS_ONLY"
    elif abs(line_m2 - wd) <= tol_m2 and door_lm > 0:
        st = "DOORS_INCLUDED_DOUBLE_WITH_TRANSITION"
    else:
        st = "NEITHER"
    return {"walls_only_m2": round(wo, 6), "with_doors_m2": round(wd, 6), "state": st}
