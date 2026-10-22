"""T-186: the default guard on synthetic villa Q (hand calculation in villa_q.py, written before any run).

Each adverse case is a failure the team actually made on the development villa (curved pool wall missed, a convention
used despite a printed structural thickness, part of a pool footprint, a staircase missed, an upper-floor flight
dropped, a landing / pool base-wall junction counted twice, a client-requested change as the approved design, a finished
depth taken as the RC wall height, a through-beam deducting the full column face). Each has a normal case that passes,
and test_each_check_is_load_bearing shows every adverse test fails on the unguarded (old) behaviour.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import default_guard as DG  # noqa: E402
from tests.t186_default_guard import villa_q as V  # noqa: E402


def run(lines, **over):
    return DG.guard(lines, **V.guard_kwargs(**over))


def codes(res, line_id=None):
    return sorted(f["code"] for f in res["findings"] if line_id is None or f["line_id"] == line_id)


def line(res, line_id):
    for ln in res["baseline"] + res["scenarios"]["S1"]:
        if ln["id"] == line_id:
            return ln
    raise KeyError(line_id)


# ------------------------------------------------------------------ hand values
def test_hand_values_of_the_fixture():
    outer = 5.00 * 2.50 + math.pi * 1.25 ** 2 / 2
    inner = 4.75 * 2.00 + math.pi * 1.00 ** 2 / 2
    assert outer == pytest.approx(V.OUTER, abs=1e-6)
    assert outer - inner == pytest.approx(V.RING, abs=1e-6)
    assert V.RING - V.STRAIGHT == pytest.approx(math.pi * (1.25 ** 2 - 1.0 ** 2) / 2, abs=1e-6)
    assert V.FLIGHT == pytest.approx(1.20 * 3.00 * 0.15 + 10 * 0.5 * 0.30 * 0.17 * 1.20, abs=1e-9)
    assert V.LANDING == pytest.approx(1.20 * 1.20 * 0.15, abs=1e-9)


# ------------------------------------------------------------------ normal: the drawing-derived BOQ passes
def test_normal_drawing_derived_boq_passes_everything():
    res = run(V.right_lines())
    assert res["findings"] == []
    assert DG.released_total(res["baseline"], "CONCRETE", "m3") == pytest.approx(
        5.234029 + 5.631181 + 4 * 0.846 + 2 * 0.216 + 0.846 + 18.0 + 1.2 + 3.6, abs=1e-5)
    assert line(res, "POOL-WALLS")["evidence_status"] == "DRAWING-CONFIRMED"
    assert line(res, "T1-WALLS")["evidence_status"] == "ASSUMED - OWNER-APPROVED (SYNTHETIC-OWNER-RULE-1)"
    assert [ln["id"] for ln in res["scenarios"]["S1"]] == ["DOME-D1-SKYLIGHT"]


# ------------------------------------------------------------------ 1 + 2 + 3: the old pool (conventions, straight strip)
def test_adverse_old_pool_is_held_with_the_printed_values_cited():
    old = V.old_pool(V.right_lines())
    # the unguarded old behaviour releases 3.125 + 4.800 = 7.925 m3 of pool
    assert DG.released_total([ln for ln in old if ln["element_id"] == "P1"], "CONCRETE", "m3") == pytest.approx(7.925)
    res = run(old)
    fl, wl = line(res, "POOL-FLOOR"), line(res, "POOL-WALLS")
    assert fl["state"] == wl["state"] == "HELD"
    assert fl["info_qty"] == 3.125 and wl["info_qty"] == 4.8          # kept as information, never 0
    assert codes(res, "POOL-FLOOR") == ["CONVENTION_WHERE_PRINTED", "PARTIAL_FOOTPRINT", "SEARCH_INCOMPLETE"]
    assert codes(res, "POOL-WALLS") == ["CONVENTION_WHERE_PRINTED", "PARTIAL_FOOTPRINT", "SEARCH_INCOMPLETE"]
    cite = [f for f in res["findings"] if f["line_id"] == "POOL-FLOOR" and f["code"] == "CONVENTION_WHERE_PRINTED"][0]
    assert cite["citation"][0]["value"] == 0.35 and cite["citation"][0]["doc"] == "D-S05"
    part = [f for f in res["findings"] if f["line_id"] == "POOL-WALLS" and f["code"] == "PARTIAL_FOOTPRINT"][0]
    assert "77.2%" in part["detail"] and "0.8836" in part["detail"]   # 3.000 / 3.883573 ; curved half 0.883573
    assert DG.released_total([ln for ln in res["baseline"] if ln["element_id"] == "P1"], "CONCRETE", "m3") == 0.0


def test_adverse_convention_despite_printed_thickness_only():
    lines = V.replace(V.right_lines(), "POOL-FLOOR", qty=round(V.OUTER * 0.25, 6),
                      values={"POOL_FLOOR_THICKNESS_M": {"value": 0.25, "source": "CONVENTION",
                                                         "ref": "POOL_FLOOR_THICKNESS_M", "approval": "X"}})
    res = run(lines)
    assert codes(res) == ["CONVENTION_WHERE_PRINTED"]                 # footprint full, search complete: still fails
    assert line(res, "POOL-FLOOR")["state"] == "HELD"


def test_adverse_printed_values_disagree_is_a_conflict_not_a_choice():
    lines = V.replace(V.right_lines(), "POOL-FLOOR",
                      values={"POOL_FLOOR_THICKNESS_M": {"value": 0.25, "source": "CONVENTION", "approval": "X"}})
    res = run(lines, printed=V.PRINTED + [V.PR_DISAGREE])
    assert codes(res) == ["PRINTED_VALUES_DISAGREE"]
    assert "[0.3, 0.35]" in res["findings"][0]["detail"]


def test_adverse_partial_pool_footprint_only():
    res = run(V.replace(V.right_lines(), "POOL-FLOOR", footprint={"value": 12.5, "unit": "m2"}))
    assert codes(res) == ["PARTIAL_FOOTPRINT"]
    assert "83.6%" in res["findings"][0]["detail"]                    # 12.5 / 14.954369


def test_footprint_within_tolerance_passes_and_overrun_fails():
    ok = run(V.replace(V.right_lines(), "POOL-WALLS", footprint={"value": V.RING * 0.996, "unit": "m2"}))
    assert ok["findings"] == []
    over = run(V.replace(V.right_lines(), "POOL-WALLS", footprint={"value": V.RING * 1.02, "unit": "m2"}))
    assert codes(over) == ["FOOTPRINT_EXCEEDS_DRAWN"]


def test_footprint_unit_mismatch_is_refused():
    with pytest.raises(DG.GuardError):
        run(V.replace(V.right_lines(), "POOL-WALLS", footprint={"value": 3.88, "unit": "m"}))


# ------------------------------------------------------------------ search record and approval (WORKFLOW_CONTROLS s.4)
def test_adverse_convention_search_and_approval():
    no_rec = run(V.replace(V.right_lines(), "T1-WALLS", searched=[]))
    assert codes(no_rec) == ["SEARCH_NOT_RECORDED"]
    part = run(V.replace(V.right_lines(), "T1-WALLS", searched=["D-A01", "D-A05"]))
    assert codes(part) == ["SEARCH_INCOMPLETE"] and "D-S05" in part["findings"][0]["detail"]
    unapproved = run(V.replace(V.right_lines(), "T1-WALLS", values={
        "TANK_HEIGHT_M": {"value": 1.50, "source": "CONVENTION", "ref": "TANK_HEIGHT_M"}}))
    assert codes(unapproved) == ["FALLBACK_NOT_APPROVED"]
    assert line(unapproved, "T1-WALLS")["evidence_status"] == "HELD"


# ------------------------------------------------------------------ 4 + 5: staircases
def test_adverse_one_of_two_staircases_missed():
    res = run(V.drop(V.right_lines(), "ST-B-F1"))
    assert codes(res) == ["SILENT_OMISSION"]
    ph = line(res, "DG5:ST-B:F1")
    assert ph["state"] == "HELD" and ph["qty"] is None                # a placeholder, never 0


def test_adverse_upper_floor_flights_dropped():
    res = run(V.drop(V.right_lines(), "ST-A-F3", "ST-A-F4"))
    assert sorted(f["element_id"] + ":" + f["detail"].rsplit(" part ", 1)[1].split()[0]
                  for f in res["findings"]) == ["ST-A:F3", "ST-A:F4"]


def test_held_line_counts_as_carried_not_omitted():
    res = run(V.replace(V.right_lines(), "ST-B-F1", state="HELD", qty=None))
    assert res["findings"] == []
    assert line(res, "ST-B-F1")["evidence_status"] == "HELD"


# ------------------------------------------------------------------ 6: double counts
def test_adverse_landing_counted_in_stair_and_slab():
    res = run(V.replace(V.right_lines(), "SLAB-1F", covers=["SL1:FIELD", "ST-A:L1"]))
    assert codes(res) == ["DOUBLE_COUNT", "DOUBLE_COUNT"]
    assert line(res, "SLAB-1F")["state"] == line(res, "ST-A-L1")["state"] == "HELD"


def test_adverse_pool_base_under_wall_counted_twice():
    lines = V.replace(V.right_lines(), "POOL-WALLS", qty=round(V.RING * 1.80, 6),
                      covers=["P1:WALL_ABOVE_BASE", "P1:BASE_UNDER_WALL"])
    unguarded = DG.released_total(lines, "CONCRETE", "m3") - DG.released_total(V.right_lines(), "CONCRETE", "m3")
    assert unguarded == pytest.approx(V.RING * 0.35, abs=1e-5)       # +1.359251 m3 double count
    res = run(lines)
    assert codes(res) == ["DOUBLE_COUNT", "DOUBLE_COUNT"]


def test_superseded_or_scenario_lines_never_double_count():
    lines = V.right_lines() + [dict(V.right_lines()[0], id="POOL-FLOOR-OLD", state="SUPERSEDED")]
    assert run(lines)["findings"] == []


# ------------------------------------------------------------------ 7: scenarios
def test_adverse_client_change_treated_as_approved_design():
    lines = V.drop(V.right_lines(), "DOME-D1-SHELL")
    lines = V.replace(lines, "DOME-D1-SKYLIGHT", scenario="S0")
    res = run(lines)
    assert codes(res) == ["CLIENT_CHANGE_AS_APPROVED", "SILENT_OMISSION"]
    assert [ln["id"] for ln in res["scenarios"]["S1"]] == ["DOME-D1-SKYLIGHT"]
    assert line(res, "DG5:D1:SHELL")["state"] == "HELD"


def test_adverse_revision_claimed_but_not_issued():
    lines = V.replace(V.right_lines(), "DOME-D1-SKYLIGHT", scenario="S2", origin="CONSULTANT_REVISION")
    res = run(lines)
    assert codes(res) == ["REVISION_NOT_ISSUED"]
    assert "DOME-D1-SKYLIGHT" in [ln["id"] for ln in res["scenarios"]["S1"]]
    ok = run(lines, revisions=[{"element_id": "D1", "doc": "D-S05 rev B"}])
    assert ok["findings"] == [] and "DOME-D1-SKYLIGHT" in [ln["id"] for ln in ok["baseline"]]


# ------------------------------------------------------------------ T-183 r2: finished depth as RC height
def test_adverse_finished_depth_taken_as_structural_height():
    lines = V.replace(V.right_lines(), "POOL-WALLS", qty=round(V.RING * 1.40, 6),
                      values={"POOL_WALL_HEIGHT_M": {"value": 1.40, "source": "PRINTED", "ref": "PR-3"}})
    res = run(lines)
    assert codes(res) == ["FINISHED_AS_STRUCTURAL"]
    assert line(res, "POOL-WALLS")["info_qty"] == pytest.approx(5.437002, abs=1e-6)
    only_finished = V.replace(V.right_lines(), "POOL-WALLS", values={
        "POOL_WALL_HEIGHT_M": {"value": 1.40, "source": "DERIVED", "ref": ["PR-3"]}})
    assert codes(run(only_finished)) == ["FINISHED_AS_STRUCTURAL"]
    ghost = V.replace(V.right_lines(), "POOL-WALLS", values={
        "POOL_WALL_HEIGHT_M": {"value": 1.45, "source": "PRINTED", "ref": "PR-99"}})
    assert codes(run(ghost)) == ["UNSUPPORTED_REF"]


def test_finished_record_is_fine_for_a_finishes_trade():
    lines = V.right_lines() + [dict(V.right_lines()[1], id="POOL-TILE", trade="TILES", unit="m2", qty=10.0,
                                    covers=["P1:TILE"],
                                    values={"POOL_WALL_HEIGHT_M": {"value": 1.40, "source": "PRINTED", "ref": "PR-3"}})]
    assert run(lines)["findings"] == []


# ------------------------------------------------------------------ T-163: through-beam on a column face
def test_adverse_through_beam_deducts_full_face_width():
    res = run(V.replace(V.right_lines(), "C3-FACE-N",
                        deductions=[{"member": "B7", "width_m": 0.60, "face_width_m": 0.60}]))
    assert codes(res) == ["DEDUCTION_EXCEEDS_MEMBER"]
    assert "0.200 m wide" in res["findings"][0]["detail"]


# ------------------------------------------------------------------ conservation and load-bearing checks
def test_every_line_once_and_no_held_value_becomes_zero():
    old = V.old_pool(V.drop(V.right_lines(), "ST-B-F1"))
    res = run(old)
    out_ids = [ln["id"] for ln in res["baseline"] + res["scenarios"]["S1"]]
    assert sorted(i for i in out_ids if not i.startswith("DG5:")) == sorted(ln["id"] for ln in old)
    assert res["summary"]["held_info_qty_never_zero"] is True
    assert all(ln["qty"] is None or ln["qty"] > 0 for ln in res["baseline"])


ADVERSE = {
    "DG-1": (lambda: V.replace(V.right_lines(), "POOL-FLOOR", values={
        "POOL_FLOOR_THICKNESS_M": {"value": 0.25, "source": "CONVENTION", "approval": "X"}}), "CONVENTION_WHERE_PRINTED"),
    "DG-2": (lambda: V.replace(V.right_lines(), "T1-WALLS", searched=[]), "SEARCH_NOT_RECORDED"),
    "DG-3": (lambda: V.replace(V.right_lines(), "POOL-WALLS", footprint={"value": V.STRAIGHT, "unit": "m2"}),
             "PARTIAL_FOOTPRINT"),
    "DG-4": (lambda: V.replace(V.right_lines(), "POOL-WALLS", values={
        "POOL_WALL_HEIGHT_M": {"value": 1.40, "source": "PRINTED", "ref": "PR-3"}}), "FINISHED_AS_STRUCTURAL"),
    "DG-5": (lambda: V.drop(V.right_lines(), "ST-A-F4"), "SILENT_OMISSION"),
    "DG-6": (lambda: V.replace(V.right_lines(), "SLAB-1F", covers=["ST-A:L2"]), "DOUBLE_COUNT"),
    "DG-7": (lambda: V.replace(V.right_lines(), "DOME-D1-SKYLIGHT", scenario="S0"), "CLIENT_CHANGE_AS_APPROVED"),
    "DG-8": (lambda: V.replace(V.right_lines(), "C3-FACE-N", deductions=[{"member": "B7", "width_m": 0.60}]),
             "DEDUCTION_EXCEEDS_MEMBER"),
}


@pytest.mark.parametrize("check", sorted(ADVERSE))
def test_each_check_is_load_bearing(check):
    make, code = ADVERSE[check]
    assert code in codes(run(make()))
    # the unguarded behaviour (this check absent) lets the defect through: the adverse test above would fail
    assert code not in codes(DG.guard(make(), disabled=(check,), **V.guard_kwargs()))


def test_check_registry_matches_codes():
    assert sorted(DG.CODES) == sorted(list(DG.LINE_CHECKS) + list(DG.SET_CHECKS))


def test_printed_record_limited_to_named_elements():
    pr = [dict(p) for p in V.PRINTED]
    for p in pr:
        if p["id"] == "PR-5":
            p["applies_to"] = ["ST-A"]                                  # printed for ST-A only
    lines = V.replace(V.right_lines(), "ST-B-F1", values={
        "STAIR_WAIST_M": {"value": 0.175, "source": "CONVENTION", "approval": "X"}})
    assert run(lines, printed=pr)["findings"] == []                    # ST-B: a genuine, approved fallback
    lines = V.replace(lines, "ST-A-F1", values={
        "STAIR_WAIST_M": {"value": 0.175, "source": "CONVENTION", "approval": "X"}})
    assert codes(run(lines, printed=pr)) == ["CONVENTION_WHERE_PRINTED"]


def test_canonical_adapter_reads_conventions_documents_and_footprint():
    row = {"line_id": "L-1", "trade": "CONCRETE", "unit": "m3", "item_code": "STR.CONC.POOL", "physical_element": "POOL",
           "evidence_state": "PROVISIONAL", "measured_net": 1.984,
           "location": {"element_id": "E-WALLS"}, "rule": {"conventions_used": ["POOL_WALL_HEIGHT_M", "X_CHOICE"]},
           "source": {"documents": [{"file": "s.dxf"}]},
           "calculation": {"inputs": {"dimensions": {"wall_plan_m2": 1.24}}}}
    held = dict(row, line_id="L-2", evidence_state="BOUNDED_EXPOSURE", measured_net=None)
    plain = dict(row, line_id="L-3", rule={"conventions_used": []})
    conv = [{"id": "POOL_WALL_HEIGHT_M", "kind": "number", "base": 1.6}]
    g = DG.lines_from_canonical([row, held, plain], conv, doc_alias={"s.dxf": "D-S"},
                                mapping={"E-WALLS": {"element_id": "P1", "element_kind": "POOL", "part": "WALLS",
                                                     "footprint_dim": "wall_plan_m2"}})
    assert [x["id"] for x in g] == ["L-1", "L-2"]
    a, b = g
    assert a["values"]["POOL_WALL_HEIGHT_M"] == {"value": 1.6, "source": "CONVENTION", "ref": "POOL_WALL_HEIGHT_M"}
    assert a["values"]["X_CHOICE"]["value"] is None and a["searched"] == ["D-S"]
    assert a["footprint"] == {"value": 1.24, "unit": "m2"} and a["element_id"] == "P1" and a["part"] == "WALLS"
    assert b["state"] == "HELD" and b["qty"] is None
