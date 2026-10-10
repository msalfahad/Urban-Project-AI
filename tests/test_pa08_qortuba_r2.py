"""PA08-QORTUBA-R2: cell forensics and free-space eligibility, on synthetic geometry that carries none of Qortuba's coordinates.

The rules under test decide which raster cells are real floor-finish space and which are the interior of some element.  Each
fixture is written so that AREA ALONE would give the wrong answer: a real 0.8 m2 water closet must survive, and a 5 m2
drafting enclosure must not.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

from engine.ingest import band_topology as BT, junctions as JN, material_bands as MB, planar_faces as PF
from research.qs_wall_treatment_01.pa08.qortuba.r2 import cells as CELLS
from tests import pa07_fixtures as F

BOX = (-2000, -2000, 14000, 14000)


class _Result:
    """The slice of a pipeline result the R2 classifier reads."""

    def __init__(self, prims, texts=(), box=BOX):
        roles = F.roles_of(prims)
        rows, bands = MB.build("VW-t", prims, roles, view_bbox=box)
        intervals, sites, seals = BT.build_view("VW-t", prims, roles, bands)
        faces, grid = PF.build("VW-t", box, seals, bands, texts)
        brows = PF.boundary_faces("VW-t", faces, grid, bands, intervals, seals)
        spaces = PF.space_register("VW-t", faces, brows)
        self.views = [{"VIEW_ID": "VW-t", "PRIMITIVES": prims, "BBOX_MM": box, "TEXTS": texts}]
        self.faces, self.grids7, self.seals, self.bands7 = {"VW-t": faces}, {"VW-t": grid}, {"VW-t": seals}, {"VW-t": bands}
        self.spaces, self.brows, self.sites7, self.roles = {"VW-t": spaces}, {"VW-t": brows}, {"VW-t": sites}, {"VW-t": roles}
        self.registers = {}


def classify(prims, texts=()):
    r = _Result(prims, texts)
    rows, meta = CELLS.build(r, "VW-t")
    return r, rows, meta


def text(t, x, y, role="ROOM_NAME", cls=None):
    return {"TEXT": t, "X": float(x), "Y": float(y), "ROLE": role, "CLASS": cls}


def of(rows, pred):
    hits = [x for x in rows if pred(x)]
    assert hits, [(x["AREA_M2"], x["SPACE_ELIGIBILITY"], x["ROOM_NAMES"]) for x in rows]
    return hits[0]


# ------------------------------------------------------------------ area alone must not decide
def test_a_small_labelled_wc_survives_and_a_large_unlabelled_enclosure_does_not():
    F.reset()
    # a 900 x 900 water closet (0.81 m2) walled on all four sides, opening into a big room through a door
    prims = F.room(0, 0, 9000, 6000, 200)
    prims += F.wall((0, 1500), (1000, 1500), 150) + F.wall((1000, 0), (1000, 1500), 150) + F.cap((0, 1500), (1000, 1500), 150, "end")
    prims += [F.seg("D", (1075, 950), (1075, 950 + 840), block=("DOOR",))]
    prims += F.rect(1000, 900, 1075, 1000, "D", block=("DOOR",))
    r, rows, meta = classify(prims, [text("W.C", 450, 700, "ROOM_NAME", "WC"), text("MAJLIS", 5000, 4000, "ROOM_NAME", "LIVING")])
    wc = of(rows, lambda x: any("W.C" in (n or "") for n in x["ROOM_NAMES"]))
    assert wc["AREA_M2"] < 1.5, wc["AREA_M2"]
    assert wc["MAY_BECOME_FLOOR_REGION"] and wc["SPACE_ELIGIBILITY"] in ("SERVICE_FREE_SPACE", "OCCUPIABLE_FREE_SPACE"), (wc["SPACE_ELIGIBILITY"], wc["REASON"])
    assert "area" not in wc["REASON"].lower() or "m2" in wc["REASON"], "the reason must name evidence, never a size threshold"


def test_a_five_square_metre_unlabelled_chord_enclosure_is_not_a_floor_region():
    F.reset()
    # a big room whose corner is fenced off by an UNRESOLVED thin pair: the enclosed 5 m2 carries no label and no material boundary
    prims = F.room(0, 0, 9000, 6000, 200) + F.wall((0, 2500), (2000, 2500), 120, layer="P") + F.wall((2000, 0), (2000, 2500), 120, layer="P")
    r, rows, meta = classify(prims, [text("MAJLIS", 6000, 4000, "ROOM_NAME", "LIVING")])
    pocket = of(rows, lambda x: not x["ROOM_NAMES"] and x["AREA_M2"] > 3)
    assert not pocket["MAY_BECOME_FLOOR_REGION"], (pocket["AREA_M2"], pocket["SPACE_ELIGIBILITY"], pocket["REASON"])
    assert pocket["SPACE_ELIGIBILITY"] in ("ARTIFACT_POCKET", "UNRESOLVED")


# ------------------------------------------------------------------ an element's interior is never floor
def test_the_interior_of_an_unresolved_wall_strip_is_that_wall_not_a_room():
    F.reset()
    prims = F.room(0, 0, 9000, 6000, 200) + F.wall((0, 3000), (9000, 3000), 120, layer="P")
    r, rows, meta = classify(prims)
    strip = of(rows, lambda x: x["IS_INSIDE_WALL_BAND"] or x["IS_FRAME_INTERIOR"])
    assert not strip["MAY_BECOME_FLOOR_REGION"]
    assert strip["HOST_ELEMENT"] and strip["INTERIOR_PROBES_IN_A_STRIP"] == strip["INTERIOR_PROBES"]
    assert "interior" in strip["REASON"]


def test_a_closed_outline_interior_is_joinery_not_floor():
    F.reset()
    t = 150.0
    prims = F.room(0, 0, 9000, 6000, t) + F.wall((0, 3000), (2000, 3000), t) + F.cap((0, 3000), (2000, 3000), t, "end")
    prims += F.wall((3900, 3000), (9000, 3000), t) + F.cap((3900, 3000), (9000, 3000), t, "start") + F.rect(2000, 2650, 3900, 3350, "W")
    r, rows, meta = classify(prims)
    inner = of(rows, lambda x: x["IS_FURNITURE_OR_CASEWORK_INTERIOR"])
    assert not inner["MAY_BECOME_FLOOR_REGION"] and inner["SPACE_ELIGIBILITY"] == "JOINERY_OR_FURNITURE_INTERIOR"


def test_stair_tread_pockets_are_stair_components():
    F.reset()
    prims = F.room(0, 0, 9000, 6000, 200)
    for k in range(9):                                   # a flight of tread lines across a 1200 mm wide stair
        prims.append(F.seg("STAIR", (6000, 500 + k * 300), (7200, 500 + k * 300)))
    prims += [F.seg("STAIR", (6000, 500), (6000, 2900)), F.seg("STAIR", (7200, 500), (7200, 2900))]
    r, rows, meta = classify(prims)
    stair = [x for x in rows if x["IS_STAIR_COMPONENT"]]
    assert stair, [(x["AREA_M2"], x["SPACE_ELIGIBILITY"]) for x in rows]
    assert all(not x["MAY_BECOME_FLOOR_REGION"] for x in stair)
    assert all(x["SPACE_ELIGIBILITY"] == "STAIR_OR_LANDING_SPACE" for x in stair)


def test_a_sliver_narrower_than_the_thinnest_band_is_an_artifact_pocket():
    F.reset()
    prims = F.room(0, 0, 9000, 6000, 200) + F.wall((0, 3000), (9000, 3000), 200)
    prims += [F.seg("X", (2000, 3150), (5000, 3150)), F.seg("X", (2000, 3200), (5000, 3200))]
    r, rows, meta = classify(prims)
    assert meta["THINNEST_ACCEPTED_BAND_MM"] == 200.0
    thin = [x for x in rows if x["CLEAR_WIDTH_MM"] < meta["THINNEST_ACCEPTED_BAND_MM"] and not x["ROOM_NAMES"]]
    assert thin and all(not x["MAY_BECOME_FLOOR_REGION"] for x in thin)


# ------------------------------------------------------------------ sheet notes are not room labels
def test_a_sheet_note_does_not_make_a_region_a_room():
    F.reset()
    prims = F.room(0, 0, 9000, 6000, 200)
    r, rows, meta = classify(prims, [text("{\\fVineta BT|b0|i0;NEIGHBOUR\\P26.50 M}", 4500, 3000, "UNDECODABLE_TEXT"),
                                     text("LEVEL R.F = 4.00 m", 4500, 2000, "UNCLASSIFIED_TEXT")])
    inner = of(rows, lambda x: x["AREA_M2"] > 40)
    assert inner["ROOM_NAMES"] == [], inner["ROOM_NAMES"]


def test_a_keyboard_arabic_stamp_is_a_room_label():
    F.reset()
    prims = F.room(0, 0, 9000, 6000, 200)
    r, rows, meta = classify(prims, [text("whgm", 4500, 3000, "UNCLASSIFIED_TEXT")])
    inner = of(rows, lambda x: x["AREA_M2"] > 40)
    assert inner["ROOM_NAMES"] == ["whgm"] and inner["MAY_BECOME_FLOOR_REGION"]


# ------------------------------------------------------------------ room relations are read through the doorway cell
def test_two_rooms_joined_by_a_door_are_not_reported_as_a_solid_wall():
    F.reset()
    t = 150.0
    prims = F.room(0, 0, 9000, 8000, t) + F.wall((0, 4000), (4000, 4000), t) + F.cap((0, 4000), (4000, 4000), t, "end")
    prims += F.wall((4900, 4000), (9000, 4000), t) + F.cap((4900, 4000), (9000, 4000), t, "start")
    prims += [F.seg("D", (4050, 4075), (4050, 4075 + 840), block=("DOOR",))]
    prims += F.rect(4000, 3925, 4060, 4075, "D", block=("DOOR",)) + F.rect(4840, 3925, 4900, 4075, "D", block=("DOOR",))
    r, rows, meta = classify(prims, [text("BED.ROOM", 4500, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 4500, 6000, "ROOM_NAME", "CORRIDOR")])
    adj = CELLS.room_adjacency(r, "VW-t", rows)
    a = of(rows, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    b = of(rows, lambda x: x["ROOM_NAMES"] == ["HALL"])
    rel = [z for z in adj if {z["ROOM_A"], z["ROOM_B"]} == {a["CELL_ID"], b["CELL_ID"]}]
    assert rel, [(z["ROOM_A"], z["ROOM_B"], z["RELATION"]) for z in adj]
    assert rel[0]["RELATION"] in ("SEPARATED_BY_DOOR", "SEPARATED_BY_OPENING"), rel[0]
    assert rel[0]["VIA"], "the relation must be read through the doorway cell, not from direct adjacency"


def test_two_rooms_with_a_solid_wall_between_them_stay_a_solid_wall():
    F.reset()
    prims = F.room(0, 0, 9000, 8000, 200) + F.wall((0, 4000), (9000, 4000), 200)
    r, rows, meta = classify(prims, [text("BED.ROOM", 4500, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 4500, 6000, "ROOM_NAME", "CORRIDOR")])
    adj = CELLS.room_adjacency(r, "VW-t", rows)
    a = of(rows, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    b = of(rows, lambda x: x["ROOM_NAMES"] == ["HALL"])
    rel = [z for z in adj if {z["ROOM_A"], z["ROOM_B"]} == {a["CELL_ID"], b["CELL_ID"]}]
    assert not rel or rel[0]["RELATION"] == "SEPARATED_BY_MATERIAL_WALL", rel


def test_every_row_carries_a_reason_and_a_class():
    F.reset()
    prims = F.room(0, 0, 9000, 6000, 200) + F.wall((0, 3000), (9000, 3000), 150)
    r, rows, meta = classify(prims, [text("BATH", 4500, 1500, "ROOM_NAME", "BATHROOM")])
    assert rows
    for x in rows:
        assert x["SPACE_ELIGIBILITY"] in CELLS.FREE_SPACE_CLASSES
        assert x["REASON"] and len(x["REASON"]) > 20
        assert x["STATUS"] in ("CLASSIFIED", "HUMAN_REVIEW")
        assert x["MAY_BECOME_FLOOR_REGION"] == (x["SPACE_ELIGIBILITY"] in CELLS.FLOOR_ELIGIBLE_CLASSES)
