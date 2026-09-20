"""PA07B / PA07C tests: band intervals, opening sites with evidence fields, single-face rule, seals, and the nine curved fixtures."""

from __future__ import annotations

import math

from engine.ingest import band_topology as BT, material_bands as MB
from tests import pa07_fixtures as F


def run(prims, bbox=None):
    roles = F.roles_of(prims)
    rows, bands = MB.build("VW-t", prims, roles, view_bbox=bbox)
    intervals, sites, seals = BT.build_view("VW-t", prims, roles, bands)
    return rows, bands, intervals, sites, seals


def frame():
    return F.wall((0, 0), (8000, 0), 200) + F.wall((0, 0), (0, 6000), 200) + F.cap((0, 0), (8000, 0), 200, "end") + F.cap((0, 0), (0, 6000), 200, "end")


def host_band(bands, pred):
    hs = [b for b in bands if b["STATUS"] == "ACCEPTED" and pred(b)]
    assert len(hs) == 1, [(b["THK"], b["LENGTH"], b["ORIENTATION"]) for b in hs]
    return hs[0]


def doorway(gap=(3000.0, 3900.0), jambs=True, leaf=False, swing=True, t=200.0):
    """A horizontal 200 wall y = 3000 from x = 0 to 7000 with a both-face gap."""
    prims = frame() + F.wall((0, 3000), (gap[0], 3000), t) + F.wall((gap[1], 3000), (7000, 3000), t) + F.cap((gap[1], 3000), (7000, 3000), t, "end")
    if jambs:
        prims += [F.seg("J", (gap[0], 3000 - t / 2), (gap[0], 3000 + t / 2)), F.seg("J", (gap[1], 3000 - t / 2), (gap[1], 3000 + t / 2))]
    if swing:
        prims.append(F.arc("S", (gap[0], 3000 + t / 2), gap[1] - gap[0], 0.0, math.pi / 2))
    if leaf:
        prims.append(F.seg("L", (gap[0], 3000 + t / 2), (gap[0], 3000 + t / 2 + (gap[1] - gap[0]))))
    return prims


def test_confirmed_door_with_swing_and_jambs():
    rows, bands, intervals, sites, seals = run(doorway())
    b = host_band(bands, lambda b: b["ORIENTATION"] == "HORIZONTAL" and b["LENGTH"] == 7000)
    mine = [i for i in intervals if i["HOST_BAND_ID"] == b["BAND_ID"]]
    assert [i["CLASS"] for i in mine] == ["MATERIAL", "OPENING", "MATERIAL"]
    s = [s for s in sites if s["HOST_BAND_ID"] == b["BAND_ID"]]
    assert len(s) == 1 and s[0]["CLASS"] == "CONFIRMED_DOOR_OPENING" and s[0]["SPAN_MM"] == 900 and s[0]["JAMB_A"] and s[0]["JAMB_B"] and s[0]["SWING_EVIDENCE"]
    assert s[0]["CROSSES_FULL_BAND"] and s[0]["FACE_A_INTERRUPTED"] and s[0]["FACE_B_INTERRUPTED"]
    for k in ("HOST_BAND_ID", "AXIAL_START", "AXIAL_END", "SPAN_MM", "LEAF_EVIDENCE", "FRAME_EVIDENCE", "GLAZING_EVIDENCE", "FREE_SPACE_SIDE_A", "FREE_SPACE_SIDE_B", "STATUS", "SOURCE"):
        assert k in s[0]
    # remaining host material = 7000 - 900
    assert round(sum(i["SPAN_MM"] for i in mine if i["CLASS"] == "MATERIAL"), 1) == 6100.0


def test_missing_leaf_with_jambs_is_probable_not_confirmed():
    _, bands, _, sites, _ = run(doorway(swing=False, leaf=False))
    s = [s for s in sites if s["SPAN_MM"] == 900]
    assert len(s) == 1 and s[0]["CLASS"] == "PROBABLE_DOOR_OPENING" and s[0]["STATUS"] == "PROVISIONAL"


def test_leaf_without_swing_with_jambs_is_confirmed():
    _, bands, _, sites, _ = run(doorway(swing=False, leaf=True))
    s = [s for s in sites if s["SPAN_MM"] == 900]
    assert len(s) == 1 and s[0]["CLASS"] == "CONFIRMED_DOOR_OPENING" and s[0]["LEAF_EVIDENCE"]


def test_both_faces_interrupted_without_any_evidence_is_unresolved_not_merged():
    _, bands, intervals, sites, _ = run(doorway(jambs=False, swing=False))
    s = [s for s in sites if s["SPAN_MM"] == 900]
    assert len(s) == 1 and s[0]["CLASS"] == "UNRESOLVED" and s[0]["STATUS"] == "INSUFFICIENT_EVIDENCE"
    assert [i["CLASS"] for i in intervals if i["HOST_BAND_ID"] == s[0]["HOST_BAND_ID"]] == ["MATERIAL", "UNRESOLVED", "MATERIAL"]


def test_single_face_gap_is_never_a_doorway():
    prims = frame() + F.wall((0, 3000), (7000, 3000), 200) + F.cap((0, 3000), (7000, 3000), 200, "end")
    # break face B (y = 3100) between x 3000 and 3900, keep face A whole
    fb = [p for p in prims if p.y1 == 3100 and p.y2 == 3100]
    prims = [p for p in prims if p not in fb] + [F.seg("W", (0, 3100), (3000, 3100)), F.seg("W", (3900, 3100), (7000, 3100))]
    prims.append(F.arc("S", (3000, 3100), 900, 0.0, math.pi / 2))     # even with a swing drawn
    _, bands, intervals, sites, _ = run(prims)
    s = [s for s in sites if s["SPAN_MM"] == 900]
    assert len(s) == 1 and s[0]["CLASS"] == "UNRESOLVED" and s[0]["STATUS"] == "SINGLE_FACE_GAP" and not s[0]["CROSSES_FULL_BAND"]
    assert all(s2["CLASS"] not in ("CONFIRMED_DOOR_OPENING", "PROBABLE_DOOR_OPENING") for s2 in sites)


def test_crossing_wall_makes_junction_intervals_not_sites():
    prims = frame() + F.wall((0, 3000), (7000, 3000), 200) + F.cap((0, 3000), (7000, 3000), 200, "end")
    # a partition from the bottom wall up to the horizontal wall: it interrupts face A (y = 2900) between 3900 and 4100
    fa = [p for p in prims if p.y1 == 2900 and p.y2 == 2900]
    prims = [p for p in prims if p not in fa] + [F.seg("W", (0, 2900), (3900, 2900)), F.seg("W", (4100, 2900), (7000, 2900))]
    prims += F.wall((4000, 0), (4000, 2900), 200)
    _, bands, intervals, sites, _ = run(prims)
    host = host_band(bands, lambda b: b["ORIENTATION"] == "HORIZONTAL" and b["LENGTH"] == 7000)
    mine = [i for i in intervals if i["HOST_BAND_ID"] == host["BAND_ID"]]
    assert [i["CLASS"] for i in mine] == ["MATERIAL", "JUNCTION", "MATERIAL"]
    assert not [s for s in sites if s["HOST_BAND_ID"] == host["BAND_ID"]]


def test_window_with_frame_lines():
    prims = doorway(gap=(3000.0, 4500.0), jambs=True, swing=False)
    prims += [F.seg("F", (3000, 2960), (4500, 2960)), F.seg("F", (3000, 3040), (4500, 3040))]
    _, bands, _, sites, _ = run(prims)
    s = [s for s in sites if s["SPAN_MM"] == 1500]
    assert len(s) == 1 and s[0]["CLASS"] == "CONFIRMED_WINDOW_OPENING" and len(s[0]["FRAME_EVIDENCE"]) == 2


def test_tiny_gap_and_short_break_are_not_openings():
    _, _, _, sites, _ = run(doorway(gap=(3000.0, 3060.0), jambs=False, swing=False))
    assert [s["CLASS"] for s in sites if s["SPAN_MM"] == 60] == ["CAD_JUNCTION"]
    _, _, _, sites, _ = run(doorway(gap=(3000.0, 3400.0), jambs=False, swing=False))
    assert [s["CLASS"] for s in sites if s["SPAN_MM"] == 400] == ["MATERIAL_CONTINUITY"]


def test_wide_jambed_gap_is_open_passage_candidate_only():
    _, _, _, sites, _ = run(doorway(gap=(2000.0, 4500.0), jambs=True, swing=False))
    s = [s for s in sites if s["SPAN_MM"] == 2500]
    assert len(s) == 1 and s[0]["CLASS"] == "UNRESOLVED" and s[0]["STATUS"] == "OPEN_PASSAGE_CANDIDATE"
    BT.promote_open_passages(s, lambda site: ("INTERIOR", "INTERIOR"))
    assert s[0]["CLASS"] == "CONFIRMED_OPEN_PASSAGE"
    s2 = [s for s in run(doorway(gap=(2000.0, 4500.0), jambs=True, swing=False))[3] if s["SPAN_MM"] == 2500]
    BT.promote_open_passages(s2, lambda site: ("INTERIOR", "EXTERIOR"))
    assert s2[0]["CLASS"] == "UNRESOLVED"


def test_seals_close_every_interval_and_carry_no_material():
    _, bands, intervals, sites, seals = run(doorway())
    chords = [s for s in seals if s["KIND"] == "THICKNESS_CHORD"]
    assert chords and all(s["MATERIAL"] is False for s in chords)
    assert all(s["MATERIAL"] is False for s in seals if s["KIND"].endswith("_CHORD"))
    assert all(s["MATERIAL"] is True for s in seals if s["KIND"] in ("FACE", "COLUMN_FACE"))
    # every interval has chords at both its ends
    by_iv = {}
    for s in chords:
        by_iv.setdefault(s["INTERVAL_ID"], 0); by_iv[s["INTERVAL_ID"]] += 1
    assert all(by_iv.get(i["INTERVAL_ID"], 0) == 2 for i in intervals)


# ------------------------------------------------------------------ curved fixtures (PA07C)
def curved(c, r, t, a0, a1):
    return F.curved_wall(c, r, t, a0, a1)


def test_c1_semicircular_wall_no_opening():
    r = 3000.0
    prims = frame() + curved((3000, 3000), r, 200, 0.0, math.pi) + F.wall((0, 3000), (0, 6000), 200)   # straight leg on the left joins the arc end (0,3000)
    prims += F.wall((6000, 0), (6000, 3000), 200)
    _, bands, intervals, sites, _ = run(prims)
    b = host_band(bands, lambda b: b["KIND"] == "C")
    assert abs(b["LENGTH"] - math.pi * r) <= 0.005 * math.pi * r
    mine = [i for i in intervals if i["HOST_BAND_ID"] == b["BAND_ID"]]
    assert [i["CLASS"] for i in mine] == ["MATERIAL"] and not [s for s in sites if s["HOST_BAND_ID"] == b["BAND_ID"]]


def _curved_with_gap(r, t, a_gap0, a_gap1, jambs=True, swing=False, frame_lines=0):
    c = (3000.0, 3000.0)
    prims = frame() + curved(c, r, t, 0.0, a_gap0) + curved(c, r, t, a_gap1, math.pi) + F.wall((6000, 0), (6000, 3000), 200) + F.wall((0, 3000), (0, 6000), 200)
    if jambs:
        for a in (a_gap0, a_gap1):
            prims.append(F.seg("J", (c[0] + (r - t / 2) * math.cos(a), c[1] + (r - t / 2) * math.sin(a)), (c[0] + (r + t / 2) * math.cos(a), c[1] + (r + t / 2) * math.sin(a))))
    span = (a_gap1 - a_gap0) * r
    if swing:
        jx, jy = c[0] + (r + t / 2) * math.cos(a_gap0), c[1] + (r + t / 2) * math.sin(a_gap0)
        prims.append(F.arc("S", (jx, jy), span, a_gap0 + math.pi / 2, a_gap0 + math.pi))
    for k in range(frame_lines):
        off = -t / 4 + k * t / 2
        prims.append(F.arc("F", c, r + off, a_gap0, a_gap1))
    return prims, span


def test_c2_curved_wall_with_door():
    r, t = 3000.0, 200.0
    a0 = math.pi / 3; a1 = a0 + 900.0 / r
    prims, span = _curved_with_gap(r, t, a0, a1, jambs=True, swing=True)
    _, bands, intervals, sites, _ = run(prims)
    b = host_band(bands, lambda b: b["KIND"] == "C")
    assert abs(b["LENGTH"] - math.pi * r) <= 0.005 * math.pi * r
    s = [s for s in sites if s["HOST_BAND_ID"] == b["BAND_ID"]]
    assert len(s) == 1 and s[0]["CLASS"] == "CONFIRMED_DOOR_OPENING" and abs(s[0]["SPAN_MM"] - 900) <= 10
    mat = sum(i["SPAN_MM"] for i in intervals if i["HOST_BAND_ID"] == b["BAND_ID"] and i["CLASS"] == "MATERIAL")
    assert abs(mat - (math.pi * r - 900)) <= 0.005 * math.pi * r
    # reversibility: the opening is an interval, the host keeps its developed geometry
    assert abs(sum(i["SPAN_MM"] for i in intervals if i["HOST_BAND_ID"] == b["BAND_ID"]) - b["LENGTH"]) <= 1


def test_c3_curved_wall_with_window():
    r, t = 3000.0, 200.0
    a0 = math.pi / 3; a1 = a0 + 1500.0 / r
    prims, span = _curved_with_gap(r, t, a0, a1, jambs=True, swing=False, frame_lines=2)
    _, bands, intervals, sites, _ = run(prims)
    b = host_band(bands, lambda b: b["KIND"] == "C")
    s = [s for s in sites if s["HOST_BAND_ID"] == b["BAND_ID"]]
    assert len(s) == 1 and s[0]["CLASS"] == "CONFIRMED_WINDOW_OPENING" and abs(s[0]["SPAN_MM"] - 1500) <= 10


def test_c4_two_concentric_decorative_arcs_are_not_a_wall():
    prims = frame() + curved((4000, 3500), 1500, 150, 0.2, 2.8)      # joined to nothing
    rows, bands, intervals, sites, _ = run(prims)
    assert not [b for b in bands if b["KIND"] == "C" and b["STATUS"] == "ACCEPTED"]
    assert any(r["CURVATURE_TYPE"] == "ARC" and r["MATERIAL_STATUS"] == "UNRESOLVED" and r["REJECTION_REASON"].startswith("ISOLATED_PAIR") for r in rows)


def test_c5_pool_curve_beside_a_true_wall():
    prims = frame() + F.wall((0, 3000), (7000, 3000), 200) + F.cap((0, 3000), (7000, 3000), 200, "end")
    prims += curved((3500, 1200), 1000, 300, 0.0, 2 * math.pi - 1e-3)      # pool coping: two concentric closed arcs 300 apart
    rows, bands, intervals, sites, _ = run(prims)
    assert not [b for b in bands if b["KIND"] == "C" and b["STATUS"] == "ACCEPTED"]
    assert host_band(bands, lambda b: b["ORIENTATION"] == "HORIZONTAL" and b["LENGTH"] == 7000)


def test_c6_curved_joined_to_straight():
    r = 3000.0
    prims = frame() + curved((3000, 3000), r, 200, 0.0, math.pi / 2) + F.wall((6000, 0), (6000, 3000), 200) + F.wall((0, 6000), (3000, 6000), 200)
    _, bands, intervals, sites, _ = run(prims)
    b = host_band(bands, lambda b: b["KIND"] == "C")
    assert abs(b["LENGTH"] - r * math.pi / 2) <= 15
    joins = b["EVIDENCE"]["INTERSECTION"]["JOINS"]
    assert len(joins) >= 1
    assert host_band(bands, lambda b: b["ORIENTATION"] == "VERTICAL" and b["LENGTH"] == 3000)


def test_c7_small_unresolved_arc_gap():
    r, t = 3000.0, 200.0
    a0 = math.pi / 3; a1 = a0 + 400.0 / r
    prims, span = _curved_with_gap(r, t, a0, a1, jambs=True, swing=False)
    _, bands, intervals, sites, _ = run(prims)
    b = host_band(bands, lambda b: b["KIND"] == "C")
    s = [s for s in sites if s["HOST_BAND_ID"] == b["BAND_ID"]]
    assert len(s) == 1 and s[0]["CLASS"] == "UNRESOLVED" and s[0]["STATUS"] == "INSUFFICIENT_EVIDENCE"


def test_c8_tangent_transition_curved_to_straight():
    r = 2000.0
    # straight wall along y = 1000 from x 0..3000 ; arc centre (3000, 3000) radius 2000 from angle -pi/2 (point (3000,1000)) to 0 (point (5000,3000)); tangent at both ends
    prims = frame() + F.wall((0, 1000), (3000, 1000), 200) + curved((3000, 3000), r, 200, -math.pi / 2, 0.0) + F.wall((5000, 3000), (5000, 6000), 200) + F.wall((0, 6000), (5000, 6000), 200)
    _, bands, intervals, sites, _ = run(prims)
    b = host_band(bands, lambda b: b["KIND"] == "C")
    st = host_band(bands, lambda b: b["ORIENTATION"] == "HORIZONTAL" and b["LENGTH"] == 3000)
    assert any(j["BAND"] in (st["BAND_ID"], st["KEY"]) for j in b["EVIDENCE"]["INTERSECTION"]["JOINS"]) or any(j["BAND"] in (b["BAND_ID"], b["KEY"]) for j in st["EVIDENCE"]["INTERSECTION"]["JOINS"])
    assert abs(b["LENGTH"] - r * math.pi / 2) <= 15


def test_c9_curved_glazing_separator_is_not_material():
    prims = frame() + F.wall((0, 3000), (7000, 3000), 200) + F.cap((0, 3000), (7000, 3000), 200, "end")
    prims.append(F.arc("G", (3500, 1500), 1200, 0.0, math.pi, role="GLAZING"))
    rows, bands, intervals, sites, _ = run(prims)
    assert not [b for b in bands if b["KIND"] == "C"]
    assert not any(r["CURVATURE_TYPE"] == "ARC" for r in rows)
