"""T-754 exterior paint edge residuals (R-T754-1 .. -4): synthetic villa V754 by hand (normal + adverse) and the
development villa pinned to the committed outputs (no private input needed).

Villa V754 (synthetic, not the development villa), by hand:
  door A: w 1.20, h 2.40, frame posts set back 0.10 from the face (drawn), head set back (section) -> 3 edges:
          2 x 2.40 + 1.20 = 6.00 lm
  door B: w 0.90, h 2.10, posts drawn over the full 0.20 depth at the jambs, head drawn full depth -> 0 lm
  door C: as B but no head drawn anywhere -> jambs 0, head HELD 0 .. 0.90 (missing fact named), never 0
  door D: block 1.00 in a 0.90 gap (conflict) -> jambs 0 .. 4.20 + head 0 .. 0.90 = 0 .. 5.10
  slab edge over a porch, 3.50 m: band drawn flush -> 1 arris 3.50; band projecting -> 7.00; one plane -> 0;
          unprinted (hidden behind a parapet) -> HELD blank with its cause, never 0
  screen front: faces 0.60 + 2.80 + 1.10 = 4.50 m, top line projected 4.500 and no vertical in the band
          -> NOT_A_CORNER; the 2.80 face turned 30 deg (projected 2.80 cos 30 = 2.424871) -> the sum 4.50 vs
          4.124871 fails -> CORNER_STANDS; a vertical drawn inside -> CORNER_STANDS
  wall-end arris +2.80 .. +3.20 between a passage face (+0.30 .. +3.20, line P) and a parapet face (+2.30 .. +2.80,
          line Q) -> HOSTED on P; with no face above +2.80 -> NO_HOST; two faces on two lines -> AMBIGUOUS
"""
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t754"
sys.path.insert(0, str(HERE))
import t754_rules as R  # noqa: E402

FACT = "door head section not issued"


# --- R-T754-1 doors ---------------------------------------------------------------------------------------------
def test_door_frame_set_back_three_edges():
    r = R.door_edges("1.20", "2.40", "SET_BACK", "SET_BACK")
    assert r["lm"] == ["6.000000", "6.000000"] and r["state"] == "POINT" and r["missing"] == []


def test_door_frame_full_depth_is_zero():
    r = R.door_edges("0.90", "2.10", "FULL_DEPTH_AT_JAMBS", "FULL_DEPTH")
    assert r["lm"] == ["0.000000", "0.000000"] and r["state"] == "POINT"


def test_door_head_not_drawn_held_never_zero():
    r = R.door_edges("0.90", "2.10", "FULL_DEPTH_AT_JAMBS", "NOT_DRAWN", FACT)
    assert r["lm"] == ["0.000000", "0.900000"] and r["state"] == "HELD_BOUND" and FACT in r["missing"]


def test_door_head_open_must_name_fact():
    with pytest.raises(R.RuleError):
        R.door_edges("0.90", "2.10", "FULL_DEPTH_AT_JAMBS", "NOT_DRAWN")


def test_door_position_conflict_is_bound():
    r = R.door_edges("0.90", "2.10", "POSITION_CONFLICT", "NOT_DRAWN", FACT)
    assert r["jambs"] == ["0.000000", "4.200000"] and r["lm"] == ["0.000000", "5.100000"]
    assert any("gap" in m for m in r["missing"])


def test_door_no_frame_drawn_is_bound():
    r = R.door_edges("1.00", "2.20", "NOT_DRAWN", "NOT_DRAWN", FACT)
    assert r["lm"] == ["0.000000", "5.400000"]


@pytest.mark.parametrize("w,h", [("900", "2.10"), ("0.90", "2100"), ("0", "2.10"), ("-0.9", "2.10")])
def test_door_units_refused(w, h):
    with pytest.raises(R.RuleError):
        R.door_edges(w, h, "SET_BACK", "SET_BACK")


def test_door_missing_size_blank_never_zero():
    r = R.door_edges(None, "2.10", "SET_BACK", "SET_BACK")
    assert r["lm"] is None and r["state"] == "HELD_BLANK"


def test_door_unknown_state_refused():
    with pytest.raises(R.RuleError):
        R.door_edges("0.9", "2.1", "FLUSH", "SET_BACK")


# --- R-T754-2 slab edge -----------------------------------------------------------------------------------------
def test_slab_edge_views():
    assert R.slab_edge_arris("3.50", "BAND_FLUSH")["lm"] == ["3.500000", "3.500000"]
    assert R.slab_edge_arris("3.50", "BAND_PROJECTING")["lm"] == ["7.000000", "7.000000"]
    assert R.slab_edge_arris("3.50", "ONE_PLANE")["lm"] == ["0.000000", "0.000000"]


def test_slab_edge_hidden_is_blank_with_cause():
    r = R.slab_edge_arris("3.50", "NOT_VISIBLE", "hidden behind the GF parapet")
    assert r["lm"] is None and r["state"] == "HELD_BLANK" and "parapet" in r["cause"]


def test_slab_edge_hidden_without_cause_refused():
    with pytest.raises(R.RuleError):
        R.slab_edge_arris("3.50", "NOT_VISIBLE")


def test_slab_edge_mm_refused_and_missing_length_blank():
    with pytest.raises(R.RuleError):
        R.slab_edge_arris("3500", "BAND_FLUSH")
    assert R.slab_edge_arris(None, "BAND_FLUSH")["lm"] is None


# --- R-T754-3 coplanar junction ---------------------------------------------------------------------------------
def test_coplanar_not_a_corner():
    assert R.coplanar_junction(["0.60", "2.80", "1.10"], "4.500", []) == "NOT_A_CORNER"


def test_rotated_face_keeps_corner():
    proj = 0.60 + 2.80 * math.cos(math.radians(30)) + 1.10
    assert R.coplanar_junction(["0.60", "2.80", "1.10"], f"{proj:.6f}", []) == "CORNER_STANDS"


def test_vertical_inside_keeps_corner():
    assert R.coplanar_junction(["0.60", "2.80", "1.10"], "4.500", ["H1"]) == "CORNER_STANDS"


def test_coplanar_needs_inputs():
    with pytest.raises(R.RuleError):
        R.coplanar_junction([], "4.5", [])


# --- R-T754-4 host ----------------------------------------------------------------------------------------------
def test_host_by_band():
    faces = [("passage", "P", "0.30", "3.20"), ("parapet", "Q", "2.30", "2.80")]
    assert R.host_by_band("2.80", "3.20", faces) == ("HOSTED", ["passage"], "P")


def test_no_host_never_neighbour():
    faces = [("parapet", "Q", "2.30", "2.80"), ("storey", "Q", "0.30", "2.30")]
    assert R.host_by_band("2.80", "3.20", faces) == ("NO_HOST", [], None)


def test_ambiguous_host():
    faces = [("a", "P", "0.30", "3.20"), ("b", "Q", "1.00", "3.50")]
    assert R.host_by_band("2.80", "3.20", faces)[0] == "AMBIGUOUS"


def test_host_inverted_interval_refused():
    with pytest.raises(R.RuleError):
        R.host_by_band("3.20", "2.80", [])


# --- development villa (committed outputs) ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    import t754_alsenan as A  # noqa: PLC0415
    return A, A.build()


def test_alsenan_rebuild_matches_committed(built):
    A, d = built
    assert json.dumps(d, indent=1, sort_keys=True) + "\n" == A.OUT_J.read_text()
    assert A.md(d) == A.OUT_M.read_text()


def test_alsenan_doors(built):
    _, d = built
    dr = d["doors"]
    assert dr["total_lm"] == ["0.000000", "12.200000"] == dr["before_lm"]
    assert len(dr["doors"]) == 7
    g9 = next(x for x in dr["doors"] if x["door"] == "D-GF-09")
    assert g9["jamb_state"] == "POSITION_CONFLICT" and g9["lm"] == ["0.000000", "5.300000"]
    assert all(x["jambs"] == ["0.000000", "0.000000"] for x in dr["doors"] if x["door"] != "D-GF-09")
    assert all(x["head"][0] == "0.000000" and Decimal(x["head"][1]) > 0 for x in dr["doors"])


def test_alsenan_corners(built):
    _, d = built
    nw, c = d["nw_parapet"], d["corners"]
    assert nw["verdict"] == "NOT_A_CORNER" and nw["removed_lm"] == ["2.600000", "2.600000"]
    assert nw["verticals_inside_span"] == []
    assert c["after_hosted"] == ["176.935812", "178.135812"] == c["after_physical"]
    assert c["parapet_ends_after"] == "6.585812"
    assert c["stop_end"]["lm"] == ["0.000000", "1.200000"]
    assert d["no_host"]["state"] == "HOSTED" and d["no_host"]["host_line"] == "L-b05f70c92405dbcfbe62"


def test_alsenan_slab_edges_and_railings(built):
    _, d = built
    by = {s["face"]: s for s in d["slab_edge_1f"]}
    assert set(by) == {"NW-1", "NW-2", "NW-3", "NE-1", "NW-4", "SW-1", "NW-5", "SE-1", "SW-2"}
    for k in ("NE-1", "NW-4", "SW-1", "NW-5", "SW-2"):
        assert by[k]["lm"] is None and by[k]["state"] == "HELD_BLANK"
    assert by["SE-1"]["part_lm"] == ["0.000000", "0.000000"] and by["SE-1"]["lm"] is None
    ids = {r["id"] for r in d["railing_ids"]}
    assert ids == {"RL-03", "RL-10"}
    assert d["paint"]["after"] == ["1009.110254", "1087.619176"] and d["paint"]["residual"] == "0.000000"
