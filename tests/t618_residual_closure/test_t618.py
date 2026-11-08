"""T-618 / R-T618-1: small finishes residuals closed to a cause or kept UNRESOLVED (research rule, unwired).

Villa K618 (synthetic, not Alsenan), hand calculations (m):
  room R1 4.00 x 3.00 (orthogonal, k = 4): P 14.00, A 12.00. Offset t = 0.10 outward: P 14.80, A 13.44
           (dP 0.80 = 8 t, dA 1.44 = 14 x 0.10 + 4 x 0.01): a uniform-offset reading, CANDIDATE.
           A reference 14.50 / 11.40 (dP +0.50, dA -0.60): opposite signs, every offset REFUTED; one notch d 0.25 x
           w 2.40 is the only one-shape reading.
  steps    reference pieces 1.20, 1.00, 0.80 (no ids); census wall gaps 1.10, 1.00, 0.80; door blocks 1.20, 1.00, 0.80:
           the block reading reproduces every piece (CANDIDATE); a reading 1.00 x 3 has his total 3.00 but not his
           pieces (refused).
  stair    reference lm 5.00 vs our level 1.00 with a flight HELD 1.50 .. 2.20: range [1.80, 2.50]; with a flight HELD
           1.50 .. unbounded: (-inf, 2.50]; 2.50 reported as a point residual is refused.
  landing  1.20 x 1.50, walled S 1.20 only: walled 1.20, open 4.20; a reference 2.40 is 1.20 above the walled bound.
The K618 outline is written as a T-606 handle chain and read back at 0 / 37 / 211 deg, mirrored, in mm and m.
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T618 = ROOT / "research" / "agents_t618"
sys.path.insert(0, str(T618))
import t618_rules as R  # noqa: E402

pytest.importorskip("shapely")
pytest.importorskip("ezdxf")
import t618_extract as X  # noqa: E402

_spec = importlib.util.spec_from_file_location("t618_alsenan", T618 / "t618_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)


# ---- (a) ranges ---------------------------------------------------------------------------------------------------------
def test_range_residual_bounded_by_hand():
    assert R.range_residual("5.00", "1.00", [("1.50", "2.20")]) == (D("1.80"), D("2.50"))


def test_range_residual_unbounded_low_end():
    assert R.range_residual("5.00", "1.00", [("1.50", None)]) == (None, D("2.50"))


def test_adverse_point_residual_from_lower_bound_refused():
    lo, hi = R.range_residual("5.00", "1.00", [("1.50", "2.20")])
    with pytest.raises(R.RuleError, match="upper end"):
        R.refuse_point_residual("2.50", lo, hi)


def test_point_residual_allowed_when_range_is_a_point():
    lo, hi = R.range_residual("5.00", "1.00", [("1.50", "1.50")])
    assert R.refuse_point_residual("2.50", lo, hi) is False


def test_add_ranges_end_by_end_unbounded_stays():
    assert R.add_ranges([(D("1.80"), D("2.50")), (None, D("-1.00"))]) == (None, D("1.50"))
    assert R.add_ranges([(D("1.80"), D("2.50")), (D("-2"), D("-1.00"))]) == (D("-0.20"), D("1.50"))


def test_adverse_held_is_never_zero():
    with pytest.raises(R.RuleError):
        R.range_residual("5.00", None, [("1.50", "2.20")])


# ---- (b) piece multiset -------------------------------------------------------------------------------------------------
HIS = ["1.20", "1.00", "0.80"]


def test_block_reading_reproduces_every_piece():
    assert R.reading_test(HIS, ["0.80", "1.20", "1.00"]) == "CANDIDATE"


def test_wall_gap_reading_refuted():
    assert R.reading_test(HIS, ["1.10", "1.00", "0.80"]) == "REFUTED"


def test_adverse_sum_only_match_refused():
    assert R.reading_test(HIS, ["1.00", "1.00", "1.00"]) == "REFUTED"
    with pytest.raises(R.RuleError, match="figure matching"):
        R.sum_only_match_refused(HIS, ["1.00", "1.00", "1.00"])


def test_adverse_count_differs_refuted():
    assert R.reading_test(HIS, ["1.20", "1.00", "0.80", "0.00"]) == "REFUTED"


def test_multiset_compare_by_hand():
    m = R.multiset_compare(HIS, ["1.10", "1.00", "0.80"])
    assert m["his_only"] == [D("1.20")] and m["ours_only"] == [D("1.10")] and m["pieces_differing"] == 1


# ---- (c) uniform offset -------------------------------------------------------------------------------------------------
def test_offset_candidate_by_hand():
    r = R.offset_test("14.00", "0.80", "1.44", 4)
    assert r["status"] == "CANDIDATE" and r["t_from_dP"] == D("0.1") and r["dA_from_dP"] == D("1.44")


def test_adverse_offset_opposite_signs_refuted():
    assert R.offset_test("14.00", "0.50", "-0.60", 4)["status"] == "REFUTED"


def test_adverse_offset_same_sign_wrong_ratio_refuted():
    r = R.offset_test("12.90", "0.70", "0.325", 4)        # corridor-like pair
    assert r["status"] == "REFUTED" and r["dP_from_dA"] < D("0.70")


def test_adverse_offset_k_not_positive():
    with pytest.raises(R.RuleError):
        R.offset_test("14", "0.5", "0.5", 0)


def test_notch_and_pocket_by_hand():
    n = R.notch_reading("0.50", "-0.60")
    assert n["kind"] == "NOTCH" and n["depth"] == D("0.25") and n["width"] == D("2.4")
    p = R.notch_reading("0.70", "0.35")
    assert p["kind"] == "POCKET" and p["width"] == D("1")
    assert R.notch_reading("-0.70", "0.35") is None


def _chain(rot_deg=0.0, mirror=False, scale=1000.0, w=4.0, h=3.0):
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))

    def tf(x, y):
        x = -x if mirror else x
        return (scale * (c * x - s * y) + 12345.0, scale * (s * x + c * y) - 6789.0)
    P = [(0, 0), (w, 0), (w, h), (0, h)]
    geom = {}
    chain = []
    for i in range(4):
        a, b = P[i], P[(i + 1) % 4]
        geom[f"K{i}"] = ("LINE", (tf(*a), tf(*b)))
        chain.append((f"K{i}", "WALL"))
    return geom, chain


@pytest.mark.parametrize("rot,mirror,scale", [(0, False, 1000.0), (37, False, 1000.0), (211, True, 1000.0),
                                              (90, True, 1.0)])
def test_k618_outline_offset_coefficient_rotation_mirror_units(rot, mirror, scale):
    geom, chain = _chain(rot, mirror, scale)
    if scale == 1.0:      # metres: the probe is in drawing units, so scale the drawing up to mm first
        geom, chain = _chain(rot, mirror, 1000.0)
    k, P, Aa = X.offset_coefficient(geom, chain)
    assert abs(k - 4.0) < 1e-6 and abs(P - 14.0) < 1e-6 and abs(Aa - 12.0) < 1e-6
    pts, arcs, ortho = X._chain_points(geom, chain)
    assert arcs == 0 and len(pts) == 4
    assert ortho == (rot % 90 == 0)


# ---- (d) landing walled sides -------------------------------------------------------------------------------------------
SIDES = {"S": {"length": "1.20", "walled": "1.20"}, "N": {"length": "1.20", "walled": "0"},
         "E": {"length": "1.50", "walled": "0"}, "W": {"length": "1.50", "walled": "0"}}


def test_landing_bound_by_hand():
    assert R.landing_bound(SIDES) == (D("1.20"), D("4.20"))
    assert R.excess_on_open_faces("2.40", "1.20") == D("1.20")
    assert R.excess_on_open_faces("1.00", "1.20") == D("0")


def test_adverse_walled_longer_than_side():
    with pytest.raises(R.RuleError):
        R.landing_bound({"S": {"length": "1.20", "walled": "1.40"}})


def test_walled_reader_mm_band_and_far_line():
    segs = [("1", "w", 0.0, 0.0, 1200.0, 0.0),            # wall on the south side
            ("1", "far", 0.0, -200.0, 1200.0, -200.0),    # the wall's other face 0.20 away: not on the side
            ("S-COL.BON", "c", 1150.0, 0.0, 1200.0, 0.0)]  # column face overlapping the wall end
    w, hs = X.walled(segs, "S", 0.0, 0.0, 1200.0)
    assert w == 1.2 and hs == ["c", "w"]
    w2, _ = X.walled(segs, "N", 1500.0, 0.0, 1200.0)
    assert w2 == 0.0


# ---- (e) notation, verdicts ---------------------------------------------------------------------------------------------
def test_per_step_row_is_flight():
    assert R.per_step_row_is_flight(5, "5") and not R.per_step_row_is_flight(10, 5)


def test_adverse_verdicts():
    assert R.check_verdict("UNRESOLVED") == "UNRESOLVED"
    with pytest.raises(R.RuleError):
        R.check_verdict("VERIFIED")
    with pytest.raises(R.RuleError):
        R.check_verdict("PROBABLY")


# ---- development villa (pinned) -----------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_alsenan_rebuild_byte_identical(built):
    txt = json.dumps(built, indent=1, ensure_ascii=False) + "\n"
    assert (T618 / "out" / "T618_RESIDUALS.json").read_text(encoding="utf-8") == txt


def test_alsenan_five_rows_and_verdicts(built):
    rows = {r["row"]: r for r in built["rows"]}
    assert list(rows) == ["1F curved", "2F corridor", "door steps", "rails", "stair skirting"]
    assert all(r["verdict"] == "UNRESOLVED" for r in rows.values())
    assert built["engine_wrong"] == []
    st = {t["reading"][:24]: t["status"] for t in rows["1F curved"]["readings_tested"]}
    assert st["uniform face offset (cen"] == "REFUTED"
    assert rows["2F corridor"]["readings_tested"][0]["status"] == "REFUTED"
    assert rows["door steps"]["candidate_parts"] == {"D-GF-09": "0.100000", "D-GF-15": "0.300000"}
    assert rows["rails"]["range_his_minus_ours"] == [None, "0.226000"]
    assert rows["stair skirting"]["range_his_minus_ours"] == [None, "0.710951"]
    net = rows["stair skirting"]["net_of"]
    assert sum(D(v) for v in net.values()) == D("0.710951")


def test_alsenan_point_residuals_refused(built):
    rows = {r["row"]: r for r in built["rows"]}
    assert rows["rails"]["point_0.226_refused_as_quantity"] is True
    assert rows["stair skirting"]["point_0.710951_refused_as_quantity"] is True


def test_alsenan_rs_landing_walled_equals_engine(built):
    st = {s["stair"]: s for s in {r["row"]: r for r in built["rows"]}["stair skirting"]["per_stair"]}
    rs = st["ST-02 round (inner)"]
    assert rs["drawn_landing"]["walled_total"] == "1.250000" == D(rs["ours_valued_level"]).quantize(D("0.000001")).__str__()
    assert rs["drawn_landing"]["his_landing_area_reproduced"] is False
    assert st["ST-03 entrance (E1)"]["drawn_landing"]["walled_total"] == "3.500000"
    assert all(s["notation"]["per_step_row_is_flight_side"] for s in st.values())


def test_alsenan_no_coordinates_no_workbook_text():
    drawn = (T618 / "T618_DRAWN.json").read_text()
    nums = []

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            nums.append(abs(v))
    walk(json.loads(drawn))
    assert nums and max(nums) < 1000.0               # lengths in m only; drawing coordinates are ~ -10^5 mm
    out = (T618 / "out" / "T618_RESIDUALS.json").read_text(encoding="utf-8")
    assert not re.search(r"[؀-ۿ]", out + drawn)


def test_alsenan_edited_input_stops_the_build(tmp_path, monkeypatch):
    pins = json.loads((T618 / "PINS.json").read_text())
    pins[A.DRAWN] = "0" * 16
    p = tmp_path / "PINS.json"
    p.write_text(json.dumps(pins))
    monkeypatch.setattr(A, "PIN_FILE", p)
    with pytest.raises(R.RuleError, match="inputs changed"):
        A.build()
