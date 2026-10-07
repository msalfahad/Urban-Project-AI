"""S4 generic footing-rebar engine (engine.source.footing_rebar): the 24 required behaviours on tiny synthetic
inputs. Every expected value is derived here from the fixture's own numbers (span, cover, count, D^2/162) - no
project total, no reference figure."""

from __future__ import annotations

import copy

import pytest

from engine.source import accurate_boq_rebar as AR
from engine.source import comparison_scope as CS
from engine.source import footing_rebar as FR
from engine.source import footing_rebar_guard as FG

SHA = "c" * 64
CTX = {"PROJECT_ID": "SYN", "DRAWING_ID": "syn.dxf", "DRAWING_SHA": SHA, "REVISION": "SYN-A",
       "ENGINE_COMMIT": "test+code:0", "REGISTER_VERSION": "FOOTING_REBAR_REGISTER_V1", "CALCULATION_ROUND": "S4",
       "unit_mass": {"method": "D2_OVER_162"}}
STRAIGHT = {"state": FR.END_STRAIGHT, "rule_id": "DET-STRAIGHT", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE"}
UNKNOWN_END = {"state": FR.END_UNKNOWN, "rule_id": "NO-DETAIL", "authority": "UNRESOLVED"}
RULES = {"cover": {"value_mm": 70.0, "rule_id": "COVER-70", "authority": "SOURCE_EXPLICIT"},
         "direction": {"rule_id": "DIR", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE"},
         "distribution": {"rule_id": "DIST", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE"}}


def kgm(d):
    return d * d / 162.0


def comp(name, c, d, run, dist, *, per_m=False, end=STRAIGHT, handles=("i", "a1", "a2")):
    adm = FG.admit_cells(c, d)
    form = adm.get("form") or {}
    return {"component": name, "count_mode": FR.BARS_PER_METRE if per_m else FR.EXPLICIT_COUNT,
            "count_value": form.get("count"), "dia_mm": form.get("dia_mm"), "run_dir": run, "dist_dir": dist,
            "end_treatment": end, "source_handles": list(handles), "source_text": f"{c} | {d}", "admission": adm,
            "authority": "SOURCE_EXPLICIT"}


def single(mark="FA", L=2000.0, W=1500.0, short=("10", "12"), long=("8", "12"), boxed="3+4"):
    return {"mark": mark, "layers": "SINGLE_LAYER", "L_mm": L, "W_mm": W, "D_mm": 400.0, "row_handle": "R1",
            "drawing_sha": SHA, "sheet_region": "schedule",
            "components": [comp(FR.BOTTOM_SHORT, *short, "W", "L"), comp(FR.BOTTOM_LONG, *long, "L", "W")],
            "boxed": None if boxed is None else {"raw_value": boxed, "source_handles": ["i", "bx"],
                                                  "semantics_class": FG.UNRESOLVED, "question_id": "Q-BOX",
                                                  "detail_reference": "typ. detail", "reason": "boxed unexplained"},
            "extras": []}


def two_layer(mark="FB", L=4000.0, W=3000.0):
    return {"mark": mark, "layers": "TWO_LAYER", "L_mm": L, "W_mm": W, "D_mm": 600.0, "row_handle": "R2",
            "drawing_sha": SHA, "sheet_region": "schedule",
            "components": [comp(FR.TOP_SHORT, "6", "14/m", "W", "L", per_m=True, end=UNKNOWN_END),
                           comp(FR.TOP_LONG, "6", "14/m", "L", "W", per_m=True, end=UNKNOWN_END),
                           comp(FR.BOTTOM_SHORT, "9", "16/m", "W", "L", per_m=True),
                           comp(FR.BOTTOM_LONG, "9", "16/m", "L", "W", per_m=True)],
            "boxed": None, "extras": []}


def occ(oid, mark, state=FR.OCC_ESTABLISHED, **kw):
    return dict({"occurrence_id": oid, "mark": mark, "state": state, "drawing_sha": SHA, "sheet_region": "plan",
                 "outline": {"handles": [f"o{oid}"]}, "tag_handles": [f"t{oid}"]}, **kw)


def by(res, oid, name):
    return next(c for c in res["components"] if c["occurrence_id"] == oid and c["component"] == name)


def run(occs, defs, rules=RULES, ctx=CTX):
    return FR.run(occs, defs, rules, ctx)


# 1 explicit count, 5 cover deduction, 17 unit mass
def test_explicit_count_cover_and_unit_mass():
    r = run([occ("O1", "FA")], [single()])
    s = by(r, "O1", FR.BOTTOM_SHORT)
    assert s["state"] == AR.VERIFIED and s["count"] == 10 and s["count_mode"] == FR.EXPLICIT_COUNT
    assert (s["raw_span_mm"], s["cover_1_mm"], s["cover_2_mm"], s["net_straight_mm"]) == (1500.0, 70.0, 70.0, 1360.0)
    assert s["kg_per_m"] == pytest.approx(144 / 162) and s["kg"] == pytest.approx(10 * 1.36 * 144 / 162)
    assert s["total_length_m"] == pytest.approx(13.6)


# 3 two directions, 4 unequal rectangle
def test_two_directions_on_an_unequal_rectangle():
    r = run([occ("O1", "FA")], [single(L=3500.0, W=1500.0, short=("32", "14"), long=("14", "14"))])
    s, l = by(r, "O1", FR.BOTTOM_SHORT), by(r, "O1", FR.BOTTOM_LONG)
    assert s["net_straight_mm"] == 1360.0 and l["net_straight_mm"] == 3360.0          # short spans W, long spans L
    assert s["kg"] == pytest.approx(32 * 1.36 * kgm(14)) and l["kg"] == pytest.approx(14 * 3.36 * kgm(14))
    swapped = single(L=3500.0, W=1500.0, short=("32", "14"), long=("14", "14"))
    swapped["components"][0]["run_dir"], swapped["components"][0]["dist_dir"] = "L", "W"
    assert by(run([occ("O1", "FA")], [swapped]), "O1", FR.BOTTOM_SHORT)["net_straight_mm"] == 3360.0  # input decides


# 2 bars per metre, 6 two-layer, 16 unknown end treatment
def test_bars_per_metre_two_layer_and_unknown_end():
    r = run([occ("O2", "FB")], [two_layer()])
    b = by(r, "O2", FR.BOTTOM_SHORT)
    assert b["state"] == AR.LOWER_BOUND and b["count_mode"] == FR.BARS_PER_METRE
    assert b["count"] == 35 and b["count_convention"] == 36                           # ceil(9 x 3.86); +1 edge bar
    pv = b["provenance"]
    assert pv["LOW"] == pytest.approx(35 * 2.86 * kgm(16)) and pv["BEST"] == pytest.approx(36 * 2.86 * kgm(16))
    assert pv["HIGH"] == pv["BEST"]
    t = by(r, "O2", FR.TOP_SHORT)
    assert t["state"] == AR.LOWER_BOUND and t["end_treatment"] == FR.END_UNKNOWN
    assert t["provenance"]["HIGH"] is None and any("END_TREATMENT" in m for m in t["missing"])
    assert by(r, "O2", FR.BOXED)["state"] == FR.NOT_APPLICABLE
    assert r["occurrences"][0]["release_state"] == FG.REBAR_LOWER_BOUND


def test_count_modes_are_never_converted():
    d = single()
    d["components"][0]["count_mode"] = FR.BARS_PER_METRE                    # the token says an explicit count
    with pytest.raises(FR.FootingRebarError, match="disagrees"):
        run([occ("O1", "FA")], [d])
    d = single()
    d["components"][0]["count_mode"] = FR.UNKNOWN
    assert by(run([occ("O1", "FA")], [d]), "O1", FR.BOTTOM_SHORT)["state"] == AR.BLOCKED_UNQUANTIFIED
    d["components"][0]["count_mode"] = "GUESS"
    with pytest.raises(FR.FootingRebarError):
        run([occ("O1", "FA")], [d])


# 7 unknown BOXED, 8 empty BOXED, 20 blocked survives summary
@pytest.mark.parametrize("raw", ["3+4", ""])
def test_boxed_unknown_or_empty_is_blocked_and_survives_the_summary(raw):
    r = run([occ("O1", "FA")], [single(boxed=raw)])
    b = by(r, "O1", FR.BOXED)
    assert b["state"] == AR.BLOCKED_UNQUANTIFIED and b["kg"] is None and b["question_id"] == "Q-BOX"
    assert b["provenance"]["BLOCKING_REASON"]
    o = r["occurrences"][0]
    assert o["release_state"] == FG.REBAR_LOWER_BOUND and o["unquantified_components"] == ["BOXED_REBAR"]
    s = r["summary"]
    assert s["blocked_unquantified_component_count"] == 1
    assert s["final_footing_rebar"] == "FINAL FOOTING REBAR NOT ESTABLISHED"
    assert s["accurate_summary"]["categories"]["FOUNDATIONS"]["blocked_unquantified_parts"] == 1


def test_quantifiable_boxed_semantics_are_refused_in_s4_v1():
    d = single()
    d["boxed"]["semantics_class"] = FG.SOURCE_EXPLICIT
    with pytest.raises(FR.FootingRebarError, match="BOXED"):
        run([occ("O1", "FA")], [d])


def test_a_footing_without_boxed_or_unresolved_parts_is_verified():
    r = run([occ("O1", "FA")], [single(boxed=None)])
    assert r["occurrences"][0]["release_state"] == FG.REBAR_VERIFIED
    assert r["summary"]["final_footing_rebar"] == "FINAL_FOOTING_REBAR_ESTABLISHED"


# 9 source conflict
def test_source_conflict_blocks_type_specific_components_and_keeps_candidates():
    o = occ("OC", "FA|FC", FR.OCC_SOURCE_CONFLICT, candidate_marks=["FA", "FC"])
    r = run([o, occ("O1", "FA")], [single(), single(mark="FC", L=2800.0, W=1400.0)])
    oc = next(x for x in r["occurrences"] if x["occurrence_id"] == "OC")
    assert oc["release_state"] == FG.REBAR_BLOCKED and oc["known_kg"] == 0 and oc["released_kg"] is None
    for name in (FR.BOTTOM_SHORT, FR.BOTTOM_LONG, FR.BOXED):
        c = by(r, "OC", name)
        assert c["state"] == AR.BLOCKED_UNQUANTIFIED and c["candidates"] == ["FA", "FC"]
        assert c["provenance"]["AUTHORITY_STATE"] == "SOURCE_CONFLICT"
    assert by(r, "OC", FR.TOP_SHORT)["state"] == FR.NOT_APPLICABLE              # no candidate has a top mesh
    assert by(r, "O1", FR.BOTTOM_SHORT)["state"] == AR.VERIFIED                   # the other FA is unaffected


# 10 duplicate footing tag / occurrence
def test_an_occurrence_entered_twice_is_refused():
    with pytest.raises(FR.FootingRebarError, match="twice"):
        run([occ("O1", "FA"), occ("O1", "FA")], [single()])


# 11 two occurrences of the same type stay separate
def test_two_occurrences_of_one_type_are_computed_separately():
    r = run([occ("O1", "FA"), occ("O2", "FA")], [single()])
    a, b = by(r, "O1", FR.BOTTOM_SHORT), by(r, "O2", FR.BOTTOM_SHORT)
    assert a["kg"] == b["kg"] and a["provenance"]["FOOTING_OCCURRENCE_ID"] == "O1"
    assert b["provenance"]["FOOTING_OCCURRENCE_ID"] == "O2"
    assert len(r["occurrences"]) == 2 and len(r["bbs"]) == 4


# 12 bar parser disagreement
def test_a_token_the_guard_fails_closed_is_blocked():
    d = single()
    d["components"][0] = comp(FR.BOTTOM_SHORT, "x", "12", "W", "L")             # unreadable cell pair
    c = by(run([occ("O1", "FA")], [d]), "O1", FR.BOTTOM_SHORT)
    assert c["state"] == AR.BLOCKED_UNQUANTIFIED and "guard" in c["why"]


# 13 missing diameter, 14 missing count, 15 missing dimension
def test_missing_inputs_block_only_their_component():
    d = single()
    d["components"][0]["dia_mm"] = None
    r = run([occ("O1", "FA")], [d])
    assert by(r, "O1", FR.BOTTOM_SHORT)["why"] == "diameter missing"
    assert by(r, "O1", FR.BOTTOM_LONG)["state"] == AR.VERIFIED
    d = single()
    d["components"][1]["count_value"] = None
    assert "count" in by(run([occ("O1", "FA")], [d]), "O1", FR.BOTTOM_LONG)["why"]
    d = single(W=None)
    r = run([occ("O1", "FA")], [d])
    assert {by(r, "O1", n)["state"] for n in (FR.BOTTOM_SHORT, FR.BOTTOM_LONG)} == {AR.BLOCKED_UNQUANTIFIED}


# 18 mass conservation (+ mutation)
def test_mass_conservation_holds_and_detects_a_tampered_component():
    r = run([occ("O1", "FA"), occ("O2", "FB")], [single(), two_layer()])
    assert r["conservation"]["all_pass"]
    comps = copy.deepcopy(r["components"])
    next(c for c in comps if c["state"] == AR.VERIFIED)["kg"] += 1.0
    bad = FR.conservation(r["occurrences"], comps, r["parts"], r["bbs"], r["summary"]["accurate_summary"])
    assert not bad["all_pass"] and not bad["checks"]["component_kg_equals_occurrence_known_kg"]
    dropped = [c for c in r["components"] if c["component"] != FR.BOXED]       # a blocked component disappears
    bad = FR.conservation(r["occurrences"], dropped, r["parts"], r["bbs"], r["summary"]["accurate_summary"])
    assert not bad["checks"]["every_required_component_once_per_occurrence"]


# 21 provenance completeness
def test_every_quantity_part_carries_the_full_provenance_contract():
    r = run([occ("O1", "FA"), occ("O2", "FB")], [single(), two_layer()])
    for p in r["parts"]:
        AR.validate_s4_part(p)
        assert set(AR.S4_PROVENANCE_FIELDS) <= set(p["provenance"])
        if p["state"] == AR.LOWER_BOUND:
            assert set(AR.S4_BOUND_FIELDS) <= set(p["provenance"])
            assert p["provenance"]["UNQUANTIFIED_COMPONENTS"] == r["occurrences"][
                [o["occurrence_id"] for o in r["occurrences"]].index(p["provenance"]["FOOTING_OCCURRENCE_ID"])][
                "unquantified_components"]
    p = copy.deepcopy(r["parts"][0])
    del p["provenance"]["RULE_ID"]
    with pytest.raises(AR.AccurateRebarError):
        AR.validate_s4_part(p)


# 22 version stamp
def test_summary_carries_the_comparison_stamp():
    s = run([occ("O1", "FA")], [single()])["summary"]
    st = CS.stamp(**s["stamp"])
    assert CS.stamp_relation(st, st) == CS.SAME_ENGINE_STATE
    other = dict(st, ENGINE_COMMIT="other")
    with pytest.raises(CS.ScopeError):
        CS.compare_stamped(1.0, 2.0, CS.DIRECT, stamp_a=st, stamp_b=other)


# 23 drawing hash mismatch
def test_an_input_from_another_drawing_is_refused():
    d = single()
    d["drawing_sha"] = "d" * 64
    with pytest.raises(FR.FootingRebarError, match="drawing sha"):
        run([occ("O1", "FA")], [d])
    with pytest.raises(FR.FootingRebarError, match="drawing sha"):
        run([dict(occ("O1", "FA"), drawing_sha="e" * 64)], [single()])


def test_a_provisional_occurrence_makes_its_parts_provisional():
    r = run([occ("O1", "FA", FR.OCC_PROVISIONAL)], [single(boxed=None)])
    assert by(r, "O1", FR.BOTTOM_SHORT)["state"] == AR.PROVISIONAL
    assert r["occurrences"][0]["release_state"] == FG.REBAR_PROVISIONAL


def test_starters_stay_with_the_column_engine():
    r = run([occ("O1", "FA")], [single()])
    assert by(r, "O1", FR.STARTER)["state"] == FR.NOT_APPLICABLE and by(r, "O1", FR.STARTER)["kg"] is None


def test_net_bbs_has_no_procurement():
    r = run([occ("O1", "FA")], [single()])
    assert all(b["used_kg"] is None and b["purchased_kg"] is None and b["waste_kg"] is None for b in r["bbs"])
    assert sum(b["net_bbs_kg"] for b in r["bbs"]) == pytest.approx(r["summary"]["verified_kg"])
