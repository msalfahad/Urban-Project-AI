"""S5 generic ground-system rebar engine (engine.source.ground_system_rebar) on synthetic members.

Every expected value is derived here from the synthetic detail (count, diameter) and the synthetic bar run with
kg/m = D^2/162 - never from a reference total.
"""

from __future__ import annotations

import copy
import sys

import pytest

from engine.source import accurate_boq_rebar as AR
from engine.source import ground_system_provenance as GP
from engine.source import ground_system_rebar as GS

SHA = "a" * 64
CTX = {"PROJECT_ID": "SYN", "DRAWING_ID": "syn.dxf", "DRAWING_SHA": SHA, "REVISION": "R0", "ENGINE_COMMIT": "t+code:0",
       "REGISTER_VERSION": "SYN_V1", "CALCULATION_ROUND": "S5-TEST",
       "unit_mass": {"method": "D2_OVER_162", "authority": "test"}}
RULES = {"cover": {"value_mm": 70, "rule_id": "COVER_SOIL", "authority": "SOURCE_EXPLICIT"},
         "development": {"state": GS.NOT_ESTABLISHED, "why": "no beam-end anchorage rule"},
         "bar_end_hooks": {"state": GS.NOT_ESTABLISHED, "why": "bar ends not detailed"},
         "stirrup_hooks": {"state": GS.NOT_ESTABLISHED, "why": "hook not sourced"},
         "stirrup_topology": {"GROUND_BEAM": {"state": "NOT_VERIFIED", "why": "legs not verified"},
                              "STRAP_BEAM": {"state": "NOT_STATED", "why": "schedule only"}}}
SRC = {"longitudinal": "SOURCE_EXPLICIT", "stirrup": "SOURCE_EXPLICIT", "section": "SOURCE_EXPLICIT"}


def gb_def(did, top, r1, r2, stirrup=(8, 150), side=None, B=300, D=400):
    return {"detail_id": did, "source_handles": [f"CLAIM:{did}"], "source_text": did, "sheet_region": "p.13",
            "authority": dict(SRC), "longitudinal": {"TOP_MAIN": top, "BOTTOM_ROW_1": r1, "BOTTOM_ROW_2": r2},
            "side": side, "stirrup": None if stirrup is None else {"dia_mm": stirrup[0], "mode": "SPACING_MM",
                                                                  "value": stirrup[1]},
            "end_zone": None, "extras": [], "section": {"B_mm": B, "D_mm": D, "D_state": "CROSS_VERIFIED_SOURCE"}}


def sb_def(did, top, bot, rate, W, H):
    return {"detail_id": did, "source_handles": [did.split(":")[1]], "source_text": did, "sheet_region": "SBT",
            "authority": dict(SRC), "longitudinal": {"TOP_MAIN": top, "BOTTOM_ROW_1": bot, "BOTTOM_ROW_2": None},
            "side": None, "stirrup": {"dia_mm": 8, "mode": "BARS_PER_METRE", "value": rate}, "end_zone": None,
            "extras": [], "section": {"B_mm": W, "D_mm": H, "D_state": "SOURCE_EXPLICIT"}}


DEFS = {"GT5": gb_def("GT5", [3, 16], [3, 16], [3, 16], D=600),
        "LT5": gb_def("LT5", [3, 14], [3, 14], [3, 14]),
        "LT25": gb_def("LT25", [3, 14], [3, 14], [3, 14], stirrup=None, D=300),
        "EXT": gb_def("EXT", [3, 16], [3, 16], [3, 16], side="2Ø12/30cm", D=None),
        "ROWS": gb_def("ROWS", [2, 12], [4, 20], [2, 16]),
        "SBT:A": sb_def("SBT:A", [13, 18], [7, 16], 8, 700, 500),
        "SBT:B1": sb_def("SBT:B1", [10, 18], [10, 18], 10, 800, 500),
        "SBT:B2": sb_def("SBT:B2", [20, 18], [10, 16], 10, 1000, 500)}


def occ(oid="GB-1", fam="GROUND_BEAM", ids=("LT5",), app="EXPLICIT_LENGTH_CONDITION", run=3.0, centre=3.6, clear=3.2,
        f2f=3.0, dist=3.0, depth=None, width=None, start=("COLUMN", "C1"), end=("COLUMN", "C2"), node_issues=None,
        flags=()):
    return {"occurrence_id": oid, "family": fam, "mark": "SB" if fam == "STRAP_BEAM" else "GB", "drawing_sha": SHA,
            "sheet_region": "plan", "start_node": {"kind": start[0], "refs": [start[1]]},
            "end_node": {"kind": end[0], "refs": [end[1]]}, "geometry_handles": ["H1", "H2"],
            "lengths": {"centreline_m": centre, "clear_concrete_m": clear, "face_to_face_m": f2f, "bar_run_lb_m": run,
                        "length_state": "CONSISTENT" if run else "LENGTH_GEOMETRY_CONFLICT",
                        "bar_run_state": "LOWER_BOUND" if run else "LENGTH_GEOMETRY_CONFLICT",
                        "issues": [] if run else ["shortest bar line > clear concrete"],
                        "stirrup_distribution_m": dist, "stirrup_distribution_basis": "SUPPORT_FACE_TO_FACE_RUN"},
            "width": width or {"state": "SOURCE_EXPLICIT", "value_mm": 300},
            "depth": depth or {"state": "SOURCE_EXPLICIT", "value_mm": 400, "bound_max_m": None},
            "detail_ids": list(ids), "applicability": app, "why_candidate": "test", "why_not_resolved": "",
            "node_issues": node_issues or {}, "questions": {"applicability": "Q1", "development": "Q7", "end": "Q10",
                                                            "stirrup_geometry": "Q6", "depth": "Q2"},
            "flags": list(flags)}


def comp(res, name):
    return next(c for c in res["components"] if c["component"] == name)


def kg(n, d, L):
    return n * L * d * d / 162


def run1(o, defs=DEFS, rules=RULES):
    return GS.occurrence_rebar(o, defs, rules, CTX)


# ---------------------------------------------------------------------------------------------------- ground beams
def test_source_supported_ground_beam_releases_longitudinal_lower_bound():
    r = run1(occ())
    for c in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2"):
        x = comp(r, c)
        assert x["state"] == AR.LOWER_BOUND and x["kg"] == pytest.approx(kg(3, 14, 3.0))
        pv = x["provenance"]
        assert pv["LOW"] == pv["BEST"] == x["kg"] and pv["HIGH"] is None
        assert "ANCHORAGE" in pv["UNQUANTIFIED_COMPONENTS"] and "BEAM_STIRRUP" in pv["UNQUANTIFIED_COMPONENTS"]
    assert r["occurrence"]["occurrence_state"] == GS.OCC_LOWER_BOUND
    assert r["occurrence"]["known_kg"] == pytest.approx(3 * kg(3, 14, 3.0))


@pytest.mark.parametrize("did,dia,stirrup_na", [("GT5", 16, False), ("LT5", 14, False), ("LT25", 14, True)])
def test_gt5_lt5_lt2_5_spans(did, dia, stirrup_na):
    r = run1(occ(ids=(did,), run=6.0 if did == "GT5" else 2.0 if did == "LT25" else 4.0,
                 dist=6.0 if did == "GT5" else 2.0 if did == "LT25" else 4.0))
    L = r["occurrence"]["bar_straight_run_lower_bound_m"]
    assert comp(r, "TOP_MAIN")["kg"] == pytest.approx(kg(3, dia, L))
    if stirrup_na:                         # the <2.5 m section prints no stirrup: nothing inherited (no Ø8/150)
        for c in GS.STIRRUP:
            assert comp(r, c)["state"] == GS.NOT_APPLICABLE
    else:
        assert comp(r, "STIRRUP_COUNT")["count"] == -(-int(round(L * 1000)) // 150)


def test_exterior_beam_releases_depth_independent_longitudinal_only():
    depth = {"state": "BOUNDED_ABOVE", "value_mm": None, "bound_max_m": 1.0}
    r = run1(occ(ids=("EXT",), app="PROJECT_GENERAL_DETAIL", depth=depth))
    assert comp(r, "TOP_MAIN")["kg"] == pytest.approx(kg(3, 16, 3.0))
    assert comp(r, "BOTTOM_ROW_2")["state"] == AR.LOWER_BOUND
    side = comp(r, "SIDE_REBAR")
    assert side["state"] == AR.BLOCKED_UNQUANTIFIED and side["kg"] is None and "BOUNDED_ABOVE" in side["why"]
    core = comp(r, "STIRRUP_CORE_PATH")
    assert core["state"] == AR.BLOCKED_UNQUANTIFIED and any("DEPTH" in f for f in core["missing_facets"])
    assert r["occurrence"]["depth_mm"] is None                # the level bound is never used as a depth value


def test_candidate_identical_longitudinal_releases_invariant():
    r = run1(occ(ids=("LT25", "LT5"), app="CANDIDATE_DETAIL",
                 depth={"state": "CANDIDATE_CONFLICT", "value_mm": None, "bound_max_m": None}))
    t = comp(r, "TOP_MAIN")
    assert t["state"] == AR.LOWER_BOUND and t["candidate_invariant"] is True
    assert t["provenance"]["CANDIDATE_INVARIANT"] is True and t["provenance"]["DETAIL_CANDIDATES"] == ["LT25", "LT5"]
    for c in ("STIRRUP_DIAMETER", "STIRRUP_COUNT", "STIRRUP_CORE_PATH"):   # LT25 prints none, LT5 Ø8/150
        assert comp(r, c)["state"] == AR.BLOCKED_UNQUANTIFIED


def test_candidate_different_longitudinal_is_blocked():
    r = run1(occ(ids=("EXT", "LT5"), app="CANDIDATE_DETAIL"))
    t = comp(r, "TOP_MAIN")
    assert t["state"] == AR.BLOCKED_UNQUANTIFIED and t["kg"] is None
    assert t["provenance"]["AUTHORITY_STATE"] == "SOURCE_CONFLICT" and "disagree" in t["why"]
    assert comp(r, "STIRRUP_COUNT")["state"] == AR.LOWER_BOUND          # Ø8/150 identical in both: invariant
    assert r["occurrence"]["occurrence_state"] == GS.OCC_BLOCKED


def test_concentrated_load_unknown_keeps_interior_detail_blocked():
    r = run1(occ(ids=("NO_DETAIL_FOR_LOAD", "LT5"), app="CANDIDATE_DETAIL"))
    for c in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "STIRRUP_COUNT", "EXTRA_SUPPORT", "MID"):
        assert comp(r, c)["state"] == AR.BLOCKED_UNQUANTIFIED, c
    assert "no project definition" in comp(r, "TOP_MAIN")["why"]
    assert r["occurrence"]["known_kg"] == 0


def test_depth_unknown_longitudinal_still_released():
    r = run1(occ(ids=("EXT",), app="PROJECT_GENERAL_DETAIL",
                 depth={"state": "SOURCE_CONFLICT", "value_mm": None, "bound_max_m": 0.3}))
    assert comp(r, "TOP_MAIN")["state"] == AR.LOWER_BOUND
    assert comp(r, "SIDE_REBAR")["state"] == AR.BLOCKED_UNQUANTIFIED
    assert r["occurrence"]["depth_mm"] is None


def test_stirrup_count_known_mass_blocked():
    r = run1(occ())
    cnt, core = comp(r, "STIRRUP_COUNT"), comp(r, "STIRRUP_CORE_PATH")
    assert cnt["state"] == AR.LOWER_BOUND and cnt["count"] == 20 and cnt["kg"] is None
    assert cnt["count_convention_not_adopted"] == 21 and cnt["provenance"]["BEST"] == 20
    assert core["state"] == AR.BLOCKED_UNQUANTIFIED and core["kg"] is None and core["stirrup_count_known"]
    assert all(c["quantity_kind"] != GS.MASS for c in r["components"] if c["component"] in
               ("STIRRUP_COUNT", "STIRRUP_DIAMETER", "STIRRUP_SPACING"))
    assert not any(p["part_id"].endswith("STIRRUP_COUNT") for p in r["parts"])


def test_two_lower_rows_stay_distinct():
    r = run1(occ(ids=("ROWS",)))
    r1, r2 = comp(r, "BOTTOM_ROW_1"), comp(r, "BOTTOM_ROW_2")
    assert (r1["bar_count"], r1["dia_mm"], r2["bar_count"], r2["dia_mm"]) == (4, 20, 2, 16)
    assert r1["kg"] == pytest.approx(kg(4, 20, 3.0)) and r2["kg"] == pytest.approx(kg(2, 16, 3.0))
    assert {p["part_id"] for p in r["parts"]} >= {"GB-1:BOTTOM_ROW_1", "GB-1:BOTTOM_ROW_2"}


def test_support_face_run_used_never_centreline_or_clear():
    r = run1(occ(run=2.85, centre=3.6, clear=3.2, f2f=2.9))
    t = comp(r, "TOP_MAIN")
    assert t["straight_run_m"] == 2.85 and t["kg"] == pytest.approx(kg(3, 14, 2.85))
    assert t["provenance"]["INPUTS"]["straight_run_basis"] == "BAR_STRAIGHT_RUN_LOWER_BOUND"


def test_bar_run_conflict_blocks_longitudinal_and_count():
    r = run1(occ(run=None, dist=None))
    for c in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "STIRRUP_COUNT"):
        assert comp(r, c)["state"] == AR.BLOCKED_UNQUANTIFIED
    assert comp(r, "STIRRUP_DIAMETER")["state"] == AR.VERIFIED       # the printed attribute is still known


def test_free_end_unresolved_blocks_only_that_end_treatment():
    r = run1(occ(end=("BOUNDARY", "7FE"), node_issues={"2": "BOUNDARY 7FE: on the plot boundary"}))
    assert "unresolved" in comp(r, "DEVELOPMENT_SUPPORT_2")["why"] and comp(r, "HOOK_2")["question_id"] == "Q10"
    assert "unresolved" not in comp(r, "DEVELOPMENT_SUPPORT_1")["why"]
    assert comp(r, "TOP_MAIN")["state"] == AR.LOWER_BOUND             # known straight steel is not held back


def test_development_and_hooks_blocked_and_no_default_accepted():
    r = run1(occ())
    for c in ("DEVELOPMENT_SUPPORT_1", "DEVELOPMENT_SUPPORT_2", "HOOK_1", "HOOK_2", "STIRRUP_HOOK_1",
              "STIRRUP_HOOK_2"):
        x = comp(r, c)
        assert x["state"] == AR.BLOCKED_UNQUANTIFIED and x["kg"] is None
    assert comp(r, "DEVELOPMENT_SUPPORT_1")["accurate_component"] == "ANCHORAGE"
    for k in ("development", "bar_end_hooks", "stirrup_hooks"):
        bad = copy.deepcopy(RULES)
        bad[k] = {"state": "CODE_DEFAULT_40D", "why": "x"}
        with pytest.raises(GS.GroundSystemRebarError):
            run1(occ(), rules=bad)


def test_stirrup_mass_refused_if_every_facet_supported():
    rules = copy.deepcopy(RULES)
    rules["stirrup_topology"]["GROUND_BEAM"] = {"state": "SOURCE_ESTABLISHED", "why": ""}
    r = run1(occ(), rules=rules)        # hooks still missing -> blocked, never computed
    assert comp(r, "STIRRUP_CORE_PATH")["state"] == AR.BLOCKED_UNQUANTIFIED


# ------------------------------------------------------------------------------------------------------ straps
def test_sb1_like_strap():
    r = run1(occ("SB-1", "STRAP_BEAM", ("SBT:A",), "EXPLICIT_MARK_MATCH", run=4.55, dist=4.55,
                 start=("FOOTING", "F1"), end=("FOOTING", "F2"), flags=["START_SUPPORT_OUTLINE_SOURCE_CONFLICT (F|F10)"],
                 depth={"state": "SOURCE_EXPLICIT", "value_mm": 500}))
    assert comp(r, "TOP_MAIN")["kg"] == pytest.approx(kg(13, 18, 4.55))
    assert comp(r, "BOTTOM_MAIN")["kg"] == pytest.approx(kg(7, 16, 4.55))
    assert comp(r, "STIRRUP_COUNT")["count"] == 37
    assert [c["component"] for c in r["components"]] == list(GS.COMPONENTS["STRAP_BEAM"])
    assert "SIDE_REBAR" not in {c["component"] for c in r["components"]}
    assert comp(r, "DEVELOPMENT_FOOTING_1")["state"] == AR.BLOCKED_UNQUANTIFIED
    assert any("F|F10" in f for f in comp(r, "TOP_MAIN")["provenance"]["OCCURRENCE_FLAGS"])
    assert {p["category"] for p in r["parts"]} == {"FOUNDATIONS"}


def test_sb2_like_conflict_blocks_bars_but_invariant_stirrup_count_releases():
    r = run1(occ("SB-2", "STRAP_BEAM", ("SBT:B1", "SBT:B2"), "CANDIDATE_DETAIL", run=1.829, dist=1.829,
                 start=("FOOTING", "F1"), end=("FOOTING", "F2"),
                 width={"state": "CANDIDATE_CONFLICT", "value_mm": None, "candidates": {"SBT:B1": 800, "SBT:B2": 1000}},
                 depth={"state": "CANDIDATE_INVARIANT", "value_mm": 500}))
    assert comp(r, "TOP_MAIN")["state"] == comp(r, "BOTTOM_MAIN")["state"] == AR.BLOCKED_UNQUANTIFIED
    cnt = comp(r, "STIRRUP_COUNT")
    assert cnt["state"] == AR.LOWER_BOUND and cnt["count"] == 19 and cnt["candidate_invariant"] is True
    core = comp(r, "STIRRUP_CORE_PATH")
    assert core["state"] == AR.BLOCKED_UNQUANTIFIED and any("WIDTH CANDIDATE_CONFLICT" in f for f in
                                                            core["missing_facets"])
    assert r["occurrence"]["occurrence_state"] == GS.OCC_BLOCKED and r["occurrence"]["known_kg"] == 0


def test_sb3_like_strap():
    d = dict(DEFS, **{"SBT:C": sb_def("SBT:C", [5, 18], [5, 16], 7, 500, 400)})
    r = run1(occ("SB-3", "STRAP_BEAM", ("SBT:C",), "EXPLICIT_MARK_MATCH", run=2.838, dist=2.838,
                 start=("FOOTING", "F1"), end=("FOOTING", "F2"), depth={"state": "SOURCE_EXPLICIT", "value_mm": 400}),
             defs=d)
    assert r["occurrence"]["known_kg"] == pytest.approx(kg(5, 18, 2.838) + kg(5, 16, 2.838))
    assert comp(r, "STIRRUP_COUNT")["count"] == 20


# ---------------------------------------------------------------------------------------- contract / conservation
def test_every_component_passes_the_generic_contract_and_parts_validate():
    for o in (occ(), occ(ids=("EXT", "LT5"), app="CANDIDATE_DETAIL"), occ(run=None, dist=None)):
        r = run1(o)
        for c in r["components"]:
            GS.validate_record(c)
            assert c["provenance"]["ELEMENT_FAMILY"] == "GROUND_BEAM"
            assert not any(k.startswith("FOOTING_") for k in c["provenance"])
        for p in r["parts"]:
            GP.validate_s5_part(p)


def test_contract_mutations_fail():
    r = run1(occ())
    t = comp(r, "TOP_MAIN")
    m = copy.deepcopy(t)
    m["provenance"]["FOOTING_OCCURRENCE_ID"] = "GB-1"
    with pytest.raises(GS.GroundSystemRebarError):
        GS.validate_record(m)
    m = copy.deepcopy(t)
    del m["provenance"]["DRAWING_SHA"]
    with pytest.raises(GS.GroundSystemRebarError):
        GS.validate_record(m)
    m = copy.deepcopy(t)
    m["provenance"]["DETAIL_APPLICABILITY_STATE"] = "CANDIDATE_DETAIL"
    m["provenance"]["CANDIDATE_INVARIANT"] = False
    with pytest.raises(GS.GroundSystemRebarError):
        GS.validate_record(m)
    m = copy.deepcopy(comp(r, "STIRRUP_COUNT"))
    m["kg"] = 1.0
    with pytest.raises(GS.GroundSystemRebarError):
        GS.validate_record(m)
    m = copy.deepcopy(comp(r, "DEVELOPMENT_SUPPORT_1"))
    m["kg"] = 0.0
    with pytest.raises(GS.GroundSystemRebarError):
        GS.validate_record(m)


def test_conservation_and_mutation():
    occs = [occ("A"), occ("B", ids=("EXT", "LT5"), app="CANDIDATE_DETAIL"), occ("C", run=None, dist=None),
            occ("S", "STRAP_BEAM", ("SBT:A",), "EXPLICIT_MARK_MATCH", run=4.55, dist=4.55,
                start=("FOOTING", "F1"), end=("FOOTING", "F2"))]
    res = GS.run(occs, DEFS, RULES, CTX)
    assert res["conservation"]["all_pass"], res["conservation"]["checks"]
    assert res["summary"]["final_ground_system_rebar"] == "FINAL GROUND-SYSTEM REBAR NOT ESTABLISHED"
    fam = res["summary"]["families"]
    assert fam["GROUND_BEAM"]["LOWER_BOUND_KNOWN_KG"] == pytest.approx(3 * kg(3, 14, 3.0))
    assert fam["STRAP_BEAM"]["LOWER_BOUND_KNOWN_KG"] == pytest.approx(kg(13, 18, 4.55) + kg(7, 16, 4.55))
    comps = [c for c in res["components"] if not (c["occurrence_id"] == "A" and c["component"] == "MID")]
    bad = GS.conservation(res["occurrences"], comps, res["parts"], res["bbs"], res["summary"]["accurate_summary"])
    assert not bad["checks"]["every_component_terminates_once_per_occurrence"]
    with pytest.raises(GS.GroundSystemRebarError):
        GS.run(occs + [occ("A")], DEFS, RULES, CTX)


def test_engine_has_no_rough_or_reference_dependency():
    src = open(GS.__file__, encoding="utf-8").read()
    for bad in ("rough_rebar", "130", "kg/m3", "freelancer", "christ", "UC4N", "U-C4N", "profiles/"):
        assert bad not in src, bad
    import importlib
    mods_before = set(sys.modules)
    importlib.reload(GS)
    assert not any("rough_rebar" in m for m in set(sys.modules) - mods_before)
