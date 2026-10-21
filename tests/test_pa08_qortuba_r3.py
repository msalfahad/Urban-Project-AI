"""PA08-QORTUBA-R3: floor-finish MEASUREMENT regions, on synthetic geometry carrying none of Qortuba's coordinates.

The rules under test separate two questions a quantity surveyor must never merge: where a floor stops, and what the thing
standing there is made of.  Each fixture checks one direction of that separation, and the closure contract is checked
explicitly: a measurement closure must never become a wall.
"""

from __future__ import annotations

import math

from engine.ingest import band_topology as BT, material_bands as MB, planar_faces as PF
from research.qs_wall_treatment_01.pa08.qortuba.r2 import cells as CELLS
from research.qs_wall_treatment_01.pa08.qortuba.r3 import floor_regions as FR
from tests import pa07_fixtures as F
from tests.test_pa08_qortuba_r2 import _Result, text, of

BOX = (-2000, -2000, 14000, 14000)


def build(prims, texts=()):
    r = _Result(prims, texts, BOX)
    rows, meta = CELLS.build(r, "VW-t")
    cls_of = {c["FACE_ID"]: c["SPACE_ELIGIBILITY"] for c in rows}
    comp, nf = FR.measurement_components(r, "VW-t")
    return r, rows, cls_of, comp, nf


def region_of(r, rows, cls_of, comp, nf, pred):
    c = of(rows, pred)
    labels, crossings = FR.assemble(r, "VW-t", c["FACE_ID"], cls_of, comp, nf)
    segs, summ = FR.boundary_segments(r, "VW-t", labels)
    area, fml = FR.polygon(r, "VW-t", labels, sorted({s["SEAL_INDEX"] for s in segs if s["COUNTS_AS_PERIMETER"]}), nf)
    return c, labels, crossings, segs, summ, area, fml


# ------------------------------------------------------------------ a doorway does not stop a floor from being measured
def test_a_room_with_a_door_still_has_a_measurable_floor_region():
    F.reset()
    t = 150.0
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (5100, 4000), t) + F.cap((0, 4000), (5100, 4000), t, "end")
    prims += [F.seg("D", (5150, 4075), (5150, 4075 + 800), block=("DOOR",))]
    prims += F.rect(5100, 3925, 5160, 4075, "D", block=("DOOR",))
    r, rows, cls_of, comp, nf = build(prims, [text("BED.ROOM", 3000, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 3000, 6000, "ROOM_NAME", "CORRIDOR")])
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    assert area is not None and summ["ALL_SEGMENTS_FIX_THE_FLOOR_LINE"], (area, summ)
    thresholds = [s for s in segs if s["BOUNDARY_BASIS"] == "THRESHOLD_CLOSURE"]
    assert thresholds, [s["BOUNDARY_BASIS"] for s in segs]
    assert abs(area - 6.0 * 4.0) < 0.6, area


def test_a_wall_whose_material_role_is_unresolved_still_fixes_the_floor_line():
    F.reset()
    # a 120 mm partition: too thin for the material guard, so the band stays UNRESOLVED - but both its faces are drawn
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (6000, 4000), 120, layer="P")
    r, rows, cls_of, comp, nf = build(prims, [text("BED.ROOM", 3000, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 3000, 6000, "ROOM_NAME", "CORRIDOR")])
    part = [b for b in r.bands7["VW-t"] if abs(b["THK"] - 120) < 1]
    assert part and part[0]["STATUS"] != "ACCEPTED", "the fixture needs a band whose material role is NOT established"
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    assert area is not None and summ["ALL_SEGMENTS_FIX_THE_FLOOR_LINE"], (area, summ["BY_BASIS_PERIMETER_CELLS"])
    assert "CAD_FACE_LINE_UNRESOLVED_ROLE" in summ["BY_BASIS_PERIMETER_CELLS"]


def test_an_unpaired_line_with_no_thickness_evidence_does_not_fix_the_floor_line():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + [F.seg("FURN", (0, 4000), (6000, 4000))]
    r, rows, cls_of, comp, nf = build(prims, [text("MAJLIS", 3000, 2000, "ROOM_NAME", "LIVING")])
    seals = r.seals["VW-t"]
    bands_by = {b["BAND_ID"]: b for b in r.bands7["VW-t"]}
    sites_by = {s["SITE_ID"]: s for s in r.sites7["VW-t"]}
    unpaired = [s for s in seals if FR.seal_basis(s, bands_by, sites_by)[0] == "UNPAIRED_LINE_NO_THICKNESS_EVIDENCE"]
    assert unpaired, "the fixture needs an unpaired wall-to-wall line"
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["MAJLIS"])
    assert len(labels) >= 2, "the region must be assembled across the line with no thickness evidence"
    assert any(x["MERGED"] for x in cross) and all(x["REVERSIBLE"] for x in cross)
    assert area is not None and abs(area - 48.0) < 1.0, area


def test_a_measurement_closure_is_never_a_wall():
    F.reset()
    t = 150.0
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (5100, 4000), t) + F.cap((0, 4000), (5100, 4000), t, "end")
    prims += [F.seg("D", (5150, 4075), (5150, 4875), block=("DOOR",))] + F.rect(5100, 3925, 5160, 4075, "D", block=("DOOR",))
    r, rows, cls_of, comp, nf = build(prims, [text("BED.ROOM", 3000, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 3000, 6000, "ROOM_NAME", "CORRIDOR")])
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    for s in segs:
        if s["BOUNDARY_BASIS"] in ("THRESHOLD_CLOSURE", "OPEN_EDGE_CLOSURE"):
            assert not s["MATERIAL_PRESENT"] and not s["PHYSICAL_WALL"] and not s["GEOMETRY_AUTHORITY"] and s["REVERSIBLE"], s
    # and the physical layer is untouched: no band gained material status from the measurement
    assert all(b["STATUS"] in ("ACCEPTED", "REJECTED", "UNRESOLVED") for b in r.bands7["VW-t"])


def test_floor_certainty_does_not_promote_the_wall_beside_it():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (6000, 4000), 120, layer="P")
    r, rows, cls_of, comp, nf = build(prims, [text("BED.ROOM", 3000, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 3000, 6000, "ROOM_NAME", "CORRIDOR")])
    before = {b["KEY"]: b["STATUS"] for b in r.bands7["VW-t"]}
    region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    after = {b["KEY"]: b["STATUS"] for b in r.bands7["VW-t"]}
    assert before == after, "measuring a floor must not change any band's material status"


def test_another_room_is_never_absorbed_into_a_measurement_region():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + [F.seg("FURN", (0, 4000), (6000, 4000))]
    r, rows, cls_of, comp, nf = build(prims, [text("BED.ROOM", 3000, 2000, "ROOM_NAME", "BEDROOM"), text("HALL", 3000, 6000, "ROOM_NAME", "CORRIDOR")])
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    conflicts = [x for x in cross if not x["MERGED"]]
    other = of(rows, lambda x: x["ROOM_NAMES"] == ["HALL"])
    assert other["FACE_ID"] not in [x["TO_FACE_ID"] for x in cross if x["MERGED"]]
    if conflicts:
        assert all(x["REVERSIBLE"] for x in conflicts)


def test_the_polygon_is_cross_checked_against_the_raster_and_refuses_on_disagreement():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200)
    r, rows, cls_of, comp, nf = build(prims, [text("MAJLIS", 3000, 4000, "ROOM_NAME", "LIVING")])
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["MAJLIS"])
    assert fml["STATUS"] == "COMPUTED" and abs(area - 48.0) < 1e-6, (area, fml)
    assert "RASTER_CROSS_CHECK_M2" in fml and abs(fml["DIFFERENCE_M2"]) <= fml["TOLERANCE_M2"]
    assert fml["RECTANGLES"] and fml["FORMULA"].endswith("m2")


def test_a_curved_bounding_line_is_reported_not_silently_ignored():
    F.reset()
    prims = F.room(0, 0, 8000, 8000, 200) + F.curved_wall((4000, 4000), 1500, 200, 0.0, 2 * math.pi)
    r, rows, cls_of, comp, nf = build(prims, [text("MAJLIS", 1000, 1000, "ROOM_NAME", "LIVING")])
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["MAJLIS"])
    assert fml.get("SKEW_SEGMENTS_IGNORED") or fml.get("STATUS") == "NOT_ESTABLISHED", fml.get("STATUS")


def test_every_boundary_segment_declares_its_basis_and_its_authority():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (6000, 4000), 150)
    r, rows, cls_of, comp, nf = build(prims, [text("BED.ROOM", 3000, 2000, "ROOM_NAME", "BEDROOM")])
    c, labels, cross, segs, summ, area, fml = region_of(r, rows, cls_of, comp, nf, lambda x: x["ROOM_NAMES"] == ["BED.ROOM"])
    assert segs
    for s in segs:
        assert s["BOUNDARY_BASIS"] in FR.FLOOR_BOUNDARY_BASES + FR.NON_FLOOR_BOUNDARY_BASES
        assert isinstance(s["FIXES_WHERE_THE_FLOOR_STOPS"], bool)
        assert s["WHY"] and len(s["WHY"]) > 15
        assert s["SEGMENT_ROLE"] in ("BOUNDARY", "INTERIOR_OBSTRUCTION")
        if s["PHYSICAL_WALL"]:
            assert s["BOUNDARY_BASIS"] == "ESTABLISHED_WALL_FACE"
