"""T-770 r8: the hub names ARCH_TAKEOFF_V3.0.85, runs it after the V3.0.84 step (a V3.0.85 run is a V3.0.84 run first) and
refuses a V3.0.85 run without its package, or the package on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3085 as A85  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3085"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3085_needs_its_inputs(tmp_path):
    assert "--v3085-inputs and --method ARCH_TAKEOFF_V3.0.85 go together" in _exit(["--method", A85.METHOD], tmp_path)


def test_v3085_inputs_refused_on_v3084(tmp_path):
    assert "--v3085-inputs and --method ARCH_TAKEOFF_V3.0.85 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.84", "--v3085-inputs", "a.json"], tmp_path)


def test_v3085_run_is_a_v3084_run_first(tmp_path):
    """adverse: without the V3.0.84 package a V3.0.85 run is refused for it, as a V3.0.84 run would be"""
    flags = [x for n in ALL if n != "3084" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3084-inputs and --method ARCH_TAKEOFF_V3.0.84 go together" in _exit(
        ["--method", A85.METHOD, "--v3085-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3085_after_v3084():
    i84 = HUB.index("names84, ident84 = A3084.write(out, l3083, raw84)")
    i85 = HUB.index("names85, ident85 = A3085.write(out, l3084, raw85)")
    assert i84 < i85 and A85.EXTENDS == "ARCH_TAKEOFF_V3.0.84"
