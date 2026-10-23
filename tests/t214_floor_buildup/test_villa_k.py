"""T-214 FLOOR_BUILDUP_V1 on the hand fixture villa T214-K (not the development villa; two floors, one wet zone, one
sunken panel, one roof). Hand truth (metres):

    GF  FFL +0.45  DRY  printed build-up 0.08                         -> b 0.08, slab top +0.37
    1F  FFL +3.95  DRY  drawn layer, vector 0.070 / current issue 0.066 -> b 0.07, slab top +3.88 (|0.004| <= 0.010)
                   WET  only the DRY cut's layer offered                -> HELD (never 0, never the dry layer)
                   SUNKEN printed base 0.07 + printed drop 0.15        -> b 0.22, slab top +3.73
    ROOF finished +7.45: constant drawn layer 0.05                      -> HELD (CONSTANT_LAYER_VS_FALLS)
         printed slab top +7.30                                         -> b 0.15
    Condition 'b <= 0.20' on 1F DRY: drawing PROVEN; owner wall-height allowance 0.10: NOT PROVEN (ALLOWANCE_AS_DATUM).

Adverse: a finished level offered as the structural top; a finish allowance used as a datum; vector without a
current-issue check; vector vs scan disagree; printed vs drawn disagree; sunken panel without its drop; a structural
datum given as the floor's FFL; mm vs m.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t214"))
import floor_buildup_v1 as FB  # noqa: E402

R = "fixture T214-K"
ALLOW = {"rule": "owner height rule", "scope": "WALL_HEIGHT_ALLOWANCE", "lo": 0.10, "ref": R}
BED = {"rule": "owner bed rule", "scope": "MORTAR_BED", "lo": 0.03, "hi": 0.04, "parts_missing": ["tile"], "ref": R}


def villa():
    return {"units": "m", "floors": [
        {"floor_id": "GF", "ffl": {"kind": "FFL", "value": 0.45, "ref": R}, "zones": [
            {"zone_id": "GF-DRY", "type": "DRY",
             "evidence": [{"source": "PRINTED_THICKNESS", "thickness": 0.08, "ref": R + " detail 3"}]}]},
        {"floor_id": "1F", "ffl": {"kind": "FFL", "value": 3.95, "ref": R}, "zones": [
            {"zone_id": "1F-DRY", "type": "DRY", "owner_items": [ALLOW, BED], "evidence": [
                {"source": "DRAWN_VECTOR", "thickness": 0.070, "cut_zone_type": "DRY", "ref": R + " section 1"},
                {"source": "DRAWN_CURRENT_ISSUE", "thickness": 0.066, "cut_zone_type": "DRY", "ref": R + " scan"}]},
            {"zone_id": "1F-WET", "type": "WET", "evidence": [
                {"source": "DRAWN_VECTOR", "thickness": 0.070, "cut_zone_type": "DRY", "ref": R + " section 1"},
                {"source": "DRAWN_CURRENT_ISSUE", "thickness": 0.066, "cut_zone_type": "DRY", "ref": R + " scan"}]},
            {"zone_id": "1F-SUNKEN", "type": "SUNKEN", "sunken_drop": 0.15,
             "evidence": [{"source": "PRINTED_THICKNESS", "thickness": 0.07, "ref": R + " wet detail"}]}]},
        {"floor_id": "ROOF", "ffl": {"kind": "FINISHED_ROOF", "value": 7.45, "ref": R}, "zones": [
            {"zone_id": "ROOF-A", "type": "ROOF", "printed_falls": True, "evidence": [
                {"source": "DRAWN_VECTOR", "thickness": 0.05, "cut_zone_type": "ROOF", "ref": R + " section 1"},
                {"source": "DRAWN_CURRENT_ISSUE", "thickness": 0.05, "cut_zone_type": "ROOF", "ref": R + " scan"}]},
            {"zone_id": "ROOF-B", "type": "ROOF", "evidence": [
                {"source": "PRINTED_TOP", "kind": "SLAB_TOP", "value": 7.30, "ref": R + " roof detail"}]}]}],
        "conditions": [
            {"condition_id": "C-OK", "floor_id": "1F", "zone_id": "1F-DRY", "max_build_up": 0.20, "ref": R},
            {"condition_id": "C-TIGHT", "floor_id": "1F", "zone_id": "1F-DRY", "max_build_up": 0.05, "ref": R},
            {"condition_id": "C-WET", "floor_id": "1F", "zone_id": "1F-WET", "max_build_up": 0.20, "ref": R}]}


def zone(res, f, z):
    return res["floors"][f]["zones"][z]


def cond(res, c):
    return next(x for x in res["conditions"] if x["condition_id"] == c)


@pytest.fixture()
def res():
    return FB.evaluate(villa())


# ------------------------------------------------------------------------------------------------------------ normal
def test_printed_build_up(res):
    z = zone(res, "GF", "GF-DRY")
    assert z["drawing"]["status"] == "DRAWING-CONFIRMED" and z["drawing"]["b"] == pytest.approx(0.08)
    assert z["slab_top_drawing"] == pytest.approx(0.37)


def test_drawn_layer_checked_on_current_issue(res):
    z = zone(res, "1F", "1F-DRY")
    assert z["drawing"]["status"] == "DRAWING-CONFIRMED" and z["drawing"]["b"] == pytest.approx(0.07)
    assert FB.structural_top(res["floors"]["1F"], "1F-DRY") == pytest.approx(3.88)


def test_sunken_panel_with_printed_drop(res):
    z = zone(res, "1F", "1F-SUNKEN")
    assert z["drawing"]["b"] == pytest.approx(0.22) and z["slab_top_drawing"] == pytest.approx(3.73)


def test_roof_with_printed_slab_top(res):
    assert zone(res, "ROOF", "ROOF-B")["drawing"]["b"] == pytest.approx(0.15)


def test_conditions_per_basis(res):
    assert cond(res, "C-OK")["DRAWING"].startswith("PROVEN")
    assert cond(res, "C-TIGHT")["DRAWING"].startswith("VIOLATED")
    assert cond(res, "C-WET")["DRAWING"].startswith("NOT PROVEN")
    assert "ALLOWANCE_AS_DATUM" in cond(res, "C-OK")["OWNER_MANUAL"]


def test_owner_method_beside_with_residual(res):
    om = {o["rule"]: o for o in zone(res, "1F", "1F-DRY")["owner_manual"]}
    assert om["owner height rule"]["usable_as_datum"] is False
    assert om["owner height rule"]["residual_drawn_minus_owner"] == [pytest.approx(-0.03)] * 2
    assert om["owner bed rule"]["partial"] is True
    assert om["owner bed rule"]["residual_drawn_minus_owner"] == [pytest.approx(0.03), pytest.approx(0.04)]
    assert "tile" in om["owner bed rule"]["residual_named"]


def test_mm_equals_m():
    v = villa()
    mm = copy.deepcopy(v)
    mm["units"] = "mm"
    for f in mm["floors"]:
        f["ffl"]["value"] *= 1000
        for z in f["zones"]:
            if "sunken_drop" in z:
                z["sunken_drop"] *= 1000
            for e in z.get("evidence", []):
                for key in ("thickness", "value"):
                    if key in e:
                        e[key] *= 1000
            z["owner_items"] = [dict(o, lo=o["lo"] * 1000, **({"hi": o["hi"] * 1000} if "hi" in o else {}))
                                for o in z.get("owner_items", [])]
    for c in mm["conditions"]:
        c["max_build_up"] *= 1000
    a, b = FB.evaluate(v), FB.evaluate(mm)
    for f in a["floors"]:
        for z in a["floors"][f]["zones"]:
            assert a["floors"][f]["zones"][z]["drawing"]["b"] == pytest.approx(b["floors"][f]["zones"][z]["drawing"]["b"])
    assert [c["DRAWING"] for c in a["conditions"]] == [c["DRAWING"] for c in b["conditions"]]


# ----------------------------------------------------------------------------------------------------------- adverse
def test_finished_level_offered_as_structural_top_refused():
    v = villa()
    v["floors"][2]["zones"][1]["evidence"][0]["kind"] = "FINISHED_ROOF"
    with pytest.raises(ValueError, match="FINISHED_AS_STRUCTURAL"):
        FB.evaluate(v)


def test_finish_allowance_used_as_datum_refused(res):
    with pytest.raises(ValueError, match="ALLOWANCE_AS_DATUM"):
        FB.structural_top(res["floors"]["1F"], "1F-DRY", basis="OWNER_MANUAL")


def test_owner_level_datum_is_usable_and_labelled():
    v = villa()
    v["floors"][1]["zones"][0]["owner_items"].append(
        {"rule": "owner datum rule", "scope": "LEVEL_DATUM", "lo": 0.10, "ref": R})
    r = FB.evaluate(v)
    assert FB.structural_top(r["floors"]["1F"], "1F-DRY", basis="OWNER_MANUAL") == [pytest.approx(3.85)] * 2
    assert cond(r, "C-OK")["OWNER_MANUAL"] == "PROVEN (ASSUMED — OWNER-APPROVED)"


def test_dry_layer_never_carried_to_wet_zone(res):
    z = zone(res, "1F", "1F-WET")
    assert z["drawing"]["status"] == "HELD" and z["drawing"]["b"] is None
    assert "slab_top_drawing" not in z
    with pytest.raises(ValueError, match="never the FFL"):
        FB.structural_top(res["floors"]["1F"], "1F-WET")


def test_constant_layer_on_roof_refused(res):
    z = zone(res, "ROOF", "ROOF-A")
    assert z["drawing"]["status"] == "HELD" and z["drawing"]["b"] is None
    assert any("CONSTANT_LAYER_VS_FALLS" in n for n in z["drawing"]["notes"])


def test_vector_without_current_issue_check_held():
    v = villa()
    v["floors"][1]["zones"][0]["evidence"].pop(1)
    z = zone(FB.evaluate(v), "1F", "1F-DRY")
    assert z["drawing"]["status"] == "HELD" and z["drawing"]["b"] is None
    assert any("REVISION_NOT_CHECKED" in n for n in z["drawing"]["notes"])


def test_vector_vs_scan_disagree_conflict():
    v = villa()
    v["floors"][1]["zones"][0]["evidence"][1]["thickness"] = 0.085
    z = zone(FB.evaluate(v), "1F", "1F-DRY")
    assert z["drawing"]["status"] == "CONFLICT" and z["drawing"]["b"] is None


def test_printed_vs_drawn_conflict_never_averaged():
    v = villa()
    v["floors"][1]["zones"][0]["evidence"].append({"source": "PRINTED_THICKNESS", "thickness": 0.10, "ref": R})
    z = zone(FB.evaluate(v), "1F", "1F-DRY")
    assert z["drawing"]["status"] == "CONFLICT" and z["drawing"]["values"] == [0.07, 0.1]


def test_sunken_without_drop_held():
    v = villa()
    v["floors"][1]["zones"][2]["sunken_drop"] = None
    z = zone(FB.evaluate(v), "1F", "1F-SUNKEN")
    assert z["drawing"]["status"] == "HELD" and z["drawing"]["basis"] == "SUNKEN_DROP_NOT_PRINTED"


def test_floor_datum_must_be_finished():
    v = villa()
    v["floors"][0]["ffl"]["kind"] = "SLAB_TOP"
    with pytest.raises(ValueError, match="FINISHED level"):
        FB.evaluate(v)


def test_structural_top_above_ffl_refused():
    v = villa()
    v["floors"][2]["zones"][1]["evidence"][0]["value"] = 7.60
    with pytest.raises(ValueError, match="above the FFL"):
        FB.evaluate(v)


def test_missing_reference_refused():
    v = villa()
    v["floors"][0]["zones"][0]["evidence"][0]["ref"] = ""
    with pytest.raises(ValueError, match="source reference"):
        FB.evaluate(v)
