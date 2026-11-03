"""T-491 Alsenan site preparation (committed values-only input ALSENAN_SITE_PREP_INPUT.json; P7757.dxf ab54dd55).
Re-runs the check without writing and pins the engineering results."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t491"
sys.path.insert(0, str(HERE))
import t491_alsenan_check as C  # noqa: E402

ROWS, SUM, PROP = C.main(write=False)
BY = {r["component"]: r for r in ROWS}
INP = json.loads((HERE / "ALSENAN_SITE_PREP_INPUT.json").read_text(encoding="utf-8"))


def test_input_is_values_only():
    txt = (HERE / "ALSENAN_SITE_PREP_INPUT.json").read_text(encoding="utf-8")
    assert "ab54dd55" in txt
    assert not re.search(r"\d{5,}\.\d", txt)  # no drawing coordinates
    assert not re.search(r"[؀-ۿ]", txt)  # no Arabic note text


def test_boundary_92_740_lm_from_printed_sides_and_dxf_pieces():
    assert SUM["boundary_lm"] == pytest.approx(92.74)
    assert SUM["dxf_sides_sum_lm"] == pytest.approx(92.74)
    for s in INP["boundary_sides_dxf"]:
        assert s["sum_m"] == pytest.approx(s["length_m"])
    assert BY["HOARDING_GROSS_BOUNDARY"]["quantity"] == pytest.approx(92.74)


def test_net_fence_held_on_the_gate_input_with_upper_bound():
    net = BY["HOARDING_FENCE_NET"]
    assert net["status"] == "HELD" and net["quantity"] is None and net["at_most"] == pytest.approx(92.74)
    assert INP["gate_widths"] is None  # permanent openings are evidence only, never used as temporary gates


def test_clearance_470_55_m2_in_scope_by_owner_rule():
    c = BY["SITE_CLEARANCE"]
    assert c["quantity"] == pytest.approx(470.55) and "17:20 (6)" in c["source"]
    assert "PROPOSED" in c["note"]


def test_no_programme_no_default_duration():
    for k in ("GUARD_CABIN_OR_TENT", "WATER_TANKS", "WATER_TANKER_TRIPS", "CONCRETE_PUMP_POURS",
              "POUR_GENERATOR_DAYS", "GENERATOR_FUEL", "GOVERNMENT_TEMPORARY_CONNECTION",
              "SITE_AND_WORKERS_INSURANCE", "HOARDING_GATES"):
        assert BY[k]["status"] == "HELD" and BY[k]["quantity"] is None, k


def test_counts_and_t471_proposal_cover_every_b1_07_component():
    assert SUM["counts"] == {"ASSUMED - OWNER-APPROVED": 1, "DRAWING-CONFIRMED": 2, "HELD": 11}
    ids = {p["component_id"] for p in PROP}
    assert "C-B1-01" in ids
    assert {f"C-B1-07-{r['component']}" for r in ROWS if r["family"] == "B1-07"} <= ids


def test_committed_outputs_match_a_fresh_run():
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(SUM, sort_keys=True))
