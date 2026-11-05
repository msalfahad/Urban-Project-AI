"""T-533 on the development villa: committed outputs reproduce from the pinned merged inputs; the 15 carried 0.15 m
walls stay HELD by name (no unit, mortar, cement or sand value); scenario S-A reproduces T-520 / T-506 figures."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t533"
sys.path.insert(0, str(HERE))
import block_module_v1 as BM  # noqa: E402
import t533_alsenan as A  # noqa: E402


def _csv(name):
    return list(csv.DictReader((HERE / "out" / name).open(encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_fifteen_walls_held_blank():
    rows = _csv("WALLS_015_T533.csv")
    assert len(rows) == 15 and len({r["wall_id"] for r in rows}) == 15
    assert not {"GF-W22", "2F-W08"} & {r["wall_id"] for r in rows}
    for r in rows:
        assert r["status"] == "HELD" and r["held"] == BM.MISSING_015
        assert all(r[k] == "" for k in ("units_nr", "panel_mortar_m3", "perimeter_mortar_m3", "cement_bags", "sand_m3"))


def test_register_has_no_015_module():
    reg, not_given = A.register()
    assert {e.thickness_m for e in reg} == {0.20}
    assert any("15 cm" in s for s in not_given)


def test_s_a_reproduces_t520_and_t506():
    s = json.loads((HERE / "out" / "SUMMARY_T533.json").read_text(encoding="utf-8"))
    t520 = json.loads((ROOT / "research/agents_t520/out/SUMMARY_T520.json").read_text(encoding="utf-8"))
    b = t520["beside_015_held_module"]
    assert float(s["s_a_reproduces_t520"]["perimeter_figure_m3"]) == pytest.approx(b["perimeter_figure_m3"], abs=1e-6)
    assert float(s["s_a_reproduces_t520"]["perimeter_high_m3"]) == pytest.approx(b["perimeter_high_m3"], abs=1e-6)
    assert float(s["s_a_reproduces_t520"]["panel_contract_m3"]) == pytest.approx(b["panel_m3"], abs=5e-6)
    sc = {r["scenario"]: r for r in _csv("SCENARIOS_015_T533.csv")}
    lo, hi = (float(x) for x in sc["S-A"]["panel_m3_material_base"].split(" .. "))
    assert hi == pytest.approx(1.945573, abs=1e-6) and lo == pytest.approx(1.941811, abs=2e-6)   # T-506 beside / low
    assert all(r["label"].startswith("FIGURE BESIDE, NOT A QUANTITY") for r in sc.values())


def test_scenario_spread_by_hand():
    # material base 175.871 m2: units 12.5 / 11.614402 / 10 per m2; panel t (1 - kappa) per m2
    sc = {r["scenario"]: r for r in _csv("SCENARIOS_015_T533.csv")}
    assert float(sc["S-A"]["units_nr_material_base"].split(" .. ")[1]) == pytest.approx(175.871 * 12.5, abs=0.01)
    assert float(sc["S-C"]["units_nr_material_base"].split(" .. ")[1]) == pytest.approx(1758.71, abs=0.01)
    assert float(sc["S-C"]["mortar_m3_per_m2"]) == pytest.approx(0.15 * (1 - 0.39 * 0.24 / 0.10), abs=1e-9)
    assert float(sc["S-B"]["units_per_m2"]) == pytest.approx(1 / (0.41 * 0.21), abs=1e-6)


def test_adverse_a_sourced_015_entry_stops_the_held_builder(monkeypatch):
    reg, ng = A.register()
    extra = BM.ModuleEntry("BLACK", 0.15, 0.39, 0.19, 0.01, 0.01, "test supplier record", "SUPPLIER_RECORD")
    monkeypatch.setattr(A, "register", lambda: (reg + [extra], ng))
    with pytest.raises(BM.ModuleError):
        A.build()
