"""T-675 MASONRY ROUND 2 (R-T675-1 .. -3). Hand fixture 'Villa K' (not the development villa):

 - a colour-less host 'BELOW_NG:N1' (net AT_LEAST 8.00 m2) created from a structural note printing BLACK block, with the
   four producer lines; a second colour-less host 'X-WALLS:walls t=0.15' with no evidence record;
 - a lintel over a 0.90 m door in a 0.15 m wall, printed bearing 0.40 m each end: START 0.75 m of block (EXACT),
   END 0.18 m to the far face of the wall met (END_OF_MASONRY, DEFICIT); f = 0.92625 x 0.15 x 0.01 = 0.001389375;
   bed 0.40 + [0, 0.18] -> 0.00055575 .. 0.00080583750 m3 (R-T372-1 (5) gave .. 0.0011115);
 - course bands: CC exact 1 dz, OC [0, 1], FU 0 (no increment), UU [0, 1], CF 0;
 - a held piece 1.20 m long with its top not drawn: soffit [0, 1.20 f] = [0, 0.00166725].
Units 8.00 x 12.5 = 100 pcs; mortar one 0.15 leaf 8.00 x 0.15 x 0.07375 = 0.0885 m3, one 0.20 leaf 0.118 m3.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t675", ROOT / "research/agents_t675/t675_masonry_round2.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

F015 = 0.001389375
ALL4 = [T.U_BLACK, T.MORTAR, T.GLUE, T.U_WHITE]
BLACK_NOTE = {"colour": "BLACK", "source": "structural sheet 1 note 3: black block under the boundary beams"}


# ------------------------------------------------------------------------------------------------ R-T675-1
def test_colour_split_black_host_retires_aac_pair():
    s = T.colour_split("BELOW_NG:N1", ALL4, BLACK_NOTE)
    assert s == {T.U_BLACK: "KEEP", T.MORTAR: "KEEP", T.GLUE: T.NA, T.U_WHITE: T.NA}


def test_colour_split_white_host_retires_black_pair():
    s = T.colour_split("W", ALL4, {"colour": "WHITE", "source": "arch note: all walls AAC"})
    assert s[T.GLUE] == s[T.U_WHITE] == "KEEP" and s[T.U_BLACK] == s[T.MORTAR] == T.NA


def test_colour_split_no_evidence_keeps_all_four():
    assert set(T.colour_split("X-WALLS:walls t=0.15", ALL4, None).values()) == {"KEEP"}


@pytest.mark.parametrize("ev", [{"colour": "GREY", "source": "x"}, {"colour": "BLACK", "source": ""},
                                {"colour": "BLACK"}])
def test_colour_split_adverse_evidence_refused(ev):
    with pytest.raises(T.T675Error):
        T.colour_split("H", ALL4, ev)


def test_colour_split_adverse_black_note_on_a_host_with_only_aac_lines():
    with pytest.raises(T.T675Error):
        T.colour_split("H", [T.GLUE, T.U_WHITE], BLACK_NOTE)


def test_conditional_black_by_hand():
    c15, c20 = T.conditional_black(8.00, 0.15), T.conditional_black(8.00, 0.20)
    assert c15["units_at_least_pcs"] == 100.0 and c20["units_at_least_pcs"] == 100.0
    assert c15["mortar_at_least_m3"] == pytest.approx(0.0885, abs=1e-9)
    assert c20["mortar_at_least_m3"] == pytest.approx(0.118, abs=1e-9)


@pytest.mark.parametrize("net,t", [(0.0, 0.15), (-1.0, 0.20), (8.0, 0.10), (8.0, 0.30)])
def test_conditional_black_adverse(net, t):
    with pytest.raises(T.T675Error):
        T.conditional_black(net, t)


def test_conditional_black_no_bound_stays_none():
    assert T.conditional_black(None, 0.15) is None


# ------------------------------------------------------------------------------------------------ R-T675-2
def test_bed_end_exact_and_deficit():
    assert T.bed_end(0.75, "END_OF_MASONRY") == {"state": "EXACT", "low": 0.40, "high": 0.40,
                                                 "why": "available >= bearing"}
    d = T.bed_end(0.18, "END_OF_MASONRY")
    assert (d["state"], d["low"], d["high"]) == ("RANGE", 0.0, 0.18)
    c = T.bed_end(0.079, "COLUMN")
    assert (c["low"], c["high"]) == (0.0, 0.079)
    o = T.bed_end(0.25, "OPENING")
    assert o["high"] == 0.25


def test_bed_lintel_by_hand():
    ends = [T.bed_end(0.75, "END_OF_MASONRY"), T.bed_end(0.18, "END_OF_MASONRY")]
    b = T.bed_lintel(ends, F015)
    assert b["state"] == "RANGE" and b["bearing_low_m"] == 0.40 and b["bearing_high_m"] == 0.58
    assert b["low"] == pytest.approx(0.000556, abs=1e-9) and b["high"] == pytest.approx(0.000806, abs=1e-9)


def test_bed_never_above_the_drawn_masonry():
    for a in (0.0, 0.05, 0.2, 0.39):
        assert T.bed_end(a, "END_OF_MASONRY")["high"] <= a + 1e-12


def test_bed_adverse_no_printed_bearing_read_stays_held():
    b = T.bed_lintel([T.bed_end(None, "COLUMN"), T.bed_end(0.75, "COLUMN")], F015)
    assert b["state"] == "HELD" and b["low"] is None and b["high"] is None


@pytest.mark.parametrize("a,s", [(-0.01, "COLUMN"), (0.2, "JAMB?"), (0.2, "SEARCH_LIMIT")])
def test_bed_adverse_inputs(a, s):
    with pytest.raises(T.T675Error):
        T.bed_end(a, s)


def test_mirror_invariance_of_the_bed():
    e1 = [T.bed_end(0.75, "END_OF_MASONRY"), T.bed_end(0.18, "COLUMN")]
    e2 = list(reversed(e1))
    assert T.bed_lintel(e1, F015) == T.bed_lintel(e2, F015)


# ------------------------------------------------------------------------------------------------ R-T675-3
@pytest.mark.parametrize("ends,want", [("CC", (1, 1)), ("OC", (0, 1)), ("CO", (0, 1)), ("FU", (0, 0)), ("UF", (0, 0)),
                                       ("UU", (0, 1)), ("CF", (0, 0)), ("OO", (0, 1)), ("FF", (0, 0)), ("CU", (0, 1))])
def test_band_bounds(ends, want):
    assert T.band_bounds(ends) == want


@pytest.mark.parametrize("ends", ["C", "CCC", "CX", ""])
def test_band_bounds_adverse(ends):
    with pytest.raises(T.T675Error):
        T.band_bounds(ends)


def test_band_cause_named_or_refused():
    cls, why = T.band_cause("run end | D-9 lintel bearing not established")
    assert cls == "DESIGNER ITEM" and why.startswith("D-9")
    _, both = T.band_cause("east ring sliver | D-7 lintel bearing not established")
    assert "D-7" in both and "dome" in both
    with pytest.raises(T.T675Error):
        T.band_cause("run end | column")


# ------------------------------------------------------------------------------------------------ development villa
@pytest.fixture(scope="module")
def res():
    return T.build()


def test_villa_part_a_four_lines_retired_by_evidence(res):
    na = [r for r in res["part_a"] if r["verdict"] == T.NA]
    assert sorted(r["code"] for r in na) == sorted([T.GLUE, T.U_WHITE] * 2)
    main = {r["code"]: r for r in res["part_a"] if r["host"].endswith("MAIN_S")}
    assert main[T.U_BLACK]["after"] == "HELD blank"
    assert main[T.U_BLACK]["beside_conditional"]["AT_LEAST_pcs"] == pytest.approx(142.3625)
    assert main[T.MORTAR]["beside_conditional"]["AT_LEAST_m3"] == pytest.approx(0.125991, abs=1e-6)
    m = res["totals"]["materials_a"]
    assert m[T.GLUE]["before"]["held"] - m[T.GLUE]["after"]["held"] == 2
    assert m[T.U_WHITE]["after"]["blank"] == m[T.U_WHITE]["before"]["blank"] - 2


def test_villa_bed_tightened_never_widened(res):
    for r in res["part_b"]["lintel_bed"]:
        if r["state"] == "HELD":
            assert (r["low"], r["high"]) == (0.0, pytest.approx(0.001111, abs=1e-6))
            continue
        assert r["low"] == pytest.approx(r["was"][0], abs=1e-6) and r["high"] <= r["was"][1] + 2e-6
    t = res["totals"]["lintel_bed_m3"]
    assert t["after_8_lintels"] == [pytest.approx(0.006113, abs=1e-6), pytest.approx(0.007628, abs=1e-6)]
    assert t["after_bearing_m"] == [4.4, pytest.approx(5.48992, abs=1e-9)]


def test_villa_bands_reproduce_and_two_are_no_increment(res):
    b = res["part_b"]["bands"]
    assert len(b) == 23
    assert sum(1 for r in b if r["verdict"] == T.NA) == 2
    assert all(r["high"] == 0.0 for r in b if r["verdict"] == T.NA)
    assert all(r["high"] > 0 and r["cause"] for r in b if r["verdict"] != T.NA)
    assert res["totals"]["held_bands"]["after"]["high"] == pytest.approx(0.017896, abs=1e-6)


def test_villa_companions_bounded_and_contain_v20(res):
    hosts = {h["mortar_line_id"]: h for h in res["part_b"]["hosts"]}
    gf_oa = hosts["L-8f163174139bcf80c7c7"]
    assert gf_oa["companion_proposed"][1] == pytest.approx(0.000834, abs=1e-6)     # V20 0.000278 + 2 x 0.000278
    for h in hosts.values():
        assert h["envelope"][0] == h["low"] and h["envelope"][1] >= h["high_drawn_t372"]


def test_villa_part_c_020_faces(res):
    assert len(res["part_c"]) == 2
    for r in res["part_c"]:
        assert r["proposed_stamp"] == T.STATUS_ASSUMED
        assert all(w["thickness_m"] == 0.2 for w in r["walls"])
