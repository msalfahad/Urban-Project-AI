"""T-390 R-T390-1: one geometric face per room; open-side (VIRTUAL) metres a face crosswalk puts on a band face line by
tolerance are never face length.

Hand fixture (NOT the development villa; metres). Kitchen K: interior x 0 .. 4.00, y 0 .. 3.00; drawn walls on the west,
north and south; the east side x = 4.00 is an OPEN SIDE (no drawn line) to a living room. Bands (centreline, t):
B-N y 3.10 t 0.20 (face y 3.00) and B-S y -0.10 t 0.20 (face y 0.00), both x -0.10 .. 8.10, continuous past the open
edge; B-SPLIT y 1.50 t 0.20, x -0.10 .. 8.10, a captured band whose middle is NOT built (no masonry inside the rooms).
Walk: 5 mm samples, centres at (k + 0.5) x 0.005.
  contour            = 4.00 + 3.00 + 4.00 + 3.00 = 14.00 m; open side = 3.00 m -> geometric face = 11.00 m (hand)
  crosswalk tolerance 0.025 m on a face line:
    T_JUNCTION at y 3.00 : centres 2.9775 .. 2.9975 = 5 x 0.005 = 0.025 m; at y 0.00: 0.0025 .. 0.0225 = 0.025 m
    CROSSING of B-SPLIT  : faces y 1.40 and 1.60, each 1.3775 .. 1.4225 / 1.5775 .. 1.6225 = 10 x 0.005 = 0.05 m
    artefact total       = 0.025 + 0.025 + 0.05 + 0.05 = 0.15 m
  T-388 (d') construct   : contour - off-line VIRTUAL only = 14.00 - (3.00 - 0.15) = 11.15 m -> false residual -0.15 m
                           (x 3.00 m height = -0.45 m2) against a family length of 11.00
  R-T390-1               : 14.00 - 3.00 = 11.00 m -> residual 0.000
Second fixture: wall face drawn y 0.00 from x 0 to 2.00 (band B-P y -0.075 t 0.15, x 0 .. 2.00), the open side runs on
collinear to x 3.20: END_REACH centres 2.0025 .. 2.0275 = 6 x 0.005 = 0.030 m; physical face 2.00 m.
"""
import csv
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research/agents_t390"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FR = _load("t390_face_length_rule", D / "face_length_rule.py")
X = _load("t390_face_crosswalk", ROOT / "research/agents_t250/face_crosswalk.py")
STEP = 0.005


def _line(a, b, cls):
    L = math.dist(a, b)
    n = round(L / STEP)
    return [(cls, a[0] + (k + 0.5) / n * (b[0] - a[0]), a[1] + (k + 0.5) / n * (b[1] - a[1]), L / n) for k in range(n)]


def _tf(p, mirror=False, rot=False):
    x, y = p
    if mirror:
        x = -x
    if rot:
        x, y = -y, x
    return x, y


def kitchen(mirror=False, rot=False):
    pts = [(0, 0), (4, 0), (4, 3), (0, 3)]
    cls = ["WALL", "VIRTUAL", "WALL", "WALL"]
    ring = []
    for i in range(4):
        ring += _line(_tf(pts[i], mirror, rot), _tf(pts[(i + 1) % 4], mirror, rot), cls[i])
    bands = [{"band": n, "t_m": 0.20, "a": _tf(a, mirror, rot), "b": _tf(b, mirror, rot)}
             for n, a, b in (("B-N", (-0.1, 3.1), (8.1, 3.1)), ("B-S", (-0.1, -0.1), (8.1, -0.1)),
                             ("B-SPLIT", (-0.1, 1.5), (8.1, 1.5)))]
    return ring, X.prepare(bands)


def artefact(ring, bands):
    split = FR.open_side_split([[(c, s) for c, _x, _y, s in ring]])
    runs = FR.cyclic_runs([(c, s) for c, _x, _y, s in ring])
    run_of = {k: j for j, (_c, _l, ix) in enumerate(runs) for k in ix}
    hits, sides = [], {}
    n = len(ring)
    for k, (c, x, y, seg) in enumerate(ring):
        if c != "VIRTUAL":
            continue
        h = X.locate((x, y), bands)
        if h is None:
            continue
        b, s, side, _ = h
        p0, p1 = ring[(k - 1) % n], ring[(k + 1) % n]
        L = math.hypot(p1[1] - p0[1], p1[2] - p0[2])
        hits.append((k, b, s, side, ((p1[1] - p0[1]) / L, (p1[2] - p0[2]) / L), seg))
        sides.setdefault((run_of[k], b["band"]), set()).add(side)
    tot = {}
    for k, b, s, side, d, seg in hits:
        cause = "CORNER" if not split["is_open"][0][k] else FR.artefact_cause(
            d, b["_f"][:2], s, b["_f"][4], sides[(run_of[k], b["band"])])
        tot[(b["band"], cause)] = round(tot.get((b["band"], cause), 0.0) + seg, 4)
    return split, tot


# ------------------------------------------------------------------------------------------------- normal case
@pytest.mark.parametrize("mirror,rot", [(False, False), (True, False), (False, True), (True, True)])
def test_kitchen_geometric_face_and_artefacts_hand(mirror, rot):
    ring, bands = kitchen(mirror, rot)
    split, tot = artefact(ring, bands)
    contour = sum(s for *_r, s in ring)
    assert contour == pytest.approx(14.00, abs=1e-9)
    assert split["open_m"] == pytest.approx(3.00, abs=1e-4) and split["corner_m"] == 0
    assert FR.geometric_face_m(contour, split["open_m"]) == pytest.approx(11.00, abs=1e-4)
    assert tot == {("B-N", "T_JUNCTION"): 0.025, ("B-S", "T_JUNCTION"): 0.025, ("B-SPLIT", "CROSSING"): 0.10}
    art = sum(tot.values())
    assert art == pytest.approx(0.15, abs=1e-9)
    # the T-388 (d') construct: contour less the OFF-LINE virtual only -> a false residual of -0.15 m
    t388_geo = contour - (split["open_m"] - art)
    assert 11.00 - t388_geo == pytest.approx(-0.15, abs=1e-4)
    # R-T390-1: the same family length closes
    c = FR.closure(11.00, contour, split["open_m"], top_m=3.00)
    assert c["ok"] and c["residual_m"] == pytest.approx(0, abs=1e-4) and c["m2"] == pytest.approx(0, abs=1e-3)
    old = FR.closure(11.00, contour, split["open_m"] - art, top_m=3.00)
    assert not old["ok"] and old["m2"] == pytest.approx(-0.45, abs=1e-3)


def test_end_reach_collinear_open_side_past_the_drawn_end():
    bands = X.prepare([{"band": "B-P", "t_m": 0.15, "a": (0.0, -0.075), "b": (2.0, -0.075)}])
    ring = _line((0, 0), (2, 0), "WALL") + _line((2, 0), (3.2, 0), "VIRTUAL") + _line((3.2, 0), (3.2, 1), "WALL") + \
        _line((3.2, 1), (0, 1), "WALL") + _line((0, 1), (0, 0), "WALL")
    split, tot = artefact(ring, bands)
    assert tot == {("B-P", "END_REACH"): 0.03}
    # the drawn face is 2.00: the crosswalk's face (2.00 + 0.03) less the artefact
    face = 2.00 + 0.03 - tot[("B-P", "END_REACH")]
    assert face == pytest.approx(2.00, abs=1e-9)


def test_corner_virtual_run_under_0_10_stays_face():
    seq = [("WALL", 0.005)] * 200 + [("VIRTUAL", 0.005)] * 4 + [("WALL", 0.005)] * 200 + [("VIRTUAL", 0.005)] * 40
    s = FR.open_side_split([seq])
    assert s["corner_m"] == pytest.approx(0.02) and s["open_m"] == pytest.approx(0.20)
    # a run wrapping past the ring start is one run (cyclic): 30 + 10 samples = 0.20 m open, not 0.15 + 0.05
    wrap = [("VIRTUAL", 0.005)] * 10 + [("WALL", 0.005)] * 400 + [("VIRTUAL", 0.005)] * 30
    w = FR.open_side_split([wrap])
    assert w["open_runs"] == [0.2] and w["corner_m"] == 0


def test_on_face_parallel_is_flagged_not_face():
    b = X.prepare([{"band": "B-P", "t_m": 0.15, "a": (0.0, -0.075), "b": (2.0, -0.075)}])[0]
    assert FR.artefact_cause((1.0, 0.0), b["_f"][:2], 1.2, 2.0, {1}) == "ON_FACE_PARALLEL"


# ------------------------------------------------------------------------------------------------- adverse cases
def test_open_side_offered_as_face_is_refused():
    with pytest.raises(FR.FaceLengthError, match="open side offered"):
        FR.face_from_pieces([("WALL", 3.00, "A"), ("VIRTUAL", 0.02, "T-junction samples")])
    assert FR.face_from_pieces([("WALL", 2.995, "A"), ("CORNER", 0.02, "c")]) == pytest.approx(3.015)


def test_face_measured_past_its_drawn_end_into_an_open_side_is_refused():
    with pytest.raises(FR.FaceLengthError, match="past its drawn end"):
        FR.face_end(3.000, 3.015, "VIRTUAL")
    assert FR.face_end(3.000, 3.000, "VIRTUAL") == 3.000
    assert FR.face_end(3.000, 3.200, "WALL") == 3.200        # the wall face continues (drawn): not an end


def test_jamb_return_counted_twice_is_refused():
    assert FR.check_jambs([("K", "J1", 0.15), ("L", "J2", 0.15)]) == pytest.approx(0.30)
    with pytest.raises(FR.FaceLengthError, match="counted twice"):
        FR.check_jambs([("K", "J1", 0.15), ("L", "J1", 0.15)])


def test_units_and_missing_are_refused_never_zero():
    with pytest.raises(FR.FaceLengthError):
        FR.open_side_split([[("WALL", 5.0)] * 10])                # mm steps
    with pytest.raises(FR.FaceLengthError):
        FR.geometric_face_m(14000.0, 3000.0)                       # mm lengths
    with pytest.raises(FR.FaceLengthError):
        FR.closure(None, 14.0, 3.0)                                # missing family length is not 0
    with pytest.raises(FR.FaceLengthError):
        FR.geometric_face_m(3.0, 4.0)                              # open side longer than the contour
    with pytest.raises(FR.FaceLengthError):
        FR.closure(11.0, 14.0, 3.0, top_m=3000)                    # height in mm
    assert FR.closure(11.2, 14.0, 3.0, top_m=None)["m2"] is None   # HELD top: no m2, residual still named


# ------------------------------------------------------------------------------------- development villa (committed)
def _rows(name):
    with open(D / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_development_villa_reconciliation_committed():
    s = json.loads((D / "summary.json").read_text(encoding="utf-8"))
    assert s["guards"] == "PASS" and s["rooms"] == 32 and s["r_t390_open"] == 0 and s["r_t390_explained"] == 2
    assert s["artefact_m_by_cause"] == {"CROSSING": 0.23, "END_REACH": 0.025, "ON_FACE_PARALLEL": 0.0, "T_JUNCTION": 0.16}
    room = {(r["room"], r["family"]): r for r in _rows("ROOM_FACE_T390.csv")}
    for rm, fam, t388, geo in (("GF-07", "tile", -0.12, 10.491), ("GF-08", "plaster", -0.14, 53.188),
                               ("GF-14", "tile", -0.045, 8.267)):
        r = room[(rm, fam)]
        assert float(r["t388_residual_m"]) == pytest.approx(t388, abs=1e-3)
        assert float(r["geometric_face_m (R-T390-1 a)"]) == pytest.approx(geo, abs=1e-3)
        assert abs(float(r["residual_m (R-T390-1)"])) <= 0.001 and r["status"] == "CLOSED"
    art = {(r["room"], r["band"], r["side"]): r for r in _rows("ARTEFACT_T390.csv")}
    # GF-07: -0.120 = the open side crossing the unbuilt WB-FL0007-FL0008 stretch (0.05 per face line) + its T-junction
    # on the GF-W01 face (0.02)
    g7 = [art[("GF-07", "WB-FL0007-FL0008", "+")], art[("GF-07", "WB-FL0007-FL0008", "-")],
          art[("GF-07", "WB-FL0001-FL0002", "+")]]
    assert [float(x["CROSSING_m"]) for x in g7] == [0.05, 0.05, 0.0] and float(g7[2]["T_JUNCTION_m"]) == 0.02
    assert float(g7[2]["corrected_face_m (face - artefact)"]) == pytest.approx(2.995)   # drawn A6 3.000, 5 mm walk
    # GF-14: -0.045 = END_REACH 0.025 past the GF-W28 end + T-junction 0.02 on the GF-W13 face; its 0.01 corner stays
    g14 = art[("GF-14", "WB-FL0030-FL0031", "+")]
    assert float(g14["END_REACH_m"]) == 0.025 and float(g14["corner_m (face)"]) == 0.01
    assert not any(float(r["ON_FACE_PARALLEL_m"]) for r in art.values())
