"""R-T789-1 on a synthetic villa (not Alsenan): parapet masonry = complement of the parapet concrete reading."""
import importlib.util, pathlib, pytest

_P = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t789/t789_rules.py"
_s = importlib.util.spec_from_file_location("t789_rules", _P)
R = importlib.util.module_from_spec(_s); _s.loader.exec_module(R)

# hand fixture: roof with 3 runs, t 0.20; b_edge default 0.175; upstand 0.30
#  A 10.00 m printed 1.00 ; B 6.00 m printed 0.50 ; C 4.00 m no print -> default 1.20
RUNS = [(10.0, 0.20, 1.00), (6.0, 0.20, 0.50), (4.0, 0.20, None)]


def _tot(material):
    out = [R.run_split(L, t, material, h, upstand=0.30) for L, t, h in RUNS]
    return sum(o["conc_m3"] for o in out), sum(o["block_m2"] for o in out), [o["h_label"] for o in out]


def test_normal_all_rc_no_masonry():
    conc, block, labels = _tot("ALL_RC")
    # by hand: 2.00 x 1.175 + 1.20 x 0.675 + 0.80 x 1.375 = 2.35 + 0.81 + 1.10 = 4.26 m3
    assert conc == pytest.approx(4.26, abs=1e-9)
    assert block == 0.0
    assert labels == ["DRAWING-READ", "DRAWING-READ", "DEFAULT"]


def test_normal_p1_block_above_upstand():
    conc, block, _ = _tot("P1_UPSTAND")
    # block: 10 x 0.875 + 6 x 0.375 + 4 x 1.075 = 8.75 + 2.25 + 4.30 = 15.30 m2; concrete 20 m x 0.2 x 0.30 = 1.20 m3
    assert block == pytest.approx(15.30, abs=1e-9)
    assert conc == pytest.approx(1.20, abs=1e-9)


def test_never_in_both_trades_same_total_height():
    for L, t, h in RUNS:
        a = R.run_split(L, t, "ALL_RC", h)
        b = R.run_split(L, t, "P1_UPSTAND", h, upstand=0.30)
        assert a["conc_m3"] == pytest.approx(b["conc_m3"] + b["block_m2"] * t)


def test_adverse_section_prints_lower_parapet_drawing_wins():
    d = R.run_split(5.0, 0.2, "P1_UPSTAND", None, upstand=0.30)      # default 1.20
    s = R.run_split(5.0, 0.2, "P1_UPSTAND", 0.60, upstand=0.30)      # section prints 0.60
    assert s["h_label"] == "DRAWING-READ" and s["block_m2"] == pytest.approx(5 * 0.475)
    assert s["block_m2"] < d["block_m2"]


def test_adverse_upstand_taller_than_parapet_gives_zero_block_not_negative():
    o = R.run_split(3.0, 0.2, "P1_UPSTAND", 0.05, b_edge=0.0, upstand=0.30)
    assert o["block_m2"] == 0.0 and o["conc_m3"] == pytest.approx(3 * 0.2 * 0.05)


@pytest.mark.parametrize("args", [
    (None, 0.2, "ALL_RC", 1.0), (0.0, 0.2, "ALL_RC", 1.0), (5.0, None, "ALL_RC", 1.0),
    (5.0, 0.2, None, 1.0), (5.0, 0.2, "BRICK?", 1.0), (5.0, 0.2, "ALL_RC", 1200.0),
])
def test_adverse_missing_or_bad_data_raises_never_zero(args):
    with pytest.raises(ValueError):
        R.run_split(*args)


def test_adverse_p1_without_upstand_raises():
    with pytest.raises(ValueError):
        R.run_split(5.0, 0.2, "P1_UPSTAND", 1.0)


def test_mirror_and_order_do_not_change_totals():
    a = _tot("P1_UPSTAND")[:2]
    RUNS.reverse()
    try:
        assert _tot("P1_UPSTAND")[:2] == pytest.approx(a)
    finally:
        RUNS.reverse()
