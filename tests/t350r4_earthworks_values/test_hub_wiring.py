"""T-350 r4: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.48, runs it after the V3.0.47 step, and refuses a
V3.0.48 run without its inputs or V3.0.48 inputs on another method (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3047 as A47  # noqa: E402
from engine.source import arch_v3048 as A48  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3048)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS)
    return str(e.value.code)


def test_extends_merged_v3047():
    assert A48.EXTENDS == A47.METHOD == "ARCH_TAKEOFF_V3.0.47"


def test_v3048_needs_its_inputs(tmp_path):
    assert "needs --v3048-inputs" in _exit(["--method", A48.METHOD], tmp_path)


def test_v3048_inputs_refused_on_v3047(tmp_path):
    assert "--v3048-inputs needs --method ARCH_TAKEOFF_V3.0.48" in _exit(
        ["--method", A47.METHOD, "--v3048-inputs", "a.json"], tmp_path)


def test_hub_chains_v3048_after_v3047():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i47, i48 = src.index("A3047.write("), src.index("A3048.write(")
    assert i47 < i48 and "l3047 = A3047.integrate(l3046, ch_v47, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.48",)' in src
