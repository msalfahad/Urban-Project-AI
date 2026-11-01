"""T-427 pins on the development villa (room-local dimensions only; no drawing content): the GF band pieces classify
as the drawing reads, the dry residual closes on its named causes, the wet split closes, and the committed outputs
reproduce."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t427"
sys.path.insert(0, str(HERE))
import t427_alsenan as A  # noqa: E402


def test_band_pieces_hand_values():
    z = A.Z.classify(A.band_pieces(), A.DRAWN)
    a = {r["id"]: r for r in z["rows"]}
    assert a["GF-RFD4E1D band west face"]["area_m2"] == pytest.approx(3.8 * 1.3 - 1.1 * 0.05)        # 4.885
    assert a["OP-003 band strip, west 3.80 (x 3.00 .. 6.80)"]["area_m2"] == pytest.approx(3.8 * 0.2)  # 0.760
    assert a["OP-003 band strip, curb 3.02 (x 6.80 .. 9.82)"]["area_m2"] == pytest.approx(3.02 * 0.2)  # 0.604
    assert a["GF-R9A05AA garden band"]["area_m2"] == pytest.approx(7.02 * 1.3 - 0.5 * 0.05)          # 9.101
    assert a["columns 2FD2 + 2FC6 and wall 336 / 337 between them"]["area_m2"] == pytest.approx(
        0.8 * 0.25 + 0.6 * 0.25 + 2.65 * 0.2)                                                         # 0.880
    assert z["moved_to_floor_m2"] == pytest.approx(5.645)
    assert z["held_m2"] == pytest.approx(9.101 + 0.604)
    assert a["GF-R9A05AA garden band"]["status"] == "HELD"


def test_dry_residual_closes():
    s = A.summarize()
    d = s["dry"]
    assert d["diff_m2"] == pytest.approx(-40.7967) and d["components_sum_m2"] == pytest.approx(-40.7967)
    # the T-418 'unexplained 2.5463' is now 1.364 (HELD strip, 0.760 floor + 0.604 curb) + 0.880 solid + 0.3023
    assert 1.364 + 0.88 + d["gf_open_room"]["freelancer_above_outline_m2"] == pytest.approx(2.5463)
    assert d["gf_open_room"]["outline_check_m2"] == pytest.approx(d["gf_open_room"]["comparable_m2"], abs=1e-3)
    assert d["by_class"]["UNEXPLAINED"] == pytest.approx(-0.3023 - 0.325)
    assert d["correction"]["corrected_candidate_dry_m2"] == pytest.approx(296.7733 + 5.645)
    assert all(c["m2"] is not None for c in d["components"])


def test_wet_split_closes():
    w = A.summarize()["wet"]
    assert w["diff_m2"] == pytest.approx(13.5656) and w["components_sum_m2"] == pytest.approx(13.5656)


def test_committed_outputs_reproduce():
    s = A.summarize()
    assert json.loads((HERE / "summary.json").read_text(encoding="utf-8")) == json.loads(json.dumps(s))
    assert (HERE / "RESIDUAL_T427.csv").read_text(encoding="utf-8") == A.table_csv(s)


def test_cross_trade_skirting_finding():
    ct = A.summarize()["cross_trade"]
    sk = [c for c in ct if c["line"].startswith("L-71e2e002")][0]
    assert sk["delta"] == pytest.approx((3.80 - 1.10) + (0.05 + 1.10 + 0.05))   # wall + column faces of the west part
    d48 = [c for c in ct if c["line"] == "designer list D-48"][0]
    assert d48["after"] == pytest.approx(9.705)
