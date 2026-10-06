"""Coverage-recovery round - synthetic tests only (no project drawing, no reference or oracle value).

The brief's 20 cases, the donor-defect regressions (U-C4N / christiannp lessons) and the sanity-tier / neck-mapping
decisions."""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from engine.source import accurate_boq_rebar as AB
from engine.source import beam_occurrence_recovery as BR
from engine.source import blocker_remediation as BRM
from engine.source import cad_guards as CG
from engine.source import column_concrete_geometry as CC
from engine.source import coverage_anomaly as CA
from engine.source import coverage_metrics as CM
from engine.source import evidence_ladder as EL
from engine.source import ground_beam_recovery as GB
from engine.source import ground_slab_recovery as GS
from engine.source import multi_route_evidence as MR
from engine.source import physical_measurement_state as PM
from engine.source import physical_wall_faces as WF
from engine.source import population_conservation as PC
from engine.source import quantity_scenarios as QS
from engine.source import rebar_sanity_variance as SV
from engine.source import rough_rebar_sanity as RR
from engine.source import slab_opening_reconciliation as SO
from engine.source import wall_band_reconciliation as WB

ROOT = Path(__file__).resolve().parents[2]
NEW_MODULES = ("physical_measurement_state.py", "quantity_scenarios.py", "population_conservation.py",
               "evidence_ladder.py", "blocker_remediation.py", "coverage_metrics.py", "coverage_anomaly.py",
               "multi_route_evidence.py", "ground_beam_recovery.py", "ground_slab_recovery.py",
               "column_concrete_geometry.py", "beam_occurrence_recovery.py", "slab_opening_reconciliation.py",
               "physical_wall_faces.py", "wall_band_reconciliation.py", "rebar_sanity_qa.py")


def depth(value=None, low=None, high=None, level="SCHEDULE"):
    """A resolver set that answers at one ladder level."""
    if value is None and low is None:
        return {}
    return {level: lambda ctx: {"value": value, "low": low, "high": high, "ref": "test"}}


SPAN = {"span_id": "S1", "geometry": {"kind": "LINE", "p0": (0.0, 0.0), "p1": (8.4, 0.0)}, "B_m": 0.2,
        "kind": "EXTERIOR", "source_handles": ["H1"]}


# 1
def test_beam_with_missing_depth_survives():
    r = GB.recover([SPAN], lambda s: {})
    rec = r["spans"][0]
    assert rec["terminal"]["terminal_state"] == "UNQUANTIFIED"
    assert rec["terminal"]["known_geometry"]["length_m"] == pytest.approx(8.4)
    assert rec["terminal"]["source_handles"] == ["H1"]
    assert r["conservation"]["ok"] and r["volume"]["UNQUANTIFIED_COMPONENTS"]


# 2
def test_source_conflict_emits_both_scenarios():
    sched = {"B1": {"B_m": 0.2, "D_m": 0.4}, "B2": {"B_m": 0.2, "D_m": 0.6}}
    r = BR.recover([{"tag_id": "t1", "type": "B1"}, {"tag_id": "t2", "type": "B2"}],
                   [{"band_id": "b", "length_m": 8.4, "width_m": 0.2}], sched, slab_t_m=0.16,
                   tag_band={"t1": "b", "t2": "b"})
    o = r["objects"][0]
    assert o["outcome"] == "TYPE_CONFLICT" and o["part"]["state"] == "SOURCE_CONFLICT"
    assert o["part"]["low"] == pytest.approx(8.4 * 0.2 * 0.24) and o["part"]["high"] == pytest.approx(8.4 * 0.2 * 0.44)


# 3
def test_blocked_semantics_never_delete_physical_area():
    assert PM.release_state(PM.MEASURED, PM.BLOCKED) == PM.AUDIT_ONLY
    assert PM.release_state(PM.MEASURED, PM.BLOCKED) != PM.UNQUANTIFIED
    rec = PM.stamp({"value": 28.4}, PM.MEASURED, PM.BLOCKED, origins=[PM.SOURCE_FACT])
    assert PM.blocked_is_not_zero(rec) and rec["value"] == 28.4


# 4
def test_unreadable_note_triggers_fallback_search():
    rec = BRM.remediate({"flag_id": "F1", "kind": "UNREADABLE_TEXT", "element": "general note 12",
                         "unknown_fact": "note text", "why_blocked": "SHX glyphs unreadable",
                         "consultant_question": "Please re-issue note 12 in a readable font."},
                        {"CAD_TEXT": lambda c: None, "PDF_VECTOR_TEXT": lambda c: {"value": "decoded", "ref": "p.8"}})
    assert [a["level"] for a in rec["attempts"]] == ["CAD_TEXT", "PDF_VECTOR_TEXT"]
    assert rec["attempts"][0]["result"] == "NOT_FOUND" and rec["result"] == BRM.RESOLVED_SOURCE
    assert rec["consultant_question"] is None


# 5
def test_unbound_beam_recovered_from_faces_and_continuity():
    sched = {"B1": {"B_m": 0.2, "D_m": 0.5}}
    r = BR.recover([{"tag_id": "t1", "type": "B1"}],
                   [{"band_id": "tagged", "length_m": 4.0, "width_m": 0.2},
                    {"band_id": "next", "length_m": 3.0, "width_m": 0.2}], sched, slab_t_m=0.16,
                   tag_band={"t1": "tagged"}, continuity={"next": "tagged"})
    nxt = next(o for o in r["objects"] if o["occurrence_id"] == "next")
    assert nxt["outcome"] == "BAND_WITHOUT_TAG" and nxt["part"]["best"] == pytest.approx(3.0 * 0.2 * 0.34)
    assert nxt["terminal"]["terminal_state"] == "CANDIDATE_QUANTIFIED"


# 6
def test_crossing_beam_kept_at_region_boundary():
    region = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    crossing = dict(SPAN, span_id="X", geometry={"kind": "LINE", "p0": (-5.0, 5.0), "p1": (15.0, 5.0)})
    assert not CG.start_point_inside_region(((-5.0, 5.0), (15.0, 5.0)), region)        # the donor defect
    assert [s["span_id"] for s in GB.spans_in_region([crossing], region)] == ["X"]


# 7
def test_curved_beam_retained_with_arc_length():
    arc = dict(SPAN, span_id="A", geometry={"kind": "ARC", "radius": 4.0, "sweep_deg": 90.0})
    r = GB.recover([arc], lambda s: depth(0.6))
    assert r["length_m"] == pytest.approx(2 * 3.141592653589793)
    assert r["spans"][0]["terminal"]["known_geometry"]["curved"] is True


# 8
def test_unlabelled_slab_cell_contributes_candidate_area():
    cells = [{"cell_id": "a", "area_m2": 15.0, "eff_width_mm": 1800, "labels": ["T=10cm"]},
             {"cell_id": "b", "area_m2": 40.0, "eff_width_mm": 1200, "labels": ["+1.00"]},
             {"cell_id": "s", "area_m2": 0.05, "eff_width_mm": 80, "labels": []}]
    cl = GS.classify(cells, is_thickness_label=lambda t: t.startswith("T="))
    t = EL.resolve("SLAB_THICKNESS", {"SAME_SHEET_TYPICAL_LABEL": lambda c: {"value": 0.10}})
    q = GS.quantities(cl, t)
    assert q["area"]["VERIFIED_QUANTITY"] == 15.0 and q["area"]["BEST_PROVISIONAL_QUANTITY"] == 55.0
    assert q["area"]["LOW_SCENARIO"] == 15.0                       # an unlabelled cell may not be slab
    assert [x["role"] for x in q["excluded"]] == [GS.EXCLUDED_SLIVER]


def test_ground_slab_decomposition_recovers_cells_between_beams():
    pytest.importorskip("shapely")
    from shapely.geometry import box
    # 6 x 4 m footprint closed by 300 mm bands, split by one internal band
    bands = [box(0, 0, 6000, 300), box(0, 3700, 6000, 4000), box(0, 0, 300, 4000), box(5700, 0, 6000, 4000),
             box(2850, 0, 3150, 4000)]
    cells = GS.decompose(bands, min_footprint_m2=1.0, labels=[(1500, 2000, "T=10cm")])
    assert len(cells) == 2 and sum(c["area_m2"] for c in cells) == pytest.approx(2 * 2.55 * 3.4)
    cl = GS.classify(cells, is_thickness_label=lambda t: t.startswith("T="))
    assert sorted(c["role"] for c in cl) == [GS.LABELLED_OFFICIAL, GS.UNLABELLED_CANDIDATE]


# 9
def test_every_slab_deduction_has_opening_provenance():
    faces = [{"face": "P", "role": "PLATE", "area_m2": 90.0},
             {"face": "V", "role": "OPENING_VOID", "area_m2": 6.0, "why": "VOID label", "tags_cm": []},
             {"face": "C", "role": "OPENING_VOID", "area_m2": 4.0, "why": "VOID label", "tags_cm": [16]}]
    r = SO.reconcile(100.0, faces, sheet="GF")
    assert {o["opening_id"] for o in r["openings"]} == {"GF:V", "GF:C"}
    assert next(o for o in r["openings"] if o["face"] == "C")["state"] == SO.OPENING_CONFLICT
    assert r["net_area"]["HIGH_SCENARIO"] == pytest.approx(94.0)
    with pytest.raises(SO.OpeningError):
        SO.reconcile(105.0, faces, sheet="GF")                      # an unexplained 5 m2 deduction


# 10
def test_column_rebar_blocker_does_not_block_concrete():
    occ = {"occurrence_id": "C1", "B_m": 0.3, "D_m": 0.6, "interval_m": 4.5, "interval_state": "ESTABLISHED"}
    r = CC.record(occ, slab_t_m=0.16)
    assert r["net_of_slab_m3"] == pytest.approx(0.18 * 4.34) and r["terminal"]["terminal_state"] == "MEASURED_COMPLETE"
    with pytest.raises(CC.ColumnConcreteError):
        CC.record(dict(occ, tie_topology="BLOCKED"), slab_t_m=0.16)


WALL = {"wall_id": "W1", "floor": "GF", "length_m": 5.0, "thickness_mm": 200, "position": "INTERNAL",
        "net_of_openings": True}


# 11 + 12
def test_material_and_paint_uncertainty_keep_physical_and_plaster_area():
    h = EL.resolve("WALL_HEIGHT", {"FLOOR_TO_FLOOR_MINUS_STRUCTURE": lambda c: {"value": 3.4}})
    fs = WF.faces(dict(WALL, finish=None), h)
    assert all(f["PHYSICAL_WALL_FACE_AREA"] == pytest.approx(17.0) for f in fs)
    assert all(f["GROSS_PLASTER_ELIGIBLE_AREA"] == pytest.approx(17.0) for f in fs)
    assert all(f["FINAL_FINISH_ASSIGNMENT"] == "BLOCKED_FINISH_NOT_ASSIGNED" for f in fs)
    reg = WF.register([WALL], lambda w: h)
    assert reg["physical_area"]["BEST_PROVISIONAL_QUANTITY"] == pytest.approx(34.0)


# 13
def test_one_physical_object_once_after_multi_route_recovery():
    rec = MR.reconcile({"TAG": [{"key": "B-1", "value": 1.20}], "FACE": [{"key": "B-1", "value": 1.21}]})
    assert len(MR.physical_objects(rec)) == 1 and rec[0]["state"] == MR.CONFIDENCE_UP
    rec2 = MR.reconcile({"TAG": [{"key": "B-1", "value": 1.2}], "FACE": [{"key": "B-1", "value": 1.6}]})
    assert rec2[0]["state"] == MR.ROUTE_CONFLICT and rec2[0]["value"] is None          # never averaged
    with pytest.raises(MR.RouteError):
        MR.reconcile({"TAG": [{"key": "B-1", "value": 1}, {"key": "B-1", "value": 1}]})


# 14
def test_schedule_definition_never_creates_an_occurrence():
    a = PC.admit([{"object_id": "row-B3", "role": "SCHEDULE_ROW"}, {"object_id": "tag-1", "role": "PLAN_TAG"}])
    assert [o["occurrence_id"] for o in a["occurrences"]] == ["tag-1"]
    assert a["definitions_not_occurrences"] == ["row-B3"]


# 15
def test_reference_and_oracle_numbers_cannot_enter_recovery_logic():
    banned = (352.436075, 44.19, 337.812, 333.173, 36.005, 36.006, 32.183, 32.404, 50.841, 46.591, 95.689, 96.753,
              590.362, 598.708, 66.579, 65.669, 6.122, 6.053, 148.095, 183.497, 71.589, 79.971, 2364.7, 22.619, 22.916,
              29.55, 37.98, 65.634, 518.25, 525.155, 372.19)
    for m in NEW_MODULES:
        src = (ROOT / "engine" / "source" / m).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
                assert not any(abs(n.value - b) <= 1e-4 * b for b in banned), (m, n.value)
        low = src.lower()
        for name in ("uc4n", "u-c4n", "christiannp", "freelancer", "alsenan", "st7757", "p7757"):
            assert name not in low, (m, name)


# 16
def test_provisional_never_labelled_verified():
    with pytest.raises(QS.ScenarioError):
        QS.part("p", "VERIFIED", 10.0, 8.0, 12.0)
    q = QS.combine([QS.part("a", "VERIFIED", 10.0), QS.part("b", "PROVISIONAL", 5.0, 4.0, 6.0)])
    assert q["VERIFIED_QUANTITY"] == 10.0 and QS.release_label(q) != "OFFICIAL"
    assert PM.release_state(PM.MEASURED, PM.VERIFIED, origins=[PM.URBAN_PROVISIONAL]) == PM.PROVISIONAL_ONLY


# 17
def test_low_high_bracket_best():
    with pytest.raises(QS.ScenarioError):
        QS.part("p", "PROVISIONAL", 5.0, 6.0, 7.0)
    q = QS.combine([QS.part("a", "LOWER_BOUND", 3.21), QS.part("b", "PROVISIONAL", 1.61, 0.0, 1.89)])
    assert q["LOWER_BOUND_QUANTITY"] <= q["LOW_SCENARIO"] <= q["BEST_PROVISIONAL_QUANTITY"]
    assert q["HIGH_SCENARIO"] is None                                  # a lower bound has no upper limit


# 18
def test_remediation_records_every_attempted_method():
    rec = BRM.remediate({"flag_id": "GB-EXT", "kind": "MISSING_DEPTH", "element": "exterior GB",
                         "known_facts": {"length_m": 8.4, "B_m": 0.3}, "unknown_fact": "depth",
                         "current_quantity": 0.0, "why_blocked": "depth not dimensioned",
                         "where_to_look": "ground-beam sections", "search_text": "FOLLOW ARCH",
                         "consultant_question": "Please confirm the exterior ground-beam depth."},
                        {"LOCAL_DIMENSION": lambda c: None, "SCHEDULE": lambda c: None,
                         "BOUNDED_CANDIDATE": lambda c: {"value": 1.0, "low": 0.9, "high": 1.3}},
                        quantity_fn=lambda d: 8.4 * 0.3 * d)
    lv = [(a["level"], a["result"]) for a in rec["attempts"]]
    assert lv[:3] == [("LOCAL_DIMENSION", "NOT_FOUND"), ("SCHEDULE", "NOT_FOUND"), ("DETAIL", "NOT_AVAILABLE")]
    assert lv[-1] == ("BOUNDED_CANDIDATE", "FOUND") and rec["result"] == BRM.RESOLVED_PROVISIONAL
    assert rec["provisional_quantity"] == pytest.approx(2.52) and rec["low_scenario"] == pytest.approx(2.268)
    assert rec["needs_consultant"] and rec["next_automated_method"] == "DETAIL"
    assert all(f in rec for f in BRM.REQUIRED_FIELDS)


# 19
def test_coverage_anomaly_on_large_unexplained_loss():
    f = CA.ground_slab_vs_footprint(70.0, 200.0)
    assert f["state"] == CA.COVERAGE_ANOMALY and f["unexplained"] == pytest.approx(130.0)
    assert CA.count_conservation("COL-GF", 30, 15)["state"] == CA.CONSERVATION_FAILURE
    assert CA.walls_vs_paired_faces(95.0, 100.0)["state"] == CA.OK


# 20
def test_all_occurrences_terminate():
    occ = [{"occurrence_id": "a", "source_handles": ["h"]}, {"occurrence_id": "b", "source_handles": ["h2"]}]
    t = [PC.terminal(occ[0], "MEASURED_COMPLETE", quantity=1.0)]
    r = PC.conserve(occ, t)
    assert not r["ok"] and r["missing"] == ["b"]
    t.append(PC.terminal(occ[1], "UNQUANTIFIED", unresolved=["DEPTH"]))
    assert PC.require_conserved(occ, t)["by_state"] == {"MEASURED_COMPLETE": 1, "UNQUANTIFIED": 1}


def test_coverage_metrics_explain_rather_than_total():
    occ = [{"terminal_state": "MEASURED_COMPLETE", "known": {"length": True, "depth": True}, "semantic_established": True,
            "source_only": True},
           {"terminal_state": "BOUNDED_QUANTIFIED", "known": {"length": True, "depth": False}}]
    m = CM.trade_coverage("GB", occ, official_qty=10.0, best_qty=40.0, dimensions=("length", "depth"))
    assert m["population_pct"] == 100.0 and m["geometry_pct"] == {"length": 100.0, "depth": 50.0}
    assert m["quantity_official_pct_of_best"] == 25.0


# ------------------------------------------------------------------------------------------- donor regressions
def test_c4n_cn_propagation_error_does_not_happen():
    """A column without its own section stays UNQUANTIFIED; no neighbour's section is propagated to it."""
    r = CC.record({"occurrence_id": "CN-1", "B_m": None, "D_m": None, "interval_m": 4.5}, slab_t_m=0.16)
    assert r["terminal"]["terminal_state"] == "UNQUANTIFIED" and r["net_of_slab_m3"] is None


def test_c4n_slab_thickness_assumption_never_overrides_project_rule():
    t = EL.resolve("SLAB_THICKNESS", {"PROJECT_GENERAL_RULE": lambda c: {"value": 0.16, "ref": "general note"},
                                      "URBAN_PROVISIONAL_FALLBACK": lambda c: {"low": 0.2, "high": 0.2}})
    assert t["value"] == 0.16 and t["level"] == "PROJECT_GENERAL_RULE" and t["fact_origin"] == "SOURCE_FACT"


def test_c4n_geometry_authority_mismatch_is_refused():
    geo = CG.physical_occurrence_geometry("B1", axis_start=(0.0, 0.0), axis_end=(6.0, 0.0), support_widths=(0.3, 0.3))
    assert CG.check_geometry_consistency(geo, concrete_span=5.7, rebar_span=5.7, concrete_basis="clear_span",
                                         rebar_basis="rebar_design_span") == []
    bad = CG.check_geometry_consistency(geo, concrete_span=5.7, rebar_span=6.2, concrete_basis="clear_span",
                                        rebar_basis="drawn_band")
    assert bad and "not derived" in bad[0]


def test_christiannp_omitted_ground_beam_steel_is_not_zero():
    s = AB.summarise([{"part_id": "gb", "category": "GROUND_BEAMS", "component": "BEAM_BOTTOM_BAR",
                       "state": "BLOCKED_UNQUANTIFIED", "kg": None, "basis": ["SCHEDULE"]},
                      {"part_id": "c", "category": "COLUMNS", "component": "COLUMN_MAIN_BAR", "state": "VERIFIED",
                       "kg": 10.0, "basis": ["SCHEDULE"]}])
    assert s["categories"]["GROUND_BEAMS"]["official_status"] == AB.BLOCKED
    assert s["project"]["final_rebar"] == AB.FINAL_REBAR_NOT_ESTABLISHED


def test_incomplete_slab_top_bars_keep_slab_partial():
    s = AB.summarise([{"part_id": "b", "category": "SLABS", "component": "SLAB_BOTTOM_X", "state": "VERIFIED",
                       "kg": 100.0, "basis": ["STRUCTURAL_DETAIL"]},
                      {"part_id": "t", "category": "SLABS", "component": "SLAB_TOP_SUPPORT",
                       "state": "BLOCKED_UNQUANTIFIED", "kg": None, "basis": ["STRUCTURAL_DETAIL"]}])
    assert s["categories"]["SLABS"]["official_status"] == AB.PARTIAL


def test_wall_pair_false_positives_are_classified():
    # a 200 mm wall (faces a, b), a finish line c 200 mm beyond b, a column across the run, a door gap
    segs = [("a", 0, 0, 6000, 0), ("b", 0, 200, 6000, 200), ("c", 0, 400, 6000, 400)]
    iv = WB.pair_parallel_faces(segs, 200.0)
    assert len(iv) == 2                                                # a-b and b-c both look like walls
    cl = WB.classify(iv, column_boxes=[(1000, -50, 1400, 450)], opening_boxes=[(4000, -50, 4900, 450)])
    t = WB.totals(cl)
    assert t[WB.COLUMN_OVERLAP] == pytest.approx(0.8) and t[WB.OPENING_SPAN] == pytest.approx(1.8)
    assert t[WB.PAIRED_WALL] == pytest.approx(2 * (6.0 - 0.4 - 0.9))
    ex = WB.explain({"established_m": 4.0, "ambiguous_m": 1.0}, {WB.PAIRED_WALL: 6.0})
    assert ex["URBAN_AMBIGUOUS_NOT_MEASURED"] == 1.0 and ex["URBAN_MISSED_OR_UNRESOLVED"] == 1.0


# ------------------------------------------------------------------------------- sanity tiers + neck mapping
PROFILE = json.loads((ROOT / "engine" / "profiles" / "URBAN_ROUGH_REBAR_PROFILE_V1.json").read_text(encoding="utf-8"))


def _acc(parts):
    return AB.summarise([dict(p, basis=["SCHEDULE"]) for p in parts])


def test_sanity_tiers():
    assert [SV.tier(x) for x in (0, 14.9, 15, 24.9, 25, 39.9, 40, -55)] == \
        [SV.NORMAL, SV.NORMAL, SV.WATCH, SV.WATCH, SV.REVIEW, SV.REVIEW, SV.MAJOR, SV.MAJOR]


def test_neck_maps_to_walls_and_columns_in_this_profile_only():
    assert RR.category_of("FOUNDATION_NECK", PROFILE) == "WALLS_AND_COLUMNS"
    assert RR.category_of("FOUNDATION_NECK") == "FOUNDATIONS_RELATED"           # engine default unchanged
    other = dict(PROFILE, mapping_overrides={})
    assert RR.category_of("FOUNDATION_NECK", other) == "FOUNDATIONS_RELATED"


def test_not_evaluable_states_and_tiered_variance():
    rough = RR.rough_summary([{"occurrence_id": "c", "element_class": "COLUMN", "concrete_m3": 1.0,
                               "concrete_state": "VERIFIED"},
                              {"occurrence_id": "n", "element_class": "FOUNDATION_NECK", "concrete_m3": 1.0,
                               "concrete_state": "VERIFIED"}], PROFILE)
    acc = _acc([{"part_id": "m", "category": "COLUMNS", "component": "COLUMN_MAIN_BAR", "state": "VERIFIED",
                 "kg": 300.0}])
    r0 = copy.deepcopy(acc)
    row = SV.compare(acc, rough, PROFILE)["rows"][0]
    assert row["state"] == SV.NOT_EVALUABLE_SCOPE_MISMATCH and row["SANITY_VARIANCE_PERCENT"] is None
    assert acc == r0
    acc2 = _acc([{"part_id": "m", "category": "COLUMNS", "component": "COLUMN_MAIN_BAR", "state": "VERIFIED",
                  "kg": 300.0},
                 {"part_id": "nk", "category": "FOUNDATIONS", "component": "NECK_MAIN_BAR", "state": "VERIFIED",
                  "kg": 120.0}])
    row = next(r for r in SV.compare(acc2, rough, PROFILE)["rows"] if r["category"] == "WALLS_AND_COLUMNS")
    assert row["state"] == SV.SANITY_VARIANCE and row["SANITY_VARIANCE_PERCENT"] == pytest.approx(5.0)
    assert row["tier"] == SV.NORMAL and not row["flags"]
    blocked = RR.rough_summary([{"occurrence_id": "c", "element_class": "COLUMN", "concrete_m3": 1.0,
                                 "concrete_state": "BLOCKED"},
                                {"occurrence_id": "c2", "element_class": "COLUMN", "concrete_m3": 1.0,
                                 "concrete_state": "VERIFIED"}], PROFILE)
    assert SV.compare(acc, blocked, PROFILE)["rows"][0]["state"] == SV.NOT_EVALUABLE_INCOMPLETE_CONCRETE
