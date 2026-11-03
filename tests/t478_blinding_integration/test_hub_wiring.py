"""T-478 rebase on the merged V3.0.44: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.45, runs it after the
V3.0.44 step, and refuses a V3.0.45 run without its inputs or V3.0.45 inputs on another method (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3044 as A44  # noqa: E402
from engine.source import arch_v3045 as A45  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3045)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS)
    return str(e.value.code)


def test_extends_merged_v3044():
    assert A45.EXTENDS == A44.METHOD == "ARCH_TAKEOFF_V3.0.44"


def test_v3045_needs_its_inputs(tmp_path):
    assert "needs --v3045-inputs" in _exit(["--method", A45.METHOD], tmp_path)


def test_v3045_inputs_refused_on_v3044(tmp_path):
    assert "--v3045-inputs needs --method ARCH_TAKEOFF_V3.0.45" in _exit(
        ["--method", A44.METHOD, "--v3045-inputs", "a.json"], tmp_path)


def test_hub_chains_v3045_after_v3044():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i44, i45 = src.index("A3044.write("), src.index("A3045.write(")
    assert i44 < i45 and "l3044 = A3044.integrate(l3043, ch_v44, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.45",)' in src
