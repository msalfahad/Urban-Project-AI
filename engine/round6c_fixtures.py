"""Round 6C — fourteen drawings about what a polygon IS.

Round 6B measured geometry well enough to be dangerous: 69 polygons, of
which some are rooms, some are halves of rooms, some are whole floor
plates containing other polygons, one is a title strip repeated on every
sheet, and one is the 900 mm gap a cabinet leaves against a wall — with a
room label sitting in it. Added up they make a number that means nothing.

These fourteen drawings are the difference:

    A  a room label inside the room it names
    B  a room label standing in the units fitted along two of its walls
    C  a room label inside a decorative rectangle drawn in the room
    D  a super-region containing three valid rooms
    E  a staircase drawn as many closed cells
    F  the same sheet strip repeated in three drawing regions
    G  a floor plan and an elevation on one sheet
    H  a floor plan and a site plan on one sheet
    I  a room with correct geometry and no name
    J  a name with no room boundary under it
    K  one label claimed by two candidates, neither inside the other
    L  two labels inside one legitimate open space
    M  one open space with two functional zones in it
    N  a parent and its children may never both release

Cases B, C, E, F, G, H, J and K exist to be REFUSED, and every drawing
carries its own title text so the drawing-role gate is exercised rather
than assumed. No coordinate in this file comes from any real project.

Cases K and N are REGISTER cases, not drawings. Two candidates that
overlap without either containing the other, and a plate that contains
three rooms, both arise from real decodes — P7757 has both — and neither
can be drawn on purpose without drawing the enclosure engine's own
failure instead. So K and N build register rows directly: their `decode`
is None and their `rows` are their drawing.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

from engine import round4_fixtures as r4
from engine.cad_fixtures import Builder

W, D, G, TXT = r4.W, r4.D, r4.G, r4.TXT

# Two drawings on one sheet are this far apart. Wider than any single
# plan in this file, so the clustering separates them at every rung of
# its ladder rather than at one chosen distance.
SHEET_STEP_MM = 200000.0

TITLE_H = 600.0      # a title is drawn bigger than the stamps it titles


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict = None
    expect: dict = field(default_factory=dict)
    rows: tuple = ()          # case K: a register built directly


# ------------------------------------------------------------- drawing kit

def _shell(b, ox, oy, w, h, *, t=200.0, door=True):
    openings = [("S", ox + w / 2 - 450, ox + w / 2 + 450)] if door else []
    r4._ring(b, ox, oy, ox + w, oy + h, layer=W, t=t, openings=openings)
    if door:
        r4._door(b, f"DENT{int(ox)}", ox + w / 2 - 450, oy, 900,
                 rotation=math.pi / 2)


def _title(b, text, x, y, height=TITLE_H):
    """A sheet title: one string, bigger than the room stamps under it."""
    b.text(text, x, y, height, TXT)


def _counter(b, axis, face, lo, hi, depth, *, layer=W):
    """A fitting standing ON a wall face: one line, and one return.

    It shares the wall's own face line, stands on the room side of it,
    and runs part of the wall's length — which is what a worktop, a
    wardrobe and a bath panel all do.
    """
    r4._emit(b, axis, face + depth, lo, hi, layer)
    cross = "V" if axis == "H" else "H"
    f0, f1 = min(face, face + depth), max(face, face + depth)
    r4._emit(b, cross, hi, f0, f1, layer)


def _box(b, x0, y0, x1, y1, layer):
    r4._emit(b, "H", y0, x0, x1, layer)
    r4._emit(b, "H", y1, x0, x1, layer)
    r4._emit(b, "V", x0, y0, y1, layer)
    r4._emit(b, "V", x1, y0, y1, layer)


# ------------------------------------------------------------------- cases

def _a():
    """A room label inside the room it names."""
    b = Builder()
    _shell(b, 0, 0, 9000, 5000)
    r4._partition_v(b, 4500, 0, 5000, t=200.0, gaps=[(2000, 2900)])
    r4._door(b, "DA", 4500, 2000, 900)
    r4._stamp(b, "S1", ["BEDROOM"], 2200, 2500)
    r4._stamp(b, "S2", ["STORE"], 6800, 2500)
    _title(b, "GROUND FLOOR PLAN", 1000, -500)
    return Case(
        "A_A_LABEL_INSIDE_THE_ROOM_IT_NAMES",
        "the ordinary case, and the floor it belongs to",
        b.build(),
        expect={"labels_map_to_area_m2": {"BEDROOM": 4.5 * 5.0,
                                          "STORE": 4.3 * 5.0},
                "floors": ["GROUND"],
                "regions_that_may_release_at_least": 1})


def _b():
    """The label sits in the strip two counters close off against a wall."""
    b = Builder()
    _shell(b, 0, 0, 6000, 6000)
    r4._partition_v(b, 1000, 0, 6000, t=200.0, gaps=[(4000, 4900)])
    r4._door(b, "DA", 1000, 4000, 900)
    r4._partition_h(b, 3000, 1200, 6000, t=200.0, gaps=[(4600, 5500)])
    r4._door(b, "DB", 4600, 3000, 900, rotation=math.pi / 2)
    # a 500 mm run of units against the partition, and a 500 mm worktop
    # against the cross wall: between their two FRONT faces they close a
    # cell that no wall of the building closes
    _counter(b, "V", 1200.0, 0.0, 2500.0, 500.0)
    _counter(b, "H", 3000.0, 1200.0, 4000.0, -500.0)
    r4._stamp(b, "S1", ["PANTRY"], 3000, 1200)
    r4._stamp(b, "S2", ["KITCHEN"], 3000, 4500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "B_A_LABEL_IN_THE_STRIP_A_COUNTER_LEAVES",
        "a label standing in the units names the room, measured through "
        "them to the walls behind",
        b.build(),
        expect={"labels_map_to_area_m2": {"PANTRY": 4.8 * 3.0,
                                          "KITCHEN": 4.8 * 2.8},
                "a_fitting_strip_is_never_a_room": True,
                "no_release_of_a_fitting_strip": True})


def _c():
    """A decorative rectangle drawn inside the room, with the label in it."""
    b = Builder()
    _shell(b, 0, 0, 6000, 5000)
    _box(b, 2000, 2000, 3200, 2800, "ANNO")
    r4._stamp(b, "S1", ["MAJLIS"], 2600, 2400)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "C_A_LABEL_INSIDE_A_DECORATIVE_RECTANGLE",
        "a rectangle drawn in a room is not the room, and not a room",
        b.build(),
        expect={"labels_map_to_area_m2": {"MAJLIS": 6.0 * 5.0},
                "no_release_below_m2": 2.0})


def _d():
    """One floor plate containing three properly walled rooms."""
    b = Builder()
    _shell(b, 0, 0, 12000, 6000)
    r4._partition_v(b, 4000, 0, 6000, t=200.0, gaps=[(1200, 2100)])
    r4._door(b, "DA", 4000, 1200, 900)
    r4._partition_v(b, 8000, 0, 6000, t=200.0, gaps=[(3600, 4500)])
    r4._door(b, "DB", 8000, 3600, 900)
    r4._stamp(b, "S1", ["BED ONE"], 2000, 3000)
    r4._stamp(b, "S2", ["BED TWO"], 6000, 3000)
    r4._stamp(b, "S3", ["BED THREE"], 10000, 3000)
    _title(b, "FIRST FLOOR PLAN", 1000, -500)
    return Case(
        "D_A_SUPER_REGION_HOLDING_THREE_ROOMS",
        "the plate that holds three rooms is not a fourth room",
        b.build(),
        expect={"floors": ["FIRST"],
                "labels_map_to_area_m2": {"BED ONE": 4.0 * 6.0,
                                          "BED TWO": 3.8 * 6.0,
                                          "BED THREE": 3.8 * 6.0},
                "released_area_never_exceeds_m2": 12.0 * 6.0})


def _e():
    """A staircase drawn as ten closed tread cells."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    r4._partition_v(b, 3000, 0, 6000, t=200.0, gaps=[(4600, 5500)])
    r4._door(b, "DA", 3000, 4600, 900)
    for i in range(1, 10):
        r4._emit(b, "H", i * 400.0, 0.0, 3000.0, W)
    r4._stamp(b, "S1", ["STAIR"], 1500, 1800)
    r4._stamp(b, "S2", ["LOBBY"], 6000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "E_A_STAIRCASE_DRAWN_AS_MANY_CELLS",
        "nine treads are not nine rooms, and not nine released areas",
        b.build(),
        expect={"no_release_below_m2": 2.0,
                "released_candidates_at_most": 1,
                "a_stair_releases_no_room_area": True})


def _f():
    """The same sheet strip drawn in three drawing regions."""
    b = Builder()
    for k in range(3):
        ox = k * SHEET_STEP_MM
        _shell(b, ox, 0, 8000, 5000)
        r4._stamp(b, f"S{k}", ["SALOON"], ox + 4000, 2500)
        _title(b, "GROUND FLOOR PLAN", ox + 500, -500)
        # a title strip, at the SAME place relative to its own region
        _box(b, ox + 0.0, -8000.0, ox + 8000.0, -6000.0, "SHEET")
    return Case(
        "F_ONE_SHEET_STRIP_REPEATED_IN_THREE_REGIONS",
        "geometry in the same place on every sheet is the sheet",
        b.build(),
        expect={"drawing_artifacts_at_least": 3,
                "repeated_geometry_groups_at_least": 1,
                "no_release_of_repeated_geometry": True})


def _g():
    """A floor plan and an elevation, on one sheet."""
    b = Builder()
    _shell(b, 0, 0, 9000, 5000)
    r4._stamp(b, "S1", ["SALOON"], 4500, 2500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    ox = SHEET_STEP_MM
    # an elevation: an outline, a roof line, three window rectangles, and
    # not one thing enclosed by a wall band
    _box(b, ox, 0, ox + 9000, 7000, "ELEV")
    r4._emit(b, "H", 5600.0, ox, ox + 9000.0, "ELEV")
    for i in range(3):
        _box(b, ox + 1500 + i * 2500, 2000, ox + 2700 + i * 2500, 3600,
             "ELEV")
    _title(b, "FRONT ELEVATION", ox + 500, -500)
    return Case(
        "G_A_FLOOR_PLAN_AND_AN_ELEVATION",
        "an elevation releases no rooms, whatever closes on it",
        b.build(),
        expect={"roles_present": ["FLOOR_PLAN", "ELEVATION"],
                "regions_that_may_release_exactly": 1,
                "no_release_outside_a_plan": True})


def _h():
    """A floor plan and a site plan, on one sheet."""
    b = Builder()
    _shell(b, 0, 0, 9000, 5000)
    r4._stamp(b, "S1", ["SALOON"], 4500, 2500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    ox = SHEET_STEP_MM
    r4._ring(b, ox, 0, ox + 40000, 30000, layer="PLOT",
             openings=[("S", ox + 18000, ox + 22000)])
    r4._ring(b, ox + 10000, 8000, ox + 26000, 20000)
    r4._stamp(b, "S2", ["VILLA"], ox + 18000, 14000)
    _title(b, "SITE PLAN", ox + 500, -500)
    return Case(
        "H_A_FLOOR_PLAN_AND_A_SITE_PLAN",
        "a plot is not a floor, and its fabric is not this floor's rooms",
        b.build(),
        expect={"roles_present": ["FLOOR_PLAN", "SITE_PLAN"],
                "regions_that_may_release_exactly": 1,
                "no_release_outside_a_plan": True})


def _i():
    """A room with correct geometry and nothing naming it."""
    b = Builder()
    _shell(b, 0, 0, 7000, 4000)
    r4._partition_v(b, 3000, 0, 4000, t=200.0, gaps=[(1500, 2400)])
    r4._door(b, "DA", 3000, 1500, 900)
    r4._stamp(b, "S1", ["MAJLIS"], 1500, 2000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "I_GEOMETRY_ESTABLISHED_IDENTITY_UNKNOWN",
        "an unnamed room is a space of the building, and stays unnamed",
        b.build(),
        expect={"unidentified_spaces_at_least": 1,
                "labels_map_to_area_m2": {"MAJLIS": 3.0 * 4.0}})


def _j():
    """A name with no room boundary under it."""
    b = Builder()
    _shell(b, 0, 0, 6000, 4000)
    r4._stamp(b, "S1", ["SALOON"], 3000, 2000)
    # a name out on the sheet, where nothing is enclosed
    r4._stamp(b, "S2", ["STORE"], 3000, -1500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "J_A_NAME_WITH_NO_ROOM_UNDER_IT",
        "no polygon under a label is an exception, never a nearest room",
        b.build(),
        expect={"labels_unresolved": ["STORE"],
                "labels_map_to_area_m2": {"SALOON": 6.0 * 4.0}})


def _k():
    """Two candidates claim one label and neither is inside the other.

    Built as register rows rather than as a drawing: this is a statement
    about the reconciliation rule, and forcing a decode to produce two
    genuinely overlapping candidates would be a drawing about the
    enclosure engine instead.
    """
    from shapely.geometry import box

    rows = (
        {"space_id": "PS-X-001", "region_id": "DR-X",
         "polygon": box(0, 0, 6000, 4000), "area_m2": 24.0,
         "basis": "CLEAR_INTERNAL_FINISH_FACE", "label_raw": "",
         "principal_dims_mm": [6000.0, 4000.0], "blockers": [],
         "release_status": "RELEASE_ELIGIBLE_GEOMETRY",
         "identity_authority": "", "geometry_authority": "",
         "normalized_identity": "", "wall_band_ids": [],
         "face_contacts": [], "cad_provenance": []},
        {"space_id": "PS-X-002", "region_id": "DR-X",
         "polygon": box(4000, 0, 10000, 4000), "area_m2": 24.0,
         "basis": "CLEAR_INTERNAL_FINISH_FACE", "label_raw": "",
         "principal_dims_mm": [6000.0, 4000.0], "blockers": [],
         "release_status": "RELEASE_ELIGIBLE_GEOMETRY",
         "identity_authority": "", "geometry_authority": "",
         "normalized_identity": "", "wall_band_ids": [],
         "face_contacts": [], "cad_provenance": []},
    )
    return Case(
        "K_ONE_LABEL_CLAIMED_BY_TWO_CANDIDATES",
        "neither contains the other, so neither may take the label",
        None,
        expect={"labels_unresolved": ["DINING"],
                "label_at_mm": [5000.0, 2000.0],
                "why": "SEVERAL_PHYSICAL_SPACES_CONTAIN_THIS_LABEL"},
        rows=rows)


def _l():
    """Two labels inside one legitimate open space."""
    b = Builder()
    _shell(b, 0, 0, 10000, 5000)
    r4._stamp(b, "S1", ["LIVING"], 2500, 2500)
    r4._stamp(b, "S2", ["DINING"], 7500, 2500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "L_TWO_LABELS_IN_ONE_OPEN_SPACE",
        "one space claimed by two names is reported, never split in two",
        b.build(),
        expect={"one_space_claimed_by_labels_at_least": 2,
                "released_candidates_at_most": 1,
                "released_area_never_exceeds_m2": 10.0 * 5.0})


def _m():
    """One open space with two functional zones drawn in it."""
    b = Builder()
    _shell(b, 0, 0, 10000, 5000)
    # a kitchenette along the north wall of an open plan: a fitting, not
    # a room, and not a second space
    _counter(b, "H", 5000.0, 6000.0, 9000.0, -600.0)
    r4._stamp(b, "S1", ["LIVING"], 2500, 2500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "M_ONE_SPACE_WITH_TWO_FUNCTIONAL_ZONES",
        "round 6C registers spaces. It does not cut them into zones",
        b.build(),
        expect={"released_candidates_at_most": 1,
                "no_functional_zone_is_emitted": True})


def _n():
    """A plate and the three rooms inside it, as register rows.

    A super-region only exists when a candidate CONTAINS candidates that
    are themselves spaces, and a drawing whose partitions close properly
    never produces one — the flood cannot walk the plate. P7757 does
    produce them, through doorways the flood walks, so the rule is real
    and it is tested where it can be stated exactly: on the register.
    """
    from shapely.geometry import box

    def _row(n, poly, label):
        return {"space_id": f"PS-Y-{n:03d}", "region_id": "DR-Y",
                "polygon": poly, "area_m2": round(poly.area / 1e6, 4),
                "basis": "CLEAR_INTERNAL_FINISH_FACE", "label_raw": label,
                "principal_dims_mm": [], "blockers": [],
                "release_status": "RELEASE_ELIGIBLE_GEOMETRY",
                "identity_authority": "IDENTITY_ESTABLISHED",
                "geometry_authority": "MEASUREMENT_COMPLETE",
                "normalized_identity": label, "wall_band_ids": [],
                "face_contacts": [], "cad_provenance": []}

    rows = (
        _row(1, box(0, 0, 12000, 6000), ""),
        _row(2, box(0, 0, 4000, 6000), "BED ONE"),
        _row(3, box(4200, 0, 8000, 6000), "BED TWO"),
        _row(4, box(8200, 0, 12000, 6000), "BED THREE"),
    )
    return Case(
        "N_A_PARENT_AND_A_CHILD_NEVER_BOTH_RELEASE",
        "a floor counted twice is a floor's worth of ceramic too many",
        None,
        expect={"super_regions_at_least": 1,
                "released_candidates_at_most": 3,
                "released_area_never_exceeds_m2": 24.0 + 22.8 + 22.8,
                "no_parent_releases_with_a_child": True},
        rows=rows)


def cases() -> list:
    return [_a(), _b(), _c(), _d(), _e(), _f(), _g(), _h(), _i(), _j(),
            _k(), _l(), _m(), _n()]


def freeze_hash() -> str:
    rows = [f"{c.name}|{c.what_it_tests}|{sorted(c.expect)}"
            for c in cases()]
    return hashlib.sha256("|".join(rows).encode("utf-8")).hexdigest()[:24]
