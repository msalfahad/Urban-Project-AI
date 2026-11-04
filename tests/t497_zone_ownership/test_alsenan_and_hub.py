"""T-497: the development-villa inputs (research/agents_t497/t497_inputs.py, read from the sha-pinned re-measure, no
private file needed) equal the Checker's F-C-T350R4-1 figures; the summary's scenario set is consistent; the hub names
ARCH_TAKEOFF_V3.0.50, runs it after the V3.0.48 step and refuses it without its inputs (no data needed)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t497"))

import t497_inputs as T  # noqa: E402
from engine.source import arch_v3048 as A48  # noqa: E402
from engine.source import arch_v3050 as A  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

S = json.loads((ROOT / "research/agents_t497/summary_t497.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def z():
    return A.load_inputs(T.build("p"), "p")["_zones"][0]


def test_trench_is_the_checker_figure(z):
    assert (z["_lo"], z["_hi"]) == (1.069269, 1.176467)                      # F-C-T350R4-1, drawn-outline scenario
    assert (z["_wlo"], z["_whi"]) == (1.203269, 1.432834)                    # the V3.0.48 range it replaces
    assert z["given_up_m2"] == {"F10F": 1.675, "footing pits": 14.479847}
    assert z["element_id"] == "EW-T350:B1-02:Z1-TRENCH-EXT-GB-MAIN" and z["evidence_status"] == "HELD"


def test_reconciliation_in_m2_closes(z):
    """V3.0.48 high 1.432834 = (27.919513 - 13.591177) x 0.10; the restated high = (27.919513 - 14.479847 - 1.675) x 0.10:
    the difference 0.256367 m3 = (0.888670 pits beyond-plot + 1.675 F10F) x 0.10, nothing else"""
    s = S["reproduced_t484"]
    do = S["scenarios"]["drawn outline"]
    own = s["strip_total_m2"] - sum(z["given_up_m2"].values())
    assert own == pytest.approx(do["trench_in_plot_m2"] + do["trench_beyond_plot_m2"], abs=2e-6)
    assert z["_whi"] - z["_hi"] == pytest.approx((14.479847 - s["in_zone_m2"] + 1.675) * 0.10, abs=2e-6)
    assert z["_wlo"] - z["_lo"] == pytest.approx(do["trench_given_up_in_plot_m2"]["F10F"] * 0.10, abs=2e-6)


def test_excavation_bound_contains_every_consistent_scenario():
    b = S["excavation_held_bound_m3"]
    assert b["v3048"] == [8.467769, 9.824584] and b["restated"] == [8.333769, 9.568217]
    assert b["restated"][0] <= b["consistent_scenarios"][0] and b["consistent_scenarios"][1] <= b["restated"][1]
    assert S["f10f_m3_all_scenarios"] == [7.2645, 8.39175]                  # the F10F line, unchanged
    for r in S["scenarios"].values():
        assert r["pits_in_plot_m2"] == pytest.approx(124.649045)             # the pits plan never moves
        assert r["trench_m3"][0] >= 1.069269 - 1e-9                          # the drawn outline is the smallest trench


def test_edited_input_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.S497, "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        T.build()


def test_extends_merged_v3048():
    assert A.EXTENDS == A48.METHOD == "ARCH_TAKEOFF_V3.0.48"


FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS)
    return str(e.value.code)


def test_v3050_needs_its_inputs(tmp_path):
    assert "--v3050-inputs and --method ARCH_TAKEOFF_V3.0.50 go together" in _exit(["--method", A.METHOD], tmp_path)


def test_v3050_inputs_refused_on_v3048(tmp_path):
    assert "go together" in _exit(["--method", A48.METHOD, "--v3050-inputs", "a.json"], tmp_path)


def test_hub_chains_v3050_after_v3048():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i48, i50 = src.index("A3048.write("), src.index("A3050.write(")
    assert i48 < i50 and "l3048 = A3048.integrate(l3047, ch_v48, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.50",)' in src
    # a V3.0.50 run is a V3.0.48 run first: the method is rewritten before every stage list is evaluated
    assert src.index('a.method = "ARCH_TAKEOFF_V3.0.48" if a.v3050') < src.index("v3044 = a.method in (")
