"""Generic ground-beam pairing fixtures (GB-MP-01..05 multi-partner, GB-ARC-01..05 arc overlap).

Synthetic geometry only: every expected value is derived here from the fixture coordinates. No project value.
"""

from __future__ import annotations

import math

import pytest

from engine.source import ground_beam_network as GN

W, TOL = 300.0, 12.0
LAY = {"1"}


def seg(h, x0, y0, x1, y1, layer="1"):
    return {"handle": h, "layer": layer, "p0": (x0, y0), "p1": (x1, y1)}


def run(faces):
    return GN.pair_straight(faces, width=W, tol=TOL, admitted_layers=LAY)


def conserved(res, faces):
    """Every admitted face: covered + unpaired = face length."""
    for row in res["ledger"]:
        assert row["covered"] + row["unpaired"] == pytest.approx(row["length"], abs=1e-6), row
    seen = {r["handle"] for r in res["ledger"]} | {r["handle"] for r in res["rejected_faces"]}
    assert seen == {f["handle"] for f in faces}


# ------------------------------------------------------------------ multi-partner
def test_gb_mp_01_one_long_face_to_one_long_face():
    faces = [seg("A", 0, 0, 5000, 0), seg("B", 0, 300, 5000, 300)]
    res = run(faces)
    assert len(res["bands"]) == 1
    b = res["bands"][0]
    assert b["length"] == pytest.approx(5000) and b["width"] == pytest.approx(300)
    assert b["rule"] == "SINGLE_PARTNER" and b["handles"] == ["A", "B"]
    assert not res["unpaired"] and not res["conflicts"]
    conserved(res, faces)


def test_gb_mp_02_one_long_face_to_two_contiguous_split_faces():
    faces = [seg("A", 0, 0, 4225, 0), seg("B1", 4225, 300, 3225, 300), seg("B2", 3225, 300, 0, 300)]
    res = run(faces)
    assert len(res["bands"]) == 1, res["bands"]
    b = res["bands"][0]
    assert b["rule"] == "MULTI_PARTNER_PAIRING"
    assert b["length"] == pytest.approx(4225)              # the whole face, not the longer partner (3225)
    assert b["faces_a"] == ["A"] and b["faces_b"] == ["B1", "B2"] and b["handles"] == ["A", "B1", "B2"]
    assert not res["unpaired"]
    conserved(res, faces)


def test_gb_mp_03_split_partner_with_physical_gap_is_not_one_band():
    faces = [seg("A", 0, 0, 4000, 0), seg("B1", 0, 300, 1500, 300), seg("B2", 2000, 300, 4000, 300)]
    res = run(faces)
    assert len(res["bands"]) == 2
    assert all(not (b["t0"] < 1600 < b["t1"]) for b in res["bands"])      # nothing spans the gap
    gap = [u for u in res["unpaired"] if u["handle"] == "A"]
    assert len(gap) == 1 and gap[0]["reason"] == "PARTNER_GAP" and gap[0]["length"] == pytest.approx(500)
    assert sum(b["length"] for b in res["bands"]) == pytest.approx(3500)
    conserved(res, faces)


def test_gb_mp_04_split_partner_with_a_valid_face_between_is_a_conflict():
    # B2's strip has a parallel face C strictly between the two faces -> the A-B2 pairing is a CONFLICT
    faces = [seg("A", 0, 0, 4000, 0), seg("B1", 0, 300, 2000, 300), seg("B2", 2000, 300, 4000, 300),
             seg("C", 2500, 150, 3800, 150)]
    res = run(faces)
    assert [c["reason"] for c in res["conflicts"] if set(c["faces"]) == {"A", "B2"}] == ["INTERVENING_FACE"]
    assert len(res["bands"]) == 1 and res["bands"][0]["handles"] == ["A", "B1"]
    assert res["bands"][0]["length"] == pytest.approx(2000)
    reasons = {u["reason"] for u in res["unpaired"] if u["handle"] == "A"}
    assert reasons == {"INTERVENING_FACE"}
    conserved(res, faces)


def test_gb_mp_05_collinear_annotation_line_is_rejected():
    faces = [seg("A", 0, 0, 4000, 0), seg("B", 0, 300, 3000, 300),
             seg("DIM", 3000, 300, 4000, 300, layer="DIM"),         # collinear, contiguous, annotation layer
             seg("TICK", 3000, 300, 3100, 300)]                      # same layer but a 100 mm tick
    res = run(faces)
    assert {(r["handle"], r["reason"]) for r in res["rejected_faces"]} == {("DIM", "LAYER_NOT_ADMITTED"),
                                                                          ("TICK", "SHORT_FACE")}
    assert len(res["bands"]) == 1 and res["bands"][0]["handles"] == ["A", "B"]
    assert res["bands"][0]["length"] == pytest.approx(3000)               # never extended by the annotation
    assert [(u["handle"], u["reason"]) for u in res["unpaired"]] == [("A", "NO_PARTNER")]
    conserved(res, faces)


def test_shared_face_with_partners_on_both_sides_is_ambiguous():
    faces = [seg("A", 0, 0, 3000, 0), seg("UP", 0, 300, 3000, 300), seg("DN", 0, -300, 3000, -300)]
    res = run(faces)
    assert not res["bands"]
    assert {c["reason"] for c in res["conflicts"]} == {"SHARED_FACE_AMBIGUOUS"}
    conserved(res, faces)


def test_merge_stops_at_a_node_crossing_the_split():
    # a cross face spanning the strip exactly at the partner split = a node: two bands, not one
    faces = [seg("A", 0, 0, 4000, 0), seg("B1", 0, 300, 2000, 300), seg("B2", 2000, 300, 4000, 300),
             seg("X", 2000, -50, 2000, 350)]
    res = run(faces)
    assert len(res["bands"]) == 2 and sum(b["length"] for b in res["bands"]) == pytest.approx(4000)


# ------------------------------------------------------------------ arcs
def arc(h, r, d0, d1, *, c=(0.0, 0.0), cw=False, layer="1"):
    return {"handle": h, "layer": layer, "cx": c[0], "cy": c[1], "r": r, "a0": math.radians(d0),
            "a1": math.radians(d1), "cw": cw}


def arun(arcs):
    return GN.pair_arcs(arcs, width=W, tol=TOL, admitted_layers=LAY)


def test_gb_arc_01_identical_sweeps():
    res = arun([arc("I", 1000, 0, 90), arc("O", 1300, 0, 90)])
    (b,) = res["bands"]
    assert b["OVERLAP_RANGE"] == [0.0, 90.0] and b["CENTERLINE_RADIUS"] == pytest.approx(1150)
    assert b["CENTERLINE_ARC_LENGTH"] == pytest.approx(1150 * math.pi / 2)
    assert b["SOURCE_HANDLES"] == ["I", "O"] and b["ARC_A_RANGE"] == [0.0, 90.0]


def test_gb_arc_02_partial_overlap_uses_the_common_range_not_the_longer_sweep():
    res = arun([arc("I", 2250, 96.38, 263.62), arc("O", 2550, 109.75, 259.84)])
    (b,) = res["bands"]
    assert b["OVERLAP_RANGE"] == pytest.approx([109.75, 259.84])
    common = math.radians(259.84 - 109.75)
    assert b["CENTERLINE_ARC_LENGTH"] == pytest.approx(2400 * common)
    longer = 2400 * math.radians(263.62 - 96.38)
    assert b["CENTERLINE_ARC_LENGTH"] < longer
    ends = {(u["handle"], tuple(round(x, 2) for x in u["range_deg"])) for u in res["unpaired"]}
    assert ends == {("I", (96.38, 109.75)), ("I", (259.84, 263.62))}


def test_gb_arc_03_same_radius_region_but_no_overlap():
    res = arun([arc("I", 1000, 0, 80), arc("O", 1300, 100, 170)])
    assert not res["bands"]
    assert [c["reason"] for c in res["conflicts"]] == ["NO_ANGULAR_OVERLAP"]
    assert {u["handle"]: u["reason"] for u in res["unpaired"]} == {"I": "NO_ANGULAR_OVERLAP", "O": "NO_ANGULAR_OVERLAP"}


def test_gb_arc_04_reversed_orientation_and_wraparound():
    # O is given clockwise (from 30 deg back to 300 deg): as CCW it is 300 -> 30 (wraps through 0)
    res = arun([arc("I", 1000, 330, 20), arc("O", 1300, 30, 300, cw=True)])
    (b,) = res["bands"]
    assert b["OVERLAP_RANGE"] == pytest.approx([330.0, 20.0])
    assert b["CENTERLINE_ARC_LENGTH"] == pytest.approx(1150 * math.radians(50))


def test_gb_arc_05_nested_concentric_beams_pair_inner_with_inner():
    res = arun([arc("A1", 1000, 0, 90), arc("A2", 1300, 0, 90), arc("B1", 2250, 0, 90), arc("B2", 2550, 0, 90)])
    assert sorted(b["SOURCE_HANDLES"] for b in res["bands"]) == [["A1", "A2"], ["B1", "B2"]]
    # three faces at the beam pitch: the middle arc would be the face of two beams -> ambiguous, no band
    res = arun([arc("R1", 1000, 0, 90), arc("R2", 1300, 0, 90), arc("R3", 1600, 0, 90)])
    assert not res["bands"] and {c["reason"] for c in res["conflicts"]} == {"SHARED_FACE_AMBIGUOUS"}
    # a third arc strictly between the two faces is an intervening face
    res = arun([arc("I", 1000, 0, 90), arc("M", 1150, 0, 90), arc("O", 1300, 0, 90)])
    assert not res["bands"] and "INTERVENING_FACE" in {c["reason"] for c in res["conflicts"]}
