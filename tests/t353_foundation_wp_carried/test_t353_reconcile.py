"""T-353: R-T353-1 gap re-check before integrating a 'missing' family.

Villa Q-353 by hand (not the development villa): foundation WP pieces
  membrane 6.340 m2 (released) + 1 held; screed 6.340 m2 + 0.317 m3 (released); pit membrane 21.360 m2 (released) +
  walls held; procurement held (item)
  -> m2: 5 lines (3 released + 2 held), released 6.340 + 6.340 + 21.360 = 34.040, 2 held blank; m3: 1 line 0.317; item: 1 held.
A candidate row with these figures -> ALREADY_CARRIED (no new version: it would double count 34.040 m2 / 0.317 m3).
Adverse: the candidate twice the pieces (a second integration) -> DIFFERS by +34.040 m2; a held line as 0 refused; a
held range in the candidate named; mm-scale figure differs; no shared code -> NOT_CARRIED.
Development villa: the T-270 records (V3.0.15) equal the V3.0.42 completeness row (19 lines, 360.0282 m2, 6.5275 m3,
11 held blank).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t353"))
import t353_reconcile as R  # noqa: E402

M, S, PM, PR = ("WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.FOOTING_SCREED", "WP.FOUNDATION.LIFT_PIT_MEMBRANE",
                "WP.FOUNDATION.PROCUREMENT")


def _recs():
    return [{"id": "m", "item_code": M, "unit": "m2", "state": "RELEASED", "value": 6.34},
            {"id": "m-h", "item_code": M, "unit": "m2", "state": "HELD", "value": None},
            {"id": "s2", "item_code": S, "unit": "m2", "state": "RELEASED", "value": 6.34},
            {"id": "s3", "item_code": S, "unit": "m3", "state": "RELEASED", "value": 0.317},
            {"id": "pm", "item_code": PM, "unit": "m2", "state": "RELEASED", "value": 21.36},
            {"id": "pm-h", "item_code": PM, "unit": "m2", "state": "HELD", "value": None},
            {"id": "p", "item_code": PR, "unit": "item", "state": "HELD", "value": None}]


def _row(scale=1.0):
    def u(lines, rel, held):
        return {"lines": lines, "released": round(rel * scale, 6), "verified": 0.0, "held_low": 0.0,
                "held_high": 0.0, "held_unknown_lines": held}
    return {"family": "B8-08", "item_codes": [M, S, PM, PR],
            "quantities": {"m2": u(5, 34.04, 2), "m3": u(1, 0.317, 0), "item": u(1, 0.0, 1)}}


def test_hand_totals():
    t = R.record_totals(_recs())
    assert t["m2"] == {"lines": 5, "released": 34.04, "held_lines": 2}
    assert t["m3"] == {"lines": 1, "released": 0.317, "held_lines": 0}
    assert t["item"] == {"lines": 1, "released": 0.0, "held_lines": 1}


def test_already_carried():
    r = R.reconcile(_recs(), _row())
    assert r["verdict"] == "ALREADY_CARRIED" and r["differences"] == []


def test_second_integration_is_named_not_netted():
    row = _row()
    row["quantities"]["m2"].update(lines=10, released=68.08, held_unknown_lines=4)
    r = R.reconcile(_recs(), row)
    assert r["verdict"] == "DIFFERS"
    assert any("+34.040000" in d for d in r["differences"])


def test_held_as_zero_refused():
    recs = _recs()
    recs[1]["value"] = 0
    with pytest.raises(ValueError, match="held line carries a figure"):
        R.record_totals(recs)


def test_released_without_figure_refused():
    recs = _recs()
    recs[0]["value"] = None
    with pytest.raises(ValueError, match="without a positive figure"):
        R.record_totals(recs)


def test_held_range_in_candidate_named():
    row = _row()
    row["quantities"]["m2"]["held_low"] = 1.5
    assert R.reconcile(_recs(), row)["verdict"] == "DIFFERS"


def test_units_mm_scale_differs():
    assert R.reconcile(_recs(), _row(scale=1000.0))["verdict"] == "DIFFERS"


def test_not_carried():
    row = copy.deepcopy(_row())
    row["item_codes"] = ["STR.CONC.BLINDING"]
    assert R.reconcile(_recs(), row)["verdict"] == "NOT_CARRIED"


def test_development_villa_v3042_carries_t270_unchanged():
    sys.path[:0] = [str(ROOT), str(ROOT / "research" / "agents_t270")]
    import t270_inputs as T
    recs = T.records()
    assert len(recs) == 19
    assert "STR.CONC.BLINDING" not in {r["item_code"] for r in recs}      # the blinding stays CONCRETE
    matrix = json.loads((ROOT / R.MATRIX).read_text(encoding="utf-8"))
    assert matrix["candidate_version"] == "ARCH_TAKEOFF_V3.0.42"
    r = R.reconcile(recs, R.matrix_row(matrix, "B8-08"))
    assert r["verdict"] == "ALREADY_CARRIED", r["differences"]
    assert r["pieces"]["m2"] == {"lines": 15, "released": 360.0282, "held_lines": 9}
    assert r["pieces"]["m3"] == {"lines": 3, "released": 6.5275, "held_lines": 1}
