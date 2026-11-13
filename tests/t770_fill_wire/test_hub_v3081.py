"""T-770: the hub names ARCH_TAKEOFF_V3.0.81, runs it after the V3.0.78 step (a V3.0.81 run is a V3.0.78 run first) and
refuses a V3.0.81 run without its fix-row set, or a fix-row set on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as A81  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3081"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3081_needs_its_inputs(tmp_path):
    assert "--v3081-inputs and --method ARCH_TAKEOFF_V3.0.81 go together" in _exit(["--method", A81.METHOD], tmp_path)


def test_v3081_inputs_refused_on_v3078(tmp_path):
    assert "--v3081-inputs and --method ARCH_TAKEOFF_V3.0.81 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.78", "--v3081-inputs", "a.json"], tmp_path)


def test_v3081_run_is_a_v3078_run_first(tmp_path):
    """adverse: without the V3.0.78 inputs a V3.0.81 run is refused for those, as a V3.0.78 run would be"""
    flags = [x for n in ALL if n != "3078" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3078-inputs and --method ARCH_TAKEOFF_V3.0.78 go together" in _exit(
        ["--method", A81.METHOD, "--v3081-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3081_after_v3078():
    i78 = HUB.index("identity=ident78, v3_0_77_identity=ident77)")
    i81 = HUB.index("names81, ident81 = A3081.write(out, l3078, raw81, A3078.METHOD)")
    assert i78 < i81 and A81.EXTENDS == "ARCH_TAKEOFF_V3.0.78"
