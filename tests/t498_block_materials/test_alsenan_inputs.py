"""T-498: the development-villa inputs of V3.0.59 rebuild from the pinned merged files (no drawing needed) and carry the
recomputed material figures on the V3.0.58 masonry lines (= V3.0.56: T-310 / T-507 moved WP only) (T-453 r2 machinery with the T-488 held walls)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t498"))

import t498_inputs as L  # noqa: E402
from engine.source import arch_v3059 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return L.build("p")


def test_inputs_load_and_rates_are_rulebook_records(doc):
    d = A.load_inputs(doc, "p")
    assert d["rulebook"]["p"][A.R_BLOCK]["blocks_per_m2_40x20_module"] == 12.5
    assert set(d["rulebook"]["p"][A.R_GLUE]["kg_per_m2_by_thickness_m"]) == {"0.15", "0.20"}


def test_reconciliation_closes_and_t488_walls_held(doc):
    b = doc["beside"]
    assert all(abs(r) <= 0.0005 for r in b["reconciliation_residuals"]) and len(b["reconciliation_residuals"]) == 13
    assert sorted(w["wall_id"] for w in b["held_walls_carried_held"]) == [
        "2F-W01", "2F-W02", "2F-W03", "2F-W04", "2F-W05", "2F-W06", "2F-W07", "2F-W08", "GF-W22"]


def test_totals_on_v3_0_56(doc):
    t = doc["beside"]["t453_totals_on_v3_0_55"]
    assert t["block_totals"] == {"VERIFIED-NET": {"m2": 86.064, "theoretical_blocks": 1075.8, "lines": 2}}
    assert t["mortar"]["m3"] == pytest.approx(1.269444) and t["mortar_range"] == {}
    g = t["glue_known_part"]
    assert g["VERIFIED-NET"]["kg"] == pytest.approx(20.061) and g["PROVISIONAL-NET"]["kg"] == pytest.approx(23.535)
    assert g["RANGE-NET"]["kg_range"] == pytest.approx([842.06025, 861.32025])
    assert t["glue_project_group"] == "HELD"


def test_hand_checks(doc):
    e = doc["expect"]
    assert e["L-1c53fadb2f92d1f36d4e"] == {A.U_BLACK: pytest.approx(777.05), A.MORTAR: pytest.approx(0.916919)}
    assert e["L-10dd62f66ad05488e63b"][A.U_BLACK] == pytest.approx(298.75)
    assert e["L-a3f88ecda2402f67c500"][A.GLUE] == pytest.approx(23.535)         # (5.59 - 0.36 D-GF-06) x 4.5
    assert doc["faces"]["L-a3f88ecda2402f67c500"]["required"] == [{"opening_id": "D-GF-06", "face_m2": 0.36}]
    assert e["L-adb393d6db51056d343b"] == {A.U_BLACK: "HELD", A.MORTAR: "HELD"}  # 0.15 black: module not stated
