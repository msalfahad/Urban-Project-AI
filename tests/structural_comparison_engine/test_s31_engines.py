"""S3.1 generic engines - synthetic tests only (no project drawing, no benchmark value).

Covers the brief's 20 cases (rough rebar, comparison scope, donor-defect guards, oracle, populations, parapet
fallback, BBS isolation), the benchmark firewall, and the S3.1 column corrections (one unit-mass method, '/m'
notation, section transitions)."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from engine.source import accurate_boq_rebar as AB
from engine.source import cad_guards as G
from engine.source import cad_oracle as CO
from engine.source import column_rebar as CR
from engine.source import comparison_scope as CS
from engine.source import rebar_sanity_variance as SV
from engine.source import rebar_unit_mass as UM
from engine.source import rough_rebar_sanity as RR
from engine.source import source_oracle_comparison as SOC
from engine.source import source_roles as SR
from engine.source import structural_population_discovery as SP

ROOT = Path(__file__).resolve().parents[2]
PROFILE = {"profile_id": "TEST", "authority": "URBAN_OWNER_ESTIMATING_RULE", "use": "SANITY_CHECK_ONLY",
           "ratios_kg_per_m3": {"WALLS_AND_COLUMNS": 200, "SLABS": 90, "BEAMS": 150}}


def occ(i, ec, m3, st="VERIFIED"):
    return {"occurrence_id": i, "element_class": ec, "concrete_m3": m3, "concrete_state": st}


# 1
def test_category_specific_rough_rebar():
    r = RR.rough_summary([occ("c1", "COLUMN", 2.0), occ("s1", "SOLID_SLAB", 10.0)], PROFILE)["categories"]
    assert r["WALLS_AND_COLUMNS"]["rough_kg_released_basis"] == 400.0                     # 2 x 200
    assert r["SLABS"]["rough_kg_released_basis"] == 900.0                                  # 10 x 90


# 2
def test_wrong_ratio_or_authority_rejected():
    for bad in (dict(PROFILE, ratios_kg_per_m3={"SLABS": 90.5}), dict(PROFILE, ratios_kg_per_m3={"SLABS": -1}),
                dict(PROFILE, authority="STRUCTURAL_CODE"), dict(PROFILE, authority="URBAN_OWNER_RULE"),
                dict(PROFILE, use="PRODUCTION"),
                dict(PROFILE, mapping={"PLAIN_CONCRETE": "SLABS"}), dict(PROFILE, mapping={"NOT_A_CLASS": "SLABS"})):
        with pytest.raises(RR.RoughRebarError):
            RR.rough_summary([occ("s", "SOLID_SLAB", 1.0)], bad)
    r = RR.rough_summary([occ("s", "SOLID_SLAB", 1.0)], PROFILE)["categories"]
    assert r["SLABS"]["ratio_kg_per_m3"] == 90                                          # a slab never takes 200


# 3
def test_unknown_category_gets_no_guessed_ratio():
    res = RR.rough_summary([occ("l1", "LINTEL", 1.0), {"occurrence_id": "x", "description": "mystery element",
                                                       "concrete_m3": 3.0, "concrete_state": "VERIFIED"},
                            occ("g", "GROUND_BEAM", 4.0)], PROFILE)
    assert {u["occurrence_id"] for u in res["not_configured"]} == {"l1", "x"}
    assert all(u["state"] == RR.NOT_CONFIGURED for u in res["not_configured"])
    g = res["categories"]["GROUND_BEAMS_AND_GROUND_SLAB"]
    assert g["ratio_state"] == RR.NOT_CONFIGURED and g["rough_kg_released_basis"] is None


# 4
def test_same_occurrence_cannot_enter_two_categories():
    with pytest.raises(RR.RoughRebarError):
        RR.rough_summary([occ("a", "COLUMN", 1.0), occ("a", "BEAM", 1.0)], PROFILE)
    with pytest.raises(CS.ScopeError):
        CS.make_view("V", [{"category": "A", "measurement_basis": "X", "included_components": ["SLAB"],
                            "overlap_policy": "p"},
                           {"category": "B", "measurement_basis": "X", "included_components": ["SLAB"],
                            "overlap_policy": "p"}])


# 5
def test_rough_result_never_modifies_actual_bbs():
    parts = [{"part_id": "m", "category": "COLUMNS", "component": "COLUMN_MAIN_BAR", "state": "VERIFIED",
              "kg": 350.0, "basis": ["SCHEDULE"]},
             {"part_id": "t", "category": "COLUMNS", "component": "COLUMN_TIE", "state": "PROVISIONAL",
              "kg": 20.0, "basis": ["STRUCTURAL_DETAIL"]},
             {"part_id": "x", "category": "COLUMNS", "component": "COLUMN_OTHER_DETAIL",
              "state": "BLOCKED_UNQUANTIFIED", "kg": None, "basis": ["STRUCTURAL_DETAIL"]}]
    actual = AB.summarise(parts)
    before = copy.deepcopy(actual)
    rough = RR.rough_summary([occ("c1", "COLUMN", 2.0, "VERIFIED"), occ("c2", "COLUMN", 1.0, "BLOCKED")], PROFILE)
    res = SV.compare(actual, rough)
    assert actual == before
    rr = rough["categories"]["WALLS_AND_COLUMNS"]
    assert rr["blocked_concrete_m3"] == 1.0 and rr["rough_kg_modelled_basis"] == 400.0      # blocked concrete out
    row = res["rows"][0]
    assert row["state"] == SV.SIDE_BY_SIDE and row["SANITY_VARIANCE_KG"] is None
    assert "missing" not in json.dumps(res).lower()


# 6
def test_donor_value_never_overwrites_urban():
    urban = {"element_id": "F1", "fact_type": "VOLUME_M3", "value": 2.0, "source_refs": ["h:1"], "status": "VERIFIED"}
    before = copy.deepcopy(urban)
    row = SOC.compare(urban, CO.answer("BOUNDING_BOX", 2.6, oracle="DONOR"), basis_match=True, rel_tol=0.01,
                      close_rel_tol=0.05)
    assert urban == before and row["urban_value"] == 2.0 and row["result"] == SOC.CONFLICT
    assert row["oracle_value"] == 2.6


# 7
def test_freelancer_value_never_resolves_a_drawing_conflict():
    with pytest.raises(SR.SourceRoleError):
        SR.admit_resolution({"role": SR.FREELANCER_QS_REFERENCE, "value": "C7"})
    with pytest.raises(SR.SourceRoleError):
        SR.admit_resolution({"role": SR.EXTERNAL_ORACLE, "value": "C7"})
    assert SR.admit_resolution({"role": SR.PRODUCTION_SOURCE})
    assert not SR.can(SR.FREELANCER_QS_REFERENCE, "create_quantity")


def _views():
    phys = CS.make_view("URBAN_PHYSICAL_VIEW", [
        {"category": "BEAMS", "measurement_basis": "BEAM_DOWNSTAND_ONLY", "included_components": ["DOWNSTAND"],
         "overlap_policy": "slab over beam belongs to SLABS"},
        {"category": "SLABS", "measurement_basis": "SLAB_FULL_DEPTH", "included_components": ["SLAB_FULL"],
         "overlap_policy": "full slab depth incl. over beams"}],
        normalization_groups=[{"group_id": "BEAMS+SLABS", "categories": ["BEAMS", "SLABS"]}])
    qs = CS.make_view("FREELANCER_QS_VIEW", [
        {"category": "BEAMS", "measurement_basis": "BEAM_GROSS_DEPTH", "included_components": ["BEAM_GROSS"],
         "overlap_policy": "slab over beam belongs to BEAMS"},
        {"category": "SLABS", "measurement_basis": "SLAB_NET_OF_BEAMS", "included_components": ["SLAB_NET"],
         "overlap_policy": "slab between beams only"}],
        normalization_groups=[{"group_id": "BEAMS+SLABS", "categories": ["BEAMS", "SLABS"]}])
    return phys, qs


# 8, 9
def test_beam_slab_allocation_not_comparable_until_normalized():
    phys, qs = _views()
    # same physical concrete: downstand 3 + slab 10 == gross beam 4 + net slab 9
    a = CS.assemble(phys, [{"component_id": "d", "kind": "DOWNSTAND", "quantity": 3.0, "unit": "m3"},
                           {"component_id": "s", "kind": "SLAB_FULL", "quantity": 10.0, "unit": "m3"}])
    b = CS.assemble(qs, [{"component_id": "g", "kind": "BEAM_GROSS", "quantity": 4.0, "unit": "m3"},
                         {"component_id": "n", "kind": "SLAB_NET", "quantity": 9.0, "unit": "m3"}])
    for cat in ("BEAMS", "SLABS"):
        st = CS.comparability(a["categories"][cat], b["categories"][cat])
        assert st == CS.NOT_COMPARABLE
        cv = CS.compare_values(a["categories"][cat]["quantity"], b["categories"][cat]["quantity"], st)
        assert cv["difference_percent"] is None and cv["difference"] is None
    grp = phys["normalization_groups"][0]
    sa = CS.normalized_group({k: v["quantity"] for k, v in a["categories"].items()}, grp)
    sb = CS.normalized_group({k: v["quantity"] for k, v in b["categories"].items()}, grp)
    cv = CS.compare_values(sa, sb, CS.NORMALIZED)
    assert cv["difference"] == 0 and cv["status"] == CS.NORMALIZED
    same = CS.comparability(a["categories"]["SLABS"], a["categories"]["SLABS"])
    assert same == CS.DIRECT


# 10
def test_region_crossing_detected_even_when_start_outside():
    region = [(0, 0), (10, 0), (10, 10), (0, 10)]
    seg = ((-5, 5), (5, 5))            # starts outside, ends inside
    through = ((-5, 5), (15, 5))       # passes through, both ends outside
    assert not G.start_point_inside_region(through, region)
    assert G.segment_intersects_region(seg, region) and G.segment_intersects_region(through, region)
    assert not G.segment_intersects_region(((-5, -5), (-1, -1)), region)


# 11
def test_one_physical_geometry_authority():
    g = G.physical_occurrence_geometry("B1", axis_start=(0, 0), axis_end=(5000, 0), support_widths=(300, 300))
    assert g["clear_span"] == 4700 and g["rebar_design_span"] == 4700 and g["centreline_span"] == 5000
    assert G.check_geometry_consistency(g, concrete_span=4700, rebar_span=4700, concrete_basis="clear_span",
                                        rebar_basis="rebar_design_span") == []
    bad = G.check_geometry_consistency(g, concrete_span=4700, rebar_span=5400, concrete_basis="clear_span",
                                       rebar_basis="schedule_span")       # rebar from a schedule span
    assert bad


# 12
def test_evidence_state_from_structure_not_free_text():
    assert G.evidence_state({"authority_class": "ENGINEERING_METHOD", "note": "VERIFIED by site"}) == "PROVISIONAL"
    assert G.evidence_state({"note": "verified"}) == "BLOCKED"
    assert G.evidence_state({"authority_class": "SOURCE_FACT", "note": "assumed"}) == "VERIFIED"


# 13
def test_oracle_pagination_is_incomplete_not_a_count():
    a = CO.answer("COUNT_TAGS", 500, entity_limit=500, returned=500, oracle="MCP")
    assert a["state"] == CO.INCOMPLETE and a["value"] is None
    row = SOC.compare({"element_id": "TAGS", "fact_type": "COUNT", "value": 640}, a, basis_match=True)
    assert row["result"] == SOC.UNAVAILABLE
    assert CO.answer("COUNT_TAGS", 120, entity_limit=500, returned=120)["state"] == CO.OK


def test_region_tool_failure_is_unavailable_not_zero():
    class Boom(CO.CadOracleReadOnly):
        name = "BROKEN"

        def ask(self, question, **k):
            raise RuntimeError("crossing selection failed")
    r = CO.region_select(Boom(), "R1")
    assert r["state"] == CO.UNAVAILABLE and r["value"] is None
    assert CO.UnavailableOracle().ask("COUNT_TAGS")["state"] == CO.UNAVAILABLE
    assert CO.answer("COUNT_TAGS", None)["state"] == CO.UNAVAILABLE                # no value is never zero


# 14
def test_open_polyline_area_not_trusted():
    sq = [(0, 0), (4, 0), (4, 3), (0, 3)]
    assert G.closed_polygon_area(sq)["area"] is None
    assert G.closed_polygon_area(sq, closed_flag=True)["area"] == 12
    assert G.closed_polygon_area(sq + [(0, 0)])["area"] == 12


# 15
def test_unreadable_text_routes_to_source_review():
    for t in (None, "", "���", "????"):
        r = G.text_readability(t)
        assert r["state"] == G.TEXT_UNREADABLE and r["route"] == G.SOURCE_REVIEW and r["rule_absent"] is None
    assert G.text_readability("LAP 40D")["state"] == "READABLE"


# 16, 17
def test_schedule_row_never_creates_occurrence_and_marks_per_floor():
    rows = [{"mark": "K1", "storey_band": "LOW", "B": 30}, {"mark": "K1", "storey_band": "UP", "B": 20},
            {"mark": "K9", "storey_band": "LOW", "B": 40}]
    occs = [{"id": "a", "mark": "K1", "storey_band": "LOW"}, {"id": "b", "mark": "K1", "storey_band": "UP"},
            {"id": "c", "mark": "K2", "storey_band": "UP"}]
    joined, unbound, orphans = G.join_occurrences(occs, rows)
    assert [j["id"] for j in joined] == ["a", "b"] and [j["definition"]["B"] for j in joined] == [30, 20]
    assert [u["id"] for u in unbound] == ["c"]
    assert [o["mark"] for o in orphans] == ["K9"] and orphans[0]["occurrences_created"] == 0
    assert not G.counts_as_physical({"region_role": "TYPICAL_DETAIL"})
    assert not G.counts_as_physical({"region_role": "PLAN", "copy_of": "x"})
    assert not G.counts_as_physical({"region_role": "PLAN", "space": "PAPER"})
    assert G.counts_as_physical({"region_role": "PLAN"})


# 18
def test_special_population_cannot_silently_disappear():
    r = SP.discover({"POOL": {"state": "PRESENT", "refs": ["p.6"]}, "RAFT": {"state": "NOT_PRESENT"}})
    pops = {x["population"]: x for x in r["rows"]}
    assert r["complete_list"] and len(pops) == len(SP.ALL_POPULATIONS)
    assert pops["RAFT"]["state"] == SP.UNKNOWN                         # absence claimed without a searched source
    assert pops["LIFT_PIT"]["state"] == SP.UNKNOWN and pops["POOL"]["state"] == SP.PRESENT
    with pytest.raises(ValueError):
        SP.discover({"NOT_A_POPULATION": {"state": "PRESENT"}})


# 19
def test_parapet_stiffener_fallback_never_verified():
    cand = json.loads((ROOT / "engine" / "profiles" / "URBAN_STANDARD_CANDIDATES_V1.json").read_text())
    c = cand["candidates"]["PARAPET_STIFFENER_COLUMN"]
    s = SP.parapet_stiffener_scenario(18.0, urban_candidate=c)
    assert s["state"] == "PROVISIONAL" and s["authority"] == "URBAN_STANDARD_CANDIDATE" and s["scenario_only"]
    assert s["flag"] == "PARAPET_STIFFENER_SPACING_REQUIRED" and s["bays"] == 5 and s["intermediate_stiffeners"] == 4
    assert SP.parapet_stiffener_scenario(18.0, drawing_spacing_m=3.0)["state"] == "VERIFIED"
    assert SP.parapet_stiffener_scenario(18.0)["state"] == SP.BLOCKED
    assert SP.parapet_ring_beam_requirement({"section": "20x30"})["state"] == SP.BLOCKED


# 20
def test_rough_ratios_cannot_influence_bbs():
    prod = ["column_rebar.py", "rebar_model.py", "rebar_unit_mass.py"]
    for m in prod:
        src = (ROOT / "engine" / "source" / m).read_text(encoding="utf-8")
        assert "rough_rebar_sanity" not in src and "ROUGH_REBAR_PROFILE" not in src and "kg_per_m3" not in src.replace(
            "kg_per_m3\": kg / volume_m3", ""), m
    import sys
    before = set(sys.modules)
    import importlib
    importlib.reload(CR)
    assert "engine.source.rough_rebar_sanity" not in (set(sys.modules) - before)


# ---------------------------------------------------------------------------------------------- firewall
BENCHMARK = ("44.19", "352.436075", "77.6305", "75.090", "39.7515", "65.965875", "59.8174", "21.8328", "12.348",
             "47.055", "590.362", "337.812", "598.708", "333.173", "22.619", "22.916", "66.579", "65.669")


def test_benchmark_values_cannot_enter_production_modules():
    hits = {}
    for p in sorted((ROOT / "engine" / "source").glob("*.py")) + sorted((ROOT / "engine" / "profiles").glob("*")):
        src = p.read_text(encoding="utf-8")
        found = [b for b in BENCHMARK if re.search(rf"(?<![\d.]){re.escape(b)}(?!\d)", src)]
        if found:
            hits[p.name] = found
        assert "alsenan_multi_engine_comparison" not in src, p.name
    assert not hits, hits


def test_new_generic_modules_hold_no_project_marks():
    names = re.compile(r"alsenan|st7757|p7757|qortuba|rashed", re.I)
    marks = re.compile(r"\b(?:C|F|SB|CB|GB|B|CN)\d{1,2}\b|\bX\d{2}-Y\d{2}\b")
    for m in ("rough_rebar_sanity.py", "accurate_boq_rebar.py", "rebar_sanity_variance.py", "rebar_boq_sections.py",
              "comparison_scope.py", "cad_oracle.py", "source_oracle_comparison.py",
              "structural_population_discovery.py", "cad_guards.py", "source_roles.py", "rebar_unit_mass.py"):
        src = (ROOT / "engine" / "source" / m).read_text(encoding="utf-8")
        assert not names.findall(src) + marks.findall(src), m
    pop = (ROOT / "engine" / "source" / "structural_population_discovery.py").read_text(encoding="utf-8")
    assert not re.search(r"(?<![\w.])4(?:\.0)?\s*m\b|max_spacing_m\s*=\s*\d", pop)   # the 4 m candidate is data


# ---------------------------------------------------------------------------------------------- S3.1 columns
def test_unit_mass_methods_and_single_method_rule():
    assert UM.kg_per_m(16, {"method": UM.D2_OVER_162}) == 256 / 162
    assert abs(UM.kg_per_m(16, {"method": UM.D2_OVER_162_16}) - 256 / 162.16) < 1e-12
    assert abs(UM.kg_per_m(16, {"method": UM.EXACT_DENSITY, "density_kg_m3": 7850}) - 1.5783361) < 1e-6    # pi/4 x 0.016^2 x 7850
    assert UM.kg_per_m(16, {"method": UM.STANDARD_MASS_TABLE, "table": {"16": 1.58}}) == 1.58
    with pytest.raises(UM.UnitMassError):
        UM.kg_per_m(18, {"method": UM.STANDARD_MASS_TABLE, "table": {"16": 1.58}})
    with pytest.raises(UM.UnitMassError):
        UM.assert_single_method([{"method": UM.D2_OVER_162}, {"method": UM.EXACT_DENSITY, "density_kg_m3": 7850}])
    from engine.source import rebar_model as RM
    assert RM.kgm(16) == 256 / 162                                   # beams / slabs / footings path unchanged


def test_per_metre_notation_is_a_rate_and_spacing_is_geometry():
    assert CR.parse_transverse_notation("6Ø8/m")["notation"] == CR.RATE_PER_M
    assert CR.parse_transverse_notation("Ø8 @ 150")["notation"] == CR.SPACING
    P = {"tie_rule": {"notation": CR.RATE_PER_M}}
    assert CR.level_method(P) == CR.RATE_COUNT
    P = {"tie_rule": {"notation": CR.SPACING}}
    assert CR.level_method(P) == CR.SPACING_WITH_ENDS
    P = {"tie_rule": {"notation": CR.RATE_PER_M}, "level_method_policy": {CR.RATE_PER_M: CR.SPACING_WITH_ENDS,
                                                                          "authority": "PROJECT_OVERRIDE"}}
    assert CR.level_method(P) == CR.SPACING_WITH_ENDS                 # explicit override possible
    lv = CR.tie_levels(3000, [{"zone_id": "Z", "spacing_mm": 150, "length_mm": None}])
    assert lv[CR.RATE_COUNT] == 20 and lv[CR.SPACING_WITH_ENDS] == 21


def test_section_transition_is_blocked_without_detail():
    cand = {"type": "K", "definition": {"B_mm": 250, "D_mm": 500, "bars": {"count": 8, "dia_mm": 16}}}
    assert CR.section_transition({}, cand, {"section_mm": [250, 500]}) is None
    t = CR.section_transition({}, cand, {"section_mm": [200, 500]})
    assert t["state"] == CR.BLOCKED and t["kind"] == "BLOCKED_TRANSITION_DETAIL"
    t = CR.section_transition({}, cand, {"section_mm": [200, 500], "transition_detail": {"kind": "OFFSET_CRANK"}})
    assert t["state"] == "DETAILED"
    assert CR.section_transition({}, cand, {"section_mm": [250, 500], "orientation_change": True})["state"] == \
        CR.BLOCKED
