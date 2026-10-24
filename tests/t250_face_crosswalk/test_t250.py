"""T-250: geometric face crosswalk (face length per wall), the room-side line of a curved opening, one datum per face
(rules R-T250-1 .. 3, proposed, any villa). Fixtures are NOT Alsenan; hand truth below.

Villa K250 (metres): outer walls t 0.20 on the centreline rectangle 0..8 x 0..5; partition P t 0.15 on x = 4 from
y = 0 to 5 (T stems on both outer walls). Room A = x 0.10 .. 3.925, y 0.10 .. 4.90; room B = x 4.075 .. 7.90, same y.
Door D 0.80 in P (y 1.00 .. 1.80, both faces); window G 1.20 in the south wall of B (x 5.00 .. 6.20).
  P, side A: room face 4.80 (A, incl. the door 0.80 -> finish 4.00) + inside the two outer walls 0.10 + 0.10 = 5.00.
  South wall, inner side: 0.10 (west wall) + A 3.825 + 0.15 (P) + B 3.825 (window 1.20, finish 2.625) + 0.10 = 8.00.
  South wall, outer side: no room 8.00.  Room contours: A = B = 2 x (3.825 + 4.80) = 17.25, all on straight faces.
Curved opening (villa K250 court): glazed band, pool-side face r 2.00 and glass lines r 2.08 / 2.12 / 2.16 / 2.20 on
one sweep of 2.50 rad; the rooms lie outside r 2.20; a 0.15 partition stops on the glass (0.15 of the arc); the
outer glass line returns 0.05 + 0.05 along the straight wall face to the jambs.
  arcs 5.000 / 5.200 / 5.300 / 5.400 / 5.500; room-side developed = 5.500 + 0.100 - 0.150 = 5.450;
  walked room face 5.452 (sampling); printed window width (pool-side face) 5.000 -> RULE_DIFFERENCE +0.450.
One datum: floor structural top 5.45, slab top above 9.65 -> interval 4.20; slab 0.16 -> plaster 4.04; beam 0.50 ->
block 3.70. A face whose block reading used 4.20 and finish reading 4.15 carries two datums -> refused.
Adverse: mirror, rotation 37 deg + 1 km shift (same results); sample length in mm; thickness in mm; a sample twice;
two lines touched / none touched / a dimension line as the room face / a chord that does not close with the walk;
a HELD datum (never 0); a HELD face length turned into m2.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t250"
sys.path.insert(0, str(HERE))
import face_crosswalk as X  # noqa: E402


# ---------------------------------------------------------------------------------------------------------- fixture
def _tf_ident(p):
    return p


def _tf_mirror(p):
    return (-p[0], p[1])


def _tf_rot(p):
    a = math.radians(37.0)
    return (p[0] * math.cos(a) - p[1] * math.sin(a) + 1000.0, p[0] * math.sin(a) + p[1] * math.cos(a) - 800.0)


def _walk(poly, cls_of, step=0.005):
    """samples along a closed polygon ring (mid-points of 5 mm steps), class from cls_of(point, edge index)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.dist(a, b)
        k = max(1, int(round(L / step)))
        h = L / k
        for j in range(k):
            t = (j + 0.5) / k
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            out.append((cls_of(p, i), p[0], p[1], h, 0))
    return out


def villa(tf):
    A = [(0.10, 0.10), (3.925, 0.10), (3.925, 4.90), (0.10, 4.90)]
    B = [(4.075, 0.10), (7.90, 0.10), (7.90, 4.90), (4.075, 4.90)]

    def cA(p, i):
        return "DOOR" if i == 1 and 1.0 <= p[1] <= 1.8 else "WALL"

    def cB(p, i):
        if i == 3 and 1.0 <= p[1] <= 1.8:
            return "DOOR"
        if i == 0 and 5.0 <= p[0] <= 6.2:
            return "WINDOW"
        return "WALL"

    samples = {}
    for name, poly, f in (("A", A, cA), ("B", B, cB)):
        samples[name] = [(c, *tf((x, y)), h, r) for c, x, y, h, r in _walk(poly, f)]
    bands = [{"band": "S", "t_m": 0.20, "a": tf((0, 0)), "b": tf((8, 0))},
             {"band": "N", "t_m": 0.20, "a": tf((0, 5)), "b": tf((8, 5))},
             {"band": "W", "t_m": 0.20, "a": tf((0, 0)), "b": tf((0, 5))},
             {"band": "E", "t_m": 0.20, "a": tf((8, 0)), "b": tf((8, 5))},
             {"band": "P", "t_m": 0.15, "a": tf((4, 0)), "b": tf((4, 5))}]
    return samples, X.prepare(bands)


def side_of(faces, band, room):
    for (b, s), f in faces.items():
        if b == band and room in f:
            return s
    return None


TFS = [_tf_ident, _tf_mirror, _tf_rot]


# ------------------------------------------------------------------------------------------------ (a) face lengths
@pytest.mark.parametrize("tf", TFS)
def test_partition_face_closes_to_the_run(tf):
    samples, bands = villa(tf)
    faces, un, _ = X.assign_samples(samples, bands)
    assert not any(sum(v.values()) > 1e-9 for v in un.values())
    P = next(b for b in bands if b["band"] == "P")
    sA = side_of(faces, "P", "A")
    c = X.close_side(P, sA, 0.0, 5.0, faces[("P", sA)], bands, [])
    assert c["ROOM"]["A"] == pytest.approx(4.80, abs=0.006)
    assert sum(c["JUNCTION"].values()) == pytest.approx(0.20, abs=0.006)
    assert set(c["JUNCTION"]) == {"S", "N"}
    assert abs(c["residual_m"]) < 1e-9
    bc = faces[("P", sA)]["A"]["by_class"]
    assert bc["DOOR"] == pytest.approx(0.80, abs=0.006)
    assert bc["WALL"] == pytest.approx(4.00, abs=0.006)


@pytest.mark.parametrize("tf", TFS)
def test_south_wall_both_sides(tf):
    samples, bands = villa(tf)
    faces, _, _ = X.assign_samples(samples, bands)
    S = next(b for b in bands if b["band"] == "S")
    s_in = side_of(faces, "S", "A")
    c = X.close_side(S, s_in, 0.0, 8.0, faces[("S", s_in)], bands, [])
    assert c["ROOM"]["A"] == pytest.approx(3.825, abs=0.006)
    assert c["ROOM"]["B"] == pytest.approx(3.825, abs=0.006)
    assert c["JUNCTION"]["P"] == pytest.approx(0.15, abs=0.006)
    assert c["JUNCTION"]["W"] + c["JUNCTION"]["E"] == pytest.approx(0.20, abs=0.006)
    assert faces[("S", s_in)]["B"]["by_class"]["WINDOW"] == pytest.approx(1.20, abs=0.006)
    out = X.close_side(S, -s_in, 0.0, 8.0, faces.get(("S", -s_in), {}), bands, [])
    assert out["NO_ROOM"] == pytest.approx(8.00, abs=0.006)
    assert out["ROOM"] == {}


@pytest.mark.parametrize("tf", TFS)
def test_room_contour_closes_from_the_room_side(tf):
    samples, bands = villa(tf)
    faces, un, _ = X.assign_samples(samples, bands)
    for room in ("A", "B"):
        on = sum(f[room]["by_class"][k] for f in faces.values() if room in f for k in f[room]["by_class"])
        assert on + sum(un.get(room, {}).values()) == pytest.approx(17.25, abs=1e-6)


def test_split_by_piece_and_stretch():
    samples, bands = villa(_tf_ident)
    faces, _, _ = X.assign_samples(samples, bands)
    P = next(b for b in bands if b["band"] == "P")
    sA = side_of(faces, "P", "A")
    parts = X.split_by_piece(faces[("P", sA)], [(0.0, 1.0, 0), (1.8, 5.0, 1)])    # the band split at the door
    assert parts[0]["A"]["m"] + parts[1]["A"]["m"] + parts[None]["A"]["m"] == pytest.approx(4.80, abs=1e-6)
    assert parts[None]["A"]["by_class"]["DOOR"] == pytest.approx(0.80 - 2 * X.END_REACH_M, abs=0.006)


def test_units_and_duplicates_refused():
    samples, bands = villa(_tf_ident)
    with pytest.raises(X.CrosswalkError):
        X.prepare([{"band": "Z", "t_m": 200, "a": (0, 0), "b": (1, 0)}])
    bad = {"A": [("WALL", 0.10, 0.10, 5.0, 0)]}
    with pytest.raises(X.CrosswalkError):
        X.assign_samples(bad, bands)
    dup = {"A": [samples["A"][0], samples["A"][0]]}
    with pytest.raises(X.CrosswalkError):
        X.assign_samples(dup, bands)
    with pytest.raises(X.CrosswalkError):
        X.assign_samples({"A": [("PAINT", 1.0, 0.1, 0.005, 0)]}, bands)


def test_column_proud_of_the_face_is_named():
    samples, bands = villa(_tf_ident)
    faces, _, _ = X.assign_samples(samples, bands)
    S = next(b for b in bands if b["band"] == "S")
    s_out = -side_of(faces, "S", "A")
    col = [(2.0, -0.20), (2.4, -0.20), (2.4, 0.10), (2.0, 0.10)]   # a column projecting 0.10 beyond the outer face
    c = X.close_side(S, s_out, 0.0, 8.0, {}, bands, [col])
    assert c["COLUMN"] == pytest.approx(0.40, abs=0.006)


# --------------------------------------------------------------------------------------- (b) curved room-side line
def _cands(touch_outer=5.5 - 0.15, touch_inner=0.0, dim=False):
    c = [{"id": "PF r2.00", "kind": "DIMENSION" if dim else "BAND_FACE", "arc_m": 5.000, "touch_m": 0.0}]
    for r, t in ((2.08, 0.0), (2.12, touch_inner), (2.16, 0.0), (2.20, touch_outer)):
        c.append({"id": f"G r{r:.2f}", "kind": "GLASS", "arc_m": r * 2.5, "touch_m": t})
    return c


def test_room_side_line_normal():
    rec = X.room_side_line(_cands(), 5.452, jamb_returns_m=0.10, partition_ends_m=0.15, printed_width_m=5.0)
    assert rec["room_face_id"] == "G r2.20"
    assert rec["developed_m"] == pytest.approx(5.45, abs=1e-9)
    assert rec["finish_minus_window_m"] == pytest.approx(0.45, abs=1e-9)
    assert rec["verdict"] == "RULE_DIFFERENCE"
    assert "G r2.12" in rec["refused"] and "PF r2.00" in rec["refused"]


def test_room_side_line_adverse():
    with pytest.raises(X.CrosswalkError):          # two lines touched by the rooms: not one room face
        X.room_side_line(_cands(touch_inner=5.0), 5.452, 0.10, 0.15)
    with pytest.raises(X.CrosswalkError):          # no line touched: the room face is not drawn
        X.room_side_line(_cands(touch_outer=0.0), 5.452, 0.10, 0.15)
    with pytest.raises(X.CrosswalkError):          # the printed width's line offered as the room face
        X.room_side_line([{"id": "PF", "kind": "DIMENSION", "arc_m": 5.0, "touch_m": 5.0}], 5.0)
    with pytest.raises(X.CrosswalkError):          # the chord (or the window width) does not close with the walk
        X.room_side_line(_cands(), 5.452 - 0.45, 0.10, 0.15)


# ------------------------------------------------------------------------------------------- (c) one datum per face
def test_one_datum_normal_and_held():
    f = {"floor_top": (5.45, "DRAWING-CONFIRMED"), "ceiling_top": (9.65, "DRAWING-CONFIRMED"), "slab_t": 0.16,
         "member_d": 0.50, "readings": {"block": 4.20, "finish": 4.20}}
    r = X.one_datum(f)
    assert r["interval"] == pytest.approx(4.20) and r["plaster_h"] == pytest.approx(4.04) and r["block_h"] == pytest.approx(3.70)
    h = X.one_datum(dict(f, ceiling_top=(None, X.HELD)))
    assert h["status"] == X.HELD and h["block_h"] is None and h["plaster_h"] is None and h["interval"] is None
    assert "slab top above" in h["missing"]


def test_two_datums_on_one_face_refused():
    f = {"floor_top": (5.45, "DRAWING-CONFIRMED"), "ceiling_top": (9.65, "DRAWING-CONFIRMED"), "slab_t": 0.16,
         "readings": {"block": 4.20, "finish": 4.15}}
    with pytest.raises(X.CrosswalkError):
        X.one_datum(f)
    with pytest.raises(X.CrosswalkError):          # mm
        X.one_datum({"floor_top": (5450, "DRAWING-CONFIRMED"), "ceiling_top": (9650, "DRAWING-CONFIRMED"), "slab_t": 160})


def test_held_face_never_becomes_zero_m2():
    assert X.sensitivity_m2(4.80, 0.01) == pytest.approx(0.048)
    with pytest.raises(X.CrosswalkError):
        X.sensitivity_m2(None, 0.01)


# --------------------------------------------------------------------------------- committed Alsenan outputs (data)
def _csv(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8")))


def test_alsenan_outputs_close():
    s = json.loads((HERE / "summary.json").read_text())
    assert s["rooms"] == 32 and s["room_closure_max_abs_m"] <= 0.002
    assert s["wall_sides"] == s["wall_sides_closed"]
    for r in _csv("WALL_SIDE_CLOSURE_T250.csv"):
        assert abs(float(r["residual_m"])) <= X.RESIDUAL_OK_M
    w03 = next(r for r in _csv("CURVED_ROOM_SIDE_T250.csv") if r["opening"] == "W03")
    lo, hi = (float(v) for v in w03["developed_room_side_m"].split(" .. "))
    assert lo <= float(w03["t128_walked_m"]) <= hi          # T-128's 6.731 is the room-side line, within sampling
    assert w03["window_line_width_m"] == "6.57"             # owner Q-38 A stays the window line
    w06 = next(r for r in _csv("WINDOW_ROOMS_T250.csv") if r["opening"] == "W06")
    assert w06["touch_m"].startswith("GF-13 ") and ";" not in w06["touch_m"]


def test_alsenan_outputs_hold_no_drawing_coordinates():
    pat = re.compile(r"-?\d{3,}\.\d{3,}")       # an absolute drawing coordinate (|x| >= 100 m with mm digits)
    for p in HERE.glob("*.csv"):
        assert not pat.search(p.read_text(encoding="utf-8")), p.name


def test_room_inside_a_band_strip_is_not_a_face_of_it():
    """adverse (Alsenan GF-16 pattern): a room region that runs between the two lines of a band (a leak into the wall
    strip) lies on the band's FAR face line from the inside; that is the neighbour's face, never this room's."""
    bands = X.prepare([{"band": "Q", "t_m": 0.15, "a": (0.0, 0.0), "b": (2.0, 0.0)}])
    # room R covers y -0.075 .. 1.0 (strip + room beyond); its bottom edge lies on the band's far face y = -0.075
    R = [(0.0, -0.075), (2.0, -0.075), (2.0, 1.0), (0.0, 1.0)]
    rows = [s for s in _walk(R, lambda p, i: "WALL") if abs(s[2] + 0.075) < 1e-9]
    polys = {"R": [{"ext": R, "holes": []}]}
    faces, un, strip = X.assign_samples({"R": rows}, bands, polys)
    assert not faces and strip["R"]["WALL"] == pytest.approx(2.0, abs=1e-6)
    # the same edge seen by a room that lies BELOW the band (outside the strip) is a face
    S = [(0.0, -1.0), (2.0, -1.0), (2.0, -0.075), (0.0, -0.075)]
    rows2 = [s for s in _walk(S, lambda p, i: "WALL") if abs(s[2] + 0.075) < 1e-9]
    faces2, _, strip2 = X.assign_samples({"S": rows2}, bands, {"S": [{"ext": S, "holes": []}]})
    assert sum(f["S"]["by_class"]["WALL"] for f in faces2.values()) == pytest.approx(2.0, abs=1e-6) and not strip2
