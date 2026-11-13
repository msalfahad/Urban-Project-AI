"""T-696 (a) census of the blank B9 lines and (b) the R-T696-1 restatement, from the merged ledgers only.

Hand fixture 'Villa M' (not the development villa) for the one-ended figure:
  - a top-storey 0.15 m black wall under a roof whose build-up b_r is not printed: U = 3.20 x (3.85 - b_r) = 12.32 -
    3.20 b_r m2 with a REQUIRED 1.50 m lintel face 1.50 x 0.20 = 0.30 m2: AT_MOST base 12.02 m2 -> 150.25 pcs, mortar
    12.02 x 0.0110625 = 0.13297125 -> printed 0.132972 (UP);
  - a below-ground 0.20 m black run printed h >= 0.80 m over 5.125 m: AT_LEAST 4.10 m2 -> 51.25 pcs; mortar at the
    0.15 leaf 4.10 x 0.0110625 = 0.04535625 -> printed 0.045356 (DOWN);
  - a white 0.20 m wall AT_MOST 10.0 m2 -> glue 45.0 kg; white units / perimeter: None (no area rule, HELD).
"""
import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t696"))


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


C = _mod("t696_b9_census", "research/agents_t696/t696_b9_census.py")
B = _mod("t696_b9_bounds", "research/agents_t696/t696_b9_bounds.py")


# ------------------------------------------------------------------------------------------------ Villa M
def test_at_most_rounds_up_after_required_face():
    u = C.material_one_end("AT_MOST", "12.32", "0.30", "MAS.UNITS.BLACK", "0.15")
    m = C.material_one_end("AT_MOST", "12.32", "0.30", "MAS.MORTAR.BLACK", "0.15")
    assert (u["base_m2"], u["printed"]) == ("12.02", 150.25)
    assert m["exact"] == "0.132971250" and m["printed"] == 0.132972


def test_at_least_rounds_down():
    m = C.material_one_end("AT_LEAST", "4.10", 0, "MAS.MORTAR.BLACK", "0.15")
    assert m["printed"] == 0.045356
    assert C.material_one_end("AT_LEAST", "4.10", 0, "MAS.UNITS.BLACK", "0.20")["printed"] == 51.25


def test_glue_and_no_rule_codes():
    assert C.material_one_end("AT_MOST", "10.0", 0, "MAS.GLUE.AAC", "0.20", Decimal("4.5"))["printed"] == 45.0
    assert C.material_one_end("AT_MOST", "10.0", 0, "MAS.UNITS.WHITE", "0.20") is None
    assert C.material_one_end("AT_MOST", "10.0", 0, "MAS.MORTAR.BLACK.PERIMETER", "0.20") is None


def test_adverse_missing_never_zero():
    with pytest.raises(ValueError):
        C.material_one_end("AT_MOST", None, 0, "MAS.UNITS.BLACK", "0.15")
    with pytest.raises(ValueError):
        C.material_one_end("RANGE", "1", 0, "MAS.UNITS.BLACK", "0.15")
    with pytest.raises(ValueError):
        C.material_one_end("AT_MOST", "0.20", "0.30", "MAS.UNITS.BLACK", "0.15")      # faces exceed the area
    with pytest.raises(ValueError):
        C.material_one_end("AT_MOST", "10.0", 0, "MAS.GLUE.AAC", "0.25")              # no borrowed glue rate


def test_mirror_wall_order_same_host_bound():
    a = C.material_one_end("AT_MOST", C.BR.add("6.93", "15.015"), 0, "MAS.UNITS.BLACK", "0.20")
    b = C.material_one_end("AT_MOST", C.BR.add("15.015", "6.93"), 0, "MAS.UNITS.BLACK", "0.20")
    assert a == b and a["printed"] == 274.3125


# ------------------------------------------------------------------------------------------------ development villa
def test_census_counts_match_the_candidate():
    d = C.build()
    assert d["blank_counts"] == {"MAS.GLUE.AAC": 10, "MAS.MORTAR.BLACK": 12, "MAS.MORTAR.BLACK.PERIMETER": 12,
                                 "MAS.UNITS.BLACK": 12, "MAS.UNITS.WHITE": 15}
    beside = {r["line_id"][:10]: r["beside"].get("printed") for r in d["rows"] if r["beside"]["kind"] != "NONE"}
    assert beside == {"L-c76dd0d1": 118.375, "L-a9876502": 48.125, "L-8075d1bd": 274.3125,
                      "L-b765c24a": 0.104762, "L-3cdc29f2": 0.056788, "L-539af3a6": 0.323689,
                      "L-bd48d897": 90.6325, "L-4ccc5dc2": 73.0125, "L-320814d3": 98.04375,
                      "L-bd21b0ea": 142.3625, "L-cf220ce7": 0.12599}
    # every parent has at least one held wall with no drawn end: no host bound, no material bound
    assert all(r["host_area_m2"]["walls_with_no_drawn_end"] for r in d["rows"] if r["cause_class"] == "OPEN BOUND"
               and "walls" in r)


def test_restatement_every_exact_end_inside():
    d = B.build()
    assert d["bounded_lines"] == 15 and d["moved"] == 10
    for r in d["rows"]:
        assert r["exact_inside_restated"]
        lo, hi = r["r_t696_1"]
        assert abs(lo - r["v3_0_68"][0]) <= 2e-6 + 1e-12 and abs(hi - r["v3_0_68"][1]) <= 4e-6 + 1e-12
    by = {r["line_id"][:10]: r for r in d["rows"]}
    assert by["L-686a15f1"]["r_t696_1"] == [0.0, 0.001112]          # D-1F-09: 0.0011115 never prints 0.001111
    assert by["L-5b828080"]["r_t696_1"] == [0.000555, 0.000888]     # D-1F-03
    assert by["L-866a6602"]["r_t696_1"] == [0.618315, 0.622077]
    assert by["L-c5969291"]["r_t696_1"] == [0.028342, 0.049797]


def test_tampered_ledger_refused(tmp_path, monkeypatch):
    bad = tmp_path / "idx.json"
    bad.write_text(B.IDX.read_text(encoding="utf-8").replace("0.618315", "0.618316"), encoding="utf-8")
    monkeypatch.setattr(B, "IDX", bad)
    monkeypatch.setattr(B, "PINS", {bad: "fc485958"})
    with pytest.raises(SystemExit):
        B.build()
