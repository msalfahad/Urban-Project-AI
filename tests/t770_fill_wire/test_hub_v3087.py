"""T-770 r10: the hub names ARCH_TAKEOFF_V3.0.87, runs it after the V3.0.86 step (a V3.0.87 run is a V3.0.86 run first) and
refuses a V3.0.87 run without its package, or the package on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3087 as A87  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3087"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3087_needs_its_inputs(tmp_path):
    assert "--v3087-inputs and --method ARCH_TAKEOFF_V3.0.87 go together" in _exit(["--method", A87.METHOD], tmp_path)


def test_v3087_inputs_refused_on_v3086(tmp_path):
    assert "--v3087-inputs and --method ARCH_TAKEOFF_V3.0.87 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.86", "--v3087-inputs", "a.json"], tmp_path)


def test_v3087_run_is_a_v3086_run_first(tmp_path):
    """adverse: without the V3.0.86 package a V3.0.87 run is refused for it, as a V3.0.86 run would be"""
    flags = [x for n in ALL if n != "3086" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3086-inputs and --method ARCH_TAKEOFF_V3.0.86 go together" in _exit(
        ["--method", A87.METHOD, "--v3087-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3087_after_v3086():
    i86 = HUB.index("names86, ident86 = A3086.write(out, l3085, raw86)")
    i87 = HUB.index("names87, ident87 = A3087.write(out, l3086, raw87)")
    assert i86 < i87 and A87.EXTENDS == "ARCH_TAKEOFF_V3.0.86"
