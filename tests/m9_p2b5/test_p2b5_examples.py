"""Phase 2B-5 (ARCH_TAKEOFF_V2.6): the ten worked examples through the verification chain. For each example the
hand derivation (typed literals) is compared with the engine's figures, and the engine's own cutting plan is rebuilt
piece by piece by the independent reference calculator: the plan must be physically complete (every surface covered
on a 10 mm grid, every piece cut from material that holds it, the material balance closed) and the reference's
quantities must equal both the engine's and the hand's. Every junction alternative the engine reports is rebuilt the
same way."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "m9_p2b4"))

import construct_reference as CR                              # noqa: E402
import install_cases as IC                                    # noqa: E402
import install_engine as IE                                   # noqa: E402
import install_reference as IR                                # noqa: E402

TOL = 0.0005                                                  # half a millimetre / half a cm2 (rounding only)
_AREAS = {}


def _area(ex):
    if ex["id"] not in _AREAS:
        _AREAS[ex["id"]] = IE.area(ex["room"], room_id=ex["id"])
    return _AREAS[ex["id"]]


def _same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= TOL
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return all(_same(v, b.get(k)) for k, v in a.items())
    return a == b


def _diff(expected, got, keys=None):
    return {k: (v, got.get(k)) for k, v in expected.items() if (keys is None or k in keys) and not _same(v, got.get(k))}


@pytest.mark.parametrize("ex", IC.SINGLE, ids=[x["id"] for x in IC.SINGLE])
def test_hand_derivation_equals_the_engine(ex):
    eng = IE.figures(_area(ex))
    assert _diff(ex["expected"], eng) == {}


@pytest.mark.parametrize("ex", IC.SINGLE, ids=[x["id"] for x in IC.SINGLE])
def test_the_reference_rebuilds_the_engine_plan_and_agrees(ex):
    a = _area(ex)
    ref = IR.summary(IR.verify_A(ex["room"], IR.URBAN, IE.plan(a)))   # raises when the plan is not complete
    assert _diff(ex["expected"], ref, keys=set(ref)) == {}, "hand vs reference"
    eng = IE.figures(a)
    assert {k: (eng[k], ref[k]) for k in ref if k in eng and not _same(eng[k], ref[k])} == {}, "engine vs reference"


@pytest.mark.parametrize("ex", IC.SINGLE, ids=[x["id"] for x in IC.SINGLE])
def test_the_open_details_are_flagged(ex):
    assert sorted(IE.figures(_area(ex))["flags"]) == sorted(ex["flags"])


@pytest.mark.parametrize("ex", IC.SINGLE, ids=[x["id"] for x in IC.SINGLE])
def test_every_junction_alternative_is_a_complete_plan(ex):
    a = _area(ex)
    jun = a["v26"]["junction"]
    assert jun["state"] == "UNRESOLVED" and jun["alternatives"][0]["flange_m"] == 0.1
    n = 0
    for alt in jun["alternatives"]:
        if not alt.get("trace"):
            continue
        pl = IE.plan(a, alt["trace"])
        ref = IR.summary(IR.verify_A(ex["room"], dict(IR.URBAN, j=pl["j"]), pl))
        assert (ref["rolls"], ref["consumed_m2"], ref["installed_m2"]) == \
            (alt["rolls"], alt["consumed_m2"], alt["installed_m2"])
        assert pl["j"] == round(alt["flange_m"] * 1000)
        n += 1
    assert n >= 1
    assert ("JUNCTION_CHANGES_ROLL_COUNT" in a["v26"]["flags"]) == (len(set(x["rolls"] for x in
                                                                           jun["alternatives"])) > 1)


@pytest.mark.parametrize("ex", [x for x in IC.SINGLE if isinstance(x["expected"]["fold"], dict)],
                         ids=[x["id"] for x in IC.SINGLE if isinstance(x["expected"]["fold"], dict)])
def test_the_continuous_fold_equals_the_reference(ex):
    """method B for the rectangular rooms: the engine's figures against the Phase 2B-4 planner (both readings agree
    on the selected direction for these rooms)."""
    room = {k: ex["room"][k] for k in ("poly", "doors")}
    room["pipes"] = []
    _, plan = CR.plan_B(room, CR.URBAN, "X", CR.FEWEST_JOINTS, splice=False)
    _, plan_y = CR.plan_B(room, CR.URBAN, "Y", CR.FEWEST_JOINTS, splice=False)
    best = min((CR.summary(CR.verify(room, CR.URBAN, p)) for p in (plan, plan_y)),
               key=lambda r: (r["rolls"], r["seams"], r["consumed_m2"]))
    f = ex["expected"]["fold"]
    assert (best["rolls"], best["consumed_m2"], best["installed_m2"], best["seams"]) == \
        (f["rolls"], f["consumed_m2"], f["installed_m2"], f["seams"])
    assert best["corner_excess_m2"] == f["corner_excess_m2"]


def _built(ex):
    out = []
    for rid, room in ex["areas"].items():
        out.append(IE.area(IC.BY_ID[room]["room"] if isinstance(room, str) else room, room_id=rid))
    return out


def test_shared_inventory_of_one_system():
    ex = IC.IX09
    built = _built(ex)
    plans = IE.shared(built)
    assert len(plans) == 1
    p = plans[0]
    e = ex["expected"]
    assert (p["rolls"], p["rolls_if_each_area_alone"], p["consumed_m2"], p["gross_roll_area_m2"],
            p["untouched_roll_tails_m2"]) == (e["rolls_shared"], e["rolls_alone"], e["consumed_m2"], e["gross_m2"],
                                              e["untouched_m2"])
    pieces = [x for r in p["cutting_plan"] for x in r["pieces"]]
    assert len(pieces) == e["pieces"]
    assert all(r["cut_m"] <= 10.0 + 1e-9 for r in p["cutting_plan"])
    cut = {}
    for a in built:                                           # every shared piece names its area's own cut
        for r in a["layout"]["layout"]["rolls"]:
            for k, s in enumerate(r["segments"]):
                cut[f"{a['room_id']}:R{r['roll']}-{k + 1}"] = s["length_m"]
    assert sorted(x["cut_id"] for x in pieces) == sorted(cut)
    assert all(cut[x["cut_id"]] == x["length_m"] for x in pieces)
    groups = {"WET": {a["room_id"]: [round(s["length_m"] * 1000) for r in a["layout"]["layout"]["rolls"]
                                     for s in r["segments"]] for a in built}}
    assert IR.pack_shared(groups, 10000) == {"WET": e["rolls_shared"]}


def test_two_systems_never_share_a_roll():
    ex = IC.IX10
    built = _built(ex)
    plans = IE.shared(built)
    e = ex["expected"]
    assert len(plans) == e["systems"]
    scope = {a["system"]["system_id"]: a["scope"] for a in built}
    assert {scope[p["system_id"]]: p["rolls"] for p in plans} == e["rolls_by_scope"]
    assert sum(p["rolls"] for p in plans) == e["rolls_total"]
    for p in plans:
        rooms = {x["room_id"] for r in p["cutting_plan"] for x in r["pieces"]}
        assert len({scope[p["system_id"]]} | {a["scope"] for a in built if a["room_id"] in rooms}) == 1
    lens = [round(s["length_m"] * 1000) for a in built for r in a["layout"]["layout"]["rolls"] for s in r["segments"]]
    assert len(CR.pack(lens, 10000)) == e["rolls_if_mixed"]        # mixing would save a roll: it is not done
    groups = {}
    for a in built:
        groups.setdefault(a["scope"], {})[a["room_id"]] = [round(s["length_m"] * 1000)
                                                            for r in a["layout"]["layout"]["rolls"]
                                                            for s in r["segments"]]
    assert IR.pack_shared(groups, 10000) == e["rolls_by_scope"]


def test_acceptance_gate():
    """areas, pieces and balances reconcile; no double counting; the packing is physically possible; open details
    are visible; no waste percentage."""
    for ex in IC.SINGLE:
        a = _area(ex)
        pp = a["v26"]["piece_plan"]
        bal = pp["balance"]
        assert abs(bal["consumed_m2"] - bal["installed_m2"] - bal["offcuts_m2"]) < 1e-6
        assert abs(bal["installed_m2"] - a["row"]["B_installed_m2"]) < 1e-6
        assert abs(bal["consumed_m2"] - a["row"]["consumed_m2"]) < 1e-6
        ids = [p["id"] for p in pp["pieces"]] + [o["id"] for o in pp["offcuts"]]
        assert len(ids) == len(set(ids))                          # every piece and offcut once
        assert all(r["cut_m"] <= 10.0 + 1e-9 for r in pp["rolls"])
        assert a["row"]["final_material_state"] == "PROVISIONAL_DETAILS_OPEN"
        assert "FLOOR_WALL_JUNCTION_UNRESOLVED (N-11 / P-1)" in a["row"]["material_state_reasons"]
        assert all(o["class"] in ("TRUE_WASTE", "REUSABLE_SUBJECT_TO_N7") for o in pp["offcuts"])
        assert "waste_pct" not in str(sorted(a["v26"]))
