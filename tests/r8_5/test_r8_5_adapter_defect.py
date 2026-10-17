"""Active-path defect report: the project reader's LWPOLYLINE closed test (R8.5 follow-up).

The defect is REPORTED, not fixed: the register pins the adapter file it was measured on, so any change
to that file makes the register stale and it must be regenerated (and a fix must go through migration,
after the column-deduction decision, never in place)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REG = Path(__file__).parent / "registers" / "R8_ADAPTER_DEFECT_CLOSED_FLAG.json"
DECODE = ROOT / "data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json"


def reg():
    return json.loads(REG.read_text())


def test_register_is_a_report_and_pins_the_unchanged_adapter():
    r = reg()
    assert r["status"] == "REPORTED_NOT_FIXED"
    att = r["no_change_attestation"]
    assert att["geometry_py_unchanged"] is True
    assert not any(att[k] for k in ("published_boqs_changed", "frozen_quantities_changed", "owner_answers_changed",
                                    "benchmark_truth_changed"))
    path = ROOT / r["location"]["file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == att["geometry_py_sha256_before"], \
        "adapter changed since the defect was measured: regenerate the register, do not edit it"
    line = path.read_text().splitlines()[r["location"]["line"] - 1]
    assert 'o.get("flag", 0) & 1' in line
    ref = ROOT / r["reference_reading"]["file"]
    assert "& 0x200" in ref.read_text().splitlines()[r["reference_reading"]["line"] - 1]


def test_coincidence_with_the_protected_value_is_recorded_not_decided():
    c = reg()["coincidence_with_protected_value"]
    assert c["room"] == "BA-092" and c["adapter_area_m2"] == 146.97 and c["defect_only_corrected_area_m2"] == 146.7697
    assert c["decides_trade_rule"] is False
    assert "UNDECIDED" in c["note"]


def test_every_r8_5_native_change_is_explained_by_the_defect_alone():
    x = reg()["r8_5_cross_reference"]
    assert x["status"] == "RUN"
    n = x["native_checks"]
    assert x["explained_by_defect_alone"] == n["CHANGED_NATIVE_AREA"] + n["CHANGED_NATIVE_TOPOLOGY"] == 25
    assert x["not_explained"] == 0 and x["not_found"] == 0


@pytest.mark.skipif(not DECODE.exists(), reason="Al Rashed decode not present in this checkout")
def test_register_reproduces_from_the_adapter_and_restores_it(tmp_path):
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_5_adapter_defect as D
    from research.qs_wall_treatment_01.pa09.alrashed import geometry as G
    orig = G._segments
    got = D.main(tmp_path / "r.json")
    assert G._segments is orig
    want = reg()
    for k in ("location", "affected_closed_outlines", "dropped_closing_edges_in_floor_windows",
              "dropped_closing_edges_total", "defect_only_counterfactual", "coincidence_with_protected_value"):
        assert got[k] == want[k], k
    assert got["dropped_closing_edges_total"] == 56
