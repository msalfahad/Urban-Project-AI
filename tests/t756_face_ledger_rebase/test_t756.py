"""T-756 exterior render / paint face ledger re-base (R-T756-1 .. -4): synthetic box villa by hand (normal + adverse)
and the development villa pinned to the committed outputs (no private input needed).

Box villa B756 (synthetic, not the development villa), by hand:
  plan 10.00 x 8.00 m, one storey band +0.30 -> +3.80 (3.50 m printed); faces N 35.00, E 28.00, S 35.00, W 28.00
  = 126.00 m2 gross; windows W1 / W2 1.20 x 1.50 = 1.80 m2 each on S -> S render 31.40; render total 122.40 m2;
  paint = render face by face (no other finish printed) = 122.40 m2; 4 corners x 3.50 = 14.00 lm.
  Adverse: a parapet screen coplanar with the S face (directions 0, 0, 90, 180, 270) -> still 4 corners, not 5;
  a slab-edge band 3.00 m long whose depth is not printed -> HELD blank (None), never 0, and the line holding it is
  blank with its valued part shown; a stone surround of unprinted material is not deducted from the paint, a printed
  tile panel 2.00 m2 is.
  Index I756: line L-A (FIN.EXT.FINISH, X:facade, m2), L-B (FIN.EXT.PAINT.EDGE, X:corner, lm 14.00).
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t756"
sys.path.insert(0, str(HERE))
import t756_rules as R  # noqa: E402

IDX = [
    {"line_id": "L-A", "item_code": "FIN.EXT.FINISH", "element_id": "X:facade", "unit": "m2"},
    {"line_id": "L-B", "item_code": "FIN.EXT.PAINT.EDGE", "element_id": "X:corner", "unit": "lm"},
]
MAPS = R.index_maps(IDX)
FACES = [("N", "35.00"), ("E", "28.00"), ("S", "31.40"), ("W", "28.00")]


# --- normal: box villa ------------------------------------------------------------------------------------------
def test_box_villa_render_equals_paint_by_hand():
    res = [R.face_paint(f, a, a) for f, a in FACES]
    assert all(r["render"] == r["paint"] for r in res)
    t = R.line_total(res)
    assert t["render"] == t["paint"] == ["122.400000", "122.400000"] and t["blank_faces"] == []


def test_box_villa_four_corners_lm():
    assert R.corners_in_band([0, 90, 180, 270], "3.50") == (4, "14.000000")


def test_mirror_and_order_do_not_move_the_result():
    a = R.line_total([R.face_paint(f, x, x) for f, x in FACES])
    b = R.line_total([R.face_paint(f, x, x) for f, x in reversed(FACES)])
    assert a == b
    assert R.corners_in_band([0, -90, -180, -270], "3.50") == (4, "14.000000")      # mirrored outline


def test_rebase_live_new_free_reason():
    r = R.rebase_all([
        ("f1", {"kind": "LINE", "line_id": "L-A", "item_code": "FIN.EXT.FINISH", "element_id": "X:facade", "unit": "m2"}),
        ("f2", {"kind": "NEW", "line_id": "L-NEW", "element_id": "X:PARAPET_OUTER"}),
        ("f3", {"kind": "NOT_A_FACE", "cite": "pier on the lower roof band"}),
        ("f4", {"kind": "NONE", "cite": "top arrises: no line"}),
    ], MAPS)
    assert [x["state"] for x in r] == ["LIVE", "NEW_FREE", "NOT_A_FACE", "MISSING"]
    assert r[3]["why"] == "top arrises: no line"


def test_edge_delta_closes_the_verdict():
    out = R.apply_deltas({"L-B": ("14.00", "14.00")},
                         [{"line_id": "L-B", "before": ("14.00", "14.00"), "after": ("10.50", "10.50")}],
                         ("-3.50", "-3.50"))
    assert out["L-B"] == (R.D("10.50"), R.D("10.50"))


def test_wire_rows_change_add_keep():
    assert R.wire_row("L-A", "LIVE", None, ("122.4", "122.4"), "DRAWING-CONFIRMED", "B756")["action"] == "CHANGE"
    assert R.wire_row("L-B", "LIVE", ("14", "14"), ("14.000", "14.000"), "HELD", "B756")["action"] == "KEEP"
    w = R.wire_row("L-NEW", "NEW_FREE", None, None, "HELD", "B756")
    assert w["action"] == "ADD" and w["after_state"] == "BLANK" and w["after"] == ""


# --- adverse ----------------------------------------------------------------------------------------------------
def test_coplanar_parapet_screen_is_no_corner():
    assert R.corners_in_band([0, 0, 90, 180, 270], "0.50") == (4, "2.000000")


def test_unprinted_slab_band_is_held_never_zero():
    assert R.band_m2("3.00", None) is None
    res = [R.face_paint("N", "35", "35"), R.face_paint("SLAB", None, None)]
    t = R.line_total(res)
    assert t["render"] is None and t["paint"] is None and t["blank_faces"] == ["SLAB"]
    assert t["valued_part"]["paint"] == ["35.000000", "35.000000"]


def test_unprinted_stone_not_deducted_printed_tile_is():
    assert R.face_paint("S", "31.40", "31.40", "1.30", "1.30", printed=False)["paint"] == ["31.400000", "31.400000"]
    assert R.face_paint("S", "31.40", "31.40", "2.00", "2.00", printed=True)["paint"] == ["29.400000", "29.400000"]


@pytest.mark.parametrize("lo,hi", [("0", "0"), ("-1", "2"), ("5", "4"), ("3", None)])
def test_bad_face_bounds_refused(lo, hi):
    with pytest.raises(R.RuleError):
        R.face_paint("F", lo, hi)


def test_zero_lower_bound_is_a_bound_not_a_value():
    assert R.face_paint("BOUNDARY", "0", "0.60")["state"] == "BOUNDED"


@pytest.mark.parametrize("h", ["3500", "0", "-1"])
def test_mm_read_as_m_refused(h):
    with pytest.raises(R.RuleError):
        R.corners_in_band([0, 90, 180, 270], h)
    with pytest.raises(R.RuleError):
        R.band_m2("3.00", h)


def test_stale_absent_and_changed_and_collision():
    a = R.rebase("x", {"kind": "LINE", "line_id": "L-GONE"}, MAPS)
    b = R.rebase("y", {"kind": "LINE", "line_id": "L-A", "element_id": "Y:facade"}, MAPS)
    c = R.rebase("z", {"kind": "NEW", "line_id": "L-Z", "element_id": "X:facade"}, MAPS)
    d = R.rebase("w", {"kind": "NEW", "line_id": "L-A", "element_id": "Q:new"}, MAPS)
    assert [a["state"], b["state"], c["state"], d["state"]] == ["STALE", "STALE", "COLLISION", "COLLISION"]


def test_rows_never_dropped_or_doubled():
    with pytest.raises(R.RuleError):
        R.rebase_all([("f", {"kind": "NONE"}), ("f", {"kind": "NONE"})], MAPS)
    with pytest.raises(R.RuleError):
        R.rebase("", {"kind": "NONE"}, MAPS)
    with pytest.raises(R.RuleError):
        R.rebase("f", {"kind": "NOT_A_FACE"}, MAPS)                # a reason without its record
    with pytest.raises(R.RuleError):
        R.index_maps(IDX + IDX[:1])


def test_delta_refusals():
    v = {"L-B": ("14.00", "14.00")}
    with pytest.raises(R.RuleError):        # total does not close the verdict
        R.apply_deltas(v, [{"line_id": "L-B", "before": ("14", "14"), "after": ("10.5", "10.5")}], ("-2.6", "-2.6"))
    with pytest.raises(R.RuleError):        # before differs from the index
        R.apply_deltas(v, [{"line_id": "L-B", "before": ("13", "13"), "after": ("10.5", "10.5")}], ("-2.5", "-2.5"))
    with pytest.raises(R.RuleError):        # absent line
        R.apply_deltas(v, [{"line_id": "L-X", "before": ("1", "1"), "after": ("0.5", "0.5")}], ("-0.5", "-0.5"))
    with pytest.raises(R.RuleError):        # applied twice
        R.apply_deltas(v, [{"line_id": "L-B", "before": ("14", "14"), "after": ("10.5", "10.5")}] * 2, ("-7", "-7"))


def test_wire_refusals():
    with pytest.raises(R.RuleError):
        R.wire_row("L-A", "LIVE", None, ("1", "1"), "VERIFIED", "s")
    with pytest.raises(R.RuleError):
        R.wire_row("L-A", "LIVE", None, ("1", "1"), "HELD", "")
    with pytest.raises(R.RuleError):
        R.wire_row("L-N", "NEW_FREE", ("1", "1"), ("1", "1"), "HELD", "s")
    with pytest.raises(R.RuleError):
        R.wire_row("L-N", "NEW_FREE", None, ("1", "1"), "HELD", "s", free=False)
    with pytest.raises(R.RuleError):
        R.wire_row("L-S", "STALE", None, ("1", "1"), "HELD", "s")


# --- development villa (pinned, no private input) ---------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    import t756_alsenan as A
    return A, A.build(), A.render()


def test_alsenan_outputs_rebuild_byte_identical(built):
    A, _, files = built
    for n, t in files.items():
        assert (A.OUT / n).read_text() == t, n


def test_alsenan_rebase_complete_and_not_stale(built):
    _, (tables, s, _, _), _ = built
    assert s["stale_or_collision"] == 0
    assert s["A_faces"]["t305_rows"] == 98 and s["A_faces"]["rows_out"] == 128
    assert s["A_faces"]["states"] == {"LIVE": 52, "NEW_FREE": 74, "NOT_A_FACE": 2}
    keys = {r["t305_key"] for r in tables["face_map"] if r["t305_key"]}
    assert len(keys) == 98                       # every T-305 row present, none dropped
    assert s["A_components"]["t311_rows"] == 46
    assert {r["component"] for r in tables["component_map"]} == {
        r["component"] for r in csv.DictReader(open(ROOT / "research/agents_t311/COMPONENT_OWNER_T311.csv"))}
    assert s["A_openings"]["rows"] == 39


def test_alsenan_edge_deltas_equal_t754(built):
    _, (tables, s, _, _), _ = built
    t754 = json.loads((ROOT / "research/agents_t754/out/T754_EDGE_RESIDUALS.json").read_text())
    assert s["B_edges"]["corners_after"] == t754["corners"]["after_physical"]
    assert s["B_edges"]["corners_before"] == t754["corners"]["before_physical"]
    ch = [e for e in tables["edge_deltas"] if e["delta"] and e["delta"] != "0.000000 .. 0.000000"]
    assert [(e["line_id"], e["delta"]) for e in ch] == [("L-d8a40db59611b0508dbc", "-2.600000 .. -2.600000")]
    assert s["B_edges"]["windows_lm"] == "103.682251"


def test_alsenan_render_equals_paint_and_held_faces(built):
    _, (tables, s, _, _), _ = built
    assert s["C_faces"]["render_minus_paint"] == ["0.000000", "0.000000"]
    assert s["C_faces"]["paint"] == ["1009.110254", "1087.619176"]
    for p in tables["face_paint"]:
        assert p["render"] == p["paint"]
        if not p["paint"]:
            assert p["cause"] and "SLAB_EDGE" in p["face_id"]
    assert len(s["C_faces"]["blank"]) == 6


def test_alsenan_wire_table(built):
    _, (tables, s, _, _), _ = built
    assert (s["D_wire"]["change"], s["D_wire"]["add"], s["D_wire"]["edge_change"]) == (3, 15, 1)
    for w in tables["wire"]:
        assert w["evidence"] not in ("VERIFIED", "RELEASED")
    blank = [w for w in tables["wire"] if w["unit"] == "m2" and not w["after"]]
    assert [w["key"] for w in blank] == ["NEW FIN.EXT.FINISH SLAB-EDGE 1F"]
    assert s["E_recheck"]["by_index"]["V3.0.77"] == {"changed": [], "absent": 0, "new_taken": []}
    for v in ("V3.0.73", "V3.0.74", "V3.0.75", "V3.0.76"):
        assert s["E_recheck"]["by_index"][v]["changed"] == []
