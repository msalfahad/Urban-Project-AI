"""T-310 r7: the hub (tools/urban_boq_m9.py) names ARCH_TAKEOFF_V3.0.57, runs it after the V3.0.56 step (a V3.0.57 run
is a V3.0.56 run first, so a V3.0.55 / .54 / .53 / .51 / .50 and a V3.0.2 .. V3.0.48 run first: the method is rewritten on
the hub's one V3.0.53 .. V3.0.56 line, before the V3.0.56 test, the hub stays line-stable), and refuses a V3.0.57 run
without its inputs or V3.0.57 inputs on another method (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3053 as A53  # noqa: E402
from engine.source import arch_v3054 as A54  # noqa: E402
from engine.source import arch_v3055 as A55  # noqa: E402
from engine.source import arch_v3056 as A56  # noqa: E402
from engine.source import arch_v3057 as A57  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) + [3050, 3051, 3053, 3054, 3055, 3056]
         for x in (f"--v{n}-inputs", "x.json")]
HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_extends_merged_v3056():
    assert A57.EXTENDS == A56.METHOD == "ARCH_TAKEOFF_V3.0.56" and A56.EXTENDS == A55.METHOD
    assert A55.EXTENDS == A54.METHOD and A54.EXTENDS == A53.METHOD


def test_v3057_needs_its_inputs(tmp_path):
    assert "--v3057-inputs and --method ARCH_TAKEOFF_V3.0.57 go together" in _exit(["--method", A57.METHOD], tmp_path)


def test_v3057_inputs_refused_on_v3056(tmp_path):
    assert "--v3057-inputs and --method ARCH_TAKEOFF_V3.0.57 go together" in _exit(
        ["--method", A56.METHOD, "--v3057-inputs", "a.json"], tmp_path)


def test_v3057_needs_the_v3056_inputs_too(tmp_path):
    """a V3.0.57 run IS a V3.0.56 run first: without --v3056-inputs it is refused by the V3.0.56 pairing"""
    flags = list(FLAGS)
    i = flags.index("--v3056-inputs")
    del flags[i:i + 2]
    msg = _exit(["--method", A57.METHOD, "--v3057-inputs", "b.json"], tmp_path, flags)
    assert "--v3056-inputs and --method ARCH_TAKEOFF_V3.0.56 go together" in msg


def test_hub_chains_v3057_after_v3056():
    i54, i55, i56, i57 = (HUB.index("A3054.write("), HUB.index("A3055.write("), HUB.index("A3056.write("),
                          HUB.index("A3057.write("))
    assert i54 < i55 < i56 < i57 and "l3056 = A3056.integrate(l3055, ch_v56, fl24)[0]" in HUB
    assert "ch_v57, log_v57 = A3057.changes_for(inp57, l3056)" in HUB
    assert '("ARCH_TAKEOFF_V3.0.57",)' in HUB
    assert "v30rec = dict(v30rec, method=A3057.METHOD, extends=A3056.METHOD," in HUB
    assert "A3052" not in HUB and "ARCH_TAKEOFF_V3.0.52" not in HUB      # r4's number is not in the hub


def test_method_rewritten_once_before_the_v3056_test():
    """a V3.0.57 run becomes a V3.0.56 run on the same hub line, before the V3.0.56 flag is read (one line)"""
    line = next(x for x in HUB.splitlines() if "a.v3057 = " in x)
    assert line.index('a.method = "ARCH_TAKEOFF_V3.0.56" if a.v3057') < line.index("a.v3056 = ") < \
        line.index("a.v3055 = ") < line.index("a.v3054 = ") < line.index("a.v3053")
    assert HUB.count("a.v3057 = ") == 1
