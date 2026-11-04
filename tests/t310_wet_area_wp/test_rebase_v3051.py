"""T-310 r4: ARCH_TAKEOFF_V3.0.55 integrates on V3.0.51 lines that already carry the V3.0.51 skirting remainder records
(hand-calculated NON-Alsenan villa K483 of the T-483 tests: room R1 released 13.0 -> 16.0 lm under two raised sills, a
held range absorbed, floor-glazing / stair-owned ranges closed, a blocked dry cell walked). Its skirting invariants are
arch_v3051.check_remainder on every line (without `before`: the V3.0.50 lines are not this version's input) and the
V3.0.44 check on the lines V3.0.51 did not re-book (a re-booked line carries the superseded V3.0.44 record)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3051 as A51  # noqa: E402
from engine.source import arch_v3055 as A52  # noqa: E402
from tests.t483_skirting_remainder import test_arch_v3051 as T  # noqa: E402


def _v3051():
    return T.run()[1]


def test_extends_merged_v3051():
    """r6: V3.0.55 extends V3.0.54 (test_rebase_v3054), which carries V3.0.51 through V3.0.53: its waiting pieces stay"""
    assert A51.METHOD == "ARCH_TAKEOFF_V3.0.51"
    assert set(A51.WAITING) <= set(A52.WAITING)


def test_normal_v3051_records_pass_through_unchanged():
    l51 = _v3051()
    _, _, ident51, _ = T.run()
    new, ident = A52.integrate(l51, [])
    assert new == l51
    assert ident["remainder"] == ident51["remainder"]          # the V3.0.51 check, re-run on the V3.0.55 lines
    assert ident["remainder"]["released_lm"] == pytest.approx(3.0)
    assert ident["outside_rows_identical_to_base"] == len(l51)


def _rec(lines, action):
    return next(x for x in lines if ((x.get("calculation") or {}).get("inputs") or {}).get(A51.REC_KEY, {}).get("action")
                == action)


def test_adverse_absorbed_range_naming_no_line_refused_by_the_v3051_check():
    """only V3.0.51's own check reads the absorbed range's carrier: it must run on the V3.0.55 lines"""
    l51 = copy.deepcopy(_v3051())
    _rec(l51, "ABSORB_RANGE")["calculation"]["inputs"][A51.REC_KEY]["carried_by"] = "L-" + "0" * 20
    with pytest.raises(ValueError, match="absorbed range line .* names no candidate line"):
        A52.integrate(l51, [])


def test_adverse_released_skirting_line_broken_after_v3051_refused():
    l51 = copy.deepcopy(_v3051())
    T.by_eid(l51, "R1:skirting")["measured_net"] += 1.0      # no longer gross - deductions
    with pytest.raises(ValueError):
        A52.integrate(l51, [])


def test_adverse_closed_range_given_a_figure_refused():
    l51 = copy.deepcopy(_v3051())
    _rec(l51, "CLOSE_RANGE")["measured_net"] = 0.0          # a closed range carries no figure (never 0)
    with pytest.raises(ValueError, match="NOT_APPLICABLE_WITH_EVIDENCE line carries no measured_net"):
        A52.integrate(l51, [])
