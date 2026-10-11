"""M3 WP7 / WP8: every concrete component has one reinforcement state and missing steel is counted (never 0 kg);
blinding is measured from the footings and beams the plans give; every other family gets a precise coverage record
(an absent label is never an absent structure)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import family_coverage as FC            # noqa: E402
from engine.source import generic_route as GR              # noqa: E402
from engine.source import provisional_estimate as PE       # noqa: E402
from tools import urban_boq_m2 as CLI                       # noqa: E402
from tools import urban_intake as UI                       # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_m3_footings as FT                              # noqa: E402


def _conv(blinding=True):
    gen = json.loads((ROOT / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json").read_text())
    prof = {"profile": "T", "conventions": [
        {"id": "BLINDING_THICKNESS_M", "title": "t", "kind": "number", "unit": "m", "base": 0.1, "low": 0.1,
         "high": 0.1, "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"}] if blinding else []}
    return GR.merge_conventions(gen, prof)


@pytest.fixture(scope="module")
def footings(tmp_path_factory):
    return GR.detect(UI.read(FT._plan(tmp_path_factory.mktemp("bl") / "f.dxf")))


def test_blinding_under_every_footing(footings):
    conv = _conv()
    items, reg, risk = GR.items_from(footings, conv, {})
    PE.check(items, conv)
    it = next(i for i in items if i["family"] == "PLAIN_CONCRETE")
    dims = [(1.5, 1.3), (1.0, 1.0), (2.4, 2.2), (2.6, 1.2), (2.0, 2.0), (1.8, 1.5)]   # F1 F3 FF F4 F2, F6 (larger)
    area = lambda p: sum((a + 2 * p) * (b + 2 * p) for a, b in dims)                  # noqa: E731
    assert (it["low"], it["base"], it["high"]) == pytest.approx((area(0.05) * 0.1, area(0.10) * 0.1,
                                                                 area(0.15) * 0.1))
    assert it["category"] == "PROVISIONAL" and it["dimensions"]["members"] == 6
    st = {r["COMPONENT_ID"]: r["REBAR_STATE"] for r in reg}
    assert st[it["component_id"]] == "EXPLICIT_NONE"


def test_blinding_without_a_printed_thickness_is_unresolved(footings):
    conv = _conv(blinding=False)
    items, reg, risk = GR.items_from(footings, conv, {})
    it = next(i for i in items if i["family"] == "PLAIN_CONCRETE")
    assert it["category"] == "UNRESOLVED" and it["blocker"] == "BLINDING_THICKNESS_NOT_PRINTED" and it["exposure_high"]


def test_every_concrete_component_has_a_state_and_missing_steel_is_counted():
    common = dict(trade="CONCRETE", storey="GF", source="test", support="CONVENTION_ONLY", confidence="LOW",
                  formula="x", assumptions=["A"], category="PROVISIONAL", low=1.0, base=1.0, high=1.0)
    items = [PE.item(item_id="a", component_id="BEAMS:GF:1", family="BEAMS", **common),
             PE.item(item_id="b", component_id="BEAMS:GF:2", family="BEAMS", **common),
             PE.item(item_id="c", component_id="SLABS:GF:3", family="SLABS", **common),
             PE.item(item_id="d", component_id="SLABS:GF:3", trade="REINFORCEMENT", family="SLABS", storey="GF",
                     category="UNRESOLVED", source="test", support="NO_GEOMETRY", confidence="LOW", blocker="X")]
    reg = [{"COMPONENT_ID": "BEAMS:GF:1", "FAMILY": "BEAMS", "STOREY": "GF", "REBAR_STATE": "PROVISIONAL_MODEL",
            "REASON": "bars", "PROVISIONAL_KG_BASE": 12.0},
           {"COMPONENT_ID": "SLABS:GF:3", "FAMILY": "SLABS", "STOREY": "GF", "REBAR_STATE": "PARTIAL_MISSING",
            "REASON": "part", "PROVISIONAL_KG_BASE": 3.0}]
    rc = GR.rebar_completeness(items, reg)
    st = {r["COMPONENT_ID"]: r for r in rc["rows"]}
    assert st["BEAMS:GF:2"]["REBAR_STATE"] == "MISSING_DATA" and st["BEAMS:GF:2"]["PROVISIONAL_KG_BASE"] is None
    assert st["SLABS:GF:3"]["UNRESOLVED_STEEL_ITEMS"] == 1 and rc["missing_steel_components"] == 2
    lines = CLI.missing_steel_lines(rc)
    assert len(lines) == 2 and all(b["UNIT"] == "-" and "not zero" in b["DESCRIPTION"] for b in lines)
    assert all(b.get("PLANNING_BASE") is None for b in lines)                         # never a 0 kg quantity
    assert "Reinforcement not quantified" in CLI.missing_steel_html(rc)


def test_family_coverage_states(footings):
    conv = _conv()
    items, reg, risk = GR.items_from(footings, conv, {})
    cov = {c["FAMILY"]: c for c in FC.coverage(footings, items, risk, GR.scope_scan(footings))}
    assert set(cov) == set(FC.FAMILIES)
    assert cov["PLAIN_CONCRETE"]["STATE"] == "QUANTIFIED"
    assert cov["LIFT"]["STATE"] == "NO_EVIDENCE_FOUND" and "confirm absent" in cov["LIFT"]["REASON"]
    assert cov["LIFT"]["NEEDED"]
    lines = CLI.not_detected_lines(list(cov.values()))
    assert len(lines) == len(FC.FAMILIES) and {b["EVIDENCE"] for b in lines} <= {
        "QUANTIFIED", "PARTLY_QUANTIFIED", "COUNTED_IN_PARENT", "DETECTED_NOT_QUANTIFIED", "NO_EVIDENCE_FOUND"}
