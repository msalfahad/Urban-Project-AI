"""T-206: LEVEL_CHAIN_V1 (merged, unchanged) on the hand fixture villa T206-Q (tests/t206_level_chain_r2/villa_q.py
holds the hand truth). Normal: sunken wet panel with a printed T.O.S., per-footing chains with a printed formation,
m and mm give one result. Adverse: a sunken panel shown only by a hatch stays HELD (never the storey's slab top, never
0); a ceiling under a sunken panel measured from the normal soffit is caught; a printed T.O.S. that contradicts the
printed floor build-up is a CONFLICT and so is every value derived through it; two printed T.O.S. never average; a
printed formation shallower than the 'not less than' note is reported VIOLATED and not adjusted; a missing formation
leaves every footing level HELD while its relation to the formation is still given by the printed layers."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import level_chain_v1 as LC  # noqa: E402
from tests.t206_level_chain_r2 import villa_q  # noqa: E402

sys.path.insert(0, str(ROOT / "research" / "agents_t206"))
import t206_alsenan_check as A  # noqa: E402


def _datum(res, chain, kind):
    return next(r for r in res["datums"] if r["chain_id"] == chain and r["kind"] == kind)


def _link(res, chain, layer):
    return next(r for r in res["links"] if r["chain_id"] == chain and r["layer"] == layer)


def _use(res, uid):
    return next(u for u in res["uses"] if u["use_id"] == uid)


@pytest.fixture(scope="module", params=["m", "mm"])
def res(request):
    p = villa_q.project()
    return LC.check(p if request.param == "m" else villa_q.in_mm(p))


def test_normal_floor_and_sunken_panel(res):
    assert _link(res, "1F", "FLOOR_BUILD_UP")["status"] == "DRAWING-CONFIRMED"
    assert _link(res, "1F", "FLOOR_BUILD_UP")["thickness"] == pytest.approx(0.10)
    assert _datum(res, "1F", "SLAB_SOFFIT")["value"] == pytest.approx(3.50)
    assert _datum(res, "1F", "BEAM_BOTTOM")["value"] == pytest.approx(3.10)
    wet = _link(res, "1F-WA", "WET_FLOOR_BUILD_UP")
    assert wet["status"] == "DRAWING-CONFIRMED" and wet["thickness"] == pytest.approx(0.35)
    assert _datum(res, "1F-WA", "SLAB_SOFFIT")["value"] == pytest.approx(3.25)


def test_ceiling_under_sunken_panel_from_normal_soffit_is_caught(res):
    u = _use(res, "CEIL-UNDER-WA")
    assert u["code"] == "WRONG_REFERENCE" and "+0.250" in u["detail"]


def test_sunken_panel_shown_only_by_hatch_stays_held(res):
    for kind in ("SLAB_TOP", "SLAB_SOFFIT"):
        d = next((r for r in res["datums"] if r["chain_id"] == "1F-WB" and r["kind"] == kind), None)
        assert d is None or (d["value"] is None and d["status"] == "HELD")
    lk = _link(res, "1F-WB", "WET_FLOOR_BUILD_UP")
    assert lk["status"] == "HELD" and lk["thickness"] is None and "1F-WB/SLAB_TOP" in lk["missing"]
    u = _use(res, "WB-TOP")      # the storey's slab top is not the sunken panel's
    assert u["code"] == "WRONG_REFERENCE" and "HELD" in u["detail"]


def test_printed_tos_against_printed_build_up_is_conflict(res):
    lk = _link(res, "2F", "FLOOR_BUILD_UP")
    assert lk["status"] == "CONFLICT" and "0.100" in lk["detail"] and "0.150" in lk["detail"]
    assert any(i["code"] == "LINK_MISMATCH" and i["chain_id"] == "2F" for i in res["issues"])
    soffit = _datum(res, "2F", "SLAB_SOFFIT")           # derived through the mismatching T.O.S
    assert soffit["status"] == "CONFLICT" and soffit["value"] is None
    assert _link(res, "2F", "SLAB_THICKNESS")["status"] == "CONFLICT"


def test_two_printed_tos_never_averaged(res):
    d = _datum(res, "2F-K", "SLAB_TOP")
    assert d["status"] == "CONFLICT" and d["value"] is None
    assert d["values"] == [pytest.approx(7.05), pytest.approx(7.10)]


def test_footing_with_printed_formation(res):
    assert _datum(res, "FTG-A", "BLINDING_TOP")["value"] == pytest.approx(-1.70)
    assert _datum(res, "FTG-A", "FOOTING_BOTTOM")["value"] == pytest.approx(-1.63)
    assert _datum(res, "FTG-A", "FOOTING_TOP")["value"] == pytest.approx(-1.03)
    assert _link(res, "FTG-A", "NECK_RUN")["thickness"] == pytest.approx(1.33)
    assert _link(res, "FTG-A", "EXCAVATION_DEPTH")["thickness"] == pytest.approx(1.80)
    b = next(b for b in res["bounds"] if b["chain_id"] == "FTG-A")
    assert b["result"] == "SATISFIED"
    u = _use(res, "NECK-A-FFL")
    assert u["code"] == "FINISHED_AS_STRUCTURAL" and "+0.300" in u["detail"]
    assert _use(res, "NECK-A-OK")["code"] == "OK"


def test_footing_without_formation_held_never_zero(res):
    for kind in ("FORMATION", "BLINDING_TOP", "FOOTING_BOTTOM", "FOOTING_TOP"):
        d = next((r for r in res["datums"] if r["chain_id"] == "FTG-B" and r["kind"] == kind), None)
        assert d is None or (d["value"] is None and d["status"] == "HELD"), kind
    for layer in ("NECK_RUN", "FOOTING_DEPTH", "UNDERLAY", "BLINDING_THICKNESS", "EXCAVATION_DEPTH"):
        assert _link(res, "FTG-B", layer)["status"] == "HELD"
    b = next(b for b in res["bounds"] if b["chain_id"] == "FTG-B")
    assert b["result"].startswith("OPEN")
    # the relation to the formation is still given by the printed layers (not a level)
    assert A.relative_stack(0.50) == {"blinding_top": 0.10, "footing_bottom": 0.17, "footing_top": 0.67}


def test_formation_shallower_than_the_note_is_violated_not_adjusted(res):
    b = next(b for b in res["bounds"] if b["chain_id"] == "FTG-C")
    assert b["result"] == "VIOLATED"
    assert any(i["code"] == "CONSTRAINT_VIOLATED" and i["chain_id"] == "FTG-C" for i in res["issues"])
    assert _datum(res, "FTG-C", "FORMATION")["value"] == pytest.approx(-1.40)


def test_relative_stack_refuses_missing_or_wrong_units():
    assert A.relative_stack(0.60) == {"blinding_top": 0.10, "footing_bottom": 0.17, "footing_top": 0.77}
    with pytest.raises(ValueError):
        A.relative_stack(None)            # missing footing depth: never defaulted
    with pytest.raises(ValueError):
        A.relative_stack(60)              # 60 (cm) given as metres
    with pytest.raises(ValueError):
        A.relative_stack(0.6, underlay_m=None)
