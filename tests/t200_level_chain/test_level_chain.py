"""T-200 LEVEL_CHAIN_V1 on the hand fixture villa T200-R (tests/t200_level_chain/villa_r.py holds the hand truth).

Normal: every datum and link of the fixture equals the hand value; units in mm give the same result.
Adverse: two sheets disagreeing on one datum -> CONFLICT (never an average); a printed layer contradicting two printed
datums -> LINK_MISMATCH; a finished level used as a structural one -> FINISHED_AS_STRUCTURAL; a sill measured from the
ground line -> WRONG_REFERENCE; a missing datum -> HELD with the missing item named, value None (never 0); a limit
('not less than') stays a limit; an owner manual layer is reported beside, never used; a zero system without evidence is
never combined; millimetres given as metres, negative layers, missing refs and unknown kinds are refused."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import level_chain_v1 as LC  # noqa: E402
from tests.t200_level_chain import villa_r  # noqa: E402


def _datum(res, chain, kind):
    return next(r for r in res["datums"] if r["chain_id"] == chain and r["kind"] == kind)


def _link(res, chain, layer):
    return next(r for r in res["links"] if r["chain_id"] == chain and r["layer"] == layer)


def _use(res, uid):
    return next(r for r in res["uses"] if r["use_id"] == uid)


HAND = {("GF-A", "GB_TOP"): 0.50, ("GF-A", "GB_BOTTOM"): -0.10, ("GF-A", "FOOTING_TOP"): -0.60,
        ("GF-A", "BLINDING_TOP"): -1.25, ("GF-A", "FORMATION"): -1.35, ("1F", "SLAB_SOFFIT"): 3.80,
        ("1F", "BEAM_BOTTOM"): 3.40, ("1F-WET", "SLAB_SOFFIT"): 3.50, ("BASIN", "POOL_BASE_UNDERSIDE"): -1.38,
        ("BASIN", "BLINDING_TOP"): -1.38, ("BASIN", "FORMATION"): -1.48}
HAND_LINKS = {("GF-A", "FLOOR_BUILD_UP"): 0.10, ("GF-A", "NECK_RUN"): 1.10, ("GF-A", "EXCAVATION_DEPTH"): 1.35,
              ("1F", "FLOOR_BUILD_UP"): 0.10, ("1F-WET", "FLOOR_BUILD_UP"): 0.38, ("RF", "PARAPET_HEIGHT"): 1.00,
              ("BASIN", "FINISHED_DEPTH"): 1.40, ("BASIN", "FLOOR_BUILD_UP"): 0.08, ("BASIN", "RC_WALL_HEIGHT"): 1.48,
              ("BASIN", "EXCAVATION_DEPTH"): 1.48}


@pytest.mark.parametrize("units", ["m", "mm"])
def test_hand_datums_and_links(units):
    p = villa_r.project() if units == "m" else villa_r.in_mm(villa_r.project())
    res = LC.check(p)
    for (c, kind), v in HAND.items():
        assert _datum(res, c, kind)["value"] == pytest.approx(v, abs=1e-6), (c, kind)
        assert _datum(res, c, kind)["status"] == "DRAWING-CONFIRMED"
    for (c, layer), v in HAND_LINKS.items():
        row = _link(res, c, layer)
        assert row["thickness"] == pytest.approx(v, abs=1e-6), (c, layer)
        assert row["status"] == "DRAWING-CONFIRMED", (c, layer, row)
    assert _datum(res, "GF-A", "FORMATION")["basis"].startswith("DERIVED")
    assert [b["result"] for b in res["bounds"]] == ["SATISFIED"]


def test_missing_founding_level_is_held_never_zero():
    res = LC.check(villa_r.project())
    for kind in ("FOOTING_TOP", "FOOTING_BOTTOM", "BLINDING_TOP", "FORMATION"):
        assert not any(r["chain_id"] == "GF-B" and r["kind"] == kind and r["value"] is not None for r in res["datums"])
    neck = _link(res, "GF-B", "NECK_RUN")
    assert neck["status"] == "HELD" and neck["thickness"] is None and "GF-B/FOOTING_TOP" in neck["missing"]
    exc = _link(res, "GF-B", "EXCAVATION_DEPTH")
    assert exc["status"] == "HELD" and exc["thickness"] is None
    assert _use(res, "U-NECK-B")["code"] == "NEEDS_HELD"
    # the roof: build-up not printed -> slab top, soffit and beam bottom HELD; the owner manual 0.10 is beside, unused
    assert _link(res, "RF", "ROOF_BUILD_UP")["status"] == "HELD"
    assert _link(res, "RF", "SLAB_THICKNESS")["status"] == "HELD"
    assert res["owner_manual_layers"][0]["thickness"] == pytest.approx(0.10)
    assert not any(r["chain_id"] == "RF" and r["kind"] == "SLAB_TOP" and r["value"] is not None
                   for r in res["datums"])


def test_uses():
    res = LC.check(villa_r.project())
    u = _use(res, "U-BASIN-WALL")
    assert u["code"] == "FINISHED_AS_STRUCTURAL" and "+0.080" in u["detail"]
    u = _use(res, "U-SILL-W5")
    assert u["code"] == "WRONG_REFERENCE" and "-0.600" in u["detail"]
    assert _use(res, "U-NECK-A-FFL")["code"] == "FINISHED_AS_STRUCTURAL"
    assert _use(res, "U-NECK-A-CONV")["code"] == "VALUE_NOT_FROM_DRAWINGS"
    assert _use(res, "U-NECK-A-OK")["code"] == "OK"
    u = _use(res, "U-WET-FILL")
    assert u["code"] == "WRONG_REFERENCE" and "+0.300" in u["detail"]
    u = _use(res, "U-ROOF-COL")
    assert u["code"] == "FINISHED_AS_STRUCTURAL" and "HELD" in u["detail"] and "not proven" in u["sensitivity"]


def test_two_sheets_disagree_conflict_not_average():
    p = villa_r.project()
    p["datums"].append({"chain_id": "1F", "kind": "FFL", "value": 4.15, "ref": "A-08 elevation", "status":
                        "DRAWING-CONFIRMED"})
    res = LC.check(p)
    row = _datum(res, "1F", "FFL")
    assert row["status"] == "CONFLICT" and row["value"] is None and row["values"] == [4.1, 4.15]
    assert _link(res, "1F", "FLOOR_BUILD_UP")["status"] == "CONFLICT"
    # the structural side is untouched by the architectural conflict
    assert _link(res, "1F", "SLAB_THICKNESS")["status"] == "DRAWING-CONFIRMED"
    assert any(i["code"] == "CONFLICT" and i["chain_id"] == "1F" for i in res["issues"])


def test_layer_contradicting_datums_is_a_mismatch():
    p = villa_r.project()
    for ly in p["layers"]:
        if ly["chain_id"] == "GF-A" and ly["layer"] == "FLOOR_BUILD_UP":
            ly["thickness"] = 0.12
    res = LC.check(p)
    row = _link(res, "GF-A", "FLOOR_BUILD_UP")
    assert row["status"] == "CONFLICT" and "0.100" in row["detail"] and "0.120" in row["detail"]
    assert any(i["code"] == "LINK_MISMATCH" for i in res["issues"])


def test_limit_stays_a_limit_and_can_be_violated():
    p = villa_r.project()
    for ly in p["layers"]:
        if ly["chain_id"] == "GF-A" and ly["layer"] == "FOOTING_DEPTH":
            ly["thickness"] = 0.60
    for d in p["datums"]:
        if d["chain_id"] == "GF-A" and d["kind"] == "FOOTING_BOTTOM":
            d["value"] = -1.10          # formation -1.25: above the 'not less than 1.30' limit
    res = LC.check(p)
    assert [b["result"] for b in res["bounds"]] == ["VIOLATED"]
    assert any(i["code"] == "CONSTRAINT_VIOLATED" for i in res["issues"])
    # without a founding level the limit is never turned into a formation level
    q = villa_r.project()
    q["datums"] = [d for d in q["datums"] if not (d["chain_id"] == "GF-A" and d["kind"] == "FOOTING_BOTTOM")]
    res = LC.check(q)
    assert res["bounds"][0]["result"].startswith("OPEN")
    assert not any(r["chain_id"] == "GF-A" and r["kind"] == "FORMATION" and r["value"] is not None
                   for r in res["datums"])


def test_zero_relation_from_marks():
    arch = [{"text": "+0.60", "value": 0.60, "x": 100.0, "y": 50.0, "ref": "a1"},
            {"text": "+0.60", "value": 0.60, "x": 900.0, "y": 50.0, "ref": "a2"},
            {"text": "+0.15", "value": 0.15, "x": 100.0, "y": 700.0, "ref": "a3"},
            {"text": "+-0.00", "value": 0.0, "x": 0.0, "y": 0.0, "ref": "a4"}]
    # the same marks on the structural sheet, moved by (+5000, -2000): one zero, offset 0
    same = [dict(m, x=m["x"] + 5000, y=m["y"] - 2000, ref="s" + m["ref"]) for m in arch]
    r = LC.zero_relation_from_marks(arch, same, "m")
    assert r["status"] == "DRAWING-CONFIRMED" and r["matched"] == 4 and r["offset"] == 0.0
    # a structural set with its own zero at the GF floor: texts differ, nothing coincides -> UNKNOWN, never assumed
    own = [dict(m, text="%+.2f" % (m["value"] - 0.60), value=m["value"] - 0.60, x=m["x"] + 5000) for m in arch]
    assert LC.zero_relation_from_marks(arch, own, "m")["status"] == "UNKNOWN"
    # coincident texts but one value disagreeing -> CONFLICT
    bad = copy.deepcopy(same)
    bad[2]["value"] = 0.25
    assert LC.zero_relation_from_marks(arch, bad, "m")["status"] == "CONFLICT"


def test_zero_system_without_relation_is_not_combined():
    p = villa_r.project()
    p["datums"].append({"chain_id": "1F", "kind": "SLAB_TOP", "value": 3.50, "system": "STRUCT", "ref": "S-04 own zero",
                        "status": "DRAWING-CONFIRMED"})
    res = LC.check(p)
    assert any(i["code"] == "ZERO_RELATION_UNKNOWN" for i in res["issues"])
    assert _datum(res, "1F", "SLAB_TOP")["value"] == pytest.approx(4.00)      # not 3.50, not a conflict
    # with an established relation (STRUCT zero = ARCH +0.50) the value is combined and agrees
    p["zero_relations"] = [{"system": "STRUCT", "offset": 0.50, "status": "DRAWING-CONFIRMED", "ref": "marks fit"}]
    res = LC.check(p)
    assert _datum(res, "1F", "SLAB_TOP")["status"] == "DRAWING-CONFIRMED"
    assert not any(i["code"] in ("ZERO_RELATION_UNKNOWN", "CONFLICT") for i in res["issues"])


def test_margin_sensitivity():
    p = villa_r.project()
    p["datums"].append({"chain_id": "RF", "kind": "SLAB_TOP", "value": 7.62, "ref": "S-05 T.O.S", "status":
                        "DRAWING-CONFIRMED"})
    res = LC.check(p)
    assert _use(res, "U-ROOF-COL")["sensitivity"].startswith("difference inside")
    p["datums"][-1]["value"] = 7.50
    res = LC.check(p)
    assert _use(res, "U-ROOF-COL")["sensitivity"].startswith("difference outside")


@pytest.mark.parametrize("mutate, msg", [
    (lambda p: p.update(units=None), "units"),
    (lambda p: p["datums"][0].update(value=4100.0), "millimetres"),
    (lambda p: p["layers"][0].update(thickness=-0.1), "negative"),
    (lambda p: p["datums"][0].update(ref=""), "ref"),
    (lambda p: p["datums"][0].update(kind="TOP_OF_SOMETHING"), "kind"),
    (lambda p: p["datums"][0].update(status="PROBABLY"), "status"),
    (lambda p: p["datums"][0].update(chain_id="NOPE"), "unknown chain"),
    (lambda p: p["layers"][0].update(layer="BEAM_DEPTH"), "no link"),
    (lambda p: p["chains"][0].update(family="TOWER"), "family"),
    (lambda p: p["uses"][0].update(used={}), "used"),
])
def test_bad_input_refused(mutate, msg):
    p = villa_r.project()
    mutate(p)
    with pytest.raises(ValueError, match=msg):
        LC.check(p)


def test_module_is_stdlib_only_and_unwired():
    src = (ROOT / "engine/source/level_chain_v1.py").read_text(encoding="utf-8")
    imports = [ln for ln in src.splitlines() if ln.startswith(("import ", "from "))]
    assert imports == ["from __future__ import annotations"]
    hits = [p for p in (ROOT / "engine").rglob("*.py") if p.name != "level_chain_v1.py"
            and "level_chain_v1" in p.read_text(encoding="utf-8", errors="ignore")]
    assert hits == []


def test_value_derived_through_a_mismatching_link_is_not_kept():
    """Adverse (pool-like basin): an architectural cut prints the base underside -1.18 (0.15 thick) while the
    structural detail prints 0.35: the link is a CONFLICT, and the blinding top / formation derived through the disputed
    underside are CONFLICT too (never -1.28 / -1.38 kept as if established); the rim -> base top wall stays confirmed."""
    p = villa_r.project()
    p["datums"].append({"chain_id": "BASIN", "kind": "POOL_BASE_UNDERSIDE", "value": -1.18, "ref": "A-07 cut base",
                        "status": "DRAWING-CONFIRMED"})
    res = LC.check(p)
    assert _link(res, "BASIN", "BASE_THICKNESS")["status"] == "CONFLICT"
    for kind in ("BLINDING_TOP", "FORMATION"):
        row = _datum(res, "BASIN", kind)
        assert row["status"] == "CONFLICT" and row["value"] is None
    assert _link(res, "BASIN", "EXCAVATION_DEPTH")["status"] == "CONFLICT"
    assert _link(res, "BASIN", "RC_WALL_HEIGHT")["thickness"] == pytest.approx(1.48)
    assert _link(res, "BASIN", "RC_WALL_HEIGHT")["status"] == "DRAWING-CONFIRMED"
