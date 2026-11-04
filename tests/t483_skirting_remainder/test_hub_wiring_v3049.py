"""T-483 r2: ARCH_TAKEOFF_V3.0.49 is rebased on the merged V3.0.48 (T-350 r4 earthworks, merge 5de697ff): it extends
V3.0.48, the hub names it, runs it after the V3.0.48 step, and refuses a V3.0.49 run without its inputs or V3.0.49
inputs on another method; V3.0.48 still runs on its own (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3048 as A48  # noqa: E402
from engine.source import arch_v3049 as A49  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402

FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path, flags=FLAGS):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + flags)
    return str(e.value.code)


def test_extends_merged_v3048():
    assert A49.EXTENDS == A48.METHOD == "ARCH_TAKEOFF_V3.0.48"
    assert A49.METHOD == "ARCH_TAKEOFF_V3.0.49"
    assert A49.REC_KEY != A48.REC_KEY and A49.INPUTS_SCHEMA == "URBAN_V3049_INPUTS_V1"


def test_v3048_waiting_pieces_carried_and_shaft_named():
    for k in A48.WAITING:
        if k != "T443_1F_SHAFT":
            assert A49.WAITING[k] == A48.WAITING[k]
    assert "T483_1F_SHAFT" in A49.WAITING and "T443_1F_SHAFT" not in A49.WAITING


def test_v3049_needs_its_inputs(tmp_path):
    assert "needs --v3049-inputs" in _exit(["--method", A49.METHOD], tmp_path)


def test_v3049_inputs_refused_on_v3048(tmp_path):
    flags = [x for x in FLAGS]
    assert "--v3049-inputs needs --method ARCH_TAKEOFF_V3.0.49" in _exit(
        ["--method", A48.METHOD, "--v3049-inputs", "a.json"], tmp_path, flags)


def test_v3048_alone_still_needs_only_its_own_inputs(tmp_path):
    """adverse: a V3.0.48 run without --v3048-inputs is refused for the V3.0.48 inputs, never for V3.0.49's"""
    flags = [x for n in list(range(302, 310)) + list(range(3010, 3048)) for x in (f"--v{n}-inputs", "x.json")]
    msg = _exit(["--method", A48.METHOD], tmp_path, flags)
    assert "needs --v3048-inputs" in msg and "v3049" not in msg


def test_hub_chains_v3049_after_v3048():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i48, i49 = src.index("A3048.write("), src.index("A3049.write(")
    assert i48 < i49 and "l3048 = A3048.integrate(l3047, ch_v48, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.49",)' in src and '("ARCH_TAKEOFF_V3.0.48",)' in src


def test_integrate_checks_earthworks_with_the_v3048_check():
    src = (ROOT / "engine/source/arch_v3049.py").read_text(encoding="utf-8")
    assert '"earthworks": A3048.check_earthworks(out)' in src and "A3043.check_earthworks" not in src


def test_hub_flag_survives_the_v213_rewrite():
    """adverse (as T-350 r4): the hub rewrites a.method to V2.13 before the stages run, so the V3.0.49 stage is gated by
    a flag computed beforehand, never by a.method; a V3.0.49 run sets the V3.0.48 flag too"""
    hub = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    assert "a.method == V3049:" not in hub and "if v3049:" in hub
    assert "v3049 = a.method == V3049  " in hub and "v3048 = v3048 or v3049" in hub
    assert hub.index("v3048 = v3048 or v3049") < hub.index('if getattr(a, "v3048_inputs", None) and not v3048:')
