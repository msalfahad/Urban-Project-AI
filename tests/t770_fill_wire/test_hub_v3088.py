"""T-770 r11: the hub names ARCH_TAKEOFF_V3.0.88, runs it after the V3.0.87 step (a V3.0.88 run is a V3.0.87 run first) and
refuses a V3.0.88 run without its package, or the package on another method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3088 as A88  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

HUB = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
ALL = sorted(set(re.findall(r'"--v(\d+)-inputs"', HUB)) - {"3088"})
FLAGS = [x for n in ALL for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_v3088_needs_its_inputs(tmp_path):
    assert "--v3088-inputs and --method ARCH_TAKEOFF_V3.0.88 go together" in _exit(["--method", A88.METHOD], tmp_path)


def test_v3088_inputs_refused_on_v3087(tmp_path):
    assert "--v3088-inputs and --method ARCH_TAKEOFF_V3.0.88 go together" in _exit(
        ["--method", "ARCH_TAKEOFF_V3.0.87", "--v3088-inputs", "a.json"], tmp_path)


def test_v3088_run_is_a_v3087_run_first(tmp_path):
    """adverse: without the V3.0.87 package a V3.0.88 run is refused for it, as a V3.0.87 run would be"""
    flags = [x for n in ALL if n != "3087" for x in (f"--v{n}-inputs", "x.json")]
    assert "--v3087-inputs and --method ARCH_TAKEOFF_V3.0.87 go together" in _exit(
        ["--method", A88.METHOD, "--v3088-inputs", "a.json"], tmp_path, flags)


def test_hub_chains_v3088_after_v3087():
    i87 = HUB.index("names87, ident87 = A3087.write(out, l3086, raw87)")
    i88 = HUB.index("names88, ident88 = A3088.write(out, l3087, raw88)")
    assert i87 < i88 and A88.EXTENDS == "ARCH_TAKEOFF_V3.0.87"
