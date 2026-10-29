"""T-346 rules R-T346-1 .. 4 on a hand-made villa (NOT the development villa).

Villa M (metres, one datum; hand calculation):
  GF block: ground +-0.00, F.F.L. +0.50, roof +4.00, parapet top +4.50. 1F set back 2.00 m on the side AND the sea:
  1F sea face 8.00 m, +4.00 -> roof +7.00 -> parapet top +7.50. The GF roof band (2.00 m deep) runs along the side and
  the sea (an L); its far end meets a roofed side passage (floor +0.10, slab +4.00 running on over it) closed by a
  0.20 m boundary wall.
  faces  G_END   GF sea face at the band's end, 2.00 m: plinth 0-0.5 1.000 | storey 0.5-4.0 7.000 | parapet 4.0-4.5 1.000
         G_UNDER GF sea face under the 1F, 8.00 m: plinth 4.000 | storey 28.000 | parapet 4.000
         U       1F sea face 8.00 m: storey 4.0-7.0 24.000 | parapet 7.0-7.5 4.000
         P       passage face inside the band, 1.80 m (2.00 - 0.20 boundary wall): plinth 0.1-0.5 0.720 | storey 0.5-4.0
                 6.300 = 7.020
  his rows  a  2.00 x 4.50 = 9.000 (sea group, 'annex face')
            b  one plane 8.20 x 7.00 (+0.50 -> +7.50) = 57.400 (sea group, 'high face')
            c  2 x 2.00 x 4.50 = 18.000 (side group, 'returns of the annex')
  hand   a = G_END 9.000, terms 0.
         b bands: 0.5-4.0 (8.20-8.00) x 3.5 = +0.700; 4.0-4.5 (8.20-16.00) x 0.5 = -3.900 (hidden overlap);
           4.5-7.0 +0.500; 7.0-7.5 +0.100 -> -2.600; drawn in his band 60.000 (57.400 = 60.000 - 2.600); plinth 4.000
           outside his band.
         c = DOUBLE COUNT of G_END 9.000 + P 7.020 + terms 0.200 (datum) + 0.080 + 0.700 (boundary wall 0.20) + 1.000
           (roof runs on above +4.00) = 1.980.
         84.400 = drawn 76.020 + double count 9.000 - 0.620 named terms, residual 0.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t346"))

import freelancer_rows as FR  # noqa: E402

GL, F1L, PL, PG, P1 = "GF", "1F", "PLINTH", "PAR-GF", "PAR-1F"


def villa(scale=1.0):
    s = scale
    return {
        "GE_p": FR.face("G_END/plinth", 2.0 * s, 0.0, 0.5 * s, line=PL),
        "GE_s": FR.face("G_END/storey", 2.0 * s, 0.5 * s, 4.0 * s, line=GL),
        "GE_t": FR.face("G_END/parapet", 2.0 * s, 4.0 * s, 4.5 * s, line=PG),
        "GU_p": FR.face("G_UNDER/plinth", 8.0 * s, 0.0, 0.5 * s, line=PL),
        "GU_s": FR.face("G_UNDER/storey", 8.0 * s, 0.5 * s, 4.0 * s, line=GL),
        "GU_t": FR.face("G_UNDER/parapet", 8.0 * s, 4.0 * s, 4.5 * s, line=PG),
        "U_s": FR.face("U/storey", 8.0 * s, 4.0 * s, 7.0 * s, line=F1L),
        "U_t": FR.face("U/parapet", 8.0 * s, 7.0 * s, 7.5 * s, line=P1),
        "P_p": FR.face("P/plinth", 1.8 * s, 0.1 * s, 0.5 * s, line=PL),
        "P_s": FR.face("P/storey", 1.8 * s, 0.5 * s, 4.0 * s, line=GL),
    }


def ledger(F, order=None):
    L = FR.Ledger()
    L.match("a", 9.0, [F["GE_p"], F["GE_s"], F["GE_t"]], 2.0, 0.0, 4.5, "band end")
    b = [F["GU_s"], F["GU_t"], F["U_s"], F["U_t"], F["GU_p"]]
    L.match("b", 57.4, list(reversed(b)) if order == "rev" else b, 8.2, 0.5, 7.5, "one plane")
    L.double_count("c", 9.0, "G_END/storey", "NW end return = row a")
    L.match("c", 9.0, [F["P_p"], F["P_s"]], 2.0, 0.0, 4.5, "passage end return")
    return L


def test_hand_calculation_and_statement():
    L = ledger(villa())
    a, b, c_dbl, c = L.parts
    assert a["drawn_m2"] == pytest.approx(9.0) and a["residual_terms_m2"] == pytest.approx(0.0)
    assert b["drawn_m2"] == pytest.approx(60.0) and b["drawn_outside_his_band_m2"] == pytest.approx(4.0)
    assert [round(x[4], 6) for x in b["bands"]] == [0.7, -3.9, 0.5, 0.1]
    assert b["residual_terms_m2"] == pytest.approx(-2.6)
    assert c_dbl["kind"] == "DOUBLE_COUNT" and c_dbl["drawn_m2"] == 0.0 and c_dbl["first_claim"] == "a"
    assert c["drawn_m2"] == pytest.approx(7.02)
    assert [round(x[4], 6) for x in c["bands"]] == [0.2, 0.08, 0.7, 1.0]
    st = L.statement({"a": 9.0, "b": 57.4, "c": 18.0})
    assert st["his_total"] == pytest.approx(84.4) and st["drawn_matched"] == pytest.approx(76.02)
    assert st["double_count"] == pytest.approx(9.0) and st["named_terms"] == pytest.approx(-0.62)
    assert st["residual"] == pytest.approx(0.0, abs=1e-9)


def test_face_order_and_millimetres_give_the_same_terms():
    base = ledger(villa()).parts[1]
    rev = ledger(villa(), "rev").parts[1]
    assert [x[4] for x in base["bands"]] == pytest.approx([x[4] for x in rev["bands"]])
    F = villa(1000.0)
    bands, d_in, d_out = FR.plane_bands(8200.0, 500.0, 7500.0,
                                        [F["GU_s"], F["GU_t"], F["U_s"], F["U_t"], F["GU_p"]])
    assert d_in / 1e6 == pytest.approx(60.0) and d_out / 1e6 == pytest.approx(4.0)
    assert sum(x[4] for x in bands) / 1e6 == pytest.approx(-2.6)


# ---------------------------------------------------------------- adverse
def test_adverse_freelancer_row_is_never_a_quantity():
    with pytest.raises(FR.RuleError):
        FR.fill_row("FREELANCER", "c", GL, 18.0, "DRAWING-CONFIRMED")
    # the naive reading 'his 2 x 2.00 x 4.50 is a face' would put 18.000 where the drawing has 7.020 (+10.980)
    ok = FR.fill_row("DRAWING", "P/storey", GL, 6.3, "DRAWING-CONFIRMED")
    assert ok["m2"] == 6.3


def test_adverse_site_wall_never_in_the_house_facade():
    with pytest.raises(FR.RuleError):
        FR.face("boundary", 0.2, 0.1, 4.0, element="BOUNDARY_WALL", line="FIN.EXT.FINISH GF")
    wall = FR.face("boundary", 0.2, 0.1, 4.0, element="SITE_WALL")
    with pytest.raises(FR.RuleError):
        FR.Ledger().match("c", 0.78, [wall], 0.2, 0.1, 4.0, "site wall as a house face")


def test_adverse_one_face_matched_twice_is_refused_and_double_count_needs_a_first_claim():
    F = villa()
    L = FR.Ledger()
    with pytest.raises(FR.RuleError):
        L.double_count("c", 9.0, "G_END/storey", "no first claim")
    L.match("a", 9.0, [F["GE_p"], F["GE_s"], F["GE_t"]], 2.0, 0.0, 4.5, "band end")
    with pytest.raises(FR.RuleError):
        L.match("c", 9.0, [F["GE_p"], F["GE_s"], F["GE_t"]], 2.0, 0.0, 4.5, "same face again")


def test_adverse_parts_must_add_up_and_share_must_be_his_plane():
    F = villa()
    L = FR.Ledger()
    with pytest.raises(FR.RuleError):
        L.match("a", 8.0, [F["GE_s"]], 2.0, 0.0, 4.5, "share not his plane")
    L.match("a", 9.0, [F["GE_p"], F["GE_s"], F["GE_t"]], 2.0, 0.0, 4.5, "band end")
    with pytest.raises(FR.RuleError):
        L.statement({"a": 9.5})


def test_adverse_unresolved_is_never_zero_and_held_has_no_point_value():
    L = FR.Ledger()
    p = L.unresolved("x", 12.0, "no element found")
    assert p["drawn_m2"] is None and p["residual_terms_m2"] is None
    st = L.statement({"x": 12.0})
    assert st["unresolved"] == 12.0 and st["residual"] == pytest.approx(0.0)
    with pytest.raises(FR.RuleError):
        FR.fill_row("DRAWING", "f", GL, 0.0, "HELD")
    with pytest.raises(FR.RuleError):
        FR.fill_row("DRAWING", "f", GL, None, "DRAWING-CONFIRMED")
    assert FR.fill_row("DRAWING", "f", GL, (0.0, 0.75), "HELD")["m2"] == (0.0, 0.75)
    with pytest.raises(FR.RuleError):
        FR.face("missing height", 1.5, 0.0, None)
