"""T-482: the three blockwork wiring conditions on the training villa, from merged public research files only
(no private drawing is read; the run's own drawing readings are constants in t482_alsenan.py with their handles).

Normal: GF 4.50 / 1F 4.20 are structural (plate top - plate top); every 2F wall under the roof-only plate carries
U - L x b_r with U - 0.05 x L equal to the carried figure (the carried 4.20 is the b_r = 0.05 what-if, exactly);
GF-W22 is the D-27 range; NW-2 moves -0.4435 m2 to its straight roof-level centreline.
Adverse: the 4.20 chain under the roof is refused; the carried GF-W22 single end as DRAWING-CONFIRMED is refused;
the arc run is refused; the held 2F-W00 stays held (never 0); the committed output is the build.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t482"


@pytest.fixture(scope="module")
def reg():
    spec = importlib.util.spec_from_file_location("t482_alsenan_test", HERE / "t482_alsenan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.build()


def test_committed_output_is_the_build(reg):
    committed = json.loads((HERE / "out/T482_CONDITIONS.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(reg)) == committed


def test_storey_basis(reg):
    b = {x["floor"]: x for x in reg["storey_basis"]}
    assert b["GF"]["structural_storey_m"] == pytest.approx(4.50) and b["GF"]["verdict"].startswith("STRUCTURAL")
    assert b["1F"]["structural_storey_m"] == pytest.approx(4.20) and b["1F"]["verdict"].startswith("STRUCTURAL")
    assert b["2F"]["structural_storey_m"] is None and b["2F"]["verdict"] == "FINISHED_AS_STRUCTURAL"
    assert b["2F"]["upper_storey_m"] == pytest.approx(4.25)
    assert reg["datums"]["SFRS"]["state"] == "ROOF_DATUM" and reg["datums"]["ANNEX-ROOF"]["state"] == "ROOF_DATUM"
    assert reg["datums"]["SFRS"]["beside"]                     # the P1 note is named, not applied


def test_2f_walls_roof_datum(reg):
    walls = {w["wall_id"]: w for w in reg["roof_walls_2F"]}
    assert len(walls) == 9
    assert walls["2F-W00"]["t482_state"] == "HELD" and walls["2F-W00"]["upper_m2_at_b0"] is None
    for w in walls.values():
        if w["t482_state"] != "ROOF_DATUM":
            continue
        assert w["check_U_minus_L_x_0.05"] == pytest.approx(w["carried_m2"], abs=0.0006)
        assert w["what_if_b_0.05_m2"] == pytest.approx(w["v1_value_at_4.20"], abs=1e-9)
        assert w["upper_m2_at_b0"] > w["carried_m2"]
    s = reg["roof_walls_summary"]
    assert s["roof_datum"] == 8 and s["held_whole"] == 1
    assert s["valued_upper_m2"] == pytest.approx(53.5225) and s["valued_L_m"] == pytest.approx(14.925)
    assert s["part_upper_m2"] == pytest.approx(46.33) and s["part_L_m"] == pytest.approx(14.57)
    assert s["valued_carried_m2"] == pytest.approx(52.776) and s["part_carried_m2"] == pytest.approx(45.6015)
    assert math.isclose(s["valued_upper_m2"] - 0.05 * s["valued_L_m"], 52.77625, abs_tol=1e-6)


def test_gf_w22_conflict(reg):
    w = {x["element_id"]: x for x in reg["width_conflicts"]}
    a = w["GF-W22"]
    assert a["range_m2"] == [pytest.approx(12.9311), pytest.approx(12.9439)]
    assert a["carried_refused"].startswith("CONFLICT_ONE_END")
    assert a["low_reading"].startswith("CB2 drawn 0.25")
    assert w["GF-W34"]["U_m2"] == pytest.approx(10.4121) and w["GF-W34"]["U_change_m2"] == pytest.approx(0.0139)


def test_parapets(reg):
    p = {x["element_id"]: x for x in reg["parapets"]}
    nw = p["1F_ROOF#PARAPET_RC:NW-2"]
    assert nw["carried_refused"].startswith("FLOOR_OUTLINE_RUN")
    assert nw["range_m2"] == [0.0, pytest.approx(3.1672)] and nw["delta_hi_m2"] == pytest.approx(-0.4435)
    assert p["ANNEX_ROOF#PARAPET_RC:NE-6x"]["range_m2"] == [0.0, pytest.approx(0.25999)]
