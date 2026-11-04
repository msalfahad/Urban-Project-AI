"""T-310 r3: ARCH_TAKEOFF_V3.0.52 integrates on V3.0.50 lines that already carry a V3.0.50 zone-ownership restatement
(hand-calculated NON-Alsenan villa E350 / E497 of the T-497 tests: trench Z1-T1 restated 0.185 .. 0.225 -> 0.165 ..
0.180 m3). Its earthworks invariant is arch_v3050.check_zone_owner on the V3.0.52 lines WITHOUT `before` (the V3.0.50
lines are not the V3.0.48 form: the V3.0.48 check must see the line rebuilt from the record). Found on the Drive run of
r3, where `before=prev` refused the restated trench line."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3048 as A48  # noqa: E402
from engine.source import arch_v3050 as A50  # noqa: E402
from engine.source import arch_v3052 as A52  # noqa: E402
from tests.t497_zone_ownership import test_arch_v3050 as T  # noqa: E402


def _v3050():
    prev, ch, _ = T.run()
    return A50.integrate(prev, ch)[0]


def test_normal_restated_trench_passes_through_unchanged():
    l50 = _v3050()
    new, ident = A52.integrate(l50, [])
    assert new == l50
    e = ident["earthworks"]
    assert e["restated"] == 1 and (e["restated_low_m3"], e["restated_high_m3"]) == (0.165, 0.18)
    assert e["earthworks_v3048"]["ranged"] == 2


def test_adverse_restated_trench_grown_beyond_its_record_refused():
    l50 = copy.deepcopy(_v3050())
    t = T._el(l50, A48.EXC, T.EID)
    t["bounded_range"]["high"] = 0.250                     # above both its record (0.180) and the range it replaced
    with pytest.raises(ValueError, match="not held at its record's range"):
        A52.integrate(l50, [])
