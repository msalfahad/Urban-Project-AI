"""T-220 on the development villa (research/agents_t220: readings by DXF handle / BOQ id, no coordinates; read this
run from Drive "Alsenan chalet project" / 'ST7757 dxf.dxf', 'ST7757.pdf' p.4-p.6 / p.15 and the architectural 1F / 2F
plans). Regression: the three planted columns and the five released storey lines with no member."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t220"))
import t220_alsenan_check as A  # noqa: E402

AP = pytest.approx


@pytest.fixture(scope="module")
def res():
    return A.run()


def pc(res, i):
    return next(p for p in res["planted"] if p["id"] == i)


def test_pc_1f_a_on_b27(res):
    p = pc(res, "PC-1F-A")
    r, g = p["on_reference_beam_register"], p["on_released_route_g"]
    assert r["section"]["status"] == "AGREE" and r["section"]["area_lo"] == AP(0.14)
    assert r["base"] == AP(5.45) and r["top"] == AP(9.65) and r["solid_m3"] == [AP(0.588), AP(0.588)]
    om = r["owner_method"]
    assert om["status"] == "CALCULATED" and om["D_ctrl"] == 0.75
    assert om["column_m3"][0] == AP(0.483) and om["joint_m3"][0] == AP(0.0826) and om["slab_part_m3"][0] == AP(0.0224)
    assert r["status"] == "DRAWING-CONFIRMED" and r["release"] == "NOT RELEASED"
    assert all(o["result"] == "PASS" for o in r["ownership"])
    short = [o for o in g["ownership"] if o["result"] == "BEAM_LINE_SHORT"]
    assert short and short[0]["beam_short_m3"][0] == AP(0.119)          # released B27 pieces stop at the column
    assert g["base"] == AP(5.45) and g["solid_m3"][0] == AP(0.588)      # the column never starts lower
    assert "10 x 16" in r["bars"]


def test_pc_1f_b_on_b26(res):
    p = pc(res, "PC-1F-B")
    r, g = p["on_reference_beam_register"], p["on_released_route_g"]
    assert r["solid_m3"] == [AP(0.420), AP(0.420)] and r["status"] == "DRAWING-CONFIRMED"
    assert r["owner_method"]["status"] == "HELD" and r["owner_method"]["column_m3_upper"] == AP(0.345)
    assert [o for o in g["ownership"] if o["result"] == "BEAM_LINE_SHORT"][0]["beam_short_m3"][0] == AP(0.085)


def test_pc_2f_on_b19_under_b7(res):
    r = pc(res, "PC-2F")["on_reference_beam_register"]
    assert r["section"]["status"] == "CONFLICT"
    assert (r["section"]["area_lo"], r["section"]["area_hi"]) == (AP(0.08), AP(0.10))
    assert r["base"] == AP(9.65) and r["solid_m3"] is None and r["status"] == "HELD"
    assert r["solid_upper_bound_m3"] == AP(0.35)                        # 0.10 x (13.90 - 0.75 - 9.65)
    assert r["top_owner"].startswith("B7")
    dbl = [o for o in r["ownership"] if o["result"] == "DOUBLE"]
    assert dbl and dbl[0]["double_m3"] == AP(0.059)                     # T-119 COL-2F-59 joint vs B7 billed through
    om = r["owner_method"]
    assert om["status"] == "HELD" and om["column_m3"] == [AP(0.276), AP(0.345)] and om["joint_m3"] == [0.0, 0.0]


def test_carry_against_the_t217_full_storey_convention(res):
    # T-217 / Lead carry 1.344 .. 1.428 m3 at 4.20 m; the drawing-derived solids differ only by the B7 junction
    a = pc(res, "PC-1F-A")["on_reference_beam_register"]["solid_m3"][0]
    b = pc(res, "PC-1F-B")["on_reference_beam_register"]["solid_m3"][0]
    c = pc(res, "PC-2F")["on_reference_beam_register"]["owner_method"]["column_m3"]
    lo, hi = a + b + c[0], a + b + c[1]
    assert (lo, hi) == (AP(1.284), AP(1.353))
    assert (1.344 - lo, 1.428 - hi) == (AP(0.06), AP(0.075))            # A x 0.75 inside B7


def test_released_lines_without_member(res):
    rl = res["released_lines"]
    assert len(rl) == 5 and res["totals"]["released_without_member_m3"] == AP(2.268)
    assert all(r["existence"] == "NOT_DRAWN" and r["state"]["m3"] is None for r in rl)
    assert sorted(r["storey"] for r in rl) == ["1F", "2F", "2F", "2F", "2F"]


def test_input_has_no_coordinates():
    txt = (ROOT / "research" / "agents_t220" / "ALSENAN_PLANTED_INPUT.json").read_text(encoding="utf-8")
    d = json.loads(txt)
    assert "\"x\"" not in txt and "\"y\"" not in txt and d["schema"] == "T220_PLANTED_INPUT_V1"
