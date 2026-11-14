"""T-770 r5: the hub names ARCH_TAKEOFF_V3.0.82, runs it after the V3.0.81 step (a V3.0.82 run is a V3.0.81 run first) and
refuses a V3.0.82 run without its package, or the package on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3082 as A82  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3082"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3082_needs_its_inputs(tmp_path):
    assert "--v3082-inputs and --method ARCH_TAKEOFF_V3.0.82 go together" in _exit(["--method", A82.METHOD], tmp_path)


def test_v3082_inputs_refused_on_v3081(tmp_path):
    assert "--v3082-inputs and --method ARCH_TAKEOFF_V3.0.82 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.81", "--v3082-inputs", "a.json"], tmp_path)


def test_v3082_run_is_a_v3081_run_first(tmp_path):
    """adverse: without the V3.0.81 package a V3.0.82 run is refused for it, as a V3.0.81 run would be"""
    flags = [x for n in ALL if n != "3081" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3081-inputs and --method ARCH_TAKEOFF_V3.0.81 go together" in _exit(
        ["--method", A82.METHOD, "--v3082-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3082_after_v3081():
    i81 = HUB.index("identity=ident81, v3_0_79_identity=ident79)")
    i82 = HUB.index("names82, ident82 = A3082.write(out, l3081, raw82)")
    assert i81 < i82 and A82.EXTENDS == "ARCH_TAKEOFF_V3.0.81"
