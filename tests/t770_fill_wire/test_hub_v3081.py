"""T-770: the hub names ARCH_TAKEOFF_V3.0.81, runs it after the V3.0.79 step (a V3.0.81 run is a V3.0.79 run first) and
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


def test_v3081_inputs_refused_on_v3079(tmp_path):
    assert "--v3081-inputs and --method ARCH_TAKEOFF_V3.0.81 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.79", "--v3081-inputs", "a.json"], tmp_path)


def test_v3081_run_is_a_v3079_run_first(tmp_path):
    """adverse: without the V3.0.79 inputs a V3.0.81 run is refused for those, as a V3.0.79 run would be"""
    flags = [x for n in ALL if n != "3079" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3079-inputs and --method ARCH_TAKEOFF_V3.0.79 go together" in _exit(
        ["--method", A81.METHOD, "--v3081-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3081_after_v3079():
    i79 = HUB.index("identity=ident79, v3_0_78_identity=ident78)")
    i81 = HUB.index("names81, ident81 = A3081.write(out, l3079, raw81, A3079.METHOD)")
    assert i79 < i81 and A81.EXTENDS == "ARCH_TAKEOFF_V3.0.79"
