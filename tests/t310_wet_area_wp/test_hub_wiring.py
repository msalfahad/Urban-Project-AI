"""T-310 r6: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.55, runs it after the V3.0.54 step (a V3.0.55 run
is a V3.0.54 run first, so a V3.0.53 / V3.0.51 / V3.0.50 and a V3.0.2 .. V3.0.48 run first: the method is rewritten on
the hub's one V3.0.53 / V3.0.54 line, before the V3.0.54 test, the hub stays line-stable), and refuses a V3.0.55 run
without its inputs or V3.0.55 inputs on another method (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3053 as A53  # noqa: E402
from engine.source import arch_v3054 as A54  # noqa: E402
from engine.source import arch_v3055 as A55  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) + [3050, 3051, 3053, 3054]
         for x in (f"--v{n}-inputs", "x.json")]
HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_extends_merged_v3054():
    assert A55.EXTENDS == A54.METHOD == "ARCH_TAKEOFF_V3.0.54" and A54.EXTENDS == A53.METHOD


def test_v3055_needs_its_inputs(tmp_path):
    assert "--v3055-inputs and --method ARCH_TAKEOFF_V3.0.55 go together" in _exit(["--method", A55.METHOD], tmp_path)


def test_v3055_inputs_refused_on_v3054(tmp_path):
    assert "--v3055-inputs and --method ARCH_TAKEOFF_V3.0.55 go together" in _exit(
        ["--method", A54.METHOD, "--v3055-inputs", "a.json"], tmp_path)


def test_v3055_needs_the_v3054_inputs_too(tmp_path):
    """a V3.0.55 run IS a V3.0.54 run first: without --v3054-inputs it is refused by the V3.0.54 pairing"""
    flags = list(FLAGS)
    i = flags.index("--v3054-inputs")
    del flags[i:i + 2]
    msg = _exit(["--method", A55.METHOD, "--v3055-inputs", "b.json"], tmp_path, flags)
    assert "--v3054-inputs and --method ARCH_TAKEOFF_V3.0.54 go together" in msg


def test_hub_chains_v3055_after_v3054():
    i53, i54, i55 = HUB.index("A3053.write("), HUB.index("A3054.write("), HUB.index("A3055.write(")
    assert i53 < i54 < i55 and "l3054 = A3054.integrate(l3053, ch_v54, fl24)[0]" in HUB
    assert "ch_v55, log_v55 = A3055.changes_for(inp55, l3054)" in HUB
    assert '("ARCH_TAKEOFF_V3.0.55",)' in HUB
    assert "v30rec = dict(v30rec, method=A3055.METHOD, extends=A3054.METHOD," in HUB
    assert "A3052" not in HUB and "ARCH_TAKEOFF_V3.0.52" not in HUB      # r4's number is not in the hub


def test_method_rewritten_once_before_the_v3054_test():
    """a V3.0.55 run becomes a V3.0.54 run on the same hub line, before the V3.0.54 flag is read (one line)"""
    line = next(x for x in HUB.splitlines() if "a.v3055 = " in x)
    assert line.index('a.method = "ARCH_TAKEOFF_V3.0.54" if a.v3055') < line.index("a.v3054 = ") < \
        line.index("a.v3053")
    assert HUB.count("a.v3055 = ") == 1
