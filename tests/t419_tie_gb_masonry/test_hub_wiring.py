"""T-419: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.46, runs it after the V3.0.45 step, and refuses a
V3.0.46 run without its inputs or V3.0.46 inputs on another method (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3045 as A45  # noqa: E402
from engine.source import arch_v3046 as A46  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3046)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS)
    return str(e.value.code)


def test_extends_merged_v3045():
    assert A46.EXTENDS == A45.METHOD == "ARCH_TAKEOFF_V3.0.45"


def test_v3046_needs_its_inputs(tmp_path):
    assert "needs --v3046-inputs" in _exit(["--method", A46.METHOD], tmp_path)


def test_v3046_inputs_refused_on_v3045(tmp_path):
    assert "--v3046-inputs needs --method ARCH_TAKEOFF_V3.0.46" in _exit(
        ["--method", A45.METHOD, "--v3046-inputs", "a.json"], tmp_path)


def test_hub_chains_v3046_after_v3045():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i45, i46 = src.index("A3045.write("), src.index("A3046.write(")
    assert i45 < i46 and "l3045 = A3045.integrate(l3044, ch_v45, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.46",)' in src
    assert 'V3046, v3045 = "ARCH_TAKEOFF_V3.0.46", a.method in (V3045, "ARCH_TAKEOFF_V3.0.46")' in src
    assert "v3046 = a.method == V3046" in src
