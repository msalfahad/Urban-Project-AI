"""T-221 on the development villa (research/agents_t221: local metres measured on the architectural DWF plan views and
outlets from the sanitary sheets; Drive titles / views only). What the drawings establish: the printed 1 % fall and the
drawn corner outlets fix the falls rise of the +9.70, +5.50 and +4.30 roofs as a range from the undrawn plane layout;
t0, the membrane layers and the reference point of each finished roof level are not printed, so every roof stays HELD
(never 0); the +13.90 roof has no outlet on any sheet; no section cuts a wet room on any floor; D-44 is drawn on no
sheet; the summary reproduces byte for byte."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t221"))
import t221_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.build()


def _roof(res, zid):
    return next(r for r in res["roofs"] if r["zone"] == zid)


@pytest.mark.parametrize("zid,lo,hi,area", [("ROOF-970", 0.1068, 0.1443, 147.691), ("TERRACE-550", 0.1902, 0.2027, 32.387),
                                            ("ROOF-430", 0.1115, 0.1470, 52.848)])
def test_falls_rise_ranges(res, zid, lo, hi, area):
    r = _roof(res, zid)
    assert r["rise_max_m"] == pytest.approx([lo, hi], abs=1e-3)
    assert r["falls"]["area_m2"] == pytest.approx(area, abs=0.01)
    assert r["parapet"]["status"] == "NOT PROVEN"


def test_terrace_far_point_hand_check(res):
    # one outlet at the far corner of a 18.972 x 1.302 leg: 0.01 x sqrt(18.972^2 + 1.302^2) .. 0.01 x (18.972 + 1.302)
    r = _roof(res, "TERRACE-550")
    assert r["rise_max_m"][0] == pytest.approx(0.01 * (18.972 ** 2 + 1.302 ** 2) ** 0.5, abs=5e-4)
    assert r["rise_max_m"][1] == pytest.approx(0.01 * (18.972 + 1.302), abs=5e-4)


def test_main_roof_without_outlets_held(res):
    r = _roof(res, "ROOF-1390")
    assert r["falls"] is None and r["falls_status"].startswith("HELD: DRAINS_NOT_DRAWN")


def test_every_zone_held_never_zero(res):
    for z in res["zones"]:
        assert z["status"] == "HELD" and z["b"] is None and z["structural_top"] is None and z["missing"]


def test_no_section_cuts_a_wet_room(res):
    assert len(res["section_cuts"]) == 6 and not any(c["cuts_wet_room"] for c in res["section_cuts"])


def test_d44_drawn_on_no_sheet(res):
    assert len(res["d44_record"]) >= 8 and not any(r["drawn"] for r in res["d44_record"])


def test_summary_reproduces(res):
    text = json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    assert text == (ROOT / "research" / "agents_t221" / "summary.json").read_text(encoding="utf-8")
