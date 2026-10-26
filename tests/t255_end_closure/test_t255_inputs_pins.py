"""T-255: pins of the development villa's V3.0.19 inputs (research/agents_t255/t255_inputs.py), read from checker
readings and merged ledgers only. The Alsenan lines themselves are private (Drive); these tests pin the inputs and the
rule on them, and an edited ledger or a chord reading stops the build."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t255"))

import t255_inputs as L  # noqa: E402
from engine.source import arch_v3019 as A  # noqa: E402


def test_ring_record_is_the_checker_reading():
    d = A.load_inputs(L.build())
    r = d["records"][0]
    ab = r["arc_band"]
    assert (r["line_id"], r["element_id"], r["before"]["measured_net"], r["value"]) == (
        "L-7076482d75ca42691468", "P-C:GROUND_BEAMS:GROUND:BAND0043", 1.7349, 1.746943)
    assert r["status"] == "DRAWING-CONFIRMED" and r["verified_by"] is None      # VERIFIED only at Gate B
    assert ab["retired_net_m2"] + ab["closing_pieces"][0]["m2"] == pytest.approx(1.83888, abs=1e-9)
    assert ab["drawn_net_m2"] * ab["depth_m"] == pytest.approx(1.746943, abs=5e-7)
    assert r["value"] - r["before"]["measured_net"] == pytest.approx(0.012043, abs=1e-9)    # +0.69 %
    assert [c["id"] for c in ab["columns_in_band"]] == ["17BA"] and ab["columns_in_band"][0]["deducted"]
    assert ab["end_a"]["reading"] == ab["end_b"]["reading"] == "DRAWN_FACES"
    own = ab["own_reproduction"]
    assert abs(own["value_m3"] - r["value"]) < 5e-5                   # this worker's read: 1.746916, -0.0015 %


def test_ring_chord_reading_or_moved_triangle_stops_the_build():
    for mut in (lambda r: r["arc_band"]["end_a"].update(reading="CHORD"),
                lambda r: r["arc_band"]["closing_pieces"][0].update(owned_by="L-other"),
                lambda r: r["arc_band"]["columns_in_band"][0].update(deducted=False),
                lambda r: r["arc_band"].pop("retired_residual")):
        d = L.build()
        mut(d["records"][0])
        with pytest.raises(A.InputsError):
            A.load_inputs(d)


def test_edited_t254_ledger_stops_the_build(monkeypatch, tmp_path):
    f = tmp_path / "T-254.md"
    f.write_text(L.T254.read_text(encoding="utf-8").replace("| 1.7349 | DRAWING-CONFIRMED |", "| 1.7350 | "
                                                                                                "DRAWING-CONFIRMED |"),
                 encoding="utf-8")
    monkeypatch.setattr(L, "T254", f)
    with pytest.raises(SystemExit, match="stale or edited"):
        L.ring_record()


def test_trace_pins_w03_w18():
    d = A.load_inputs(L.build())
    t = {x["opening"]: x["trades"] for x in d["opening_trace"]}
    assert set(t) == {"W03", "W18"}
    assert t["W03"]["WINDOW_SUPPLY_M2"]["value"] == 28.251 and t["W18"]["WINDOW_SUPPLY_M2"]["value"] == 1.08
    assert t["W03"]["MASONRY"]["state"] == "NOT_APPLICABLE"                  # glazed host: nothing built
    pl = t["W03"]["PLASTER_ROOM_SIDE"]
    assert pl["value"] == pytest.approx(6.731 * 3.65) and len(pl["parts"]) == 2
    assert sum(p["value"] for p in pl["parts"]) == pytest.approx(24.56815, abs=1e-9)
    assert [p["state"] for p in pl["parts"]] == ["CARRIED_ONCE", "HELD"]
    assert t["W18"]["MASONRY"]["state"] == "HELD" and t["W18"]["MASONRY"]["value"] == 1.0094
    for o in t.values():                                                      # a held side is never 0
        for x in o.values():
            for p in x.get("parts") or [x]:
                assert p.get("value") is None or p["value"] > 0


def test_trace_double_deduction_or_open_part_dropped_is_refused():
    d = L.build()
    pl = d["opening_trace"][0]["trades"]["PLASTER_ROOM_SIDE"]
    bad = copy.deepcopy(d)
    bad["opening_trace"][0]["trades"]["PLASTER_ROOM_SIDE"]["parts"][1]["line_ids"] = pl["parts"][0]["line_ids"]
    with pytest.raises(A.InputsError, match="two parts"):
        A.load_inputs(bad)
    bad = copy.deepcopy(d)
    bad["opening_trace"][0]["trades"]["PLASTER_ROOM_SIDE"]["parts"][1]["value"] = 5.0
    with pytest.raises(A.InputsError, match="do not close"):
        A.load_inputs(bad)
