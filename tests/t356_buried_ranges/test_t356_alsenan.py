"""T-356 development-villa checks on the COMMITTED outputs (a consumer reads the files, not the builder)."""

import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t356"
sys.path.insert(0, str(HERE))
import t356_alsenan as A  # noqa: E402

AP = pytest.approx


def _rows(name):
    return list(csv.DictReader(io.StringIO((HERE / name).read_text(encoding="utf-8"))))


@pytest.fixture(scope="module")
def built():
    return A.main([])


def test_byte_rebuild(built):
    for name, text in built.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_of_record():
    s = json.loads((HERE / "summary_t356.json").read_text(encoding="utf-8"))
    assert s["candidate"] == "ARCH_TAKEOFF_V3.0.24"
    assert s["candidate_lines_json_sha256"].startswith("19394733")


def test_input_values_only_and_identity():
    d = json.loads((HERE / "ALSENAN_T356_INPUT.json").read_text(encoding="utf-8"))
    assert d["source"]["sha256"].startswith("9f9d1179")
    assert d["band"]["centreline_m"] == AP(91.94) and d["band"]["crossing_total_m"] == AP(21.45)
    assert d["band"]["crossing_outline_count"] == 9
    assert d["straps_total"]["own_strip_m2"] == AP(9.10196, abs=1e-6)


def test_every_t347_over_line_finding_answered():
    ids = {r["line_id"] for r in _rows("FINDINGS_T356.csv")}
    for lid in ("L-35382b18e2e362df3ae6", "L-6290a9f3d93f38cd46d6", "L-81444e222487437e257e",
                "L-e2134034441cb7db7bd7", "L-0c5ede7fd2c9e425aa8d", "L-f0e25ad2cf73bf2a35ea",
                "L-970bac563cbcd69e2a30", "L-f24cf117a9ce1e875785"):
        assert lid in ids


def test_strap_range_and_decomposition_closes():
    s = json.loads((HERE / "summary_t356.json").read_text(encoding="utf-8"))["strap_blinding"]
    assert s["ledger"] == [0.0, AP(0.912684, abs=1e-6)]                    # printed widths x drawn axis clear
    assert s["drawn_polygon_high"] == AP(0.910196, abs=1e-6)                # the drawn polygon, kept as the check
    assert abs(s["t233_minus_ledger"]) < 0.001                              # T-100 / T-233 0.913 (rounded lengths)
    assert sum(s["decomposition_m3"].values()) == AP(s["line"][1], abs=1e-6)
    assert s["decomposition_m3"]["gb_blinding_plan_deduction"] < 0          # the inadmissible deduction is named


def test_band_line_not_a_reading():
    r = [x for x in _rows("FINDINGS_T356.csv") if x["line_id"] == "L-6290a9f3d93f38cd46d6"][0]
    assert r["verdict"] == "CORRECT_RANGE"
    assert (float(r["ledger_low"]), float(r["ledger_high"])) == (AP(5.6392), AP(11.0328))


def test_fill_held_blank_never_zero():
    for r in _rows("FILL_T350_T356.csv"):
        assert r["status"] == "HELD" and r["value_m3"] == ""
        if r["lo_m3"] == "0.000000":
            assert r["lo_basis"].startswith("READING_NONE")                # a reading, never a defaulted zero
        assert r["hi_m3"] not in ("", "0.000000")
    band = [r for r in _rows("FILL_T350_T356.csv") if r["line_id"] == "L-6290a9f3d93f38cd46d6"][0]
    assert band["lo_m3"] == ""                                                 # not established, not 0


def test_downgrades_only_for_single_readings():
    d = json.loads((HERE / "DOWNGRADE_PROPOSALS_T356.json").read_text(encoding="utf-8"))["proposals"]
    right = {r["line_id"] for r in _rows("FINDINGS_T356.csv") if r["verdict"] == "LINE_RIGHT"}
    for p in d:
        assert p["proposed_state"] == "HELD" and p["issued_by"].startswith("PROPOSAL")
        assert not right & set(p["line_ids"])
        lo, hi = p["audit_range_m3"]
        assert lo <= hi
    gb = [p for p in d if p["proposal_id"] == "DGP-T356-GB-D34"][0]
    assert len(gb["line_ids"]) == 9
    assert gb["audit_range_m3"] == [AP(1.643901, abs=1e-6), AP(2.291867, abs=1e-6)]
