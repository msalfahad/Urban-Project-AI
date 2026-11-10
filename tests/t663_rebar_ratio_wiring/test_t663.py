"""T-663: the four Checker wiring conditions on the R-T662-1 ratio (R-T663-1 .. 4). Synthetic villa "V663" (not the
training villa) by hand, normal and adverse: a calibrated member ratioed with a cited range; a PARTIAL member ratioed
(refused); a borrowed ratio (refused: the type stays HELD); a range with no cited page (refused); laps inside the
calibration kg (refused); a shared band and two disagreeing measures (not bound). Then the development villa from
repository files only: outputs current, totals unchanged from T-662, nothing wired."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t663"))
sys.path.insert(0, str(ROOT / "research" / "agents_t662"))
import t663_rules as R  # noqa: E402
import t662_rules as R2  # noqa: E402

D = Decimal


def rel(v, lid="x", unit="kg"):
    return {"line_id": lid, "class": "RELEASED", "measured_net": v, "held_low": None, "held_high": None, "unit": unit}


def bnd(lo, hi, lid="x", unit="kg"):
    return {"line_id": lid, "class": "HELD", "measured_net": None, "held_low": lo, "held_high": hi, "unit": unit}


def blank(lid="x", unit="kg"):
    return {"line_id": lid, "class": "HELD", "measured_net": None, "held_low": None, "held_high": None, "unit": unit}


# ---- villa "V663" (hand) ------------------------------------------------------------------------------------------------
# Ground beams GB1 .. GB3, simple spans (splice NOT_REQUIRED), 0.30 x 0.50 m:
#   GB1 4.00 m clear, concrete 0.30 x 0.50 x 4.00 = 0.600 m3 released; bars: bottom 3 d16 x 4.00 = 12.00 m x 1.580247
#       = 18.962963 kg, top 2 d12 x 4.00 = 8.00 m x 0.888889 = 7.111111 kg, ends 40d..70d: 3 x 2 x 0.64 .. 1.12 m d16
#       = 6.068148 .. 10.619259 kg (anchorage, installed), links 27 x 1.50 m d8 x 0.395062 = 16.000000 kg
#       -> 48.142222 .. 52.693333 kg
#   GB2 2.50 m, 0.375 m3; bottom 3 d16 x 2.5 = 11.851852, top 2 d12 x 2.5 = 4.444444, links 17 x 1.5 x 0.395062 =
#       10.074074 -> 26.370370 kg (released)
#   GB3 3.00 m, 0.450 m3, every bar group blank -> ratio member
# calibration GROUND_BEAM: (48.142222 + 26.370370) .. (52.693333 + 26.370370) / 0.975
#   = 74.512593 .. 79.063704 kg / 0.975 m3 = 76.423172 .. 81.090978 kg/m3;
#   GB3: 0.45 x 76.423172 x 1.03 = 35.422140 .. 0.45 x 81.090978 x 1.05 = 38.315487 kg
KGM = {8: D(64) / 162, 12: D(144) / 162, 16: D(256) / 162}


def v663():
    gb1 = [("BOTTOM", 12 * KGM[16], 12 * KGM[16]), ("TOP", 8 * KGM[12], 8 * KGM[12]),
           ("BOTTOM_ENDS_NOTE_9_40D_70D", D("3.84") * KGM[16], D("6.72") * KGM[16]), ("LINKS", D("40.5") * KGM[8],
                                                                                     D("40.5") * KGM[8])]
    gb2 = [("BOTTOM", D("7.5") * KGM[16], D("7.5") * KGM[16]), ("TOP", 5 * KGM[12], 5 * KGM[12]),
           ("LINKS", D("25.5") * KGM[8], D("25.5") * KGM[8])]
    return gb1, gb2


def kg(groups):
    return sum((D(lo) for _, lo, _ in groups), D(0)), sum((D(hi) for _, _, hi in groups), D(0))


def test_v663_hand_calibration_and_ratio():
    gb1, gb2 = v663()
    assert R.lap_audit(gb1, "NOT_REQUIRED")["passes"] and R.lap_audit(gb2, "NOT_REQUIRED")["passes"]
    a = R.lap_audit(gb1, "NOT_REQUIRED")
    assert a["lap_kg"] == ["0.000000", "0.000000"] and a["anchorage_kg"] == ["6.068148", "10.619259"]
    (l1, h1), (l2, h2) = kg(gb1), kg(gb2)
    assert R.S(l1) == "48.142222" and R.S(h1) == "52.693333" and R.S(l2) == "26.370370"
    cal = R2.calibrate([{"member": "GB1", "kg_low": l1, "kg_high": h1, "m3": D("0.600")},
                        {"member": "GB2", "kg_low": l2, "kg_high": h2, "m3": D("0.375")}])
    assert cal["ratio_low"] == "76.423172" and cal["ratio_high"] == "81.090978"
    r = R2.assign("NONE", cal, ("RELEASED", D("0.45"), D("0.45")))
    assert r["route"] == "RATIO" and r["kg_low"] == "35.422140" and r["kg_high"] == "38.315487"
    # normal: a cited range containing the ratio -> INSIDE, and the gate opens only with n >= 3 and laps proven absent
    ref = {"type": "GROUND_BEAM", "book": "Book X", "folder": "F", "page": "112", "low": 60, "high": 120}
    rc = R.range_check("GROUND_BEAM", cal["ratio_low"], cal["ratio_high"], [ref])
    assert rc["status"] == "INSIDE" and rc["references"][0]["page"] == "112"
    assert R.gate("INSIDE", 3, True) == {"wiring_ready": True, "blockers": []}
    g = R.gate(rc["status"], cal["n"], True)
    assert not g["wiring_ready"] and g["blockers"] == ["(2) calibration n = 2 < 3 (WEAK)"]


def test_range_outside_is_flagged_not_adjusted():
    ref = {"type": "BEAM", "book": "Book X", "folder": "F", "page": "9", "low": 80, "high": 150}
    rc = R.range_check("BEAM", "147.788330", "175.869052", [ref])
    assert rc["status"] == "OUTSIDE_FLAGGED" and rc["ratio"] == ["147.788330", "175.869052"]


def test_range_without_cited_page_refused():
    for bad in ({"type": "BEAM", "book": "Book X", "folder": "F", "page": "", "low": 80, "high": 150},
                {"type": "BEAM", "book": "", "folder": "F", "page": "3", "low": 80, "high": 150},
                {"type": "BEAM", "book": "B", "folder": "F", "page": "3", "low": 150, "high": 80},
                {"type": "BEAM", "book": "B", "folder": "F", "page": "3", "low": None, "high": 80}):
        with pytest.raises(R.RuleError, match="RANGE_REFUSED"):
            R.range_check("BEAM", 100, 120, [bad])
    rc = R.range_check("BEAM", 100, 120, [], ["book A"])
    assert rc["status"] == "NOT_CHECKED_NO_CITED_SOURCE" and rc["sources_searched"] == ["book A"]
    assert not R.gate(rc["status"], 44, True)["wiring_ready"]


def test_laps_inside_calibration_refused():
    gb1, _ = v663()
    with_lap = gb1 + [("PROCUREMENT_WEIGHT_INCL_LAPS_LAPS_ONLY", D("9.102"), D("15.929"))]
    a = R.lap_audit(with_lap, "NOT_REQUIRED")
    assert not a["passes"] and a["lap_kg"] == ["9.102000", "15.929000"]
    with pytest.raises(R.RuleError, match="LAPS_IN_CALIBRATION"):
        R.require_lap_free(a, "GB1")
    # a bar-end group on a population that draws or needs a splice: lap and anchorage cannot be told apart
    for need in ("DRAWN_OVERLAP", "REQUIRED", "NOT_ESTABLISHED"):
        assert not R.lap_audit(gb1, need)["passes"]
    with pytest.raises(R.RuleError, match="no splice-need record"):
        R.lap_audit(gb1, None)
    assert not R.gate("INSIDE", 5, False)["wiring_ready"]


def test_partial_member_ratio_refused_and_stays_partial():
    assert R.partial_resolution(["TOP_END_LEGS"], {}) == ("PARTIAL", ["TOP_END_LEGS"])
    assert R.partial_resolution(["TOP_END_LEGS"], {"TOP_END_LEGS": "0.40 m printed"}) == ("COUNTABLE", [])
    for route in ("PARTIAL_HELD", "DETAILED", "RATIO_HELD"):
        with pytest.raises(R.RuleError, match="RATIO_REFUSED"):
            R.wiring_route_guard(route, "F12")
    assert R2.assign("PARTIAL", {"ratio_low": "70", "ratio_high": "71"}, ("RELEASED", D(1), D(1)))["route"] == \
        "PARTIAL_HELD"


def test_borrowed_ratio_refused():
    # a NECK with concrete but no counted neck: never the beam or footing ratio
    r = R2.assign("NONE", None, ("RELEASED", D("0.5"), D("0.5")))
    assert r["route"] == "RATIO_HELD" and "no borrowed ratio" in r["cause"]
    ref = {"type": "BEAM", "book": "Book X", "folder": "F", "page": "9", "low": 80, "high": 200}
    assert R.range_check("NECK", 100, 120, [ref])["status"] == "NOT_CHECKED_NO_CITED_SOURCE"


def test_binding_rules():
    line = {"line_id": "L1", "class": "RELEASED", "measured_net": 0.516}
    conc = {"P-C:GB:BAND1": [line], "P-C:GB:BAND2": [{"line_id": "L2", "class": "HELD", "measured_net": None,
                                                      "held_low": 0.20, "held_high": 0.28}],
            "P-C:GB:BAND3": [{"line_id": "L3", "class": "HELD", "measured_net": None, "held_low": None,
                              "held_high": None}]}
    own = {"GB:BAND1": {"S1"}, "GB:BAND2": {"S2"}, "GB:BAND3": {"S3"}, "GB:BAND4": {"S4", "S5"}}
    assert R.bind("S1", [{"component": "GB:BAND1", "m3": "0.516"}], conc, own)["bound"]
    assert R.bind("S2", [{"component": "GB:BAND2", "m3": "0.25"}], conc, own)["bound"]
    # adverse: two measures disagree (mirror of a wrong span picked), shared band, blank line, no register, absent id
    assert "(d) two measures" in R.bind("S1", [{"component": "GB:BAND1", "m3": "2.565"}], conc, own)["reason"]
    assert "(d) two measures" in R.bind("S2", [{"component": "GB:BAND2", "m3": "0.296"}], conc, own)["reason"]
    conc["P-C:GB:BAND4"] = [line]
    assert "(c)" in R.bind("S4", [{"component": "GB:BAND4", "m3": "0.516"}], conc, own)["reason"]
    assert "(d) concrete line HELD blank" in R.bind("S3", [{"component": "GB:BAND3", "m3": "0.4"}], conc, own)["reason"]
    assert "(a)" in R.bind("S9", [], conc, own)["reason"]
    assert "(b)" in R.bind("S9", [{"component": "GB:BAND9", "m3": "1"}], conc, {})["reason"]
    # units: 516 (litres read as m3) never binds
    assert not R.bind("S1", [{"component": "GB:BAND1", "m3": "516"}], conc, own)["bound"]


# ---- development villa (repository files only) ------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    import t663_alsenan as A
    return A, A.build()


def test_villa_nothing_wired_totals_unchanged(built):
    A, o = built
    t = o["gate_b_ratio_table"]
    assert t["rows_n"] == 28 and t["total_kg"] == ["2204.240949", "2909.015321"]
    assert t["released_detailed_kg_unchanged"] == "9628.462205"
    assert all(r["label"] == R.LABEL and r["bar_lines_replaced"] for r in t["rows"])
    # no cited range exists today: no row is wiring-ready, and every row names condition (1)
    assert t["wiring_ready_n"] == 0 and all(r["blockers"][0].startswith("(1)") for r in t["rows"])
    assert all(any(b.startswith("(2)") for b in r["blockers"]) for r in t["rows"] if r["type"] == "FOOTING")


def test_villa_laps_and_partials(built):
    _, o = built
    c3 = o["condition_3_laps"]["by_type"]
    assert all(v["laps_ok"] and v["lap_kg"] == ["0.000000", "0.000000"] for v in c3.values())
    assert c3["BEAM"]["members"] == 44 and c3["BEAM"]["anchorage_kg_kept"] == ["381.928000", "668.367000"]
    assert o["condition_3_laps"]["ground_slab_proof"]["bare_mesh_kg_per_m3_at_0_10_m"] == "61.728395"
    f = o["condition_2_footing_partial"]
    assert sorted(m["mark"] for m in f["members"]) == ["F12", "F13", "F14", "FF"]
    assert all(m["state_after"] == "PARTIAL" and m["held_by_name"] == ["TOP_END_LEGS"] for m in f["members"])
    assert f["footing_calibration_n"] == 1


def test_villa_binding(built):
    _, o = built
    b = o["condition_4_binding"]
    assert sum(b["summary"].values()) == 175
    for m in b["members"]:
        assert m.get("ratio_after_binding") != "RATIO"           # no uncalibrated type gets a borrowed ratio
        if m.get("bound") and m["type"] == "GROUND_BEAM":
            assert m["reason"].startswith("(a)-(d) pass")


def test_outputs_current(built):
    A, o = built
    assert json.loads(A.OUT_JSON.read_text(encoding="utf-8")) == json.loads(json.dumps(o, ensure_ascii=False))
    assert A.OUT_MD.read_text(encoding="utf-8") == A.md(o)


@pytest.mark.skipif(os.environ.get("URBAN_T663_WRITE") != "1", reason="writer: URBAN_T663_WRITE=1 only")
def test_write_outputs():
    import t663_alsenan as A
    A.write()
