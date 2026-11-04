"""T-310: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.49, runs it after the V3.0.48 step (a V3.0.49 run is
a V3.0.2 .. V3.0.48 run first), gates it by a flag set before the V2.13 rewrite, and refuses a V3.0.49 run without its
inputs or V3.0.49 inputs on another method (no data needed)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3048 as A48  # noqa: E402
from engine.source import arch_v3049 as A49  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) for x in (f"--v{n}-inputs", "x.json")]
HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS)
    return str(e.value.code)


def test_extends_merged_v3048():
    assert A49.EXTENDS == A48.METHOD == "ARCH_TAKEOFF_V3.0.48"


def test_v3049_needs_its_inputs(tmp_path):
    assert "needs --v3049-inputs" in _exit(["--method", A49.METHOD], tmp_path)


def test_v3049_inputs_refused_on_v3048(tmp_path):
    assert "--v3049-inputs needs --method ARCH_TAKEOFF_V3.0.49" in _exit(
        ["--method", A48.METHOD, "--v3049-inputs", "a.json"], tmp_path)


def test_hub_chains_v3049_after_v3048():
    i48, i49 = HUB.index("A3048.write("), HUB.index("A3049.write(")
    assert i48 < i49 and "l3048 = A3048.integrate(l3047, ch_v48, fl24)[0]" in HUB
    assert '("ARCH_TAKEOFF_V3.0.49",)' in HUB


def test_every_earlier_stage_runs_for_v3049():
    """every method list naming V3.0.48 names V3.0.49 too, except the T-443 / T-350 r4 flag line, which the T-310 line
    right below it widens (v3047 / v3048 or v3049)"""
    lists = [x for x in re.findall(r"a\.method in \(([^)]*)\)", HUB) if re.search(r"\bV3048\b", x)]
    missing = [x for x in lists if not re.search(r"\bV3049\b", x)]
    assert missing == ["V3047, V3048"]
    assert "v3047, v3048 = v3047 or v3049, v3048 or v3049" in HUB


def test_flag_not_a_method_compare_in_the_stage():
    assert "if v3049:" in HUB and "v3049 = a.method == V3049  " in HUB
    assert HUB.count("a.method == V3049") == 1
