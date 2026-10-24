"""T-265 Villa E hand fixture (synthetic, not Alsenan): an exterior ground beam with a printed section, a boundary
band with a '(T&B)' label pair and a corner, a plain band; adverse cases. Hand figures are worked in the comments."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t265"))
import t265_gb_bars as G  # noqa: E402

EXT = {"section_id": "VE_EXT", "source": "Villa E sheet S-5 exterior GB", "applies_to": ["GB_EXTERIOR"],
       "b_m": 0.30, "top": [(3, 16)], "bottom_rows": [[(3, 16)], [(3, 16)]], "stirrup": (8, 0.15),
       "side": {"bars_per_level": 2, "dia_mm": 12, "pitch_m": 0.30}}
BND = {"section_id": "VE_BND", "source": "Villa E sheet S-6 boundary wall A-A", "applies_to": ["BOUNDARY_GB"],
       "b_m": 0.20, "depth_m": 0.40, "top": [(2, 14)], "bottom_rows": [[(3, 16)]], "stirrup": (8, 0.20)}


def comp(rows, c):
    return [r for r in rows if r["component"] == c][0]


def ext_member(L=4.20, D=1.00, **kw):
    m = {"member_id": "VE-E1", "family": "GB_EXTERIOR", "L_m": L, "depth_m": D, "state": G.APPLIES,
         "column_zones": "NONE"}
    m.update(kw)
    return m


def test_exterior_run_by_hand():
    rows = G.population(ext_member(), EXT)
    # 3 d16 x 4.20 x 256/162 = 19.911 kg per 3-bar layer (top, row 1, row 2)
    for c in ("TOP", "BOTTOM_ROW_1", "BOTTOM_ROW_2"):
        assert comp(rows, c)["kg"] == pytest.approx(19.911, abs=1e-3)
        assert comp(rows, c)["status"] == G.RELEASED_LB
    # side: gap 1.00 - 0.041 - 0.082 = 0.877 .. 1.00 - 0.116 - 0.182 = 0.702 -> ceil(g/0.30)-1 = 2 at both ends
    side = comp(rows, "SIDE")
    assert side["n_bars"] == 4 and side["kg"] == pytest.approx(4 * 4.20 * 144 / 162, abs=1e-3)   # 14.933
    tot = sum(r["kg"] for r in rows if r["kg"] is not None)
    assert tot == pytest.approx(74.667, abs=2e-3)   # sum of row-rounded kg
    st = comp(rows, "STIRRUP_COUNT")
    assert st["n_bars"] == "28..29" and st["status"] == G.CONFIRMED_COUNT           # ceil(4.20 / 0.15) = 28
    assert comp(rows, "STIRRUP_MASS")["kg"] is None and comp(rows, "STIRRUP_MASS")["status"] == G.HELD


def test_units_declared_and_converted():
    assert G.length_m(420, "cm") == pytest.approx(4.20)
    assert G.length_m(4200, "mm") == pytest.approx(4.20)
    a = G.population(ext_member(L=G.length_m(4200, "mm")), EXT)
    b = G.population(ext_member(L=4.20), EXT)
    assert [r["kg"] for r in a] == [r["kg"] for r in b]
    with pytest.raises(ValueError):
        G.length_m(4.2, None)


def test_mirror_or_rotation_does_not_change_the_population():
    # the population depends only on the run length and the section; a mirrored / rotated plan gives the same run
    rows1 = G.population(ext_member(member_id="VE-E1"), EXT)
    rows2 = G.population(ext_member(member_id="VE-E1-mirrored"), EXT)
    assert [r["kg"] for r in rows1] == [r["kg"] for r in rows2]


def test_boundary_band_with_corner_and_tb_reading():
    tb = G.tb_reading([(2, 14, "TOP"), (3, 16, "BOTTOM")], {"TOP": 2, "BOTTOM": 3}, 0.20, 0.025, 8)
    assert tb["reading"] == "PER_LAYER_BY_LEADER" and tb["top"] == [(2, 14)] and tb["bottom"] == [(3, 16)]
    assert tb["rejected"][0][0] == "LITERAL_BOTH_LAYERS"     # 5 bars in one 0.20 m layer do not fit
    # L band: long leg 12.50 m owns the corner square, short leg 3.80 m starts at its face
    legs = [("VE-B1", 12.50), ("VE-B2", 3.80)]
    rows = []
    for mid, L in legs:
        rows += G.population({"member_id": mid, "family": "BOUNDARY_GB", "L_m": L, "depth_m": 0.40,
                              "state": G.APPLIES, "column_zones": "UNKNOWN_COUNT"}, BND, stock_m=12.0)
    top = sum(r["kg"] for r in rows if r["component"] == "TOP")
    bot = sum(r["kg"] for r in rows if r["component"] == "BOTTOM_ROW_1")
    assert top == pytest.approx(2 * 16.30 * 196 / 162, abs=1e-3)       # 39.442
    assert bot == pytest.approx(3 * 16.30 * 256 / 162, abs=1e-3)       # 77.274
    sp = [r for r in rows if r["component"].startswith("SPLICES")]
    assert len(sp) == 1 and sp[0]["n_bars"] == 5 and sp[0]["kg"] is None and sp[0]["status"] == G.HELD
    stc = [r for r in rows if r["component"] == "STIRRUP_COUNT"]
    assert all(r["status"] == G.HELD and r["n_bars"] is None for r in stc)   # column count unknown


def test_plain_band_has_no_rebar_line_not_zero():
    rows = G.population({"member_id": "VE-P", "family": "PAVING", "L_m": 5.0, "state": G.PLAIN,
                         "provenance": "S-6 'PLAIN CONC.'"}, None)
    assert rows[0]["status"] == G.NO_REBAR and rows[0]["kg"] is None


def test_adverse_typical_section_on_a_member_it_does_not_name_is_refused():
    with pytest.raises(ValueError, match="never applied"):
        G.population({"member_id": "VE-I1", "family": "GB_INTERIOR", "L_m": 3.0, "depth_m": 0.6,
                      "state": G.APPLIES}, EXT)


def test_adverse_kg_rate_refused():
    with pytest.raises(ValueError, match="rate"):
        G.population(ext_member(kg_per_m3=110), EXT)
    sec = dict(EXT, kg_per_m=17.8)
    with pytest.raises(ValueError, match="rate"):
        G.population(ext_member(), sec)


def test_adverse_invented_lap_refused():
    with pytest.raises(ValueError, match="lap"):
        G.population(ext_member(), dict(EXT, lap={"length_d": 50}))


def test_adverse_missing_depth_holds_side_bars_never_zero():
    rows = G.population(ext_member(D=None), EXT)
    side = comp(rows, "SIDE")
    assert side["status"] == G.HELD and side["kg"] is None
    assert comp(rows, "TOP")["kg"] == pytest.approx(19.911, abs=1e-3)   # depth-independent bars still counted


def test_adverse_knife_edge_depth_holds_side_bars():
    rows = G.population(ext_member(D=0.85), EXT)      # gaps 0.727 -> 2 levels, 0.552 -> 1 level: not invariant
    side = comp(rows, "SIDE")
    assert side["status"] == G.HELD and side["kg"] is None and "[1, 2]" in side["basis"]


def test_adverse_conflict_and_unprinted_members_held():
    for st in (G.CONFLICT, G.NONE_PRINTED):
        rows = G.population({"member_id": "VE-X", "family": "GB_EXTERIOR", "L_m": 2.0, "state": st}, EXT)
        assert len(rows) == 1 and rows[0]["status"] == G.HELD and rows[0]["kg"] is None


def test_adverse_tb_literal_when_drawn_and_fitting_else_conflict():
    wide = G.tb_reading([(2, 12, "TOP"), (2, 12, "BOTTOM")], {"TOP": 4, "BOTTOM": 4}, 0.40, 0.025, 8)
    assert wide["reading"] == "LITERAL_BOTH_LAYERS"
    bad = G.tb_reading([(2, 14, "TOP"), (3, 16, "BOTTOM")], {"TOP": 3, "BOTTOM": 3}, 0.20, 0.025, 8)
    assert bad["reading"] == G.CONFLICT and bad["top"] is None


def test_adverse_missing_length_held():
    rows = G.population(ext_member(L=None), EXT)
    assert rows[0]["status"] == G.HELD and rows[0]["kg"] is None
