"""T-229 on the development villa (research/agents_t229: readings by DXF handle / band id, no coordinates; census read
this run from Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' and the committed route G overlays).
Regression: B27 / B26 continuous through the planted columns, the T.C ends, the beside-support cuts, the oblique
ends, and the joints billed twice under beams that run over a column."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t229"))
import t229_alsenan_check as A  # noqa: E402

AP = pytest.approx


@pytest.fixture(scope="module")
def res():
    return A.run()


def beam(s, name):
    return next(b for b in s["beams"] if b["beam"] == name)


def test_census_complete(res):
    s = res["summary"]
    assert s["counts"]["GF"] == {"pieces": 65, "supports": 30, "carried": 4}
    assert s["counts"]["1F"] == {"pieces": 43, "supports": 20, "carried": 1}
    assert s["counts"]["2F"] == {"pieces": 19, "supports": 9, "carried": 0}
    c = s["census"]
    assert (c["cuts"], c["ends"], c["under"]) == (36, 182, 11)
    assert c["by_class"]["CUT_AT_CARRIED"] == 2 and c["by_class"]["SUPPORT_CUT"] == 22
    assert c["by_class"]["SUPPORT_CUT_BESIDE"] == 10 and c["by_class"]["PROJECTION_CUT"] == 2


def test_b27_continuous_through_pc_1f_a(res):
    s = res["summary"]
    g = next(x for x in s["gaps"] if x["a"] == "GF:BAND0048.1")
    assert g["cls"] == "CUT_AT_CARRIED" and g["status"] == "BEAM_SHORT"
    assert g["members"] == [["329", "CARRIED_COLUMN", AP(0.2693, abs=1e-4)]]
    assert g["short_m3"] == AP(0.4418, abs=1e-4)                 # 0.51982 m2 x 0.85
    assert g["under_carried_m2"] * 0.85 == AP(0.119, abs=1e-3)   # T-220's 0.119 under the column
    b = beam(s, "GF B27 (BAND0048)")
    assert b["released_m3"] == AP(2.5025, abs=1e-4) and b["route_g_held_m3"] == AP(0.8406, abs=1e-4)
    assert b["held_resolved_here"] is True and b["status"] == "DRAWING-CONFIRMED"
    # plus both oblique ends against C11 / the D.C column faces: hand 0.90 x 0.85 x 5.4686 = 4.1835 (+ corner slivers)
    assert b["drawing_derived_m3"] == AP(4.1918, abs=1e-3)
    assert abs(b["drawing_derived_m3"] - 0.90 * 0.85 * 4.40 / 0.80459) < 0.012


def test_b26_and_the_turned_column(res):
    s = res["summary"]
    g = next(x for x in s["gaps"] if x["a"] == "GF:BAND0047.1")
    assert g["cls"] == "CUT_AT_CARRIED" and g["short_m3"] == AP(0.1163, abs=1e-4)
    e = next(x for x in s["ends"] if x["piece"] == "GF:BAND0047.2" and x["end"] == 1)
    assert e["cls"] == "END_SHORT_AT_CARRIED" and e["short_m3"] == AP(0.1812, abs=1e-4)   # T.C at C8 (31B)
    b28 = next(x for x in s["ends"] if x["piece"] == "GF:BAND0035.1" and x["end"] == 0)
    assert b28["cls"] == "END_SHORT_AT_CARRIED" and b28["short_m3"] == AP(0.0612, abs=1e-4)
    b = beam(s, "GF B26 (BAND0047)")
    assert b["drawing_derived_m3"] == AP(4.0846, abs=1e-3)
    # without the T.C end the run equals the T-110 one-span reference 3.9048 within the overlay fit
    assert b["drawing_derived_m3"] - 0.1812 == AP(3.9048, abs=2e-3)


def test_beside_support_and_holds(res):
    s = res["summary"]
    assert s["short"]["beside_support_m3"] == AP(0.476, abs=1e-3)
    b20 = beam(s, "GF B20 (BAND0043)")
    assert b20["short_m3"] == AP(0.09, abs=1e-3) and b20["drawing_derived_m3"] is None   # route G hold at C stays
    held = {(h["a"], h["cls"]) for h in s["held"]["gaps"]}
    assert ("1F:BAND0026.1", "SUPPORT_CUT_BESIDE") in held          # CB10 width conflict (D-02)
    assert ("GF:BAND0031.1", "PROJECTION_CUT") in held and ("1F:BAND0013.1", "PROJECTION_CUT") in held


def test_double_joints(res):
    d = res["summary"]["double"]
    assert d["released_m3"] == AP(0.2778, abs=1e-4)
    lines = {l["outline"]: l for l in d["lines"]}
    assert lines["350"]["released"]["result"] == "DOUBLE" and lines["350"]["column"] == "C3"
    assert lines["347"]["released"]["double_m3"] == AP(0.06, abs=1e-4)
    # PC-2F under B7: the T-119 ledger joint is DOUBLE, the T-220 record (to the B7 soffit) is not
    pc2 = lines["778"]
    assert pc2["ledger_t119"]["result"] == "DOUBLE" and pc2["ledger_t119"]["double_m3"] == AP(0.0599, abs=1e-4)
    assert pc2["record_t220"]["result"] == "PASS" and pc2["released"]["result"] == "PASS"
    # beams that carry a member over its footprint (PC-2F on B19, the turned C9 on B16 / B21): PASS
    assert lines["77B"]["released"]["result"] == "PASS" and lines["322"]["released"]["result"] == "PASS"


def test_totals(res):
    s = res["summary"]["short"]
    assert s["cut_at_carried_m3"] == AP(0.5581, abs=1e-4)
    assert s["end_short_at_carried_m3"] == AP(0.2425, abs=1e-4)
    assert s["end_short_oblique_m3"] == AP(0.512, abs=1e-3)
    assert s["total_confirmed_m3"] == AP(1.8175, abs=1e-3)
