"""T-310 r7: ARCH_TAKEOFF_V3.0.57 integrates on V3.0.56 lines that already carry the V3.0.56 stair skirting records
(T-508, merge 40ab9061) and the V3.0.55 blockwork wiring records (T-488, merge e8143e40). Its invariants re-run both
merged checks on the V3.0.57 lines (arch_v3055.check_wiring, arch_v3056.check_stair_skirting), and the V3.0.44 skirting
check reads only the lines neither V3.0.51 nor V3.0.56 re-recorded: the normal case passes every record through
byte-identical with the same check result; the adverse cases (a held roof-datum wall released, both stair skirting forms
valued, a landing piece at 0, a lone form-pair line) are refused by V3.0.57 itself. Fixtures: the synthetic NON-Alsenan
villas of T-488 and K508 of T-508 (their hand figures, no drawing)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3055 as A55  # noqa: E402
from engine.source import arch_v3056 as A56  # noqa: E402
from engine.source import arch_v3057 as A57  # noqa: E402
from tests.t488_blockwork_wiring import test_arch_v3055 as B  # noqa: E402
from tests.t508_stair_skirting import test_arch_v3056 as S  # noqa: E402


def test_extends_merged_v3056():
    assert A57.EXTENDS == A56.METHOD == "ARCH_TAKEOFF_V3.0.56" and A57.METHOD == "ARCH_TAKEOFF_V3.0.57"
    assert A56.EXTENDS == A55.METHOD
    assert set(A56.WAITING) <= set(A57.WAITING)


def test_normal_v3056_stair_skirting_records_pass_through_unchanged():
    _, l56, ident56, _ = S.run()
    new, ident = A57.integrate(l56, [])
    assert new == l56
    assert ident["stair_skirting"] == ident56["stair_skirting"]   # the V3.0.56 check, re-run on the V3.0.57 lines
    assert ident["outside_rows_identical_to_base"] == len(l56)


def test_normal_v3055_wiring_records_pass_through_unchanged():
    l55, ident55, *_ = B.run()
    new, ident = A57.integrate(l55, [])
    assert new == l55
    assert ident["wiring"] == ident55["wiring"]                   # the V3.0.55 check, re-run on the V3.0.57 lines


def test_adverse_held_roof_datum_wall_released_refused():
    l55, *_ = B.run()
    bad = copy.deepcopy(l55)
    for ln in bad:
        if ln["calculation"]["inputs"].get(A55.REC_KEY, {}).get("action") == "PART_HELD":
            ln["evidence_state"], ln["measured_net"] = "SOURCE_DERIVED", 11.2
            break
    with pytest.raises(ValueError):
        A57.integrate(bad, [])


def test_adverse_both_stair_skirting_forms_valued_refused():
    _, l56, _, _ = S.run()
    bad = copy.deepcopy(l56)
    for ln in bad:
        if ln["item_code"] in (A56.ZIG, A56.SLO):
            ln["evidence_state"], ln["measured_net"], ln["gross"], ln["rfi"] = "MEASURED", 1.0, 1.0, None
    with pytest.raises(ValueError):
        A57.integrate(bad, [])


def test_adverse_zero_landing_and_lone_pair_line_refused():
    _, l56, _, _ = S.run()
    bad = copy.deepcopy(l56)
    for ln in bad:
        if ln["location"]["element_id"] == "STAIR-SKIRT:LD:landing":
            ln["measured_net"] = ln["gross"] = 0.0
    with pytest.raises(ValueError):
        A57.integrate(bad, [])
    drop = next(ln["line_id"] for ln in l56 if ln["item_code"] == A56.SLO)
    with pytest.raises(ValueError):
        A57.integrate([ln for ln in l56 if ln["line_id"] != drop], [])


def test_v3056_re_recorded_skirting_not_read_by_the_v3044_check():
    """a room skirting line V3.0.56 re-recorded (shaft stretches retired) is checked by V3.0.56's own check only"""
    _, l56, _, _ = S.run()
    rec = [ln for ln in l56 if ((ln.get("calculation") or {}).get("inputs") or {}).get(A56.REC_KEY)]
    assert rec, "the K508 fixture carries V3.0.56 records"
    new, ident = A57.integrate(l56, [])
    assert new == l56 and "skirting" in ident
