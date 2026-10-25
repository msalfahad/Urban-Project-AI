"""T-170 on the development villa (research/agents_t170: values, Drive titles, DXF handles / coordinates only).
Established this run from 'ST7757 dxf.dxf' (FOUNDATION PLAN outlines) and 'ST7757.pdf' p.9 / p.13 / p.14: 26 footing
elements, 24 with a printed neat pit plan (blinding 0.10 projecting 0.10, p.13), FF (lift, p.14: no projection, no
membrane thickness) and the F10 / F outline (two tags) HELD; the footprint net of the F9 / FN overlap reproduces the
Checker-verified underlay area of 109.85 m2 (T-219); every excavation and backfill volume HELD on the formation."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t170"))
import t170_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.run()


def test_inventory(res):
    from collections import Counter
    c = Counter(p["type"] for p in res["pits"])
    assert res["footings"] == 26 and res["beams"] == 61
    assert c == {"F": 4, "F2": 2, "F3": 2, "F4": 2, "F5": 2, "F6": 1, "F8": 1, "F9": 1, "F11": 1, "F12": 1,
                 "F13": 1, "F14": 1, "F15": 1, "FF": 1, "FN": 4, "F10/F": 1}


def test_neat_plan_and_footprint_cross_check(res):
    assert res["neat_pits_confirmed"] == 24
    assert res["footprint_m2_confirmed_pits"] == pytest.approx(109.99)
    assert res["neat_pit_plan_m2"] == pytest.approx(129.57)
    fo = sum(o["footing_overlap_m2"] for o in res["overlaps"])
    assert fo == pytest.approx(0.14)                                   # F9 / FN, D-32
    assert res["footprint_m2_confirmed_pits"] - fo == pytest.approx(109.85)   # = T-219 VERIFIED underlay area


def test_held_pits_by_name(res):
    h = res["held_pits"]
    ff = next(k for k in h if ":FF@" in k)
    assert set(h[ff]) == {"UNDERLAY_NOT_PRINTED", "BLINDING_PROJECTION_NOT_PRINTED"}
    f10 = next(k for k in h if "T652" in k)
    assert any(x.startswith("FOOTING_CONFLICT") for x in h[f10])
    assert len(h) == 2


def test_every_volume_held_never_zero(res):
    for key in ("excavation_m3", "backfill_m3"):
        assert res[key]["DRAWING-CONFIRMED"] is None and res[key]["lines"] == 0 and res[key]["HELD_lines"] == 87
    for p in res["pits"]:
        assert p["excavation_m3"] is None
        if p["neat_status"] == "DRAWING-CONFIRMED":
            assert "FORMATION_ONLY_A_BOUND" in p["excavation_why"] and "WORKING_SPACE" in p["excavation_why"]


def test_chain_per_type(res):
    ch = res["per_type_chain"]
    for t, H in (("F", 0.30), ("F2", 0.35), ("F4", 0.40), ("F6", 0.50), ("F9", 0.55), ("F12", 0.70)):
        assert ch[t] == {"blinding_top": 0.10, "footing_bottom": 0.17, "footing_top": pytest.approx(0.17 + H)}
    assert ch["FF"]["footing_bottom"] is None


def test_real_and_near_overlaps(res):
    real = [o for o in res["overlaps"] if o["neat_overlap_m2"] > 0]
    assert sorted(round(o["neat_overlap_m2"], 6) for o in real) == [0.005625, 0.33]
    near = [o for o in res["overlaps"] if 0 < o["w_star_m"] <= 0.30]
    assert len(near) == 6


def test_trenches(res):
    assert res["trenches_confirmed"] == 58 and res["trench_neat_plan_m2"] == pytest.approx(97.1445)
    straps = [t for t in res["trenches"] if t["kind"] == "STRAP"]
    assert len(straps) == 3 and all(t["neat_status"] == "HELD" for t in straps)
