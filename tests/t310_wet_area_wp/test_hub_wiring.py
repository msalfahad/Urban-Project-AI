"""T-310 r3: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.52, runs it after the V3.0.50 step (a V3.0.52 run
is a V3.0.50 run first, so a V3.0.2 .. V3.0.48 run first: the method is rewritten on the hub's one V3.0.50 line, the hub
stays line-stable), and refuses a V3.0.52 run without its inputs or V3.0.52 inputs on another method (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3050 as A50  # noqa: E402
from engine.source import arch_v3052 as A52  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) + [3050] for x in (f"--v{n}-inputs", "x.json")]
HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS)
    return str(e.value.code)


def test_extends_merged_v3050():
    assert A52.EXTENDS == A50.METHOD == "ARCH_TAKEOFF_V3.0.50"
    assert A52.METHOD == "ARCH_TAKEOFF_V3.0.52"


def test_v3052_needs_its_inputs(tmp_path):
    assert "--v3052-inputs and --method ARCH_TAKEOFF_V3.0.52 go together" in _exit(["--method", A52.METHOD], tmp_path)


def test_v3052_inputs_refused_on_v3050(tmp_path):
    assert "--v3052-inputs and --method ARCH_TAKEOFF_V3.0.52 go together" in _exit(
        ["--method", A50.METHOD, "--v3052-inputs", "a.json"], tmp_path)


def test_hub_chains_v3052_after_v3050():
    i50, i52 = HUB.index("A3050.write("), HUB.index("A3052.write(")
    assert i50 < i52 and "l3050 = A3050.integrate(l3048, ch_v50, fl24)[0]" in HUB
    assert '("ARCH_TAKEOFF_V3.0.52",)' in HUB
    assert "v30rec = dict(v30rec, method=A3052.METHOD, extends=A3050.METHOD," in HUB


def test_method_rewritten_once_before_the_v3050_line():
    """a V3.0.52 run becomes a V3.0.50 run on the same hub line, before the V3.0.50 flag is read (one line)"""
    line = next(x for x in HUB.splitlines() if "a.v3052 = " in x)
    assert line.index('a.method = "ARCH_TAKEOFF_V3.0.50" if a.v3052') < line.index("a.v3050 = ")
    assert HUB.count("a.v3052 = ") == 1
