"""T-581 on the training villa: every frame-block door on the masonry (wall-end) basis; the T-571 table stands.
Runs from the committed measurement (numbers and DXF handles only); the private drawing is not needed."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_p = ROOT / "research" / "agents_t581" / "t581_width_basis.py"
_s = importlib.util.spec_from_file_location("t581_width_basis_tv", _p)
W = importlib.util.module_from_spec(_s)
sys.modules["t581_width_basis_tv"] = W
_s.loader.exec_module(W)


@pytest.fixture(scope="module")
def res():
    return W.build(None)


def test_every_frame_block_door_listed_once_with_both_widths(res):
    ids = [o["id"] for o in res["openings"]]
    assert len(ids) == 26 == len(set(ids))
    for o in res["openings"]:
        assert o["overall_m"] and o["frame_clear_m"] and o["face_a_gap_m"] and o["face_b_gap_m"]
        assert abs(o["face_a_gap_m"] - o["face_b_gap_m"]) <= 0.005


def test_census_used_one_basis_masonry(res):
    used = {o["id"]: o["census_basis_used"] for o in res["openings"]}
    assert used.pop("D-GF-09") == "UNRESOLVED (" + W.CONFLICT + ")"
    assert len(used) == 25 and set(used.values()) == {"MASONRY (= wall-end gap)"}


def test_d_gf_09_is_a_drawing_conflict_held_with_a_bound(res):
    # insert 3FF: wall ends 46.9 / 946.9 mm on both faces inside the D120 footprint 0 / 1000: frame drawn over masonry
    o = next(o for o in res["openings"] if o["id"] == "D-GF-09")
    assert o["block"] == "D120" and o["overall_m"] == 1.0 and o["face_a_gap_m"] == o["face_b_gap_m"] == 0.9
    assert o["state"] == W.UNRESOLVED and o["wall_ends_sit"] == "INSIDE_FOOTPRINT"
    assert o["masonry_m"] is None and o["lintel_masonry"] is None
    assert o["bound_m"] == [0.9, 1.0] and o["lintel_bound"] == [1.2, 1.5]
    others = [x for x in res["openings"] if x["block"] == "D120" and x["id"] != "D-GF-09"]
    assert len(others) == 4 and all(x["wall_ends_sit"] == "AT_BLOCK_EDGES" and x["masonry_m"] == 1.0 for x in others)
    assert [x["id"] for x in res["openings"] if x["state"] != W.CONFIRMED] == ["D-GF-09"]


def test_t571_table_restated_with_d_gf_09_held(res):
    r = res["restated_owner_0.15"]
    assert [c["id"] for c in r["changes"]] == ["D-GF-09"]
    a = r["after"]
    assert a["no_width"] == ["D-GF-09"] and a["total_at_most_nr"] == 59
    assert a["at_most"][1.2]["GF"] == 12 and a["at_most"][1.5]["GF"] == 9
    lo, hi = r["table_low"], r["table_high"]
    assert lo["total_at_most_nr"] == hi["total_at_most_nr"] == 60
    assert (lo["at_most"][1.2]["GF"], lo["at_most"][1.5]["GF"]) == (13, 9)
    assert (hi["at_most"][1.2]["GF"], hi["at_most"][1.5]["GF"]) == (12, 10)
    assert lo["total_established_nr"] == hi["total_established_nr"] == 16
    assert r["lm_low"] == pytest.approx(91.5) and r["lm_high"] == pytest.approx(91.8)
    # T-571's AT_MOST 91.5 lm is not an upper bound once D-GF-09 may need 1.50: the upper bound is 91.8 lm
    assert r["census_at_most_lm"] == pytest.approx(91.5) and r["census_at_most_is_upper_bound"] is False


def test_refused_bases_beside(res):
    ov = res["beside_block_overall_refused"]
    assert ov["diff_nr"][1.2]["GF"] == -1 and ov["diff_nr"][1.5]["GF"] == 1 and ov["diff_lm"] == pytest.approx(0.3)
    assert [c["id"] for c in ov["changes"]] == ["D-GF-09"]
    fc = res["beside_frame_clear_refused"]
    moved = sorted(c["id"] for c in fc["changes"] if c["piece_old"] != c["piece_new"])
    assert moved == sorted(["D-GF-01", "D-GF-05", "D-GF-06", "D-GF-08", "D-GF-13", "D-1F-02", "D-1F-03", "D-2F-01"])
    assert fc["diff_lm"] == pytest.approx(-2.4)


def test_outside_census_insert_named(res):
    assert set(res["outside_census"]) == {"2D8"}
    hs = {i["handle"] for i in res["inserts"]}
    assert hs == set(W.INSERT_TO_OPENING) | set(res["outside_census"])


def test_stale_map_refused(tmp_path, monkeypatch):
    monkeypatch.setitem(W.INSERT_TO_OPENING, "ZZZ", "D-GF-01")
    with pytest.raises(W.BasisError, match="stale"):
        W.build(None)
