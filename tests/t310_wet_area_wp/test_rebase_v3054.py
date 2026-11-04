"""T-310 r6: ARCH_TAKEOFF_V3.0.57 integrates on V3.0.54 lines that already carry the V3.0.54 railing-run records
(T-480, merge 1b66b719) and the V3.0.53 lintel records (T-487, merge dbc619fd). Its invariants re-run both merged
checks on the V3.0.57 lines (arch_v3053.check_lintels, arch_v3054.check_runs): the normal case passes every record
through byte-identical with the same check result; the adverse cases (a railing run re-valued on plan lengths, a held
turn line dropped, a lintel line with its record stripped) are refused by V3.0.57 itself. Fixtures: the synthetic
NON-Alsenan villas D (T-480) and of T-487 (their hand figures, no drawing)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3053 as A53  # noqa: E402
from engine.source import arch_v3054 as A54  # noqa: E402
from engine.source import arch_v3057 as A57  # noqa: E402
from tests.t480_rail_runs import test_arch_v3054 as R  # noqa: E402
from tests.t487_lintel_lines import test_arch_v3053 as L  # noqa: E402


def _v3054():
    c = R.candidate()
    _, _, (out, ident) = R.run(c, R.doc(c))
    return out, ident


def _v3053():
    c = L.candidate()
    _, _, (out, ident) = L.run(c, L.doc(c))
    return out, ident


def test_extends_merged_v3054():
    # r7: V3.0.57 extends V3.0.56 (test_rebase_v3056), which carries V3.0.54 through V3.0.55
    assert A54.METHOD == "ARCH_TAKEOFF_V3.0.54" and A57.METHOD == "ARCH_TAKEOFF_V3.0.57"
    bound = {"T483_1F_SHAFT", "T443_1F_SHAFT"}   # bound by V3.0.56 (R-T508-1 (3)), no longer waiting
    assert set(A54.WAITING) - bound <= set(A57.WAITING) and set(A53.WAITING) - bound <= set(A57.WAITING)


def test_normal_v3054_rail_records_pass_through_unchanged():
    l54, ident54 = _v3054()
    new, ident = A57.integrate(l54, [])
    assert new == l54
    assert ident["rail_runs"] == ident54["rail_runs"]          # the V3.0.54 check, re-run on the V3.0.57 lines
    assert ident["outside_rows_identical_to_base"] == len(l54)


def test_normal_v3053_lintel_records_pass_through_unchanged():
    l53, ident53 = _v3053()
    new, ident = A57.integrate(l53, [])
    assert new == l53
    assert ident["lintels"] == ident53["lintels"]              # the V3.0.53 check, re-run on the V3.0.57 lines


def test_adverse_rail_run_on_plan_lengths_refused():
    l54, _ = _v3054()
    bad = copy.deepcopy(l54)
    for ln in bad:
        if R.eid(ln) == "RAIL:RL-01":
            ln["measured_net"] = ln["gross"] = 2.24 + 1.1 + 2.52           # plan lengths, not the pitch line
    with pytest.raises(ValueError):                    # refused at V3.0.57 integration (the family guard sees it first)
        A57.integrate(bad, [])
    with pytest.raises(ValueError, match="pitch-line sum"):    # and by the V3.0.54 check V3.0.57 re-runs
        A54.check_runs(bad)


def test_adverse_held_turn_line_dropped_refused():
    l54, _ = _v3054()
    bad = [ln for ln in l54 if R.eid(ln) != "RAIL:RL-01:ST-D:T-LD"]
    with pytest.raises(ValueError, match="has no blank line"):
        A57.integrate(bad, [])


def test_adverse_lintel_line_without_its_record_refused():
    l53, _ = _v3053()
    bad = copy.deepcopy(l53)
    ln = next(x for x in bad if x["item_code"] == A53.CODE)
    ln["calculation"]["inputs"].pop(A53.REC_KEY)
    with pytest.raises(ValueError, match="carries no V3.0.53 lintel record"):
        A57.integrate(bad, [])
