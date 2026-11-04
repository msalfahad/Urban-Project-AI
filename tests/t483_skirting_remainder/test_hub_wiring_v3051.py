"""T-483 r2: ARCH_TAKEOFF_V3.0.51 is rebased on the merged V3.0.50 (T-497 zone ownership, merge 5f8814e8, itself on
V3.0.48): it extends V3.0.50, the hub names it, runs it after the V3.0.50 step (a V3.0.51 run is a V3.0.50 run first),
and refuses a V3.0.51 run without its inputs or V3.0.51 inputs on another method; V3.0.50 still runs on its own (no
data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3050 as A50  # noqa: E402
from engine.source import arch_v3051 as A51  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_extends_merged_v3050():
    assert A51.EXTENDS == A50.METHOD == "ARCH_TAKEOFF_V3.0.50"
    assert A51.METHOD == "ARCH_TAKEOFF_V3.0.51"
    assert A51.REC_KEY != A50.REC_KEY and A51.INPUTS_SCHEMA == "URBAN_V3051_INPUTS_V1"


def test_v3050_waiting_pieces_carried_and_shaft_named():
    for k in A50.WAITING:
        if k != "T443_1F_SHAFT":
            assert A51.WAITING[k] == A50.WAITING[k]
    assert "T483_1F_SHAFT" in A51.WAITING and "T443_1F_SHAFT" not in A51.WAITING


def test_v3051_needs_its_inputs(tmp_path):
    assert "--v3051-inputs and --method ARCH_TAKEOFF_V3.0.51 go together" in _exit(
        ["--method", A51.METHOD, "--v3050-inputs", "y.json"], tmp_path)


def test_v3051_inputs_refused_on_v3050(tmp_path):
    assert "--v3051-inputs and --method ARCH_TAKEOFF_V3.0.51 go together" in _exit(
        ["--method", A50.METHOD, "--v3050-inputs", "y.json", "--v3051-inputs", "a.json"], tmp_path)


def test_v3051_run_is_a_v3050_run_first(tmp_path):
    """adverse: a V3.0.51 run without the V3.0.50 inputs is refused for those, as a V3.0.50 run would be"""
    assert "--v3050-inputs and --method ARCH_TAKEOFF_V3.0.50 go together" in _exit(
        ["--method", A51.METHOD, "--v3051-inputs", "a.json"], tmp_path)


def test_hub_chains_v3051_after_v3050():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i50, i51 = src.index("A3050.write("), src.index("A3051.write(")
    assert i50 < i51 and "l3050 = A3050.integrate(l3048, ch_v50, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.51",)' in src and '("ARCH_TAKEOFF_V3.0.50",)' in src
    # the method is rewritten V3.0.51 -> V3.0.50 before the V3.0.50 line rewrites it to V3.0.48 (flags computed first)
    assert src.index('a.method = "ARCH_TAKEOFF_V3.0.50" if a.v3051') < \
        src.index('a.method = "ARCH_TAKEOFF_V3.0.48" if a.v3050') < src.index("v3044 = a.method in (")
    assert "if a.v3051:" in src and "a.method == \"ARCH_TAKEOFF_V3.0.51\":" not in src


def test_integrate_checks_earthworks_with_the_v3050_check():
    src = (ROOT / "engine/source/arch_v3051.py").read_text(encoding="utf-8")
    assert '"earthworks": A3050.check_zone_owner(out)' in src and "A3043.check_earthworks" not in src
