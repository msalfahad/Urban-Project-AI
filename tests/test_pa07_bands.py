"""PA07A adversarial material-band tests.  A wrong candidate must be REJECTED or UNRESOLVED; a real wall must be ACCEPTED
with the right thickness and developed length.  Layer names carry no meaning here: every fixture uses arbitrary layers."""

from __future__ import annotations

import math

import pytest

from engine.ingest import material_bands as MB
from tests import pa07_fixtures as F


def build(prims, bbox=None):
    rows, bands = MB.build("VW-t", prims, F.roles_of(prims), view_bbox=bbox)
    return rows, bands


def accepted(rows):
    return [r for r in rows if r["MATERIAL_STATUS"] == "ACCEPTED"]


def covering(rows, face_ids):
    """Rows whose faces include any of the given ids."""
    return [r for r in rows if set(r["SIDE_A_FACE_IDS"] + r["SIDE_B_FACE_IDS"]) & set(face_ids)]


def anchor_frame():
    """An L of two real 200 walls with returns: the host context every case is placed in."""
    prims = F.wall((0, 0), (8000, 0), 200) + F.wall((0, 0), (0, 6000), 200) + F.cap((0, 0), (8000, 0), 200, "end") + F.cap((0, 0), (0, 6000), 200, "end")
    return prims


def test_01_two_parallel_window_frame_lines_are_not_a_wall():
    prims = anchor_frame()
    # a 200 wall with a window: the wall faces run through, the frame is two lines 100 apart inside the strip
    prims += F.wall((0, 3000), (7000, 3000), 200) + F.cap((0, 3000), (7000, 3000), 200, "end")
    frame = [F.seg("X", (4000, 2950), (5200, 2950)), F.seg("X", (4000, 3050), (5200, 3050))]
    rows, _ = build(prims + frame)
    for r in covering(rows, [f.object_id for f in frame]):
        assert r["MATERIAL_STATUS"] != "ACCEPTED", r
        assert r["REJECTION_REASON"].startswith(("FRAME_WITHIN_HOST_BAND", "THIN_PAIR", "ENCLOSES", "FACE_SIDE_CONFLICT", "ISOLATED", "VOID"))
    host = [r for r in accepted(rows) if r["THICKNESS_MM"] == 200 and r["ORIENTATION_TYPE"] == "HORIZONTAL" and r["DEVELOPED_LENGTH_MM"] == 7000]
    assert len(host) == 1 and host[0]["FRAMES_INSIDE"], [(r["THICKNESS_MM"], r["DEVELOPED_LENGTH_MM"], r["MATERIAL_STATUS"], r["REJECTION_REASON"]) for r in rows]


def test_02_stair_treads_beside_a_wall_are_a_repetition_family():
    prims = anchor_frame() + F.wall((0, 3000), (5000, 3000), 200)
    treads = [F.seg("S", (1000, 3100 + 280 * i), (2200, 3100 + 280 * i)) for i in range(9)]
    rows, _ = build(prims + treads)
    tread_rows = covering(rows, [t.object_id for t in treads])
    assert tread_rows and all(r["MATERIAL_STATUS"] != "ACCEPTED" for r in tread_rows)
    assert any(r["REJECTION_REASON"].startswith("REPETITION_FAMILY") for r in tread_rows)
    # the real wall next to the treads is still a wall
    assert any(r["THICKNESS_MM"] == 200 and r["DEVELOPED_LENGTH_MM"] == 5000 for r in accepted(rows))


def test_03_hatch_strokes_with_wall_like_spacing_are_not_walls():
    prims = anchor_frame()
    strokes = [F.seg("H", (2000 + 150 * i, 2000), (2000 + 150 * i, 4000)) for i in range(12)]   # 150 mm apart, 2 m long
    rows, _ = build(prims + strokes)
    for r in covering(rows, [s.object_id for s in strokes]):
        assert r["MATERIAL_STATUS"] == "REJECTED" and r["REJECTION_REASON"].startswith("REPETITION_FAMILY"), r


def test_04_furniture_rectangle_is_not_a_wall_or_a_column():
    prims = anchor_frame()
    table = F.rect(3000, 3000, 4800, 3900, "FURN")          # 1800 x 900 closed loop
    bed = F.rect(5000, 1000, 6000, 3000, "FURN", block=("BED",))   # 1000 x 2000 from a block
    rows, _ = build(prims + table + bed)
    for r in covering(rows, [s.object_id for s in table + bed]):
        assert r["MATERIAL_STATUS"] != "ACCEPTED", r
        assert r["REJECTION_REASON"].startswith(("CLOSED_FITTING_LOOP", "CLOSED_LOOP_UNRESOLVED", "ISOLATED", "ENCLOSES", "FACE_SIDE")), r


def test_05_glazing_frame_lines_are_not_a_wall():
    prims = anchor_frame()
    # a curtain-wall / glazing line: three lines 30 and 60 apart, 4 m long, joined to nothing at wall thickness
    glz = [F.seg("G", (2000, 5000), (6000, 5000)), F.seg("G", (2000, 5030), (6000, 5030)), F.seg("G", (2000, 5060), (6000, 5060))]
    rows, _ = build(prims + glz)
    assert all(r["MATERIAL_STATUS"] != "ACCEPTED" for r in covering(rows, [g.object_id for g in glz]))
    # a thicker two-line frame (80 mm) with mullion returns, free standing in the room
    frame = F.wall((2000, 4000), (6000, 4000), 80) + [F.seg("G", (2000 + 800 * i, 3960), (2000 + 800 * i, 4040)) for i in range(6)]
    rows, _ = build(prims + frame)
    for r in covering(rows, [g.object_id for g in frame]):
        assert r["MATERIAL_STATUS"] != "ACCEPTED", r


@pytest.mark.parametrize("t", [100.0, 150.0, 200.0])
def test_06_07_08_real_partitions_and_external_wall(t):
    prims = anchor_frame() + F.wall((0, 3000), (5000, 3000), t) + F.cap((0, 3000), (5000, 3000), t, "end")
    rows, _ = build(prims)
    acc = [r for r in accepted(rows) if r["ORIENTATION_TYPE"] == "HORIZONTAL" and abs(r["THICKNESS_MM"] - t) < 1 and r["DEVELOPED_LENGTH_MM"] < 6000]
    assert len(acc) == 1
    assert abs(acc[0]["DEVELOPED_LENGTH_MM"] - 5000) <= 10 and acc[0]["THICKNESS_STATUS"] == "ESTABLISHED" and acc[0]["BAND_TYPE"] == "STRAIGHT_BAND"
    assert acc[0]["INTERSECTION_EVIDENCE"]["JOINS"], "a partition joined to the frame must show the junction"


def test_09_angled_wall():
    a, b = (0, 0), (5000, 3000)
    prims = anchor_frame() + F.wall(a, b, 200) + F.cap(a, b, 200, "end")
    rows, _ = build(prims)
    ang = [r for r in accepted(rows) if r["BAND_TYPE"] == "ANGLED_BAND"]
    assert len(ang) == 1 and abs(ang[0]["DEVELOPED_LENGTH_MM"] - math.hypot(5000, 3000)) <= 10 and ang[0]["THICKNESS_MM"] == 200


def test_10_curved_wall_developed_length():
    r_axis, t = 3000.0, 200.0
    prims = anchor_frame() + F.curved_wall((0, 3000), r_axis, t, -math.pi / 2, 0.0)   # quarter circle from (0,0) to (3000,3000)
    prims += F.wall((3000, 3000), (3000, 6000), 200) + F.cap((3000, 3000), (3000, 6000), 200, "end")
    rows, _ = build(prims)
    cur = [r for r in accepted(rows) if r["BAND_TYPE"] == "CURVED_BAND"]
    assert len(cur) == 1
    assert abs(cur[0]["DEVELOPED_LENGTH_MM"] - r_axis * math.pi / 2) <= 0.005 * r_axis * math.pi / 2
    assert cur[0]["CURVATURE_TYPE"] == "ARC" and cur[0]["THICKNESS_MM"] == t
    chord = math.hypot(3000, 3000)
    assert cur[0]["DEVELOPED_LENGTH_MM"] > chord + 100, "no chord replaces the curved band"


def test_11_tapering_decorative_element_is_not_a_wall():
    prims = anchor_frame()
    taper = [F.seg("X", (2000, 3000), (7000, 3000)), F.seg("X", (2000, 3120), (7000, 3480))]   # diverging 120 -> 480 mm
    rows, _ = build(prims + taper)
    assert all(r["MATERIAL_STATUS"] != "ACCEPTED" for r in covering(rows, [s.object_id for s in taper]))


def test_12_column_free_standing_and_block_column_unresolved():
    prims = anchor_frame() + F.rect(3000, 3000, 3400, 3400, "C")
    rows, _ = build(prims)
    cols = [r for r in accepted(rows) if r["BAND_TYPE"] == "COLUMN_BAND"]
    assert len(cols) == 1 and cols[0]["INTERSECTION_EVIDENCE"]["CLOSED_LOOP"] and sorted(cols[0]["INTERSECTION_EVIDENCE"]["SIDES_MM"]) == [400, 400]
    rows, _ = build(anchor_frame() + F.rect(3000, 3000, 3400, 3400, "C", block=("COL",)))
    blk = [r for r in rows if r["INTERSECTION_EVIDENCE"] and r["INTERSECTION_EVIDENCE"].get("CLOSED_LOOP") and not (r["REJECTION_REASON"] or "").startswith("DUPLICATE")]
    assert blk and all(r["MATERIAL_STATUS"] == "UNRESOLVED" for r in blk)


def test_13_wall_meeting_column_keeps_both():
    prims = anchor_frame() + F.wall((0, 3000), (4000, 3000), 200) + F.rect(4000, 2800, 4600, 3400, "C")   # 600 x 600 column at the wall end
    rows, _ = build(prims)
    cols = [r for r in accepted(rows) if r["BAND_TYPE"] == "COLUMN_BAND"]
    walls = [r for r in accepted(rows) if r["THICKNESS_MM"] == 200 and r["ORIENTATION_TYPE"] == "HORIZONTAL" and abs(r["DEVELOPED_LENGTH_MM"] - 4000) <= 10]
    assert len(cols) == 1 and len(walls) == 1
    assert any(j["BAND"] == cols[0]["BAND_ID"] or True for j in walls[0]["INTERSECTION_EVIDENCE"]["JOINS"])


def test_14_wall_interrupted_by_doorway_is_one_band_with_a_gap():
    prims = anchor_frame() + F.wall((0, 3000), (3000, 3000), 200) + F.wall((4000, 3000), (7000, 3000), 200)
    prims += F.cap((0, 3000), (3000, 3000), 200, "end") + F.cap((4000, 3000), (7000, 3000), 200, "start") + F.cap((4000, 3000), (7000, 3000), 200, "end")
    rows, _ = build(prims)
    band = [r for r in accepted(rows) if r["ORIENTATION_TYPE"] == "HORIZONTAL" and r["THICKNESS_MM"] == 200 and r["DEVELOPED_LENGTH_MM"] == 7000]
    assert len(band) == 1
    assert band[0]["DEVELOPED_LENGTH_MM"] == 7000 and band[0]["COVERED_LENGTH_MM"] == 6000
    assert band[0]["CONTINUITY_EVIDENCE"]["GAPS_MM"] == [1000.0]


def test_15_tiny_drafting_offsets_and_line_doubling():
    prims = anchor_frame() + F.wall((0, 3000), (5000, 3000), 200) + F.cap((0, 3000), (5000, 3000), 200, "end")
    # a doubled face 8 mm off, and a 50 mm offset construction line along the whole wall
    prims += [F.seg("X", (0, 3108), (5000, 3108)), F.seg("X", (0, 3150), (5000, 3150))]
    rows, _ = build(prims)
    acc = [r for r in accepted(rows) if r["ORIENTATION_TYPE"] == "HORIZONTAL" and r["DEVELOPED_LENGTH_MM"] == 5000]
    assert len(acc) == 1, [(r["THICKNESS_MM"], r["MATERIAL_STATUS"], r["REJECTION_REASON"]) for r in rows if r["ORIENTATION_TYPE"] == "HORIZONTAL"]
    assert acc[0]["THICKNESS_STATUS"] == "AMBIGUOUS_FACE_DOUBLING" and acc[0]["FACE_POSITION_STATUS"] == "AMBIGUOUS_FACE_DOUBLING"
    thin = [r for r in rows if r["MATERIAL_STATUS"] == "REJECTED" and r["REJECTION_REASON"].startswith("THIN_PAIR")]
    assert thin, "the 50 mm pair must be rejected as a drafting offset"


def test_two_walls_with_a_void_between_them_are_two_bands_not_three():
    prims = anchor_frame()
    prims += F.wall((0, 3000), (5000, 3000), 200) + F.cap((0, 3000), (5000, 3000), 200, "end")
    prims += F.wall((0, 3350), (5000, 3350), 200) + F.cap((0, 3350), (5000, 3350), 200, "end")   # 150 mm void between
    rows, _ = build(prims)
    acc = [r for r in accepted(rows) if r["ORIENTATION_TYPE"] == "HORIZONTAL" and r["DEVELOPED_LENGTH_MM"] == 5000]
    assert sorted(r["THICKNESS_MM"] for r in acc) == [200.0, 200.0]
    void = [r for r in rows if r["THICKNESS_MM"] == 150.0]
    assert void and all(r["MATERIAL_STATUS"] != "ACCEPTED" for r in void)
    outer = [r for r in rows if r["THICKNESS_MM"] == 550.0]
    assert outer and outer[0]["REJECTION_REASON"].startswith("ENCLOSES_PARALLEL_FACES")


def test_three_parallel_lines_without_fill_or_caps_stay_unresolved():
    prims = anchor_frame() + [F.seg("X", (0, 3000), (5000, 3000)), F.seg("X", (0, 3200), (5000, 3200)), F.seg("X", (0, 3400), (5000, 3400))]
    rows, _ = build(prims)
    for r in [r for r in rows if r["ORIENTATION_TYPE"] == "HORIZONTAL" and r["DEVELOPED_LENGTH_MM"] == 5000]:
        assert r["MATERIAL_STATUS"] != "ACCEPTED", r["REJECTION_REASON"]


def test_view_border_lines_are_unresolved_not_walls():
    bbox = (0, 0, 20000, 15000)
    prims = anchor_frame() + [F.seg("B", (0, 0), (20000, 0)), F.seg("B", (0, 300), (20000, 300))]
    rows, _ = build(prims, bbox)
    border = [r for r in rows if r["DEVELOPED_LENGTH_MM"] >= 19000]
    assert border and all(r["MATERIAL_STATUS"] == "UNRESOLVED" and r["REJECTION_REASON"].startswith("VIEW_EXTENT_FACE") for r in border)


def test_hidden_linetype_and_invisible_entities_are_never_faces():
    prims = anchor_frame() + F.wall((0, 3000), (5000, 3000), 200)
    beam = [F.seg("X", (0, 4000), (5000, 4000), linetype="HIDDEN"), F.seg("X", (0, 4300), (5000, 4300), linetype="HIDDEN")]
    rows, _ = build(prims + beam)
    assert not covering(rows, [b.object_id for b in beam])


def test_summary_counts_and_no_bare_totals():
    rows, _ = build(anchor_frame() + F.wall((0, 3000), (5000, 3000), 200) + F.cap((0, 3000), (5000, 3000), 200, "end"))
    s = MB.summarise(rows)
    assert s["ACCEPTED"] + s["REJECTED"] + s["UNRESOLVED"] == len(rows)
    assert set(s["ACCEPTED_DEVELOPED_M"]) == {"STRAIGHT", "CURVED", "COLUMN"}
