"""T-770 r7: the hub names ARCH_TAKEOFF_V3.0.84, runs it after the V3.0.83 step (a V3.0.84 run is a V3.0.83 run first) and
refuses a V3.0.84 run without its package, or the package on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3084 as A84  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3084"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3084_needs_its_inputs(tmp_path):
    assert "--v3084-inputs and --method ARCH_TAKEOFF_V3.0.84 go together" in _exit(["--method", A84.METHOD], tmp_path)


def test_v3084_inputs_refused_on_v3083(tmp_path):
    assert "--v3084-inputs and --method ARCH_TAKEOFF_V3.0.84 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.83", "--v3084-inputs", "a.json"], tmp_path)


def test_v3084_run_is_a_v3083_run_first(tmp_path):
    """adverse: without the V3.0.83 package a V3.0.84 run is refused for it, as a V3.0.83 run would be"""
    flags = [x for n in ALL if n != "3083" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3083-inputs and --method ARCH_TAKEOFF_V3.0.83 go together" in _exit(
        ["--method", A84.METHOD, "--v3084-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3084_after_v3083():
    i83 = HUB.index("names83, ident83 = A3083.write(out, l3082, raw83)")
    i84 = HUB.index("names84, ident84 = A3084.write(out, l3083, raw84)")
    assert i83 < i84 and A84.EXTENDS == "ARCH_TAKEOFF_V3.0.83"
