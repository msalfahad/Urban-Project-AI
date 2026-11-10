"""T-669: owner of an exterior corner square with no column (R-T669-1), the drawn lower end of a roof-storey column
(R-T669-2) and the census of every B10 line HELD in V3.0.63 (research/agents_t669). Hand villa "V669" (not the
training villa) with normal and adverse cases, then the development-villa ledger rebuilt from committed files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t669"))
import t669_rules as R  # noqa: E402
import t669_alsenan as A  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t669" / "out" / "T669_LEDGER.json"

# ---- villa "V669" (hand) -----------------------------------------------------------------------------------------
# An L corner of two exterior ground-beam runs, 0.25 wide, no column at the corner (origin = outer corner).
#   run N (along y): outer edge x 0 from y 0 to 6.00, inner edge x 0.25 from y 0 to 5.75 -> both edges cross the square
#   run E (along x): outer edge y 0 from x 0 to 8.00, inner edge y 0.25 from x 0.25 (stops on run N's inner edge)
#   square 0.25 x 0.25 -> owner run N; its first span 0.25 .. 2.25 (2.00 m to a column) becomes 2.25 m
#   prism at a 0.40 floor: 2.00 x 0.25 x 0.40 = 0.200000 -> 2.25 x 0.25 x 0.40 = 0.225000 (+0.025000 = the square)
SQ = ("0", "0", "0.25", "0.25")
RUN_N = R.both_edges_box("y", ("0", "0", "6.00"), ("0.25", "0", "5.75"))
RUN_E = R.both_edges_box("x", ("0", "0", "8.00"), ("0.25", "0.25", "8.00"))


def _t(b):  # mirror about the corner diagonal (x <-> y): a rotated / mirrored villa
    return None if b is None else (b[1], b[0], b[3], b[2])


def test_hand_corner_normal():
    assert RUN_N == (D("0"), D("0"), D("0.25"), D("5.75"))   # common extent of the two edges
    assert RUN_E == (D("0.25"), D("0"), D("8.00"), D("0.25"))
    assert R.corner_owner(SQ, runs=[("N", RUN_N), ("E", RUN_E)]) == ("RUN", "N")
    span = R.span_with_square("2.00", "0.25")
    assert span == D("2.25")
    assert R.prism("2.00", "0.25", "0.40") == D("0.200000")
    assert R.prism(span, "0.25", "0.40") - R.prism("2.00", "0.25", "0.40") == R.prism("0.25", "0.25", "0.40")


def test_hand_corner_mirror_rotation():
    assert R.corner_owner(_t(SQ), runs=[("N", _t(RUN_N)), ("E", _t(RUN_E))]) == ("RUN", "N")
    # translated by (+3.0, -1.5): the owner does not depend on the frame
    sh = lambda b: (D(b[0]) + 3, D(b[1]) - D("1.5"), D(b[2]) + 3, D(b[3]) - D("1.5"))  # noqa: E731
    assert R.corner_owner(sh(SQ), runs=[("N", sh(RUN_N)), ("E", sh(RUN_E))]) == ("RUN", "N")


def test_adverse_corner_inside_column():
    col = ("K1", ("-0.05", "-0.05", "0.30", "0.40"))
    assert R.corner_owner(SQ, runs=[("N", RUN_N), ("E", RUN_E)], columns=[col]) == ("COLUMN", "K1")


def test_adverse_square_partly_in_column():
    with pytest.raises(R.Refused, match="PARTIAL"):
        R.corner_owner(SQ, runs=[("N", RUN_N)], columns=[("K2", ("0.10", "0.10", "0.50", "0.50"))])


def test_adverse_no_run_draws_both_edges():
    run_n_short = R.both_edges_box("y", ("0", "0", "6.00"), ("0.25", "0.25", "5.75"))  # inner edge stops at E's face
    with pytest.raises(R.Refused, match="NONE"):
        R.corner_owner(SQ, runs=[("N", run_n_short), ("E", RUN_E)])


def test_adverse_both_runs_draw_through():
    run_e_through = R.both_edges_box("x", ("0", "0", "8.00"), ("0.25", "0", "8.00"))
    with pytest.raises(R.Refused, match="DOUBLE"):
        R.corner_owner(SQ, runs=[("N", RUN_N), ("E", run_e_through)])


def test_adverse_units_and_missing():
    with pytest.raises(R.Refused, match="mm"):
        R.prism("2250", "0.25", "0.40")
    with pytest.raises(R.Refused, match="never 0"):
        R.prism(None, "0.25", "0.40")
    with pytest.raises(R.Refused):
        R.corner_owner(None, runs=[("N", RUN_N)])
    assert R.both_edges_box("x", ("0", "0", "1"), ("0.25", "2", "3")) is None   # edges share no extent


# column lower end: base +3.50 (fixed), opening head +6.10 printed, slab T 0.15 printed, finished roof +7.00
def test_hand_column_low_normal():
    h_low, m3, h_c = R.column_low(section_min="0.09", base="3.50", opening_top="6.10", slab_t_min="0.15",
                                  finished_top="7.00", single_plane=True)
    assert (h_low, m3, h_c) == (D("2.75"), D("0.247500"), D("3.50"))   # 0.09 x 2.75 ; ceiling 0.09 x 3.50 = 0.315


@pytest.mark.parametrize("kw,match", [
    ({"opening_top": None}, "opening top"),
    ({"slab_t_min": None}, "slab thickness"),
    ({"single_plane": False}, "one drawn plane"),
    ({"base_fixed": False}, "base not fixed"),
    ({"opening_top": "6.95"}, "CONFLICT"),             # 6.95 + 0.15 - 3.50 = 3.60 > 3.50
    ({"slab_t_min": "150"}, "mm"),
    ({"opening_top": "3.20"}, "wrong storey"),          # 3.20 + 0.15 - 3.50 < 0
])
def test_adverse_column_low_refused(kw, match):
    args = dict(section_min="0.09", base="3.50", opening_top="6.10", slab_t_min="0.15", finished_top="7.00",
                single_plane=True)
    args.update(kw)
    with pytest.raises(R.Refused, match=match):
        R.column_low(**args)


# ---- development villa (committed inputs only) ---------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return A.build()


def test_dev_rebuild_equals_committed(doc):
    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(doc, sort_keys=True))


def test_dev_corner_square(doc):
    a = doc["a_corner_square"]
    assert a["owner"]["line_id"] == "L-6bf14711ae0b84d0f8b9" and a["owner"]["kind"] == "RUN"
    assert a["span_m"] == ["1.200000", "1.500000"]
    assert a["floor_m3"] == {"before_V3_0_63": "0.090000", "after": "0.112500", "delta": "0.022500"}
    assert a["square_m3_at_floor"] == a["floor_m3"]["delta"] and a["residual_m3"] == "0.000000"


def test_dev_roof_columns(doc):
    b = doc["b_roof_columns"]
    rows = {r["line"]: r for r in b["rows"]}
    assert len(rows) == 6
    for lid in ("L-d79d17d1", "L-26f6b6f2", "L-33a9b772", "L-919a5749"):
        assert (rows[lid]["low_m3"], rows[lid]["high_m3"]) == ("0.303000", "0.425000")
    assert (rows["L-53f223b0"]["low_m3"], rows["L-53f223b0"]["high_m3"]) == ("0.424200", "0.595000")
    assert rows["L-fad18af6"]["low_m3"] is None and rows["L-fad18af6"]["high_m3"] == "0.506250"
    assert "not printed" in rows["L-fad18af6"]["why_no_low"]
    assert (b["five_2f_low_m3"], b["five_2f_high_m3"]) == ("1.636200", "2.295000")


def test_dev_census_complete_once_never_zero(doc):
    index = json.loads(A.INDEX.read_text(encoding="utf-8"))
    held = {x["line_id"] for x in index["lines"] if x["item_code"] in A.CODE_FAMILY and x["class"] == "HELD"}
    rows = doc["c_census"]["rows"]
    ids = [r["line_id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(held) == 144 and set(ids) == held
    for r in rows:
        assert r["cause_class"] in ("DESIGNER ITEM", "MEASURABLE NOW", "OPEN BOUND") and r["named"]
        if r["bound_V3_0_63"] is None:                 # blank stays blank: never 0
            continue
        assert D(r["bound_V3_0_63"][0]) <= D(r["bound_V3_0_63"][1])
    t = doc["c_census"]["totals"]
    assert (t["bounded"], t["blank"]) == (82, 62)
    assert (t["bounded_low_m3"], t["bounded_high_m3"]) == ("42.203169", "62.166947")
    assert t["by_class"] == {"DESIGNER ITEM": 103, "MEASURABLE NOW": 7, "OPEN BOUND": 34}


def test_dev_no_absolute_drawing_coordinates_or_workbook_text():
    import re
    led = json.loads(OUT.read_text(encoding="utf-8"))
    s = json.dumps({k: led[k] for k in ("a_corner_square", "b_roof_columns")})
    assert not re.search(r"(?<![A-Z0-9@,])\d{4,}\.\d", s)
    assert "xlsx" not in OUT.read_text(encoding="utf-8").lower()
