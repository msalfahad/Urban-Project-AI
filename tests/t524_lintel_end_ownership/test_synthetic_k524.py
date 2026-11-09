"""T-524 fixture K524 (not the training villa): lintel end zones at a column, a cross wall and a shared pier, by hand.

b_min 0.40. T-453 basis L = w + 0.80, concrete B D L, formwork 2 L D + w B.
  K1  w 1.20, B 0.20, D 0.20; START BOUNDED (a 0.90); END runs into a column 0.30 deep at a = 0.10.
      r = 0.30, inside the column min(0.30, 0.30) = 0.30 -> 0.2 x 0.2 x 0.30 = 0.012 m3 (column line), not built 0.
      L lo 1.20 + 0.40 + 0 = 1.60 (0.064), hi 1.20 + 0.40 + 0.10 = 1.70 (0.068); T-453 2.00 (0.080); 0.080 - 0.068 = 0.012.
      formwork hi 2 x 1.70 x 0.20 + 1.20 x 0.20 = 0.92 m2.
  K2  w 0.90, B 0.15, D 0.20; END at a = 0.05 against a column only 0.20 deep: r 0.35 = 0.20 inside + 0.15 beyond
      (a lintel does not pass a column: not built). T-453 0.051; hi 0.03 x 1.35 = 0.0405; 0.0105 = 0.006 + 0.0045.
  K3  w 0.80, B 0.15, D 0.20; START stops 0.25 beyond the jamb at the far face of a 0.15 cross wall: r 0.15 not built
      (0.0045 m3), extension <= 0.25, never 0.40 and never to a column; cross-wall window <= 0.15 x 0.20 = 0.03 m2.
  K4/K5 w 0.90 and 0.70, B 0.15, D 0.20, head 2.20 both, pier 0.30: T-453 zones overlap 0.80 - 0.30 = 0.50 m
      -> 0.015 m3 lintel on lintel; pair hi 0.90 + 0.40 + 0.70 + 0.40 + 0.30 = 2.70 (0.081); T-453 0.051 + 0.045 = 0.096.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t524"))

import t524_lintel_end_ownership as T  # noqa: E402


def lintel(i, w, B, D, start, end, head=2.2, **kw):
    L = w + 0.80
    d = {"id": i, "width_m": w, "B": B, "D": D, "t453_length_m": L, "t453_concrete_m3": round(B * D * L, 6),
         "t453_formwork_m2": round(2 * L * D + w * B, 6), "head_m": head, "ends": [dict(start, side="START"),
                                                                                   dict(end, side="END")]}
    d.update(kw)
    return d


OK = {"state": T.BOUNDED, "available_m": 0.90, "stopper": T.END}


def col(a, along, cid="COL-K"):
    return {"state": T.DEFICIT, "available_m": a, "stopper": T.COLUMN, "host": {"id": cid, "along_m": along}}


def fixture():
    k1 = lintel("K1", 1.20, 0.20, 0.20, OK, col(0.10, 0.30, "COL-K1"))
    k2 = lintel("K2", 0.90, 0.15, 0.20, OK, col(0.05, 0.20, "COL-K2"))
    k3 = lintel("K3", 0.80, 0.15, 0.20, {"state": T.DEFICIT, "available_m": 0.25, "stopper": T.END,
                                         "through_walls": "XW-1"}, OK)
    k4 = lintel("K4", 0.90, 0.15, 0.20, OK, {"state": T.DEFICIT, "available_m": 0.30, "stopper": T.OPENING,
                                             "stopper_id": "K5"})
    k5 = lintel("K5", 0.70, 0.15, 0.20, {"state": T.DEFICIT, "available_m": 0.30, "stopper": T.OPENING,
                                         "stopper_id": "K4"}, OK)
    return [k1, k2, k3, k4, k5], [("K4", "K5")]


def test_column_end_by_hand():
    r = T.assess_lintel(fixture()[0][0])
    e = r["ends"][1]
    assert e["inside_column_m"] == pytest.approx(0.30) and e["not_built_m"] == pytest.approx(0.0)
    assert (r["concrete_lo_m3"], r["concrete_hi_m3"]) == (0.064, 0.068)
    assert r["formwork_hi_m2"] == pytest.approx(0.92) and r["state"] == "HELD_BY_NAME"
    assert e["ext_hi_m"] == pytest.approx(0.10)          # the lintel ends at the column face


def test_shallow_column_rest_not_built():
    r = T.assess_lintel(fixture()[0][1])
    e = r["ends"][1]
    assert e["inside_column_m"] == pytest.approx(0.20) and e["not_built_m"] == pytest.approx(0.15)
    assert r["concrete_hi_m3"] == pytest.approx(0.0405)


def test_end_short_of_support_held_never_extended():
    r = T.assess_lintel(fixture()[0][2])
    e = r["ends"][0]
    assert e["ext_hi_m"] == pytest.approx(0.25) and e["ext_lo_m"] == 0.0
    assert e["not_built_m"] == pytest.approx(0.15) and e["inside_column_m"] == 0.0 and e["host"] is None
    assert e["cross_wall_window_max_m2"] == pytest.approx(0.03) and e["end_stop_face_max_m2"] == pytest.approx(0.03)
    assert r["state"] == "HELD_BY_NAME" and r["concrete_lo_m3"] > 0          # held, never 0


def test_pair_pier_occupied_once():
    out = T.assess_set(*fixture())
    p = out["pairs"][0]
    assert p["t453_overlap_m"] == pytest.approx(0.50) and p["lintel_on_lintel_m3"] == pytest.approx(0.015)
    assert p["length_hi_m"] == pytest.approx(2.70) and p["concrete_hi_m3"] == pytest.approx(0.081)
    assert p["length_lo_m"] == pytest.approx(0.90 + 0.40 + 0.70 + 0.40)


def test_set_conservation_and_destinations():
    s = T.assess_set(*fixture())["summary"]
    assert s["t453_m3"] == pytest.approx(0.080 + 0.051 + 0.048 + 0.051 + 0.045)
    assert s["inside_column_m3"] == {"COL-K1": 0.012, "COL-K2": 0.006}
    assert s["lintel_on_lintel_m3"] == pytest.approx(0.015)
    assert s["not_built_m3"] == pytest.approx(0.0045 + 0.0045)
    assert s["removed_m3"] == pytest.approx(0.012 + 0.006 + 0.015 + 0.009)
    assert s["split_held"] == []


def test_mirror_same_numbers():
    k1 = fixture()[0][0]
    m = copy.deepcopy(k1)
    m["ends"][0], m["ends"][1] = dict(k1["ends"][1], side="START"), dict(k1["ends"][0], side="END")
    a, b = T.assess_lintel(k1), T.assess_lintel(m)
    assert (a["concrete_lo_m3"], a["concrete_hi_m3"], a["formwork_hi_m2"]) == \
           (b["concrete_lo_m3"], b["concrete_hi_m3"], b["formwork_hi_m2"])


def test_jamb_inside_column_never_counted_twice():
    # jamb drawn 0.10 inside a 0.30 deep column, a = 0: span strip 0.10 + end zone min(0.40, 0.30 - 0.10) = 0.20
    k = lintel("K6", 0.60, 0.20, 0.20, col(0.0, 0.30, "COL-K6"), OK, span_in_column_m=0.10, span_column_id="COL-K6")
    s = T.assess_set([k])["summary"]
    assert s["inside_column_m3"]["COL-K6"] == pytest.approx(0.04 * 0.30)    # never more than the column depth
    assert s["not_built_m3"] == pytest.approx(0.04 * 0.20)
    assert T.assess_lintel(k)["length_hi_m"] == pytest.approx(0.50 + 0.40)


def test_column_not_identified_split_held_not_zero():
    k = lintel("K7", 0.80, 0.15, 0.20, OK, {"state": T.DEFICIT, "available_m": 0.10, "stopper": T.COLUMN})
    out = T.assess_set([k])
    assert out["summary"]["split_held"] == ["K7 END"]
    e = out["lintels"]["K7"]["ends"][1]
    assert e["inside_column_m"] is None and e["not_built_m"] is None
    assert out["lintels"]["K7"]["concrete_hi_m3"] == pytest.approx(0.03 * 1.30)


def test_held_end_keeps_t453_basis_in_hi_zero_in_lo():
    k = lintel("K8", 0.80, 0.15, 0.20, OK, {"state": T.HELD, "available_m": 0.64, "stopper": T.END})
    r = T.assess_lintel(k)
    assert (r["length_lo_m"], r["length_hi_m"]) == (1.2, 1.6) and r["state"] == "HELD_BY_NAME"


@pytest.mark.parametrize("mut, msg", [
    (lambda k: k["ends"][1].update(available_m=250), "metres"),
    (lambda k: k["ends"][1].update(available_m=None), "needs its measured"),
    (lambda k: k["ends"][1].update(available_m=0.45), "not a deficit"),
    (lambda k: k.update(t453_length_m=1.90), r"not w \+ 2 b_min"),
    (lambda k: k.update(span_in_column_m=1.20), "net span"),
    (lambda k: k["ends"][1].update(stopper="SEARCH_LIMIT"), "not handled"),
])
def test_refusals(mut, msg):
    k = copy.deepcopy(fixture()[0][0])
    mut(k)
    with pytest.raises(T.Refused, match=msg):
        T.assess_lintel(k)


def test_pair_refusals():
    ls, prs = fixture()
    one = copy.deepcopy(ls)
    one[4]["ends"][0] = dict(OK, side="START")
    with pytest.raises(T.Refused, match="one side only"):
        T.assess_set(one, prs)
    two = copy.deepcopy(ls)
    two[4]["ends"][0]["available_m"] = 0.31
    with pytest.raises(T.Refused, match="two values"):
        T.assess_set(two, prs)
    head = copy.deepcopy(ls)
    head[4]["head_m"] = 2.40
    with pytest.raises(T.Refused, match="heads"):
        T.assess_set(head, prs)
    with pytest.raises(T.Refused, match="without its pair"):
        T.assess_set(ls, [])
    with pytest.raises(T.Refused, match="second record"):
        T.assess_set(ls + [copy.deepcopy(ls[0])], prs)
