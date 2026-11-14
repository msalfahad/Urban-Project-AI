"""T-785 R-T785-1 (upturn in lm beside m2, his gross-perimeter basis) and R-T785-2 (sunken wet room: recess + 0.30 up).

Normal: a synthetic villa (not Alsenan): a 2.40 x 1.80 bath, door 0.80, one open edge 0.60; run from m2 / 0.20; gross
perimeter = run + door + open edge = box perimeter; a sunken bath on a panel with loop 8.0 m: printed drop used,
default 0.30 kept under a 0.34 bound and capped at a 0.24 bound; the Alsenan set closes both differences with residual 0.
Adverse: mm read as m, NaN / negative / missing, no recess, height 0 refused (HELD, never 0); a mirrored room (same
lengths) gives the same figures. Writes nothing."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t785"))
import t785_rules as R  # noqa: E402
import fill_t785 as F  # noqa: E402


# ------------------------------------------------------------------ normal (synthetic villa)
def test_run_and_gross_perimeter_by_hand():
    box = 2 * (2.40 + 1.80)                       # 8.40
    run = box - 0.80 - 0.60                       # walls only 7.00
    assert R.run_lm(run * 0.20, 0.20) == pytest.approx(7.00)
    assert R.like_for_like_perimeter(7.00, [0.80], [0.60]) == pytest.approx(box)


def test_sunken_room_printed_default_and_cap():
    p = R.sunken_room(7.00, [{"panel": "P1", "loop_m": 8.0, "d_max_m": 0.24, "d_printed_m": 0.15}])
    assert p["recess_m2"] == pytest.approx(1.20) and p["label"] == "DRAWING-READ"
    assert p["upturn_m2"] == pytest.approx(2.10)                       # 7.00 x 0.30
    q = R.sunken_room(7.00, [{"panel": "P1", "loop_m": 8.0, "d_max_m": 0.34, "d_printed_m": None}])
    assert q["recess_m2"] == pytest.approx(2.40) and not q["parts"][0]["capped"]
    c = R.sunken_room(7.00, [{"panel": "P1", "loop_m": 8.0, "d_max_m": 0.24, "d_printed_m": None},
                             {"panel": "P2", "loop_m": 2.0, "d_max_m": None, "d_printed_m": None}])
    assert c["recess_m2"] == pytest.approx(8.0 * 0.24 + 2.0 * 0.30) and c["parts"][0]["capped"]
    assert c["label"] == "DEFAULT"


def test_mirror_same_lengths_same_result():
    a = R.sunken_room(6.5, [{"loop_m": 7.1, "d_max_m": 0.24}])
    b = R.sunken_room(6.5, [{"loop_m": 7.1, "d_max_m": 0.24}])     # mirrored plan: lengths unchanged
    assert a["recess_m2"] == b["recess_m2"] and a["upturn_m2"] == b["upturn_m2"]


def test_split_closes():
    s = R.split(10.0, 9.0, [{"qty": "0.8", "sign": 1}, {"qty": "0.2", "sign": 1}])
    assert s["residual"] == pytest.approx(0.0) and s["closed"]
    t = R.split(10.0, 9.0, [{"qty": "0.5", "sign": 1}])
    assert not t["closed"]                                          # 0.5 / 9.0 = 5.6 % unnamed


# ------------------------------------------------------------------ adverse
@pytest.mark.parametrize("bad", [None, 0, -1.0, float("nan"), True])
def test_missing_values_refused(bad):
    with pytest.raises(R.WetRuleError):
        R.run_lm(bad, 0.20)
    with pytest.raises(R.WetRuleError):
        R.sunken_room(bad, [{"loop_m": 5.0, "d_max_m": 0.24}])
    with pytest.raises(R.WetRuleError):
        R.sunken_room(5.0, [{"loop_m": bad, "d_max_m": 0.24}])


def test_units_and_no_recess_refused():
    with pytest.raises(R.WetRuleError):
        R.recess_depth(d_printed_m=240)                             # mm read as m
    with pytest.raises(R.WetRuleError):
        R.recess_depth(d_max_m=340)
    with pytest.raises(R.WetRuleError):
        R.run_lm(1.0, 200)                                          # height in mm
    with pytest.raises(R.WetRuleError):
        R.sunken_room(5.0, [])
    with pytest.raises(R.WetRuleError):
        R.split(1.0, 0, [])


# ------------------------------------------------------------------ development villa (repository data only)
def test_alsenan_fix_rows_close_and_match_out():
    d = F.build()
    s = d["summary"]
    assert s["floor_m2"]["residual"] == pytest.approx(0.0, abs=1e-6)
    assert s["upturn_lm"]["residual"] == pytest.approx(0.0, abs=1e-6)
    assert s["floor_m2"]["his"] == 72.01 and s["upturn_lm"]["his"] == 144.61
    assert len(d["rooms"]) == 18 and sum(1 for t in d["rooms"] if t["freelancer_row"]) == 17
    assert all(x["net"] > 0 for x in d["new_lines"]) and all(x["after"]["net"] > 0 for x in d["rows"])
    assert sum(1 for x in d["new_lines"] if x["item_code"] == "FIN.WP.WALL_UPTURN_LM") == 18
    assert sum(1 for x in d["new_lines"] if x["item_code"] == "FIN.WP.SUNKEN_RECESS") == 6
    out = json.loads((ROOT / "research/agents_t785/out/FIX_ROWS.json").read_text(encoding="utf-8"))
    assert out == json.loads(json.dumps(d, ensure_ascii=False))
    for x in d["rows"]:                                             # sunken upturn = run x 0.30, run from the 0.20 line
        assert x["after"]["net"] == pytest.approx(x["before"]["net"] / 0.20 * 0.30, abs=1e-6)
    assert not math.isnan(s["sunken_rooms"]["recess_m2"])
