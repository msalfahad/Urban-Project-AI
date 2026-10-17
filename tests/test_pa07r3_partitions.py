"""PA07R3 (PA08-QORTUBA-R1) generic partition recovery: the failure classes of the Qortuba merged cell, each reproduced on a
synthetic fixture that carries none of the Qortuba geometry.  Every rule is judged by what it must NOT do as much as by what it
recovers: thickness alone never promotes, a doorless end gap is never merged, a wardrobe against a wall never becomes a room."""

from __future__ import annotations

import math

from engine.ingest import band_topology as BT, material_bands as MB, planar_faces as PF
from tests import pa07_fixtures as F

BOX = (-2000, -2000, 12000, 12000)


def run(prims, texts=(), box=BOX, support=()):
    roles = F.roles_of(prims)
    rows, bands = MB.build("VW-t", prims, roles, view_bbox=box, thickness_support=support)
    intervals, sites, seals = BT.build_view("VW-t", prims, roles, bands)
    faces, grids = PF.build("VW-t", box, seals, bands, texts)
    brows = PF.boundary_faces("VW-t", faces, grids, bands, intervals, seals)
    spaces = PF.space_register("VW-t", faces, brows)
    return dict(rows=rows, bands=bands, intervals=intervals, sites=sites, seals=seals, faces=faces, grids=grids, spaces=spaces)


def rooms_of(r, min_m2=1.5):
    return sorted(s["AREA_GEOMETRIC_M2"] for s in r["spaces"] if s["AREA_GEOMETRIC_M2"] >= min_m2)


def accepted(r):
    return [b for b in r["bands"] if b["STATUS"] == "ACCEPTED"]


# ------------------------------------------------------------------ FC-1: floating-point direction frame
def test_fc1_horizontal_faces_with_endpoint_noise_pair():
    F.reset()
    a = F.seg("W", (0, 1000), (3000, 1000 - 6e-11))          # atan2 gives -2e-14 -> used to come back as pi - epsilon
    b = F.seg("W", (0, 1200), (3000, 1200))
    assert MB._dir_key(MB._angle(a)) == MB._dir_key(MB._angle(b)) == 0
    assert abs(MB._angle(a)) < 1e-9, "a line with endpoint noise is direction 0, not pi - epsilon"
    pairs = MB._pairs([a, b])
    assert len(pairs) == 1 and abs(pairs[0][2] - 200) < 1e-6


# ------------------------------------------------------------------ fixtures: two rooms and a shared wall with a corner door
def two_rooms(t=150.0, gap=900.0, evidence=(), double=False, extra=()):
    """Outer ring 0..6000 x 0..8000, shared wall y = 4000 from x = 0 to 6000 - gap; the corner door gap runs to the east wall."""
    F.reset()
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (6000 - gap, 4000), t) + F.cap((0, 4000), (6000 - gap, 4000), t, "end")
    x0 = 6000 - gap
    if "leaf" in evidence:
        if double:
            prims += [F.seg("D", (x0 + 50, 4000 + t / 2), (x0 + 50, 4000 + t / 2 + gap / 2 - 60), block=("DOOR",)),
                      F.seg("D", (6000 - 50, 4000 + t / 2), (6000 - 50, 4000 + t / 2 + gap / 2 - 60), block=("DOOR",))]
        else:
            prims += [F.seg("D", (x0 + 50, 4000 + t / 2), (x0 + 50, 4000 + t / 2 + gap - 60), block=("DOOR",))]
    if "frame" in evidence:
        prims += F.rect(x0, 4000 - t / 2, x0 + 60, 4000 + t / 2, "D", block=("DOOR",)) + F.rect(6000 - 60, 4000 - t / 2, 6000, 4000 + t / 2, "D", block=("DOOR",))
    prims += list(extra)
    return prims


def door_site(r):
    s = [s for s in r["sites"] if s.get("END_GAP")]
    assert len(s) == 1, [(z["CLASS"], z["STATUS"], z["SPAN_MM"], z.get("END_GAP")) for z in r["sites"]]
    return s[0]


def test_corner_door_leaf_only_150_wall():
    r = run(two_rooms(150, 900, ("leaf",)))
    s = door_site(r)
    assert s["CLASS"] == "PROBABLE_DOOR_OPENING" and s["STATUS"] == "PROVISIONAL" and abs(s["SPAN_MM"] - 900) < 1 and s["LEAF_EVIDENCE"]
    assert len(rooms_of(r)) == 2, "two rooms, never merged through the corner door"


def test_corner_door_frame_only_200_wall():
    r = run(two_rooms(200, 900, ("frame",)))
    s = door_site(r)
    assert s["CLASS"] == "PROBABLE_DOOR_OPENING" and s["JAMB_A"] and s["JAMB_B"] and not s["LEAF_EVIDENCE"]
    assert len(rooms_of(r)) == 2


def test_corner_door_leaf_and_frame_is_confirmed_no_swing():
    r = run(two_rooms(150, 900, ("leaf", "frame")))
    s = door_site(r)
    assert s["CLASS"] == "CONFIRMED_DOOR_OPENING" and s["STATUS"] == "ESTABLISHED" and not s["SWING_EVIDENCE"]
    assert len(rooms_of(r)) == 2


def test_corner_double_leaf_door():
    r = run(two_rooms(200, 1800, ("leaf", "frame"), double=True))
    s = door_site(r)
    assert s["CLASS"] == "CONFIRMED_DOOR_OPENING" and all(l.get("DOUBLE_LEAF") for l in s["LEAF_EVIDENCE"]) and len(s["LEAF_EVIDENCE"]) == 2
    assert len(rooms_of(r)) == 2


def test_doorless_end_gap_is_unresolved_never_merged():
    r = run(two_rooms(150, 1200, ()))
    s = door_site(r)
    assert s["CLASS"] == "UNRESOLVED" and s["STATUS"] == "INSUFFICIENT_EVIDENCE"
    assert len(rooms_of(r)) == 2, "a wall that stops 1200 mm short of the next wall with nothing drawn separates provisionally"
    assert all(sp["GEOMETRY_STATUS"] == "BOUNDARY_PROVISIONAL" for sp in r["spaces"] if sp["AREA_GEOMETRIC_M2"] >= 1.5)


def test_door_near_junction_short_return_follows_the_wall():
    # the shared wall continues 100 mm past the door up to the east wall: a return of the wall's thickness, authored 150 in the source
    F.reset()
    t = 150.0
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (5000, 4000), t) + F.cap((0, 4000), (5000, 4000), t, "end")
    prims += F.wall((5900, 4000), (6000, 4000), t) + F.cap((5900, 4000), (6000, 4000), t, "start")
    prims += [F.seg("D", (5050, 4075), (5050, 4075 + 840), block=("DOOR",))] + F.rect(5000, 3925, 5060, 4075, "D", block=("DOOR",)) + F.rect(5840, 3925, 5900, 4075, "D", block=("DOOR",))
    r = run(prims, support=(150.0,))
    # the 100 mm return follows its wall (authored thickness, same axis): the door is an ordinary gap inside one band, not an end gap
    s = [s for s in r["sites"] if abs(s["SPAN_MM"] - 900) < 1]
    assert len(s) == 1 and s[0]["CLASS"] == "CONFIRMED_DOOR_OPENING", [(z["CLASS"], z["SPAN_MM"], z.get("END_GAP")) for z in r["sites"]]
    assert len(rooms_of(r)) == 2


def test_end_gap_junction_tolerance_and_along_wall():
    # a partition stopping 150 mm short of the perpendicular wall is a drafting junction, no site; a stub running along an accepted wall hosts no opening
    r = run(two_rooms(150, 150, ()))
    assert not [s for s in r["sites"] if s.get("END_GAP")]
    assert len(rooms_of(r)) == 2


def test_two_facing_bands_share_one_end_gap_site():
    # a 200 wall and a 150 wall face each other across one 900 door (different thickness = two bands)
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (2500, 4000), 200) + F.cap((0, 4000), (2500, 4000), 200, "end")
    prims += F.wall((3400, 4000), (6000, 4000), 150) + F.cap((3400, 4000), (6000, 4000), 150, "start")
    prims += [F.seg("D", (2550, 4100), (2550, 4100 + 840), block=("DOOR",))] + F.rect(2500, 3900, 2560, 4100, "D", block=("DOOR",)) + F.rect(3340, 3925, 3400, 4075, "D", block=("DOOR",))
    r = run(prims)
    sites = [s for s in r["sites"] if s.get("END_GAP")]
    assert len(sites) == 1 and sites[0]["CLASS"] == "CONFIRMED_DOOR_OPENING", [(s["CLASS"], s["SPAN_MM"]) for s in sites]
    shared = [iv for iv in r["intervals"] if (iv.get("START_STATE") or {}).get("STATE") == "END_GAP_SHARED" or (iv.get("END_STATE") or {}).get("STATE") == "END_GAP_SHARED"]
    assert shared, "the facing band records that the site is hosted by the other one"
    assert len(rooms_of(r)) == 2


# ------------------------------------------------------------------ FC-3 / FC-4: unresolved strips and closed outlines
def test_fc3_unresolved_strip_is_capped_never_a_corridor():
    # a 120 partition between two rooms that stays UNRESOLVED (thin, no fill, no authored thickness) still separates: its strip is capped
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (6000, 4000), 120, layer="P")
    r = run(prims)
    part = [b for b in r["bands"] if abs(b["THK"] - 120) < 1]
    assert part and part[0]["STATUS"] == "UNRESOLVED"
    caps = [s for s in r["seals"] if s["KIND"] == "UNRESOLVED_CHORD" and s.get("SIDE") == "END"]
    assert len(caps) == 2
    assert len(rooms_of(r)) == 2


def test_fc4_closed_outline_between_two_rooms_separates_them():
    # a 1900 x 700 closed outline of wall-layer lines completes the partition between two rooms: rooms stay apart, the outline is not floor
    F.reset()
    t = 150.0
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (2000, 4000), t) + F.cap((0, 4000), (2000, 4000), t, "end")
    prims += F.wall((3900, 4000), (6000, 4000), t) + F.cap((3900, 4000), (6000, 4000), t, "start")
    prims += F.rect(2000, 3650, 3900, 4350, "W")
    r = run(prims)
    outline = [s for s in r["seals"] if s.get("OUTLINE")]
    assert len(outline) == 4 and outline[0]["OUTLINE_SIZE_MM"] == [1900, 700]
    big = rooms_of(r)
    assert len(big) == 2 and all(a < 25 for a in big), big
    inner = [f for f in r["faces"] if 1.0 <= f["AREA_GEOMETRIC_M2"] < 1.5]
    assert inner and inner[0]["STATUS"] != "ESTABLISHED", "the outline interior is an enclosed face bounded by provisional chords, never silently floor of either room"


def test_fc4_wardrobe_against_wall_stays_room_floor():
    F.reset()
    prims = F.room(0, 0, 6000, 4000, 200) + F.rect(0, 0, 2000, 600, "J")
    r = run(prims)
    assert not [s for s in r["seals"] if s.get("OUTLINE")]
    assert len(rooms_of(r)) == 1 and abs(rooms_of(r)[0] - 24.0) < 0.5


# ------------------------------------------------------------------ FC-7 / repeated blocks: furniture never becomes a wall
def test_fc7_bed_against_wall_with_stray_piece_is_not_a_wall():
    F.reset()
    t = 200.0
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (5100, 4000), t) + F.cap((0, 4000), (5100, 4000), t, "end")
    # a bed drawn against the partition face with the wall face as its near side: far side + two returns in a block, plus a stray exploded 100 mm piece on the far side
    prims += [F.seg("F", (500, 4700), (2500, 4700), block=("BED",)), F.seg("F", (500, 4100), (500, 4700), block=("BED",)), F.seg("F", (2500, 4100), (2500, 4700), block=("BED",))]
    prims += [F.seg("F", (2500, 4700), (2600, 4700))]
    r = run(prims)
    bed = [b for b in r["bands"] if abs(b["THK"] - 600) < 1]
    assert bed and all(b["STATUS"] == "REJECTED" and b["REASON"].startswith("MIXED_BLOCK_STRIP") for b in bed), [(b["STATUS"], b["REASON"]) for b in bed]
    assert bed[0]["EVIDENCE"]["BLOCK_SHARE_BY_SIDE"]["B"] < 1.0, "the stray model-space piece is on the block side: length weighting, not all/any"
    part = [b for b in r["bands"] if abs(b["THK"] - 200) < 1 and abs(b["LENGTH"] - 5100) < 60]
    assert part and part[0]["STATUS"] == "ACCEPTED", [(b["STATUS"], b["REASON"]) for b in part]
    # the same bed drawn with all four sides in the block is a closed fitting loop: rejected too, the partition still accepted
    F.reset()
    prims = F.room(0, 0, 6000, 8000, t) + F.wall((0, 4000), (5100, 4000), t) + F.cap((0, 4000), (5100, 4000), t, "end") + F.rect(500, 4100, 2500, 4700, "F", block=("BED",))
    r = run(prims)
    assert all(b["STATUS"] == "REJECTED" for b in r["bands"] if abs(b["THK"] - 600) < 1), [(b["STATUS"], b["REASON"]) for b in r["bands"] if abs(b["THK"] - 600) < 1]
    assert [b for b in r["bands"] if abs(b["THK"] - 200) < 1 and abs(b["LENGTH"] - 5100) < 60][0]["STATUS"] == "ACCEPTED"


def test_repeated_block_symbol_strip_rejected():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200)
    for k, x in enumerate((1000, 3000)):
        for p in F.rect(x, 2000, x + 500, 2400, "F", block=("CHAIR",)):
            p.object_id = f"{p.object_id}@{100 + k}"
            prims.append(p)
    r = run(prims)
    sym = [b for b in r["bands"] if b["BLOCK"]]
    assert sym and all(b["STATUS"] == "REJECTED" and b["REASON"].startswith(("REPEATED_BLOCK_SYMBOL_STRIP", "DUPLICATE_OF_BAND")) for b in sym), [(b["STATUS"], b["REASON"]) for b in sym]
    assert any(b["REASON"].startswith("REPEATED_BLOCK_SYMBOL_STRIP") for b in sym)
    assert len(rooms_of(r)) == 1


# ------------------------------------------------------------------ §3 thickness-supported band rule
def test_thin_partition_with_authored_thickness_and_junction_is_accepted_but_not_alone():
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (6000, 4000), 120)
    r0 = run(prims)
    thin0 = [b for b in r0["bands"] if abs(b["THK"] - 120) < 1][0]
    assert thin0["STATUS"] == "UNRESOLVED" and thin0["REASON"].startswith("THIN_BAND_UNCONFIRMED")
    r1 = run(prims, support=(120.0,))
    thin1 = [b for b in r1["bands"] if abs(b["THK"] - 120) < 1][0]
    assert thin1["STATUS"] == "ACCEPTED" and thin1["EVIDENCE"].get("THICKNESS_SUPPORT_RULE")
    # the same 120 pair drawn inside a block (a frame symbol) is never promoted by the authored thickness
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 4000), (6000, 4000), 120)
    for p in prims[-2:]:
        p.provenance.block_path = ("FRAME",)
    r2 = run(prims, support=(120.0,))
    thin2 = [b for b in r2["bands"] if abs(b["THK"] - 120) < 1][0]
    assert thin2["STATUS"] != "ACCEPTED"
    # an isolated 120 pair in the middle of the room with the authored thickness: no junction, not promoted
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((1500, 4000), (4500, 4000), 120)
    r3 = run(prims, support=(120.0,))
    thin3 = [b for b in r3["bands"] if abs(b["THK"] - 120) < 1][0]
    assert thin3["STATUS"] != "ACCEPTED"


# ------------------------------------------------------------------ §9 measurement layer: the arrangement area
def test_arrangement_area_of_a_rectangular_room_is_exact():
    from research.qs_wall_treatment_01.pa08.qortuba.r1 import measure as ME
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200)
    r = run(prims)
    face = max(r["faces"], key=lambda f: f["AREA_GEOMETRIC_M2"] if f["SPACE_ELIGIBILITY"] == "ELIGIBLE" else 0)
    area, formula = ME.face_polygon_area(face, r["grids"], r["seals"])
    assert area is not None and abs(area - 48.0) < 1e-6, (area, formula.get("WHY"))
    assert formula["STATUS"] == "COMPUTED" and formula["RECTANGLES"]


def test_arrangement_area_of_an_l_shaped_room_sums_its_rectangles():
    from research.qs_wall_treatment_01.pa08.qortuba.r1 import measure as ME
    F.reset()
    # a 6000 x 8000 room with a 2000 x 3000 block walled off in one corner -> 48 - 6 = 42 m2
    prims = F.room(0, 0, 6000, 8000, 200) + F.wall((0, 3000), (2000, 3000), 200) + F.wall((2000, 0), (2000, 3000), 200) + F.cap((0, 3000), (2000, 3000), 200, "end")
    r = run(prims)
    faces = sorted((f for f in r["faces"] if f["SPACE_ELIGIBILITY"] == "ELIGIBLE"), key=lambda f: -f["AREA_GEOMETRIC_M2"])
    area, formula = ME.face_polygon_area(faces[0], r["grids"], r["seals"])
    assert area is not None and abs(area - 41.4) < 0.5, (area, formula.get("FORMULA"))
    assert len(formula["RECTANGLES"]) >= 2, "an L-shaped region is measured as a sum of rectangles, not one bounding box"


def test_arrangement_refuses_a_face_bounded_by_a_curved_wall():
    from research.qs_wall_treatment_01.pa08.qortuba.r1 import measure as ME
    F.reset()
    prims = F.room(0, 0, 6000, 8000, 200) + F.curved_wall((3000, 4000), 1500, 200, 0.0, 2 * math.pi)
    r = run(prims)
    for f in r["faces"]:
        if f["SPACE_ELIGIBILITY"] != "ELIGIBLE":
            continue
        area, formula = ME.face_polygon_area(f, r["grids"], r["seals"])
        if formula.get("STATUS") == "NOT_APPLICABLE":
            assert "not axis-aligned" in formula["WHY"]
            return
    raise AssertionError("a face bounded by the curved wall should refuse the arrangement method")
