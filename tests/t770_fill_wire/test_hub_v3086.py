"""T-770 r9: the hub names ARCH_TAKEOFF_V3.0.86, runs it after the V3.0.85 step (a V3.0.86 run is a V3.0.85 run first) and
refuses a V3.0.86 run without its package, or the package on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3086 as A86  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3086"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3086_needs_its_inputs(tmp_path):
    assert "--v3086-inputs and --method ARCH_TAKEOFF_V3.0.86 go together" in _exit(["--method", A86.METHOD], tmp_path)


def test_v3086_inputs_refused_on_v3085(tmp_path):
    assert "--v3086-inputs and --method ARCH_TAKEOFF_V3.0.86 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.85", "--v3086-inputs", "a.json"], tmp_path)


def test_v3086_run_is_a_v3085_run_first(tmp_path):
    """adverse: without the V3.0.85 package a V3.0.86 run is refused for it, as a V3.0.85 run would be"""
    flags = [x for n in ALL if n != "3085" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3085-inputs and --method ARCH_TAKEOFF_V3.0.85 go together" in _exit(
        ["--method", A86.METHOD, "--v3086-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3086_after_v3085():
    i85 = HUB.index("names85, ident85 = A3085.write(out, l3084, raw85)")
    i86 = HUB.index("names86, ident86 = A3086.write(out, l3085, raw86)")
    assert i85 < i86 and A86.EXTENDS == "ARCH_TAKEOFF_V3.0.85"
